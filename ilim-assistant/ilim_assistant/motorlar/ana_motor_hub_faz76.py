# Created by Ümit & Gökçenur
"""
Ana Motor — Faz 76: ROK hub (U7).

Genel modda niyet → yardımcı motora sessiz yönlendirme + anlık köprü.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

from ilim_assistant.ruzgar_motor_kernel import (
    INTENT_CHAT,
    INTENT_COMMAND,
    INTENT_DO,
    classify_motor_intent,
)

FAZ76_VERSION = "ana-motor-hub-faz76-v1-2026-05-26"

_HUB_MOTORS = (
    "programlama",
    "video",
    "hafiza",
    "tercume",
    "ses",
    "okuma",
)

_MOTOR_LABEL = {
    "programlama": "Programlama",
    "video": "Video",
    "hafiza": "Hafıza",
    "tercume": "Tercüme",
    "ses": "Ses",
    "okuma": "Okuma / İlim",
    "genel": "Ana Motor",
}

_HELP_RE = re.compile(
    r"(?:hangi\s+motor|motor\s+yönlendir|motor\s+yonlendir|hub\s+durum|"
    r"orkestra\s+özeti|orkestra\s+ozeti)",
    re.I,
)
_VIDEO_DL_HINT = re.compile(
    r"(?:indir|download|youtube|youtu\.be)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_HUB", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz76_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def motor_label(motor_id: str) -> str:
    return _MOTOR_LABEL.get((motor_id or "").strip().lower(), motor_id or "?")


def _score_intent(intent: dict[str, Any]) -> int:
    kind = str(intent.get("intent") or INTENT_CHAT)
    if kind == INTENT_DO:
        return 3
    if kind == INTENT_COMMAND:
        return 2
    return 0


def is_video_download_request(message: str) -> bool:
    """YouTube/web + indir — Ana Motor'dan doğrudan video motoru."""
    raw = (message or "").strip()
    if not raw or not _VIDEO_DL_HINT.search(raw):
        return False
    try:
        from ilim_assistant.motorlar.video_faz71 import extract_urls

        urls = extract_urls(raw)
    except Exception:
        urls = []
    if not urls:
        return False
    blob = _ascii_fold(raw + " " + " ".join(urls))
    return "youtube" in blob or "youtu.be" in blob


def resolve_hub_target(
    message: str,
    motor_flags: dict[str, bool] | None = None,
) -> tuple[str, dict[str, Any]]:
    """En uygun yardımcı motor; genel = Ana Motor'da kal."""
    flags = motor_flags or {}
    msg = (message or "").strip()
    meta: dict[str, Any] = {"version": FAZ76_VERSION, "candidates": []}

    if not msg or not _enabled():
        return "genel", meta

    if is_video_download_request(msg):
        meta["candidates"].append(
            {"motor": "video", "score": 10, "reason": "youtube_download"}
        )
        meta["winner"] = "video"
        meta["reason"] = "youtube_download"
        return "video", meta

    try:
        from ilim_assistant.motorlar.programlama_faz10 import should_delegate_to_programlama

        if should_delegate_to_programlama(
            msg, "genel", coding_mode=False, motor_flags=flags
        ):
            meta["candidates"].append(
                {"motor": "programlama", "score": 9, "reason": "faz10_delegate"}
            )
            meta["winner"] = "programlama"
            meta["reason"] = "faz10_delegate"
            return "programlama", meta
    except Exception:
        pass

    best_id = "genel"
    best_score = 0
    best_reason = "stay_genel"

    for mid in _HUB_MOTORS:
        if mid == "programlama":
            continue
        try:
            spec = classify_motor_intent(
                msg,
                mid,
                mode_norm=mid,
                motor_flags=flags,
            )
        except Exception:
            continue
        sc = _score_intent(spec)
        if flags.get(mid) or flags.get("bilim") and mid == "okuma":
            sc += 1
        if flags.get("bellek") and mid == "hafiza":
            sc += 1
        meta["candidates"].append(
            {"motor": mid, "score": sc, "reason": spec.get("reason"), "intent": spec.get("intent")}
        )
        if sc > best_score:
            best_score = sc
            best_id = mid
            best_reason = str(spec.get("reason") or "rok")

    if best_score > 0:
        meta["winner"] = best_id
        meta["reason"] = best_reason
        return best_id, meta

    meta["winner"] = "genel"
    meta["reason"] = "no_strong_motor"
    return "genel", meta


def maybe_hub_instant(
    message: str,
    motor_flags: dict[str, bool] | None = None,
) -> str | None:
    """Genel modda anlık yardımcı motor yanıtı (varsa)."""
    if not _enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None

    if _HELP_RE.search(_ascii_fold(raw)):
        return format_hub_help()

    if is_video_download_request(raw):
        try:
            from ilim_assistant.motorlar.video_faz71 import maybe_instant_faz71

            vhit = maybe_instant_faz71(raw)
            if vhit:
                return vhit
        except Exception:
            pass

    try:
        from ilim_assistant.motorlar.hafiza_faz75 import maybe_instant_faz75

        hit = maybe_instant_faz75(raw, mode_norm="hafiza")
        if hit:
            return hit
    except Exception:
        pass

    target, _meta = resolve_hub_target(raw, motor_flags)
    if target == "genel":
        return None

    _instant_fns: dict[str, tuple[str, str]] = {
        "video": ("ilim_assistant.motorlar.video_faz71", "maybe_instant_faz71"),
        "ses": ("ilim_assistant.motorlar.ses_faz72", "maybe_instant_faz72"),
        "okuma": ("ilim_assistant.motorlar.okuma_faz73", "maybe_instant_faz73"),
        "tercume": ("ilim_assistant.motorlar.tercume_faz74", "maybe_instant_faz74"),
    }
    spec = _instant_fns.get(target)
    if spec:
        try:
            mod = __import__(spec[0], fromlist=[spec[1]])
            fn = getattr(mod, spec[1])
            hit = fn(raw)
            if hit:
                return hit
        except Exception:
            pass

    if target == "programlama":
        try:
            from ilim_assistant.motorlar.programlama_motoru import (
                maybe_programlama_instant_reply,
                unpack_programlama_instant,
            )

            raw_prog = maybe_programlama_instant_reply(
                raw, "programlama", workspace_root=None
            )
            if raw_prog:
                text, _ = unpack_programlama_instant(raw_prog)
                if text:
                    return text
        except Exception:
            pass

    return None


def format_hub_help() -> str:
    lines = [
        "Ümit abi, **Ana Motor hub (Faz 76)** — doğal cümleyle yardımcı motora gider:",
        "",
        "· Kod / proje → **Programlama**",
        "· Video indir / FFmpeg → **Video**",
        "· Hatırla / görev → **Hafıza**",
        "· Çevir → **Tercüme**",
        "· Ses / TTS → **Ses**",
        "· Arşiv / ilim metni → **Okuma**",
        "",
        "İsterseniz ilgili sekmeye geçmeden Ana Motor'da yazmaya devam edebilirsiniz.",
        f"({FAZ76_VERSION})",
    ]
    return "\n".join(lines)


def hub_directive_for_mode(target: str, meta: dict[str, Any] | None = None) -> str:
    m = meta or {}
    reason = m.get("reason") or "rok"
    return (
        f"[ANA MOTOR HUB — Faz 76]\n"
        f"Bu tur **{motor_label(target)}** motoruna yönlendirildi ({reason}).\n"
        "Yanıtı o motorun araçları ve üslubuyla ver; kullanıcıya sekme değiştirmesi "
        "şart değil.\n"
    )


def build_delegated_motor_context(target: str, message: str) -> str:
    """Hub delege modunda tek motor bağlamı (ağır çekirdek yerine)."""
    mid = (target or "").strip().lower()
    msg = (message or "").strip()
    loaders: dict[str, tuple[str, str]] = {
        "video": ("ilim_assistant.motorlar.video_motoru", "build_motor_context"),
        "ses": ("ilim_assistant.ses_motoru", "build_motor_context"),
        "okuma": ("ilim_assistant.okuma_motoru", "build_motor_context"),
        "tercume": ("ilim_assistant.tercume_motoru", "build_motor_context"),
        "hafiza": ("ilim_assistant.motorlar.hafiza_motoru", "build_motor_context"),
        "programlama": (
            "ilim_assistant.motorlar.programlama_motoru",
            "build_motor_context",
        ),
    }
    spec = loaders.get(mid)
    if not spec:
        return ""
    try:
        mod = __import__(spec[0], fromlist=[spec[1]])
        fn = getattr(mod, spec[1])
        if mid == "programlama":
            return str(fn(msg, workspace_root=None) or "").strip()
        return str(fn(msg) or "").strip()
    except Exception:
        return ""


def apply_genel_hub_routing(
    message: str,
    *,
    motor_flags: dict[str, bool] | None = None,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    """
    Genel mod turu: anlık yanıt veya mod değişimi.
    Dönüş: og_direct | mode | hub_meta
    """
    out: dict[str, Any] = {"hub_meta": {}, "version": FAZ76_VERSION}
    if not _enabled():
        return out

    flags = motor_flags
    if flags is None:
        try:
            from ilim_assistant.idrak_entegrasyon import motor_niyeti_heuristic

            flags = motor_niyeti_heuristic(message)
        except Exception:
            flags = {}

    instant = maybe_hub_instant(message, motor_flags=flags)
    if instant:
        out["og_direct"] = instant
        out["hub_meta"] = {"instant": True}
        return out

    target, meta = resolve_hub_target(message, flags)
    out["hub_meta"] = meta
    if target != "genel":
        out["mode"] = target
        out["hub_directive"] = hub_directive_for_mode(target, meta)
    return out


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["ana_motor_hub_faz76"] = faz76_enabled()
    return out
