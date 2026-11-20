# Created by Ümit & Gökçenur
"""Kilitli motor boot — tek kaynak (.cursorrules / masaüstü / desktop_server).

Sıra değiştirilemez: ana motor → çekirdek → 7 ara motor.
RUZGAR_DEFER_MOTOR_BOOT yardımcı ısınmaları erteler; bu kilidi atlamaz.
"""

from __future__ import annotations

import importlib
import sys
from typing import Final

BOOT_KILIT_VERSION: Final = "ruzgar-boot-kilit-v1-2026-11-20"

ANA_MOTOR: Final = "ilim_assistant.main_engine"
CEKIRDEK: Final = "ilim_assistant.motorlar.ruzgar_cekirdegi"
ARA_MOTORLAR: Final[tuple[str, ...]] = (
    "ilim_assistant.ses_motoru",
    "ilim_assistant.video_motoru",
    "ilim_assistant.okuma_motoru",
    "ilim_assistant.mimar_motoru",
    "ilim_assistant.tercume_motoru",
    "ilim_assistant.motorlar.hafiza_motoru",
    "ilim_assistant.programlama_motoru",
)

_DONE = False


def boot_manifest() -> list[str]:
    return [ANA_MOTOR, CEKIRDEK, *ARA_MOTORLAR]


def boot_motorlar_anaonce(*, announce: bool = False) -> None:
    """Ana motor → çekirdek → 7 ara motor (sıra kilitli). İdempotent."""
    global _DONE
    if _DONE and all(n in sys.modules for n in boot_manifest()):
        return
    importlib.import_module(ANA_MOTOR)
    importlib.import_module(CEKIRDEK)
    for name in ARA_MOTORLAR:
        importlib.import_module(name)
    _DONE = True
    if announce:
        print(
            f"[Rüzgar] Motor boot tamam ({BOOT_KILIT_VERSION}).",
            file=sys.stderr,
            flush=True,
        )


def ensure_boot_motorlar_anaonce(*, announce: bool = False) -> None:
    """Eksik motor varsa kilitli sırayla tamamla."""
    boot_motorlar_anaonce(announce=announce)
