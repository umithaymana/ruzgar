# Created by Ümit & Gökçenur
"""Ruzgar Cekirdegi: coklu motorlari tek merkezde orkestre eder.
Bilim motoru Kultur ve Ilim Hazinesi vizyonuyla (dort kuliyat arsivi + metin turu) beslenir.

Motor bağlamları tembel yüklenir (Ümit & Gökçenur hız paketi — tek seferde tüm motor importu yok).

Kuvve-i Hafıza (kalıcı sohbet + kişisel veri) ana yolda `prepare_turn` ile modele enjekte edilir;
SQLite: `ilim-assistant/hafiza/gecmis_sohbetler.db`.
"""

from ilim_assistant.dinamit_gelisme import dinamit_heartbeat
from ilim_assistant.ruzgar_perf import RUZGAR_PERF_MIMAR


def build_core_context(message: str) -> str:
    from ilim_assistant.bilim_motoru import build_motor_context as bilim_context
    from ilim_assistant.programlama_motoru import build_motor_context as programlama_context
    from ilim_assistant.ses_motoru import build_motor_context as ses_context
    from ilim_assistant.tercume_motoru import build_motor_context as tercume_context
    from ilim_assistant.video_motoru import build_motor_context as video_context

    prompt = (message or "").strip()
    parts = []
    _dh = dinamit_heartbeat()
    if _dh.strip():
        parts.append(_dh.strip())
    parts.extend(
        [
        f"[RUZGAR CEKIRDEGI — {RUZGAR_PERF_MIMAR}]",
        "Bu merkez; Ses, Video, Bilim (ilim/tarih), Tercume ve Programlama motorlarini birlikte kullanir.",
        "Karmasik cok-asamali taleplerde islemleri asama asama planla, ara ciktilari belirt ve",
        "mumkun oldugunda tek akista tamamlanabilir bir eylem zinciri olustur.",
        "Ornek senaryo: video indir -> sesi ayikla -> tercume/tecvid isle -> videoya geri birlestir.",
        "",
        ses_context(prompt),
        "",
        video_context(prompt),
        "",
        bilim_context(prompt),
        "",
        tercume_context(prompt),
        "",
        programlama_context(prompt),
        ]
    )
    return "\n".join(parts)
