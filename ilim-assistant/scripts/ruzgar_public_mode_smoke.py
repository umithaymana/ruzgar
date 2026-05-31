#!/usr/bin/env python3
"""Halk modu yol ayrımı smoke — kişisel hafıza kullanıcıya göre ayrılır."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="ruzgar-public-"))
    os.environ["RUZGAR_PUBLIC_MODE"] = "1"
    os.environ["RUZGAR_DATA_ROOT"] = str(tmp / "data")
    os.environ["RUZGAR_SHARED_ROOT"] = str(_ROOT)

    from ilim_assistant import ruzgar_public_mode as pm
    from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

    pm.bind_request_user("UmitAbi")
    m1 = get_hafiza_motor()
    p1 = pm.genel_hafiza_path()
    pm.clear_request_user()

    pm.bind_request_user("AyseHanim")
    m2 = get_hafiza_motor()
    p2 = pm.genel_hafiza_path()
    pm.clear_request_user()

    if p1 == p2:
        print("FAIL ayni hafiza yolu", p1)
        return 1
    if m1 is m2:
        print("FAIL ayni motor ornegi")
        return 1
    if "umitabi" not in str(p1).lower():
        print("FAIL user slug p1", p1)
        return 1

    health = pm.public_mode_health()
    if not health.get("public_mode"):
        print("FAIL public_mode flag")
        return 1
    if not health.get("knowledge_exists"):
        print("FAIL knowledge root")
        return 1

    print("OK ruzgar public mode — kullanici hafiza ayri")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
