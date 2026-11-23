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


# ── Madde 3.6: SSE / WS kimlik kapısı (/api/chat/full ile aynı kurallar) ────────

MSG_OTURUM_GECERSIZ = "Oturum geçersiz veya süresi dolmuş. PWA'dan tekrar giriş."
MSG_SOHBET_ACL = "Sohbet motoru bu kullanıcı için kapalı (panel ACL)."


def _env_on(name: str, default: str = "1") -> bool:
    return (os.environ.get(name, default) or default).strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def stream_auth_enabled() -> bool:
    """``RUZGAR_STREAM_AUTH=0`` → stream/WS eski davranış (doğrulama yok)."""
    return _env_on("RUZGAR_STREAM_AUTH")


def stream_slot_enabled() -> bool:
    """``RUZGAR_STREAM_SLOT=0`` → stream/WS kuyruk (eşzamanlı yazı tavanı) uygulanmaz."""
    return _env_on("RUZGAR_STREAM_SLOT")


def stream_auth_gate(session_token: str | None) -> dict[str, Any]:
    """Token varsa doğrula + sohbet ACL + (açıksa) kuyruk yuvası al.

    Token YOKSA (masaüstü) hiçbir şey yapmaz: ``{"ok": True}``.
    Dönüş: ``{"ok": True, "auth": dict|None, "slot": str|None}`` veya
    ``{"ok": False, "code": ..., "error": ...}``. Yuva alındıysa
    ``stream_auth_release`` ile bırakılmalı.
    """
    tok = (session_token or "").strip()
    if not tok or not stream_auth_enabled():
        return {"ok": True, "auth": None, "slot": None}
    from ilim_assistant.ruzgar_mobil_oturum import (
        begin_chat_slot,
        motor_allowed,
        validate_token,
    )

    auth = validate_token(tok)
    if auth is None:
        return {"ok": False, "code": "oturum_gecersiz", "error": MSG_OTURUM_GECERSIZ}
    if not motor_allowed(auth, "sohbet"):
        return {"ok": False, "code": "motor_acl", "error": MSG_SOHBET_ACL}
    slot = None
    if stream_slot_enabled():
        res = begin_chat_slot(tok)
        if not res.get("ok"):
            return {
                "ok": False,
                "code": "kuyruk",
                "error": str(res.get("message") or "kuyruk"),
                "queue": True,
            }
        slot = res.get("slot")
    return {"ok": True, "auth": auth, "slot": slot}


def stream_auth_release(gate: dict[str, Any] | None) -> None:
    """Kapıdan alınan kuyruk yuvasını bırak (her koşulda güvenli, idempotent)."""
    try:
        slot = (gate or {}).get("slot")
        if slot:
            from ilim_assistant.ruzgar_mobil_oturum import end_chat_slot

            end_chat_slot(slot)
            gate["slot"] = None  # type: ignore[index]
    except Exception:
        pass


def stream_auth_error_events(gate: dict[str, Any], user_message: str = "") -> list[dict[str, Any]]:
    """Reddedilen istek için istemcinin anladığı olay çifti (error + done)."""
    err = str(gate.get("error") or MSG_OTURUM_GECERSIZ)
    code = str(gate.get("code") or "oturum_gecersiz")
    return [
        {"type": "error", "text": err, "code": code, "auth_error": True},
        {
            "type": "done",
            "full_reply": err,
            "user_message": (user_message or "").strip(),
            "stream_error": True,
            "auth_error": True,
            "code": code,
        },
    ]


def kapsam_status() -> dict[str, Any]:
    sc = current_scope()
    return {
        "enabled": kapsam_enabled(),
        "legacy": legacy_policy(),
        "pc_key": PC_KEY,
        "current": sc.key,
    }
