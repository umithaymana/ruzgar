# Created by Ümit & Gökçenur
"""
Hafıza motoru — Faz 75: ROK pilot (U6) — konuşarak yap.

Hatırla / unut / profil · görev · hatırlatıcı · hafıza durumu · genel sözlük bakışı.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.ruzgar_motor_kernel import (
    INTENT_CHAT,
    INTENT_COMMAND,
    INTENT_DO,
    register_classifier,
)

FAZ75_VERSION = "hafiza-faz75-v1-2026-05-26"

_QUESTION_RE = re.compile(
    r"(?:\b(?:nedir|nasıl|nasil|ne\s+demek)\b|^(?:açıkla|acikla|anlat)\b)",
    re.I,
)
_STATUS_RE = re.compile(
    r"(?:haf[ıi]za\s+(?:durum|ozet|özet|istatistik)|hafiza\s+durum|"
    r"ne\s+kay[ıi]tl[ıi]|kayit\s+say)",
    re.I,
)
_HELP_RE = re.compile(
    r"(?:haf[ıi]za\s+komut|hafiza\s+komut|neler\s+hat[ıi]rl|komut\s+listesi)",
    re.I,
)
_REMEMBER_RE = re.compile(
    r"(?:hat[ıi]rla|haf[ıi]zaya\s+al|kaydet|not\s+al|profil|"
    r"(?:sana\s+)?(?:öğretiyorum|ogretiyorum|öğret(?:iyorum)?))",
    re.I,
)
_FORGET_RE = re.compile(r"(?:\bunut\b|haf[ıi]zadan\s+sil)", re.I)
_TASK_RE = re.compile(r"(?:görev|gorev)", re.I)
_REMINDER_RE = re.compile(r"(?:hat[ıi]rlat|reminder|alarm)", re.I)
_LOOKUP_RE = re.compile(
    r"(?:genel\s+bak|haf[ıi]zada\s+ara|ne\s+biliyorsun|bunu\s+biliyor\s+musun)",
    re.I,
)

_REGISTERED = False


def _enabled() -> bool:
    return os.environ.get("RUZGAR_HAFIZA_FAZ75", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz75_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def ensure_kernel_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register_classifier("hafiza", classify_hafiza_intent)
    _REGISTERED = True


def _looks_like_miss(ans: str) -> bool:
    if not ans or not str(ans).strip():
        return True
    a = unicodedata.normalize("NFKC", str(ans).strip()).lower()
    if "öğrenmedim" in a or "ogrenmedim" in a:
        return "mimar" in a or "öğretir" in a or "ogretir" in a
    return False


def _footer(reply: str) -> str:
    body = (reply or "").strip()
    if FAZ75_VERSION in body:
        return body
    return f"{body}\n({FAZ75_VERSION})"


def classify_hafiza_intent(
    message: str,
    *,
    mode_norm: str = "hafiza",
    **kwargs: Any,
) -> dict[str, Any]:
    _ = kwargs
    if mode_norm != "hafiza":
        return {"intent": INTENT_CHAT, "reason": "wrong_mode"}
    raw = (message or "").strip()
    if not raw:
        return {"intent": INTENT_CHAT, "reason": "empty"}
    low = _ascii_fold(raw)

    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(raw):
            return {"intent": INTENT_CHAT, "reason": "casual_social"}
    except Exception:
        pass

    if _STATUS_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "status"}
    if _HELP_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "help"}

    if _FORGET_RE.search(low):
        return {"intent": INTENT_DO, "reason": "forget"}
    if _REMEMBER_RE.search(low):
        return {"intent": INTENT_DO, "reason": "remember"}
    if _TASK_RE.search(low):
        return {"intent": INTENT_DO, "reason": "task"}
    if _REMINDER_RE.search(low):
        return {"intent": INTENT_DO, "reason": "reminder"}
    if _LOOKUP_RE.search(low) or (
        len(raw) < 120 and "?" in raw and not _REMEMBER_RE.search(low)
    ):
        return {"intent": INTENT_DO, "reason": "lookup"}

    if _QUESTION_RE.search(raw):
        return {"intent": INTENT_CHAT, "reason": "question"}

    return {"intent": INTENT_CHAT, "reason": "conversation"}


def format_hafiza_status() -> str:
    lines = [
        "Ümit abi, **hafıza motoru durumu:**",
        "",
    ]
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        motor = get_hafiza_motor()
        all_items = motor.tum_bilgiler()
        hafiza_items = motor.tum_bilgiler(motor_tipi="Hafıza")
        lines.append(f"· Genel sözlük kayıt: **{len(all_items)}**")
        lines.append(f"· Kişisel (Hafıza etiketi): **{len(hafiza_items)}**")
    except Exception as exc:
        lines.append(f"· Sözlük okunamadı: {exc}")

    try:
        root = Path(__file__).resolve().parents[2]
        gh = root / "ruzgar_genel_hafiza.json"
        if gh.is_file():
            lines.append(f"· `ruzgar_genel_hafiza.json`: {gh.stat().st_size // 1024} KB")
    except Exception:
        pass

    try:
        from ilim_assistant.gorev_yoneticisi import list_tasks

        tasks = list_tasks(80)
        pending = sum(1 for t in tasks if (t.get("status") or "") == "pending")
        lines.append(f"· Görevler: **{len(tasks)}** (bekleyen {pending})")
    except Exception as exc:
        lines.append(f"· Görevler: okunamadı ({exc})")

    try:
        from ilim_assistant.dinamit_hatirlatici import fetch_due_reminders

        due = fetch_due_reminders()
        lines.append(f"· Tetiklenmeyi bekleyen hatırlatıcı: **{len(due)}**")
    except Exception:
        lines.append("· Hatırlatıcı: (servis yok)")

    lines.extend(
        [
            "",
            "Komutlar: `hatırla: …` · `unut: …` · `görev oluştur: …` · `görev listesi`",
            "· `yarın saat 10'da hatırlat: …`",
        ]
    )
    return _footer("\n".join(lines))


def format_help() -> str:
    return _footer(
        "Ümit abi, **hafıza motoru — konuşarak komutlar:**\n\n"
        "· `hatırla: …` / `bunu hatırla: …` — kişisel not\n"
        "· `unut: …` — kayıt sil\n"
        "· `profilimi göster` — kişisel notlar\n"
        "· `görev oluştur: …` · `görev listesi`\n"
        "· `5 dakika sonra hatırlat: …`\n"
        "· `hafıza durumu` — özet\n"
        "· Kısa soru — genel sözlükte arama (ör. «X nedir?»)\n"
        "· `sana öğretiyorum …` veya `hatırla: soru = cevap`\n"
    )


def try_lookup(message: str) -> str | None:
    """
    Genel sözlük araması — kullanıcıya anında şablon döndürmez.
    Isabet/kaçırma LLM + doğal sentez boru hattına bırakılır (hafiza_dogal_sentez).
    Eski anında lookup: RUZGAR_HAFIZA_INSTANT_LOOKUP=1 (yalnızca hata ayıklama).
    """
    if os.environ.get("RUZGAR_HAFIZA_INSTANT_LOOKUP", "0").strip().lower() not in (
        "1",
        "true",
        "yes",
    ):
        return None
    from ilim_assistant.hafiza_i_ruzgar import genel_hafiza_lookup

    q = (message or "").strip()
    if len(q) < 3:
        return None
    ans = genel_hafiza_lookup(q)
    if not ans or _looks_like_miss(ans):
        return None
    return _footer(str(ans).strip())


def _delegate_commands(message: str) -> str | None:
    for importer in (
        ("ilim_assistant.kisisel_hafiza", "try_consume_memory_command"),
        ("ilim_assistant.gorev_yoneticisi", "try_consume_task_command"),
        ("ilim_assistant.dinamit_hatirlatici", "try_consume_hatirlatici_intent"),
    ):
        try:
            mod = __import__(importer[0], fromlist=[importer[1]])
            fn = getattr(mod, importer[1])
            reply = fn(message)
            if reply:
                return _footer(reply.replace("Mimar", "Ümit abi", 1))
        except Exception:
            continue
    return None


def maybe_instant_faz75(
    message: str,
    *,
    mode_norm: str = "hafiza",
    allow_lookup: bool = False,
) -> str | None:
    if not _enabled():
        return None
    ensure_kernel_registered()
    raw = (message or "").strip()
    if not raw:
        return None

    mode = (mode_norm or "hafiza").strip().lower()
    intent = classify_hafiza_intent(raw, mode_norm=mode)
    reason = intent.get("reason") or ""

    if mode == "hafiza" and intent.get("intent") == INTENT_COMMAND:
        if reason == "status":
            return format_hafiza_status()
        if reason == "help":
            return format_help()

    delegated = _delegate_commands(raw)
    if delegated:
        return delegated

    return None


def maybe_instant_faz75_hub(message: str) -> str | None:
    """Ana Motor hub — komut/öğretme evet; genel soru lookup hayır (LLM'e bırak)."""
    return maybe_instant_faz75(message, mode_norm="hafiza", allow_lookup=False)


def augment_hafiza_context(base: str) -> str:
    if not _enabled():
        return base
    ensure_kernel_registered()
    extra = (
        "\n[HAFIZA ROK — Faz 75]\n"
        "Konuşarak: hatırla · unut · görev · hatırlatıcı · hafıza durumu\n"
        "Kapat: RUZGAR_HAFIZA_FAZ75=0\n"
    )
    return (base or "").rstrip() + extra


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["hafiza_faz75"] = faz75_enabled()
    return out


def faz75_directive() -> str:
    return (
        "[HAFIZA — Konuşarak yap Faz 75]\n"
        "Örnek: `hatırla: X = Y` · `görev listesi` · `hafıza durumu`\n"
        "Kapat: RUZGAR_HAFIZA_FAZ75=0\n"
    )


ensure_kernel_registered()
