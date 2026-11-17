# Created by Ümit & Gökçenur
"""F5.3–F5.6 — çekirdek envanter + hub-dışı + STT yüzey + hub niyet smoke."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.dinleme_motoru import stt_surface_status
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target
    from ilim_assistant.motorlar.ruzgar_cekirdegi import (
        ARA_MOTOR_BOOT_ORDER,
        HUB_MOTOR_IDS,
        build_core_context,
        cekirdek_envanter,
        is_hub_disi_yardimci,
    )

    env = cekirdek_envanter()
    assert env["ara_motor_boot_order"] == list(ARA_MOTOR_BOOT_ORDER)
    assert list(HUB_MOTOR_IDS) == env["hub_motors"]
    assert "mimar" in env["hub_motors"] and "hafiza" in env["hub_motors"]
    assert "hizir" in env["hub_motors"]
    assert is_hub_disi_yardimci("gelisim")
    assert is_hub_disi_yardimci("duzen")
    assert not is_hub_disi_yardimci("mimar")

    # Seçimli bağlam: selam → bilim/video yüklemesin (iskelet kısa)
    slim = build_core_context("selam naber")
    assert "RUZGAR CEKIRDEGI" in slim
    assert "yardimci_hub_disi" in slim or "Gelişim" in slim

    heavy = build_core_context("bu videoyu indir ve altyazı ekle")
    assert len(heavy) >= len(slim)

    st = stt_surface_status()
    assert st["surface"] == "ses_stt_pipeline"
    assert st["http_path"] == "/api/stt"
    assert st["primary"] == "faster-whisper"

    tgt, meta = resolve_hub_target("fotosentez nedir")
    assert tgt == "genel", (tgt, meta)
    tgt2, _ = resolve_hub_target("pytest geçir")
    assert tgt2 in ("programlama", "genel")

    # JS hub alias sözleşmesi (F5.6)
    hub_js = (REPO / "ruzgar-desktop" / "ana-motor-hub.js").read_text(encoding="utf-8")
    assert 't === "okuma"' in hub_js or 't === "okuma" ||' in hub_js
    assert 'return "genel"' in hub_js
    assert 'if (t === "okuma") return "mimar"' not in hub_js

    print("smoke_f5_cekirdek_hub_stt OK", env["version"], st["surface"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
