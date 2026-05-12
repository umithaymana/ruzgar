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
    Öncelik: OPENAI_COMPAT varsayılanı.
    - Ollama: base http://127.0.0.1:11434/v1, api_key=ollama (veya boş)
    - Model: OLLAMA_CHAT_MODEL veya model parametresi
    """
    base = base_url or os.environ.get("OPENAI_COMPAT_BASE", "http://127.0.0.1:11434/v1")
    key = api_key if api_key is not None else os.environ.get("OPENAI_COMPAT_KEY", "ollama")
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
        return f"[Hata] {e}"


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
    base = base_url or os.environ.get("OPENAI_COMPAT_BASE", "http://127.0.0.1:11434/v1")
    key = api_key if api_key is not None else os.environ.get("OPENAI_COMPAT_KEY", "ollama")
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
        yield f"[Hata] {e}"


def optional_web_context(query: str, max_results: int = 3) -> str:
    """Eski API uyumu: arama + kısa özet. Tam özellik için web_tools.build_web_context kullan."""
    if os.environ.get("ENABLE_WEB_SEARCH", "1") != "1":
        return ""
    try:
        from ilim_assistant.web_tools import build_web_context

        return build_web_context(query, max_results=max_results, fetch_first_n_urls=0)
    except Exception as e:
        return f"[Web araması başarısız: {e}]"
