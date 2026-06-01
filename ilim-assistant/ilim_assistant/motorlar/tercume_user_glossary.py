# Created by Ümit & Gökçenur
"""Tercüme Faz 15B — kullanıcı terim tablosu (TM düzenleme)."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any

USER_GLOSSARY_VERSION = "tercume-user-glossary-v17f-2026-05-29"
_MAX_ENTRIES = 400

_lock = threading.Lock()


def user_glossary_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_USER_GLOSSARY", "1").strip().lower() not in (
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


def _glossary_path() -> Path:
    d = _repo_root() / ".ruzgar"
    d.mkdir(parents=True, exist_ok=True)
    return d / "tercume_user_glossary.json"


def _glossary_rel_path() -> str:
    try:
        return _glossary_path().relative_to(_repo_root().resolve()).as_posix()
    except ValueError:
        return ".ruzgar/tercume_user_glossary.json"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _load_raw() -> dict[str, Any]:
    path = _glossary_path()
    if not path.is_file():
        return {"version": USER_GLOSSARY_VERSION, "entries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"version": USER_GLOSSARY_VERSION, "entries": []}


def _save_raw(data: dict[str, Any]) -> None:
    payload = {
        "version": USER_GLOSSARY_VERSION,
        "updated_at": time.time(),
        "entries": data.get("entries") or [],
    }
    path = _glossary_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def list_entries(*, limit: int = 80) -> dict[str, Any]:
    if not user_glossary_enabled():
        return {"ok": True, "enabled": False, "entries": [], "version": USER_GLOSSARY_VERSION}
    with _lock:
        data = _load_raw()
    entries = data.get("entries") or []
    if not isinstance(entries, list):
        entries = []
    lim = max(1, min(200, int(limit)))
    return {
        "ok": True,
        "enabled": True,
        "entries": entries[:lim],
        "total": len(entries),
        "version": USER_GLOSSARY_VERSION,
        "path": _glossary_rel_path(),
    }


def add_entry(
    *,
    src: str,
    tr: str = "",
    en: str = "",
    ar: str = "",
    scope: str = "",
    note: str = "",
) -> dict[str, Any]:
    if not user_glossary_enabled():
        return {"ok": False, "error": "Kullanıcı sözlüğü kapalı."}
    source = (src or "").strip()
    if len(source) < 2:
        return {"ok": False, "error": "Kaynak terim en az 2 karakter."}
    row = {
        "id": uuid.uuid4().hex[:10],
        "src": source,
        "tr": (tr or "").strip(),
        "en": (en or "").strip(),
        "ar": (ar or "").strip(),
        "scope": (scope or "").strip().replace("\\", "/"),
        "note": (note or "").strip()[:200],
        "created_at": time.time(),
    }
    with _lock:
        data = _load_raw()
        entries = list(data.get("entries") or [])
        sl = _norm(source)
        entries = [e for e in entries if not (isinstance(e, dict) and _norm(str(e.get("src"))) == sl)]
        entries.append(row)
        if len(entries) > _MAX_ENTRIES:
            entries = entries[-_MAX_ENTRIES:]
        data["entries"] = entries
        _save_raw(data)
    return {"ok": True, "entry": row, "total": len(entries)}


def import_rows(
    rows: list[dict[str, str]],
    *,
    merge: bool = True,
) -> dict[str, Any]:
    """Toplu terim içe aktarma (CSV/JSON/TMX sonrası)."""
    if not user_glossary_enabled():
        return {"ok": False, "error": "Kullanıcı sözlüğü kapalı."}
    if not rows:
        return {"ok": False, "error": "İçe aktarılacak satır yok."}
    added = 0
    skipped = 0
    with _lock:
        data = _load_raw()
        entries = list(data.get("entries") or []) if merge else []
        existing = {_norm(str(e.get("src"))) for e in entries if isinstance(e, dict)}
        for raw in rows[:250]:
            if not isinstance(raw, dict):
                skipped += 1
                continue
            source = str(raw.get("src") or "").strip()
            if len(source) < 2:
                skipped += 1
                continue
            sl = _norm(source)
            if sl in existing:
                entries = [e for e in entries if not (isinstance(e, dict) and _norm(str(e.get("src"))) == sl)]
                existing.discard(sl)
            row = {
                "id": uuid.uuid4().hex[:10],
                "src": source,
                "tr": str(raw.get("tr") or "").strip(),
                "en": str(raw.get("en") or "").strip(),
                "ar": str(raw.get("ar") or "").strip(),
                "scope": str(raw.get("scope") or "").strip().replace("\\", "/"),
                "note": str(raw.get("note") or "").strip()[:200],
                "created_at": time.time(),
            }
            if not row["tr"] and not row["en"] and not row["ar"]:
                skipped += 1
                continue
            entries.append(row)
            existing.add(sl)
            added += 1
        if len(entries) > _MAX_ENTRIES:
            entries = entries[-_MAX_ENTRIES:]
        data["entries"] = entries
        _save_raw(data)
    return {
        "ok": True,
        "added": added,
        "skipped": skipped,
        "total": len(entries),
        "version": USER_GLOSSARY_VERSION,
    }


def import_from_text(text: str, fmt: str = "", *, merge: bool = True) -> dict[str, Any]:
    from ilim_assistant.motorlar.tercume_glossary_import import parse_glossary_import

    parsed = parse_glossary_import(text, fmt)
    if not parsed.get("ok"):
        return parsed
    hit = import_rows(list(parsed.get("rows") or []), merge=merge)
    if hit.get("ok"):
        hit["format"] = parsed.get("format")
        hit["parsed"] = parsed.get("count")
    return hit


def import_from_tmx(text: str, *, tgt_lang: str = "tr", merge: bool = True) -> dict[str, Any]:
    from ilim_assistant.motorlar.tercume_tmx import parse_tmx

    code = (tgt_lang or "tr").strip().lower()[:2] or "tr"
    col = {"tr": "tr", "en": "en", "ar": "ar"}.get(code, "tr")
    pairs = parse_tmx(text)
    if not pairs:
        return {"ok": False, "error": "TMX içinde geçerli <tu> çifti yok."}
    rows: list[dict[str, str]] = []
    for src, tgt in pairs:
        row = {"src": src, col: tgt}
        rows.append(row)
    hit = import_rows(rows, merge=merge)
    if hit.get("ok"):
        hit["format"] = "tmx"
        hit["parsed"] = len(pairs)
    return hit


def delete_entry(entry_id: str) -> dict[str, Any]:
    eid = (entry_id or "").strip()
    if not eid:
        return {"ok": False, "error": "id gerekli"}
    with _lock:
        data = _load_raw()
        entries = [e for e in (data.get("entries") or []) if isinstance(e, dict) and e.get("id") != eid]
        if len(entries) == len(data.get("entries") or []):
            return {"ok": False, "error": "Terim bulunamadı"}
        data["entries"] = entries
        _save_raw(data)
    return {"ok": True, "deleted": eid, "total": len(entries)}


def _scope_matches(scope: str, source_file: str) -> bool:
    sc = (scope or "").strip().replace("\\", "/").lower()
    if not sc:
        return True
    sf = (source_file or "").strip().replace("\\", "/").lower()
    return sc in sf or sf.endswith(sc)


def matching_user_terms(
    text: str,
    *,
    source_file: str = "",
    tgt_lang: str = "tr",
    max_terms: int = 12,
) -> list[tuple[str, str]]:
    if not user_glossary_enabled():
        return []
    code = (tgt_lang or "tr").strip().lower()[:2] or "tr"
    col = {"tr": "tr", "en": "en", "ar": "ar", "de": "en", "fr": "en", "fa": "ar", "ru": "en"}.get(
        code, "tr"
    )
    blob = _norm(f"{text} {source_file}")
    with _lock:
        entries = list(_load_raw().get("entries") or [])
    out: list[tuple[str, str]] = []
    for e in entries:
        if len(out) >= max_terms:
            break
        if not isinstance(e, dict):
            continue
        if not _scope_matches(str(e.get("scope") or ""), source_file):
            continue
        src = str(e.get("src") or "").strip()
        if not src or _norm(src) not in blob:
            continue
        tgt = str(e.get(col) or e.get("tr") or e.get("en") or "").strip()
        if tgt:
            out.append((src, tgt))
    return out


def user_glossary_directive(
    text: str,
    *,
    source_file: str = "",
    tgt_lang: str = "tr",
    max_terms: int = 10,
) -> str:
    pairs = matching_user_terms(text, source_file=source_file, tgt_lang=tgt_lang, max_terms=max_terms)
    if not pairs:
        return ""
    lines = ["KULLANICI TERİMLERİ (Ümit abi — bu çeviri için sabit kalsın):"]
    for src, tgt in pairs[:max_terms]:
        lines.append(f"- «{src}» → {tgt}")
    lines.append(f"({USER_GLOSSARY_VERSION})\n")
    return "\n".join(lines)
