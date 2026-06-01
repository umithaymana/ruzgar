#!/usr/bin/env python3
"""Mimar Faz 4 — atölye smoke (offline: modüller + API route listesi)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
REPO = _ROOT.parent


def _fail(msg: str) -> int:
    print(f"FAIL {msg}")
    return 1


def main() -> int:
    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    needed = [
        "/api/mimar/fotograf/list",
        "/api/mimar/fotograf/upload",
        "/api/mimar/fotograf/ocr",
        "/api/mimar/sanat/list",
        "/api/mimar/sanat/copy",
        "/api/mimar/sanat/sketch",
        "/api/mimar/tasarim/project/list",
        "/api/mimar/tasarim/project/new",
        "/api/mimar/tasarim/sketch/from-chat-handoff",
        "/api/mimar/tasarim/project/duplicate",
        "/api/mimar/tasarim/project/regenerate",
        "/api/mimar/tasarim/project/export-png",
    ]
    missing = [p for p in needed if p not in paths]
    if missing:
        return _fail(f"routes missing: {missing}")

    from ilim_assistant.motorlar import mimar_fotograf, mimar_sanat, mimar_tasarim

    if not mimar_fotograf.capabilities().get("ok"):
        return _fail("fotograf capabilities")
    if not mimar_sanat.capabilities().get("ok"):
        return _fail("sanat capabilities")
    if not mimar_tasarim.capabilities().get("ok"):
        return _fail("tasarim capabilities")

    lst = mimar_fotograf.list_photos(repo_root=REPO)
    if not isinstance(lst, dict) or "items" not in lst:
        return _fail("fotograf list shape")

    proj = mimar_tasarim.new_project(name="_smoke", repo_root=REPO)
    pid = (proj.get("project") or {}).get("id")
    if not pid:
        return _fail("tasarim new_project id")

    handoff = mimar_tasarim.build_chat_handoff_text("ev çiz", "tamam", "not")
    if "ev" not in handoff.lower():
        return _fail("chat handoff text")

    dup = mimar_tasarim.duplicate_project(pid, repo_root=REPO)
    dup_id = (dup.get("project") or {}).get("id")
    if not dup_id:
        return _fail("duplicate_project")

    try:
        mimar_sanat.copy_work("nope", mode="trace", repo_root=REPO)
        return _fail("copy_work should reject bad rel")
    except (ValueError, FileNotFoundError):
        pass

    if mimar_sanat.pillow_available():
        from PIL import Image

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "smoke.jpg"
            Image.new("RGB", (32, 32), color=(120, 80, 40)).save(p, "JPEG")
            up = mimar_sanat.upload_bytes(
                p.read_bytes(), "smoke.jpg", repo_root=REPO
            )
            rel = (up.get("item") or {}).get("rel")
            if not rel:
                return _fail("sanat upload rel")
            for mode in ("trace", "poster", "pencil"):
                cp = mimar_sanat.copy_work(rel, mode=mode, repo_root=REPO)
                if cp.get("mode") != mode:
                    return _fail(f"copy_work mode {mode}")

    from ilim_assistant.motorlar.okuma_faz73 import (
        classify_okuma_intent,
        ensure_kernel_registered,
    )
    from ilim_assistant.ruzgar_motor_kernel import classify_motor_intent

    ensure_kernel_registered()
    oi = classify_okuma_intent("arsiv durumu", mode_norm="okuma")
    mi = classify_okuma_intent("arsiv durumu", mode_norm="mimar")
    if oi.get("intent") != "command" or mi.get("intent") != "command":
        return _fail("okuma/mimar intent arsiv")
    rk = classify_motor_intent("arsiv durumu", "mimar", mode_norm="mimar")
    if rk.get("intent") != "command":
        return _fail("kernel mimar intent", str(rk))

    print("OK mimar faz4 — routes + modüller + mimar ROK alias")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
