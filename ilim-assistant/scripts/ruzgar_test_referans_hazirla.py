#!/usr/bin/env python3
"""Test klon referansları — kuran.wav, gazel.wav, ilahi.wav (Commons, kişisel test)."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = "RuzgarTestReferans/1.0 (local XTTS test)"
_IA = Path(__file__).resolve().parents[1]
_REF = _IA / "arsiv" / "ses-referans"

# Commons — kısa, temiz konuşma/tilavet (CC / public domain)
_JOBS: list[tuple[str, str, float, float, str]] = [
    (
        "kuran",
        "File:Sura Minshawi 96.ogg",
        0.0,
        75.0,
        "Sure Al-Alak tilaveti — Muhammad Siddiq Al-Minshawi (Commons PD)",
    ),
    (
        "gazel",
        "File:002 Misra-i Berceste 17.04.2013.OGG",
        180.0,
        75.0,
        "Misra-i Berceste şiir okuma kesiti",
    ),
    (
        "ilahi",
        "File:002 Nur iklimi 20.05.2010 Prof.Dr M CESUR.ogg",
        45.0,
        60.0,
        "Tasavvuf sohbet kesiti — yumuşak vokal ilahi profili testi (CC)",
    ),
]


def _wiki_url(title: str) -> str:
    q = urllib.parse.urlencode(
        {
            "action": "query",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
        }
    )
    req = urllib.request.Request(
        f"https://commons.wikimedia.org/w/api.php?{q}",
        headers={"User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    page = next(iter(data["query"]["pages"].values()))
    if "missing" in page:
        raise FileNotFoundError(f"Commons dosyası yok: {title}")
    return str(page["imageinfo"][0]["url"])


def _fetch(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        dest.write_bytes(r.read())


def _trim_wav(src: Path, dest: Path, start: float, dur: float) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start:.2f}",
            "-t",
            f"{dur:.2f}",
            "-i",
            str(src),
            "-vn",
            "-ar",
            "22050",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


def main() -> int:
    if str(_IA) not in sys.path:
        sys.path.insert(0, str(_IA))
    from ilim_assistant.env_bootstrap import ensure_ruzgar_env
    from ilim_assistant.motorlar.ses_klon_motoru import normalize_reference_to_wav

    ensure_ruzgar_env()
    _REF.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for prof, title, start, dur, note in _JOBS:
        print(f"\n[{prof}] {note}")
        url = _wiki_url(title)
        suffix = Path(urllib.parse.urlparse(url).path).suffix or ".bin"
        raw = _REF / f"_{prof}_raw{suffix}"
        print(f"  indir: {url[:90]}…")
        _fetch(url, raw)
        tmp = _REF / f"_{prof}_trim.wav"
        _trim_wav(raw, tmp, start, dur)
        out = _REF / f"{prof}.wav"
        normalize_reference_to_wav(tmp, out)
        raw.unlink(missing_ok=True)
        tmp.unlink(missing_ok=True)
        print(f"  OK {out.name} ({out.stat().st_size // 1024} KB, {dur:.0f} sn)")
        manifest.append(
            {
                "profil": prof,
                "dosya": out.as_posix(),
                "kaynak": title,
                "not_tr": note,
            }
        )

    meta = _REF / "TEST_REFERANS_README.json"
    meta.write_text(
        json.dumps({"referanslar": manifest, "kullanim": "Rüzgar tilavet/klon testi"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nTamam — 3 referans hazır: {_REF}")
    print("Rüzgar'da okutulacak örnek metinler için scripts/ruzgar_test_okuma_metinleri.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
