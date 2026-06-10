# Created by Ümit & Gökçenur
"""Ana Motor Faz Z2 — motor rehberi (? yardım penceresi içeriği)."""

from __future__ import annotations

import os
from typing import Any

FAZ_Z_REHBER_VERSION = "ana-motor-motor-rehberi-z2-2026-06-10"


def motor_rehberi_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_REHBERI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def chat_simple_default() -> bool:
    return os.environ.get("RUZGAR_ANA_CHAT_SIMPLE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def archive_fold_default() -> bool:
    return os.environ.get("RUZGAR_ANA_ARCHIVE_FOLD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _section(
    motor_id: str,
    title: str,
    purpose: str,
    bullets: list[str],
) -> dict[str, Any]:
    return {
        "id": motor_id,
        "title": title,
        "purpose": purpose,
        "bullets": bullets,
    }


def build_motor_rehberi() -> dict[str, Any]:
    sections = [
        _section(
            "genel",
            "Ana Motor (genel sohbet)",
            "Tek sohbetten bilgi, arşiv, web ve motor yönlendirme.",
            [
                "Web ara + sayfa oku (0–3) ile güncel kaynak",
                "@@dosya/yol — workspace dosyası okuma",
                "Faz W: backend motor yürütme (video/tercüme anında)",
                "Faz X: ajan 2.0 — çok tur patch + doğrulama",
                "Faz Y: güven rozeti + LLM kalite denetimi",
                "Faz Z: sade sohbet, katlanır arşiv, multi-hop RAG",
            ],
        ),
        _section(
            "tercume",
            "Tercüme motoru",
            "Kitap/PDF çeviri, segment düzenleme ve arşiv çıktısı.",
            [
                "Çalışma: kaynak/hedef dil, sayfa aralığı, segment düzenleme",
                "«Bu sayfayı çevir» / «Tamamını çevir» — sohbetten doğal komut",
                "Çıktı: ilim-assistant/arsiv/tercume-output",
                "Arşiv indirme paneli — katlanır liste (Faz Z uyumlu)",
            ],
        ),
        _section(
            "programlama",
            "Programlama motoru",
            "Kod modu, patch onayı ve workspace düzenleme.",
            [
                "Kod modu — yerel ilim indeksini atlar, odak kod",
                "Ajan döngüsü: staging → py_compile → uygula",
                "Patch onay kartı dashboard’da (Faz E3)",
            ],
        ),
        _section(
            "hafiza",
            "Hafıza motoru",
            "hatırla / unut / profil ve oturum arşivi.",
            [
                "«hatırla …» — ruzgar_genel_hafiza.json",
                "Arşiv oturumu — dashboard Arşiv & birleştir (katlanır)",
                "Timeline filtreleri ve CSV/JSON dışa aktarma",
            ],
        ),
        _section(
            "video",
            "Video motoru",
            "Sinema, indirme, kesim ve V5 metinden film.",
            [
                "Sinema URL + timeline kesim",
                "«video oluştur» — sahne planı + Edge-TTS montaj",
                "FFmpeg + yt-dlp + sunucu 8779 gerekli",
            ],
        ),
        _section(
            "hizir",
            "HIZIR",
            "Pazar taraması ve merkezi bellek vitrini.",
            [
                "Sayfayı Temizle — vitrin + önbellek",
                "Hızlı Yenile — mevcut sorguyla tarama",
            ],
        ),
        _section(
            "ses",
            "Ses motoru",
            "TTS, tilavet ve ses referansları.",
            [
                "Sesli yanıt — sohbet composer’dan aç/kapa",
                "Tilavet profilleri — arşiv/ses-referans",
            ],
        ),
        _section(
            "mimar",
            "Mimar motoru",
            "Fotoğraf, resim/sanat ve tasarım atölyesi.",
            [
                "3 bağımsız sayfa — yan sohbet + tek aktif panel",
                "Çalışma köprüsü — Ana Motor’dan panel açma",
            ],
        ),
    ]
    return {
        "ok": True,
        "version": FAZ_Z_REHBER_VERSION,
        "enabled": motor_rehberi_enabled(),
        "chat_simple_default": chat_simple_default(),
        "archive_fold_default": archive_fold_default(),
        "sections": sections,
    }


def get_motor_rehberi_status() -> dict[str, Any]:
    return build_motor_rehberi()
