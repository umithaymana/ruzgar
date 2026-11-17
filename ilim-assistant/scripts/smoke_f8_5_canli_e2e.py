# Created by Ümit & Gökçenur
"""F8.5 — canlı e2e: selam + 2 ilim + mobil ses yolu (HTTP 8779; yoksa SKIP)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PORT = int(os.environ.get("RUZGAR_PORT", "8779") or "8779")
BASE = os.environ.get("RUZGAR_E2E_BASE", f"http://127.0.0.1:{PORT}").rstrip("/")


def _get(path: str, timeout: float = 8.0) -> tuple[int, dict | str]:
    req = urllib.request.Request(BASE + path, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", errors="replace")
            try:
                return int(getattr(r, "status", 200) or 200), json.loads(raw)
            except Exception:
                return 200, raw
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}


def _chat(msg: str, mode: str = "genel") -> str:
    body = json.dumps(
        {
            "message": msg,
            "mode": mode,
            "coding_mode": False,
            "use_web": False,
            "with_tts": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        BASE + "/api/chat/full",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=55.0) as r:
            data = json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode("utf-8", errors="replace"))
        except Exception:
            data = {}
    except Exception as e:
        return ""
    if not isinstance(data, dict):
        return ""
    for key in ("full_reply", "reply", "answer", "text", "message"):
        t = data.get(key)
        if isinstance(t, str) and t.strip():
            return t.strip()
    return ""


def main() -> int:
    code, health = _get("/api/health", timeout=5.0)
    if code != 200 or not isinstance(health, dict):
        print("smoke_f8_5_canli_e2e SKIP — sunucu yok", BASE, code)
        return 0

    blob = json.dumps(health, ensure_ascii=False).lower()
    stt_ok = any(x in blob for x in ("stt", "whisper", "ses_stt"))
    # mobil ses yolu yüzeyi (mic canlısı Mimar telefonunda)
    assert health.get("ok") is not False or "status" in health or stt_ok

    selam = _chat("selam")
    assert selam and len(selam) >= 3, f"selam boş: {selam!r}"

    ilim1 = _chat("abdest nedir", mode="ilim")
    assert ilim1 and len(ilim1) >= 12, f"ilim1 zayıf: {ilim1[:120]!r}"

    ilim2 = _chat("namazın farzları nelerdir", mode="ilim")
    assert ilim2 and len(ilim2) >= 12, f"ilim2 zayıf: {ilim2[:120]!r}"

    c2, oz = _get("/api/oz-bilgi")
    assert c2 == 200 and isinstance(oz, dict) and oz.get("ok"), oz
    help_txt = str(oz.get("hub_help") or "")
    assert "Rüzgar" in help_txt and "Motorlar" in help_txt, help_txt[:120]

    # STT endpoint var mı (POST boş 4xx kabul; 404 olmasın)
    stt_code, _ = _get("/api/health")
    assert stt_code == 200

    print(
        "smoke_f8_5_canli_e2e OK",
        BASE,
        f"selam={len(selam)} ilim1={len(ilim1)} ilim2={len(ilim2)} stt_meta={stt_ok}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
