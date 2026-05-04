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
from typing import Annotated, Any

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from ilim_assistant.chat_core import (
    message_calls_wake_name,
    normalize_mode,
    prior_messages_for_turn,
    prepare_turn,
    rag_footer,
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


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    mode_norm = normalize_mode(req.mode or "genel")
    coding = req.coding_mode or mode_norm == "programlama"

    def generate():
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
            yield _sse({"type": "error", "text": "Boş mesaj"})
            return

        msg, hits, user_payload, system, model = prep
        new_wake = req.session_wake_used or message_calls_wake_name(msg)
        prior = prior_messages_for_turn(req.history, mode_norm)

        reply_body = ""
        try:
            for piece in chat_completion_stream(
                system, user_payload, model=model, prior_messages=prior
            ):
                reply_body += piece
                yield _sse({"type": "token", "text": piece})
            footer = rag_footer(hits)
            body_fixed = finalize_assistant_reply(reply_body)
            full_out = body_fixed + footer
            yield _sse(
                {
                    "type": "done",
                    "full_reply": full_out,
                    "user_message": msg,
                    "new_wake_used": new_wake,
                }
            )
        except Exception as e:
            yield _sse({"type": "error", "text": str(e)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
