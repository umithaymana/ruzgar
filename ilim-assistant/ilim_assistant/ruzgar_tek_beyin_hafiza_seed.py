# Created by Ümit & Gökçenur
"""Çekirdek kişisel profiller — ruzgar_genel_hafiza.json'a kalıcı tohum kayıtlar."""

from __future__ import annotations

from typing import Any

_SEEDED = False

_CORE_PROFILES: tuple[tuple[str, str], ...] = (
    (
        "Gökçenur kimdir",
        "Gökçenur Haymana, Mimar Ümit'in eşi ve Rüzgar projesinin mimarlarından biridir. "
        "Teknik ve yaratıcı fikirleriyle projeye güç verir; seninle birlikte bu sistemi inşa ediyor.",
    ),
    (
        "gökçe nur haymana kimdir",
        "Gökçenur Haymana, Mimar Ümit'in eşi ve Rüzgar projesinin mimarlarından biridir. "
        "Teknik ve yaratıcı fikirleriyle projeye güç verir.",
    ),
    (
        "Gökçenur bu projede ne yapıyor",
        "Gökçenur, bu projenin en önemli parçalarından biri; teknik ve yaratıcı fikirleriyle "
        "Rüzgar'a güç veriyor ve Mimar Ümit ile birlikte geliştiriyor.",
    ),
    (
        "Yavuz Kara kimdir",
        "Yavuz Kara, Mimar Ümit Bey'in teyzesinin oğludur — yakın aile çevresinden, senin "
        "bildiğin biri; ansiklopedik bir isim değil.",
    ),
    (
        "yavuz kara kimdir",
        "Yavuz Kara, Mimar Ümit Bey'in teyzesinin oğludur — yakın aile çevresinden.",
    ),
    (
        "Ümit kimdir",
        "Ümit Bey, Rüzgar projesinin mimarı ve benim kullanıcım; Gökçenur ile birlikte "
        "bu süper asistanı geliştiriyor.",
    ),
    (
        "Rüzgar kimdir",
        "Ben Rüzgar; Mimar Ümit ve Gökçenur tarafından geliştirilen, kişiye özel süper asistanım. "
        "Sohbetlerini, projelerini ve hafızandaki bilgileri takip ederim.",
    ),
)


def ensure_core_hafiza_profiles() -> dict[str, Any]:
    """İlk turda çekirdek profilleri diske yaz (eksikse)."""
    global _SEEDED
    if _SEEDED:
        return {"ok": True, "skipped": True}
    _SEEDED = True
    added = 0
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        motor = get_hafiza_motor()
        for soru, cevap in _CORE_PROFILES:
            motor._upsert_kayit("Hafıza", soru, cevap)
            added += 1
        if added:
            motor._sync_hafiza_view()
            motor._dosyaya_kaydet()
        return {"ok": True, "added": added}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:160]}
