"""Şamile RAG: ana indeksi bozmadan kategori shard'ları.

Garanti ilkeleri
----------------
- Ana `.rag_index/{chunks,embeddings,manifest}` dokunulmaz.
- Her kategori kendi shard klasöründe; kitap kitap checkpoint.
- Gömme CPU (varsayılan) — Ollama VRAM çakışmasın.
- Finalize atomik (tmp → replace); yarıda kalan `building/` ile devam.
- Arama: mmap + satır offset; shard'ı RAM'e komple yüklemez.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from ilim_assistant.rag_store import (
    Chunk,
    _get_embedder,
    _index_dir,
    _knowledge_root,
    _MODEL_NAME,
    _split_text,
)

_EMB_DIM = 384
_BATCH = int(os.environ.get("RUZGAR_SHAMELA_EMBED_BATCH", "96") or "96")
_SHAMELA_REL = Path("ilim") / "din" / "shamela"


def _shards_root() -> Path:
    p = _index_dir() / "shards" / "shamela"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _registry_path() -> Path:
    return _shards_root() / "registry.json"


def _state_path() -> Path:
    return _shards_root() / "_build_state.json"


def _atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_registry() -> dict:
    p = _registry_path()
    if not p.is_file():
        return {"model": _MODEL_NAME, "ready": {}, "updated_at": None}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"model": _MODEL_NAME, "ready": {}, "updated_at": None}


def save_registry(reg: dict) -> None:
    reg = dict(reg)
    reg["model"] = _MODEL_NAME
    reg["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _atomic_json(_registry_path(), reg)


def load_state() -> dict:
    p = _state_path()
    if not p.is_file():
        return {"version": 1, "cats": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "cats": {}}


def save_state(st: dict) -> None:
    _atomic_json(_state_path(), st)


def shamela_root() -> Path:
    return _knowledge_root() / _SHAMELA_REL


def list_categories() -> list[str]:
    root = shamela_root()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def category_dir(cat: str) -> Path:
    return shamela_root() / cat


def shard_ready_dir(cat: str) -> Path:
    return _shards_root() / cat


def shard_building_dir(cat: str) -> Path:
    return _shards_root() / "_building" / cat


def _book_dirs(cat: str) -> list[Path]:
    base = category_dir(cat)
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir())


def _rel_source(path: Path) -> str:
    """knowledge köküne göre POSIX kaynak yolu (Windows da /)."""
    rel = path.relative_to(_knowledge_root())
    return rel.as_posix()


def _iter_book_chunks(book: Path) -> Iterable[Chunk]:
    for md in sorted(book.rglob("*.md")):
        try:
            body = md.read_text(encoding="utf-8")
        except OSError:
            continue
        src = _rel_source(md)
        for piece in _split_text(body):
            yield Chunk(text=piece, source=src)


def _count_book_chunks(book: Path) -> int:
    n = 0
    for _ in _iter_book_chunks(book):
        n += 1
    return n


def _book_part_dir(cat: str, book_name: str) -> Path:
    return shard_building_dir(cat) / "books" / book_name


def _book_done(cat: str, book_name: str) -> bool:
    d = _book_part_dir(cat, book_name)
    return (d / "emb.npy").is_file() and (d / "chunks.jsonl").is_file() and (d / "ok.json").is_file()


def _embed_texts(model, texts: Sequence[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, _EMB_DIM), dtype=np.float32)
    arr = model.encode(
        list(texts),
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=_BATCH,
    )
    out = np.asarray(arr, dtype=np.float32)
    if out.ndim != 2 or out.shape[1] != _EMB_DIM:
        raise RuntimeError(f"beklenmeyen gömme şekli: {out.shape}")
    return out


def build_book(cat: str, book: Path, *, model=None) -> dict:
    """Tek kitap → building parçası. Var ve ok ise atlar."""
    name = book.name
    out_dir = _book_part_dir(cat, name)
    if _book_done(cat, name):
        meta = json.loads((out_dir / "ok.json").read_text(encoding="utf-8"))
        return {"status": "cached", "book": name, **meta}

    out_dir.mkdir(parents=True, exist_ok=True)
    chunks = list(_iter_book_chunks(book))
    if not chunks:
        meta = {"chunks": 0, "book": name}
        _atomic_json(out_dir / "ok.json", meta)
        # boş dosyalar
        (out_dir / "chunks.jsonl").write_text("", encoding="utf-8")
        np.save(str(out_dir / "emb.npy"), np.zeros((0, _EMB_DIM), dtype=np.float32))
        return {"status": "empty", **meta}

    model = model or _get_embedder()
    texts = [c.text for c in chunks]
    # bellek: batch batch yaz
    emb_path = out_dir / "emb_write.tmp.npy"
    mm = np.lib.format.open_memmap(
        str(emb_path), mode="w+", dtype=np.float32, shape=(len(texts), _EMB_DIM)
    )
    t0 = time.perf_counter()
    hb_path = _shards_root() / "_heartbeat.json"
    total = len(texts)
    for i in range(0, total, _BATCH):
        batch = texts[i : i + _BATCH]
        mm[i : i + len(batch)] = _embed_texts(model, batch)
        mm.flush()
        done = min(i + len(batch), total)
        # Watchdog büyük kitapta takılma sanmasın: her batch kalp atışı
        _atomic_json(
            hb_path,
            {
                "cat": cat,
                "book": name,
                "done": done,
                "of": total,
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
    del mm
    os.replace(emb_path, out_dir / "emb.npy")

    jl = out_dir / "chunks.jsonl.tmp"
    with jl.open("w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(
                json.dumps({"text": c.text, "source": c.source}, ensure_ascii=False)
                + "\n"
            )
    os.replace(jl, out_dir / "chunks.jsonl")

    meta = {
        "chunks": len(chunks),
        "book": name,
        "seconds": round(time.perf_counter() - t0, 2),
    }
    _atomic_json(out_dir / "ok.json", meta)
    return {"status": "built", **meta}


def _write_offsets(chunks_path: Path, offsets_path: Path, n_lines: int) -> None:
    """Her satırın dosya ofseti (uint64)."""
    off = np.lib.format.open_memmap(
        str(offsets_path.with_suffix(".tmp.npy")),
        mode="w+",
        dtype=np.uint64,
        shape=(n_lines,),
    )
    i = 0
    with chunks_path.open("rb") as f:
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            if not line.strip():
                continue
            if i >= n_lines:
                break
            off[i] = pos
            i += 1
    off.flush()
    del off
    os.replace(offsets_path.with_suffix(".tmp.npy"), offsets_path)
    if i != n_lines:
        raise RuntimeError(f"offset satır uyumsuz: {i} != {n_lines}")


def finalize_category(cat: str) -> dict:
    """Kitap parçalarını tek shard'a birleştir (mmap stream); ready işaretle."""
    books = _book_dirs(cat)
    if not books:
        return {"status": "error", "error": "kategori yok", "cat": cat}

    missing = [b.name for b in books if not _book_done(cat, b.name)]
    if missing:
        return {
            "status": "incomplete",
            "cat": cat,
            "missing_books": len(missing),
            "sample": missing[:5],
        }

    total = 0
    part_meta: list[tuple[str, int]] = []
    for b in books:
        ok = json.loads((_book_part_dir(cat, b.name) / "ok.json").read_text(encoding="utf-8"))
        n = int(ok.get("chunks") or 0)
        part_meta.append((b.name, n))
        total += n

    ready = shard_ready_dir(cat)
    staging = _shards_root() / "_staging" / cat
    if staging.exists():
        import shutil

        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)

    emb_final = staging / "embeddings.npy"
    chunks_final = staging / "chunks.jsonl"
    offsets_final = staging / "chunks.offsets.npy"

    if total == 0:
        np.save(str(emb_final), np.zeros((0, _EMB_DIM), dtype=np.float32))
        chunks_final.write_text("", encoding="utf-8")
        np.save(str(offsets_final), np.zeros((0,), dtype=np.uint64))
    else:
        mm = np.lib.format.open_memmap(
            str(emb_final), mode="w+", dtype=np.float32, shape=(total, _EMB_DIM)
        )
        row = 0
        with chunks_final.open("w", encoding="utf-8", newline="\n") as out_f:
            for name, n in part_meta:
                if n <= 0:
                    continue
                part = _book_part_dir(cat, name)
                arr = np.load(str(part / "emb.npy"), mmap_mode="r")
                if arr.shape != (n, _EMB_DIM):
                    raise RuntimeError(
                        f"{cat}/{name} şekil uyumsuz: {arr.shape} beklenen ({n}, {_EMB_DIM})"
                    )
                mm[row : row + n] = arr
                with (part / "chunks.jsonl").open(encoding="utf-8") as inf:
                    for line in inf:
                        if line.strip():
                            out_f.write(line if line.endswith("\n") else line + "\n")
                row += n
                del arr
        mm.flush()
        del mm
        if row != total:
            raise RuntimeError(f"birleşim satır uyumsuz: {row} != {total}")
        _write_offsets(chunks_final, offsets_final, total)

    digest_src = f"{cat}:{total}:{_MODEL_NAME}"
    manifest = {
        "cat": cat,
        "num_chunks": total,
        "num_books": len(books),
        "model": _MODEL_NAME,
        "dim": _EMB_DIM,
        "knowledge_prefix": f"{_SHAMELA_REL.as_posix()}/{cat}",
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "digest": digest_src,
    }
    _atomic_json(staging / "manifest.json", manifest)

    # Atomik yayın: staging → ready
    import shutil

    if ready.exists():
        bak = ready.with_name(ready.name + ".bak_old")
        if bak.exists():
            shutil.rmtree(bak, ignore_errors=True)
        os.replace(ready, bak)
    ready.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staging, ready)
    # eski yedek temizliği (başarılıysa)
    bak = ready.with_name(ready.name + ".bak_old")
    if bak.exists():
        shutil.rmtree(bak, ignore_errors=True)

    reg = load_registry()
    ready_map = dict(reg.get("ready") or {})
    ready_map[cat] = {
        "chunks": total,
        "books": len(books),
        "path": str(ready),
        "built_at": manifest["built_at"],
    }
    reg["ready"] = ready_map
    save_registry(reg)

    st = load_state()
    cats = dict(st.get("cats") or {})
    cats[cat] = {
        "status": "ready",
        "chunks": total,
        "books": len(books),
        "finished_at": manifest["built_at"],
    }
    st["cats"] = cats
    save_state(st)

    return {"status": "ready", "cat": cat, "chunks": total, "books": len(books)}


def build_category(
    cat: str,
    *,
    finalize: bool = True,
    max_books: int | None = None,
) -> dict:
    """Kategoriyi kitap kitap göm; isteğe bağlı finalize."""
    os.environ.setdefault("RUZGAR_EMBED_DEVICE", "cpu")
    os.environ.setdefault("OMP_NUM_THREADS", "6")
    os.environ.setdefault("MKL_NUM_THREADS", "6")

    books = _book_dirs(cat)
    if not books:
        return {"status": "error", "error": "kategori yok", "cat": cat}
    if max_books is not None:
        books = books[: max(0, int(max_books))]

    st = load_state()
    cats = dict(st.get("cats") or {})
    cats[cat] = {
        **(cats.get(cat) or {}),
        "status": "building",
        "total_books": len(_book_dirs(cat)),
        "started_at": (cats.get(cat) or {}).get("started_at")
        or time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    st["cats"] = cats
    st["current_cat"] = cat
    save_state(st)

    model = _get_embedder()
    built = 0
    cached = 0
    empty = 0
    chunks_sum = 0
    t0 = time.perf_counter()

    for i, book in enumerate(books, 1):
        r = build_book(cat, book, model=model)
        stt = r.get("status")
        if stt == "cached":
            cached += 1
        elif stt == "empty":
            empty += 1
        else:
            built += 1
        chunks_sum += int(r.get("chunks") or 0)
        elapsed = max(time.perf_counter() - t0, 0.001)
        # Her kitapta checkpoint — watchdog ve devam güvenliği
        cats[cat]["progress"] = {
            "done": i,
            "of": len(books),
            "built": built,
            "cached": cached,
            "chunks_seen": chunks_sum,
            "last_book": book.name,
            "last_status": stt,
        }
        st["cats"] = cats
        st["paused"] = False
        save_state(st)
        if i % 5 == 0 or i == len(books) or stt == "built":
            print(
                f"[{cat}] {i}/{len(books)} book={book.name} "
                f"status={stt} chunks={r.get('chunks')} "
                f"rate_books/h={i / elapsed * 3600:.1f}",
                flush=True,
            )

    out: dict = {
        "status": "books_done",
        "cat": cat,
        "built": built,
        "cached": cached,
        "empty": empty,
        "books": len(books),
        "chunks_seen": chunks_sum,
        "seconds": round(time.perf_counter() - t0, 1),
    }
    if finalize:
        fin = finalize_category(cat)
        out["finalize"] = fin
        out["status"] = fin.get("status") or out["status"]
    return out


def cleanup_building(cat: str) -> None:
    """Finalize sonrası building parçalarını sil (disk)."""
    import shutil

    d = shard_building_dir(cat)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def _read_chunk_at(chunks_path: Path, offsets: np.ndarray, i: int) -> Chunk | None:
    try:
        with chunks_path.open("rb") as f:
            f.seek(int(offsets[i]))
            line = f.readline().decode("utf-8")
        o = json.loads(line)
        return Chunk(text=o["text"], source=o["source"])
    except Exception:
        return None


# Sorgu → kategori ipuçları (tüm 40 shard'ı taramak ~12GB mmap; RAM'de sohbeti öldürür)
_CAT_QUERY_HINTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        (
            "hadis",
            "buhari",
            "buhârî",
            "buhârî",
            "muslim",
            "müslim",
            "musned",
            "müsned",
            "sünen",
            "sunen",
            "niyet",
            "sahih",
            "rivayet",
            "isnad",
            "sened",
        ),
        # Küçükten büyüğe — 06/07 tek başına ~1.5GB; önce ince shard
        ("10_hadis_ilimleri", "08_tahric_etraf", "09_ilel_sual", "06_hadis_sunen"),
    ),
    (
        ("tefsir", "ayet", "kur'an", "kuran", "quran", "meal", "sure "),
        ("04_kuran_ilim_usul", "05_tecvid_kiraat", "03_tefsir"),
    ),
    (
        ("fıkıh", "fikih", "hanefi", "şafii", "safii", "maliki", "hanbeli", "fetva", "ibadet"),
        ("22_fetvalar", "18_genel_fikih", "12_fikih_kaideler", "14_hanefi"),
    ),
    (("akaid", "akaîd", "itikad", "kelam", "mezhep"), ("01_akaid", "02_firak_redler")),
    (
        (
            "siyer",
            "peygamber",
            "gazve",
            "megazi",
            "kimdir",
            "sahabe",
            "sahabi",
            "sahâbe",
            "muhammed",
            "resulullah",
            "ebubekir",
            "ebu bekir",
            "hz omer",
            "hz ömer",
            "hz osman",
            "hz ali",
            "hatice",
            "aise",
            "ayse",
            "âişe",
            "hamza",
            "halid",
        ),
        ("24_siyer", "26_teracim", "25_tarih", "23_rekaik_adab"),
    ),
    (("tarih", "halife", "osmanlı", "teracim", "tabakat"), ("25_tarih", "26_teracim")),
    (("nahiv", "sarf", "belagat", "lugat", "garib", "dil "), ("31_nahiv_sarf", "30_garib_lugat", "35_belagat", "29_dil")),
    (("usul", "kıyas", "icma"), ("11_usul_fikih", "12_fikih_kaideler")),
)

# İpucu yoksa: küçük/orta «çekirdek» — asla 40'ı birden açma
_DEFAULT_CORE_CATS: tuple[str, ...] = (
    "06_hadis_sunen",
    "01_akaid",
    "18_genel_fikih",
    "24_siyer",
    "39_genel",
)


def _fold_simple(s: str) -> str:
    import unicodedata

    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    # Türkçe ı/İ NFKD ile düşmez — «hazır mı» → «hazir mi»
    t = t.replace("ı", "i").replace("İ", "i")
    return t.lower()


def pick_shamela_cats_for_query(
    query: str,
    ready: dict | Sequence[str],
    *,
    max_cats: int | None = None,
) -> list[str]:
    """Sorguya göre en fazla N hazır shard seç (bellek/süre koruması)."""
    if max_cats is None:
        try:
            max_cats = int(os.environ.get("RUZGAR_SHAMELA_MAX_CATS", "3") or "3")
        except ValueError:
            max_cats = 3
    max_cats = max(1, min(8, int(max_cats)))
    try:
        max_mb = float(os.environ.get("RUZGAR_SHAMELA_MAX_MB", "700") or "700")
    except ValueError:
        max_mb = 700.0
    max_bytes = max(50.0, max_mb) * 1_000_000.0
    ready_keys = set(ready.keys() if isinstance(ready, dict) else ready)
    if not ready_keys:
        return []

    def _emb_size(cat: str) -> int:
        p = shard_ready_dir(cat) / "embeddings.npy"
        try:
            return int(p.stat().st_size) if p.is_file() else 10**18
        except OSError:
            return 10**18

    low = _fold_simple(query)
    picked: list[str] = []
    used_bytes = 0

    def _add(cat: str, *, force: bool = False) -> bool:
        nonlocal used_bytes
        if cat not in ready_keys or cat in picked:
            return len(picked) >= max_cats
        sz = _emb_size(cat)
        # İlk kategori veya force: büyük shard'a izin; aksi MB bütçesi
        if picked and (not force) and used_bytes + sz > max_bytes:
            return len(picked) >= max_cats
        picked.append(cat)
        used_bytes += sz
        return len(picked) >= max_cats

    # Kitap adı geçiyorsa ilgili büyük sunen shard zorunlu (yoksa yanlış ince shard)
    if any(k in low for k in ("buhari", "buhârî", "muslim", "muslum", "müslim", "sahih")):
        _add("06_hadis_sunen", force=True)
        if "serh" in low or "şerh" in low or "serif" in low:
            _add("07_hadis_serh", force=True)
        _add("10_hadis_ilimleri")
        if len(picked) >= max_cats:
            return picked[:max_cats]

    # «kimdir / hz …» → siyer–teracim–tarih zorunlu (fıkıh/usul gürültüsü olmasın)
    _kimdir = "kimdir" in low or "kim idi" in low or "kimdi" in low
    _siyer_person = _kimdir or any(
        k in low
        for k in (
            "peygamber",
            "resulullah",
            "sahabe",
            "sahabi",
            "siyer",
            "teracim",
            "tabakat",
        )
    ) or (
        re.search(r"\bhz\b", low)
        and any(
            k in low
            for k in (
                "muhammed",
                "ebubekir",
                "omer",
                "osman",
                "ali",
                "hatice",
                "aise",
                "ayse",
                "hamza",
                "halid",
            )
        )
    )
    if _siyer_person:
        for cat in ("24_siyer", "26_teracim", "25_tarih", "23_rekaik_adab"):
            _add(cat, force=True)
        if picked:
            return picked[:max_cats]

    for cues, cats in _CAT_QUERY_HINTS:
        if any(_fold_simple(c) in low for c in cues):
            # İpucu listesini boyuta göre sırala (küçük önce)
            for cat in sorted(cats, key=_emb_size):
                if _add(cat):
                    return picked[:max_cats]

    # Klasör adından kaba eşleşme (örn. «hanefi»)
    for cat in sorted(ready_keys, key=_emb_size):
        token = cat.split("_", 1)[-1].replace("_", " ")
        if token and _fold_simple(token) in low:
            if _add(cat):
                return picked[:max_cats]

    if not picked:
        for cat in sorted(_DEFAULT_CORE_CATS, key=_emb_size):
            if _add(cat):
                break

    # Hâlâ boşsa: en küçük embedding dosyalarından al
    if not picked:
        for cat in sorted(ready_keys, key=_emb_size)[:max_cats]:
            _add(cat)

    return picked[:max_cats]


def search_shamela_shards(
    query: str,
    top_k: int = 5,
    *,
    q_vec: np.ndarray | None = None,
    cats: Sequence[str] | None = None,
) -> List[Tuple[str, str, float]]:
    """Hazır shard'larda mmap kosinüs; sorguya göre az kategori + süre bütçesi."""
    reg = load_registry()
    ready = dict(reg.get("ready") or {})
    if not ready:
        return []
    if cats is None:
        use = pick_shamela_cats_for_query(query, ready)
    else:
        use = [c for c in cats if c in ready]
        if not use:
            use = pick_shamela_cats_for_query(query, ready)
    if not use:
        return []

    def _sz(cat: str) -> int:
        p = shard_ready_dir(cat) / "embeddings.npy"
        try:
            return int(p.stat().st_size) if p.is_file() else 10**18
        except OSError:
            return 10**18

    # Küçük shard önce — süre bütçesi dolmadan en az bir isabet şansı
    use = sorted(use, key=_sz)

    try:
        budget = float(os.environ.get("RUZGAR_SHAMELA_SEARCH_BUDGET_SEC", "20") or "20")
    except ValueError:
        budget = 20.0
    budget = max(5.0, min(45.0, budget))

    # Embedder yükü bütçeye dahil edilmez (yoksa 6sn dolup 0 hit dönüyordu)
    if q_vec is None:
        model = _get_embedder()
        q_vec = np.asarray(
            model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0],
            dtype=np.float32,
        )
    else:
        q_vec = np.asarray(q_vec, dtype=np.float32)

    t0 = time.monotonic()
    tk = max(1, int(top_k))
    per_shard = max(tk, min(12, tk * 2))
    best: dict[tuple[str, str], Tuple[str, str, float]] = {}

    block = int(os.environ.get("RUZGAR_SHAMELA_SCORE_BLOCK", "65536") or "65536")

    for cat in use:
        if best and time.monotonic() - t0 > budget:
            break
        d = shard_ready_dir(cat)
        emb_p = d / "embeddings.npy"
        ch_p = d / "chunks.jsonl"
        off_p = d / "chunks.offsets.npy"
        if not (emb_p.is_file() and ch_p.is_file() and off_p.is_file()):
            continue
        emb = np.load(str(emb_p), mmap_mode="r")
        if emb.ndim != 2 or emb.shape[0] == 0:
            continue
        offsets = np.load(str(off_p), mmap_mode="r")
        if len(offsets) != len(emb):
            continue

        # blok blok skor; shard içi top
        n = emb.shape[0]
        cand_idx: list[int] = []
        cand_sc: list[float] = []
        blocks_done = 0
        for start in range(0, n, block):
            # En az 1 blok her zaman; sonrasında bütçe
            if blocks_done >= 1 and time.monotonic() - t0 > budget:
                break
            end = min(start + block, n)
            sims = emb[start:end] @ q_vec
            take = min(per_shard, end - start)
            if take <= 0:
                continue
            local = np.argpartition(-sims, take - 1)[:take]
            for j in local:
                cand_idx.append(start + int(j))
                cand_sc.append(float(sims[int(j)]))
            blocks_done += 1
        if not cand_idx:
            continue
        order = np.argsort(-np.asarray(cand_sc))[:per_shard]
        for oi in order:
            ii = cand_idx[int(oi)]
            sc = cand_sc[int(oi)]
            ch = _read_chunk_at(ch_p, offsets, ii)
            if ch is None:
                continue
            key = (ch.source, (ch.text or "")[:96])
            prev = best.get(key)
            if prev is None or sc > prev[2]:
                best[key] = (ch.text, ch.source, sc)

    ranked = sorted(best.values(), key=lambda h: h[2], reverse=True)
    # Lexik bonus: soru kelimesi geçen parçayı öne al (yanlış semantik komşu ezmesin)
    try:
        qf = _fold_simple(query)
        q_toks = [t for t in re.findall(r"[a-z0-9']{3,}|[\u0600-\u06ff]{3,}", qf + " " + (query or "")) if len(t) >= 3]
        if "niyet" in qf:
            q_toks.extend(["نية", "نيات", "بالنيات", "الاعمال", "الأعمال"])
        def _lex_bonus(item: Tuple[str, str, float]) -> float:
            text, src, sc = item
            blob = f"{text}\n{src}"
            blob_f = _fold_simple(blob)
            b = 0.0
            for t in q_toks[:20]:
                if t in blob or t in blob_f:
                    b += 0.04
            return float(sc) + min(0.25, b)
        ranked = sorted(ranked, key=_lex_bonus, reverse=True)
    except Exception:
        pass
    return ranked[:tk]


def format_samile_ready_reply() -> str:
    """Sohbet için: indeks hazır mı? — health JSON değil, düz Türkçe."""
    st = public_status()
    total = int(st.get("categories_total") or 0)
    ready_n = int(st.get("categories_ready") or 0)
    pending = list(st.get("pending") or [])
    if st.get("ready") and total > 0 and not pending:
        return (
            f"Evet Ümit abi — Şamile shard indeksi hazır. "
            f"{ready_n}/{total} kategori ready; bekleyen yok. "
            f"İlim sorusu sorarsan bu indeksten bakarım."
        )
    if total <= 0:
        return (
            "Şamile shard tarafında henüz kategori görünmüyor. "
            "İndeks kurulumu tamamlanmamış olabilir."
        )
    pend_s = ", ".join(pending[:8]) + ("…" if len(pending) > 8 else "")
    return (
        f"Şamile indeksi kısmen hazır: {ready_n}/{total} kategori ready. "
        f"Bekleyen: {pend_s or '—'}."
    )


def looks_like_samile_status_question(message: str) -> bool:
    low = _fold_simple(message)
    if not low.strip():
        return False
    has_samile = any(k in low for k in ("samile", "samil", "shamel", "shard"))
    has_status = any(
        k in low
        for k in (
            "hazir mi",
            "ready",
            "indeks",
            "index",
            "durum",
            "calisiyor mu",
        )
    )
    return has_samile and has_status


def status_report() -> dict:
    reg = load_registry()
    st = load_state()
    all_cats = list_categories()
    ready = dict(reg.get("ready") or {})
    return {
        "model": _MODEL_NAME,
        "categories_total": len(all_cats),
        "categories_ready": len(ready),
        "ready": ready,
        "pending": [c for c in all_cats if c not in ready],
        "state": st,
        "main_index_untouched": True,
        "shards_root": str(_shards_root()),
    }


def public_status() -> dict:
    """Health yüzeyi için küçük, kararlı Şamile shard özeti."""
    report = status_report()
    total = int(report.get("categories_total") or 0)
    ready = int(report.get("categories_ready") or 0)
    pending = list(report.get("pending") or [])
    return {
        "ready": total > 0 and ready == total and not pending,
        "categories_total": total,
        "categories_ready": ready,
        "pending": pending,
        "model": report.get("model"),
        "main_index_untouched": bool(report.get("main_index_untouched")),
    }


@dataclass
class LoopResult:
    done: list[str]
    skipped: list[str]
    current: str | None
    last: dict | None


def build_next_pending(*, cleanup: bool = True, max_books: int | None = None) -> dict:
    """Sıradaki hazır olmayan kategoriyi işle."""
    reg = load_registry()
    ready = set((reg.get("ready") or {}).keys())
    for cat in list_categories():
        if cat in ready:
            continue
        # building yarım olabilir — build_category devam eder
        out = build_category(cat, finalize=True, max_books=max_books)
        if out.get("status") == "ready" and cleanup:
            cleanup_building(cat)
        return out
    return {"status": "all_done", **status_report()}
