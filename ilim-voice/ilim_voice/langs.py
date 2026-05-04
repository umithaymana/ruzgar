"""NLLB dil kodları ve arayüz etiketleri."""

# facebook/nllb-200-* için kaynak/hedef kodları
NLLB_CODES = {
    "Türkçe": "tur_Latn",
    "İngilizce": "eng_Latn",
    "Arapça": "arb_Arab",
    "Farsça": "pes_Arab",
    "Almanca": "deu_Latn",
    "Fransızca": "fra_Latn",
    "Rusça": "rus_Cyrl",
    "Urduca": "urd_Arab",
    "Endonezce": "ind_Latn",
    "Özbekça": "uzn_Latn",
}

# XTTS v2 için kısa dil kodu (ses üretimi); listede olmayanlar MMS-TTS veya metin diline göre yaklaşım
XTTS_LANG = {
    "tur_Latn": "tr",
    "eng_Latn": "en",
    "arb_Arab": "ar",
    "deu_Latn": "de",
    "fra_Latn": "fr",
    "rus_Cyrl": "ru",
    "ind_Latn": "id",
}

# Farsça XTTS'te yok → MMS-TTS checkpoint
MMS_TTS_MODEL_BY_NLLB = {
    "pes_Arab": "facebook/mms-tts-fas",
}

# faster-whisper dil kodları → NLLB (otomatik akış için)
WHISPER_TO_NLLB = {
    "tr": "tur_Latn",
    "en": "eng_Latn",
    "ar": "arb_Arab",
    "fa": "pes_Arab",
    "de": "deu_Latn",
    "fr": "fra_Latn",
    "ru": "rus_Cyrl",
    "id": "ind_Latn",
    "uz": "uzn_Latn",
}
