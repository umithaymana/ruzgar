# Created by Ümit & Gökçenur
"""Tercüme Faz 6 — onaylı çeviri → ana motor hafızası (genel + knowledge RAG)."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

TERCUME_BRIDGE_VERSION = "tercume-hafiza-bridge-v6-faz6-2026-05-31"
_BRIDGE_LOG = "tercume_bridge_log.jsonl"
_MAX_SORU = 220
_MAX_CEVAP = 1800
_MAX_SOURCE_SNIP = 120

_WS_RE = re.compile(r"\s+")


def tercume_bridge_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_BRIDGE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def knowledge_bridge_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_BRIDGE_KNOWLEDGE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _repo_root() -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root(None)
        if r:
            return Path(r)
    except Exception:
        pass
    return Path(__file__).resolve().parents[2]


def _bridge_log_path() -> Path:
    d = _repo_root() / ".ruzgar"
    d.mkdir(parents=True, exist_ok=True)
    return d / _BRIDGE_LOG


def _clean(text: str, limit: int) -> str:
    t = _WS_RE.sub(" ", (text or "").strip())
    if len(t) > limit:
        return t[: limit - 1].rstrip() + "…"
    return t


def _soru_key(
    *,
    source_file: str,
    source_excerpt: str,
    tgt_lang: str,
    page_index: int | None,
) -> str:
    name = Path(source_file).stem if source_file else "metin"
    page = f" s{int(page_index) + 1}" if page_index is not None else ""
    snip = _clean(source_excerpt, _MAX_SOURCE_SNIP)
    lang = (tgt_lang or "tr").strip().lower()[:2] or "tr"
    if snip:
        return _clean(f"tercüme {name}{page} ({lang}): {snip}", _MAX_SORU)
    return _clean(f"tercüme {name}{page} ({lang})", _MAX_SORU)


def build_bridge_preview(
    source_text: str,
    translated_text: str,
    *,
    source_file: str = "",
    page_index: int | None = None,
    tgt_lang: str = "tr",
    src_lang: str = "auto",
) -> dict[str, Any]:
    """Ana hafızaya yazılacak soru/cevap önizlemesi (henüz diske yazmaz)."""
    src = (source_text or "").strip()
    tr = (translated_text or "").strip()
    if not tr:
        return {"ok": False, "error": "Hedef çeviri boş."}
    if len(tr) < 12:
        return {"ok": False, "error": "Çeviri çok kısa (en az 12 karakter)."}

    soru = _soru_key(
        source_file=source_file,
        source_excerpt=src[:400] if src else Path(source_file).name,
        tgt_lang=tgt_lang,
        page_index=page_index,
    )
    cevap = _clean(tr, _MAX_CEVAP)

    return {
        "ok": True,
        "version": TERCUME_BRIDGE_VERSION,
        "soru": soru,
        "cevap": cevap,
        "source_file": source_file or "",
        "page_index": page_index,
        "tgt_lang": tgt_lang,
        "src_lang": src_lang,
        "source_chars": len(src),
        "target_chars": len(tr),
        "motor_tipi": "Tercüme",
        "hint": "Onay sonrası ruzgar_genel_hafiza.json + isteğe knowledge/learned/tercume/",
    }


def _append_bridge_log(entry: dict[str, Any]) -> None:
    path = _bridge_log_path()
    row = {"ts": time.time(), **entry}
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > 120:
            path.write_text("\n".join(lines[-120:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def read_bridge_log(*, limit: int = 12) -> list[dict[str, Any]]:
    path = _bridge_log_path()
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
    except OSError:
        return []


def save_bridge_entry(
    source_text: str,
    translated_text: str,
    *,
    source_file: str = "",
    page_index: int | None = None,
    tgt_lang: str = "tr",
    src_lang: str = "auto",
    approved: bool = False,
    save_knowledge: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Onaylı çeviriyi genel hafızaya (ve isteğe knowledge RAG) yazar."""
    if not tercume_bridge_enabled():
        return {"ok": False, "error": "Tercüme hafıza köprüsü kapalı (RUZGAR_TERCUME_BRIDGE=0)."}
    if not approved:
        return {"ok": False, "error": "Onay gerekli (approved=1)."}

    preview = build_bridge_preview(
        source_text,
        translated_text,
        source_file=source_file,
        page_index=page_index,
        tgt_lang=tgt_lang,
        src_lang=src_lang,
    )
    if not preview.get("ok"):
        return preview

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "soru": preview.get("soru"),
            "cevap_chars": len(str(preview.get("cevap") or "")),
            "version": TERCUME_BRIDGE_VERSION,
        }

    soru = str(preview.get("soru") or "")
    cevap = str(preview.get("cevap") or "")

    from ilim_assistant.ruzgar_hafiza_koprusu import ogren_learning_for_motor

    ogren_learning_for_motor("tercume", soru, cevap)

    knowledge_rel = ""
    if save_knowledge and knowledge_bridge_enabled():
        try:
            from ilim_assistant.memory import save_exchange

            title = Path(source_file).stem[:60] if source_file else "tercume_parcasi"
            user_block = soru
            if source_text.strip():
                user_block += f"\n\nKaynak parça:\n{source_text.strip()[:1200]}"
            path, _msg = save_exchange(
                user_block,
                cevap,
                title_hint=f"tercume_{title}",
                rebuild_index=True,
            )
            try:
                from ilim_assistant.rag_store import _KNOWLEDGE_ROOT

                knowledge_rel = path.relative_to(_KNOWLEDGE_ROOT.parent).as_posix()
            except ValueError:
                knowledge_rel = f"knowledge/learned/{path.name}"
        except Exception:
            knowledge_rel = ""

    _append_bridge_log(
        {
            "lesson": "bridge_save",
            "soru": soru,
            "source_file": source_file,
            "page_index": page_index,
            "tgt_lang": tgt_lang,
            "knowledge_rel": knowledge_rel,
            "version": TERCUME_BRIDGE_VERSION,
        }
    )

    return {
        "ok": True,
        "saved": True,
        "soru": soru,
        "cevap_chars": len(cevap),
        "knowledge_rel": knowledge_rel,
        "version": TERCUME_BRIDGE_VERSION,
        "message": "Ana hafızaya kaydedildi — genel sohbette bu parça hatırlanabilir.",
    }
