# Created by Ümit & Gökçenur
"""Ana Motor Faz Y2 — sohbet içi kaynak + güven rozeti."""

from __future__ import annotations

import os
import re
from typing import Any

FAZ_Y_ROZET_VERSION = "ana-motor-kaynak-rozet-y2-2026-06-10"

_GUVEN_RE = re.compile(
    r"\*\*Güven:\s*(yüksek|orta|düşük|dusuk)\*\*",
    re.I,
)


def kaynak_rozet_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_KAYNAK_ROZET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def parse_guven_level(text: str) -> str:
    m = _GUVEN_RE.search(text or "")
    if not m:
        return "bilinmiyor"
    raw = m.group(1).lower().replace("dusuk", "düşük")
    return raw


def _guven_label(level: str) -> str:
    return {
        "yüksek": "Yüksek güven",
        "orta": "Orta güven",
        "düşük": "Düşük güven",
        "bilinmiyor": "Güven belirtilmedi",
    }.get(level, "Güven belirtilmedi")


def _guven_css_class(level: str) -> str:
    if level == "yüksek":
        return "trust-high"
    if level == "orta":
        return "trust-mid"
    if level == "düşük":
        return "trust-low"
    return "trust-unknown"


def _source_previews(hits: list | None, *, limit: int = 4) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(hits or [], start=1):
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        text = str(item[0] or "").strip()
        src = str(item[1] or "").strip()
        score = None
        if len(item) >= 3:
            try:
                score = float(item[2])
            except (TypeError, ValueError):
                pass
        preview = text[:120] + ("…" if len(text) > 120 else "")
        out.append(
            {
                "id": f"K{i}",
                "source": src,
                "preview": preview,
                "score": score,
            }
        )
        if len(out) >= limit:
            break
    return out


def build_source_trust_card(
    reply: str,
    user_message: str,
    *,
    hits: list | None = None,
    question_plan: Any | None = None,
    web_was_used: bool = False,
    reflection_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not kaynak_rozet_enabled():
        return {"ok": False, "disabled": True}

    body = (reply or "").strip()
    if not body:
        return {"ok": False, "error": "bos_cevap"}

    meta = reflection_meta if isinstance(reflection_meta, dict) else {}
    level = parse_guven_level(body)
    n_src = len(hits or [])
    previews = _source_previews(hits)

    primary = ""
    if question_plan is not None:
        if hasattr(question_plan, "primary"):
            primary = str(getattr(question_plan, "primary", "") or "")
        elif isinstance(question_plan, dict):
            primary = str(question_plan.get("primary") or "")

    hint_parts: list[str] = []
    if n_src:
        hint_parts.append(f"{n_src} yerel kaynak")
    if web_was_used:
        hint_parts.append("web")
    if meta.get("mismatch"):
        hint_parts.append("kaynak uyumu kontrol edildi")
    if meta.get("llm_reflection_applied"):
        hint_parts.append("LLM denetim")

    return {
        "ok": True,
        "version": FAZ_Y_ROZET_VERSION,
        "guven_level": level,
        "guven_label": _guven_label(level),
        "guven_class": _guven_css_class(level),
        "source_count": n_src,
        "sources_preview": previews,
        "web_used": bool(web_was_used),
        "plan_primary": primary,
        "hint": " · ".join(hint_parts) if hint_parts else "Genel yanıt",
        "mismatch": bool(meta.get("mismatch")),
        "reflection_note": str(meta.get("mismatch_note") or "")[:300],
    }
