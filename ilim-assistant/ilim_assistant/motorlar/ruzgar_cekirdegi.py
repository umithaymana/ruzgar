# Created by Ümit & Gökçenur
"""Ruzgar Cekirdegi: coklu motorlari tek merkezde orkestre eder.

Boot vs orkestra (Faz 5 — net hikâye):
- Boot (`desktop_server._boot_motorlar_anaonce`): 7 motor ısınır —
  ses → video → **okuma** → **mimar** → tercüme → **hafıza** → programlama
  (+ ana motor + bu çekirdek modülü).
- Orkestra (`build_core_context`): 5’li bağlam birleştirir —
  Ses, Video, **Bilim** (okuma_motoru yüzü / `bilim_motoru` shim), Tercüme, Programlama.
- **Mimar** ve **Hafıza** boot’ta ısınır ama bu fonksiyon onları çağırmaz;
  UI «Mimar» / «Hafıza» / «Okuma» modlarında `prepare_turn` kendi `build_motor_context`
  yolunu kullanır (5’li çekirdek zorlanmaz).

Bilim motoru = Okuma/İlim arşivi yüzü (isim kayması bilinçli shim).

Kuvve-i Hafıza (kalıcı sohbet): SQLite `hafiza/gecmis_sohbetler.db` + hafiza modu bağlamı.
"""

from ilim_assistant.dinamit_gelisme import dinamit_heartbeat
from ilim_assistant.ruzgar_perf import RUZGAR_PERF_MIMAR


def build_core_context(message: str) -> str:
    from ilim_assistant.bilim_motoru import build_motor_context as bilim_context
    from ilim_assistant.motorlar.programlama_motoru import (
        build_motor_context as programlama_context,
    )
    from ilim_assistant.ses_motoru import build_motor_context as ses_context
    from ilim_assistant.tercume_motoru import build_motor_context as tercume_context
    from ilim_assistant.motorlar.video_motoru import build_motor_context as video_context

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
