# -*- coding: utf-8 -*-
"""Mevcut chunks.jsonl ile embeddings.npy satır sayısını hizala.

Tam markdown taraması yapmaz. Uzun iş yarıda kalırsa aynı dosyadan devam eder.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "6")
os.environ.setdefault("MKL_NUM_THREADS", "6")
os.environ.setdefault("RUZGAR_EMBED_DEVICE", "cpu")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(6)

from ilim_assistant.rag_store import _get_embedder, _index_dir  # noqa: E402

BATCH = 128
WINDOW = 1024


def _count_lines(path: Path) -> int:
    n = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def main() -> int:
    idx = _index_dir()
    chunks_path = idx / "chunks.jsonl"
    final_path = idx / "embeddings.npy"
    rebuild_path = idx / "embeddings_rebuild.npy"
    progress_path = idx / "embeddings_rebuild.progress"
    if not chunks_path.is_file():
        print("chunks.jsonl yok", flush=True)
        return 1

    n = _count_lines(chunks_path)
    print(f"chunks {n}", flush=True)
    if n < 1:
        print("chunk yok", flush=True)
        return 1

    start = 0
    if rebuild_path.is_file() and progress_path.is_file():
        try:
            done = int(progress_path.read_text(encoding="utf-8").strip() or "0")
            old = np.load(str(rebuild_path), mmap_mode="r")
            if old.shape == (n, 384) and 0 <= done <= n:
                start = done
                print(f"devam {start}/{n}", flush=True)
            del old
        except Exception as exc:
            print(f"eski yarim indeks atlandi: {exc}", flush=True)
            start = 0

    if start == 0:
        if rebuild_path.is_file():
            rebuild_path.unlink()
        mm = np.lib.format.open_memmap(
            str(rebuild_path), mode="w+", dtype=np.float32, shape=(n, 384)
        )
    else:
        mm = np.load(str(rebuild_path), mmap_mode="r+")

    model = _get_embedder()
    buf: list[str] = []
    seen = 0
    t0 = time.perf_counter()

    def flush(texts: list[str], at: int) -> None:
        if not texts:
            return
        arr = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=BATCH,
        )
        arr = np.asarray(arr, dtype=np.float32)
        mm[at : at + len(texts)] = arr
        mm.flush()
        progress_path.write_text(str(at + len(texts)), encoding="utf-8")
        done_n = at + len(texts)
        elapsed = max(time.perf_counter() - t0, 0.001)
        rate = (done_n - start) / elapsed if done_n > start else 0.0
        left = (n - done_n) / rate if rate else 0.0
        print(
            f"gombu {done_n}/{n}  {rate:.0f}/sn  kalan {left/60:.1f} dk",
            flush=True,
        )

    with chunks_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            if seen < start:
                seen += 1
                continue
            buf.append(json.loads(line)["text"])
            if len(buf) >= WINDOW:
                flush(buf, seen)
                seen += len(buf)
                buf = []
        if buf:
            flush(buf, seen)
            seen += len(buf)

    if seen != n:
        print(f"satir uyusmadi {seen} != {n}", flush=True)
        return 1

    mm.flush()
    del mm
    wrote = np.load(str(rebuild_path), mmap_mode="r")
    if wrote.shape != (n, 384):
        print(f"sekil hatali {wrote.shape}", flush=True)
        return 1
    if not np.isfinite(wrote[:8]).all():
        print("gombu sayilari bozuk", flush=True)
        return 1
    del wrote

    os.replace(str(rebuild_path), str(final_path))
    progress_path.unlink(missing_ok=True)
    print(f"TAMAM embeddings {n} x 384", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
