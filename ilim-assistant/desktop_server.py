"""
RÜZGAR masaüstü kabuğu için yerel HTTP API (Electron).

Çalıştırma (ilim-assistant klasöründe):
  python desktop_server.py

Varsayılan: http://127.0.0.1:8777
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
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

# Proje kökü (YAPAY ZEKA): ilim-assistant/desktop_server.py → iki üst dizin
REPO_ROOT = Path(__file__).resolve().parent.parent
_SKIP_LIST_NAMES = frozenset({"node_modules", "__pycache__", ".venv", "venv", ".git"})


def _repo_resolve_under_root(rel_query: str, must_be_dir: bool = False) -> Path:
    raw = (rel_query or "").strip().replace("\\", "/").lstrip("/")
    root = REPO_ROOT.resolve()
    target = (root / raw.replace("/", os.sep)).resolve() if raw else root
    try:
        target.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz yol (proje dışı).")
    if must_be_dir:
        if not target.is_dir():
            raise HTTPException(status_code=404, detail="Klasör yok.")
    else:
        if not target.is_file():
            raise HTTPException(status_code=404, detail="Dosya yok.")
    return target


def _repo_list_children(rel_query: str) -> list[dict[str, Any]]:
    raw = (rel_query or "").strip().replace("\\", "/").lstrip("/")
    target = _repo_resolve_under_root(rel_query, must_be_dir=True)
    out: list[dict[str, Any]] = []
    for p in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        name = p.name
        if name in _SKIP_LIST_NAMES:
            continue
        if name.startswith(".") and name != ".vscode":
            continue
        rel_full = f"{raw}/{name}" if raw else name
        rel_full = rel_full.replace("\\", "/")
        out.append({"name": name, "isDir": p.is_dir(), "rel": rel_full})
    return out

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


class CodeRunBody(BaseModel):
    code: str = ""
    language: str = "python"
    timeout_sec: float = 8.0
    workspace_root: str | None = Field(
        default=None,
        description="Electron proje kökü (örn. YAPAY ZEKA); sunucuda doğrulanır.",
    )
    cwd_rel: str | None = Field(
        default=None,
        description="Çalışma dizini köke göre (örn. ruzgar-desktop); kayıtlı dosyanın klasörü.",
    )


def _normalize_workspace_root(raw: str | None) -> str | None:
    wr = (raw or "").strip()
    if not wr:
        return None
    n = os.path.normpath(wr)
    return n if os.path.isdir(n) else None


def _is_inside_workspace(workspace_root: str, candidate: str) -> bool:
    wr = os.path.normpath(workspace_root)
    ca = os.path.normpath(candidate)
    try:
        return os.path.commonpath([wr, ca]) == wr
    except ValueError:
        return False


def _resolve_workspace_run_dir(workspace_root: str, cwd_rel: str | None) -> str | None:
    """Güvenli çalışma dizini: kök veya kök altı klasör (dosya yolu verilirse üst klasör)."""
    wr = _normalize_workspace_root(workspace_root)
    if not wr:
        return None
    rel = (cwd_rel or "").strip().replace("\\", "/").lstrip("/")
    if not rel:
        return wr
    cand = os.path.normpath(os.path.join(wr, rel.replace("/", os.sep)))
    if not _is_inside_workspace(wr, cand):
        return None
    if os.path.isfile(cand):
        cand = os.path.dirname(cand)
    return cand if os.path.isdir(cand) else None


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


@app.get("/api/workspace/list")
def api_workspace_list(rel: str = Query("")) -> dict[str, Any]:
    """Proje köküne göre klasör içeriği (Okuma / Programlama ağaçları; Electron olmadan da çalışır)."""
    items = _repo_list_children(rel)
    return {"ok": True, "items": items}


@app.get("/api/workspace/read-text")
def api_workspace_read_text(rel: str = Query("")) -> dict[str, Any]:
    """UTF-8 metin dosyası okuma (PDF vb. ikilik içerik kullanıcıya ham görünebilir)."""
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        raise HTTPException(status_code=400, detail="rel gerekli.")
    target = _repo_resolve_under_root(raw, must_be_dir=False)
    if target.stat().st_size > 2_000_000:
        raise HTTPException(status_code=400, detail="Dosya çok büyük (2 MB).")
    text = target.read_text(encoding="utf-8", errors="replace")
    return {"ok": True, "text": text}


@app.post("/api/code/run")
async def api_code_run(body: CodeRunBody):
    """Programlama Atölyesi: Python/JavaScript kodunu kontrollü çalıştırır.

    Kod geçici dosyaya yazılır; workspace_root + cwd_rel ile çalışma dizini proje içine alınır.
    """
    code = (body.code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Çalıştırılacak kod boş.")
    if len(code) > 80_000:
        raise HTTPException(status_code=400, detail="Kod çok büyük (80 KB sınırı).")

    lang = (body.language or "python").strip().lower()
    timeout = max(1.0, min(float(body.timeout_sec or 8.0), 20.0))
    if lang in ("py", "python", "python3"):
        filename = "main.py"
        runner = sys.executable
    elif lang in ("js", "javascript", "node"):
        filename = "main.js"
        runner = "node"
    else:
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"{lang} dili bu çalıştırma sürümünde desteklenmiyor. İlk sürüm: Python + JavaScript.",
            "exit_code": None,
            "timeout": False,
        }

    wr_norm = _normalize_workspace_root(body.workspace_root)
    run_dir = None
    cwd_used_rel = None
    if wr_norm:
        run_dir = _resolve_workspace_run_dir(body.workspace_root or "", body.cwd_rel)
        if run_dir:
            try:
                cwd_used_rel = os.path.relpath(run_dir, wr_norm).replace("\\", "/")
            except ValueError:
                cwd_used_rel = ""

    def _run() -> dict[str, Any]:
        work_td = tempfile.mkdtemp(prefix="ruzgar_code_")
        src = os.path.join(work_td, filename)
        try:
            with open(src, "w", encoding="utf-8", newline="\n") as f:
                f.write(code)
            abs_src = os.path.abspath(src)
            proc_cwd = run_dir if run_dir else work_td
            cmd = [runner, abs_src]
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=proc_cwd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    shell=False,
                )
                out: dict[str, Any] = {
                    "ok": proc.returncode == 0,
                    "stdout": (proc.stdout or "")[:20_000],
                    "stderr": (proc.stderr or "")[:20_000],
                    "exit_code": proc.returncode,
                    "timeout": False,
                }
                if cwd_used_rel is not None:
                    out["cwd_used_rel"] = cwd_used_rel
                return out
            except subprocess.TimeoutExpired as e:
                out = {
                    "ok": False,
                    "stdout": (e.stdout or "")[:20_000] if isinstance(e.stdout, str) else "",
                    "stderr": f"Zaman aşımı: {timeout:.1f} saniye içinde bitmedi.",
                    "exit_code": None,
                    "timeout": True,
                }
                if cwd_used_rel is not None:
                    out["cwd_used_rel"] = cwd_used_rel
                return out
            except FileNotFoundError as e:
                out = {
                    "ok": False,
                    "stdout": "",
                    "stderr": f"Çalıştırıcı bulunamadı: {runner} ({e})",
                    "exit_code": None,
                    "timeout": False,
                }
                if cwd_used_rel is not None:
                    out["cwd_used_rel"] = cwd_used_rel
                return out
        finally:
            shutil.rmtree(work_td, ignore_errors=True)

    return await run_in_threadpool(_run)


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
