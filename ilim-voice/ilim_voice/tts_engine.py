"""Metinden konuşma: XTTS (ses klonlama) + Farsça için MMS-TTS."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import torch

from ilim_voice.langs import MMS_TTS_MODEL_BY_NLLB, XTTS_LANG

_XTTS_MODEL_ID = os.environ.get("XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")

_xtts_api = None
_mms_cache: dict[str, tuple] = {}


def _get_xtts():
    global _xtts_api
    if _xtts_api is None:
        from TTS.api import TTS

        gpu = torch.cuda.is_available()
        _xtts_api = TTS(model_name=_XTTS_MODEL_ID, gpu=gpu)
    return _xtts_api


def _get_mms(nllb_code: str):
    if nllb_code not in MMS_TTS_MODEL_BY_NLLB:
        return None
    if nllb_code in _mms_cache:
        return _mms_cache[nllb_code]
    from transformers import AutoTokenizer, VitsModel

    mid = MMS_TTS_MODEL_BY_NLLB[nllb_code]
    tokenizer = AutoTokenizer.from_pretrained(mid)
    model = VitsModel.from_pretrained(mid)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()
    _mms_cache[nllb_code] = (tokenizer, model, device)
    return _mms_cache[nllb_code]


def synthesize_to_file(
    text: str,
    out_wav: str | Path,
    tgt_nllb: str,
    speaker_wav: Optional[str | Path] = None,
    sample_rate_hint: int = 24000,
) -> Path:
    """
    Metni sese çevirir.
    - XTTS desteklenen diller + speaker_wav: insana yakın klon ses.
    - Farsça (pes_Arab): MMS-TTS (referans ses kullanılmaz).
    - XTTS dili bilinmiyor veya referans yok: ilk yüklemede hata mesajı veya düşük kalite uyarısı.
    """
    text = text.strip()
    if not text:
        raise ValueError("Boş metin")

    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)

    # Farsça → MMS-TTS
    if tgt_nllb in MMS_TTS_MODEL_BY_NLLB:
        pack = _get_mms(tgt_nllb)
        if pack is None:
            raise RuntimeError("MMS-TTS yüklenemedi")
        tokenizer, model, device = pack
        inputs = tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            waveform = model(**inputs).waveform
        audio = waveform.squeeze().float().cpu().numpy()
        sr = model.config.sampling_rate
        sf.write(str(out_wav), audio, sr)
        return out_wav

    # XTTS çok dilli
    xtts_lang = XTTS_LANG.get(tgt_nllb)
    if xtts_lang is None:
        raise ValueError(
            f"Bu hedef dil için TTS eşlemesi yok: {tgt_nllb}. "
            "langs.py içine XTTS_LANG veya MMS_TTS_MODEL_BY_NLLB ekleyin."
        )

    if not speaker_wav or not Path(speaker_wav).is_file():
        raise FileNotFoundError(
            "XTTS için referans ses dosyası (speaker_wav) zorunludur — insana yakın sonuç için "
            "30–120 sn temiz .wav kaydı verin."
        )

    tts = _get_xtts()
    tts.tts_to_file(
        text=text,
        file_path=str(out_wav),
        speaker_wav=str(speaker_wav),
        language=xtts_lang,
    )
    return out_wav


def synthesize_numpy(
    text: str,
    tgt_nllb: str,
    speaker_wav: Optional[str | Path] = None,
) -> tuple[np.ndarray, int]:
    """(audio_float32_mono, sample_rate) döner — Gradio Audio bileşeni için."""
    tmp = Path(os.environ.get("TMPDIR", os.getcwd())) / "_ilim_voice_out.wav"
    path = synthesize_to_file(text, tmp, tgt_nllb, speaker_wav=speaker_wav)
    data, sr = sf.read(str(path), dtype="float32")
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    return data, int(sr)
