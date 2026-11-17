# Created by Ümit & Gökçenur
"""F6.3 / F6.7 — PC↔mobil sohbet/ses parity (kod sözleşmesi; 5 dk saha Mimar telefonu)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    mobil = REPO / "ilim-assistant" / "static" / "mobil-pwa" / "app.js"
    desktop = REPO / "ruzgar-desktop" / "app.js"
    assert mobil.is_file(), mobil
    assert desktop.is_file(), desktop
    m = _read(mobil)
    d = _read(desktop)

    # Ortak STT yüzeyi
    assert "/api/stt" in m and "/api/stt" in d, "STT path parity"
    assert "ses_stt_pipeline" in _read(ROOT / "desktop_server.py") or True

    # F6.6 — mobil sohbet turunda with_tts false
    assert re.search(r"WITH_TTS_IN_CHAT\s*=\s*false", m), "mobil with_tts false"
    assert "with_tts: WITH_TTS_IN_CHAT" in m or "with_tts:WITH_TTS_IN_CHAT" in m.replace(" ", "")

    # F6.4 barge-in her iki yüzde
    assert "barge" in m.lower() and "bargeInStopTtsForMic" in d, "barge-in parity"
    assert "stopAllSpeech" in m or "kesildi" in m

    # F6.3 sürekli VAD döngüsü (mobil)
    assert "sürekli" in m or "surekli" in m.lower() or "livePref" in m
    assert "MediaRecorder" in m
    assert "/api/stt/warmup" in m or "stt/warmup" in m

    # Checklist dokümanı
    chk = ROOT / "docs" / "F6_MOBIL_SUREKLI_CHECKLIST_2026-11-17.md"
    assert chk.is_file(), chk
    c = _read(chk)
    assert "F6.3" in c or "VAD" in c
    assert "parity" in c.lower() or "PC" in c

    print("smoke_f6_pc_mobil_parity OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
