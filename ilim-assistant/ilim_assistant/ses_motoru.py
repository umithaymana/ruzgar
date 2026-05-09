# Created by Ümit & Gökçenur
"""Uyumluluk katmanı: asıl ses motoru `motorlar/ses_motoru` içindedir."""

from ilim_assistant.motorlar.ses_motoru import (  # noqa: F401
    EDGE_VOICES,
    IcerikYolu,
    MIMAR_IMZA,
    PROJE_ADI,
    SesKarakteri,
    analiz_icerik_yolu,
    build_motor_context,
    build_tts_yonergesi,
    edge_pitch_string,
    edge_rate_yuzdesi,
    kutsal_okuma_tonu_gerekli,
    metadata_json_imza,
    normalize_ses_karakteri,
    pdf_metni_oku,
    profil_aciklamasi,
    ton_metni_icerik,
    tts_metadata_kimlik,
    varsayilan_karakter_icerige,
)
