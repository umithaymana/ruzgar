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
import uuid
from pathlib import Path
from typing import Annotated, Any, Iterator

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, WebSocket
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
from ilim_assistant.stream_orchestra import prefetch_main_engine_bundle_for_stream
from ilim_assistant.hafiza_i_ruzgar import (
    genel_hafiza_lookup,
    get_hafiza_motor as _get_hafiza_motor,
)
from ilim_assistant.text_encoding import finalize_assistant_reply
from ilim_assistant.llm_brain import select_brain_chain, stream_chat_with_brain
from ilim_assistant.llm_ollama import format_llm_user_error
from ilim_assistant.motorlar.programlama_motoru import (
    apply_assistant_reply_tools,
    code_debug_max_retries,
    wants_autonomous_code_debug,
)
from ilim_assistant.stt_whisper import stt_runtime_available, transcribe_file
from ilim_assistant.video_ffmpeg import (
    MAX_SEGMENT_SECONDS,
    burn_subtitles_into_mp4,
    concat_two_files,
    export_directory,
    ffmpeg_available,
    ffprobe_available,
    ffprobe_json,
    mux_replace_audio,
    summarize_probe,
    transcode_to_mp4,
    trim_media,
)

app = FastAPI(title="RÜZGAR Desktop API")

# Video probe: tarayıcıdan gelen dosya üst sınırı (metadata okuma; yine de güvenlik)
MAX_VIDEO_PROBE_BYTES = 600 * 1024 * 1024

# Proje kökü (YAPAY ZEKA): ilim-assistant/desktop_server.py → iki üst dizin
_ILIM_ASSISTANT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = _ILIM_ASSISTANT_ROOT.parent
_SKIP_LIST_NAMES = frozenset({"node_modules", "__pycache__", ".venv", "venv", ".git"})


def _load_env_file() -> None:
    """``ilim-assistant/.env`` — GOOGLE_GEMINI_API_KEY vb. (mevcut ortamı ezmez)."""
    path = _ILIM_ASSISTANT_ROOT / ".env"
    if not path.is_file():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except OSError:
        pass


_load_env_file()


def pdf_text_runtime_available() -> bool:
    try:
        import pypdf  # noqa: F401

        return True
    except ImportError:
        return False


def docx_text_runtime_available() -> bool:
    try:
        import docx  # noqa: F401

        return True
    except ImportError:
        return False


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


def _parse_bool_form(val: str | None, default: bool = True) -> bool:
    if val is None or str(val).strip() == "":
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")


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


def _boot_motorlar_anaonce() -> None:
    """.cursorrules — Ana motor → çekirdek → 5 yardımcı (sıra kilitli)."""
    import importlib

    importlib.import_module("ilim_assistant.main_engine")
    importlib.import_module("ilim_assistant.motorlar.ruzgar_cekirdegi")
    for name in (
        "ilim_assistant.ses_motoru",
        "ilim_assistant.video_motoru",
        "ilim_assistant.okuma_motoru",
        "ilim_assistant.tercume_motoru",
        "ilim_assistant.programlama_motoru",
    ):
        importlib.import_module(name)


@app.on_event("startup")
async def _warmup_rag() -> None:
    """İlk sohbet turunda RAG disk okumasını ve gömme modelini önceden yükle."""
    try:
        _boot_motorlar_anaonce()
    except Exception:
        pass
    try:
        from ilim_assistant.rag_store import warmup_index

        warmup_index()
    except Exception:
        pass
    try:
        _get_hafiza_motor()
    except Exception:
        pass
    try:
        from ilim_assistant.dinamit_hatirlatici import start_reminder_background_thread
        from ilim_assistant.gorev_yoneticisi import init_tasks_db

        start_reminder_background_thread()
        init_tasks_db()
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
    # None/boş: eski istemciler veya hatalı JSON; Kod modu açıksa programlama varsayılır (prefetch atlanır).
    mode: str | None = None
    # Electron getRoot() — @@dosya yolları bu köke göre çözülür
    workspace_root: str | None = None
    # Web ara kapalı olsa bile mesajdaki https URL’lerini oku
    read_message_links: bool = True


def _effective_chat_mode_raw(req: ChatRequest) -> str:
    """Kod modu açıksa her zaman programlama (UI genel kalsa bile tam indeks prefetch kapalı)."""
    if req.coding_mode:
        return "programlama"
    raw = (req.mode or "").strip()
    return raw or "genel"


class ReminderAckBody(BaseModel):
    """Dinamit hatırlatıcı onayı (masaüstü uyumluluğu)."""

    id: str = ""


class TaskCreateBody(BaseModel):
    title: str = ""
    detail: str = ""


class TaskUpdateBody(BaseModel):
    id: int = 0
    status: str = "done"
    detail: str | None = None


class VideoDownloadBody(BaseModel):
    url: str = ""


class VideoConcatBody(BaseModel):
    """İki proje içi dosyayı concat ile birleştirir (codec uyumu şarta bağlı)."""

    rel_a: str = ""
    rel_b: str = ""
    copy_streams: bool = True


class VideoEditClipItem(BaseModel):
    rel: str = ""
    start_sec: float = 0.0
    end_sec: float | None = None
    label: str = ""


class VideoEditMixBody(BaseModel):
    """Timeline kurgusu: kesilmiş parçaları sırayla birleştirir (parça ≤ 5 dk)."""

    clips: list[VideoEditClipItem] = Field(default_factory=list)
    copy_streams: bool = True
    project_name: str = ""


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


class IdrakPretreatBody(BaseModel):
    message: str = ""
    history: list[dict[str, Any]] = Field(default_factory=list)


class HizirPazarTaraBody(BaseModel):
    query: str = Field(default="", description="Ürün veya arama (boşsa genel tarama metni)")
    channels: list[str] | None = Field(
        default=None,
        description="Pazar kanalları (trendyol, amazon_tr, hepsiburada, amazon_us, amazon_gb, amazon_de, ebay, aliexpress); boş veya atlanırsa tümü",
    )


class HizirFirsatKaldirBody(BaseModel):
    kart_id: str = Field(default="", description="ARBITRAJ kart_id (Ticaret Avcısı)")


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


@app.post("/api/idrak/pretreat")
def api_idrak_pretreat(body: IdrakPretreatBody):
    """Ses/STT ve sohbet kutusu için hızlı yazım + devam cümlesi ön-işlemi."""
    from ilim_assistant.idrak_on_islem import pretreat_user_turn

    pt = pretreat_user_turn(body.message, body.history)
    return {
        "ok": True,
        "text": pt.text,
        "changed": pt.changed,
        "continuation": pt.continuation,
        "replacements": list(pt.replacements),
    }


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


def _super_brain_health_block() -> dict[str, Any]:
    try:
        from ilim_assistant.llm_brain import brain_health_snapshot

        return brain_health_snapshot()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _sample_cpu_percent() -> float | None:
    """İsteğe bağlı `psutil` — yoksa null (istemci yine 200 alır)."""
    try:
        import psutil  # type: ignore[import-not-found]

        return float(psutil.cpu_percent(interval=0.05))
    except Exception:
        return None


def _sample_gpu_percent() -> float | None:
    """NVIDIA GPU kullanımı; yoksa null."""
    try:
        import shutil
        import subprocess

        exe = shutil.which("nvidia-smi")
        if not exe:
            return None
        r = subprocess.run(
            [
                exe,
                "--query-gpu=utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if r.returncode != 0:
            return None
        vals: list[float] = []
        for line in (r.stdout or "").splitlines():
            s = line.strip()
            if not s:
                continue
            try:
                vals.append(float(s))
            except ValueError:
                continue
        if not vals:
            return None
        return float(sum(vals) / len(vals))
    except Exception:
        return None


@app.get("/api/health")
def health():
    import os as _os

    _m = _os.environ.get("HIZIR_MOCK_MARKETPLACE", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    _ak = (_os.environ.get("HIZIR_AMAZON_ACCESS_KEY") or "").strip()
    _sk = (_os.environ.get("HIZIR_AMAZON_SECRET_KEY") or "").strip()
    _tg = (_os.environ.get("HIZIR_AMAZON_PARTNER_TAG") or "").strip()
    _eb = bool(
        (_os.environ.get("HIZIR_EBAY_CLIENT_ID") or "").strip()
        and (_os.environ.get("HIZIR_EBAY_CLIENT_SECRET") or "").strip()
    )
    _ae = bool(
        (_os.environ.get("HIZIR_ALIEXPRESS_APP_KEY") or "").strip()
        and (_os.environ.get("HIZIR_ALIEXPRESS_APP_SECRET") or "").strip()
        and (_os.environ.get("HIZIR_ALIEXPRESS_ACCESS_TOKEN") or "").strip()
    )
    from ilim_assistant.chat_core import _main_chat_genel_only, _web_secondary_policy_enabled
    from ilim_assistant.defaults import DEFAULT_OLLAMA_CHAT_MODEL

    _main_only = _main_chat_genel_only()
    return {
        "ok": True,
        "service": "ruzgar-desktop-api",
        "stt": stt_runtime_available(),
        "pdf_text": pdf_text_runtime_available(),
        "docx_text": docx_text_runtime_available(),
        "ffmpeg": ffmpeg_available(),
        "ffprobe": ffprobe_available(),
        "merkezi_bellek": True,
        "ana_motor": {
            "main_only_genel_hafiza": _main_only,
            "main_only_warning": (
                "Genel modda yalnızca hafıza JSON; LLM/RAG/web kapalı"
                if _main_only
                else None
            ),
            "web_secondary_strong_rag_only": _web_secondary_policy_enabled(),
            "question_plan_enabled": os.environ.get("RUZGAR_ANA_MOTOR_PLAN", "1").strip().lower()
            not in ("0", "false", "no"),
            "clarify_enabled": os.environ.get("RUZGAR_ANA_MOTOR_CLARIFY", "1").strip().lower()
            not in ("0", "false", "no"),
            "ollama_chat_model": os.environ.get("OLLAMA_CHAT_MODEL", DEFAULT_OLLAMA_CHAT_MODEL),
            "enable_web_search": os.environ.get("ENABLE_WEB_SEARCH", "1") == "1",
            "rag_top_k_default": os.environ.get("RAG_TOP_K", "2"),
            "rag_top_k_genel": os.environ.get("RUZGAR_GENEL_RAG_TOP_K", "4"),
            "archive_score_min": os.environ.get("RUZGAR_ARCHIVE_SCORE_MIN", "0.22"),
            "web_suppress_rag_min": os.environ.get("RUZGAR_WEB_SUPPRESS_RAG_MIN", "0.38"),
            "ana_motor_agent_enabled": os.environ.get("RUZGAR_ANA_MOTOR_AGENT", "1").strip().lower()
            not in ("0", "false", "no"),
        },
        "super_brain": _super_brain_health_block(),
        "hizir": {
            "mock_marketplace": _m,
            "amazon_paapi_credentials": bool(_ak and _sk and _tg),
            "ebay_browse_credentials": bool(_eb),
            "aliexpress_open_credentials": bool(_ae),
        },
    }


@app.get("/api/ui/manifest")
def api_ui_manifest():
    """Dashboard/atölye metinleri için tek kaynak; UI statik Faz 7'ye takılmaz."""
    from ilim_assistant.ruzgar_ui_manifest import build_ui_manifest

    return build_ui_manifest(health=health())


@app.get("/api/system-metrics")
def api_system_metrics():
    """Masaüstü performans pill — `ruzgar-desktop/app.js` her ~2.5 sn çağırır."""
    return {
        "cpu_percent": _sample_cpu_percent(),
        "gpu_percent": _sample_gpu_percent(),
    }


@app.get("/api/reminders/pending")
def api_reminders_pending():
    """Dinamit hatırlatıcılar — istemci 24 sn'de bir poll eder."""
    from ilim_assistant.dinamit_hatirlatici import fetch_due_reminders

    return {"ok": True, "items": fetch_due_reminders()}


@app.post("/api/reminders/ack")
def api_reminders_ack(body: ReminderAckBody):
    from ilim_assistant.dinamit_hatirlatici import mark_triggered

    raw = (body.id or "").strip()
    try:
        rid = int(raw)
    except ValueError:
        rid = 0
    if rid > 0:
        mark_triggered(rid)
    return {"ok": True, "id": raw}


@app.get("/api/self-test")
def api_self_test():
    """Rüzgar kendi sağlık ve mod davranışını hızlı kontrol eder."""
    from ilim_assistant.ruzgar_selftest import run_self_tests

    return run_self_tests()


@app.get("/api/tasks")
def api_tasks(limit: int = 50):
    from ilim_assistant.gorev_yoneticisi import list_tasks

    return {"ok": True, "items": list_tasks(limit)}


@app.post("/api/tasks")
def api_tasks_create(body: TaskCreateBody):
    from ilim_assistant.gorev_yoneticisi import create_task

    return {"ok": True, "task": create_task(body.title, body.detail)}


@app.post("/api/tasks/update")
def api_tasks_update(body: TaskUpdateBody):
    from ilim_assistant.gorev_yoneticisi import update_task

    ok = update_task(body.id, body.status, body.detail)
    return {"ok": ok, "id": body.id}


@app.get("/api/merkezi-bellek")
@app.get("/api/merkezi-bellek/")
def api_merkezi_bellek():
    """Merkezi Bellek v3 — Ticaret Avcısı senkronu + HIZIR ticaret + genel önbellek."""
    try:
        from ilim_assistant.hizir.bellek import load_merkezi_bellek, merkezi_bellek_path
        from ilim_assistant.hizir.ticaret_avci import reconcile_ticaret_avci_firsatlar

        data = reconcile_ticaret_avci_firsatlar()
        return {
            "ok": True,
            "path": str(merkezi_bellek_path()),
            "schema": data.get("schema"),
            "version": data.get("version"),
            "data": data,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/hizir/pazar-tara")
def api_hizir_pazar_tara(body: HizirPazarTaraBody):
    """Panelden canlı keşif: Tool-Bridge + UniversalScraper; sonuç `merkezi_bellek`e yazılır."""
    try:
        from ilim_assistant.hizir.tool_bridge import build_dynamic_operasyon_context

        q = (body.query or "").strip()
        msg = f"Pazar yerini tara: {q}" if q else "Pazar yerini tara"
        ctx = build_dynamic_operasyon_context(
            msg,
            weather_q=False,
            has_live_weather_block=False,
            mode_norm="genel",
            pazar_kanallari=body.channels,
        )
        from ilim_assistant.hizir.ticaret_avci import reconcile_ticaret_avci_firsatlar

        data = reconcile_ticaret_avci_firsatlar()
        return {
            "ok": True,
            "tool_context_chars": len(ctx),
            "data": data,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/hizir/temizle")
def api_hizir_temizle():
    """HIZIR vitrin: otomatik fırsatlar + pazar önbelleği + pas geç listesi temizlenir."""
    try:
        from ilim_assistant.hizir.bellek import clear_hizir_vitrin_state, merkezi_bellek_path

        data = clear_hizir_vitrin_state()
        return {"ok": True, "path": str(merkezi_bellek_path()), "data": data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/hizir/firsat-kaldir")
def api_hizir_firsat_kaldir(body: HizirFirsatKaldirBody):
    """PAS GEÇ: kartı pas_gecildi listesine alır ve listeyi yeniden üretir."""
    try:
        from ilim_assistant.hizir.bellek import merkezi_bellek_path, pas_gec_hizir_kart

        data = pas_gec_hizir_kart((body.kart_id or "").strip())
        return {"ok": True, "path": str(merkezi_bellek_path()), "data": data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/video/download")
async def api_video_download(body: VideoDownloadBody):
    """YouTube/web video URL'sini yt-dlp ile indirir ve merkezi havuza kaydeder."""
    url = (body.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL boş.")
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Yalnızca geçerli http/https URL kabul edilir.")

    def _run():
        from ilim_assistant.motorlar.video_motoru import download_video_with_yt_dlp

        result = download_video_with_yt_dlp(url)
        payload = result.to_metadata()
        if result.error:
            payload["error"] = result.error
        return payload

    try:
        data = await run_in_threadpool(_run)
        return {"ok": bool(data.get("ok")), "result": data}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/video/probe")
async def api_video_probe(file: UploadFile = File(...)):
    """Yüklenen video/ses dosyası için ffprobe ile süre, codec, çözünürlük özeti."""
    if not ffprobe_available():
        raise HTTPException(
            status_code=503,
            detail="ffprobe bulunamadı: FFmpeg kurun ve PATH'e ekleyin.",
        )
    raw = await file.read()
    ln = len(raw)
    if ln < 32:
        raise HTTPException(status_code=400, detail="Dosya çok kısa veya boş.")
    if ln > MAX_VIDEO_PROBE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Dosya çok büyük (>{MAX_VIDEO_PROBE_BYTES // (1024 * 1024)} MB).",
        )

    fn = (file.filename or "").lower()
    sfx = ".bin"
    for ext in (
        ".mkv",
        ".webm",
        ".mov",
        ".avi",
        ".mp4",
        ".m4v",
        ".wav",
        ".mp3",
        ".flac",
        ".ogg",
        ".opus",
    ):
        if fn.endswith(ext):
            sfx = ext
            break

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=sfx)
        os.write(fd, raw)
        os.close(fd)

        def _run():
            data = ffprobe_json(tmp_path)
            return summarize_probe(data)

        summary = await run_in_threadpool(_run)
        return {"ok": True, "summary": summary}
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


@app.post("/api/video/trim")
async def api_video_trim(
    start_sec: Annotated[float, Form()] = 0.0,
    duration_sec: Annotated[float | None, Form()] = None,
    end_sec: Annotated[float | None, Form()] = None,
    copy_streams: Annotated[str, Form()] = "true",
    rel: Annotated[str | None, Form()] = None,
    file: UploadFile | None = File(None),
):
    """Zaman aralığı keser; çıktı `.ruzgar-video-export/` altına yazılır."""
    if not ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail="ffmpeg bulunamadı: FFmpeg kurun ve PATH'e ekleyin.",
        )
    rel_s = (rel or "").strip()
    if rel_s and file is not None:
        raise HTTPException(status_code=400, detail="rel ve file aynı istekte kullanılamaz.")
    if not rel_s and file is None:
        raise HTTPException(status_code=400, detail="rel veya file gerekli.")

    copy_flag = _parse_bool_form(copy_streams, True)
    sp = max(0.0, float(start_sec))
    dur: float | None = None
    if duration_sec is not None and float(duration_sec) > 0:
        dur = float(duration_sec)
    elif end_sec is not None:
        dur = float(end_sec) - sp
    else:
        raise HTTPException(status_code=400, detail="duration_sec veya end_sec gerekli.")
    if dur is None or dur <= 0:
        raise HTTPException(status_code=400, detail="Geçersiz süre (duration veya end).")
    if dur > MAX_SEGMENT_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"Kesim süresi en fazla {MAX_SEGMENT_SECONDS // 3600} saat olabilir.",
        )

    tmp_input: str | None = None
    try:
        if rel_s:
            input_path = _repo_resolve_under_root(rel_s)
        else:
            raw = await file.read()
            if len(raw) < 32:
                raise HTTPException(status_code=400, detail="Dosya çok kısa veya boş.")
            if len(raw) > MAX_VIDEO_PROBE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dosya çok büyük (>{MAX_VIDEO_PROBE_BYTES // (1024 * 1024)} MB); proje içi rel kullanın.",
                )
            sfx = ".bin"
            low = ((file.filename if file else "") or "").lower()
            for ext in (
                ".mkv",
                ".webm",
                ".mov",
                ".avi",
                ".mp4",
                ".m4v",
                ".wav",
                ".mp3",
            ):
                if low.endswith(ext):
                    sfx = ext
                    break
            fd, tmp_input = tempfile.mkstemp(suffix=sfx)
            os.write(fd, raw)
            os.close(fd)
            input_path = Path(tmp_input)

        out_dir = export_directory(REPO_ROOT)
        stem = input_path.stem or "media"
        suf = ".mp4" if not copy_flag else (input_path.suffix or ".mp4")
        out_name = f"ruzgar_trim_{uuid.uuid4().hex[:10]}_{stem}{suf}"
        out_path = out_dir / out_name

        def _run():
            trim_media(
                input_path,
                out_path,
                start_sec=sp,
                duration_sec=dur,
                copy_streams=copy_flag,
            )

        await run_in_threadpool(_run)
        rel_out = out_path.relative_to(REPO_ROOT.resolve()).as_posix()
        return {"ok": True, "output_rel": rel_out}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        if tmp_input and os.path.isfile(tmp_input):
            try:
                os.unlink(tmp_input)
            except OSError:
                pass


@app.post("/api/video/transcode")
async def api_video_transcode(
    rel: Annotated[str | None, Form()] = None,
    file: UploadFile | None = File(None),
):
    """Tam dosyayı H.264 + AAC MP4 olarak yeniden kodlar."""
    if not ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail="ffmpeg bulunamadı: FFmpeg kurun ve PATH'e ekleyin.",
        )
    rel_s = (rel or "").strip()
    if rel_s and file is not None:
        raise HTTPException(status_code=400, detail="rel ve file aynı istekte kullanılamaz.")
    if not rel_s and file is None:
        raise HTTPException(status_code=400, detail="rel veya file gerekli.")

    tmp_input: str | None = None
    try:
        if rel_s:
            input_path = _repo_resolve_under_root(rel_s)
        else:
            raw = await file.read()
            if len(raw) < 64:
                raise HTTPException(status_code=400, detail="Dosya çok kısa veya boş.")
            if len(raw) > MAX_VIDEO_PROBE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dosya çok büyük (>{MAX_VIDEO_PROBE_BYTES // (1024 * 1024)} MB); proje içi rel kullanın.",
                )
            low = ((file.filename if file else "") or "").lower()
            sfx = ".bin"
            for ext in (".mkv", ".webm", ".mov", ".avi", ".mp4", ".m4v", ".mp3", ".wav"):
                if low.endswith(ext):
                    sfx = ext
                    break
            fd, tmp_input = tempfile.mkstemp(suffix=sfx)
            os.write(fd, raw)
            os.close(fd)
            input_path = Path(tmp_input)

        out_dir = export_directory(REPO_ROOT)
        out_path = out_dir / f"ruzgar_x264_{uuid.uuid4().hex[:10]}.mp4"

        def _run():
            transcode_to_mp4(input_path, out_path)

        await run_in_threadpool(_run)
        rel_out = out_path.relative_to(REPO_ROOT.resolve()).as_posix()
        return {"ok": True, "output_rel": rel_out}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        if tmp_input and os.path.isfile(tmp_input):
            try:
                os.unlink(tmp_input)
            except OSError:
                pass


@app.post("/api/video/concat")
async def api_video_concat(body: VideoConcatBody):
    """İki proje içi dosyayı birleştirir (ffmpeg concat demuxer)."""
    if not ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail="ffmpeg bulunamadı: FFmpeg kurun ve PATH'e ekleyin.",
        )
    a = (body.rel_a or "").strip()
    b = (body.rel_b or "").strip()
    if not a or not b:
        raise HTTPException(status_code=400, detail="rel_a ve rel_b gerekli.")
    pa = _repo_resolve_under_root(a)
    pb = _repo_resolve_under_root(b)
    out_dir = export_directory(REPO_ROOT)
    out_path = out_dir / f"ruzgar_concat_{uuid.uuid4().hex[:12]}.mp4"

    def _run():
        concat_two_files(pa, pb, out_path, copy_streams=bool(body.copy_streams))

    try:
        await run_in_threadpool(_run)
        rel_out = out_path.relative_to(REPO_ROOT.resolve()).as_posix()
        return {"ok": True, "output_rel": rel_out}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/video/edit/mix")
async def api_video_edit_mix(body: VideoEditMixBody):
    """Timeline parçalarını kesip birleştirir; metadata Merkezi Zihin Havuzu'na yazılır."""
    if not ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail="ffmpeg bulunamadı: FFmpeg kurun ve PATH'e ekleyin.",
        )
    if not body.clips:
        raise HTTPException(status_code=400, detail="En az bir parça gerekli.")

    from ilim_assistant.motorlar.video_motoru import EDIT_CLIP_MAX_SEC, mix_timeline_clips

    payload = [
        {
            "rel": (c.rel or "").strip(),
            "start_sec": float(c.start_sec or 0),
            "end_sec": c.end_sec,
            "label": (c.label or "").strip(),
        }
        for c in body.clips
    ]
    for i, row in enumerate(payload):
        if not row["rel"]:
            raise HTTPException(status_code=400, detail=f"Parça {i + 1}: rel boş.")
        if row["end_sec"] is not None:
            span = float(row["end_sec"]) - row["start_sec"]
            if span > EDIT_CLIP_MAX_SEC + 0.05:
                raise HTTPException(
                    status_code=400,
                    detail=f"Parça {i + 1}: en fazla {EDIT_CLIP_MAX_SEC // 60} dakika.",
                )

    def _run():
        return mix_timeline_clips(
            payload,
            workspace_root=str(REPO_ROOT.resolve()),
            copy_streams=bool(body.copy_streams),
            project_name=(body.project_name or "").strip(),
        )

    try:
        result = await run_in_threadpool(_run)
        meta = result.to_metadata()
        return {
            "ok": result.ok,
            "output_rel": result.output_rel,
            "project_id": result.project_id,
            "parts": result.parts,
            "total_duration_sec": result.total_duration_sec,
            "error": result.error,
            "metadata": meta,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


MAX_SUBTITLE_BYTES = 12 * 1024 * 1024


@app.post("/api/video/burn-subtitles")
async def api_video_burn_subtitles(
    rel_video: Annotated[str, Form()],
    rel_sub: Annotated[str, Form()],
):
    """Altyazıyı (SRT/ASS/VTT) videoya gömer; çıktı `.ruzgar-video-export/` altına yazılır."""
    if not ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail="ffmpeg bulunamadı: FFmpeg kurun ve PATH'e ekleyin.",
        )
    rv = (rel_video or "").strip()
    rs = (rel_sub or "").strip()
    if not rv or not rs:
        raise HTTPException(status_code=400, detail="rel_video ve rel_sub gerekli.")
    video_path = _repo_resolve_under_root(rv)
    sub_path = _repo_resolve_under_root(rs)
    if sub_path.stat().st_size > MAX_SUBTITLE_BYTES:
        raise HTTPException(status_code=400, detail="Altyazı dosyası çok büyük.")
    low = sub_path.suffix.lower()
    if low not in (".srt", ".ass", ".ssa", ".vtt"):
        raise HTTPException(
            status_code=400,
            detail="Altyazı uzantısı desteklenmiyor (.srt, .ass, .ssa, .vtt).",
        )
    out_dir = export_directory(REPO_ROOT)
    stem = video_path.stem or "video"
    out_path = out_dir / f"ruzgar_subburn_{uuid.uuid4().hex[:10]}_{stem}.mp4"

    def _run():
        burn_subtitles_into_mp4(video_path, sub_path, out_path)

    try:
        await run_in_threadpool(_run)
        rel_out = out_path.relative_to(REPO_ROOT.resolve()).as_posix()
        return {"ok": True, "output_rel": rel_out}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/video/mux-audio")
async def api_video_mux_audio(
    rel_video: Annotated[str, Form()],
    rel_audio: Annotated[str, Form()],
    copy_video: Annotated[str, Form()] = "true",
    shortest: Annotated[str, Form()] = "true",
):
    """Harici ses dosyasını videonun ses izine bağlar (çoğu durumda eski ses yerine geçer)."""
    if not ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail="ffmpeg bulunamadı: FFmpeg kurun ve PATH'e ekleyin.",
        )
    rv = (rel_video or "").strip()
    ra = (rel_audio or "").strip()
    if not rv or not ra:
        raise HTTPException(status_code=400, detail="rel_video ve rel_audio gerekli.")
    video_path = _repo_resolve_under_root(rv)
    audio_path = _repo_resolve_under_root(ra)
    copy_v = _parse_bool_form(copy_video, True)
    short = _parse_bool_form(shortest, True)
    out_dir = export_directory(REPO_ROOT)
    stem = video_path.stem or "video"
    out_path = out_dir / f"ruzgar_muxaud_{uuid.uuid4().hex[:10]}_{stem}.mp4"

    def _run():
        mux_replace_audio(
            video_path,
            audio_path,
            out_path,
            copy_video=copy_v,
            shortest=short,
        )

    try:
        await run_in_threadpool(_run)
        rel_out = out_path.relative_to(REPO_ROOT.resolve()).as_posix()
        return {"ok": True, "output_rel": rel_out}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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


@app.get("/api/workspace/read-pdf")
def api_workspace_read_pdf(rel: str = Query("")) -> dict[str, Any]:
    """PDF'den düz metin çıkarır (Okuma atölyesi). pypdf yoksa 503."""
    if not pdf_text_runtime_available():
        raise HTTPException(
            status_code=503,
            detail="PDF metin çıkarma için: pip install pypdf",
        )
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        raise HTTPException(status_code=400, detail="rel gerekli.")
    target = _repo_resolve_under_root(raw, must_be_dir=False)
    if target.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Dosya PDF değil.")
    max_bytes = 15_000_000
    if target.stat().st_size > max_bytes:
        raise HTTPException(status_code=400, detail=f"PDF çok büyük ({max_bytes // 1_000_000} MB sınır).")

    from pypdf import PdfReader

    reader = PdfReader(str(target))
    n_pages = len(reader.pages)
    max_pages = min(n_pages, 100)
    parts: list[str] = []
    for i in range(max_pages):
        try:
            t = reader.pages[i].extract_text() or ""
        except Exception:
            t = ""
        parts.append(t)
    full = "\n\n".join(parts).strip()
    hard_cap = 450_000
    truncated_len = False
    if len(full) > hard_cap:
        full = full[:hard_cap] + "\n\n… [metin uzun olduğu için kesildi]"
        truncated_len = True
    truncated_pages = max_pages < n_pages
    return {
        "ok": True,
        "text": full,
        "pages_total": n_pages,
        "pages_read": max_pages,
        "truncated_pages": truncated_pages,
        "truncated_length": truncated_len,
    }


def _docx_file_to_plain(target: Path) -> str:
    from docx import Document

    doc = Document(str(target))
    chunks: list[str] = []
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t:
            chunks.append(t)
    for tbl in doc.tables:
        for row in tbl.rows:
            cells = [(c.text or "").strip() for c in row.cells]
            line = " | ".join(x for x in cells if x)
            if line:
                chunks.append(line)
    return "\n\n".join(chunks).strip()


@app.get("/api/workspace/read-docx")
def api_workspace_read_docx(rel: str = Query("")) -> dict[str, Any]:
    """DOCX (Word) gövdesinden düz metin çıkarır. python-docx yoksa 503."""
    if not docx_text_runtime_available():
        raise HTTPException(
            status_code=503,
            detail="DOCX okuma için: pip install python-docx",
        )
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        raise HTTPException(status_code=400, detail="rel gerekli.")
    target = _repo_resolve_under_root(raw, must_be_dir=False)
    if target.suffix.lower() != ".docx":
        raise HTTPException(status_code=400, detail="Dosya DOCX değil (.doc eski format desteklenmez).")
    max_bytes = 15_000_000
    if target.stat().st_size > max_bytes:
        raise HTTPException(status_code=400, detail=f"Dosya çok büyük ({max_bytes // 1_000_000} MB sınır).")
    full = _docx_file_to_plain(target)
    hard_cap = 450_000
    truncated = False
    if len(full) > hard_cap:
        full = full[:hard_cap] + "\n\n… [metin uzun olduğu için kesildi]"
        truncated = True
    return {"ok": True, "text": full, "truncated_length": truncated}


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


def _iter_instant_chat_events(
    reply: str,
    user_message: str,
    *,
    session_wake_used: bool,
    msg_for_wake: str,
    orch: dict[str, Any] | None = None,
    instant_gundelik: bool = False,
    instant_clarify: bool = False,
) -> Iterator[dict]:
    """Ollama/RAG beklemeden tek tur bitir (SSE/WS)."""
    full_out = finalize_assistant_reply(reply)
    yield {"type": "token", "text": full_out}
    new_wake = session_wake_used or message_calls_wake_name(msg_for_wake)
    done: dict[str, Any] = {
        "type": "done",
        "full_reply": full_out,
        "user_message": user_message,
        "new_wake_used": new_wake,
    }
    if orch:
        try:
            from ilim_assistant.ana_motor_agent import mark_agent_answer_done

            if orch.get("agent_steps"):
                orch["agent_steps"] = mark_agent_answer_done(orch["agent_steps"])
        except Exception:
            pass
        done["orchestra"] = orch
    if instant_gundelik:
        done["instant_gundelik"] = True
    if instant_clarify:
        done["instant_clarify"] = True
    yield done


def iter_chat_turn_events(req: ChatRequest) -> Iterator[dict]:
    """SSE/WS: Ana motor durumları → prepare_turn (İdrak + orkestra) → LLM."""
    from ilim_assistant.idrak_on_islem import pretreat_user_turn

    pt = pretreat_user_turn(req.message, req.history)
    if pt.text != (req.message or "").strip():
        req = req.model_copy(update={"message": pt.text})
    mode_raw = _effective_chat_mode_raw(req)
    mode_norm = normalize_mode(mode_raw)
    coding = req.coding_mode or mode_norm == "programlama"
    yield {
        "type": "meta",
        "chat_route": {
            "mode_raw": (req.mode or "").strip() or None,
            "mode_effective": mode_norm,
            "coding_mode": coding,
            "idrak_surface": {
                "changed": pt.changed,
                "continuation": pt.continuation,
                "replacements": list(pt.replacements)[:8],
            },
        },
    }
    yield {"type": "status", "text": "Rüzgar hazırlanıyor…"}

    orch: dict[str, Any] = {}
    for _consumer in (
        "ilim_assistant.dinamit_hatirlatici:try_consume_hatirlatici_intent",
        "ilim_assistant.kisisel_hafiza:try_consume_memory_command",
        "ilim_assistant.gorev_yoneticisi:try_consume_task_command",
    ):
        try:
            mod_name, fn_name = _consumer.split(":", 1)
            mod = __import__(mod_name, fromlist=[fn_name])
            reply = getattr(mod, fn_name)(req.message)
            if reply:
                yield from _iter_instant_chat_events(
                    reply,
                    (req.message or "").strip(),
                    session_wake_used=req.session_wake_used,
                    msg_for_wake=req.message,
                    orch=orch,
                    instant_gundelik=True,
                )
                return
        except Exception:
            pass

    turn_plan = None
    motor_flags: dict[str, bool] = {}
    if os.environ.get("RUZGAR_ANA_MOTOR_PLAN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        if mode_norm in ("genel", "uretim", "gelisim"):
            try:
                from ilim_assistant.ana_motor_plan import plan_question
                from ilim_assistant.idrak_entegrasyon import motor_niyeti_heuristic

                motor_flags = motor_niyeti_heuristic(req.message)
                turn_plan = plan_question(req.message, mode_norm, motor_flags)
                yield {"type": "status", "text": turn_plan.status_text}
                plan_dict = turn_plan.to_dict()
                orch["plan"] = plan_dict
                yield {"type": "meta", "plan": plan_dict}
                try:
                    from ilim_assistant.ana_motor_plan import maybe_gundelik_instant_reply

                    instant = maybe_gundelik_instant_reply(
                        req.message,
                        mode_norm,
                        motor_flags,
                        question_plan=turn_plan,
                    )
                    if instant:
                        yield from _iter_instant_chat_events(
                            instant,
                            (req.message or "").strip(),
                            session_wake_used=req.session_wake_used,
                            msg_for_wake=req.message,
                            orch=orch,
                            instant_gundelik=True,
                        )
                        return
                except Exception:
                    pass
            except Exception:
                turn_plan = None

    agent_context = ""
    workspace_step = None
    retrieval_notes: list[str] = []
    if mode_norm in ("genel", "uretim", "gelisim"):
        _run_agent = turn_plan is None or bool(
            getattr(turn_plan, "use_ilim_rag", True)
        ) or getattr(turn_plan, "primary", "") in (
            "bilgi",
            "bilim",
            "dosya",
            "islem",
            "dilbilgisi",
        )
        if _run_agent:
            try:
                from ilim_assistant.ana_motor_agent import run_agent_workspace_phase

                agent_context, workspace_step, ws_events = run_agent_workspace_phase(
                    req.message,
                    mode_norm,
                    turn_plan,
                    workspace_root=req.workspace_root,
                )
                for ev in ws_events:
                    yield ev
            except Exception:
                agent_context = ""
                workspace_step = None

    reuse_b = None
    _skip_prefetch = mode_norm in ("programlama", "hafiza") or coding or (
        turn_plan is not None
        and hasattr(turn_plan, "use_ilim_rag")
        and not bool(turn_plan.use_ilim_rag)
    )
    if mode_norm == "programlama":
        yield {
            "type": "status",
            "text": "Programlama atölyesi — yerel ilim indeksi atlandı…",
        }
    if (
        mode_norm != "hafiza"
        and os.environ.get("RUZGAR_STREAM_PREFETCH_BUNDLE", "1").strip().lower()
        not in (
            "0",
            "false",
            "no",
        )
        and not _skip_prefetch
    ):
        bundle, evs = prefetch_main_engine_bundle_for_stream(
            req.message,
            req.history,
            mode_raw,
            question_plan=turn_plan,
        )
        for ev in evs:
            txt = str(ev.get("text") or "").strip()
            if txt:
                retrieval_notes.append(txt[:72])
            yield ev
        if evs or bundle.hits or (bundle.ilim_citation_tail or "").strip():
            reuse_b = bundle

    if mode_norm in ("genel", "uretim", "gelisim"):
        try:
            from ilim_assistant.ana_motor_agent import build_agent_steps

            orch["agent_steps"] = [
                s.to_dict()
                for s in build_agent_steps(
                    turn_plan, workspace_step, retrieval_notes
                )
            ]
        except Exception:
            pass

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
        reuse_main_engine_bundle=reuse_b,
        orchestration_out=orch,
        question_plan=turn_plan,
        agent_context=agent_context or None,
    )
    if prep is None:
        yield {"type": "error", "text": "Boş mesaj"}
        return

    msg, hits, user_payload, system, model, og_direct = prep
    new_wake = req.session_wake_used or message_calls_wake_name(msg)

    if og_direct is not None:
        _instant_g = False
        _instant_c = False
        try:
            from ilim_assistant.ana_motor_plan import maybe_gundelik_instant_reply

            _instant_g = bool(
                maybe_gundelik_instant_reply(
                    msg, mode_norm, motor_flags, question_plan=turn_plan
                )
            )
        except Exception:
            pass
        if turn_plan is not None and getattr(turn_plan, "clarification", None):
            clar = str(turn_plan.clarification or "").strip()
            if clar and str(og_direct or "").strip() == clar:
                _instant_c = True
        yield from _iter_instant_chat_events(
            og_direct,
            msg,
            session_wake_used=req.session_wake_used,
            msg_for_wake=msg,
            orch=orch,
            instant_gundelik=_instant_g,
            instant_clarify=_instant_c,
        )
        return

    prior = prior_messages_for_turn(req.history, mode_norm)
    try:
        brain_sel = select_brain_chain(
            message=msg,
            mode_norm=mode_norm,
            coding_mode=coding,
            question_plan=turn_plan,
            legacy_model=model,
        )
        yield {
            "type": "meta",
            "brain": brain_sel.to_public_dict(),
        }
    except Exception:
        pass
    reply_body = ""
    try:
        wants_dbg = mode_norm == "programlama" and wants_autonomous_code_debug(msg)
        retry_cap = code_debug_max_retries() if wants_dbg else 0
        extras_remaining = retry_cap
        active_prior: list = list(prior) if prior else []

        if wants_dbg:
            yield {"type": "status", "text": "Otomatik kod hata ayıklama (Faz 10.4)…"}

        while True:
            round_body = ""
            for piece in stream_chat_with_brain(
                system,
                user_payload,
                model=model,
                prior_messages=active_prior,
                mode_norm=mode_norm,
                coding_mode=coding,
                message=msg,
                question_plan=turn_plan,
            ):
                round_body += piece
                reply_body += piece
                yield {"type": "token", "text": piece}

            if not wants_dbg:
                break

            summ, pytest_rep = apply_assistant_reply_tools(
                round_body,
                req.workspace_root,
                run_pytest=True,
            )
            if pytest_rep is None:
                yield {
                    "type": "status",
                    "text": "Otomatik doğrulama atlandı — workspace kökü yok (LOCAL_TOOLS_ROOT).",
                }
                break
            if pytest_rep.ok:
                yield {
                    "type": "meta",
                    "code_debug": {"phase": "pytest_ok", "exit": pytest_rep.exit_code},
                }
                break
            if not summ.writes:
                yield {
                    "type": "status",
                    "text": "Otomatik debug durdu — model @@write ile dosya yazmadı.",
                }
                break
            if extras_remaining <= 0:
                lim_txt = (
                    "Otomatik tekrar kapalı (RUZGAR_CODE_DEBUG_LOOPS=0) — pytest hâlâ kırmızı."
                    if retry_cap == 0
                    else "Otomatik debug: deneme limiti doldu (RUZGAR_CODE_DEBUG_LOOPS)."
                )
                yield {"type": "status", "text": lim_txt}
                break

            extras_remaining -= 1
            snippet = (pytest_rep.output or "").strip()[:14000]
            fail_msg = (
                "[OTOMATIK DEBUG — Ümit & Gökçenur — Faz 10.6]\n"
                "pytest başarısız. Çıktıyı satır satır oku; **yalnızca gerekli** `@@write yol` + "
                "kod bloğu ile düzelt. Gereksiz refaktör yok; kabuk komutu yok.\n\n"
                f"```text\n{snippet}\n```\n"
            )
            active_prior = list(active_prior) + [
                {"role": "assistant", "content": round_body},
                {"role": "user", "content": fail_msg},
            ]
        footer = rag_footer(hits)
        body_fixed = finalize_assistant_reply(reply_body)
        full_out = body_fixed + footer
        done_llm: dict[str, Any] = {
            "type": "done",
            "full_reply": full_out,
            "user_message": msg,
            "new_wake_used": new_wake,
        }
        if orch:
            try:
                from ilim_assistant.ana_motor_agent import mark_agent_answer_done

                if orch.get("agent_steps"):
                    orch["agent_steps"] = mark_agent_answer_done(orch["agent_steps"])
            except Exception:
                pass
            done_llm["orchestra"] = orch
        yield done_llm
    except Exception as e:
        yield {"type": "error", "text": format_llm_user_error(e)}


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
