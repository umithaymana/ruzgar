# Created by Ümit & Gökçenur
"""
Ana Motor — Faz E: tek yüz (sohbet → Tercüme / Video quiet handoff).

6c kalıbı: genel sohbette atölye niyetini tanır; UI'ya surface_handoff verir.
Kısa anlık çeviri (backend) ve «belgeyi tercümeye gönder» (tek_sohbet) ile çakışmaz.
Serbest kod / shell yok.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

FAZ_E_VERSION = "ana-motor-faz-e-tek-yuz-v1-2026-10-21"

_SRT_PATH_RE = re.compile(
    r"(?P<path>(?:[\w.\-]+/)*[\w.\-]+\.(?:srt|vtt))\b",
    re.I,
)
_URL_RE = re.compile(
    r"(https?://[^\s<>\"']+|www\.[^\s<>\"']+|youtu\.be/[^\s<>\"']+|"
    r"(?:youtube\.com|youtu\.be)/[^\s<>\"']+)",
    re.I,
)
_TRANSLATE_VERB_RE = re.compile(
    r"\b(?:çevir|cevir|tercüme\s*et|tercume\s*et|translate)\b",
    re.I,
)
_LANG_PAIR_RE = re.compile(
    r"(?:(?:den|dan)\s+)?(?P<source>türkçe|turkce|ingilizce|english|arapça|arapca|"
    r"almanca|fransızca|fransizca|farsça|farsca|osmanlıca|osmanlica)"
    r"\s*(?:[-–—]|den|dan|to|->|→)?\s*"
    r"(?P<target>türkçe|turkce|ingilizce|english|arapça|arapca|"
    r"almanca|fransızca|fransizca|farsça|farsca|osmanlıca|osmanlica)\b",
    re.I,
)
_LANG_TO_RE = re.compile(
    r"(?P<target>türkçe|turkce|ingilizce|english|arapça|arapca|"
    r"almanca|fransızca|fransizca|farsça|farsca|osmanlıca|osmanlica)"
    r"(?:ya|ye|ya\s+çevir|ye\s+çevir|ya\s+cevir|ye\s+cevir)?\b",
    re.I,
)
_ATOLYE_TERCUME_RE = re.compile(
    r"^(?:tercümede|tercumede|tercüme\s*atölyesinde|tercume\s*atolyesinde|"
    r"tercüme\s*paneline|tercume\s*paneline)\s*[:\-]?\s*(.+)$",
    re.I,
)
_VIDEO_ACTION_RE = re.compile(
    r"\b(?:indir|download|bilgi|info|oynat|izle|aç|ac)\b",
    re.I,
)
_VIDEO_PREFIX_RE = re.compile(
    r"^(?:videoda|video\s*atölyesinde|video\s*atolyesinde|videoya)\s*[:\-]?\s*(.+)$",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ_E", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz_e_enabled() -> bool:
    return _enabled()


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def _norm_lang(label: str) -> str:
    low = (label or "").lower().replace("ı", "i").replace("ş", "s").replace("ç", "c")
    low = low.replace("ö", "o").replace("ü", "u").replace("ğ", "g")
    table = {
        "turkce": "tr",
        "ingilizce": "en",
        "english": "en",
        "arapca": "ar",
        "almanca": "de",
        "fransizca": "fr",
        "farsca": "fa",
        "osmanlica": "ota",
    }
    return table.get(low, low[:8] or "auto")


def _looks_instant_short_translate(raw: str) -> bool:
    """Kısa sohbet içi çeviri — backend anlık yol; E handoff yapmaz."""
    try:
        from ilim_assistant.ana_motor_tercume_yurut import is_instant_translate_message

        if is_instant_translate_message(raw):
            # SRT / uzun metin / atölye öneki varsa yine E
            if _SRT_PATH_RE.search(raw):
                return False
            if _ATOLYE_TERCUME_RE.match(raw):
                return False
            if len(raw) > 220:
                return False
            return True
    except Exception:
        pass
    return False


def parse_tercume_gorev_intent(message: str) -> dict[str, Any] | None:
    """Genel sohbetten tercüme atölye handoff niyeti."""
    if not _enabled():
        return None
    raw = _fold(message)
    if not raw or len(raw) > 800:
        return None
    # Yüzey gönder — tek_sohbet yolu
    if re.search(r"terc[uü]meye\s+g[öo]nder|ceviriye\s+g[öo]nder", raw, re.I):
        return None
    if _looks_instant_short_translate(raw):
        return None

    path = ""
    sm = _SRT_PATH_RE.search(raw)
    if sm:
        path = sm.group("path")

    text_body = ""
    m_atolye = _ATOLYE_TERCUME_RE.match(raw)
    if m_atolye:
        text_body = (m_atolye.group(1) or "").strip()
    elif path and _TRANSLATE_VERB_RE.search(raw):
        text_body = path
    elif _TRANSLATE_VERB_RE.search(raw) and (path or len(raw) >= 40):
        # Uzun çeviri cümlesi veya SRT — atölyeye
        text_body = raw
    else:
        return None

    source_lang = "auto"
    target_lang = "en"
    lp = _LANG_PAIR_RE.search(raw)
    if lp:
        source_lang = _norm_lang(lp.group("source"))
        target_lang = _norm_lang(lp.group("target"))
    else:
        lt = _LANG_TO_RE.search(raw)
        if lt:
            target_lang = _norm_lang(lt.group("target"))

    kind_detail = "srt" if path else "text"
    task_line = text_body[:600]
    return {
        "motor": "tercume",
        "kind": "tercume_gorev",
        "kind_detail": kind_detail,
        "task_line": task_line,
        "text": text_body[:6000],
        "path": path[:400],
        "source_lang": source_lang,
        "target_lang": target_lang,
        "version": FAZ_E_VERSION,
    }


def parse_video_gorev_intent(message: str) -> dict[str, Any] | None:
    """Genel sohbetten video atölye handoff niyeti (URL + indir/bilgi)."""
    if not _enabled():
        return None
    raw = _fold(message)
    if not raw or len(raw) > 800:
        return None
    if re.search(r"videoya\s+g[öo]nder", raw, re.I):
        return None

    url = ""
    um = _URL_RE.search(raw)
    if um:
        url = um.group(0).rstrip(".,);]")
        if url.startswith("www."):
            url = "https://" + url

    body = raw
    vm = _VIDEO_PREFIX_RE.match(raw)
    if vm:
        body = (vm.group(1) or "").strip()
        if not url:
            um2 = _URL_RE.search(body)
            if um2:
                url = um2.group(0).rstrip(".,);]")
                if url.startswith("www."):
                    url = "https://" + url

    if not url:
        return None
    if not (_VIDEO_ACTION_RE.search(raw) or vm):
        # URL var ama eylem yok — yalnız «videoda:» öneki veya indir/bilgi
        return None

    action = "indir"
    low = raw.lower()
    if re.search(r"\b(?:bilgi|info)\b", low):
        action = "bilgi"
    elif re.search(r"\b(?:oynat|izle)\b", low):
        action = "oynat"

    return {
        "motor": "video",
        "kind": "video_gorev",
        "task_line": body[:600] if body else url,
        "url": url[:800],
        "action": action,
        "version": FAZ_E_VERSION,
    }


def parse_faz_e_intent(message: str) -> dict[str, Any] | None:
    """Tercüme veya video — tercüme önce (SRT+çevir çakışmasın diye)."""
    hit = parse_tercume_gorev_intent(message)
    if hit:
        return hit
    return parse_video_gorev_intent(message)


def enrich_orchestra_faz_e(
    orch: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    """Tek yüz: tercüme/video niyeti → quiet handoff."""
    out = dict(orch or {})
    if not _enabled():
        return out
    if isinstance(out.get("ui_action"), dict) and out["ui_action"].get("type"):
        return out
    hit = parse_faz_e_intent(message)
    if not hit:
        return out
    mid = str(hit["motor"])
    try:
        from ilim_assistant.ruzgar_orkestrasyon_faz_c import enrich_orchestra_motor

        out = enrich_orchestra_motor(
            out,
            target=mid,
            channel="faz_e_tek_yuz",
        )
    except Exception:
        out["active_motor"] = mid
    out["tek_sohbet"] = True
    out["quiet"] = True
    out["faz_e"] = FAZ_E_VERSION
    ua: dict[str, Any] = {
        "type": "surface_handoff",
        "motor": mid,
        "kind": hit["kind"],
        "task_line": hit.get("task_line") or "",
        "version": FAZ_E_VERSION,
    }
    if mid == "tercume":
        ua["text"] = hit.get("text") or hit.get("task_line") or ""
        ua["path"] = hit.get("path") or ""
        ua["source_lang"] = hit.get("source_lang") or "auto"
        ua["target_lang"] = hit.get("target_lang") or "en"
        ua["kind_detail"] = hit.get("kind_detail") or "text"
    else:
        ua["url"] = hit.get("url") or ""
        ua["action"] = hit.get("action") or "indir"
    out["ui_action"] = ua
    return out


def faz_e_status() -> dict[str, Any]:
    return {"enabled": _enabled(), "version": FAZ_E_VERSION}
