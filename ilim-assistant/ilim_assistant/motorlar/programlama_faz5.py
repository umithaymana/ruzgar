# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 5: oturum proje bağlamı.

Yerel dosya (git'e gitmez): `<workspace>/.ruzgar/programlama_oturum.json`
Amaç: LLM her turda açık dosya, hedef, son yazımlar ve pytest özetini görsün.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import infer_rel_paths, repo_root

FAZ5_VERSION = "programlama-faz5-v1-2026-05-20"
SESSION_REL_DIR = ".ruzgar"
SESSION_FILENAME = "programlama_oturum.json"
MAX_TURNS = 24
MAX_WRITES = 16
MAX_SNIPPET_CHARS = 2800


def _enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_SESSION_CTX", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def session_file_path(workspace_root: str | Path | None = None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    return root / SESSION_REL_DIR / SESSION_FILENAME


def _empty_session(root_s: str | None = None) -> dict[str, Any]:
    return {
        "version": FAZ5_VERSION,
        "updated_at": time.time(),
        "workspace_root": root_s,
        "project": {
            "name": "",
            "goal": "",
            "stack": [],
            "notes": "",
        },
        "active_file": "",
        "editor_language": "",
        "editor_snippet": "",
        "open_files": [],
        "recent_writes": [],
        "recent_turns": [],
        "last_pytest": None,
    }


def load_session(workspace_root: str | Path | None = None) -> dict[str, Any]:
    if not _enabled():
        return _empty_session()
    path = session_file_path(workspace_root)
    root = repo_root(workspace_root)
    root_s = str(root) if root else None
    if path is None or not path.is_file():
        return _empty_session(root_s)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return _empty_session(root_s)
        raw.setdefault("project", {})
        raw.setdefault("recent_turns", [])
        raw.setdefault("recent_writes", [])
        raw["workspace_root"] = root_s or raw.get("workspace_root")
        return raw
    except (OSError, json.JSONDecodeError):
        return _empty_session(root_s)


def save_session(workspace_root: str | Path | None, data: dict[str, Any]) -> dict[str, Any]:
    if not _enabled():
        return data
    path = session_file_path(workspace_root)
    if path is None:
        return data
    data = dict(data)
    data["version"] = FAZ5_VERSION
    data["updated_at"] = time.time()
    root = repo_root(workspace_root)
    if root is not None:
        data["workspace_root"] = str(root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass
    return data


def sync_client_editor_state(
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
    editor_snippet: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """İstemciden gelen açık dosya + editör özeti (her tur başında)."""
    sess = load_session(workspace_root)
    af = (active_file or "").strip().replace("\\", "/").lstrip("/")
    if af:
        sess["active_file"] = af[:400]
        opens = list(sess.get("open_files") or [])
        if af not in opens:
            opens.insert(0, af)
        sess["open_files"] = opens[:12]
    lang = (language or "").strip()
    if lang:
        sess["editor_language"] = lang[:40]
    snip = (editor_snippet or "").strip()
    if snip:
        sess["editor_snippet"] = snip[:MAX_SNIPPET_CHARS]
    return save_session(workspace_root, sess)


def _append_unique_writes(sess: dict[str, Any], paths: list[str]) -> None:
    if not paths:
        return
    rows = list(sess.get("recent_writes") or [])
    now = time.time()
    for p in paths:
        rel = str(p).strip().replace("\\", "/").lstrip("/")
        if not rel:
            continue
        rows = [r for r in rows if str(r.get("path") or "") != rel]
        rows.insert(0, {"path": rel, "ts": now})
    sess["recent_writes"] = rows[:MAX_WRITES]


def record_tool_summary(
    workspace_root: str | Path | None,
    *,
    writes: list[str] | None = None,
    pytest_ok: bool | None = None,
    pytest_exit: int | None = None,
) -> None:
    sess = load_session(workspace_root)
    _append_unique_writes(sess, list(writes or []))
    if pytest_ok is not None:
        sess["last_pytest"] = {
            "ok": bool(pytest_ok),
            "exit": int(pytest_exit or 0),
            "ts": time.time(),
        }
    save_session(workspace_root, sess)


def record_chat_turn(
    workspace_root: str | Path | None,
    *,
    user_message: str,
    assistant_reply: str,
    writes: list[str] | None = None,
    pytest_ok: bool | None = None,
    pytest_exit: int | None = None,
    active_file: str | None = None,
) -> None:
    if not _enabled():
        return
    sess = load_session(workspace_root)
    if active_file:
        sync_client_editor_state(workspace_root, active_file=active_file)
        sess = load_session(workspace_root)
    root = repo_root(workspace_root)
    inferred = infer_rel_paths(user_message, root) if root else []
    _append_unique_writes(sess, list(writes or []) + inferred)
    if pytest_ok is not None:
        sess["last_pytest"] = {
            "ok": bool(pytest_ok),
            "exit": int(pytest_exit or 0),
            "ts": time.time(),
        }
    turns = list(sess.get("recent_turns") or [])
    preview = (assistant_reply or "").strip().replace("\r\n", "\n")
    if len(preview) > 420:
        preview = preview[:417] + "…"
    turns.insert(
        0,
        {
            "ts": time.time(),
            "user": (user_message or "").strip()[:500],
            "assistant_preview": preview,
            "files_touched": list(writes or [])[:8],
            "pytest_ok": pytest_ok,
        },
    )
    sess["recent_turns"] = turns[:MAX_TURNS]
    save_session(workspace_root, sess)


def clear_session(workspace_root: str | Path | None) -> dict[str, Any]:
    path = session_file_path(workspace_root)
    if path is not None and path.is_file():
        try:
            path.unlink()
        except OSError:
            pass
    return _empty_session(str(repo_root(workspace_root)) if repo_root(workspace_root) else None)


def patch_project_from_message(message: str) -> dict[str, str] | None:
    """«proje kaydet: ad | hedef: … | stack: python, fastapi»"""
    raw = (message or "").strip()
    if not raw:
        return None
    low = raw.lower()
    if not any(
        k in low
        for k in (
            "proje kaydet",
            "proje adı",
            "proje adi",
            "hedef:",
            "hedef ",
            "stack:",
            "yığın:",
            "yigin:",
        )
    ):
        return None
    out: dict[str, str] = {}
    m_name = re.search(
        r"(?:proje\s+kaydet|proje\s+ad[ıi])\s*:?\s*(.+?)(?:\||$)",
        raw,
        re.I,
    )
    if m_name:
        out["name"] = m_name.group(1).strip()[:120]
    m_goal = re.search(r"hedef\s*:?\s*(.+?)(?:\||$)", raw, re.I)
    if m_goal:
        out["goal"] = m_goal.group(1).strip()[:800]
    m_stack = re.search(r"(?:stack|yığın|yigin)\s*:?\s*(.+?)(?:\||$)", raw, re.I)
    if m_stack:
        out["stack"] = m_stack.group(1).strip()[:200]
    m_note = re.search(r"(?:not|notlar)\s*:?\s*(.+?)(?:\||$)", raw, re.I)
    if m_note:
        out["notes"] = m_note.group(1).strip()[:600]
    return out or None


def apply_project_patch(workspace_root: str | Path | None, patch: dict[str, Any]) -> dict[str, Any]:
    sess = load_session(workspace_root)
    proj = dict(sess.get("project") or {})
    if patch.get("name") is not None:
        proj["name"] = str(patch["name"])[:120]
    if patch.get("goal") is not None:
        proj["goal"] = str(patch["goal"])[:800]
    if patch.get("stack") is not None:
        st = patch["stack"]
        if isinstance(st, list):
            proj["stack"] = [str(x).strip()[:40] for x in st if str(x).strip()][:12]
        else:
            parts = re.split(r"[,;|]+", str(st))
            proj["stack"] = [p.strip()[:40] for p in parts if p.strip()][:12]
    if patch.get("notes") is not None:
        proj["notes"] = str(patch["notes"])[:600]
    sess["project"] = proj
    return save_session(workspace_root, sess)


def wants_project_summary(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "proje özeti",
            "proje ozeti",
            "proje bağlamı",
            "proje baglami",
            "proje durumu",
            "oturum özeti",
            "oturum ozeti",
            "session context",
        )
    )


def wants_project_clear(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "proje temizle",
            "oturum temizle",
            "proje bağlamını sil",
            "proje baglamini sil",
            "session clear",
        )
    )


def usta_coding_directive() -> str:
    return (
        "[USTA PROGRAMLAMA — Faz 5 — Ümit & Gökçenur]\n"
        "Hedef seviye: senin gibi modüler yazılım — betik → uygulama → paket/kütüphane → "
        "çok modüllü yapay zeka sistemi.\n"
        "Her tur: (1) proje hedefini hatırla (2) en küçük doğru patch (3) test/lint ile doğrula.\n"
        "Üstteki [OTURUM PROJE BAĞLAMI] satırlarına sadık kal; açık dosyayı ve son pytest'i yok sayma.\n"
        "Yeni özellik: önce arayüz/sözleşme, sonra çekirdek, sonra test; gereksiz soyutlama yok.\n"
    )


def format_session_context_block(workspace_root: str | Path | None) -> str:
    if not _enabled():
        return ""
    sess = load_session(workspace_root)
    proj = sess.get("project") or {}
    lines: list[str] = [
        "[OTURUM PROJE BAĞLAMI — Faz 5]",
    ]
    name = str(proj.get("name") or "").strip()
    goal = str(proj.get("goal") or "").strip()
    stack = proj.get("stack") or []
    notes = str(proj.get("notes") or "").strip()
    if name:
        lines.append(f"Proje adı: {name}")
    if goal:
        lines.append(f"Hedef: {goal}")
    if stack:
        lines.append("Yığın: " + ", ".join(str(x) for x in stack[:12]))
    if notes:
        lines.append(f"Notlar: {notes[:400]}")
    af = str(sess.get("active_file") or "").strip()
    if af:
        lines.append(f"Açık dosya (atölye): {af}")
    lang = str(sess.get("editor_language") or "").strip()
    if lang:
        lines.append(f"Editör dili: {lang}")
    snip = str(sess.get("editor_snippet") or "").strip()
    if snip and len(snip) > 20:
        preview = snip if len(snip) <= 900 else snip[:897] + "…"
        lines.append(f"Editördeki kod (özet):\n```\n{preview}\n```")
    opens = sess.get("open_files") or []
    if isinstance(opens, list) and opens:
        lines.append("Son açılan dosyalar: " + ", ".join(str(x) for x in opens[:8]))
    writes = sess.get("recent_writes") or []
    if writes:
        wpaths = [str(w.get("path") or "") for w in writes[:6] if w.get("path")]
        if wpaths:
            lines.append("Son yazılan/okunan yollar: " + ", ".join(wpaths))
    lp = sess.get("last_pytest")
    if isinstance(lp, dict) and lp.get("ok") is not None:
        st = "geçti" if lp.get("ok") else "kaldı"
        lines.append(f"Son pytest: {st} (exit {lp.get('exit', '?')})")
    turns = sess.get("recent_turns") or []
    if turns:
        lines.append("Son turlar (kısa):")
        for t in turns[:4]:
            if not isinstance(t, dict):
                continue
            u = str(t.get("user") or "")[:80]
            a = str(t.get("assistant_preview") or "")[:100]
            lines.append(f"  · Kullanıcı: {u}")
            if a:
                lines.append(f"    Yanıt: {a}")
    if len(lines) <= 1:
        lines.append(
            "(Henüz kayıtlı oturum yok — «proje kaydet: Ad | hedef: …» ile hedef tanımlayabilirsin.)"
        )
    lines.append(
        "Komutlar: proje özeti · proje kaydet: … · proje temizle"
    )
    return "\n".join(lines)


def format_project_summary_report(workspace_root: str | Path | None) -> str:
    block = format_session_context_block(workspace_root)
    path = session_file_path(workspace_root)
    path_s = str(path) if path else "(workspace yok)"
    return (
        "Ümit abi, Programlama oturum özeti (Faz 5):\n\n"
        f"{block}\n\n"
        f"Dosya: `{path_s}`\n"
        f"Sürüm: {FAZ5_VERSION}"
    )


def build_session_api_payload(workspace_root: str | Path | None = None) -> dict[str, Any]:
    sess = load_session(workspace_root)
    return {
        "ok": True,
        "version": FAZ5_VERSION,
        "path": str(session_file_path(workspace_root) or ""),
        "session": sess,
        "context_text": format_session_context_block(workspace_root),
    }


def maybe_apply_message_project_patch(
    message: str, workspace_root: str | Path | None
) -> bool:
    patch = patch_project_from_message(message)
    if not patch:
        return False
    apply_project_patch(workspace_root, patch)
    return True
