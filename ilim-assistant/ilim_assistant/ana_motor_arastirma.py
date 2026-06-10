# Created by Ümit & Gökçenur
"""Ana Motor Faz C / 9.1 — birleşik araştırma raporu (yerel + web envanter)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any


def arastirma_report_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_ARASTIRMA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(getattr(question_plan, "primary", "") or "").strip().lower()
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return ""


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _excerpt(text: str, cap: int) -> str:
    body = (text or "").strip().replace("\r\n", "\n")
    if len(body) <= cap:
        return body
    return body[: cap - 20].rstrip() + "\n… [kısaltıldı]"


def should_build_research_report(
    *,
    question_plan: Any | None,
    hits: list[tuple[str, str, float]] | None,
    web_extra: str,
    mode_norm: str,
) -> bool:
    if not arastirma_report_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim", "okuma", "hafiza"):
        return False
    primary = _plan_primary(question_plan)
    if primary not in ("bilgi", "bilim", "dilbilgisi"):
        return False
    return bool(hits) or bool((web_extra or "").strip())


def build_unified_research_report(
    user_message: str,
    *,
    hits: list[tuple[str, str, float]] | None,
    web_extra: str,
    question_plan: Any | None = None,
    mode_norm: str = "genel",
) -> str:
    """
    Çok kaynaklı envanter raporu — ek LLM yok; ana modele bağlam kartı.
    """
    if not should_build_research_report(
        question_plan=question_plan,
        hits=hits,
        web_extra=web_extra,
        mode_norm=mode_norm,
    ):
        return ""
    try:
        y_cap = max(400, int(os.environ.get("RUZGAR_ARASTIRMA_YEREL_MAX", "720")))
    except ValueError:
        y_cap = 720
    try:
        w_cap = max(400, int(os.environ.get("RUZGAR_ARASTIRMA_WEB_MAX", "1200")))
    except ValueError:
        w_cap = 1200

    q = (user_message or "").strip()[:300]
    lines: list[str] = [
        "\n\n[BİRLEŞİK ARAŞTIRMA RAPORU — Ana Motor Faz C / 9.1 — Ümit & Gökçenur]",
        f"Soru: {q}",
        f"Tarama damgası: {_utc_stamp()}",
        "",
    ]
    n_local = len(hits or [])
    if n_local:
        lines.append(f"## Yerel kaynaklar ({n_local} parça)")
        for i, (text, src, score) in enumerate((hits or [])[:8], 1):
            label = (src or "kaynak").replace("\\", "/")
            if len(label) > 72:
                label = "…" + label[-69:]
            lines.append(f"- **[Y{i}]** `{label}` · skor {float(score):.2f}")
            ex = _excerpt(text, y_cap // max(1, min(n_local, 4)))
            if ex:
                lines.append(f"  {ex.replace(chr(10), ' ')}")
        lines.append("")
    else:
        lines.append("## Yerel kaynaklar\n- (Bu turda yerel parça bağlanmadı.)\n")

    web = (web_extra or "").strip()
    if web:
        lines.append("## Web taraması")
        lines.append(_excerpt(web, w_cap))
        lines.append("")
    else:
        lines.append("## Web taraması\n- (Web metni bağlanmadı.)\n")

    lines.append(
        "Talimat: Yanıtını bu rapordaki **[Y#]** ve web özetine dayandır; "
        "çelişki varsa belirt. Liste sorularında mümkünse **tam sıralı** ver.\n"
        "[/BİRLEŞİK ARAŞTIRMA RAPORU]\n"
    )
    return "\n".join(lines)


def maybe_build_unified_research_report(
    user_message: str,
    *,
    hits: list[tuple[str, str, float]] | None,
    web_extra: str,
    question_plan: Any | None = None,
    mode_norm: str = "genel",
) -> str:
    try:
        return build_unified_research_report(
            user_message,
            hits=hits,
            web_extra=web_extra,
            question_plan=question_plan,
            mode_norm=mode_norm,
        )
    except Exception:
        return ""
