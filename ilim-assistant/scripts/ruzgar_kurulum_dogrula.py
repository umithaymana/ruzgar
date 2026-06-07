#!/usr/bin/env python3
"""Rüzgar ses/video kurulum doğrulama — Ümit abi checklist."""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

_IA = Path(__file__).resolve().parents[1]
if str(_IA) not in sys.path:
    sys.path.insert(0, str(_IA))


def ok(msg: str) -> None:
    print(f"  OK  {msg}")


def fail(msg: str, detail: str = "") -> None:
    print(f"  FAIL {msg}" + (f" — {detail}" if detail else ""))


def main() -> int:
    fails = 0
    print("Rüzgar kurulum doğrulama\n")

    try:
        from ilim_assistant.env_bootstrap import ensure_ruzgar_env

        ensure_ruzgar_env()
    except Exception:
        pass

    try:
        import torch

        ok(f"torch {torch.__version__} (cuda={torch.cuda.is_available()})")
    except Exception as e:
        fail("torch", str(e))
        fails += 1

    try:
        import torchaudio

        ok(f"torchaudio {torchaudio.__version__}")
    except Exception as e:
        fail("torchaudio", str(e))
        fails += 1

    try:
        from TTS.api import TTS  # noqa: F401

        ok("coqui-tts (TTS.api)")
    except Exception as e:
        fail("coqui-tts", str(e)[:120])
        fails += 1

    try:
        from ilim_assistant.motorlar.ses_klon_motoru import clone_status_snapshot

        snap = clone_status_snapshot()
        if snap.get("xtts"):
            ok("XTTS runtime")
        else:
            fail("XTTS runtime", snap.get("hint_tr", "")[:100])
            fails += 1
    except Exception as e:
        fail("clone_status", str(e))
        fails += 1

    try:
        import edge_tts

        ok(f"edge-tts")
    except Exception as e:
        fail("edge-tts", str(e))
        fails += 1

    try:
        from ilim_assistant.video_ffmpeg import ffmpeg_available, ffprobe_available

        ok(f"ffmpeg={ffmpeg_available()} ffprobe={ffprobe_available()}")
    except Exception as e:
        fail("ffmpeg", str(e))
        fails += 1

    try:
        from ilim_assistant.motorlar.video_motoru import ytdlp_available

        ok(f"yt-dlp={ytdlp_available()}")
    except Exception as e:
        fail("yt-dlp", str(e))
        fails += 1

    import os

    tess = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if Path(tess).is_file():
        ok(f"tesseract {tess}")
    else:
        fail("tesseract", "TESSERACT_CMD veya PATH")

    ref_dir = Path(__file__).resolve().parents[1] / "arsiv" / "ses-referans"
    ref_dir.mkdir(parents=True, exist_ok=True)
    ok(f"referans klasörü {ref_dir.name}/")

    try:
        with urllib.request.urlopen("http://127.0.0.1:8779/api/health", timeout=5) as r:
            j = json.loads(r.read().decode())
        clone = j.get("tts_clone") or {}
        if clone.get("xtts"):
            ok("API health — tts_clone.xtts=true")
        else:
            fail("API tts_clone.xtts", "Sunucuyu yeniden başlatın")
            fails += 1
    except Exception as e:
        fail("API http://127.0.0.1:8779", str(e)[:80])
        fails += 1

    print()
    if fails:
        print(f"SONUÇ: {fails} eksik — yukarıdaki FAIL satırlarına bakın.")
        return 1
    print("SONUÇ: Tüm kontroller geçti — sohbetten «videodaki sesi kuran sesi yap» deneyebilirsin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
