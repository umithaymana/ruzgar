# Created by Ümit & Gökçenur
"""Ana Motor Faz Q3 — timeline olaylarından otomatik «hatırla» tetikleme."""

from __future__ import annotations

import os
from typing import Any

_REMEMBER_TYPES = frozenset(
    {"archived", "restored", "merged", "auto_paket", "active_session"}
)


def timeline_remember_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_TIMELINE_REMEMBER", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _max_batch() -> int:
    try:
        return max(1, min(10, int(os.environ.get("RUZGAR_ANA_TIMELINE_REMEMBER_MAX", "5"))))
    except ValueError:
        return 5


def run_timeline_remember(
    session_id: str,
    *,
    topic: str = "",
    upload_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Tek oturumu timeline bağlamından hafızaya yaz."""
    if not timeline_remember_enabled():
        return {"ok": False, "error": "Timeline hatırla köprüsü kapalı."}
    sid = (session_id or "").strip()
    if not sid:
        return {"ok": False, "error": "session_id gerekli."}
    from ilim_assistant.ana_motor_session_hafiza import remember_upload_session

    label = (topic or f"Timeline hatırla — {sid[:8]}").strip()[:200]
    result = remember_upload_session(sid, upload_ids=upload_ids, topic=label)
    try:
        from ilim_assistant.ana_motor_hatirla_gecmis import append_remember_history

        append_remember_history(
            session_id=sid,
            topic=label,
            file_count=result.get("file_count"),
            ok=bool(result.get("ok")),
            source="timeline_single",
        )
    except Exception:
        pass
    return result


def auto_remember_from_timeline(*, limit: int | None = None) -> dict[str, Any]:
    """Son timeline olaylarından uygun oturumları hafızaya yaz."""
    if not timeline_remember_enabled():
        return {"ok": False, "error": "Timeline hatırla köprüsü kapalı."}
    cap = int(limit if limit is not None else _max_batch())
    from ilim_assistant.ana_motor_oturum_timeline import build_session_timeline

    tl = build_session_timeline(limit=60)
    events = list(tl.get("events") or [])
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    for ev in events:
        etype = str(ev.get("type") or "")
        if etype not in _REMEMBER_TYPES:
            continue
        sid = str(ev.get("session_id") or "").strip()
        if not sid or sid in seen:
            continue
        seen.add(sid)
        topic = str(ev.get("topic") or ev.get("label") or f"Timeline — {etype}")[:200]
        rr = run_timeline_remember(sid, topic=topic)
        results.append({"session_id": sid, "event_type": etype, **rr})
        if not rr.get("ok"):
            errors.append(f"{sid[:8]}: {rr.get('error') or 'hata'}")
        if len(results) >= cap:
            break

    ok_count = sum(1 for r in results if r.get("ok"))
    if not results:
        return {
            "ok": False,
            "error": "Hatırlanacak timeline oturumu bulunamadı.",
            "attempted": 0,
        }
    return {
        "ok": ok_count > 0,
        "remembered_count": ok_count,
        "attempted": len(results),
        "results": results,
        "errors": errors,
        "hint": f"Timeline'dan {ok_count}/{len(results)} oturum hafızaya yazıldı.",
    }
