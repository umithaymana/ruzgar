# Created by Ümit & Gökçenur
"""Madde 4 — indeks sağlığı: hariç tutma + learned ince yol (kör full rebuild yok)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, name: str) -> int:
    print(("OK" if cond else "FAIL") + " - " + name)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.rag_store import (
        _is_shamela_main_skip,
        _is_thin_auto_ingest_rel,
        _allow_new_main_rel,
        _load_markdown_files,
        index_health_report,
        upsert_sources_into_main_index,
        Chunk,
    )

    failed = 0
    failed += _ok(_is_shamela_main_skip("ilim/din/shamela/hadis/foo.md"), "skip shamela posix")
    failed += _ok(
        _is_shamela_main_skip(r"ilim\din\shamela\hadis\foo.md"),
        "skip shamela win",
    )
    failed += _ok(not _is_shamela_main_skip("learned/x.md"), "learned not skip")
    failed += _ok(_is_thin_auto_ingest_rel("learned/a.md"), "thin learned")
    failed += _ok(not _is_thin_auto_ingest_rel("ortak_kaynak/alanlar/x.md"), "thin not ortak")
    failed += _ok(not _allow_new_main_rel("ortak_kaynak/yeni.md"), "new ortak blocked")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "learned").mkdir()
        (root / "ilim" / "din" / "shamela" / "x").mkdir(parents=True)
        (root / "ortak_kaynak").mkdir()
        (root / "learned" / "a.md").write_text("# a\nmerhaba learned\n", encoding="utf-8")
        (root / "ilim" / "din" / "shamela" / "x" / "b.md").write_text(
            "# sham\n", encoding="utf-8"
        )
        (root / "ortak_kaynak" / "c.md").write_text("# ortak yeni\n", encoding="utf-8")
        (root / "old.md").write_text("# eski\n", encoding="utf-8")

        known = {"old.md"}
        loaded = _load_markdown_files(root, known_norm=known, restrict_new=True)
        rels = {r.replace("\\", "/") for r, _ in loaded}
        failed += _ok("learned/a.md" in rels or "learned\\a.md".replace("\\", "/") in {
            x.replace("\\", "/") for x in rels
        } or any(x.endswith("learned/a.md") or x.endswith("learned\\a.md") for x in rels),
            "load includes learned")
        # normalize check
        normed = {r.replace("\\", "/") for r, _ in loaded}
        failed += _ok("learned/a.md" in normed, "load learned norm")
        failed += _ok("old.md" in normed, "load known old")
        failed += _ok(not any("shamela" in r for r in normed), "load skips shamela")
        failed += _ok("ortak_kaynak/c.md" not in normed, "load skips new ortak")

    health = index_health_report()
    failed += _ok(isinstance(health, dict) and "learned_missing" in health, "health keys")
    failed += _ok(health.get("shamela_policy") == "main_index_skip_shards_own", "health policy")

    # upsert: mini sahte indeks (gömme mock)
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        idx = tdir / "idx"
        know = tdir / "know"
        idx.mkdir()
        (know / "learned").mkdir(parents=True)
        body0 = "# eski\nbase chunk\n"
        (know / "learned" / "eski.md").write_text(body0, encoding="utf-8")
        (know / "learned" / "yeni.md").write_text("# yeni\nyeni learned metin\n", encoding="utf-8")

        chunks = [Chunk(text="base chunk", source="learned/eski.md")]
        emb = np.ones((1, 8), dtype=np.float32)
        np.save(str(idx / "embeddings.npy"), emb)
        (idx / "chunks.jsonl").write_text(
            json.dumps({"text": "base chunk", "source": "learned/eski.md"}, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
        man = {
            "digest": "x",
            "num_chunks": 1,
            "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "file_digests": {"learned/eski.md": "oldhash"},
        }
        (idx / "manifest.json").write_text(
            json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        class _FakeEnc:
            def encode(self, texts, normalize_embeddings=True, show_progress_bar=False):
                return np.ones((len(texts), 8), dtype=np.float32)

        with mock.patch.dict(
            "os.environ",
            {"RUZGAR_RAG_INDEX_DIR": str(idx)},
            clear=False,
        ), mock.patch(
            "ilim_assistant.rag_store._get_embedder", return_value=_FakeEnc()
        ), mock.patch(
            "ilim_assistant.rag_store._knowledge_root", return_value=know
        ):
            # index dir cache — yeniden çözümle
            import ilim_assistant.rag_store as rs

            rs.invalidate_rag_cache()
            out = upsert_sources_into_main_index(
                ["learned/yeni.md", "learned/eski.md"],
                knowledge_root=know,
            )
            failed += _ok(out.get("changed_files", 0) >= 1, "upsert changed")
            failed += _ok(out.get("status") in ("upsert", "learned_upsert"), "upsert status")
            man2 = json.loads((idx / "manifest.json").read_text(encoding="utf-8"))
            keys = {k.replace("\\", "/") for k in man2.get("file_digests") or {}}
            failed += _ok("learned/yeni.md" in keys, "upsert yeni in manifest")

    print(f"result: {11 - failed + (0 if failed else 0)} checks; failed={failed}")
    # recount roughly
    print("result:", "FAIL" if failed else "pass", f"({failed} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
