# -*- coding: utf-8 -*-
"""Sıra 2: mevcut eser/yazılım envanteri — çift yükleme engeli. RAG yok."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALAN = ROOT / "knowledge/ortak_kaynak/alanlar"
RAF = ALAN / "bilgisayar_eserleri"
OUT = RAF / "SAHNE_Y1_ENVANTER_2026-11-13.json"

# Plan omurga / meslek → mevcut kalın paketler (yeniden indirme YOK)
ZATEN_VAR = {
    "omurga_harita_maplibre_natural_earth": {
        "kaynak": "25_ILERI_10_2 + 10_4",
        "kanit": ["cografya_tarih (77 parça)", "atlas_natural_earth"],
        "durum": "zaten_var",
    },
    "omurga_uzay_astro": {
        "kaynak": "25_ILERI_10_2",
        "kanit": ["uzay_astro (53 parça)"],
        "durum": "zaten_var",
    },
    "omurga_ffmpeg_video": {
        "kaynak": "25_ILERI_D + 10_2",
        "kanit": ["ffmpeg", "atolye_gece", "sistem ffmpeg winget"],
        "durum": "zaten_var",
    },
    "omurga_openstax_fenni": {
        "kaynak": "25_ILERI_10_4",
        "kanit": ["openstax_derin", "mit_ocw_secme"],
        "durum": "zaten_var",
    },
    "omurga_ses_stt_tts": {
        "kaynak": "25_ILERI_B",
        "kanit": ["whisper", "piper", "web_audio_mdn"],
        "durum": "zaten_var",
    },
    "omurga_homelab_cam": {
        "kaynak": "25_ILERI_I",
        "kanit": ["home_assistant", "esp_idf"],
        "durum": "zaten_var",
    },
    "omurga_three_webrtc": {
        "kaynak": "25_ILERI_D",
        "kanit": ["godot_three_cam", "webrtc_mdn", "opencv"],
        "durum": "zaten_var",
    },
    "yazilimci_programlama": {
        "kaynak": "25_ILERI_F + bilgisayar_muhendisligi + dals 01-12",
        "kanit": ["tree_sitter", "ollama", "playwright", "7034+ md programlama dalı"],
        "durum": "zaten_var",
    },
    "arastirmaci_tercume_hafiza": {
        "kaynak": "25_ILERI_A/C + Şamile/ilim",
        "kanit": ["ir_book", "marian_opus", "camel_farasa", "knowledge/ilim"],
        "durum": "zaten_var_kismi",
    },
    "yazilim_ffmpeg_opencv": {
        "kaynak": "tools + sistem",
        "kanit": ["opencv 5.0.0", "ffmpeg.exe winget", "video_ffmpeg.py"],
        "durum": "zaten_var",
    },
}


def md_stats(path: Path) -> dict:
    files = list(path.rglob("*.md")) if path.exists() else []
    return {
        "md": len(files),
        "kb": round(sum(f.stat().st_size for f in files) / 1024, 1) if files else 0.0,
    }


def main() -> int:
    ince_alanlar = {}
    for name in sorted(p.name for p in ALAN.iterdir() if p.is_dir()):
        if name == "bilgisayar_eserleri":
            continue
        st = md_stats(ALAN / name)
        ince_alanlar[name] = {**st, "ince_mi": st["md"] < 20 or st["kb"] < 50}

    eksik_meslek_raflari = [
        "mimar_muteahhit_bina_3d_4d",  # FreeCAD var; bina/şehircilik kalınlaştırılacak
        "yonetmen_kurgu_teori",  # ffmpeg var; kurgu teorisi kalınlaştırılacak
        "doktor_egitmen_anatomi",  # alan stub
        "avukat_noter_dosya",  # hukuk stub
        "tarihci_rehber_atlas",  # nebula var; rehber kalın
        "muhendis_simulasyon",  # fizik/elektronik var; simülasyon paket
        "gazeteci_acik_veri",
        "muzisyen_partisyon",  # muzik stub
        "ciftci_saha_hava",
        "ogrenci_quiz_hafiza",
        "aile_cihaz_defteri",
        "gezgin_dil_cep",
    ]

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "plan": "RUZGAR_SAHNE_BASLAMA_PLANI_2026-11-13.docx sıra 2",
        "kural": "zaten_var → ikinci indirme YOK; RAG yok",
        "zaten_var": ZATEN_VAR,
        "ince_alan_stublar": ince_alanlar,
        "siradaki_kalin_dolum": eksik_meslek_raflari,
        "bilgisayar_eserleri_not": "On binlerce md; omurga büyük ölçüde burada.",
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("ince_stub", sum(1 for v in ince_alanlar.values() if v["ince_mi"]))
    print("eksik_meslek", len(eksik_meslek_raflari))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
