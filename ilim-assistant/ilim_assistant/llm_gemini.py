# Created by Ümit & Gökçenur
"""
Google Gemini API (Google AI Studio) — yerel Ollama'ya alternatif bulut beyin.

Ücretsiz geliştirici kotası: https://aistudio.google.com/apikey
REST: generativelanguage.googleapis.com/v1beta
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Iterator, Optional

import requests
from requests.adapters import HTTPAdapter

from ilim_assistant.defaults import DEFAULT_GEMINI_MODEL
from ilim_assistant.text_encoding import repair_utf8_mojibake

_GEMINI_API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
_http_session: requests.Session | None = None


def _session() -> requests.Session:
    global _http_session
    if _http_session is None:
        s = requests.Session()
        adapter = HTTPAdapter(pool_connections=2, pool_maxsize=4, max_retries=0)
        s.mount("https://", adapter)
        _http_session = s
    return _http_session


def gemini_api_key() -> str:
    return (
        os.environ.get("GOOGLE_GEMINI_API_KEY", "").strip()
        or os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("RUZGAR_GEMINI_API_KEY", "").strip()
    )


def gemini_configured() -> bool:
    return bool(gemini_api_key())


def _normalize_model_name(model: str) -> str:
    m = (model or "").strip()
    if m.startswith("models/"):
        m = m[7:]
    return m or DEFAULT_GEMINI_MODEL


def _gemini_timeout() -> tuple[float, float]:
    try:
        conn = float(os.environ.get("RUZGAR_GEMINI_CONNECT_TIMEOUT_SEC", "8"))
    except ValueError:
        conn = 8.0
    try:
        read = float(os.environ.get("RUZGAR_GEMINI_READ_TIMEOUT_SEC", "18"))
    except ValueError:
        read = 18.0
    return max(3.0, min(conn, 60.0)), max(5.0, min(read, 120.0))


def _gemini_stream_wall_sec() -> float:
    try:
        cap = float(os.environ.get("RUZGAR_GEMINI_STREAM_MAX_SEC", "45"))
    except ValueError:
        cap = 45.0
    return max(12.0, min(cap, 300.0))


def format_gemini_user_error(exc: BaseException) -> str:
    raw = str(exc).strip()
    low = raw.lower()
    model = os.environ.get("RUZGAR_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    if "timed out" in low or "timeout" in low:
        return (
            f"Gemini yanıt vermedi (zaman aşımı). Model: {model}. "
            "API anahtarınızı ve kotanızı Google AI Studio'dan kontrol edin."
        )
    if "connection" in low or "refused" in low or "failed to establish" in low:
        return (
            "Gemini API'ye bağlanılamadı. İnternet bağlantısını kontrol edin; "
            "GOOGLE_GEMINI_API_KEY tanımlı olmalı."
        )
    if "401" in raw or "403" in raw or "api key" in low or "permission" in low:
        return (
            "Gemini API anahtarı geçersiz veya yetkisiz. "
            "https://aistudio.google.com/apikey adresinden yeni anahtar alın ve "
            "GOOGLE_GEMINI_API_KEY ortam değişkenine yazın."
        )
    if "429" in raw or "quota" in low or "rate" in low:
        return (
            "Gemini kotası veya hız sınırı aşıldı. Bir süre bekleyin veya "
            "Google AI Studio kotanızı kontrol edin."
        )
    if "404" in raw and "model" in low:
        return (
            f"Gemini modeli bulunamadı: {model}. "
            "RUZGAR_GEMINI_MODEL değerini güncelleyin (ör. gemini-2.0-flash)."
        )
    if not raw:
        return "Gemini isteği başarısız (ayrıntı yok)."
    return f"Gemini hatası: {raw[:500]}"


def _build_gemini_contents(
    user: str,
    prior_messages: Optional[list] = None,
) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for m in prior_messages or []:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "").strip().lower()
        text = str(m.get("content") or "").strip()
        if not text:
            continue
        if role == "assistant":
            role = "model"
        if role not in ("user", "model"):
            continue
        contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": user}]})
    return contents


def _extract_text_from_chunk(obj: dict[str, Any]) -> str:
    candidates = obj.get("candidates") or []
    if not candidates:
        return ""
    c0 = candidates[0] if isinstance(candidates[0], dict) else {}
    content = c0.get("content") or {}
    parts = content.get("parts") or []
    chunks: list[str] = []
    for p in parts:
        if isinstance(p, dict) and p.get("text"):
            chunks.append(str(p["text"]))
    return "".join(chunks)


def _parse_stream_line(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    if line.startswith("data:"):
        line = line[5:].strip()
    if not line or line == "[DONE]":
        return ""
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return ""
    if isinstance(obj, list):
        out = ""
        for item in obj:
            if isinstance(item, dict):
                out += _extract_text_from_chunk(item)
        return out
    if isinstance(obj, dict):
        return _extract_text_from_chunk(obj)
    return ""


def chat_completion_stream_gemini(
    system: str,
    user: str,
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    prior_messages: Optional[list] = None,
    max_output_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Iterator[str]:
    """Gemini streamGenerateContent (SSE)."""
    key = (api_key or gemini_api_key()).strip()
    if not key:
        yield (
            "Gemini API anahtarı yok. GOOGLE_GEMINI_API_KEY tanımlayın "
            "(https://aistudio.google.com/apikey)."
        )
        return

    model_id = _normalize_model_name(model or os.environ.get("RUZGAR_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL)
    url = f"{_GEMINI_API_ROOT}/models/{model_id}:streamGenerateContent?alt=sse"

    try:
        mt = int(
            max_output_tokens
            if max_output_tokens is not None
            else os.environ.get("RUZGAR_GEMINI_MAX_OUTPUT_TOKENS", "4096")
        )
    except ValueError:
        mt = 4096
    try:
        temp = float(
            temperature
            if temperature is not None
            else os.environ.get("RUZGAR_GEMINI_TEMPERATURE", "0.35")
        )
    except ValueError:
        temp = 0.35

    payload: dict[str, Any] = {
        "contents": _build_gemini_contents(user, prior_messages),
        "generationConfig": {
            "temperature": temp,
            "maxOutputTokens": max(256, min(mt, 8192)),
        },
    }
    sys_txt = (system or "").strip()
    if sys_txt:
        payload["systemInstruction"] = {"parts": [{"text": sys_txt}]}

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": key,
    }

    try:
        with _session().post(
            url,
            json=payload,
            headers=headers,
            stream=True,
            timeout=_gemini_timeout(),
        ) as resp:
            if resp.status_code >= 400:
                err_body = resp.text[:800]
                yield format_gemini_user_error(
                    RuntimeError(f"HTTP {resp.status_code}: {err_body}")
                )
                return
            resp.encoding = "utf-8"
            accumulated = ""
            stream_deadline = time.monotonic() + _gemini_stream_wall_sec()
            for raw_line in resp.iter_lines(decode_unicode=False):
                if time.monotonic() > stream_deadline:
                    yield format_gemini_user_error(
                        TimeoutError(
                            f"Gemini akışı {_gemini_stream_wall_sec():.0f} sn içinde tamamlanmadı."
                        )
                    )
                    return
                if not raw_line:
                    continue
                try:
                    line = raw_line.decode("utf-8")
                except UnicodeDecodeError:
                    line = raw_line.decode("utf-8", errors="replace")
                piece = _parse_stream_line(line)
                if not piece:
                    continue
                if piece.startswith(accumulated):
                    delta = piece[len(accumulated) :]
                else:
                    delta = piece
                accumulated = piece
                if delta:
                    yield repair_utf8_mojibake(delta)
            if not accumulated:
                yield "Gemini boş yanıt döndürdü."
    except requests.RequestException as e:
        yield format_gemini_user_error(e)


def chat_completion_gemini(
    system: str,
    user: str,
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    prior_messages: Optional[list] = None,
) -> str:
    parts = list(
        chat_completion_stream_gemini(
            system,
            user,
            model=model,
            api_key=api_key,
            prior_messages=prior_messages,
        )
    )
    return repair_utf8_mojibake("".join(parts))
