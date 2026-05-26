from __future__ import annotations

import time
from typing import Any


CURRENT_PHASE = 77
CURRENT_PHASE_LABEL = "Faz 68–77"


def _phase(n: int, name: str, status: str = "tamam") -> dict[str, str]:
    return {"phase": f"Faz {n}", "name": name, "status": status}


def build_ui_manifest(*, health: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tek kaynak: masaüstü UI faz/kabiliyet metinlerini backend'den besler."""
    from ilim_assistant.motorlar.video_motoru import list_recent_downloads

    health = health or {}
    super_brain = health.get("super_brain") if isinstance(health, dict) else {}
    gemini_ok = bool((super_brain or {}).get("gemini_configured"))
    recent_downloads = [
        row for row in list_recent_downloads(8) if isinstance(row, dict) and row.get("ok")
    ]

    return {
        "ok": True,
        "version": 2,
        "generated_at": time.time(),
        "current_phase": CURRENT_PHASE,
        "current_phase_label": CURRENT_PHASE_LABEL,
        "dashboard": {
            "badge": "Ana Motor · Hub Faz 76",
            "promise": (
                "Orkestra şefi: Ana Motor'dan doğal cümleyle yardımcı motora yönlendirme. "
                "Tüm yardımcı motorlar ROK (Faz 68–75) + hub (Faz 76)."
            ),
            "welcome_foot": "Faz 68–77 · Ümit & Gökçenur",
            "help_title": "Rüzgar — Konuşarak yap (ROK)",
        },
        "phases": [
            _phase(0, "UI iskeleti"),
            _phase(1, "Programlama", "1.3 + debug"),
            _phase(2, "Okuma"),
            _phase(3, "Tercüme"),
            _phase(4, "Ses"),
            _phase(5, "Video", "v5 + indirme"),
            _phase(6, "Ana Motor akıl"),
            _phase(7, "Cila"),
            _phase(8, "Merkezi hafıza"),
            _phase(9, "Gemini-first hız"),
            _phase(10, "Otonom debug"),
            _phase(11, "İdrak ön-işlemi"),
            _phase(12, "Cevap kalitesi"),
            _phase(13, "Kişisel hafıza"),
            _phase(14, "Self-test"),
            _phase(15, "Debug v2"),
            _phase(16, "Görevler + hatırlatıcı", "aktif"),
        ],
        "motors": {
            "genel": {"tag": f"Hub Faz 76 · Gemini {'✓' if gemini_ok else '?'}"},
            "hafiza": {"tag": "Faz 75 · Konuşarak yap (ROK)"},
            "hizir": {"tag": "Ekonomik avcı · operasyon"},
            "ses": {"tag": "Faz 72 · Konuşarak yap (ROK)"},
            "video": {"tag": "Faz 71 · Konuşarak yap (ROK)"},
            "okuma": {"tag": "Faz 73 · Konuşarak yap (ROK)"},
            "tercume": {"tag": "Faz 74 · Konuşarak yap (ROK)"},
            "programlama": {"tag": "Faz 68–70 · Konuşarak yap"},
        },
        "capabilities": [
            "Ansiklopedik soruda Gemini-first, ağır indeks atlama",
            "Kod modunda yerel ilim indeksi atlama",
            "İdrak ön-işlemi ve devam cümlesi genişletme",
            "hatırla / unut / profil komutları",
            "görev oluştur / görev listesi",
            "hatırlatıcı pending/ack API",
            "YouTube/web video indirme + son indirmeler",
            "Ses Faz 72: konuşarak profil seçimi · ses ayarları · oku: yönergesi",
            "Ses API: /api/tts · /api/ses/settings",
            "Okuma Faz 73: arsiv durumu · metin türü · kaynak ipucu",
            "Tercüme Faz 74: dil çifti · dil listesi · altyazı yönergesi",
            "Hafıza Faz 75: hatırla · görev · hatırlatıcı · hafıza durumu",
            "Ana Motor Faz 76: hub yönlendirme · /api/ana-motor/hub-route",
            "Faz 77: video indirme doğrudan API · scripts/rok_smoke.py KPI",
            "self-test API",
            "Programlama Faz 8: şablon sonrası atölye odak + api başlat/durdur",
            "Programlama Faz 10: workspace indeks, @@read/@@write, patch onayla, Ana Motor delege",
            "Web şablonları: static_site (HTML) · react_vite (SPA)",
            "Faz 11: programlama orkestra adımları + atölye patch şeridi",
            "Faz 12: patch diff önizleme + programlama_smoke.py + hızlı şablon",
            "Faz 13: proje tara / proje özeti dosya haritası · @@find · sembol özeti",
            "Faz 14: görev: proje hedef — çok tur patch + doğrulama · görev durdur",
            "Faz 15: npm install/build/test · git status/diff — yalnızca projects/",
            "Faz 16: çok dosya patch — diff + Kabul/Red + toplu uygula + .bak geri al",
            "Faz 17: git durum/diff · commit öner · onaylı git commit (no --no-verify)",
            "Faz 18: programlama_smoke --ci · SLO scaffold<30s · birleşik üstayol raporu",
            "Faz 19: görev v2 — iş:/yap: · doğal cümle · 120sn · Groq öncelik · erken dur",
            "Faz 20: birleşik ajan · ruzgar-tool read/write/grep/verify",
        ],
        "video": {
            "download_api": "/api/video/download",
            "recent_downloads": recent_downloads,
        },
    }
