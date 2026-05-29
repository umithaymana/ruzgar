from __future__ import annotations

import re
from typing import Any

FAZ92_VERSION = "programlama-faz92-v1-2026-05-27"


def _sentences(text: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip())
    out = [x.strip(" -\t\r\n") for x in raw if x.strip()]
    return out[:8]


def _extract_acceptance(text: str) -> list[str]:
    low = (text or "").lower()
    checks: list[str] = []
    if any(x in low for x in ("test", "pytest", "unit test", "coverage")):
        checks.append("İlgili testler çalışmalı ve kritik test kırılmamalı.")
    if any(x in low for x in ("hata", "bug", "fix", "düzelt", "duzelt")):
        checks.append("Tarif edilen hata tekrar etmemeli.")
    if any(x in low for x in ("refactor", "temizle", "iyileştir", "iyilestir")):
        checks.append("Davranış korunurken kod okunabilirliği artmalı.")
    if any(x in low for x in ("performans", "hız", "latency", "slow")):
        checks.append("Performans metriği kötüleşmemeli.")
    if not checks:
        checks.append("Değişiklik kullanıcı isteğini doğrudan karşılamalı.")
    return checks[:3]


def build_task_plan(message: str) -> dict[str, Any]:
    msg = (message or "").strip()
    if not msg:
        return {
            "version": FAZ92_VERSION,
            "goal": "",
            "steps": [],
            "acceptance": [],
        }
    try:
        from ilim_assistant.motorlar.programlama_faz101_report_read import wants_report_read

        if wants_report_read(msg):
            return {
                "version": FAZ92_VERSION,
                "goal": "Bench/KPI raporunu oku ve Türkçe özetle (kod değişikliği yok)",
                "steps": [
                    "İlgili JSON rapor dosyasını bul ve oku.",
                    "Skorları ve geçen/kalan maddeleri kısa özetle.",
                ],
                "acceptance": [
                    "Kullanıcıya rapor özeti verilir; otomatik pytest/smoke tetiklenmez.",
                ],
            }
    except Exception:
        pass
    sents = _sentences(msg)
    goal = sents[0][:220] if sents else msg[:220]
    steps: list[str] = []
    for s in sents[1:4]:
        if len(s) >= 6:
            steps.append(s[:180])
    if not steps:
        steps = [
            "İlgili dosya ve akışı tespit et.",
            "İsteğe uygun en küçük güvenli değişikliği uygula.",
            "Test/lint ile doğrula ve sonucu özetle.",
        ]
    return {
        "version": FAZ92_VERSION,
        "goal": goal,
        "steps": steps[:4],
        "acceptance": _extract_acceptance(msg),
    }


def render_plan_directive(plan: dict[str, Any]) -> str:
    goal = str(plan.get("goal") or "").strip()
    steps = [str(x).strip() for x in (plan.get("steps") or []) if str(x).strip()]
    acceptance = [
        str(x).strip() for x in (plan.get("acceptance") or []) if str(x).strip()
    ]
    lines = ["[PROGRAMLAMA GOREV PLANI]"]
    if goal:
        lines.append(f"Amac: {goal}")
    if steps:
        lines.append("Adimlar:")
        lines.extend(f"- {s}" for s in steps[:4])
    if acceptance:
        lines.append("Kabul:")
        lines.extend(f"- {a}" for a in acceptance[:3])
    lines.append("Cevapta gereksiz aciklama yerine goreve odaklan.")
    lines.append("[/PROGRAMLAMA GOREV PLANI]")
    return "\n".join(lines)


def assess_risk(message: str) -> dict[str, Any]:
    raw = (message or "").strip()
    low = raw.lower()
    risky_terms = (
        "delete",
        "sil",
        "drop table",
        "truncate",
        "reset",
        "hard reset",
        "force push",
        "rm -rf",
        "production",
        "canlıya al",
        "canliya al",
        "migrate",
        "migration",
    )
    risky_hits = [x for x in risky_terms if x in low]
    confirmed = any(
        x in low
        for x in (
            "onayli",
            "onaylı",
            "eminim",
            "devam et onayli",
            "riskini kabul ediyorum",
        )
    )
    level = "high" if risky_hits else "low"
    return {
        "version": FAZ92_VERSION,
        "level": level,
        "hits": risky_hits[:6],
        "requires_confirmation": bool(risky_hits) and not confirmed,
        "confirmed": confirmed,
    }


def risk_confirmation_text(risk: dict[str, Any]) -> str:
    hits = ", ".join(risk.get("hits") or [])
    why = f" (riskli işaretler: {hits})" if hits else ""
    return (
        "Bu istek yüksek riskli görünüyor"
        f"{why}. Devam etmem için mesajı "
        "`devam et onayli` diye bitir."
    )


def should_self_heal_retry(reply_text: str, *, mode_norm: str) -> bool:
    if (mode_norm or "").strip().lower() != "programlama":
        return False
    low = (reply_text or "").strip().lower()
    if not low:
        return False
    transient_hit = any(
        x in low
        for x in (
            "programlama motoru şu an yanıt üretemedi",
            "programlama motoru su an yanit uretemedi",
            "rate limit",
            "429",
            "gemini kotası dolu",
            "gemini kotasi dolu",
            "timeout",
            "timed out",
            "connection reset",
            "service unavailable",
            "bad gateway",
        )
    )
    too_short_errorish = len(low) < 20 and any(
        x in low for x in ("hata", "error", "yok", "failed", "bos", "empty")
    )
    return transient_hit or too_short_errorish


def self_heal_retry_prompt(user_message: str, last_reply: str) -> str:
    return (
        "[PROGRAMLAMA SELF-HEAL RETRY]\n"
        "Önceki deneme başarısız/eksik kaldı. Aynı görevi yeniden dene.\n"
        "- Kısa, net ve uygulanabilir yanıt ver.\n"
        "- Gerekirse yerel kod/denge yaklaşımıyla ilerle.\n"
        "- Geçici kota/bağlantı hatasını kullanıcıya yansıtmadan çözüm odaklı devam et.\n\n"
        f"[Kullanıcı isteği]\n{(user_message or '').strip()[:1200]}\n\n"
        f"[Önceki başarısız yanıt]\n{(last_reply or '').strip()[:1400]}"
    )


def needs_refactor_scope_clarification(message: str) -> bool:
    raw = (message or "").strip().lower()
    if not raw:
        return False
    broad_terms = (
        "tüm proje",
        "tum proje",
        "her yerde",
        "komple",
        "bastan yaz",
        "baştan yaz",
        "büyük refactor",
        "buyuk refactor",
        "genel refactor",
        "across repo",
        "whole codebase",
    )
    if not any(t in raw for t in broad_terms):
        return False
    # Kullanıcı kapsamı zaten belirttiyse tekrar sorma.
    if any(x in raw for x in ("sadece ", "yalnızca ", "yalnizca ", "dosya:", "klasör:", "folder:")):
        return False
    return True


def refactor_scope_question() -> str:
    return (
        "Bu istek çok dosyalı/büyük refactor görünüyor. Hata riskini azaltmak için "
        "kapsamı netleştirir misin: hangi klasör/dosyalarla sınırlayayım?"
    )

