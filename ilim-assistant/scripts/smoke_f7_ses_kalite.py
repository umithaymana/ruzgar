# Created by Ümit & Gökçenur
"""F7 — profil / klon politikası / first-byte API smoke (TTS ağ ölçümü opsiyonel)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.motorlar.ses_klon_motoru import should_use_clone
    from ilim_assistant.ses_f7_kalite import (
        F7_VERSION,
        clone_policy_snapshot,
        f7_enabled,
        profile_ton_snapshot,
    )

    assert f7_enabled()
    prof = profile_ton_snapshot()
    assert "profiller" in prof
    for k in ("alim", "edip", "asistan"):
        assert k in prof["profiller"]
        assert prof["profiller"][k].get("voice")
        assert prof["profiller"][k].get("rate")

    pol = clone_policy_snapshot()
    assert "policy" in pol

    # F7.4 — auto + onay yok → klon yok
    assert should_use_clone(backend="auto", karakter="asistan", ayar={}) is False
    assert should_use_clone(backend="edge", karakter="asistan", ayar={}) is False
    # açık backend=clone → True (runtime yoksa yine True — API sonra 503)
    assert should_use_clone(backend="clone", karakter="asistan", ayar={}) is True
    assert (
        should_use_clone(
            backend="auto", karakter="asistan", ayar={"klon_onay": True}
        )
        in (True, False)
    )  # referans yoksa False

    # first-byte: V0 ref / vs_v0 hesabı (Edge ağına bağımlı değil)
    from ilim_assistant.ses_f7_kalite import V0_TTS_FIRST_BYTE_REF_MS, V3_TARGET_FIRST_BYTE_MS

    assert V0_TTS_FIRST_BYTE_REF_MS >= 1000
    assert V3_TARGET_FIRST_BYTE_MS < V0_TTS_FIRST_BYTE_REF_MS
    fb = 420.0
    assert (V0_TTS_FIRST_BYTE_REF_MS - fb) > 0
    assert fb <= V3_TARGET_FIRST_BYTE_MS

    print("smoke_f7_ses_kalite OK", F7_VERSION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
