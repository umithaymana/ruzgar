# -*- coding: utf-8 -*-
"""
Sıra 33 — meslek paketleri için yan indeks (.rag_index/sahne_y1/).
Ana chunks.jsonl (589MB) canlı sunucu+Unicode yolda OSError verdi; yan indeks güvenli.
Ana birleşim: sessiz RAM penceresinde _sahne_y1_rag_meslek_ekle.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from ilim_assistant.rag_store import Chunk, _MODEL_NAME, _get_embedder, _split_text  # noqa: E402

RAF = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"
OUT = ROOT / ".rag_index" / "sahne_y1"
REPORT = RAF / "SAHNE_Y1_RAG_SIDECAR_RAPOR.json"
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
DALS = (
    "08_yazilim_mi_mari_leri_",
    "18_bi_li_msel_ara_tirma_y_ntemleri_",
    "07_si_ber_g_venli_k",
    "14_fi_zi_k",
)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files: list[tuple[str, str]] = []
    for key in KEYS:
        for dal in DALS:
            d = RAF / dal / "metin" / key
            if not d.is_dir():
                continue
            for md in sorted(d.glob("*.md")):
                body = md.read_text(encoding="utf-8", errors="ignore")
                if len(body.strip()) < 40:
                    continue
                rel = str(md.relative_to(ROOT / "knowledge")).replace("\\", "/")
                files.append((rel, body))
    print("files", len(files), flush=True)
    chunks: list[Chunk] = []
    digests: dict[str, str] = {}
    for rel, body in files:
        h = hashlib.sha256((rel + "\0" + body).encode("utf-8")).hexdigest()
        digests[rel] = h
        for piece in _split_text(body):
            chunks.append(Chunk(text=piece, source=rel))
    print("chunks", len(chunks), flush=True)
    model = _get_embedder()
    batch = 32
    parts = []
    texts = [c.text for c in chunks]
    for i in range(0, len(texts), batch):
        sl = texts[i : i + batch]
        print(f"embed {i}-{i+len(sl)}/{len(texts)}", flush=True)
        parts.append(model.encode(sl, normalize_embeddings=True, show_progress_bar=False))
    emb = np.vstack(parts)
    np.save(OUT / "embeddings.npy", emb)
    with (OUT / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({"text": c.text, "source": c.source}, ensure_ascii=False) + "\n")
    man = {
        "num_chunks": len(chunks),
        "model": _MODEL_NAME,
        "file_digests": digests,
        "kind": "sahne_y1_sidecar",
        "note": "Ana indekse birleşim sonra; arama köprüsü ayrı dilimde",
    }
    (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps({"status": "sidecar_ok", **{k: man[k] for k in ("num_chunks", "model")}}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SIDECAR", OUT, "chunks", len(chunks), flush=True)
    print("SMOKE_SAHNE_RAG_SIDECAR=PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
