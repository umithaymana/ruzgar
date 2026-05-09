# Created by Ümit & Gökçenur
"""Merkezi Zihin Havuzu — Genel, İlim Hazinesi ve Arşiv tek RAG indeksini paylaşır."""

from __future__ import annotations

import os


def merkezi_zihin_defaults_enabled() -> bool:
    return (
        os.environ.get("RUZGAR_MERKEZI_ZIHIN", "1").strip().lower()
        not in ("0", "false", "no")
    )


def include_all_modes_in_pool() -> bool:
    """Ses / üretim / video / hızlı modlarda da RAG dene (daha fazla yükleme)."""
    return os.environ.get(
        "RUZGAR_MERKEZI_ZIHIN_INCLUDE_ALL_MODES", "0"
    ).strip().lower() in ("1", "true", "yes")


def no_rag_modes() -> frozenset[str]:
    if merkezi_zihin_defaults_enabled() and include_all_modes_in_pool():
        return frozenset()
    return frozenset({"ses", "uretim", "video", "hizli"})


def model_directive_for_unified_retrieval() -> str:
    if not merkezi_zihin_defaults_enabled():
        return ""
    return (
        "\n\n[TALİMAT — Merkezi Zihin Havuzu — Ümit & Gökçenur]\n"
        "Yerel metin bağlamı **tek indeks**: Genel külliyat, İlim Hazinesi ve "
        "**Arşiv** (tasavvuf vb.) ortak havuzdadır — uygun olduğunda bu kaynakları dikkate al. "
        "Kullanıcı yalın günlük sohbet ediyorsa gereksiz ders / tahlil açma.\n"
    )
