#!/usr/bin/env python3
"""Yol C / Blok C — kök neden sınıflandırıcı smoke (yanlış scope etiketi yok)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz102_e1_live import classify_root_cause

    assert classify_root_cause(success=True) == "ok"
    # pytest_scope metni artık scope_rejected değil
    c = classify_root_cause(
        success=False,
        verify_ok=False,
        detail="doğrulama OK (pytest_scope) sonra kırmızı — pytest failed",
    )
    assert c == "pytest_failed", c

    c2 = classify_root_cause(
        success=False,
        verify_ok=False,
        detail="**Tur 1/21** Yazılan: 1 dosya Doğrulama: kırmızı",
    )
    assert c2 == "pytest_failed", c2

    c3 = classify_root_cause(
        success=False,
        verify_ok=False,
        detail="yazım reddedildi: kapsam dışı (faz 78)",
    )
    assert c3 == "scope_rejected", c3

    c4 = classify_root_cause(
        success=False,
        verify_ok=True,
        writes_ok=0,
        detail="ajan turu bitti ama dosya yazılmadı",
    )
    assert c4 == "no_write", c4

    print("OK e1-root-cause — pytest_scope false-positive yok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
