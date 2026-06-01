# Created by Ümit & Gökçenur
"""Tercüme Faz 4 + 14C — parçalar arası terim tutarlılığı (kalıcı TM)."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

TERCUME_MEMORY_VERSION = "tercume-translate-memory-v14c-2026-05-29"
_TAIL_MAX = 480
_PAIR_MAX = 28

_lock = threading.Lock()
_sessions: dict[str, dict[str, Any]] = {}


def tercume_memory_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_MEMORY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def tercume_memory_persist_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_MEMORY_PERSIST", "1").strip().lower() not in (
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


def _tm_dir() -> Path:
    d = _repo_root() / ".ruzgar" / "tercume_tm"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _key(source_file: str) -> str:
    raw = (source_file or "inline").strip().replace("\\", "/").lower()
    return raw or "inline"


def _session_id(source_file: str, tgt_lang: str) -> str:
    lang = (tgt_lang or "tr").strip().lower()[:12] or "tr"
    return f"{_key(source_file)}|{lang}"


def _disk_path(session_id: str) -> Path:
    import hashlib

    digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:20]
    return _tm_dir() / f"tm_{digest}.json"


def _empty_state(source_file: str, tgt_lang: str) -> dict[str, Any]:
    return {
        "source_file": (source_file or "").strip().replace("\\", "/"),
        "tgt_lang": (tgt_lang or "tr").strip().lower()[:12] or "tr",
        "pairs": [],
        "tail": "",
        "updated_at": 0.0,
        "version": TERCUME_MEMORY_VERSION,
    }


def _persist_state(session_id: str, state: dict[str, Any]) -> None:
    if not tercume_memory_persist_enabled():
        return
    path = _disk_path(session_id)
    payload = {
        "session_id": session_id,
        "source_file": state.get("source_file") or "",
        "tgt_lang": state.get("tgt_lang") or "tr",
        "pairs": state.get("pairs") or [],
        "tail": state.get("tail") or "",
        "updated_at": state.get("updated_at") or time.time(),
        "version": TERCUME_MEMORY_VERSION,
    }
    try:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def _load_from_disk(session_id: str) -> dict[str, Any] | None:
    if not tercume_memory_persist_enabled():
        return None
    path = _disk_path(session_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    pairs = data.get("pairs") or []
    if not isinstance(pairs, list):
        pairs = []
    clean_pairs: list[dict[str, str]] = []
    for p in pairs:
        if not isinstance(p, dict):
            continue
        src = str(p.get("src") or "").strip()
        tgt = str(p.get("tgt") or "").strip()
        if src and tgt:
            clean_pairs.append({"src": src, "tgt": tgt})
    return {
        "source_file": str(data.get("source_file") or ""),
        "tgt_lang": str(data.get("tgt_lang") or "tr"),
        "pairs": clean_pairs[-_PAIR_MAX:],
        "tail": str(data.get("tail") or "")[-_TAIL_MAX:],
        "updated_at": float(data.get("updated_at") or 0),
        "version": str(data.get("version") or TERCUME_MEMORY_VERSION),
        "persisted": True,
    }


def _get_session(source_file: str, tgt_lang: str) -> dict[str, Any]:
    sid = _session_id(source_file, tgt_lang)
    with _lock:
        if sid in _sessions:
            return _sessions[sid]
    loaded = _load_from_disk(sid)
    if loaded:
        with _lock:
            _sessions[sid] = loaded
        return loaded
    st = _empty_state(source_file, tgt_lang)
    with _lock:
        _sessions[sid] = st
    return st


def _save_session(session_id: str, state: dict[str, Any]) -> None:
    state["updated_at"] = time.time()
    with _lock:
        _sessions[session_id] = state
    _persist_state(session_id, state)


def mine_line_pairs(
    source_text: str,
    translated: str,
    *,
    max_pairs: int = 6,
) -> list[tuple[str, str]]:
    """Satır hizalı kısa metinlerden terim çifti çıkar (mümkünse)."""
    src_lines = [ln.strip() for ln in (source_text or "").splitlines() if ln.strip()]
    tgt_lines = [ln.strip() for ln in (translated or "").splitlines() if ln.strip()]
    if not src_lines or len(src_lines) != len(tgt_lines) or len(src_lines) > 14:
        return []
    out: list[tuple[str, str]] = []
    for s, t in zip(src_lines, tgt_lines):
        if len(s) < 3 or len(t) < 3 or len(s) > 140 or len(t) > 180:
            continue
        if s == t:
            continue
        out.append((s, t))
        if len(out) >= max_pairs:
            break
    return out


def _append_pairs(state: dict[str, Any], new_pairs: list[tuple[str, str]]) -> None:
    if not new_pairs:
        return
    existing = {str(p.get("src") or "").lower() for p in state.get("pairs") or [] if isinstance(p, dict)}
    for src, tgt in new_pairs:
        sl = src.lower()
        if sl in existing:
            continue
        state.setdefault("pairs", []).append({"src": src, "tgt": tgt})
        existing.add(sl)
    pairs = state.get("pairs") or []
    if len(pairs) > _PAIR_MAX:
        state["pairs"] = pairs[-_PAIR_MAX:]


def _pairs_block(pairs: list[dict[str, str]], tgt_lang: str) -> str:
    if not pairs:
        return ""
    lines = ["TERİM TUTARLILIĞI (önceki bölümlerle aynı çeviriyi kullan):"]
    for p in pairs[-16:]:
        src = p.get("src") or ""
        tgt = p.get("tgt") or ""
        if src and tgt:
            lines.append(f"- «{src}» → {tgt}")
    lines.append(f"({TERCUME_MEMORY_VERSION})\n")
    return "\n".join(lines)


def consistency_block(source_file: str, *, tgt_lang: str = "tr") -> str:
    if not tercume_memory_enabled():
        return ""
    st = _get_session(source_file, tgt_lang)
    parts: list[str] = []
    tail = str(st.get("tail") or "").strip()
    if tail:
        parts.append(
            "ÖNCEKİ BÖLÜM SONU (üslup ve terimleri sürdür):\n"
            f"…{tail[-_TAIL_MAX:]}\n"
        )
    pairs = st.get("pairs") or []
    if isinstance(pairs, list) and pairs:
        parts.append(_pairs_block(pairs, tgt_lang))
    return "\n".join(parts).strip()


def seed_pairs_from_glossary(source_file: str, text: str, *, tgt_lang: str) -> None:
    """Glossary eşleşen terimleri belleğe sabitle."""
    if not tercume_memory_enabled():
        return
    from ilim_assistant.motorlar.tercume_glossary import glossary_term_pairs

    pairs = glossary_term_pairs(text, source_file=source_file, tgt_lang=tgt_lang)
    if not pairs:
        return
    sid = _session_id(source_file, tgt_lang)
    st = _get_session(source_file, tgt_lang)
    _append_pairs(st, pairs)
    _save_session(sid, st)


def record_translation(
    source_file: str,
    *,
    source_text: str,
    translated: str,
    tgt_lang: str = "tr",
) -> None:
    if not tercume_memory_enabled():
        return
    sid = _session_id(source_file, tgt_lang)
    tail = (translated or "").strip()
    if not tail:
        return
    st = _get_session(source_file, tgt_lang)
    seed_pairs_from_glossary(source_file, source_text, tgt_lang=tgt_lang)
    st = _get_session(source_file, tgt_lang)
    mined = mine_line_pairs(source_text, translated, max_pairs=6)
    _append_pairs(st, mined)
    st["tail"] = tail[-_TAIL_MAX:]
    _save_session(sid, st)


def _delete_disk_for_session(session_id: str) -> None:
    try:
        _disk_path(session_id).unlink(missing_ok=True)
    except OSError:
        pass


def clear_session(source_file: str, *, tgt_lang: str | None = None) -> None:
    sf = (source_file or "").strip()
    if not sf:
        clear_all_sessions()
        return
    if tgt_lang:
        sid = _session_id(sf, tgt_lang)
        with _lock:
            _sessions.pop(sid, None)
        _delete_disk_for_session(sid)
        return
    base = _key(sf)
    with _lock:
        doomed = [k for k in list(_sessions.keys()) if k.startswith(base + "|")]
        for k in doomed:
            _sessions.pop(k, None)
    if tercume_memory_persist_enabled():
        for path in _tm_dir().glob("tm_*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if _key(str(data.get("source_file") or "")) == base:
                    path.unlink(missing_ok=True)
            except Exception:
                continue


def clear_all_sessions() -> None:
    with _lock:
        _sessions.clear()
    if tercume_memory_persist_enabled():
        for path in _tm_dir().glob("tm_*.json"):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                continue


def memory_status(source_file: str, *, tgt_lang: str = "tr") -> dict[str, Any]:
    """Faz 14C — oturum + disk TM özeti."""
    if not tercume_memory_enabled():
        return {
            "ok": True,
            "enabled": False,
            "version": TERCUME_MEMORY_VERSION,
        }
    sf = (source_file or "").strip()
    if not sf:
        return {
            "ok": False,
            "error": "rel gerekli",
            "version": TERCUME_MEMORY_VERSION,
        }
    sid = _session_id(sf, tgt_lang)
    st = _get_session(sf, tgt_lang)
    pairs = st.get("pairs") or []
    n_pairs = len(pairs) if isinstance(pairs, list) else 0
    disk = _disk_path(sid)
    return {
        "ok": True,
        "enabled": True,
        "persist": tercume_memory_persist_enabled(),
        "source_file": sf,
        "tgt_lang": (tgt_lang or "tr").strip().lower()[:12],
        "pairs": n_pairs,
        "has_tail": bool(st.get("tail")),
        "persisted_on_disk": disk.is_file(),
        "updated_at": st.get("updated_at"),
        "version": TERCUME_MEMORY_VERSION,
    }


def session_snapshot(source_file: str, *, tgt_lang: str = "tr") -> dict[str, Any]:
    hit = memory_status(source_file, tgt_lang=tgt_lang)
    if not hit.get("ok"):
        return hit
    return {
        "ok": True,
        "source_file": source_file or "",
        "pairs": hit.get("pairs") or 0,
        "has_tail": hit.get("has_tail"),
        "persisted": hit.get("persisted_on_disk"),
        "version": TERCUME_MEMORY_VERSION,
    }
