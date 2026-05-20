#!/usr/bin/env python3
"""Başlatıcı: GLOBAL_API_KEY yüklü mü? (0/1, anahtar yazdırmaz)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ilim_assistant.config import apply_global_api_key_to_runtime, gemini_ready

apply_global_api_key_to_runtime()
print("1" if gemini_ready() else "0")
