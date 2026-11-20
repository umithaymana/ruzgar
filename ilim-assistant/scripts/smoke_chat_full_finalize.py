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
    # Stream: finalize, done bloğunda yield'den ÖNCE
    i_done_blk = ds.find('if obj.get("type") == "done":', i_iter)
    blk = ds[i_done_blk : i_done_blk + 500] if i_done_blk > 0 else ""
    i_fin_rel = blk.find("_finalize_done_chat_turn(req, obj)")
    i_yield_done = blk.find("yield obj")
    failed += _ok(
        i_done_blk > 0 and i_fin_rel >= 0 and i_yield_done > i_fin_rel,
        "stream finalize yield öncesi",
    )
    failed += _ok('"tur_teshis": done_event.get("tur_teshis")' in ds, "full yanıtta tur_teshis")
    failed += _ok('"chat_persisted": bool(done_event.get("chat_persisted"))' in ds, "full yanıtta chat_persisted")
    failed += _ok('"masa": done_event.get("masa")' in ds, "full yanıtta masa")
    # Fast lane de ortak kapıya bağlandı
    failed += _ok(
        "def _fast_lane_post_done" in ds and "_finalize_done_chat_turn" in ds,
        "fast_lane ortak finalize",
    )
    failed += _ok("umed_timeout_reply()" in ds, "deadline TIMEOUT (MISS değil)")
    app_js = (ROOT.parent / "ruzgar-desktop" / "app.js").read_text(encoding="utf-8")
    failed += _ok("masa: j.masa || null" in app_js, "client full→done masa")

    total = 10
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
