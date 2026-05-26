# Created by Ümit & Gökçenur
"""
Okuma motoru — Faz 73: ROK pilot (U4) — konuşarak yap.

Arşiv özeti · metin türü (hadis/gazel/tasavvuf) · Kur'an/Mektubat kaynak ipucu.
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

FAZ73_VERSION = "okuma-faz73-v1-2026-05-26"

_QUESTION_RE = re.compile(
    r"(?:\b(?:nedir|nasıl|nasil|ne\s+demek)\b|^(?:açıkla|acikla|anlat)\b)",
    re.I,
)
_ARSIV_RE = re.compile(
    r"(?:arsiv\s+(?:durum|ozet|özet|liste|klasor|klasör|ne\s+var)|"
    r"ilim\s+hazinesi|kultur\s+hazinesi|külliyat|kulliyat)",
    re.I,
)
_INDEX_RE = re.compile(
    r"(?:index\s+durum|indeks\s+durum|jsonl\s+durum|arsiv\s+index)",
    re.I,
)
_CATEGORIZE_RE = re.compile(
    r"(?:hadis\s+mi|gazel\s+mi|tasavvuf|metin\s+tür|metin\s+tur|tür\s+analiz|"
    r"tur\s+analiz|kategorize|siniflandir|sınıflandır|bu\s+metin)",
    re.I,
)
_SOURCE_RE = re.compile(
    r"(?:kaynak\s+bul|sure\s+ayet|hangi\s+ayet|hangi\s+mektup|mektup\s+no|"
    r"kuran\s+ipucu|mektubat\s+ipucu)",
    re.I,
)
_ANALYZE_PREFIX_RE = re.compile(
    r"(?:analiz|kategorize|türünü|turunu)\s*[:：]\s*(.+)$",
    re.I | re.DOTALL,
)

_REGISTERED = False
_DOC_EXTS = {".pdf", ".txt", ".md", ".jsonl"}


def _enabled() -> bool:
    return os.environ.get("RUZGAR_OKUMA_FAZ73", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz73_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def ensure_kernel_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register_classifier("okuma", classify_okuma_intent)
    _REGISTERED = True


def extract_analysis_text(message: str) -> str:
    raw = (message or "").strip()
    m = _ANALYZE_PREFIX_RE.search(raw)
    if m:
        return m.group(1).strip()
    if len(raw) >= 72:
        return raw
    return ""


def classify_okuma_intent(
    message: str,
    *,
    mode_norm: str = "okuma",
    **kwargs: Any,
) -> dict[str, Any]:
    _ = kwargs
    if mode_norm != "okuma":
        return {"intent": INTENT_CHAT, "reason": "wrong_mode"}
    raw = (message or "").strip()
    if not raw:
        return {"intent": INTENT_CHAT, "reason": "empty"}
    low = _ascii_fold(raw)

    if _ARSIV_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "arsiv_status"}
    if _INDEX_RE.search(low):
        return {"intent": INTENT_COMMAND, "reason": "index_status"}

    if _SOURCE_RE.search(low):
        return {"intent": INTENT_DO, "reason": "source_lookup"}

    body = extract_analysis_text(raw)
    if _CATEGORIZE_RE.search(low) or (body and len(body) >= 40):
        return {
            "intent": INTENT_DO,
            "reason": "categorize_text",
            "text": body or raw,
        }

    if _QUESTION_RE.search(raw) and not _CATEGORIZE_RE.search(low):
        return {"intent": INTENT_CHAT, "reason": "question"}

    if len(raw) >= 120:
        return {"intent": INTENT_DO, "reason": "categorize_text", "text": raw}

    return {"intent": INTENT_CHAT, "reason": "conversation"}


def _count_docs(root: Path) -> tuple[int, int]:
    """(dosya sayısı, jsonl satır sayısı yaklaşık)"""
    if not root.is_dir():
        return 0, 0
    files = 0
    jsonl_lines = 0
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf in _DOC_EXTS:
            files += 1
        if p.name == "index.jsonl":
            try:
                jsonl_lines += sum(
                    1
                    for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines()
                    if ln.strip()
                )
            except Exception:
                pass
    return files, jsonl_lines


def format_arsiv_status() -> str:
    from ilim_assistant.okuma_motoru import (
        _ARSIV,
        _KURAN,
        _LEGACY_KURAN,
        _LEGACY_MEKTUBAT,
        _MEKTUBAT,
        _read_jsonl,
    )

    kulliyat = [
        "Tasavvuf_Kulliyati",
        "Hadis_Kulliyati",
        "Klasik_Turk_Edebiyati",
        "Tarih_ve_Kultur",
    ]
    lines = [
        "Ümit abi, **Kültür ve İlim Hazinesi** arşiv özeti:",
        "",
    ]
    total_files = 0
    for name in kulliyat:
        root = _ARSIV / name
        n, jl = _count_docs(root)
        total_files += n
        lines.append(f"· **{name}** — {n} dosya · index satırı ~{jl}")
    kuran_n = len(_read_jsonl(_KURAN / "index.jsonl")) + len(
        _read_jsonl(_LEGACY_KURAN / "index.jsonl")
    )
    mekt_n = len(_read_jsonl(_MEKTUBAT / "index.jsonl")) + len(
        _read_jsonl(_LEGACY_MEKTUBAT / "index.jsonl")
    )
    lines.extend(
        [
            "",
            f"Kur'an index.jsonl: **{kuran_n}** satır · Mektubat: **{mekt_n}** satır",
            f"Kök: `{_ARSIV.as_posix()}`",
            "",
            "PDF/TXT ekledikten sonra: `python -m ilim_assistant.arsiv_indexle`",
            f"({FAZ73_VERSION})",
        ]
    )
    return "\n".join(lines)


def format_index_status() -> str:
    from ilim_assistant.okuma_motoru import (
        _KURAN,
        _LEGACY_KURAN,
        _LEGACY_MEKTUBAT,
        _MEKTUBAT,
        _read_jsonl,
    )

    paths = [
        ("Kuran_i_Kerim", _KURAN / "index.jsonl"),
        ("Mektubat_i_Rabbani", _MEKTUBAT / "index.jsonl"),
        ("kuran (legacy)", _LEGACY_KURAN / "index.jsonl"),
        ("mektubat (legacy)", _LEGACY_MEKTUBAT / "index.jsonl"),
    ]
    lines = ["Ümit abi, **arsiv index.jsonl** durumu:", ""]
    for label, p in paths:
        if p.is_file():
            n = len(_read_jsonl(p))
            lines.append(f"· {label}: **{n}** satır — `{p.name}`")
        else:
            lines.append(f"· {label}: (dosya yok)")
    lines.append(f"\n({FAZ73_VERSION})")
    return "\n".join(lines)


def format_categorize(text: str) -> str:
    from ilim_assistant.okuma_motoru import kategorize_metin_parcastipi

    body = (text or "").strip()
    if len(body) < 24:
        return (
            "Ümit abi, metin türü için en az bir paragraf yapıştırın.\n"
            "Örnek: `bu metin hadis mi:` + rivayet metni\n"
            f"({FAZ73_VERSION})"
        )
    kod, acik = kategorize_metin_parcastipi(body)
    etiket = {
        "hadis": "Hadis / rivayet",
        "gazel": "Gazel / nazım",
        "tasavvufi_aciklama": "Tasavvufî düzyazı",
        "belirsiz": "Belirsiz",
    }.get(kod, kod)
    preview = body if len(body) <= 180 else f"{body[:180]}…"
    return (
        f"Ümit abi, metin türü tahmini: **{etiket}**\n\n"
        f"{acik}\n\n"
        f"Önizleme: {preview}\n"
        f"({FAZ73_VERSION})"
    )


def format_source_lookup(message: str) -> str:
    from ilim_assistant.okuma_motoru import (
        _KURAN,
        _LEGACY_KURAN,
        _LEGACY_MEKTUBAT,
        _MEKTUBAT,
        _best_match,
        _infer_source,
        _read_jsonl,
    )

    prompt = (message or "").strip()
    source = _infer_source(prompt)
    kuran_rows = _read_jsonl(_KURAN / "index.jsonl") + _read_jsonl(
        _LEGACY_KURAN / "index.jsonl"
    )
    mektubat_rows = _read_jsonl(_MEKTUBAT / "index.jsonl") + _read_jsonl(
        _LEGACY_MEKTUBAT / "index.jsonl"
    )
    k = _best_match(prompt, kuran_rows, "kuran")
    m = _best_match(prompt, mektubat_rows, "mektubat")

    lines = [
        "Ümit abi, **kaynak ipucu** (index.jsonl eşleşmesi):",
        "",
        f"· Sınıf: **{source}**",
    ]
    if k:
        lines.append(f"· Kur'an: Sure/Ayet **{k[1]}** (skor {k[0]:.2f})")
    if m:
        lines.append(f"· Mektubat: **{m[1]}** (skor {m[0]:.2f})")
    if not k and not m:
        lines.append(
            "· Kesin eşleşme yok — metni genişletin veya `python -m ilim_assistant.arsiv_indexle`"
        )
    lines.append(f"\n({FAZ73_VERSION})")
    return "\n".join(lines)


def maybe_instant_faz73(message: str) -> str | None:
    if not _enabled():
        return None
    ensure_kernel_registered()
    raw = (message or "").strip()
    if not raw:
        return None

    intent = classify_okuma_intent(raw, mode_norm="okuma")
    reason = intent.get("reason") or ""

    if intent.get("intent") == INTENT_COMMAND:
        if reason == "arsiv_status":
            return format_arsiv_status()
        if reason == "index_status":
            return format_index_status()

    if intent.get("intent") == INTENT_DO:
        if reason == "source_lookup":
            return format_source_lookup(raw)
        if reason == "categorize_text":
            txt = intent.get("text") or extract_analysis_text(raw) or raw
            return format_categorize(txt)

    low = _ascii_fold(raw)
    if low.startswith("arsiv:") or low.startswith("okuma:"):
        rest = raw.split(":", 1)[-1].strip()
        if rest:
            return format_categorize(rest)

    return None


def augment_okuma_context(base: str) -> str:
    if not _enabled():
        return base
    ensure_kernel_registered()
    extra = (
        "\n[OKUMA ROK — Faz 73]\n"
        "Konuşarak: «arsiv durumu» · «index durumu» · metin yapıştır + «hadis mi» · «kaynak bul»\n"
        "Kapat: RUZGAR_OKUMA_FAZ73=0\n"
    )
    return (base or "").rstrip() + extra


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["okuma_faz73"] = faz73_enabled()
    return out


def faz73_directive() -> str:
    return (
        "[OKUMA — Konuşarak yap Faz 73]\n"
        "Örnek: `arsiv durumu` · `index durumu` · uzun metin + `bu metin hadis mi`\n"
        "Kapat: RUZGAR_OKUMA_FAZ73=0\n"
    )


ensure_kernel_registered()
