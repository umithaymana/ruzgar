# -*- coding: utf-8 -*-
"""
Sıra 33 — hafif RAG: yalnız yeni meslek metin paketlerini ana indekse ekler.
Tam incremental (tüm knowledge tarama) 16GB+canlı sunucuda OpenBLAS OOM verdiği için.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.rag_store import (  # noqa: E402
    Chunk,
    _MODEL_NAME,
    _atomic_save_npy,
    _atomic_write_chunks_jsonl,
    _atomic_write_text,
    _get_embedder,
    _index_dir,
    _load_chunks,
    _load_embeddings,
    _split_text,
)

RAF = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"
KEYS = [
    "mimar_bina_3d",
    "yonetmen_kurgu",
    "egitim_anatomi",
    "hukuk_dosya_masa",
    "muzik_partisyon",
    "gazeteci_acik_veri",
    "ciftci_saha",
    "ogrenci_quiz",
    "aile_cihaz",
    "muhendis_sim",
    "gezgin_rehber",
]
REPORT = RAF / "SAHNE_Y1_RAG_MESLEK_RAPOR.json"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT / "knowledge")).replace("\\", "/")


def main() -> int:
    files: list[tuple[str, str]] = []
    for key in KEYS:
        for dal in ("08_yazilim_mi_mari_leri_", "18_bi_li_msel_ara_tirma_y_ntemleri_", "07_si_ber_g_venli_k", "14_fi_zi_k"):
            d = RAF / dal / "metin" / key
            if not d.is_dir():
                continue
            for md in sorted(d.glob("*.md")):
                body = md.read_text(encoding="utf-8", errors="ignore")
                if len(body.strip()) < 40:
                    continue
                files.append((_rel(md), body))
    print("files", len(files), flush=True)
    if not files:
        print("FAIL: dosya yok", flush=True)
        return 1

    idx = _index_dir()
    manifest_path = idx / "manifest.json"
    chunks_path = idx / "chunks.jsonl"
    emb_path = idx / "embeddings.npy"
    old = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    old_digests = dict(old.get("file_digests") or {})

    new_digests: dict[str, str] = {}
    for rel, body in files:
        h = hashlib.sha256()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(body.encode("utf-8"))
        new_digests[rel] = h.hexdigest()

    changed = [rel for rel, fd in new_digests.items() if old_digests.get(rel) != fd]
    print("changed", len(changed), flush=True)
    if not changed:
        print("cached — yeni gömme yok", flush=True)
        REPORT.write_text(
            json.dumps({"status": "cached", "files": len(files), "chunks": old.get("num_chunks")}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return 0

    old_chunks = _load_chunks()
    old_emb = _load_embeddings()
    if not old_chunks or old_emb is None or len(old_chunks) != len(old_emb):
        print("FAIL: ana indeks okunamadı / uyumsuz — tam incremental sonra", flush=True)
        return 2

    changed_set = set(changed)
    keep_i = []
    kept = []
    for i, c in enumerate(old_chunks):
        if c.source in changed_set:
            continue
        keep_i.append(i)
        kept.append(c)
    keep_emb = old_emb[keep_i] if keep_i else old_emb[:0]

    new_chunks: list[Chunk] = []
    payload = {rel: body for rel, body in files}
    for rel in sorted(changed):
        for piece in _split_text(payload[rel]):
            new_chunks.append(Chunk(text=piece, source=rel))
    print("new_chunks", len(new_chunks), flush=True)

    model = _get_embedder()
    batch = 24
    import numpy as np

    parts = []
    texts = [c.text for c in new_chunks]
    for i in range(0, len(texts), batch):
        sl = texts[i : i + batch]
        print(f"embed {i}-{i+len(sl)}/{len(texts)}", flush=True)
        parts.append(model.encode(sl, normalize_embeddings=True, show_progress_bar=False))
    emb_new = np.vstack(parts) if parts else None
    if emb_new is None:
        emb_out = keep_emb
    else:
        emb_out = np.vstack([keep_emb, emb_new]) if len(keep_i) else emb_new

    chunks_out = kept + new_chunks
    old_digests.update(new_digests)
    # digest: hafif — file_digests birleşik hash
    overall = hashlib.sha256()
    for rel in sorted(old_digests.keys()):
        overall.update(rel.encode("utf-8"))
        overall.update(old_digests[rel].encode("utf-8"))
    digest = overall.hexdigest()

    _atomic_save_npy(emb_path, emb_out)
    _atomic_write_chunks_jsonl(chunks_path, chunks_out)
    _atomic_write_text(
        manifest_path,
        json.dumps(
            {
                "digest": digest,
                "num_chunks": len(chunks_out),
                "model": _MODEL_NAME,
                "file_digests": old_digests,
                "sahne_y1_meslek_rag": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    rep = {
        "status": "incremental_meslek",
        "files_changed": len(changed),
        "new_chunks": len(new_chunks),
        "total_chunks": len(chunks_out),
        "model": _MODEL_NAME,
    }
    REPORT.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("REPORT", REPORT, rep, flush=True)
    print("SMOKE_SAHNE_RAG_MESLEK=PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
