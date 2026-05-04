"""
İlim Voice — çok dilli çeviri + STT + TTS web arayüzü.

Çalıştırma (proje kökünde):
  pip install -r requirements.txt
  python gradio_app.py

Ortam:
  NLLB_MODEL  facebook/nllb-200-distilled-600M (varsayılan) veya daha büyük model
  WHISPER_MODEL  large-v3 | medium | small ...
"""

from __future__ import annotations

import os
import tempfile

import gradio as gr

from ilim_voice.langs import NLLB_CODES
from ilim_voice.pipeline import speech_translate_speech, text_translate_speech

LANG_CHOICES = list(NLLB_CODES.keys())

WHISPER_HINT = [
    ("Otomatik", None),
    ("Türkçe", "tr"),
    ("İngilizce", "en"),
    ("Arapça", "ar"),
    ("Farsça", "fa"),
    ("Almanca", "de"),
    ("Fransızca", "fr"),
]


def ui_text_to_speech(text: str, src: str, tgt: str, ref_audio):
    if not text or not text.strip():
        return None, "Metin girin."
    ref_path = None
    if ref_audio is not None:
        ref_path = ref_audio if isinstance(ref_audio, str) else getattr(ref_audio, "name", None)
    try:
        fd, tmp_out = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        _, translated, wav = text_translate_speech(
            text.strip(), src, tgt, speaker_wav=ref_path, out_path=tmp_out
        )
        note = f"Çeviri:\n{translated}\n\n"
        if tgt == "Farsça":
            note += "(Farsça TTS: MMS — referans ses kullanılmaz.)"
        elif not ref_path:
            note += "Uyarı: XTTS için referans .wav yükleyin; yoksa hata alırsınız (Farsça hariç)."
        return str(wav), note
    except Exception as e:
        return None, str(e)


def ui_speech_pipeline(audio, whisper_hint, manual_src: str, tgt: str, ref_audio):
    if audio is None:
        return None, "Ses dosyası yükleyin."
    path = audio if isinstance(audio, str) else getattr(audio, "name", None)
    if not path:
        return None, "Dosya okunamadı."

    hint = None
    for label, code in WHISPER_HINT:
        if label == whisper_hint:
            hint = code
            break

    ref_path = None
    if ref_audio is not None:
        ref_path = ref_audio if isinstance(ref_audio, str) else getattr(ref_audio, "name", None)

    manual = manual_src if manual_src != "Otomatik (Whisper)" else None

    try:
        fd, tmp_out = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        transcript, translated, src_code, wav = speech_translate_speech(
            path,
            tgt,
            speaker_wav=ref_path,
            whisper_lang=hint,
            manual_src_label=manual,
            out_path=tmp_out,
        )
        note = (
            f"Algılanan / kaynak NLLB: {src_code}\n\n"
            f"Transkript:\n{transcript}\n\n"
            f"Çeviri:\n{translated}"
        )
        return str(wav), note
    except Exception as e:
        return None, str(e)


def build_demo():
    with gr.Blocks(title="İlim Voice") as demo:
        gr.Markdown(
            "## İlim Voice — çeviri + okuma (açık kaynak)\n"
            "**XTTS** için insana yakın ses: 30–120 sn temiz **Türkçe** referans kaydı yükleyin. "
            "**Farsça** hedefte MMS-TTS kullanılır (referans gerekmez). "
            "Kritik dini metinlerde çeviriyi mutlaka kontrol edin."
        )

        with gr.Tab("Metin → çeviri → ses"):
            t_in = gr.Textbox(label="Metin", lines=8)
            src_dd = gr.Dropdown(LANG_CHOICES, value="Türkçe", label="Kaynak dil")
            tgt_dd = gr.Dropdown(LANG_CHOICES, value="İngilizce", label="Hedef dil")
            ref = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Referans ses (XTTS — Farsça hariç)")
            btn = gr.Button("Oluştur", variant="primary")
            out_a = gr.Audio(label="Çıktı ses", type="filepath")
            out_n = gr.Textbox(label="Durum / çeviri metni", lines=12)
            btn.click(ui_text_to_speech, [t_in, src_dd, tgt_dd, ref], [out_a, out_n])

        with gr.Tab("Ses → çeviri → ses"):
            aud = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Konuşma / ses dosyası")
            wh = gr.Dropdown([x[0] for x in WHISPER_HINT], value="Otomatik", label="Whisper dil ipucu")
            man = gr.Dropdown(
                ["Otomatik (Whisper)"] + LANG_CHOICES,
                value="Otomatik (Whisper)",
                label="Kaynak dil (Whisper yanılırsa elle seçin)",
            )
            tgt2 = gr.Dropdown(LANG_CHOICES, value="Türkçe", label="Çeviri hedef dili")
            ref2 = gr.Audio(sources=["upload"], type="filepath", label="Referans ses (XTTS)")
            btn2 = gr.Button("Çalıştır", variant="primary")
            out_a2 = gr.Audio(label="Çevrilmiş ses", type="filepath")
            out_n2 = gr.Textbox(label="Transkript ve çeviri", lines=14)
            btn2.click(ui_speech_pipeline, [aud, wh, man, tgt2, ref2], [out_a2, out_n2])

    return demo


if __name__ == "__main__":
    build_demo().launch(server_name="0.0.0.0", server_port=7860, share=False)
