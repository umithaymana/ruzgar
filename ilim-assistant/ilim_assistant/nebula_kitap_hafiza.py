# Created by Ümit & Gökçenur
"""
Nebula — yapılandırılmış kitap / ansiklopedi hafızası.

Politika (Mimar ile netleşen):
- Sohbet: yalnızca «hatırla / profil» → `ruzgar_genel_hafiza.json` (kisisel_hafiza).
- Devasa kaynaklar: ayrı komutla dosya okunur; konu/başlık paketleri halinde
  `knowledge/nebula/<koleksiyon>/incremental/` altına yazılır + RAG indeksi güncellenir.
  Büyük dosyalar **arka planda** yüklenir (sohbet 120 sn zaman aşımına düşmez).
"""

from __future__ import annotations

import json
import os
import re
import threading
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from ilim_assistant.rag_store import _KNOWLEDGE_ROOT, build_index

_PKG_ROOT = Path(__file__).resolve().parent.parent
_NEBULA_ROOT = _KNOWLEDGE_ROOT / "nebula"
_RAG_STATE = _PKG_ROOT / ".rag_index"
_DEFAULT_BATCH = 400
_ASYNC_MIN_BYTES = int(os.environ.get("RUZGAR_NEBULA_ASYNC_MIN_BYTES", "350000"))

_PATH_RE = re.compile(
    r"(?P<p>"
    r"(?:[A-Za-z]:)?"
    r"(?:[\\/][\w.\-\s\u00c0-\u024f\u1e00-\u1eff]+)+"
    r"\.(?:txt|json|md|tab|tsv)"
    r"|"
    r"knowledge[\\/][\w.\-\s\u00c0-\u024f\u1e00-\u1eff\\/]+"
    r"\.(?:txt|json|md|tab|tsv)"
    r")",
    re.IGNORECASE | re.UNICODE,
)

_BULK_INTENT = re.compile(
    r"(?is)"
    r"(?:"
    r"haf[ıi]zana\s+(?:kaydet|al|yaz|öğren|ogren)"
    r"|(?:kitab[ıi]?n?[ıi]?|dosyas?[ıi]?n?[ıi]?|kaynağ[ıi]?n?[ıi]?|kaynag[ıi]?n?[ıi]?)"
    r"\s+.*?(?:oku|öğren|ogren|kaydet|indeksle|haf[ıi]zana)"
    r"|\.(?:txt|json|md)\s+dosyas[ıi]n[ıi]\s+oku"
    r"|(?:oku\s+ve\s+)?haf[ıi]zana\s+kaydet"
    r"|nebula(?:ya)?\s+(?:kaydet|al|öğren)"
    r")",
)

_job_lock = threading.Lock()
_bg_job: dict[str, Any] = {"running": False}


def is_nebula_kitap_intent(message: str) -> bool:
    """Dosya yolu + kitap/ansiklopedi yükleme niyeti (kişisel «hatırla»dan ayır)."""
    raw = (message or "").strip()
    if not raw or not _BULK_INTENT.search(raw):
        return False
    return _extract_path_from_message(raw) is not None


def get_background_job_status() -> dict[str, Any]:
    with _job_lock:
        return dict(_bg_job)


def _slug(name: str, max_len: int = 48) -> str:
    t = unicodedata.normalize("NFKC", (name or "").strip()).casefold()
    t = re.sub(r"[^\w\s\-]", "", t, flags=re.UNICODE)
    t = re.sub(r"[\s\-]+", "-", t).strip("-")
    return (t[:max_len] or "koleksiyon")[:max_len]


def _parse_line_record(line: str) -> tuple[str, str] | None:
    s = (line or "").strip()
    if not s or s.startswith("#"):
        return None
    if "\t" in s:
        a, b = s.split("\t", 1)
    elif "|" in s:
        a, b = s.split("|", 1)
    elif "=" in s and not s.startswith("="):
        a, b = s.split("=", 1)
    else:
        return None
    title, body = a.strip(), b.strip()
    if not title:
        return None
    return title, body or "(Metin boş)"


def _iter_entries_from_path(src: Path) -> Iterator[tuple[str, str]]:
    if src.suffix.lower() == ".json":
        data = json.loads(src.read_text(encoding="utf-8"))
        entries = data.get("entries", data) if isinstance(data, dict) else data
        if not isinstance(entries, list):
            raise ValueError("JSON: 'entries' dizisi veya liste bekleniyor.")
        for item in entries:
            if isinstance(item, dict):
                title = str(item.get("title") or item.get("baslik") or "").strip()
                body = str(
                    item.get("body")
                    or item.get("metin")
                    or item.get("description")
                    or ""
                ).strip()
                if title:
                    yield title, body or "(Metin boş)"
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                yield str(item[0]).strip(), str(item[1]).strip()
        return

    if src.suffix.lower() == ".md":
        text = src.read_text(encoding="utf-8")
        parts = re.split(r"(?m)^##\s+", text)
        if len(parts) <= 1:
            for line in text.splitlines():
                rec = _parse_line_record(line)
                if rec:
                    yield rec
            return
        for block in parts[1:]:
            lines = block.strip().splitlines()
            if not lines:
                continue
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            if title:
                yield title, body or "(Metin boş)"
        return

    for line in src.read_text(encoding="utf-8").splitlines():
        rec = _parse_line_record(line)
        if rec:
            yield rec


def _batch_markdown(
    entries: list[tuple[str, str]],
    batch_index: int,
    collection: str,
    source_name: str,
) -> str:
    head = (
        f"# Nebula — {collection}\n\n"
        f"- Paket: `{batch_index:05d}`\n"
        f"- Kayıt: **{len(entries)}**\n"
        f"- Kaynak dosya: `{source_name}`\n"
        f"- Yükleme (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n"
        "---\n\n"
    )
    parts = [head]
    for title, body in entries:
        safe_title = title.replace("\n", " ").strip()[:500]
        parts.append(f"## {safe_title}\n{body.strip()}\n\n")
    return "".join(parts)


def _already_in_tarih_hafiza(src: Path) -> str | None:
    """tarih_kaynak_buyuk.json zaten TARIH_VE_KULTUR protokolünde indekslendiyse anında bilgi."""
    name = src.name.casefold()
    if "tarih_kaynak_buyuk" not in name and "tarih_kaynak" not in name:
        return None
    state_path = _RAG_STATE / "tarih_protocol_state.json"
    if not state_path.is_file():
        return None
    try:
        st = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if st.get("status") != "complete":
        return None
    lines = int(st.get("lines_ingested") or 0)
    batches = int(st.get("batches_written") or 0)
    if lines < 1000:
        return None
    return (
        f"Mimar, **{src.name}** zaten tarih hafızasında — **{lines}** kayıt, "
        f"**{batches}** paket (`knowledge/TARIH_VE_KULTUR/incremental/`). "
        f"RAG indeksinde aranır; aynı dosyayı tekrar yüklemene gerek yok. "
        f"Doğrudan tarih sorusu sor (ör. Osmanlı, İstanbul tarihi). "
        f"İsteğe bağlı nebula kopyası için mesajına **zorla nebula** ekle."
    )


def _force_nebula_copy(message: str) -> bool:
    return bool(re.search(r"(?i)zorla\s+nebula", message or ""))


def ingest_structured_source(
    source: Path,
    *,
    batch_size: int = _DEFAULT_BATCH,
    collection_slug: str | None = None,
    rebuild_index: bool = True,
) -> dict[str, Any]:
    """Tek dosyayı başlık/konu paketlerine bölerek nebula klasörüne yazar."""
    src = Path(source).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Dosya bulunamadı: {src}")

    slug = collection_slug or _slug(src.stem)
    out_dir = _NEBULA_ROOT / slug / "incremental"
    out_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(out_dir.glob("nebula_batch_*.md"))
    batch_no = len(existing)
    total = 0
    batch: list[tuple[str, str]] = []

    for title, body in _iter_entries_from_path(src):
        batch.append((title, body))
        if len(batch) >= batch_size:
            path = out_dir / f"nebula_batch_{batch_no:05d}.md"
            path.write_text(
                _batch_markdown(batch, batch_no, slug, src.name),
                encoding="utf-8",
            )
            batch_no += 1
            total += len(batch)
            batch = []

    if batch:
        path = out_dir / f"nebula_batch_{batch_no:05d}.md"
        path.write_text(
            _batch_markdown(batch, batch_no, slug, src.name),
            encoding="utf-8",
        )
        total += len(batch)
        batch_no += 1

    if total == 0:
        raise ValueError(
            "Kayıt çıkarılamadı. Desteklenen biçimler: "
            "satır başına `Başlık<TAB>Metin`, JSON `entries`, veya `## Başlık` Markdown."
        )

    info: dict[str, Any] = {"status": "skipped", "chunks": "?"}
    if rebuild_index:
        info = build_index(force=False, incremental=True)

    meta_path = _NEBULA_ROOT / slug / "meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(
            {
                "collection": slug,
                "source_file": str(src),
                "records_ingested": total,
                "batches": batch_no,
                "last_ingest_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "index": info,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "collection": slug,
        "records": total,
        "batches": batch_no,
        "out_dir": str(out_dir),
        "index": info,
    }


def _format_done_reply(stats: dict[str, Any]) -> str:
    idx = stats.get("index") or {}
    return (
        f"Tamam Mimar — **{stats['records']}** kaydı **{stats['batches']}** paket halinde "
        f"`knowledge/nebula/{stats['collection']}/` altına yazdım. "
        f"İndeks: {idx.get('status', '?')} ({idx.get('chunks', '?')} parça). "
        f"Tarih sorularında RAG bu havuzu da kullanır."
    )


def _start_background_ingest(src: Path, batch_size: int) -> str:
    global _bg_job
    with _job_lock:
        if _bg_job.get("running"):
            prog = _bg_job.get("progress") or ""
            return (
                f"Mimar, arka planda yükleme zaten sürüyor: `{_bg_job.get('source_name', '?')}`. "
                f"{prog} Bittiğinde sohbette «nebula durum» yazabilirsin."
            )
        _bg_job = {
            "running": True,
            "source_name": src.name,
            "source_path": str(src),
            "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "progress": "Paketler yazılıyor…",
            "error": None,
            "stats": None,
        }

    def _worker() -> None:
        global _bg_job
        try:
            with _job_lock:
                _bg_job["progress"] = "Kayıtlar paketleniyor…"
            stats = ingest_structured_source(src, batch_size=batch_size)
            with _job_lock:
                _bg_job.update(
                    running=False,
                    progress="Tamamlandı",
                    stats=stats,
                    finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                )
        except Exception as exc:
            with _job_lock:
                _bg_job.update(running=False, error=str(exc), progress="Hata")

    threading.Thread(target=_worker, daemon=True, name="nebula-ingest").start()
    mb = max(1, round(src.stat().st_size / (1024 * 1024), 1))
    return (
        f"Mimar, **{src.name}** (~{mb} MB) arka planda hafızaya alınıyor — "
        f"bu turda beklemene gerek yok (2–8 dk sürebilir, indeks dahil). "
        f"Bitince «nebula durum» yaz veya doğrudan tarih sorusu sor. "
        f"Not: `tarih_kaynak_buyuk.json` zaten `TARIH_VE_KULTUR` içindeyse tekrar yüklemeye gerek yoktu."
    )


def _resolve_source_path(raw: str) -> Path | None:
    p = Path(raw.strip().strip('"').strip("'"))
    candidates = [
        p,
        _PKG_ROOT / p,
        _KNOWLEDGE_ROOT / p,
        _PKG_ROOT / "knowledge" / p.name if p.name else None,
    ]
    for c in candidates:
        if c is None:
            continue
        try:
            r = c.resolve()
        except OSError:
            continue
        if r.is_file():
            return r
    return None


def _extract_path_from_message(message: str) -> Path | None:
    for m in _PATH_RE.finditer(message):
        resolved = _resolve_source_path(m.group("p"))
        if resolved:
            return resolved
    return None


def try_consume_nebula_status_command(message: str) -> str | None:
    raw = (message or "").strip().casefold()
    if raw not in ("nebula durum", "nebula durumu", "kitap durum", "yükleme durumu"):
        return None
    j = get_background_job_status()
    if j.get("running"):
        return (
            f"Mimar, arka plan yüklemesi sürüyor: **{j.get('source_name', '?')}** — "
            f"{j.get('progress', '…')}"
        )
    if j.get("error"):
        return f"Mimar, son yükleme hatası: {j['error']}"
    if j.get("stats"):
        return _format_done_reply(j["stats"])
    return "Mimar, arka planda aktif kitap yüklemesi yok. Son iş tamamlanmış veya henüz başlatılmamış."


def try_consume_nebula_kitap_command(message: str) -> str | None:
    """
    Devasa kaynak: anında cevap (zaten indeksli / arka plan). Küçük dosya: senkron.
    """
    raw = (message or "").strip()
    if not raw or len(raw) > 4000:
        return None

    st = try_consume_nebula_status_command(raw)
    if st:
        return st

    if not is_nebula_kitap_intent(raw):
        return None

    src = _extract_path_from_message(raw)
    if src is None:
        return (
            "Mimar, kitabı veya ansiklopedi dosyasını hafızama düzenli yazmam için "
            "tam yolunu veya `knowledge/...` göreli yolunu mesajına ekle "
            "(ör. `.txt`, `.json`, `.md`)."
        )

    if not _force_nebula_copy(raw):
        already = _already_in_tarih_hafiza(src)
        if already:
            return already

    try:
        batch_raw = (os.environ.get("RUZGAR_NEBULA_BATCH_SIZE") or "").strip()
        batch_size = int(batch_raw) if batch_raw else _DEFAULT_BATCH
    except ValueError:
        batch_size = _DEFAULT_BATCH
    batch_size = max(50, min(batch_size, 2000))

    try:
        size = src.stat().st_size
    except OSError as exc:
        return f"Mimar, dosyaya erişemedim: {exc}"

    if size >= _ASYNC_MIN_BYTES:
        return _start_background_ingest(src, batch_size)

    try:
        stats = ingest_structured_source(src, batch_size=batch_size)
    except Exception as exc:
        return f"Mimar, dosyayı hafızaya alamadım: {exc}"

    return _format_done_reply(stats)
