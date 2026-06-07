#!/usr/bin/env python3
# Created by Ümit & Gökçenur
"""Ses motoru S1–S6 smoke test (unit + opsiyonel canlı API)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

API = os.environ.get("RUZGAR_API", "http://127.0.0.1:8779").rstrip("/")

_pass = 0
_fail = 0
_skip = 0


def ok(name: str, detail: str = "") -> None:
    global _pass
    _pass += 1
    s = f"  PASS  {name}"
    if detail:
        s += f" — {detail}"
    print(s)


def fail(name: str, detail: str = "") -> None:
    global _fail
    _fail += 1
    s = f"  FAIL  {name}"
    if detail:
        s += f" — {detail}"
    print(s)


def skip(name: str, detail: str = "") -> None:
    global _skip
    _skip += 1
    s = f"  SKIP  {name}"
    if detail:
        s += f" — {detail}"
    print(s)


def test_s1_prosody() -> None:
    from ilim_assistant.motorlar.ses_motoru import IcerikYolu
    from ilim_assistant.motorlar.ses_prosody import (
        metin_parcala,
        prosody_etkin,
        prosody_gerekli,
        prosody_ozet,
    )

    if not prosody_etkin():
        skip("S1 prosody_etkin", "RUZGAR_TTS_PROSODY=0")
    else:
        ok("S1 prosody_etkin")

    uzun = "Bu birinci cümle. Bu ikinci cümle biraz daha uzun olsun ki prosody devreye girsin."
    if prosody_gerekli(uzun):
        ok("S1 prosody_gerekli uzun metin")
    else:
        fail("S1 prosody_gerekli uzun metin")

    parcalar = metin_parcala(uzun, IcerikYolu.genel)
    if len(parcalar) >= 2:
        ok("S1 metin_parcala", f"{len(parcalar)} parça")
    else:
        fail("S1 metin_parcala", f"beklenen >=2, got {len(parcalar)}")

    oz = prosody_ozet(parcalar)
    if oz.get("parcalar", 0) >= 2:
        ok("S1 prosody_ozet")
    else:
        fail("S1 prosody_ozet", str(oz))


def test_s2_stt() -> None:
    from ilim_assistant.stt_whisper import stt_runtime_available

    if stt_runtime_available():
        ok("S2 Whisper runtime")
    else:
        skip("S2 Whisper runtime", "pip install faster-whisper veya RUZGAR_STT=0")


def test_s3_altyazi() -> None:
    from ilim_assistant.motorlar.altyazi_fabrika import (
        FABRIKA_VERSION,
        list_sablonlar,
        parse_srt,
    )

    ok("S3 FABRIKA_VERSION", FABRIKA_VERSION)
    sab = list_sablonlar()
    if sab:
        ok("S3 sablonlar", str(len(sab)))
    else:
        fail("S3 sablonlar", "bos")

    sample = """1
00:00:00,000 --> 00:00:02,000
Merhaba dunya
"""
    cues = parse_srt(sample)
    if len(cues) == 1 and "Merhaba" in cues[0].text:
        ok("S3 parse_srt")
    else:
        fail("S3 parse_srt", str(cues))


def test_s4_klon() -> None:
    from ilim_assistant.motorlar.ses_klon_motoru import clone_status_snapshot

    snap = clone_status_snapshot()
    if snap.get("enabled") is not False:
        ok("S4 clone snapshot", f"xtts={snap.get('xtts')}")
    else:
        skip("S4 clone", "kapali")


def test_s5_tilavet() -> None:
    from ilim_assistant.motorlar.ses_tilavet import (
        TILAVET_VERSION,
        tilavet_etkin,
        tespit_tilavet_modu,
        tilavet_parcala,
    )

    ok("S5 TILAVET_VERSION", TILAVET_VERSION)
    if tilavet_etkin():
        ok("S5 tilavet_etkin")
    else:
        skip("S5 tilavet_etkin", "RUZGAR_TTS_TILAVET=0")

    mod = tespit_tilavet_modu("Bismillahirrahmanirrahim ﴿1﴾")
    if mod:
        ok("S5 tespit_tilavet_modu", mod.value)
    else:
        fail("S5 tespit_tilavet_modu")

    parcalar = tilavet_parcala("Besmele. Bir ayet metni.")
    if parcalar:
        ok("S5 tilavet_parcala", str(len(parcalar)))
    else:
        fail("S5 tilavet_parcala")


def test_s6_dublaj() -> None:
    from ilim_assistant.motorlar.video_dublaj import (
        DUBLAJ_VERSION,
        DubSegment,
        _merge_dub_segments,
        dubbing_status_snapshot,
    )

    ok("S6 DUBLAJ_VERSION", DUBLAJ_VERSION)
    snap = dubbing_status_snapshot()
    if snap.get("enabled"):
        ok("S6 dub enabled", f"max_seg={snap.get('max_segments')}")
    else:
        skip("S6 dub", "RUZGAR_VIDEO_DUB=0")

    segs = [
        DubSegment(1, 0, 2, "hello"),
        DubSegment(2, 2.2, 4, "world"),
    ]
    merged = _merge_dub_segments(segs)
    if len(merged) == 1 and "hello world" in merged[0].source_text:
        ok("S6 merge segments")
    else:
        fail("S6 merge segments", str(merged))


def _http_json(method: str, path: str, body: dict | None = None, timeout: int = 30):
    url = f"{API}{path}"
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def test_api_health() -> None:
    try:
        st, j = _http_json("GET", "/api/health", timeout=8)
    except Exception as e:
        skip("API health", str(e))
        return
    if st != 200:
        fail("API health", f"HTTP {st}")
        return
    ok("API health")
    if j.get("ffmpeg"):
        ok("API ffmpeg")
    else:
        skip("API ffmpeg", "PATH yok — S1/S6 mux etkilenir")
    for key in ("tts_tilavet", "video_dub"):
        if key in j:
            ok(f"API health.{key}", str(j[key])[:60])


def test_api_endpoints() -> None:
    endpoints = [
        ("GET", "/api/ses/settings", None),
        ("GET", "/api/tts/clone/status", None),
        ("GET", "/api/video/dub/status", None),
        ("GET", "/api/video/subtitles/templates", None),
        ("GET", "/api/tts/tilavet/info?text=Besmele", None),
    ]
    for method, path, body in endpoints:
        try:
            st, j = _http_json(method, path, body, timeout=15)
            if st == 200 and j.get("ok", True):
                ok(f"API {path.split('?')[0]}", str(j)[:80])
            else:
                fail(f"API {path}", f"HTTP {st} {j}")
        except Exception as e:
            fail(f"API {path}", str(e))


def test_api_tts_short() -> None:
    try:
        from ilim_assistant.tts_service import edge_available
    except Exception:
        edge_available = lambda: False  # type: ignore

    if not edge_available():
        skip("API POST /api/tts", "edge-tts yok veya ag yok")
        return
    url = f"{API}/api/tts"
    body = json.dumps(
        {"text": "Ruzgar ses testi.", "karakter": "asistan", "backend": "edge"}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            ct = r.headers.get("Content-Type", "")
            data = r.read()
        if r.status == 200 and len(data) > 500 and ("audio" in ct or data[:3] == b"ID3"):
            ok("API POST /api/tts kisa metin", f"{len(data)} byte MP3")
        elif r.status == 200 and len(data) > 100:
            ok("API POST /api/tts kisa metin", f"{len(data)} byte")
        else:
            fail("API POST /api/tts", f"HTTP {r.status} len={len(data)} ct={ct}")
    except urllib.error.HTTPError as e:
        fail("API POST /api/tts", f"HTTP {e.code} {e.read().decode()[:200]}")
    except Exception as e:
        fail("API POST /api/tts", str(e))


def main() -> int:
    print("=== Ses motoru S1–S6 smoke ===\n")
    print("[Unit]")
    test_s1_prosody()
    test_s2_stt()
    test_s3_altyazi()
    test_s4_klon()
    test_s5_tilavet()
    test_s6_dublaj()

    print("\n[API — canli sunucu]")
    test_api_health()
    test_api_endpoints()
    test_api_tts_short()

    print(f"\n=== Sonuc: PASS={_pass} FAIL={_fail} SKIP={_skip} ===")
    return 1 if _fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
