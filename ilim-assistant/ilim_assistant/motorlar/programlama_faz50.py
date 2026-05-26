# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 50: Doğal dil → proje üret köprüsü.

«Şu özelliklere sahip site yap», «bana bir API yap» → ProjeUretSpec (Faz 47 pipeline).
Ana Motor genel modda otomatik programlama delege (faz10 ile).
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ilim_assistant.motorlar.programlama_faz47 import ProjeUretSpec

FAZ50_VERSION = "programlama-faz50-v1-2026-05-26"


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ50", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz50_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def extract_features_list(text: str) -> list[str]:
    """Özellik listesi: «özellikleri: login, crud» veya madde işaretli satırlar."""
    raw = (text or "").strip()
    if not raw:
        return []
    out: list[str] = []
    seen: set[str] = set()

    def add(part: str) -> None:
        p = part.strip().strip("-•*").strip()
        if len(p) < 2 or len(p) > 120:
            return
        key = _ascii_fold(p)
        if key in seen:
            return
        seen.add(key)
        out.append(p)

    for m in re.finditer(
        r"(?:özellikler(?:i)?|ozellikler(?:i)?)\s*[:\-–]\s*(.+?)(?:\n\n|$)",
        raw,
        re.I | re.S,
    ):
        chunk = m.group(1).strip()
        for piece in re.split(r"[,;•\n]+", chunk):
            add(piece)

    for m in re.finditer(
        r"(?:şu|su)\s+özellikler(?:e)?\s+sahip\s*[:\-]?\s*(.+?)(?:\s+(?:bir|html|web|site|api|uygulama)\b|$)",
        raw,
        re.I | re.S,
    ):
        chunk = m.group(1).strip()
        for piece in re.split(r"[,;•\n]+", chunk):
            add(piece)

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith(("-", "•", "*")) and len(line) > 3:
            add(line[1:])

    return out[:12]


def merge_goal_with_features(goal: str, features: list[str]) -> str:
    base = (goal or "").strip()
    if not features:
        return base
    feat_block = "Özellikler: " + "; ".join(features)
    if feat_block.lower() in base.lower():
        return base
    if base:
        return f"{base}\n{feat_block}"
    return feat_block


def _default_slug(prefix: str = "proje") -> str:
    return f"{prefix}-{int(time.time()) % 100000}"


def _slug_after_build_verb(text: str) -> str | None:
    """«… yap dukkan-vitrin» — yapdıktan sonraki proje adı."""
    m = re.search(
        r"(?:yap|oluştur|olustur|üret|uret|hazırla|hazirla|kur)\s+"
        r"([\w][\w.\-]{1,46})\s*$",
        (text or "").strip(),
        re.I,
    )
    if not m:
        return None
    slug = m.group(1).strip()
    if _ascii_fold(slug) in ("su", "sü", "şu", "bir", "bana", "benim"):
        return None
    return slug


def _resolve_project_name(text: str, *, default_prefix: str = "proje") -> str:
    return (
        _slug_after_build_verb(text)
        or _extract_project_slug_faz50(text)
        or _default_slug(default_prefix)
    )


def _extract_project_slug_faz50(text: str) -> str | None:
    from ilim_assistant.motorlar.programlama_faz47 import _extract_project_slug

    skip = {"su", "sü", "şu", "bir", "bana", "benim", "html", "web", "site", "sitesi"}
    slug = _extract_project_slug(text)
    if slug and _ascii_fold(slug) not in skip:
        return slug
    for w in re.findall(r"[\w][\w.\-]{1,46}", text or ""):
        if _ascii_fold(w) not in skip and len(w) >= 3:
            return w.strip()
    return None


def parse_faz50_proje_uret(message: str) -> "ProjeUretSpec | None":
    """Doğal cümle → ProjeUretSpec (Faz 47 komutundan önce dene)."""
    if not _enabled():
        return None
    from ilim_assistant.motorlar.programlama_faz47 import (
        ProjeUretSpec,
        _extract_project_slug,
        _goal_from_remainder,
        infer_template_from_text,
        proje_uret_enabled,
    )

    if not proje_uret_enabled():
        return None
    raw = (message or "").strip()
    if len(raw) < 8:
        return None
    low = _ascii_fold(raw)
    features = extract_features_list(raw)

    def _spec(tid: str, name: str, goal_raw: str) -> ProjeUretSpec:
        goal = merge_goal_with_features(
            _goal_from_remainder(goal_raw, name, tid),
            features,
        )
        return ProjeUretSpec(
            template_id=tid,
            project_name=name,
            goal=goal,
            source="faz50",
        )

    # «şu özelliklere sahip … site/api … yap»
    m_feat = re.search(
        r"(?:şu|su)\s+(?:özellikler|ozellikler)(?:e)?\s+sahip\s+(.+?)\s+"
        r"(?:bir\s+)?(.+?)\s+(?:yap|oluştur|olustur|üret|uret|hazırla|hazirla)\s*"
        r"([\w.\-]+)?\s*(.*)$",
        raw,
        re.I | re.S,
    )
    if m_feat:
        feat_txt = m_feat.group(1).strip()
        body = m_feat.group(2).strip()
        name = (m_feat.group(3) or "").strip() or _resolve_project_name(
            raw, default_prefix="site"
        )
        tail = (m_feat.group(4) or "").strip()
        if feat_txt and not features:
            for piece in re.split(r"[,;]+", feat_txt):
                if piece.strip():
                    features.append(piece.strip())
        tid = infer_template_from_text(body + " " + raw)
        if not name:
            name = _default_slug("site" if tid == "static_site" else "app")
        goal_raw = tail or feat_txt or body
        return _spec(tid, name, goal_raw)

    site_cues = (
        r"(?:bana\s+)?(?:bir\s+)?(?:html\s+)?(?:web\s+)?(?:sitesi|site|vitrin|landing|sayfa)\s+"
        r"(?:yap|oluştur|olustur|üret|uret|hazırla|hazirla|kur)",
        r"(?:yap|oluştur|olustur|üret|uret)\s+(?:bana\s+)?(?:bir\s+)?(?:html\s+)?(?:web\s+)?(?:sitesi|site)",
    )
    if any(re.search(p, low) for p in site_cues):
        name = _resolve_project_name(raw, default_prefix="site")
        return _spec("static_site", name, raw)

    api_cues = (
        r"(?:bana\s+)?(?:bir\s+)?(?:fastapi\s+)?(?:api|rest\s+api)\s+"
        r"(?:yap|oluştur|olustur|üret|uret|hazırla|hazirla)",
        r"(?:yap|oluştur|olustur|üret|uret)\s+(?:bana\s+)?(?:bir\s+)?(?:fastapi\s+)?api\b",
    )
    if any(re.search(p, low) for p in api_cues):
        name = _resolve_project_name(raw, default_prefix="api")
        return _spec("fastapi_api", name, raw)

    app_cues = (
        r"(?:bana\s+)?(?:bir\s+)?(?:react\s+)?(?:uygulama|app|mobil\s+uygulama)\s+"
        r"(?:yap|oluştur|olustur|üret|uret)",
    )
    if any(re.search(p, low) for p in app_cues):
        tid = infer_template_from_text(raw)
        name = _resolve_project_name(raw, default_prefix="app")
        return _spec(tid, name, raw)

    if features and re.search(r"\b(yap|olustur|uret|üret|hazirla)\b", low):
        tid = infer_template_from_text(raw)
        name = _resolve_project_name(raw, default_prefix="proje")
        return _spec(tid, name, raw)

    return None


def should_delegate_proje_uret_from_genel(
    message: str,
    mode_norm: str = "genel",
) -> bool:
    """Ana Motor → Programlama: proje üret niyeti."""
    if not _enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim", ""):
        return False
    if parse_faz50_proje_uret(message):
        return True
    try:
        from ilim_assistant.motorlar.programlama_faz47 import parse_proje_uret_command

        if parse_proje_uret_command(message):
            return True
    except Exception:
        pass
    low = _ascii_fold(message)
    if len(low) < 10:
        return False
    if "@@write" in low or "@@read" in low or "traceback" in low:
        return False
    build = re.search(
        r"\b(yap|olustur|uret|üret|hazirla|hazırla|kur|olustur)\b",
        low,
    )
    if not build:
        return False
    cues = (
        "site yap",
        "sitesi yap",
        "web sitesi",
        "html site",
        "vitrin",
        "landing",
        "uygulama yap",
        "app yap",
        "proje uret",
        "proje üret",
        "ozellikler",
        "özellikler",
        "sifirdan",
        "sıfırdan",
        "bagimsiz proje",
        "bağımsız proje",
        "fastapi",
        "react",
    )
    return any(c in low for c in cues)


def faz50_directive() -> str:
    return (
        "[FAZ 50 — doğal dil proje üret]\n"
        "«Şu özelliklere sahip site yap», «bana API yap» → proje üret pipeline.\n"
        "Özellik listesi hedef metne eklenir; özel özellikte ajan devreye girer.\n"
    )
