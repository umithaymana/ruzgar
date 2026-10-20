# Created by Ümit & Gökçenur
"""Tercüme — SRT/VTT çeviri (Faz SRT, 2026-10-20).

Video/ffmpeg gerekmez. Cue zaman damgaları korunur; metin tercume_llm ile çevrilir.
Sohbet: yapıştırılan SRT veya göreli .srt yolu.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

SRT_VERSION = "tercume-srt-v1-2026-10-20"

_SRT_BODY_RE = re.compile(
    r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}",
)
_PATH_RE = re.compile(
    r"(?:^|\s)((?:[\w.\-]+/)*[\w.\-]+\.(?:srt|vtt))\b",
    re.I,
)
_CMD_PATH_RE = re.compile(
    r"(?:(?:altyaz[ıi]|srt|vtt)\s*(?:dosyas[ıi]n[ıi]\s*)?(?:çevir|cevir)|"
    r"(?:çevir|cevir)\s+(?:şu\s+)?(?:altyaz[ıi]|srt))"
    r"\s*[:\-]?\s*(.+)$",
    re.I | re.DOTALL,
)


def srt_translate_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_SRT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def instant_max_cues() -> int:
    try:
        return max(5, min(int(os.environ.get("RUZGAR_TERCUME_SRT_INSTANT_MAX", "60")), 200))
    except ValueError:
        return 60


def looks_like_srt_body(text: str) -> bool:
    raw = (text or "").strip()
    if len(raw) < 20 or "-->" not in raw:
        return False
    return bool(_SRT_BODY_RE.search(raw))


def extract_srt_path_hint(message: str) -> str | None:
    raw = (message or "").strip()
    if not raw:
        return None
    m = _CMD_PATH_RE.search(raw)
    if m:
        cand = m.group(1).strip().strip("«»\"'")
        # gövde SRT ise yol değil
        if looks_like_srt_body(cand):
            return None
        p = _PATH_RE.search(cand) or _PATH_RE.search(raw)
        if p:
            return p.group(1).replace("\\", "/")
        if cand.lower().endswith((".srt", ".vtt")) and "\n" not in cand:
            return cand.replace("\\", "/")
    p2 = _PATH_RE.search(raw)
    if p2 and re.search(r"(?:çevir|cevir|altyaz|srt)", raw, re.I):
        return p2.group(1).replace("\\", "/")
    return None


def extract_srt_body_from_message(message: str) -> str | None:
    raw = (message or "").strip()
    if not raw:
        return None
    if looks_like_srt_body(raw):
        # komut önekini at
        m = re.search(r"(?:çevir|cevir|tercüme|tercume)\s*[:：]\s*", raw, re.I)
        if m:
            rest = raw[m.end() :].strip()
            if looks_like_srt_body(rest):
                return rest
        # zaman damgasından başlat
        m2 = _SRT_BODY_RE.search(raw)
        if m2:
            # cue numarası varsa biraz geri
            start = max(0, raw.rfind("\n", 0, m2.start()) + 1)
            chunk = raw[start:].strip()
            if looks_like_srt_body(chunk):
                return chunk
        return raw
    return None


def translate_srt_text(
    content: str,
    *,
    src_lang: str = "auto",
    tgt_lang: str = "tr",
) -> dict[str, Any]:
    """Ham SRT/VTT metnini çevir → yeni SRT."""
    if not srt_translate_enabled():
        return {"ok": False, "error": "srt_disabled", "version": SRT_VERSION}
    from ilim_assistant.motorlar.altyazi_fabrika import (
        cues_to_srt,
        max_cues_limit,
        parse_srt,
        translate_cues,
        _vtt_to_srtish,
    )

    raw = (content or "").strip()
    if not raw:
        return {"ok": False, "error": "empty", "version": SRT_VERSION}
    if raw.lstrip().lower().startswith("webvtt") or "-->" in raw and raw.count(":") > 4:
        if raw.lstrip().lower().startswith("webvtt"):
            raw = _vtt_to_srtish(raw)
    cues = parse_srt(raw)
    if not cues:
        return {"ok": False, "error": "no_cues", "version": SRT_VERSION}
    lim = max_cues_limit()
    if len(cues) > lim:
        return {
            "ok": False,
            "error": "too_many_cues",
            "cue_count": len(cues),
            "limit": lim,
            "version": SRT_VERSION,
        }
    src = (src_lang or "auto").strip().lower()[:8] or "auto"
    tgt = (tgt_lang or "tr").strip().lower()[:2] or "tr"
    if tgt in ("", "same", "none"):
        out_srt = cues_to_srt(cues)
        return {
            "ok": True,
            "srt": out_srt,
            "cue_count": len(cues),
            "src": src,
            "tgt": tgt,
            "translated": False,
            "version": SRT_VERSION,
        }
    done = translate_cues(cues, src_lang=src, tgt_lang=tgt)
    return {
        "ok": True,
        "srt": cues_to_srt(done),
        "cue_count": len(done),
        "src": src,
        "tgt": tgt,
        "translated": True,
        "version": SRT_VERSION,
    }


def translate_srt_path(
    path: Path,
    *,
    src_lang: str = "auto",
    tgt_lang: str = "tr",
) -> dict[str, Any]:
    if not path.is_file():
        return {"ok": False, "error": "not_found", "version": SRT_VERSION}
    suf = path.suffix.lower()
    if suf not in (".srt", ".vtt"):
        return {"ok": False, "error": "bad_ext", "version": SRT_VERSION}
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:160], "version": SRT_VERSION}
    out = translate_srt_text(raw, src_lang=src_lang, tgt_lang=tgt_lang)
    if out.get("ok"):
        out["source_name"] = path.name
    return out


def maybe_run_srt_translate(
    message: str,
    *,
    workspace_root: str | Path | None = None,
    allow_llm: bool = True,
) -> dict[str, Any]:
    """Sohbet / hub — SRT yapıştırma veya yol → çeviri yanıtı."""
    if not srt_translate_enabled():
        return {"ok": True, "handled": False, "reason": "disabled"}
    raw = (message or "").strip()
    if not raw:
        return {"ok": True, "handled": False, "reason": "empty"}

    from ilim_assistant.motorlar.tercume_faz74 import lang_label, parse_language_pair

    src, tgt = parse_language_pair(raw)
    path_hint = extract_srt_path_hint(raw)
    body = extract_srt_body_from_message(raw)

    if not path_hint and not body:
        return {"ok": True, "handled": False, "reason": "not_srt"}

    if not allow_llm:
        return {"ok": True, "handled": False, "reason": "llm_off"}

    result: dict[str, Any]
    if path_hint:
        root = Path(workspace_root) if workspace_root else None
        p = Path(path_hint)
        if not p.is_file() and root is not None:
            cand = (root / path_hint).resolve()
            try:
                cand.relative_to(root.resolve())
                p = cand
            except ValueError:
                pass
        if not p.is_file():
            return {
                "ok": False,
                "handled": True,
                "reply": (
                    f"Ümit abi, SRT yolu bulunamadı: `{path_hint}`.\n"
                    "Çalışma alanı içindeki göreli yolu yazın."
                ),
                "channel": "tercume_srt",
                "version": SRT_VERSION,
            }
        result = translate_srt_path(p, src_lang=src, tgt_lang=tgt)
    else:
        assert body is not None
        # cue sayısı anlık üst sınır
        from ilim_assistant.motorlar.altyazi_fabrika import parse_srt

        preview = parse_srt(body)
        if len(preview) > instant_max_cues():
            return {
                "ok": True,
                "handled": True,
                "reply": (
                    f"Ümit abi, bu SRT **{len(preview)}** cue — sohbet anlığı "
                    f"üst sınırı **{instant_max_cues()}**.\n"
                    "Video → Altyazı işle **veya** `POST /api/tercume/srt` ile çevirin.\n"
                    f"({SRT_VERSION})"
                ),
                "channel": "tercume_srt_limit",
                "cue_count": len(preview),
                "version": SRT_VERSION,
            }
        result = translate_srt_text(body, src_lang=src, tgt_lang=tgt)

    if not result.get("ok"):
        err = str(result.get("error") or "çeviri başarısız")
        return {
            "ok": False,
            "handled": True,
            "reply": f"Ümit abi, SRT çevirisi olmadı: {err}\n({SRT_VERSION})",
            "channel": "tercume_srt",
            "error": err,
            "version": SRT_VERSION,
        }

    srt_out = str(result.get("srt") or "")
    n = int(result.get("cue_count") or 0)
    reply = (
        f"Ümit abi, **SRT çeviri** ({lang_label(src)} → {lang_label(tgt)}) · "
        f"{n} cue:\n\n```srt\n{srt_out.strip()}\n```\n"
        f"({SRT_VERSION})"
    )
    return {
        "ok": True,
        "handled": True,
        "reply": reply,
        "channel": "tercume_srt",
        "srt": srt_out,
        "cue_count": n,
        "src": result.get("src"),
        "tgt": result.get("tgt"),
        "version": SRT_VERSION,
    }


def srt_status() -> dict[str, Any]:
    return {
        "enabled": srt_translate_enabled(),
        "version": SRT_VERSION,
        "instant_max_cues": instant_max_cues(),
    }
