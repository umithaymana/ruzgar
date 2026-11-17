# Created by Ümit & Gökçenur
"""F4 — doğal sohbet + hibrit B + hub stay + rozet smoke."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_plan import should_stay_on_ana_motor_bilgi
    from ilim_assistant.ruzgar_provider_rozet import note_brain_used, provider_rozet_label
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target
    from ilim_assistant.prompts import pick_system
    from ilim_assistant.ruzgar_genel_faz90 import (
        build_genel_brain_chain_ids,
        genel_hibrit_b_enabled,
    )

    assert genel_hibrit_b_enabled()
    with patch(
        "ilim_assistant.ruzgar_genel_faz90.ollama_available", return_value=True
    ), patch(
        "ilim_assistant.ruzgar_genel_faz90._gemini_on_cooldown", return_value=False
    ):
        chain = build_genel_brain_chain_ids()
    assert chain[0] in ("denge", "hizli"), chain

    sys_thin = pick_system(False, "genel", thin_pipe=True)
    assert "Rüzgar" in sys_thin
    assert "[TALİMAT" not in sys_thin or "Kurallar" in sys_thin
    assert len(sys_thin) < 2500

    note_brain_used("denge", provider="ollama")
    assert provider_rozet_label("denge") == "yerel"
    assert provider_rozet_label("gemini") == "bulut"
    assert provider_rozet_label("", raftan=True) == "raftan"

    assert should_stay_on_ana_motor_bilgi("fotosentez nedir")
    assert should_stay_on_ana_motor_bilgi("lale devri nedir anlat")
    tgt, meta = resolve_hub_target("fotosentez nedir")
    assert tgt == "genel", (tgt, meta)

    tgt2, _ = resolve_hub_target("Osman Bey kimdir?")
    assert tgt2 == "genel"

    # F5 alias sözleşmesi (chat_core requests ister — kaynak satır smoke)
    _cc = (ROOT / "ilim_assistant" / "chat_core.py").read_text(encoding="utf-8")
    assert '"bilim": "genel"' in _cc and '"okuma": "genel"' in _cc
    assert '"ilim": "genel"' in _cc
    assert '"bilim": "mimar"' not in _cc

    os.environ["RUZGAR_GENEL_HIBRIT_B"] = "0"
    try:
        # cache yok — fonksiyon her seferinde env okur
        assert not genel_hibrit_b_enabled()
    finally:
        os.environ["RUZGAR_GENEL_HIBRIT_B"] = "1"

    print("smoke_f4_dogal_hibrit OK", chain[:3])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
