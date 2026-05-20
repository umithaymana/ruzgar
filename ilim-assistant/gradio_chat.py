"""
İlim Assistant — RAG + güçlü web + kod modu + sohbeti bilgiye kaydet.

1) pip install -r requirements.txt
2) ollama pull llama3.1:8b   (varsayılan güçlü; çok düşük RAM: llama3.2:3b + OLLAMA_CHAT_MODEL)
   Kod modu için isteğe bağlı: ollama pull qwen2.5-coder:7b → OLLAMA_CHAT_MODEL_CODING
3) python -m ilim_assistant.ingest_cli
4) python gradio_chat.py

Masaüstü (Cursor benzeri kabuk): üst klasörde `ruzgar-desktop` — önce `python desktop_server.py`, sonra `npm start`.

Ortam:
  OLLAMA_CHAT_MODEL — genel sohbet (kodda varsayılan: llama3.1:8b)
  OLLAMA_CHAT_MODEL_CODING — kod modunda öncelik (yoksa OLLAMA_CHAT_MODEL)
  ENABLE_WEB_SEARCH — 1 (varsayılan) / 0 web'i tamamen kapat
  CHAT_MAX_TOKENS — üst sınır (varsayılan 720; düşürürsen daha hızlı biter)
  CHAT_TEMPERATURE — varsayılan 0.42 (mantık/hitap dengesi)
  CHAT_TOP_P — varsayılan 0.92; '' veya none ile devre dışı
  ANTI_REPEAT_INSTRUCTION — 1 (varsayılan) önceki cevabı tekrarlamaya karşı ek talimat; 0 kapatır
  RUZGAR_DEFAULT_FETCH_PAGES — masaüstü API’de sayfa çekimi varsayılanı (varsayılan 0)
  RAG_TOP_K — yerel bağlam parça sayısı (varsayılan 2; artırırsan daha bağlam, biraz daha yavaş)
  RAG_INDEX_CACHE — 1 (varsayılan) yerel indeksi RAM’de tutar; 0 her aramada diskten okur
  Yerel araçlar (5): ENABLE_LOCAL_TOOLS — 1 varsayılan (0=kapat); LOCAL_TOOLS_ROOT — Gradio’da @@dosya için proje kökü
  LOCAL_TOOLS_TZ — varsayılan Europe/Istanbul; LOCAL_TOOLS_FILE_MAX_CHARS — tek dosya üst sınırı (karakter)
  Web: ENABLE_WEB_LINK_READ — mesajdaki https URL’lerini oku (1); ENABLE_WEB_SEARCH — DuckDuckGo araması (1)
  WEB_ANSWER_FROM_SOURCES — web bağlamından kullanıcıya özet talimatı (1); RUZGAR_DEFAULT_FETCH_PAGES — masaüstü varsayılan sayfa okuma (1)
  WEB_QUERY_MAX_CHARS — DDG arama sorgusu üst sınırı (varsayılan 240); RUZGAR_WEATHER_WEB_SUPPLEMENT — hava sorusunda canlı API varken DuckDuckGo’yu da çek (1; varsayılan 0 = hız için atla)
  RUZGAR_WEATHER_BEFORE_JSON — anlık hava cevabını genel hafıza JSON taramasından önce ver (0 = eski sıra; varsayılan 1)
"""

from __future__ import annotations

import os

try:
    from ilim_assistant.env_bootstrap import ensure_ruzgar_env

    ensure_ruzgar_env()
except Exception:
    pass

import gradio as gr

from ilim_assistant.approved_executor import (
    PRESETS,
    preset_labels,
    run_custom_winget,
    run_preset,
)
from ilim_assistant.chat_core import respond
from ilim_assistant.memory import save_exchange
from ilim_assistant.safety_policy import DISCLAIMER_TR

try:
    from ilim_assistant.ruzgar_hafiza_koprusu import ensure_hafiza_bridge_ready

    ensure_hafiza_bridge_ready()
except Exception:
    pass


def ops_preview(preset_key: str) -> str:
    if not preset_key:
        return DISCLAIMER_TR
    p = PRESETS.get(preset_key)
    if not p:
        return DISCLAIMER_TR
    cmd = " ".join(p.argv)
    return f"{DISCLAIMER_TR}\n\n{p.label}\n{p.description}\n\nÇalıştırılacak komut:\n{cmd}"


def ops_run(preset_key: str, approved: bool) -> str:
    if not approved:
        return "İşlem yapılmadı: aşağıdaki **Onaylıyorum** kutusunu işaretle."
    if not preset_key:
        return "Önce bir işlem seç."
    _, out = run_preset(preset_key)
    return out


def ops_run_custom(custom_line: str, approved: bool) -> str:
    if not approved:
        return "Onay kutusu işaretli değil."
    _, out = run_custom_winget(custom_line or "")
    return out


def save_last_turn(last_user: str, last_reply: str, title_hint: str):
    if not last_user or not last_reply:
        return "Kaydedilecek son tur yok."
    try:
        _, msg = save_exchange(last_user, last_reply, title_hint or None, rebuild_index=True)
        return msg
    except Exception as e:
        return f"Kayıt hatası: {e}"


def build_ui():
    header = (
        "## RÜZGAR — İlim asistanı\n"
        "Mesajında **Rüzgar** dendiğinde ilk yanıtında: *Efendim Ümit abi, sana nasıl yardımcı olabilirim?* "
        "(Ardından soruna cevap verir.)\n\n"
        "**Karşılama:** Bu sohbette **ilk kez** adıyla seslenince sabit cümle gelir; sonra doğrudan cevap. "
        "**Web:** DuckDuckGo (varsayılan **açık**; daha çok sonuç için ayarlardan sonuç sayısı; URL çekimi geciktirir — hız için 0 tut). "
        "**Akış:** Sohbet sekmesinde *Akışlı yanıt* açıkken cevap token token görünür (kapatırsan tek parça gelir). "
        "**Öğrenme:** Son turu `knowledge/learned/` içine kaydederek güçlendirirsin.\n\n"
        "**Kod:** Güçlü yerel kod modeli veya API önerilir. "
        "**PC işlemleri:** Aşağıda **Onaylı işlemler** sekmesinden — önizleme ve senin onayın olmadan hiçbir komut çalışmaz; "
        "Rüzgar sohbetten tek başına bilgisayarı yönetemez."
    )

    pl = preset_labels()
    first_preset = pl[0][1] if pl else None

    with gr.Blocks(title="RÜZGAR — İlim Asistanı") as demo:
        gr.Markdown(header)
        with gr.Tabs():
            with gr.Tab("Sohbet"):
                chatbot = gr.Chatbot(height=460, label="Sohbet")
                msg = gr.Textbox(
                    label="Mesajınız",
                    lines=3,
                    placeholder="Örn: Rüzgar, bugünün haberlerini özetle… / Rüzgar, FastAPI JWT örneği yaz…",
                )
                with gr.Row():
                    use_web = gr.Checkbox(label="Web araması + özet", value=True)
                    read_message_links = gr.Checkbox(
                        label="Mesajdaki bağlantıları oku (web kapalı olsa bile)",
                        value=True,
                    )
                    coding_mode = gr.Checkbox(
                        label="Kod / yazılım modu (sistem istemi + kod modeli)", value=False
                    )
                    stream_reply = gr.Checkbox(
                        label="Akışlı yanıt (cevap yazılırken göster)",
                        value=True,
                    )
                fetch_pages = gr.Slider(
                    0,
                    5,
                    value=0,
                    step=1,
                    label="Kaç farklı URL’den sayfa metni çekilsin (0 = sadece arama listesi; web açıkken hız için 0 önerilir)",
                )
                with gr.Row():
                    send = gr.Button("Gönder", variant="primary")
                    clear = gr.Button("Sohbeti temizle")

                gr.Markdown("### Son turu bilgi tabanına kaydet (öğren)")
                title_hint = gr.Textbox(label="Kısa başlık (isteğe bağlı)", lines=1)
                save_btn = gr.Button("Son cevabı öğrenilenlere kaydet + indeksi güncelle")
                save_status = gr.Textbox(label="Kayıt durumu", interactive=False, lines=2)

                last_user = gr.State("")
                last_reply = gr.State("")
                session_wake_used = gr.State(False)

                send.click(
                    respond,
                    [
                        msg,
                        chatbot,
                        use_web,
                        fetch_pages,
                        coding_mode,
                        stream_reply,
                        session_wake_used,
                        read_message_links,
                    ],
                    [chatbot, msg, last_user, last_reply, save_status, session_wake_used],
                )
                msg.submit(
                    respond,
                    [
                        msg,
                        chatbot,
                        use_web,
                        fetch_pages,
                        coding_mode,
                        stream_reply,
                        session_wake_used,
                        read_message_links,
                    ],
                    [chatbot, msg, last_user, last_reply, save_status, session_wake_used],
                )
                clear.click(
                    lambda: ([], "", "", "", "Temizlendi.", False),
                    None,
                    [chatbot, msg, last_user, last_reply, save_status, session_wake_used],
                )

                save_btn.click(save_last_turn, [last_user, last_reply, title_hint], [save_status])

            with gr.Tab("Onaylı işlemler (PC)"):
                gr.Markdown(
                    "### Güvenli, elle onaylı komutlar\n"
                    "- Burada gösterilenler dışında **otomatik çalıştırma yok**.\n"
                    "- **Sistem32 vb. dosya yazma / silme** bu arayüzde yok; şüpheli dosya için Windows "
                    "**Güvenlik** uygulamasını kullan; silme kararı sende.\n"
                    "- Defender taraması **algılar ve raporlar**; otomatik silme yapmaz.\n"
                    f"- {DISCLAIMER_TR}"
                )
                op_dd = gr.Dropdown(
                    choices=pl,
                    value=first_preset,
                    label="Ön tanımlı işlem",
                    interactive=True,
                )
                op_preview = gr.Textbox(label="Önizleme", lines=12, interactive=False)
                op_ok = gr.Checkbox(
                    label="Bu komutu çalıştırmayı onaylıyorum (önizlemeyi okudum)",
                    value=False,
                )
                op_run_btn = gr.Button("Onayla ve çalıştır", variant="primary")
                op_out = gr.Textbox(label="Çıktı", lines=16, interactive=False)

                gr.Markdown("#### İsteğe bağlı: yalnızca Python winget satırı")
                custom_winget = gr.Textbox(
                    lines=2,
                    label="İzinli biçim",
                    placeholder="winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements",
                )
                op_ok2 = gr.Checkbox(label="Özel winget satırını onaylıyorum", value=False)
                op_run_custom = gr.Button("Özel winget satırını çalıştır")

                op_dd.change(ops_preview, [op_dd], [op_preview])
                demo.load(ops_preview, [op_dd], [op_preview])
                op_run_btn.click(ops_run, [op_dd, op_ok], [op_out])
                op_run_custom.click(ops_run_custom, [custom_winget, op_ok2], [op_out])

    return demo


if __name__ == "__main__":
    try:
        from ilim_assistant.rag_store import warmup_index

        warmup_index()
    except Exception:
        pass
    if os.environ.get("RUZGAR_PRINT_READY_SEAL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        print(
            "Rüzgar Kullanıma Hazır, Sistemi Yeniden Başlatabilirsiniz.",
            flush=True,
        )
    build_ui().launch(server_name="0.0.0.0", server_port=7861)
