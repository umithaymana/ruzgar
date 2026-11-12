# Created by Ümit & Gökçenur
"""
Şamile derin çekirdek — Mimar onaylı müteber eserler (2026-11-12).

Kural: Çekirdek eserlerde sayfa/satır atlanmaz; Rüzgar okur, analiz eder, sohbet dilinde anlatır.
Diğer eserler yüzey; net soruda onlara da inilebilir.

Liste Word önerisinden gelir; DB eşlemesi ayrı turda.
Kapat: RUZGAR_SAMILE_DERIN=0
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

VERSION = "ruzgar-samile-derin-cekirdek-v1-2026-11-12"
_ESLESME_PATH = (
    Path(__file__).resolve().parents[1] / "docs" / "SAMILE_DERIN_CEKIRDEK_ESLESME.json"
)

# Ana dallar — derin öncelik (kategori kodları)
ANA_DERIN_CATS: frozenset[str] = frozenset(
    {
        "01_akaid",
        "03_tefsir",
        "06_hadis_sunen",
        "07_hadis_serh",
        "11_usul_fikih",
        "14_hanefi",
        "15_maliki",
        "16_safii",
        "17_hanbeli",
        "24_siyer",
    }
)


def derin_enabled() -> bool:
    return os.environ.get("RUZGAR_SAMILE_DERIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def is_ana_derin_cat(cat: str) -> bool:
    return (cat or "").strip() in ANA_DERIN_CATS


def derin_okuma_directive(*, cat_hint: str = "") -> str:
    if not derin_enabled():
        return ""
    ana = is_ana_derin_cat(cat_hint) if cat_hint else True
    if not ana:
        return (
            "\n\n[TALİMAT — ŞAMİLE YÜZEY / NET SORU]\n"
            "Bu tur yüzey rafı olabilir. Net eser/metin sorulursa yine doğru oku; "
            "uydurma yok. Çekirdek müteber varsa onu tercih et.\n"
        )
    return (
        "\n\n[TALİMAT — ŞAMİLE DERİN ÇEKİRDEK — ZORUNLU]\n"
        "Müteber çekirdek eserlerde **sayfa ve satır atlama**. "
        "Pasajı tam oku, sonra analiz et; sohbet dilinde anlat. "
        "Harf kaydırma / benzer isim uydurma yasak. "
        "Bağlamdaki metne sadık kal; yoksa öğret cümlesi.\n"
        "Liste: docs/SAMILE_DERIN_CEKIRDEK_ESER_LISTESI_ONERI.docx (Mimar onayı).\n"
    )


def load_eslesme() -> dict[str, Any]:
    """Onaylı/öneri eşleme JSON — yoksa boş."""
    try:
        if _ESLESME_PATH.is_file():
            return json.loads(_ESLESME_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def matched_book_ids() -> list[int]:
    data = load_eslesme()
    out: list[int] = []
    for row in data.get("rows") or []:
        if row.get("status") == "OK" and row.get("book_id"):
            try:
                out.append(int(row["book_id"]))
            except (TypeError, ValueError):
                continue
    return out


def public_meta() -> dict[str, Any]:
    data = load_eslesme()
    return {
        "version": VERSION,
        "enabled": derin_enabled(),
        "ana_cats": sorted(ANA_DERIN_CATS),
        "rule": "cekirdek_eserlerde_satir_atlama_yok",
        "eslesme_matched": int(data.get("matched") or 0),
        "eslesme_unmatched": int(data.get("unmatched") or 0),
        "matched_book_ids": matched_book_ids()[:80],
    }
