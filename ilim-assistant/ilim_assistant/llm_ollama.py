"""Ollama yerel LLM veya OpenAI uyumlu HTTP API."""

from __future__ import annotations

import json
import os
from typing import Iterator, Optional

import requests
from requests.adapters import HTTPAdapter

from ilim_assistant.defaults import DEFAULT_OLLAMA_CHAT_MODEL
from ilim_assistant.text_encoding import repair_utf8_mojibake

_http_session: requests.Session | None = None


def format_llm_user_error(exc: BaseException) -> str:
    """Masaüstü / Ana Motor: Ollama hatalarını Ümit abi için okunur Türkçe metne çevirir."""
    raw = str(exc).strip()
    low = raw.lower()
    model = os.environ.get("OLLAMA_CHAT_MODEL", DEFAULT_OLLAMA_CHAT_MODEL)
    base = (
        os.environ.get("OLLAMA_API_BASE")
        or os.environ.get("OPENAI_COMPAT_BASE")
        or "http://127.0.0.1:11434/v1"
    ).rstrip("/")
    if "timed out" in low or "timeout" in low or "read timed out" in low:
        return (
            f"Ollama yanıt vermedi (zaman aşımı). Model: {model}. "
            "Ollama çalışıyor mu? İlk token büyük modellerde dakikalar sürebilir. "
            "Deneyin: `ollama serve` veya daha hafif model (`ollama pull llama3.2:3b`)."
        )
    if (
        "connection" in low
        or "refused" in low
        or "failed to establish" in low
        or "10061" in raw
        or "actively refused" in low
    ):
        return (
            f"Ollama'ya bağlanılamadı ({base}). "
            "Ollama uygulamasını veya `ollama serve` sürecini başlatın; "
            "Start-Ruzgar.ps1 API ile birlikte Ollama'yı da dener."
        )
    if "model" in low and ("not found" in low or "does not exist" in low):
        return (
            f"Model bulunamadı: {model}. "
            f"Kurulum: `ollama pull {model}` veya OLLAMA_CHAT_MODEL ortam değişkenini değiştirin."
        )
    if not raw:
        return "LLM isteği başarısız (ayrıntı yok). Ollama günlüklerine bakın."
    return f"LLM hatası: {raw[:500]}"


def _ollama_http_timeout(*, streaming: bool) -> float | tuple[float, float]:
    """
    (bağlan, oku) — okuma süresi iki kez arasında veya ilk bayta kadar boşluktur.
    Ağır model / uzun istemde ilk token 300 sn'yi aşabildiği için okuma üst sınırı env ile genişletilebilir.
    """
    try:
        conn = float(os.environ.get("RUZGAR_OLLAMA_CONNECT_TIMEOUT_SEC", "30"))
    except ValueError:
        conn = 30.0
    read_default = "900" if streaming else "480"
    raw_read = os.environ.get("RUZGAR_OLLAMA_READ_TIMEOUT_SEC", "").strip()
    if not raw_read:
        raw_read = os.environ.get("OLLAMA_REQUEST_READ_TIMEOUT_SEC", read_default)
    try:
        read_s = float(raw_read)
    except ValueError:
        read_s = float(read_default)
    read_s = max(60.0, min(read_s, 86400.0))
    conn = max(5.0, min(conn, 120.0))
    return (conn, read_s)


def ollama_reachable(timeout_sec: float = 2.5) -> bool:
    """Yerel Ollama dinliyor mu? (Gemini varken gereksiz yedek beklemesini keser)."""
    base = (
        os.environ.get("OLLAMA_API_BASE")
        or os.environ.get("OPENAI_COMPAT_BASE")
        or "http://127.0.0.1:11434/v1"
    ).rstrip("/")
    root = base[:-3] if base.endswith("/v1") else base
    try:
        r = _http_session_singleton().get(
            f"{root}/api/tags",
            timeout=max(1.0, min(timeout_sec, 8.0)),
        )
        return r.status_code == 200
    except Exception:
        return False


def _http_session_singleton() -> requests.Session:
    """Ollama’ya tekrarlayan isteklerde TCP bağlantısını yeniden kullan (keep-alive)."""
    global _http_session
    if _http_session is None:
        s = requests.Session()
        adapter = HTTPAdapter(pool_connections=4, pool_maxsize=8, max_retries=0)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _http_session = s
    return _http_session


def _build_chat_messages(
    system: str,
    user: str,
    prior_messages: Optional[list] = None,
) -> list[dict]:
    out: list[dict] = [{"role": "system", "content": system}]
    for m in prior_messages or []:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        out.append({"role": role, "content": content})
    out.append({"role": "user", "content": user})
    return out


def _apply_chat_limits(payload: dict) -> None:
    """Yanıt süresini makul tutmak için üst sınır (OpenAI uyumlu gövde)."""
    raw = os.environ.get("CHAT_MAX_TOKENS", "720")
    try:
        mt = int(raw)
        if mt > 0:
            payload["max_tokens"] = mt
    except ValueError:
        pass


def _apply_sampling_extras(payload: dict) -> None:
    """top_p: daha tutarlı çıktı; CHAT_TOP_P= boş bırakılırsa gönderilmez (model varsayılanı)."""
    raw = os.environ.get("CHAT_TOP_P", "0.92").strip()
    if not raw or raw in ("-", "none"):
        return
    try:
        tp = float(raw)
        if 0 < tp <= 1:
            payload["top_p"] = tp
    except ValueError:
        pass


def chat_completion(
    system: str,
    user: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    prior_messages: Optional[list] = None,
) -> str:
    """
    Yerel Ollama — OpenAI uyumlu /v1 uç noktası (OLLAMA_API_BASE).
    Bulut zeka için ``llm_gemini`` kullanın.
    """
    base = base_url or os.environ.get("OLLAMA_API_BASE") or os.environ.get(
        "OPENAI_COMPAT_BASE", "http://127.0.0.1:11434/v1"
    )
    key = api_key if api_key is not None else os.environ.get("OLLAMA_API_KEY") or os.environ.get(
        "OPENAI_COMPAT_KEY", "ollama"
    )
    m = model or os.environ.get("OLLAMA_CHAT_MODEL", DEFAULT_OLLAMA_CHAT_MODEL)

    payload = {
        "model": m,
        "messages": _build_chat_messages(system, user, prior_messages),
        "temperature": float(os.environ.get("CHAT_TEMPERATURE", "0.42")),
        "stream": False,
    }
    _apply_chat_limits(payload)
    _apply_sampling_extras(payload)
    url = base.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    try:
        resp = _http_session_singleton().post(
            url,
            json=payload,
            headers=headers,
            timeout=_ollama_http_timeout(streaming=False),
        )
        # Windows: Content-Type'ta charset yoksa requests ISO-8859-1 varsayabiliyor; Türkçe bozulur.
        resp.encoding = "utf-8"
        if resp.status_code >= 400:
            return f"[HTTP {resp.status_code}] {resp.text[:800]}"
        body = resp.json()
        out = body["choices"][0]["message"]["content"].strip()
        return repair_utf8_mojibake(out)
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        return format_llm_user_error(e)


def chat_completion_stream(
    system: str,
    user: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    prior_messages: Optional[list] = None,
) -> Iterator[str]:
    """
    OpenAI uyumlu streaming (SSE). Her parça assistant içeriğinden bir metin parçası.
    Hata durumunda tek seferlik bir hata metni verilir.
    """
    base = base_url or os.environ.get("OLLAMA_API_BASE") or os.environ.get(
        "OPENAI_COMPAT_BASE", "http://127.0.0.1:11434/v1"
    )
    key = api_key if api_key is not None else os.environ.get("OLLAMA_API_KEY") or os.environ.get(
        "OPENAI_COMPAT_KEY", "ollama"
    )
    m = model or os.environ.get("OLLAMA_CHAT_MODEL", DEFAULT_OLLAMA_CHAT_MODEL)

    payload = {
        "model": m,
        "messages": _build_chat_messages(system, user, prior_messages),
        "temperature": float(os.environ.get("CHAT_TEMPERATURE", "0.42")),
        "stream": True,
    }
    _apply_chat_limits(payload)
    _apply_sampling_extras(payload)
    url = base.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    try:
        with _http_session_singleton().post(
            url,
            json=payload,
            headers=headers,
            stream=True,
            timeout=_ollama_http_timeout(streaming=True),
        ) as resp:
            resp.encoding = "utf-8"
            if resp.status_code >= 400:
                err = resp.text[:800]
                yield f"[HTTP {resp.status_code}] {err}"
                return
            # decode_unicode=True yerine bayttan UTF-8: Windows'ta yanlış kod sayfası kullanımını engeller
            for raw in resp.iter_lines(decode_unicode=False):
                if not raw:
                    continue
                try:
                    line = raw.decode("utf-8")
                except UnicodeDecodeError:
                    line = raw.decode("utf-8", errors="replace")
                if line.startswith("data: "):
                    data = line[6:].strip()
                elif line.startswith("data:"):
                    data = line[5:].strip()
                else:
                    continue
                if data == "[DONE]":
                    break
                try:
                    body = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = body.get("choices") or []
                if not choices:
                    continue
                delta = (
                    (choices[0].get("delta") or {})
                    if isinstance(choices[0], dict)
                    else {}
                )
                piece = delta.get("content") or ""
                if piece:
                    # Artımlı mojibake onarımı önceki karakterleri değiştirebildiği için
                    # reply_body birikimini BOZUYORDU; akışta ham parça verilir.
                    # Birleşik onarım yalnızca tam metinde (desktop_server / done).
                    yield piece
    except requests.RequestException as e:
        yield format_llm_user_error(e)


def optional_web_context(query: str, max_results: int = 3) -> str:
    """Eski API uyumu: arama + kısa özet. Tam özellik için web_tools.build_web_context kullan."""
    if os.environ.get("ENABLE_WEB_SEARCH", "1") != "1":
        return ""
    try:
        from ilim_assistant.web_tools import build_web_context

        return build_web_context(query, max_results=max_results, fetch_first_n_urls=0)
    except Exception as e:
        return f"[Web araması başarısız: {e}]"
