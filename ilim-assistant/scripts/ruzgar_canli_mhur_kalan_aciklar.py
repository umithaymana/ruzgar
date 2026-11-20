#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kalan açıklar canlı mühür: çok-kaynak RAG (≥3 eser) + Ollama local-first.

Neden önceki turda açık kaldı:
- `.rag_index` boştu (vektör yok) → diversify canlı koşulamadı
- Ollama kurulu değildi → zincir buluta düşüyordu
- main birleşimi ayrı «al» bekliyordu

Bu script: gerçek hadis/siyer/tefsir örneklerinden mini indeks kurar,
filtre AÇIK iken ≥3 eser diversify doğrular, Ollama local-first zincirini mühürler.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CORPUS = ROOT / "knowledge" / "_canli_mhur_cok_kaynak"
INDEX = ROOT / ".rag_index"

_SOURCES: list[tuple[str, str]] = [
    (
        "ilim/din/05_hadis/kutub_i_sitte/buhari",
        "knowledge/ilim/din/05_hadis/kutub_i_sitte/buhari/incremental/buhari_batch_0001.md",
    ),
    (
        "ilim/din/05_hadis/kutub_i_sitte/buhari",
        "knowledge/ilim/din/05_hadis/kutub_i_sitte/buhari/incremental/buhari_batch_0002.md",
    ),
    (
        "ilim/din/05_hadis/kutub_i_sitte/tirmizi",
        "knowledge/ilim/din/05_hadis/kutub_i_sitte/tirmizi/incremental/tirmizi_batch_0001.md",
    ),
    (
        "ilim/din/05_hadis/kutub_i_sitte/tirmizi",
        "knowledge/ilim/din/05_hadis/kutub_i_sitte/tirmizi/incremental/tirmizi_batch_0002.md",
    ),
    (
        "ilim/din/05_hadis/kutub_i_sitte/muslim",
        "knowledge/ilim/din/05_hadis/kutub_i_sitte/muslim/incremental/muslim_batch_0001.md",
    ),
    (
        "ilim/din/08_siyer/eserler/maghazi_waqidi",
        "knowledge/ilim/din/08_siyer/eserler/maghazi_waqidi/incremental/maghazi_waqidi_batch_0001.md",
    ),
    (
        "ilim/din/08_siyer",
        "knowledge/ilim/din/08_siyer/incremental/siyer_kavramlar_tr.md",
    ),
    (
        "ilim/din/02_tefsir/klasik/beyzavi",
        "knowledge/ilim/din/02_tefsir/klasik/beyzavi/incremental/beyzavi_batch_0001.md",
    ),
]


def _prepare_corpus() -> int:
    if CORPUS.exists():
        shutil.rmtree(CORPUS)
    CORPUS.mkdir(parents=True)
    n = 0
    for rel, src_rel in _SOURCES:
        src = ROOT / src_rel
        if not src.is_file():
            print(f"SKIP missing {src_rel}")
            continue
        dest_dir = CORPUS.joinpath(*rel.split("/"))
        dest_dir.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8", errors="ignore")[:12000]
        (dest_dir / src.name).write_text(text, encoding="utf-8")
        n += 1
    (CORPUS / "README.md").write_text(
        "Canlı mühür örnek derlemesi — tam Şamile değil; diversify ≥3 eser smoke.\n",
        encoding="utf-8",
    )
    return n


def main() -> int:
    os.chdir(ROOT)
    os.environ["RUZGAR_KNOWLEDGE_ROOT"] = str(CORPUS)
    os.environ["RUZGAR_RAG_INDEX_DIR"] = str(INDEX)
    # Local-first modeller (VM'de küçük Ollama)
    for k, v in (
        ("OLLAMA_CHAT_MODEL", "qwen2.5:0.5b"),
        ("OLLAMA_CHAT_MODEL_FAST", "qwen2.5:0.5b"),
        ("RUZGAR_BRAIN_DENGE_MODEL", "qwen2.5:0.5b"),
        ("RUZGAR_BRAIN_HIZLI_MODEL", "qwen2.5:0.5b"),
    ):
        os.environ.setdefault(k, v)

    n = _prepare_corpus()
    if n < 4:
        print(f"FAIL corpus too small: {n}")
        return 2

    from ilim_assistant.rag_store import build_index, search
    from ilim_assistant.ruzgar_cok_kaynak_sentez import (
        _source_book_key,
        diversify_hits_by_book,
    )
    from ilim_assistant.ruzgar_anlam_koruma import chunk_fits_query
    from ilim_assistant.ruzgar_genel_faz90 import (
        build_genel_brain_chain_ids,
        build_ilim_rag_brain_chain_ids,
        ollama_available,
    )
    from ilim_assistant.llm_ollama import ollama_reachable, chat_completion

    # Köprü self-check
    buhari = next(CORPUS.rglob("buhari_batch_0001.md"))
    assert chunk_fits_query(
        "niyet hadisi", buhari.read_text(encoding="utf-8")
    ), "TR→AR köprü niyet/hadis"

    built = build_index(knowledge_root=CORPUS, force=True)
    print("build", built)
    hits = search("niyet hadisi", top_k=16)
    books = sorted({_source_book_key(s) for _, s, _ in hits})
    div = diversify_hits_by_book(hits, max_books=5, per_book=2, max_total=10)
    div_books = sorted({_source_book_key(s) for _, s, _ in div})
    print("hits", len(hits), "books", books)
    print("div", len(div), "div_books", div_books)

    if len(div_books) < 3:
        print(f"FAIL diversify books={div_books}")
        return 3

    if not ollama_reachable() or not ollama_available():
        print("FAIL ollama not reachable")
        return 4

    ilim = build_ilim_rag_brain_chain_ids()
    genel = build_genel_brain_chain_ids()
    print("ilim_chain", ilim)
    print("genel_chain", genel)
    if not ilim or ilim[0] not in ("denge", "hizli"):
        print(f"FAIL ilim chain not local-first: {ilim}")
        return 5
    if not genel or genel[0] not in ("denge", "hizli"):
        print(f"FAIL genel chain not local-first: {genel}")
        return 6

    # Küçük generate — yerel model cevap üretiyor mu
    out = chat_completion(
        system="Kısa cevap ver.",
        user="Selam, bir kelimeyle cevap ver.",
        model=os.environ["OLLAMA_CHAT_MODEL"],
    )
    text = (out or "").strip()
    print("ollama_chat_ok", bool(text), "preview", text[:80].replace("\n", " "))
    if not text or text.startswith("[HTTP"):
        print("FAIL ollama chat:", text[:200])
        return 7

    print("CANLI_MHUR_KALAN_ACIKLAR_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
