"""Rüzgar — sohbet kapsamı (Madde 3): kullanıcı + cihaz izolasyonu.

Amaç: PC ile mobil (ve kaç cihaz olursa olsun) birbirinin sohbet geçmişini,
özetini ve «yankı» cevabını görmesin. Cevap yalnız soran cihaza gider.

Kapsam anahtarı:
  - Masaüstü (token yok)            → ``pc``
  - Mobil oturum (geçerli token)    → ``u:<kullanici>|d:<cihaz>``
  - Token var ama geçersiz/süresi dolmuş → ``anon:<kısa özet>`` (hiçbir geçmiş görmez)

Kapsam, istek girişinde ``ContextVar`` olarak bağlanır; arşiv ve özet katmanı
imza değiştirmeden ``current_scope()`` ile okur. Her HTTP/WS isteği kendi
asyncio görevinde çalıştığı için istekler arası sızıntı olmaz; anyio thread
havuzu bağlamı çağrı anında kopyalar.

Eski (kapsamsız) satırlar silinmez: ``RUZGAR_KAPSAM_LEGACY``
  - ``pc``   (varsayılan) → yalnız PC kapsamı görür
  - ``all``  → herkes görür (eski davranış)
  - ``none`` → kimse görmez

Kapatma (eski davranış): ``RUZGAR_KAPSAM=0``
"""

from __future__ import annotations

import hashlib
import os
import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

PC_KEY = "pc"
_SAFE = re.compile(r"[^A-Za-z0-9_.\-]")


def kapsam_enabled() -> bool:
    return (os.environ.get("RUZGAR_KAPSAM", "1") or "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def legacy_policy() -> str:
    v = (os.environ.get("RUZGAR_KAPSAM_LEGACY", "pc") or "pc").strip().lower()
    return v if v in ("pc", "all", "none") else "pc"


@dataclass(frozen=True)
class ChatScope:
    key: str
    user: str = "pc"
    device: str = "pc"
    conversation: str = ""
    authed: bool = False
    # Aynı isteğin tekrar çözülmesini önlemek için (token özeti, ham token değil)
    fingerprint: str = ""

    @property
    def is_pc(self) -> bool:
        return self.key == PC_KEY


PC_SCOPE = ChatScope(key=PC_KEY, fingerprint="pc|")

_current: ContextVar[ChatScope | None] = ContextVar("ruzgar_chat_scope", default=None)


def _clean(value: Any, limit: int = 64) -> str:
    return _SAFE.sub("", str(value or "").strip())[:limit]


def _fp(token: str, device_hint: str, conv: str) -> str:
    h = hashlib.sha1((token or "").encode("utf-8")).hexdigest()[:10] if token else ""
    return f"{h}|{device_hint}|{conv}"


def resolve_scope(
    session_token: str | None = None,
    *,
    device_hint: str | None = None,
    conversation_id: str | None = None,
) -> ChatScope:
    """İstek bilgisinden kapsamı çöz (ağ/disk dışında yan etki yok)."""
    tok = (session_token or "").strip()
    conv = _clean(conversation_id)
    dev_hint = _clean(device_hint)
    fp = _fp(tok, dev_hint, conv)
    if not tok:
        # Token yok → masaüstü. Aynı makinede çalışan başka bir istemci kendini
        # ``device_id`` ile ayırabilir; yoksa PC.
        if dev_hint and dev_hint != "pc":
            return ChatScope(
                key=f"d:{dev_hint}",
                user="anon",
                device=dev_hint,
                conversation=conv,
                authed=False,
                fingerprint=fp,
            )
        return ChatScope(
            key=PC_KEY, conversation=conv, fingerprint=fp
        )
    auth: dict[str, Any] | None = None
    try:
        from ilim_assistant.ruzgar_mobil_oturum import validate_token

        auth = validate_token(tok)
    except Exception:
        auth = None
    if not auth:
        digest = hashlib.sha1(tok.encode("utf-8")).hexdigest()[:8]
        return ChatScope(
            key=f"anon:{digest}",
            user="anon",
            device=f"anon-{digest}",
            conversation=conv,
            authed=False,
            fingerprint=fp,
        )
    user = _clean(auth.get("kullanici")) or "user"
    device = _clean(auth.get("device_id")) or _clean(dev_hint)
    if not device:
        # Cihaz kimliği hiç yoksa oturuma bağlı kal (başka cihazla karışmaz)
        device = "s" + hashlib.sha1(tok.encode("utf-8")).hexdigest()[:8]
    return ChatScope(
        key=f"u:{user}|d:{device}",
        user=user,
        device=device,
        conversation=conv,
        authed=True,
        fingerprint=fp,
    )


# ASGI katmanının bıraktığı (token, cihaz) — çözümleme tembel (ilk ihtiyaçta)
_pending: ContextVar[tuple[str, str] | None] = ContextVar(
    "ruzgar_chat_scope_pending", default=None
)


def current_scope() -> ChatScope:
    """Bağlı kapsam; yoksa PC (arka plan işleri, test, CLI)."""
    s = _current.get()
    if s is not None:
        return s
    p = _pending.get()
    if p:
        sc = resolve_scope(p[0], device_hint=p[1])
        _current.set(sc)
        return sc
    return PC_SCOPE


def bind_scope(scope: ChatScope) -> ChatScope:
    _current.set(scope)
    return scope


def bind_scope_for_request(req: Any) -> ChatScope:
    """``ChatRequest`` benzeri nesneden kapsamı bağla (aynı istek için tekrar çözmez)."""
    p = _pending.get() or ("", "")
    tok = getattr(req, "session_token", None) or p[0] or ""
    dev = getattr(req, "device_id", None) or p[1] or ""
    conv = (
        getattr(req, "conversation_id", None)
        or getattr(req, "ana_motor_session_id", None)
        or ""
    )
    fp = _fp(str(tok).strip(), _clean(dev), _clean(conv))
    cur = _current.get()
    if cur is not None and cur.fingerprint == fp:
        return cur
    return bind_scope(
        resolve_scope(str(tok), device_hint=str(dev), conversation_id=str(conv))
    )


def row_visible(row: dict[str, Any], scope: ChatScope | None = None) -> bool:
    """Arşiv satırı bu kapsama görünür mü?"""
    if not kapsam_enabled():
        return True
    sc = scope or current_scope()
    rk = row.get("scope")
    if rk:
        return str(rk) == sc.key
    pol = legacy_policy()
    if pol == "all":
        return True
    if pol == "none":
        return False
    return sc.is_pc


class KapsamASGIMiddleware:
    """Saf ASGI (tamponlama yok, SSE/WS'e dokunmaz): Bearer/cihaz başlığını bağlama bırak."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        try:
            if scope.get("type") in ("http", "websocket") and kapsam_enabled():
                hdr = {k: v for k, v in (scope.get("headers") or [])}
                auth = hdr.get(b"authorization", b"").decode("latin-1").strip()
                tok = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
                dev = hdr.get(b"x-ruzgar-device", b"").decode("latin-1").strip()
                if tok or dev:
                    _pending.set((tok, dev))
        except Exception:
            pass
        await self.app(scope, receive, send)


def kapsam_status() -> dict[str, Any]:
    sc = current_scope()
    return {
        "enabled": kapsam_enabled(),
        "legacy": legacy_policy(),
        "pc_key": PC_KEY,
        "current": sc.key,
    }
