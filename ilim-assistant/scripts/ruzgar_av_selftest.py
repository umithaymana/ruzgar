#!/usr/bin/env python3
"""Rüzgar Virüs Kalkanı — hızlı yerel doğrulama."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.motorlar.ruzgar_antivirus import (  # noqa: E402
    check_url_reputation,
    ruzgar_scan_file,
)

def main() -> int:
    ok = True
    staging = ROOT / "arsiv" / "_virus_guard_staging" / "selftest"
    staging.mkdir(parents=True, exist_ok=True)
    path = staging / "ruzgar_sig_probe.bin"
    # Tam EICAR Windows Defender tarafından silinebilir; imza katmanı aynı dizeyi arar.
    path.write_bytes(b"probe:" + b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" + b"\n")

    v = ruzgar_scan_file(path, mode="deep")
    if v.clean:
        print("FAIL: EICAR should be detected")
        ok = False
    else:
        print(f"OK: EICAR blocked risk={v.risk_score} threats={v.threats[:2]}")

    path.unlink(missing_ok=True)

    url_hits = check_url_reputation("http://127.0.0.1.evil.test/malware.exe")
    if url_hits:
        print(f"OK: URL reputation hits={url_hits[:1]}")
    else:
        print("INFO: URL not blocked (blocklist may be empty)")

    print(f"engine layers sample: {v.layers}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
