# -*- coding: utf-8 -*-
"""Bilgisayar RAG yeniden indeks — ilerleme + checkpoint (EN SONDA).

Kesilirse aynı chunk sayısında EMBED kaldığı yerden devam eder.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ilim_assistant.rag_store import Chunk, _MODEL_NAME, _get_embedder, _split_text
from ilim_assistant.ruzgar_bilgisayar_rag import (
    VERSION,
    _iter_md_files,
    _pkg,
    index_dir,
    promote_staging,
    public_status,
    source_root,
)

BATCH = 96
CKPT_EVERY = 4096  # satır
WORK = _pkg() / ".rag_index_bilgisayar_work"


def _save_ckpt(done: int, n_chunks: int, dim: int) -> None:
    meta = {
        "done": done,
        "n_chunks": n_chunks,
        "dim": dim,
        "model": _MODEL_NAME,
        "version": VERSION,
    }
    (WORK / "ckpt.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except Exception:
        pass

    print("RAG_BUILD_START", flush=True)
    files = _iter_md_files()
    print(f"FILES {len(files)} root={source_root()}", flush=True)

    chunks: list[Chunk] = []
    dals: set[str] = set()
    t0 = time.time()
    for n, path in enumerate(files, 1):
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            rel = str(path.relative_to(_pkg() / "knowledge")).replace("\\", "/")
        except ValueError:
            rel = str(path).replace("\\", "/")
        parts = path.parts
        for i, p in enumerate(parts):
            if p == "bilgisayar_eserleri" and i + 1 < len(parts):
                dals.add(parts[i + 1])
                break
        for piece in _split_text(body):
            chunks.append(Chunk(text=piece, source=rel))
        if n % 500 == 0 or n == len(files):
            print(
                f"CHUNK {n}/{len(files)} chunks={len(chunks)} elapsed={time.time()-t0:.0f}s",
                flush=True,
            )

    n_chunks = len(chunks)
    if n_chunks == 0:
        print("RAG_BUILD_RESULT", json.dumps({"ok": False, "error": "chunk yok"}), flush=True)
        return 1

    WORK.mkdir(parents=True, exist_ok=True)
    chunks_path = WORK / "chunks.jsonl"
    emb_path = WORK / "embeddings.npy"
    ckpt_path = WORK / "ckpt.json"

    # Chunk listesini yaz (resume için sabit kaynak)
    with chunks_path.open("w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(json.dumps({"text": c.text, "source": c.source}, ensure_ascii=False) + "\n")

    print(f"EMBED_START chunks={n_chunks} model={_MODEL_NAME}", flush=True)
    model = _get_embedder()
    # dim öğren
    probe = model.encode([chunks[0].text], normalize_embeddings=True, show_progress_bar=False)
    dim = int(np.asarray(probe).shape[-1])

    start = 0
    if ckpt_path.is_file() and emb_path.is_file():
        try:
            meta = json.loads(ckpt_path.read_text(encoding="utf-8"))
            if (
                int(meta.get("n_chunks", -1)) == n_chunks
                and int(meta.get("dim", -1)) == dim
                and meta.get("model") == _MODEL_NAME
            ):
                start = int(meta.get("done", 0))
                print(f"RESUME from {start}/{n_chunks}", flush=True)
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            start = 0

    if start <= 0 or not emb_path.is_file():
        # yeni memmap
        emb = np.lib.format.open_memmap(
            str(emb_path), mode="w+", dtype=np.float32, shape=(n_chunks, dim)
        )
        start = 0
        _save_ckpt(0, n_chunks, dim)
    else:
        emb = np.lib.format.open_memmap(str(emb_path), mode="r+")

    texts = [c.text for c in chunks]
    for i in range(start, n_chunks, BATCH):
        end = min(i + BATCH, n_chunks)
        vec = model.encode(
            texts[i:end],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        emb[i:end] = np.asarray(vec, dtype=np.float32)
        done = end
        if done % CKPT_EVERY < BATCH or done == n_chunks:
            emb.flush()
            _save_ckpt(done, n_chunks, dim)
            print(f"EMBED {done}/{n_chunks} elapsed={time.time()-t0:.0f}s", flush=True)

    emb.flush()
    del emb

    # Staging → swap
    staging = _pkg() / ".rag_index_bilgisayar_staging"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    shutil.copy2(chunks_path, staging / "chunks.jsonl")
    # memmap dosyasını kopyala
    shutil.copy2(emb_path, staging / "embeddings.npy")
    payload = {
        "ok": True,
        "version": VERSION,
        "num_chunks": n_chunks,
        "num_files": len(files),
        "model": _MODEL_NAME,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": str(source_root()),
        "dals": sorted(dals),
    }
    (staging / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    out = index_dir()
    bak = _pkg() / ".rag_index_bilgisayar_bak"
    if bak.exists():
        shutil.rmtree(bak, ignore_errors=True)
    swapped = False
    try:
        if out.exists():
            os.replace(out, bak)
        os.replace(staging, out)
        swapped = True
        shutil.rmtree(bak, ignore_errors=True)
    except OSError as e:
        payload["swap_error"] = f"{type(e).__name__}: {e}"
        payload["staging"] = str(staging)
    payload["swapped"] = swapped
    print("RAG_BUILD_RESULT", json.dumps(payload, ensure_ascii=False), flush=True)
    if not swapped:
        p = promote_staging()
        print("RAG_PROMOTE", json.dumps(p, ensure_ascii=False), flush=True)

    # work temizle (başarılı swap sonrası)
    if swapped:
        shutil.rmtree(WORK, ignore_errors=True)

    print("RAG_STATUS", json.dumps(public_status(), ensure_ascii=False), flush=True)
    print("DONE_RAG", flush=True)
    return 0 if swapped else 2


if __name__ == "__main__":
    raise SystemExit(main())
