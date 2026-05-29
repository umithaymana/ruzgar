from __future__ import annotations

import time
from typing import Any


CURRENT_PHASE = 100
CURRENT_PHASE_LABEL = "Faz 86–100 · A→J"


def _phase(n: int, name: str, status: str = "tamam") -> dict[str, str]:
    return {"phase": f"Faz {n}", "name": name, "status": status}


def build_ui_manifest(*, health: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tek kaynak: masaüstü UI faz/kabiliyet metinlerini backend'den besler."""
    from ilim_assistant.motorlar.video_motoru import list_recent_downloads

    health = health or {}
    genel_tag = "Faz 98 · Orkestra şefi"
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
            "badge": "Ana Motor · Faz 100 hub (A→J)",
            "promise": (
                "Hub: programlama, video, ses, okuma, tercüme, hafıza, hızır. "
                "A→J planı kapandı — programlama Faz 98, tercüme atölye Blok J."
            ),
            "welcome_foot": "Faz 86–98 · Ümit & Gökçenur",
            "help_title": "Rüzgar — Faz 98 onaylı işlem + ROK",
        },
        "phases": [
            _phase(86, "Dalga I tamam"),
            _phase(87, "Dalga J tamam"),
            _phase(88, "Dalga K tamam"),
            _phase(89, "Hub cila v2"),
            _phase(90, "Prompt zinciri"),
            _phase(91, "Araç plan v4"),
            _phase(92, "Karar günlüğü"),
            _phase(93, "Test direktifi"),
            _phase(94, "Pre-turn test"),
            _phase(95, "Prompt önbellek"),
            _phase(96, "Anlık programlama"),
            _phase(97, "Kapsam kilidi"),
            _phase(98, "Onaylı yerel işlem", "aktif"),
            _phase(100, "A→J kapanış · hub notu", "aktif"),
        ],
        "motors": {
            "genel": {"tag": genel_tag},
            "hafiza": {"tag": "Faz 75 · Konuşarak yap (ROK)"},
            "hizir": {"tag": "Faz 84 · Hub + ticaret (ROK)"},
            "ses": {"tag": "Faz 72 · Konuşarak yap (ROK)"},
            "video": {"tag": "Faz 71/84 · İndir + ara (ROK)"},
            "okuma": {"tag": "Faz 73 · Konuşarak yap (ROK)"},
            "tercume": {"tag": "Faz 91–100 · Atölye UI (Blok J)"},
            "programlama": {"tag": "Faz 85–90 · Yerel zincir E3 + onay"},
        },
        "capabilities": [
            "Faz 98: dosya kopyala/taşı, pip, shell — «tamam yap» onayı ile",
            "Ana Motor hub: programlama, video, ses, okuma, tercüme, hafıza, hızır",
            "Video: URL indir · isimle YouTube ara",
            "Programlama: proje üret, ajan uyum, pytest",
            "ROK tüm yardımcı motorlar · Ümit cevap emri",
            "Faz 100: Ana Motor hub — tercüme/programlama/video/ses/okuma/hafıza/hızır",
            "Tercüme atölye: OCR, e-kitap, URL içe aktar, hedef kaydet",
        ],
        "video": {
            "download_api": "/api/video/download",
            "search_api": "/api/video/search",
            "recent_downloads": recent_downloads,
        },
    }
