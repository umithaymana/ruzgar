# -*- coding: utf-8 -*-
"""V2 smoke — STT decode (PyAV metadata_errors) + sessiz wav transcribe."""
from __future__ import annotations

import os
import struct
import sys
import tempfile
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.stt_whisper import (
        _decode_audio_f32,
        get_model,
        stt_runtime_available,
        transcribe_file_detailed,
    )

    failed = 0
    failed += _ok(stt_runtime_available(), "stt available")

    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    wav = Path(tmp)
    n = 16000
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack("<" + "h" * n, *([0] * n)))

    try:
        arr = _decode_audio_f32(wav, sampling_rate=16000)
        failed += _ok(hasattr(arr, "shape") and arr.shape[0] > 1000, f"decode len={getattr(arr, 'shape', None)}")

        if os.environ.get("RUZGAR_V2_STT_LIVE", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        ):
            t0 = time.perf_counter()
            get_model()
            load_ms = (time.perf_counter() - t0) * 1000.0
            t1 = time.perf_counter()
            try:
                res = transcribe_file_detailed(wav, language="tr")
                ms = (time.perf_counter() - t1) * 1000.0
                failed += _ok(True, f"transcribe ok ms={ms:.0f} load_ms={load_ms:.0f}")
                failed += _ok(res.language is not None, f"lang={res.language}")
            except Exception as exc:
                failed += _ok(False, f"transcribe {exc}")
                failed += _ok(False, "lang skip")
        else:
            failed += _ok(True, "live skip")
            failed += _ok(True, "lang skip")
    finally:
        try:
            wav.unlink(missing_ok=True)
        except OSError:
            pass

    # Patch işareti
    get_model()
    import faster_whisper.audio as fw_audio

    failed += _ok(
        bool(getattr(fw_audio, "_ruzgar_v2_decode_patched", False)),
        "decode patch",
    )

    total = 5
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
