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
    "mimar",
    "hizir",
)

_MOTOR_LABEL = {
    "programlama": "Programlama",
    "video": "Video",
    "hafiza": "Hafıza",
    "tercume": "Tercüme",
    "ses": "Ses",
    "mimar": "Mimar atölyesi",
    "okuma": "Mimar (eski ad)",
    "hizir": "Hızır / Ticaret",
    "genel": "Ana Motor",
}

_HELP_RE = re.compile(
    r"(?:hangi\s+motor|motor\s+yönlendir|motor\s+yonlendir|hub\s+durum|"
    r"orkestra\s+özeti|orkestra\s+ozeti)",
    re.I,
)
_VIDEO_DL_HINT = re.compile(
    r"(?:indir|indirme|download|youtube|youtu\.be|dailymotion|dai\.ly|vimeo|tiktok|twitch|"
    r"oynat|izle|aç|ac|burada\s+oynat|sinema|video\s+at|"
    r"bunu|sunu|şunu|videoyu|filmi|oynayan|paneldeki|link)",
    re.I,
)
_VIDEO_HOST_HINT = re.compile(
    r"youtube|youtu\.be|dailymotion|dai\.ly|vimeo|tiktok|twitch|twitter|x\.com|"
    r"facebook|fb\.watch|instagram|\.mp4|\.mkv|\.webm|\.m3u8",
    re.I,
)
_MULTI_STEP_RE = re.compile(
    r"(?:\sve\s|\s+sonra\s+|,\s*|\s+ardından\s|\s+ardindan\s)",
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


def is_video_url_message(message: str) -> bool:
    """Mesajda tanınan video sayfası veya dosya URL'si var mı."""
    raw = (message or "").strip()
    if not raw:
        return False
    try:
        from ilim_assistant.motorlar.video_faz71 import extract_urls

        urls = extract_urls(raw)
    except Exception:
        urls = []
    if not urls:
        return False
    blob = _ascii_fold(raw + " " + " ".join(urls))
    return bool(_VIDEO_HOST_HINT.search(blob))


def is_video_download_request(message: str) -> bool:
    """Video URL + indir/oynat/aç — veya yalnızca link yapıştırma → sinema."""
    raw = (message or "").strip()
    if not raw or not is_video_url_message(raw):
        return False
    if _VIDEO_DL_HINT.search(raw):
        return True
    try:
        from ilim_assistant.motorlar.video_faz71 import extract_urls

        urls = extract_urls(raw)
    except Exception:
        urls = []
    if not urls:
        return False
    rest = raw
    for u in urls:
        rest = rest.replace(u, "")
    rest = re.sub(r"https?://[^\s]+", "", rest).strip()
    return len(rest) < 48 and len(raw) < 220


def is_video_workflow_request(message: str) -> bool:
    """Kesim, kurgu, medya bilgisi vb. — genel moddan video motoruna."""
    if is_video_download_request(message):
        return True
    raw = (message or "").strip()
    if not raw:
        return False
    try:
        from ilim_assistant.motorlar.video_faz84 import wants_video_search

        if wants_video_search(raw):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.video_faz71 import classify_video_intent

        intent = classify_video_intent(raw, mode_norm="video")
        kind = str(intent.get("intent") or INTENT_CHAT)
        reason = str(intent.get("reason") or "")
        if kind in (INTENT_DO, INTENT_COMMAND) and reason not in (
            "question",
            "conversation",
            "empty",
        ):
            return True
    except Exception:
        pass
    low = _ascii_fold(raw)
    if _MULTI_STEP_RE.search(low) and re.search(
        r"indir|kes|kurgu|altyaz|mux|medya\s+bilgi|dönüştür|donustur|listeye\s+ekle",
        low,
    ):
        return True
    return bool(
        re.search(
            r"video|ffmpeg|kesim|\bkes\b|kurgu|montaj|altyaz|sinema|medya\s+bilgi|"
            r"transcode|donustur|dönüştür|panel.*ac|panel.*aç|bunu|şunu|oynayan",
            low,
        )
    )


def resolve_hub_target(
    message: str,
    motor_flags: dict[str, bool] | None = None,
    workspace_root: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """En uygun yardımcı motor; genel = Ana Motor'da kal."""
    flags = motor_flags or {}
    msg = (message or "").strip()
    meta: dict[str, Any] = {"version": FAZ76_VERSION, "candidates": []}

    if not msg or not _enabled():
        return "genel", meta

    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(msg):
            meta["winner"] = "genel"
            meta["reason"] = "casual_social"
            return "genel", meta
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.motor_ogrenilen_eylemler import match_learned_action

        learned = match_learned_action(msg, workspace_root)
        if learned and learned.get("motor"):
            mid = str(learned["motor"]).strip().lower()
            meta["learned_action"] = learned
            meta["candidates"].append(
                {
                    "motor": mid,
                    "score": 99,
                    "reason": "learned_action",
                    "action_id": learned.get("id"),
                }
            )
            meta["winner"] = mid
            meta["reason"] = "learned_action"
            return mid, meta
    except Exception:
        pass

    if is_video_download_request(msg):
        meta["candidates"].append(
            {"motor": "video", "score": 10, "reason": "video_url_open"}
        )
        meta["winner"] = "video"
        meta["reason"] = "video_url_open"
        return "video", meta

    try:
        from ilim_assistant.motorlar.video_faz84 import wants_video_search

        if wants_video_search(msg):
            meta["candidates"].append(
                {"motor": "video", "score": 9, "reason": "youtube_search"}
            )
            meta["winner"] = "video"
            meta["reason"] = "youtube_search"
            return "video", meta
    except Exception:
        pass

    if is_video_workflow_request(msg):
        meta["candidates"].append(
            {"motor": "video", "score": 8, "reason": "video_workflow"}
        )
        meta["winner"] = "video"
        meta["reason"] = "video_workflow"
        return "video", meta

    try:
        from ilim_assistant.motorlar.motor_kabiliyetleri import resolve_target_from_registry

        reg_id, reg_meta = resolve_target_from_registry(msg)
        if reg_id:
            meta["registry"] = reg_meta
            reg_score = int(reg_meta.get("score") or 0)
            if reg_score >= 4:
                meta["candidates"].append(
                    {
                        "motor": reg_id,
                        "score": reg_score,
                        "reason": "kabiliyet_registry",
                    }
                )
                meta["winner"] = reg_id
                meta["reason"] = "kabiliyet_registry"
                return reg_id, meta
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.hizir_faz84 import wants_hub_hizir_route

        if wants_hub_hizir_route(msg):
            meta["candidates"].append(
                {"motor": "hizir", "score": 9, "reason": "hizir_trade"}
            )
            meta["winner"] = "hizir"
            meta["reason"] = "hizir_trade"
            return "hizir", meta
    except Exception:
        pass

    if flags.get("tercume"):
        try:
            from ilim_assistant.motorlar.tercume_faz74 import classify_tercume_intent
            from ilim_assistant.ruzgar_motor_kernel import INTENT_DO

            tint = classify_tercume_intent(msg, mode_norm="tercume")
            if tint.get("intent") == INTENT_DO:
                meta["candidates"].append(
                    {"motor": "tercume", "score": 10, "reason": "translate_do"}
                )
                meta["winner"] = "tercume"
                meta["reason"] = "translate_do"
                return "tercume", meta
        except Exception:
            pass

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
        if flags.get(mid) or (
            mid == "mimar"
            and (flags.get("okuma") or flags.get("bilim") or flags.get("mimar"))
        ):
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


_MOTOR_INSTANT_FNS: dict[str, tuple[str, str]] = {
    "video": ("ilim_assistant.motorlar.video_faz71", "maybe_instant_faz71"),
    "ses": ("ilim_assistant.motorlar.ses_faz72", "maybe_instant_faz72"),
    "mimar": ("ilim_assistant.motorlar.mimar_faz5", "maybe_instant_faz5"),
    "okuma": ("ilim_assistant.motorlar.okuma_faz73", "maybe_instant_faz73"),
    "tercume": ("ilim_assistant.motorlar.tercume_faz74", "maybe_instant_faz74"),
}


def _try_programlama_instant(
    raw: str, workspace_root: str | None
) -> tuple[str | None, dict[str, Any]]:
    try:
        from ilim_assistant.motorlar.programlama_motoru import (
            maybe_programlama_instant_reply,
            unpack_programlama_instant,
        )

        raw_prog = maybe_programlama_instant_reply(
            raw, "programlama", workspace_root=workspace_root
        )
        if raw_prog:
            return unpack_programlama_instant(raw_prog)
    except Exception:
        pass
    return None, {}


def maybe_motor_instant_for_target(
    message: str,
    target: str,
    *,
    workspace_root: str | None = None,
) -> tuple[str | None, dict[str, Any]]:
    """Tek hedef motorda anında metin yanıtı (Faz A — hub delegasyon)."""
    mid = (target or "").strip().lower()
    if mid == "okuma":
        mid = "mimar"
    raw = (message or "").strip()
    extra: dict[str, Any] = {}
    if not raw or not mid or mid == "genel":
        return None, extra

    if mid == "hafiza":
        try:
            from ilim_assistant.motorlar.hafiza_faz75 import maybe_instant_faz75

            hit = maybe_instant_faz75(raw, mode_norm="hafiza", allow_lookup=False)
            if hit:
                return hit, extra
        except Exception:
            pass
        return None, extra

    if mid == "programlama":
        text, prog_meta = _try_programlama_instant(raw, workspace_root)
        if text:
            extra.update(prog_meta)
            return text, extra
        return None, extra

    if mid == "video":
        if is_video_download_request(raw):
            try:
                from ilim_assistant.motorlar.video_faz71 import maybe_instant_faz71

                vhit = maybe_instant_faz71(raw)
                if vhit:
                    return vhit, extra
            except Exception:
                pass
        try:
            from ilim_assistant.motorlar.video_faz84 import maybe_instant_faz84

            v84 = maybe_instant_faz84(raw, workspace_root)
            if v84:
                return v84, extra
        except Exception:
            pass

    if mid == "hizir":
        try:
            from ilim_assistant.motorlar.hizir_faz84 import maybe_instant_faz84 as hizir_hit

            hh = hizir_hit(raw, mode_norm="hizir")
            if hh:
                return hh, extra
        except Exception:
            pass

    spec = _MOTOR_INSTANT_FNS.get(mid)
    if spec:
        try:
            mod = __import__(spec[0], fromlist=[spec[1]])
            fn = getattr(mod, spec[1])
            hit = fn(raw)
            if hit:
                return str(hit).strip() or None, extra
        except Exception:
            pass

    return None, extra


def build_motor_dispatch_payload(
    message: str,
    target: str,
    *,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    """Masaüstü hub — hedef motorda anında iş / metin yanıtı."""
    mid = (target or "").strip().lower()
    if mid == "okuma":
        mid = "mimar"
    try:
        from ilim_assistant.ana_motor_backend_yurut import execute_backend_motor

        be = execute_backend_motor(message, mid, workspace_root=workspace_root)
        if be.get("handled") or be.get("error"):
            out = {
                "ok": bool(be.get("ok", True)),
                "handled": bool(be.get("handled")),
                "instant": bool(be.get("handled")),
                "target": mid,
                "target_label": motor_label(mid),
                "version": FAZ76_VERSION,
                "backend_yurut": True,
            }
            if be.get("reply"):
                out["reply"] = be["reply"]
            if be.get("error"):
                out["error"] = be["error"]
            if be.get("meta"):
                out["meta"] = be["meta"]
            return out
    except Exception:
        pass
    reply, meta = maybe_motor_instant_for_target(
        message, mid, workspace_root=workspace_root
    )
    out: dict[str, Any] = {
        "ok": True,
        "handled": bool(reply),
        "instant": bool(reply),
        "target": mid,
        "target_label": motor_label(mid),
        "version": FAZ76_VERSION,
    }
    if reply:
        out["reply"] = reply
    if meta:
        out["meta"] = meta
    return out


def maybe_hub_instant(
    message: str,
    motor_flags: dict[str, bool] | None = None,
    workspace_root: str | None = None,
) -> str | None:
    """Genel modda anlık yardımcı motor yanıtı (varsa)."""
    if not _enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None

    try:
        from ilim_assistant.motorlar.motor_ogrenilen_eylemler import try_instant_learned_commands

        teach = try_instant_learned_commands(raw, workspace_root)
        if teach:
            return teach
    except Exception:
        pass

    if _HELP_RE.search(_ascii_fold(raw)):
        return format_hub_help()

    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(raw):
            return None
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.video_faz84 import maybe_instant_faz84

        v84 = maybe_instant_faz84(raw, workspace_root)
        if v84:
            return v84
    except Exception:
        pass

    if is_video_download_request(raw):
        try:
            from ilim_assistant.motorlar.video_faz71 import maybe_instant_faz71

            vhit = maybe_instant_faz71(raw)
            if vhit:
                return vhit
        except Exception:
            pass

    try:
        from ilim_assistant.motorlar.hizir_faz84 import maybe_instant_faz84 as hizir_hit

        hh = hizir_hit(raw, mode_norm="hizir")
        if hh:
            return hh
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.hafiza_faz75 import maybe_instant_faz75_hub

        hit = maybe_instant_faz75_hub(raw)
        if hit:
            return hit
    except Exception:
        pass

    target, _meta = resolve_hub_target(raw, motor_flags, workspace_root=workspace_root)
    if target == "genel":
        return None

    reply, _ = maybe_motor_instant_for_target(raw, target, workspace_root=workspace_root)
    return reply


def format_hub_help() -> str:
    lines = [
        "Ümit abi, **Ana Motor hub (Faz 76)** — doğal cümleyle yardımcı motora gider:",
        "",
        "· Kod / proje → **Programlama**",
        "· Video indir / FFmpeg → **Video**",
        "· Hatırla / görev → **Hafıza**",
        "· Çevir → **Tercüme**",
        "· Ses / TTS → **Ses**",
        "· Fotoğraf / sanat / çizim → **Mimar**",
        "· Arşiv / ilim metni → **Mimar** (eski Okuma)",
        "· Pazar / fırsat / ürün tara → **Hızır**",
        "· Video ara (isim) → **Video** (liste; «2 numarayı indir»)",
        "",
        "İsterseniz ilgili sekmeye geçmeden Ana Motor'da yazmaya devam edebilirsiniz.",
        "",
        "**Faz C — eylem öğretme:**",
        "· `eylem öğret: «tetik cümle» → video/kes`",
        "· `eylem listesi` · `eylem paneli` · `eylem sil: «tetik»`",
        f"({FAZ76_VERSION})",
    ]
    return "\n".join(lines)


def hub_directive_for_mode(
    target: str,
    meta: dict[str, Any] | None = None,
    message: str = "",
) -> str:
    m = meta or {}
    reason = m.get("reason") or "rok"
    extra = ""
    try:
        from ilim_assistant.motorlar.ruzgar_hub_faz85 import hub_delegate_directive_extra

        extra = hub_delegate_directive_extra(target, message)
    except Exception:
        pass
    return (
        f"[ANA MOTOR HUB — Faz 76]\n"
        f"Bu tur **{motor_label(target)}** motoruna yönlendirildi ({reason}).\n"
        "Yanıtı o motorun araçları ve üslubuyla ver; kullanıcıya sekme değiştirmesi "
        "şart değil.\n"
        f"{extra}"
    )


def build_delegated_motor_context(
    target: str,
    message: str,
    *,
    workspace_root: str | None = None,
    hub_meta: dict[str, Any] | None = None,
) -> str:
    """Hub delege modunda tek motor bağlamı (ağır çekirdek yerine)."""
    mid = (target or "").strip().lower()
    msg = (message or "").strip()
    loaders: dict[str, tuple[str, str]] = {
        "video": ("ilim_assistant.motorlar.video_motoru", "build_motor_context"),
        "ses": ("ilim_assistant.ses_motoru", "build_motor_context"),
        "mimar": ("ilim_assistant.mimar_motoru", "build_motor_context"),
        "okuma": ("ilim_assistant.okuma_motoru", "build_motor_context"),
        "tercume": ("ilim_assistant.tercume_motoru", "build_motor_context"),
        "hafiza": ("ilim_assistant.motorlar.hafiza_motoru", "build_motor_context"),
        "hizir": ("ilim_assistant.hizir.tool_bridge", "build_dynamic_operasyon_context"),
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
            ctx = str(fn(msg, workspace_root=workspace_root) or "").strip()
            try:
                from ilim_assistant.motorlar.programlama_faz79 import (
                    format_handoff_context_block,
                )

                handoff = format_handoff_context_block(
                    msg,
                    workspace_root,
                    hub_meta=hub_meta,
                )
                if handoff:
                    ctx = (
                        f"[HUB → PROGRAMLAMA — Handoff v3]\n{handoff}\n\n---\n{ctx}"
                    ).strip()
            except Exception:
                pass
            return ctx
        if mid == "hizir":
            return str(fn(msg, mode_norm="hizir") or "").strip()
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

    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(message):
            out["hub_meta"] = {"reason": "casual_social", "winner": "genel"}
            return out
    except Exception:
        pass

    instant = maybe_hub_instant(message, motor_flags=flags, workspace_root=workspace_root)
    if instant:
        target, meta = resolve_hub_target(message, flags, workspace_root=workspace_root)
        hm = dict(meta or {})
        hm["instant"] = True
        if target and target != "genel":
            hm["target"] = target
        out["og_direct"] = instant
        out["hub_meta"] = hm
        return out

    target, meta = resolve_hub_target(message, flags)
    out["hub_meta"] = meta
    if target != "genel":
        try:
            from ilim_assistant.ana_motor_backend_yurut import try_backend_before_delegate

            be = try_backend_before_delegate(
                message, target, workspace_root=workspace_root
            )
            if be.get("handled") and be.get("reply"):
                reply = str(be["reply"])
                try:
                    from ilim_assistant.ruzgar_orkestrasyon_faz_c import polish_motor_reply

                    reply = polish_motor_reply(
                        reply,
                        target=target,
                        channel=str((be.get("meta") or {}).get("channel") or ""),
                    )
                except Exception:
                    pass
                out["og_direct"] = reply
                out["hub_meta"] = {
                    **meta,
                    "backend_yurut": True,
                    "channel": (be.get("meta") or {}).get("channel"),
                    "target": target,
                }
                return out
        except Exception:
            pass
        out["mode"] = target
        out["hub_directive"] = hub_directive_for_mode(target, meta, message)
    return out


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["ana_motor_hub_faz76"] = faz76_enabled()
    try:
        from ilim_assistant.ruzgar_genel_faz90 import enrich_health_build as _e90

        out = _e90(out)
    except Exception:
        pass
    return out
