# -*- coding: utf-8 -*-
"""Smoke — /api/chat/full done sonrası ortak finalize kancası (kaynak doğrulama)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    failed += _ok("def _finalize_done_chat_turn" in ds, "finalize helper tanımlı")
    i_full = ds.find("def _chat_full_sync")
    i_fin = ds.find("_finalize_done_chat_turn(req, done_event)", i_full)
    failed += _ok(i_full > 0 and i_fin > i_full, "finalize _chat_full_sync içinde")
    i_iter = ds.find("def iter_chat_turn_events")
    i_fin2 = ds.find("_finalize_done_chat_turn(req, obj)", i_iter)
    failed += _ok(i_iter > 0 and i_fin2 > i_iter, "finalize stream iter içinde")
    failed += _ok('"tur_teshis": done_event.get("tur_teshis")' in ds, "full yanıtta tur_teshis")
    failed += _ok('"chat_persisted": bool(done_event.get("chat_persisted"))' in ds, "full yanıtta chat_persisted")
    # Fast lane de ortak kapıya bağlandı
    failed += _ok(
        "def _fast_lane_post_done" in ds and "_finalize_done_chat_turn(req, done)" in ds,
        "fast_lane ortak finalize",
    )

    total = 6
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
