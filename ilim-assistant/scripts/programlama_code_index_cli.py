#!/usr/bin/env python3
"""Semantik kod indeksi CLI — build / search / smoke."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WORKSPACE = Path((os.environ.get("RUZGAR_WORKSPACE_ROOT") or "").strip() or str(_ROOT.parent))


def main() -> int:
    ap = argparse.ArgumentParser(description="Rüzgar semantik kod indeksi")
    ap.add_argument("action", choices=("build", "search", "smoke"), help="build | search | smoke")
    ap.add_argument("query", nargs="?", default="", help="Arama sorgusu (search)")
    ap.add_argument("--scope", default="", help="projects/<ad> kapsamı")
    ap.add_argument("--force", action="store_true", help="İndeksi zorla yeniden oluştur")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    from ilim_assistant.motorlar.programlama_code_index import (
        build_code_index,
        run_code_index_smoke,
        search_code_index,
    )

    if args.action == "build":
        rep = build_code_index(WORKSPACE, force=args.force)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0 if rep.get("ok") else 1

    if args.action == "search":
        if not args.query.strip():
            print("Sorgu gerekli", file=sys.stderr)
            return 2
        rep = search_code_index(
            WORKSPACE,
            args.query,
            scope_rel=args.scope or None,
            top_k=max(1, args.top),
        )
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0 if rep.get("ok") else 1

    rep = run_code_index_smoke(WORKSPACE)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
