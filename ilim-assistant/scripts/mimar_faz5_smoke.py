#!/usr/bin/env python3
"""Mimar Faz 5 — doğal dil atölye niyeti smoke."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar import mimar_faz5
    from ilim_assistant.ruzgar_motor_kernel import classify_motor_intent

    mimar_faz5.ensure_kernel_registered()

    p = mimar_faz5.parse_atolye_action("ev planı çiz")
    if not p or p.get("action") not in ("sketch_from_chat", "sketch_from_text"):
        print("FAIL ev planı çiz", p)
        return 1

    p2 = mimar_faz5.parse_atolye_action("eseri tanı")
    if p2.get("tab") != "resim-sanat" or p2.get("action") != "identify":
        print("FAIL eseri tanı", p2)
        return 1

    inst = mimar_faz5.maybe_instant_faz5("sanat galerisi")
    if not inst or "Sanat" not in inst:
        print("FAIL instant tab", inst)
        return 1

    arsiv = classify_motor_intent("arsiv durumu", "mimar", mode_norm="mimar")
    if arsiv.get("intent") != "command":
        print("FAIL arsiv still command", arsiv)
        return 1

    ciz = classify_motor_intent("kopya çıkar poster", "mimar", mode_norm="mimar")
    if ciz.get("intent") != "do" or ciz.get("atolye", {}).get("mode") != "poster":
        print("FAIL kopya poster", ciz)
        return 1

    from desktop_server import app

    paths = {getattr(r, "path", "") for r in app.routes}
    if "/api/mimar/atolye/parse" not in paths:
        print("FAIL route /api/mimar/atolye/parse")
        return 1

    print("OK mimar faz5 — niyet + route")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
