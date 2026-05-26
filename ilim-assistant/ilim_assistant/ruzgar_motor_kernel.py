# Created by Ümit & Gökçenur
"""
Rüzgar Ortak Motor Çekirdeği (ROK) — U0.

Tüm yardımcı motorlar aynı tur mantığını paylaşır:
  sohbet | yap (ajan) | komut (anlık)

Motor özel davranış: `register_classifier(motor_id, fn)` ile bağlanır.
Programlama pilot: `programlama_faz68`.
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from typing import Any, Callable

KERNEL_VERSION = "ruzgar-motor-kernel-v1-2026-05-26"

IntentKind = str  # "chat" | "do" | "command"

INTENT_CHAT = "chat"
INTENT_DO = "do"
INTENT_COMMAND = "command"

_CLASSIFIERS: dict[str, Callable[..., dict[str, Any]]] = {}

_QUESTION_RE = re.compile(
    r"^(?:nedir|nasıl|nasil|ne\s+demek|açıkla|acikla|anlat|why|what\s+is|kim|kaç|"
    r"hangi|nerede|ne\s+zaman|mi\s*$|mı\s*$|mu\s*$|mü\s*$)\b",
    re.I,
)
_ACTION_RE = re.compile(
    r"(?:\b(?:yap|olustur|oluştur|ekle|duzelt|düzelt|geçir|gecir|bitir|tamamla|yaz|"
    r"güncelle|guncelle|kur|oluştur|refactor|fix|add|create|build|implement|calistir|"
    r"çalıştır|degistir|değiştir|guncelle|üret|uret|tasarla|hazirla|hazırla)\b)",
    re.I,
)


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def kernel_enabled() -> bool:
    return os.environ.get("RUZGAR_MOTOR_KERNEL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def register_classifier(
    motor_id: str,
    fn: Callable[..., dict[str, Any]],
) -> None:
    """Motor özel niyet sınıflandırıcısı kaydet."""
    mid = (motor_id or "").strip().lower()
    if mid:
        _CLASSIFIERS[mid] = fn


def motor_env(motor_id: str, key: str, default: str = "") -> str:
    """Motor izolasyonu: RUZGAR_<MOTOR>_<KEY> — çapraz faz env karışmasın."""
    mid = (motor_id or "").strip().upper().replace("-", "_")
    k = (key or "").strip().upper()
    specific = os.environ.get(f"RUZGAR_{mid}_{k}", "").strip()
    if specific:
        return specific
    return os.environ.get(key, default).strip() or default


def classify_base_intent(message: str) -> dict[str, Any]:
    """Motor bağımsız hafif ön sınıflandırma."""
    raw = (message or "").strip()
    low = _ascii_fold(raw)
    t0 = time.perf_counter()
    if not raw:
        return {
            "intent": INTENT_CHAT,
            "reason": "empty",
            "elapsed_ms": 0.0,
        }
    if _QUESTION_RE.search(low) and not _ACTION_RE.search(low):
        return {
            "intent": INTENT_CHAT,
            "reason": "question",
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    if _ACTION_RE.search(raw):
        return {
            "intent": INTENT_DO,
            "reason": "action_verb",
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    return {
        "intent": INTENT_CHAT,
        "reason": "default",
        "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
    }


def classify_motor_intent(
    message: str,
    motor_id: str,
    *,
    mode_norm: str = "",
    workspace_root: Any = None,
    active_file: str | None = None,
    coding_mode: bool = False,
    motor_flags: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """
    Birleşik niyet — önce motor sınıflandırıcısı, yoksa taban heuristik.
    """
    mid = (motor_id or mode_norm or "genel").strip().lower()
    t0 = time.perf_counter()
    out: dict[str, Any] = {
        "ok": True,
        "motor_id": mid,
        "intent": INTENT_CHAT,
        "reason": "unset",
        "start_agent": False,
        "kernel_version": KERNEL_VERSION,
    }
    if not kernel_enabled():
        base = classify_base_intent(message)
        out.update(base)
        out["kernel_disabled"] = True
        return out

    fn = _CLASSIFIERS.get(mid)
    if fn is not None:
        try:
            spec = fn(
                message,
                mode_norm=mode_norm or mid,
                workspace_root=workspace_root,
                active_file=active_file,
                coding_mode=coding_mode,
                motor_flags=motor_flags or {},
            )
            if isinstance(spec, dict) and spec.get("intent"):
                out.update(spec)
                out["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 2)
                return out
        except Exception as exc:
            out["classifier_error"] = str(exc)[:120]

    base = classify_base_intent(message)
    out.update(base)
    out["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return out


def sse_event(
    event_type: str,
    *,
    text: str = "",
    phase: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Tüm motorlarda ortak SSE sözleşmesi."""
    ev: dict[str, Any] = {
        "type": event_type,
        "kernel": KERNEL_VERSION,
        "ts": time.time(),
    }
    if text:
        ev["text"] = text
    if phase:
        ev["phase"] = phase
    if extra:
        ev.update(extra)
    return ev


def format_intent_hint(intent: dict[str, Any], *, motor_label: str = "Motor") -> str:
    """Kullanıcıya kısa Türkçe yönlendirme."""
    kind = str(intent.get("intent") or INTENT_CHAT)
    if kind == INTENT_DO and not intent.get("start_agent"):
        return (
            f"Ümit abi, {motor_label} işi anladı ama başlatamadı: "
            f"{intent.get('block_reason') or 'proje kapsamı seçin (projects/<ad>/).'}"
        )
    if kind == INTENT_CHAT:
        return ""
    return ""
