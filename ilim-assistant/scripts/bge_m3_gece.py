"""Gece işi — bge-m3 indir, Şâmile'yi YAN indekse göm.

Canlı MiniLM shard'larına ve ana `.rag_index/embeddings.npy` dosyasına DOKUNMAZ.
Çıktı: `.rag_index/shards/shamela_bge_m3/<kategori>/embeddings.npy`
Arama kodu bu dosyayı kendiliğinden kullanmaz; geçiş ayrı onaydır.

Kaldığı yerden sürer (kategori başına `ilerleme.json`).
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".rag_index" / "shards" / "shamela"
DST = ROOT / ".rag_index" / "shards" / "shamela_bge_m3"
LOG = DST / "gece.log"
MODEL_ID = "BAAI/bge-m3"
DIM = 1024
BATCH = 16


def log(msg: str) -> None:
    DST.mkdir(parents=True, exist_ok=True)
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " " + msg
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def count_lines(path: Path) -> int:
    n = 0
    with path.open("rb") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def embed_shard(model, cat: str) -> str:
    src = SRC / cat
    chunks = src / "chunks.jsonl"
    if not chunks.is_file():
        return "chunks yok"
    out_dir = DST / cat
    out_dir.mkdir(parents=True, exist_ok=True)
    emb_path = out_dir / "embeddings.npy"
    prog_path = out_dir / "ilerleme.json"
    n = count_lines(chunks)
    done = 0
    if prog_path.is_file():
        try:
            done = int(json.loads(prog_path.read_text(encoding="utf-8")).get("done") or 0)
        except Exception:
            done = 0
    if emb_path.is_file() and done >= n > 0:
        return f"hazır {n}"
    if done > 0 and not emb_path.is_file():
        done = 0
    emb = np.lib.format.open_memmap(
        emb_path, mode="w+" if done == 0 else "r+", dtype=np.float32, shape=(n, DIM)
    )
    batch_txt: list[str] = []
    seen = 0
    t0 = time.time()
    with chunks.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if seen < done:
                seen += 1
                continue
            try:
                batch_txt.append(json.loads(line)["text"])
            except Exception:
                batch_txt.append("")
            seen += 1
            if len(batch_txt) >= BATCH:
                vec = model.encode(batch_txt, batch_size=BATCH, normalize_embeddings=True, show_progress_bar=False)
                emb[done : done + len(batch_txt)] = np.asarray(vec, dtype=np.float32)
                done += len(batch_txt)
                batch_txt = []
                emb.flush()
                prog_path.write_text(json.dumps({"done": done, "n": n}), encoding="utf-8")
                if done % 2000 < BATCH:
                    log(f"  {cat} {done}/{n} · {time.time() - t0:.0f} sn")
    if batch_txt:
        vec = model.encode(batch_txt, batch_size=BATCH, normalize_embeddings=True, show_progress_bar=False)
        emb[done : done + len(batch_txt)] = np.asarray(vec, dtype=np.float32)
        done += len(batch_txt)
        emb.flush()
    prog_path.write_text(json.dumps({"done": done, "n": n, "bitti": True}), encoding="utf-8")
    del emb
    return f"bitti {done}"


def main() -> int:
    log("başladı")
    try:
        from sentence_transformers import SentenceTransformer
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        log(f"cihaz {device} · model iniyor: {MODEL_ID}")
        model = SentenceTransformer(MODEL_ID, device=device)
        dim = int(model.get_sentence_embedding_dimension())
        if dim != DIM:
            log(f"HATA boyut {dim} beklenen {DIM}")
            return 2
        reg = json.loads((SRC / "registry.json").read_text(encoding="utf-8"))
        cats = sorted((reg.get("ready") or {}).keys())
        log(f"kategori {len(cats)}")
        for i, cat in enumerate(cats, 1):
            log(f"[{i}/{len(cats)}] {cat}")
            try:
                log("  " + embed_shard(model, cat))
            except RuntimeError as e:
                if "out of memory" in str(e).lower() and device == "cuda":
                    log("VRAM doldu, CPU'ya geçiliyor")
                    torch.cuda.empty_cache()
                    model = SentenceTransformer(MODEL_ID, device="cpu")
                    device = "cpu"
                    log("  " + embed_shard(model, cat))
                else:
                    raise
        log("TÜMÜ BİTTİ · canlı arama hâlâ MiniLM · geçiş ayrı onay")
        return 0
    except Exception:
        log("HATA\n" + traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
