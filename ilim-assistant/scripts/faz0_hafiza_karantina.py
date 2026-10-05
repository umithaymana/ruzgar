# -*- coding: utf-8 -*-
"""Faz 0: BilgiKutuphane + din oturum ozetlerini karantinaya al (kisisel hatirla dokunulmaz)."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAFIZA = ROOT / "ruzgar_genel_hafiza.json"
OUT_DIR = ROOT / "arsiv" / "hafiza_karantina"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

DIN_KEYS = (
    "kuran",
    "kur'an",
    "kur’an",
    "hadis",
    "buhari",
    "tefsir",
    "fikih",
    "fıkıh",
    "ayet",
    "namaz",
    "islam",
    "diyanet",
    "sahih",
    "meal",
    "mushaf",
    "sünnet",
    "sunnet",
)


def _blob(it: dict) -> str:
    parts = []
    for k in (
        "soru",
        "cevap",
        "metin",
        "ozet",
        "baslik",
        "etiket",
        "motor_tipi",
        "tip",
        "icerik",
        "not",
        "kaynak",
    ):
        parts.append(str(it.get(k) or ""))
    return " ".join(parts).lower()


def _is_personal_hatirla(it: dict) -> bool:
    tip = str(it.get("motor_tipi") or it.get("tip") or "").lower()
    etiket = str(it.get("etiket") or "").lower()
    if "hatirla" in tip or "hatırla" in tip:
        return True
    if "kisisel" in tip or "kişisel" in tip or "profil" in tip:
        return True
    if "hatirla" in etiket or "aile" in etiket:
        return True
    return False


def _should_quarantine(it: dict) -> tuple[bool, str]:
    if not isinstance(it, dict):
        return False, ""
    if _is_personal_hatirla(it):
        return False, ""
    tip = str(it.get("motor_tipi") or it.get("tip") or "")
    if tip == "BilgiKutuphane":
        return True, "BilgiKutuphane"
    blob = _blob(it)
    if any(k in blob for k in DIN_KEYS):
        # Oturum ozeti / soft din mention — karantinaya
        return True, "din_kelime_oturum"
    return False, ""


def main() -> None:
    raw = HAFIZA.read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, list):
        items = data
        container = "list"
    elif isinstance(data, dict):
        list_key = None
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                list_key = k
                break
        if list_key is None:
            raise SystemExit(f"Liste bulunamadi. Keys={list(data.keys())[:20]}")
        items = data[list_key]
        container = list_key
    else:
        raise SystemExit(f"Beklenmeyen tip: {type(data)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backup = OUT_DIR / f"ruzgar_genel_hafiza_BEFORE_{STAMP}.json"
    shutil.copy2(HAFIZA, backup)

    keep: list = []
    quarantined: list = []
    reasons: dict[str, int] = {}
    for it in items:
        yes, reason = _should_quarantine(it if isinstance(it, dict) else {})
        if yes:
            q = dict(it)
            q["_karantina_neden"] = reason
            q["_karantina_ts"] = STAMP
            quarantined.append(q)
            reasons[reason] = reasons.get(reason, 0) + 1
        else:
            keep.append(it)

    q_path = OUT_DIR / f"karantina_{STAMP}.jsonl"
    with q_path.open("w", encoding="utf-8") as f:
        for row in quarantined:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = {
        "ok": True,
        "stamp": STAMP,
        "container": container,
        "onceki_adet": len(items),
        "kalan_adet": len(keep),
        "karantina_adet": len(quarantined),
        "nedenler": reasons,
        "backup": str(backup.relative_to(ROOT)),
        "karantina_dosya": str(q_path.relative_to(ROOT)),
        "not": "Kisisel hatirla/profil dokunulmadi. BilgiKutuphane + din kelimeli kayitlar karantinada.",
    }
    (OUT_DIR / f"rapor_{STAMP}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if container == "list":
        out_data = keep
    else:
        out_data = dict(data)
        out_data[container] = keep

    HAFIZA.write_text(
        json.dumps(out_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
