"""
RÜZGAR masaüstü kabuğu için yerel HTTP API (Electron).

Çalıştırma (ilim-assistant klasöründe):
  python desktop_server.py

Varsayılan: http://127.0.0.1:8777
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Annotated, Any, Iterator

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from pydantic import BaseModel, Field
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from ilim_assistant.chat_core import (
    message_calls_wake_name,
    normalize_mode,
    prior_messages_for_turn,
    prepare_turn,
    rag_footer,
)
from ilim_assistant.hafiza_i_ruzgar import (
    genel_hafiza_lookup,
    get_hafiza_motor as _get_hafiza_motor,
)
from ilim_assistant.text_encoding import finalize_assistant_reply
from ilim_assistant.llm_ollama import chat_completion_stream
from ilim_assistant.stt_whisper import stt_runtime_available, transcribe_file

app = FastAPI(title="RÜZGAR Desktop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _warmup_rag() -> None:
    """İlk sohbet turunda RAG disk okumasını ve gömme modelini önceden yükle."""
    try:
        from ilim_assistant.rag_store import warmup_index

        warmup_index()
    except Exception:
        pass
    try:
        _get_hafiza_motor()
    except Exception:
        pass


def _default_fetch_pages() -> float:
    try:
        return float(os.environ.get("RUZGAR_DEFAULT_FETCH_PAGES", "1"))
    except ValueError:
        return 1.0


class ChatRequest(BaseModel):
    message: str = ""
    history: list[dict[str, Any]] = Field(default_factory=list)
    use_web: bool = True
    fetch_pages: float = Field(default_factory=_default_fetch_pages)
    coding_mode: bool = False
    session_wake_used: bool = False
    # genel | ses | okuma | video | uretim | programlama | gelisim | duzen | dosya | hizli
    mode: str = "genel"
    # Electron getRoot() — @@dosya yolları bu köke göre çözülür
    workspace_root: str | None = None
    # Web ara kapalı olsa bile mesajdaki https URL’lerini oku
    read_message_links: bool = True


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


class HafizaArsivAdd(BaseModel):
    raw: str = ""


class HafizaMotorRead(BaseModel):
    raw: str = ""


class HafizaImportBlok(BaseModel):
    raw: str = ""


class GenelHafizaBakBody(BaseModel):
    message: str = ""


@app.post("/api/hafiza/genel-bak")
def api_genel_hafiza_bak(body: GenelHafizaBakBody):
    """Ana sohbet ön kontrol: genel hafızada tam/benzer cevap (UI düşünme balonu atlatma)."""
    m = (body.message or "").strip()
    if not m:
        return {"ok": True, "hit": False, "answer": None}
    ans = genel_hafiza_lookup(m)
    if ans is None:
        return {"ok": True, "hit": False, "answer": None}
    out = finalize_assistant_reply(ans)
    return {"ok": True, "hit": True, "answer": out}


@app.get("/api/hafiza/arsiv")
def api_hafiza_arsiv():
    """Öğrenme sözlüğü — arayüz sadece `data` ile motor cevabı eşlemesi yapar (analiz listesi ayrı)."""
    m = _get_hafiza_motor()
    return {"ok": True, "data": m.tum_bilgiler(motor_tipi="Hafıza"), "items": []}


@app.post("/api/hafiza/arsiv/add")
def api_hafiza_arsiv_add(body: HafizaArsivAdd):
    """Satırları `soru = cevap` formatında ayrıştırır ve kalıcı hafızaya yazar."""
    m = _get_hafiza_motor()
    raw = (body.raw or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Boş kayıt")
    added = 0
    for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        txt = line.strip()
        if not txt or txt.startswith("#"):
            continue
        if "=" not in txt:
            continue
        soru, _, cevap = txt.partition("=")
        soru = soru.strip()
        cevap = cevap.strip()
        if soru and cevap:
            m.ekle_bilgi(soru, cevap, motor_tipi="Hafıza")
            added += 1

    if added == 0:
        raise HTTPException(status_code=400, detail="Geçerli 'Soru = Cevap' satırı yok")

    return {"ok": True, "added": added}


@app.post("/api/hafiza/motor-read")
def api_hafiza_motor_read(body: HafizaMotorRead):
    m = _get_hafiza_motor()
    ans = m.cevap_ver(body.raw or "")
    return {"ok": True, "answer": ans}


@app.post("/api/hafiza/import-blok")
def api_hafiza_import_blok(body: HafizaImportBlok):
    """Çok satırlı metinde yalnızca `soru = cevap` satırlarını öğrenir."""
    m = _get_hafiza_motor()
    items = m.import_metin_blok(body.raw or "", motor_tipi="Hafıza")
    return {"ok": True, "added": len(items), "items": items}


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "ruzgar-desktop-api",
        "stt": stt_runtime_available(),
    }


def _normalize_stt_lang(lang: str | None) -> str | None:
    if not lang:
        return None
    s = lang.strip().lower()
    if s in ("auto", "detect", "none"):
        return None
    return lang.strip()[:16]


@app.post("/api/stt")
async def api_stt(
    file: UploadFile = File(...),
    lang: Annotated[str | None, Query()] = "tr",
):
    """Tarayıcıdan gelen ses dosyasını yerel Whisper ile metne çevirir (internet şart değil)."""
    if not stt_runtime_available():
        raise HTTPException(
            status_code=503,
            detail="Yerel STT kullanılamıyor: pip install faster-whisper veya RUZGAR_STT=0 kaldırın.",
        )
    raw = await file.read()
    if not raw or len(raw) < 64:
        raise HTTPException(status_code=400, detail="Ses verisi çok kısa veya boş.")

    sfx = ".webm"
    fn = (file.filename or "").lower()
    if fn.endswith(".wav"):
        sfx = ".wav"
    elif fn.endswith(".ogg"):
        sfx = ".ogg"
    elif fn.endswith(".mp4") or fn.endswith(".m4a"):
        sfx = ".m4a"

    wl = _normalize_stt_lang(lang)

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=sfx)
        os.write(fd, raw)
        os.close(fd)

        def _run():
            return transcribe_file(tmp_path, language=wl)

        text, detected = await run_in_threadpool(_run)
        return {"text": text, "language": detected}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        if tmp_path and os.path.isfile(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def iter_chat_turn_events(req: ChatRequest) -> Iterator[dict]:
    """Gradio / SSE / WS; önce `prepare_turn` → merkezi `ruzgar_genel_hafiza.json` eşlemesi."""
    mode_norm = normalize_mode(req.mode or "genel")
    coding = req.coding_mode or mode_norm == "programlama"
    prep = prepare_turn(
        req.message,
        req.history,
        req.use_web,
        req.fetch_pages,
        coding,
        req.session_wake_used,
        mode=mode_norm,
        workspace_root=req.workspace_root,
        read_message_links=req.read_message_links,
    )
    if prep is None:
        yield {"type": "error", "text": "Boş mesaj"}
        return

    msg, hits, user_payload, system, model, og_direct = prep
    new_wake = req.session_wake_used or message_calls_wake_name(msg)

    if og_direct is not None:
        full_out = finalize_assistant_reply(og_direct)
        yield {"type": "meta", "instant_memory": True}
        yield {"type": "token", "text": full_out}
        yield {
            "type": "done",
            "full_reply": full_out,
            "user_message": msg,
            "new_wake_used": new_wake,
        }
        return

    prior = prior_messages_for_turn(req.history, mode_norm)
    reply_body = ""
    try:
        for piece in chat_completion_stream(
            system, user_payload, model=model, prior_messages=prior
        ):
            reply_body += piece
            yield {"type": "token", "text": piece}
        footer = rag_footer(hits)
        body_fixed = finalize_assistant_reply(reply_body)
        full_out = body_fixed + footer
        yield {
            "type": "done",
            "full_reply": full_out,
            "user_message": msg,
            "new_wake_used": new_wake,
        }
    except Exception as e:
        yield {"type": "error", "text": str(e)}


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    def generate():
        yield ":ruzgar-events\n\n"
        for obj in iter_chat_turn_events(req):
            yield _sse(obj)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket) -> None:
    """Electron Işık Hızı: SSE ile aynı `iter_chat_turn_events` (önce öğrenme merkezi)."""
    await ws.accept()
    try:
        payload = await ws.receive_json()
    except Exception:
        try:
            await ws.send_json({"type": "error", "text": "Geçersiz veya boş istek"})
        except Exception:
            pass
        await ws.close()
        return
    try:
        req = ChatRequest(**payload)
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "text": f"İstek şeması: {e}"})
        except Exception:
            pass
        await ws.close()
        return
    try:
        async for obj in iterate_in_threadpool(iter_chat_turn_events(req)):
            await ws.send_json(obj)
    except Exception:
        pass
    try:
        await ws.close()
    except Exception:
        pass


if __name__ == "__main__":
    # Railway / Render vb.: PORT atanır (varsayılan 8777 yerine).
    _port_raw = os.environ.get("PORT", os.environ.get("RUZGAR_API_PORT", "8777"))
    port = int(_port_raw)
    _default_host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    host = os.environ.get("RUZGAR_API_HOST", _default_host)
    # Varsayılan: daha az log I/O (yüksek trafikli token akışı için)
    log_level = os.environ.get("RUZGAR_UVICORN_LOG", "warning")
    access_log = os.environ.get("RUZGAR_ACCESS_LOG", "0").strip() in ("1", "true", "yes")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        access_log=access_log,
    )
