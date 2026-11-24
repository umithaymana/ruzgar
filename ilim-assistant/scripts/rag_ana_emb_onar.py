"""Ana RAG indeksinde embeddings.npy kayıpsa, MEVCUT chunks.jsonl'dan yeniden gömer (onarım).

- chunks.jsonl / manifest.json'a DOKUNMAZ; yeniden parçalama yok; aynı model (manifest.model).
- Çıktı: .rag_index/embeddings.npy (atomik yazım). Zaten varsa --zorla olmadan çıkar.
- Cihaz: varsayılan cuda (yoksa cpu). Ollama/XTTS VRAM'i kullanıyorsa RUZGAR_EMBED_DEVICE=cpu verilebilir.

Kullanım:  python scripts/rag_ana_emb_onar.py [--cihaz cuda|cpu] [--zorla]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cihaz", default="cuda")
    ap.add_argument("--zorla", action="store_true")
    ap.add_argument("--batch", type=int, default=128)
    a = ap.parse_args()

    from ilim_assistant import rag_store as R

    idx = R._index_dir()
    emb_p, ch_p, man_p = idx / "embeddings.npy", idx / "chunks.jsonl", idx / "manifest.json"
    if emb_p.is_file() and not a.zorla:
        print("embeddings.npy zaten var; çıkıldı:", emb_p)
        return 0
    man = json.loads(man_p.read_text(encoding="utf-8"))
    n_exp = int(man.get("num_chunks") or 0)
    model_name = man.get("model") or R._MODEL_NAME
    texts: list[str] = []
    with ch_p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                texts.append(json.loads(line)["text"])
    print(f"parça: {len(texts)} (manifest {n_exp}) · model: {model_name}", flush=True)
    if len(texts) != n_exp:
        print("HATA: chunks.jsonl satır sayısı manifest ile uyuşmuyor; durdum.")
        return 2

    from sentence_transformers import SentenceTransformer

    dev = a.cihaz
    try:
        import torch

        if dev == "cuda" and not torch.cuda.is_available():
            dev = "cpu"
    except Exception:
        dev = "cpu"
    model = SentenceTransformer(model_name, device=dev)
    if dev == "cuda":
        model.half()  # VRAM/hız; kosinüs için fark ihmal edilir, çıktı float32'ye çevrilir
    print("cihaz:", dev, flush=True)

    out = np.zeros((len(texts), int(model.get_sentence_embedding_dimension())), dtype=np.float32)
    t0 = time.time()
    step = 20000
    for s in range(0, len(texts), step):
        e = min(s + step, len(texts))
        v = model.encode(
            texts[s:e], batch_size=a.batch, normalize_embeddings=True, show_progress_bar=False
        )
        out[s:e] = np.asarray(v, dtype=np.float32)
        el = time.time() - t0
        print(f"{e}/{len(texts)} · {el:.0f} sn · kalan ~{el / e * (len(texts) - e):.0f} sn", flush=True)
    R._atomic_save_npy(emb_p, out)
    print("yazıldı:", emb_p, out.shape, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
