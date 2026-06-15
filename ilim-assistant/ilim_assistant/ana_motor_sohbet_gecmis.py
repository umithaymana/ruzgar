# Created by Ümit & Gökçenur
"""Ana Motor Faz AA1 — sohbet geçmişi arama (jsonl + API)."""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

FAZ_AA_CHAT_VERSION = "ana-motor-sohbet-gecmis-aa1-2026-06-10"

_PKG_ROOT = Path(__file__).resolve().parent.parent
_HISTORY_PATH = _PKG_ROOT / ".ruzgar" / "ana_motor_chat_history.jsonl"
_MAX_STORE = 500


def chat_history_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_CHAT_HISTORY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _default_limit() -> int:
    try:
        return max(5, min(int(os.environ.get("RUZGAR_ANA_CHAT_HISTORY_LIMIT", "30")), 100))
    except ValueError:
        return 30


def _normalize_query(q: str) -> str:
    t = unicodedata.normalize("NFKC", (q or "").strip().lower())
    t = re.sub(r"\s+", " ", t)
    return t


def _trim_history_file() -> None:
    if not _HISTORY_PATH.is_file():
        return
    try:
        lines = _HISTORY_PATH.read_text(encoding="utf-8").splitlines()
        if len(lines) <= _MAX_STORE:
            return
        _HISTORY_PATH.write_text("\n".join(lines[-_MAX_STORE:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def append_chat_turn(
    *,
    user_message: str,
    assistant_message: str,
    mode_norm: str = "genel",
    session_id: str | None = None,
    plan_primary: str = "",
) -> dict[str, Any]:
    if not chat_history_enabled():
        return {"ok": True, "stored": False, "reason": "disabled"}
    user = (user_message or "").strip()
    reply = (assistant_message or "").strip()
    if not user or not reply or reply.startswith("["):
        return {"ok": True, "stored": False, "reason": "empty"}
    entry: dict[str, Any] = {
        "ts": time.time(),
        "mode": str(mode_norm or "genel")[:24],
        "user": user[:2000],
        "assistant": reply[:4000],
        "plan_primary": str(plan_primary or "")[:32],
    }
    if session_id:
        entry["session_id"] = str(session_id)[:64]
    try:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _trim_history_file()
        return {"ok": True, "stored": True, "version": FAZ_AA_CHAT_VERSION}
    except Exception as exc:
        return {"ok": False, "stored": False, "error": str(exc)[:160]}


def _load_entries(*, limit: int | None = None) -> list[dict[str, Any]]:
    cap = int(limit if limit is not None else _default_limit())
    if not _HISTORY_PATH.is_file():
        return []
    items: list[dict[str, Any]] = []
    try:
        lines = _HISTORY_PATH.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                items.append(row)
            if len(items) >= cap:
                break
    except Exception:
        return []
    return items


def recent_chat_history(*, limit: int | None = None) -> dict[str, Any]:
    if not chat_history_enabled():
        return {"ok": True, "items": [], "count": 0, "disabled": True}
    items = _load_entries(limit=limit)
    return {
        "ok": True,
        "version": FAZ_AA_CHAT_VERSION,
        "items": items,
        "count": len(items),
    }


def should_inject_disk_history_into_prior() -> bool:
    """Kapalı (varsayılan): disk jsonl yalnızca açık «geçmiş sohbet» sorusunda kullanılır."""
    return os.environ.get("RUZGAR_CHAT_DISK_PRIOR", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def chat_history_stats() -> dict[str, Any]:
    """jsonl arşiv özeti — satır sayısı + son tur (Faz AH1)."""
    if not chat_history_enabled():
        return {
            "ok": True,
            "enabled": False,
            "stored_turns": 0,
            "version": FAZ_AA_CHAT_VERSION,
        }
    stored = 0
    if _HISTORY_PATH.is_file():
        try:
            stored = sum(1 for line in _HISTORY_PATH.read_text(encoding="utf-8").splitlines() if line.strip())
        except Exception:
            stored = 0
    recent = _load_entries(limit=1)
    last = recent[0] if recent else {}
    last_user = str(last.get("user") or "").strip()
    return {
        "ok": True,
        "enabled": True,
        "stored_turns": stored,
        "max_store": _MAX_STORE,
        "last_at": last.get("ts"),
        "last_mode": last.get("mode"),
        "last_user_preview": last_user[:120] if last_user else "",
        "recall_active": stored > 0,
        "version": FAZ_AA_CHAT_VERSION,
    }


def export_session_chat_history(
    *,
    session_id: str | None = None,
    mode: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Faz AB1 — jsonl kayıtlarını isteğe bağlı oturum/mod filtresiyle dışa aktar."""
    if not chat_history_enabled():
        return {"ok": False, "error": "Sohbet geçmişi kapalı.", "items": [], "count": 0}
    try:
        cap = max(5, min(int(limit or 100), 500))
    except (TypeError, ValueError):
        cap = 100
    sid = (session_id or "").strip()
    mode_norm = (mode or "").strip().lower()
    scan_cap = 500 if sid or mode_norm else cap
    items = _load_entries(limit=scan_cap)
    if sid:
        items = [row for row in items if str(row.get("session_id") or "") == sid]
    if mode_norm:
        items = [row for row in items if str(row.get("mode") or "genel").lower() == mode_norm]
    items = items[:cap]
    return {
        "ok": True,
        "version": FAZ_AA_CHAT_VERSION,
        "exported_at": time.time(),
        "session_id": sid or None,
        "mode": mode_norm or None,
        "items": items,
        "count": len(items),
    }


def clear_chat_history(
    *,
    mode: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Sohbet jsonl kaydını temizle — isteğe bağlı mod/oturum filtresi."""
    if not chat_history_enabled():
        return {"ok": True, "cleared": 0, "disabled": True, "version": FAZ_AA_CHAT_VERSION}
    mode_norm = (mode or "").strip().lower()
    sid = (session_id or "").strip()
    if not _HISTORY_PATH.is_file():
        return {"ok": True, "cleared": 0, "version": FAZ_AA_CHAT_VERSION}
    if not mode_norm and not sid:
        try:
            count = len(_HISTORY_PATH.read_text(encoding="utf-8").splitlines())
            _HISTORY_PATH.unlink(missing_ok=True)
            return {"ok": True, "cleared": count, "all": True, "version": FAZ_AA_CHAT_VERSION}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:200], "version": FAZ_AA_CHAT_VERSION}
    try:
        kept: list[str] = []
        removed = 0
        for line in _HISTORY_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                kept.append(line)
                continue
            drop = False
            if mode_norm and str(row.get("mode") or "genel").lower() == mode_norm:
                drop = True
            if sid and str(row.get("session_id") or "") == sid:
                drop = True
            if drop:
                removed += 1
            else:
                kept.append(line)
        if kept:
            _HISTORY_PATH.write_text("\n".join(kept) + "\n", encoding="utf-8")
        else:
            _HISTORY_PATH.unlink(missing_ok=True)
        return {
            "ok": True,
            "cleared": removed,
            "mode": mode_norm or None,
            "session_id": sid or None,
            "version": FAZ_AA_CHAT_VERSION,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "version": FAZ_AA_CHAT_VERSION}


_RECALL_STOP = frozenset(
    {
        "olabilir",
        "miyiz",
        "musun",
        "mısın",
        "hakkında",
        "hakkinda",
        "konuş",
        "konus",
        "konuşmuş",
        "konusmus",
        "bahset",
        "hatırla",
        "hatirla",
        "sana",
        "bana",
        "biz",
        "ben",
        "sen",
        "için",
        "icin",
        "olan",
        "olarak",
        "daha",
        "başka",
        "baska",
        "hangi",
        "sorular",
        "sorulari",
        "soruları",
        "sormuştum",
        "sormustum",
        "sordum",
        "lütfen",
        "lutfen",
        "konustuk",
        "konuştuk",
        "konusmustuk",
        "konuşmuştuk",
    }
)


def _looks_like_generic_past_summary(message: str) -> bool:
    blob = _normalize_query(message)
    if any(x in blob for x in ("dun ne", "dün ne", "gecen ne", "geçen ne", "daha once ne", "daha önce ne")):
        return True
    return bool(re.search(r"ne\s+(?:konus|konuş)(?:tuk|tik|mus|muş|mustuk|muştuk)?", blob, re.I))


def _looks_like_question_list_request(message: str) -> bool:
    blob = _normalize_query(message)
    if any(
        x in blob
        for x in (
            "hangi soru",
            "ne sormu",
            "sormustum",
            "sormuştum",
            "sordum",
            "baska hangi",
            "başka hangi",
        )
    ):
        return True
    return bool(re.search(r"(?:baska|başka)\s+hangi\s+(?:soru|konu|mesaj)", blob, re.I))


def _extract_recall_terms(message: str) -> list[str]:
    raw = _normalize_query(message)
    for phrase in (
        "hakkında konuşmuş olabilir miyiz",
        "hakkinda konusmus olabilir miyiz",
        "hakkında konuş",
        "hakkinda konus",
        "konuşmuş olabilir",
        "konusmus olabilir",
        "hatırlıyor musun",
        "hatirliyor musun",
    ):
        raw = raw.replace(phrase, " ")
    terms: list[str] = []
    for word in re.split(r"[^\wçğıöşü]+", raw, flags=re.I):
        w = (word or "").strip().lower()
        if len(w) < 4 or w in _RECALL_STOP:
            continue
        terms.append(w)
        if w.endswith(("larım", "larim", "lerim", "miz", "mız")) and len(w) > 5:
            terms.append(w[:-3])
        elif w.endswith(("ım", "im", "um", "üm")) and len(w) > 4:
            terms.append(w[:-2])
    out: list[str] = []
    seen: set[str] = set()
    for t in terms:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:5]


def _history_from_client(client_history: list | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not client_history:
        return rows
    pending_user = ""
    for item in client_history:
        if isinstance(item, dict):
            role = str(item.get("role") or "").strip().lower()
            content = str(item.get("content") or "").strip()
            if not content:
                continue
            if role == "user":
                pending_user = content
            elif role == "assistant" and pending_user:
                rows.append(
                    {
                        "user": pending_user,
                        "assistant": content,
                        "mode": "genel",
                        "ts": 0.0,
                    }
                )
                pending_user = ""
            continue
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            user = str(item[0] or "").strip()
            assistant = str(item[1] or "").strip()
            if user and assistant:
                rows.append({"user": user, "assistant": assistant, "mode": "genel", "ts": 0.0})
    return rows


def _merge_history_items(
    *,
    disk_items: list[dict[str, Any]],
    client_history: list | None,
    limit: int,
) -> list[dict[str, Any]]:
    client_rows = _history_from_client(client_history)
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in client_rows + list(disk_items or []):
        u = str(row.get("user") or "").strip()
        a = str(row.get("assistant") or "").strip()
        key = f"{u}\0{a}"
        if not u or key in seen:
            continue
        seen.add(key)
        merged.append(row)
        if len(merged) >= limit:
            break
    return merged


def _reply_question_list(items: list[dict[str, Any]]) -> str:
    if not items:
        return (
            "Ümit abi, kayıtlı önceki oturum sohbeti bulamadım — "
            "bugünkü penceredeki konuşmalara bakabiliriz; istersen önemli bir şeyi «hatırla» ile yazdır."
        )
    seen: set[str] = set()
    questions: list[str] = []
    for row in items:
        u = str(row.get("user") or "").strip()
        if not u or u in seen:
            continue
        seen.add(u)
        questions.append(u)
    if not questions:
        return (
            "Ümit abi, kayıtlı soru bulamadım. "
            "Kalıcı not için «hatırla: …» yazabilirsin."
        )
    lines = ["Ümit abi, kayıtlı son sorularından bazıları:", ""]
    for i, q in enumerate(questions[:12], 1):
        lines.append(f"{i}. {q[:160]}")
    lines.append("")
    lines.append(
        "(Bunlar diske kayıtlı son turlar + bu oturumdaki mesajların; "
        "«hatırla» ile yazdıkların kalıcı hafızada da tutulur.)"
    )
    return "\n".join(lines).strip()


def _reply_topic_recall(message: str, items: list[dict[str, Any]]) -> str:
    terms = _extract_recall_terms(message)
    topic_label = ", ".join(terms[:2]) if terms else "bu konu"
    hits: list[dict[str, Any]] = []
    for term in terms or [topic_label]:
        data = search_chat_history(term, limit=6)
        for row in data.get("items") or []:
            hits.append(row)
    hafiza_snip = ""
    try:
        from ilim_assistant.hafiza_i_ruzgar import genel_hafiza_lookup

        for term in terms or [message]:
            ans = genel_hafiza_lookup(term)
            if ans:
                hafiza_snip = str(ans).strip()[:420]
                break
        if not hafiza_snip:
            ans = genel_hafiza_lookup(message)
            if ans:
                hafiza_snip = str(ans).strip()[:420]
    except Exception:
        pass

    if not hits and not hafiza_snip:
        return (
            f"Ümit abi, «{topic_label}» hakkında kayıtlı bir sohbet veya «hatırla» notu bulamadım. "
            "İstersen şimdi anlat — «hatırla: …» ile kalıcı yazabilirim."
        )

    lines = [f"Ümit abi, «{topic_label}» ile ilgili kayıtlarım:", ""]
    if hafiza_snip:
        lines.append(f"· **Kalıcı hafıza:** {hafiza_snip}")
        lines.append("")
    shown = 0
    seen_u: set[str] = set()
    for row in hits:
        u = str(row.get("user_snippet") or row.get("user") or "").strip()
        a = str(row.get("assistant_snippet") or row.get("assistant") or "").strip()
        if not u or u in seen_u:
            continue
        seen_u.add(u)
        lines.append(f"· **Sen:** {u[:140]}")
        if a:
            lines.append(f"  **Rüzgar:** {a[:220]}")
        lines.append("")
        shown += 1
        if shown >= 4:
            break
    if shown == 0 and not hafiza_snip:
        return (
            f"Ümit abi, «{topic_label}» hakkında kayıtlı bir sohbet bulamadım. "
            "İstersen şimdi anlat — «hatırla: …» ile kalıcı yazabilirim."
        )
    lines.append(
        "(Kayıtlar diske yazılan son sohbetler ve «hatırla» notlarından gelir; "
        "bilgisayar kapandıysa yalnızca «hatırla» kalıcıdır.)"
    )
    return "\n".join(lines).strip()


def try_past_conversation_reply(
    message: str,
    *,
    limit: int = 8,
    client_history: list | None = None,
) -> str | None:
    """Geçmiş sohbet / hafıza sorusu — kayıtlı jsonl + oturum geçmişi (LLM beklemeden)."""
    if not chat_history_enabled():
        return None
    try:
        from ilim_assistant.ana_motor_plan import looks_like_past_conversation_query

        if not looks_like_past_conversation_query(message):
            return None
    except Exception:
        return None

    disk = recent_chat_history(limit=max(limit, 30))
    items = _merge_history_items(
        disk_items=list(disk.get("items") or []),
        client_history=client_history,
        limit=max(limit, 30),
    )

    if _looks_like_question_list_request(message):
        return _reply_question_list(items)

    terms = _extract_recall_terms(message)
    if (
        not _looks_like_generic_past_summary(message)
        and (terms or re.search(r"(?:hakkında|hakkinda)\s+konu", _normalize_query(message), re.I))
    ):
        return _reply_topic_recall(message, items)

    if not items:
        return (
            "Ümit abi, kayıtlı önceki oturum sohbeti bulamadım — "
            "bugünkü penceredeki konuşmalara bakabiliriz; istersen önemli bir şeyi «hatırla» ile yazdır."
        )
    lines = [
        "Ümit abi, kayıtlı son sohbetlerden hatırladıklarım:",
        "",
    ]
    for row in items[: min(5, len(items))]:
        u = str(row.get("user") or "").strip()
        a = str(row.get("assistant") or "").strip()
        if not u:
            continue
        lines.append(f"· **Sen:** {u[:120]}")
        if a:
            lines.append(f"  **Rüzgar:** {a[:200]}")
        lines.append("")
    lines.append(
        "(Bunlar diske kayıtlı son turlar; bilgisayar kapandıysa yalnızca «hatırla» ile yazdıkların kalıcıdır.)"
    )
    return "\n".join(lines).strip()


def search_chat_history(
    query: str,
    *,
    limit: int | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    if not chat_history_enabled():
        return {"ok": True, "items": [], "count": 0, "disabled": True}
    q = _normalize_query(query)
    if len(q) < 2:
        return {"ok": False, "error": "sorgu_kisa", "items": [], "count": 0}
    cap = int(limit if limit is not None else _default_limit())
    mode_f = (mode or "").strip().lower()
    hits: list[dict[str, Any]] = []
    for row in _load_entries(limit=_MAX_STORE):
        blob = _normalize_query(
            f"{row.get('user', '')} {row.get('assistant', '')} {row.get('plan_primary', '')}"
        )
        if mode_f and str(row.get("mode") or "").lower() != mode_f:
            continue
        if q not in blob:
            continue
        snippet_u = str(row.get("user") or "")[:160]
        snippet_a = str(row.get("assistant") or "")[:240]
        hits.append(
            {
                "ts": row.get("ts"),
                "mode": row.get("mode"),
                "user_snippet": snippet_u,
                "assistant_snippet": snippet_a,
                "plan_primary": row.get("plan_primary"),
                "session_id": row.get("session_id"),
            }
        )
        if len(hits) >= cap:
            break
    return {
        "ok": True,
        "version": FAZ_AA_CHAT_VERSION,
        "query": query,
        "items": hits,
        "count": len(hits),
    }
