# Created by Ümit & Gökçenur
"""Tek beyin Faz G — uzun oturum özeti, önbellek ve OturumOzet köprüsü."""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

TEK_BEYIN_OZET_VERSION = "tek-beyin-ozet-v1-2026-06-12-faz-g"

_PKG_ROOT = Path(__file__).resolve().parent.parent
_CACHE_PATH = _PKG_ROOT / ".ruzgar" / "tek_beyin_ozet_cache.json"

_SUMMARY_QUERY = re.compile(
    r"(?:"
    r"özetle|ozetle|"
    r"ne\s+konu[sş]tuk|neler\s+konu[sş]tuk|"
    r"bugün\s+ne\s+konu[sş]|bugun\s+ne\s+konus|"
    r"oturum\s+özeti|oturum\s+ozeti|"
    r"konu[sş]ma\s+özeti|konusma\s+ozeti|"
    r"bugünkü\s+sohbet|bugunku\s+sohbet"
    r")",
    re.I,
)


def tek_beyin_ozet_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_TEK_BEYIN_OZET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _min_turns() -> int:
    try:
        return max(6, min(int(os.environ.get("RUZGAR_TEK_BEYIN_OZET_MIN_TURNS", "8")), 24))
    except ValueError:
        return 8


def _sync_every_n() -> int:
    try:
        return max(4, min(int(os.environ.get("RUZGAR_TEK_BEYIN_OZET_SYNC_N", "8")), 20))
    except ValueError:
        return 8


def _clip(text: str, limit: int) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= limit else t[: max(0, limit - 1)].rstrip() + "…"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", (text or "").strip().lower()))


def looks_like_session_summary_query(message: str) -> bool:
    raw = (message or "").strip()
    if len(raw) < 8 or len(raw) > 400:
        return False
    return bool(_SUMMARY_QUERY.search(_norm(raw)))


def _turns_merged(*, history: list | None, disk_limit: int = 24) -> list[dict[str, str]]:
    try:
        from ilim_assistant.ruzgar_tek_beyin_baglam import _turns_from_history
    except Exception:
        _turns_from_history = None  # type: ignore[assignment,misc]

    client_rows: list[dict[str, str]] = []
    if _turns_from_history is not None:
        client_rows = _turns_from_history(history, limit=disk_limit)

    if len(client_rows) >= _min_turns():
        return client_rows[-disk_limit:]

    disk_rows: list[dict[str, str]] = []
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import recent_chat_history

        items = list(recent_chat_history(limit=disk_limit).get("items") or [])
        for row in reversed(items):
            u = str(row.get("user") or "").strip()
            a = str(row.get("assistant") or "").strip()
            if u:
                disk_rows.append({"user": u, "assistant": a})
    except Exception:
        pass
    if not disk_rows and not client_rows:
        return []
    if not client_rows:
        return disk_rows[-disk_limit:]
    seen: set[str] = set()
    merged: list[dict[str, str]] = []
    for row in disk_rows + client_rows:
        u = row.get("user") or ""
        a = row.get("assistant") or ""
        key = f"{u}\0{a}"
        if not u or key in seen:
            continue
        seen.add(key)
        merged.append({"user": u, "assistant": a})
    return merged[-disk_limit:]


def _classify_turn(user_msg: str) -> str:
    try:
        from ilim_assistant.ruzgar_tek_beyin import looks_like_friend_mood_chat

        if looks_like_friend_mood_chat(user_msg):
            return "mood"
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_tek_beyin_oturum import _breaks_mood_thread

        if _breaks_mood_thread(user_msg):
            return "bilgi"
    except Exception:
        pass
    return "sohbet"


def rebuild_session_summary(
    *,
    history: list | None = None,
    session_id: str | None = None,
) -> dict[str, Any] | None:
    """LLM yok — son turlardan yapılandırılmış özet."""
    if not tek_beyin_ozet_enabled():
        return None
    turns = _turns_merged(history=history)
    if len(turns) < _min_turns():
        return None

    topics: list[str] = []
    mood_labels: list[str] = []
    bilgi_arasi: list[str] = []
    seen_topics: set[str] = set()

    try:
        from ilim_assistant.ruzgar_tek_beyin_oturum import _mood_label_for
    except Exception:
        _mood_label_for = lambda _m: "sohbet"  # type: ignore[assignment,misc]

    for row in turns:
        u = str(row.get("user") or "").strip()
        if not u:
            continue
        kind = _classify_turn(u)
        if kind == "mood":
            mood_labels.append(_mood_label_for(u))
            key = _norm(u)[:48]
            if key not in seen_topics:
                seen_topics.add(key)
                topics.append(_clip(u, 56))
        elif kind == "bilgi":
            bilgi_arasi.append(_clip(u, 52))
        else:
            key = _norm(u)[:48]
            if key not in seen_topics:
                seen_topics.add(key)
                topics.append(_clip(u, 56))

    lines: list[str] = []
    if mood_labels:
        lines.append(f"Duygu tonu: {mood_labels[-1]}")
    if topics:
        lines.append("Konuşulan başlıklar: " + "; ".join(topics[-7:]))
    if bilgi_arasi:
        lines.append("Ara bilgi soruları: " + "; ".join(bilgi_arasi[-4:]))
    summary_text = "\n".join(lines).strip()
    if not summary_text:
        return None

    return {
        "version": TEK_BEYIN_OZET_VERSION,
        "updated_at": time.time(),
        "session_id": (session_id or "")[:64] or None,
        "turn_count": len(turns),
        "topics": topics[-10:],
        "mood": mood_labels[-1] if mood_labels else "",
        "bilgi_arasi": bilgi_arasi[-5:],
        "summary_text": summary_text[:1200],
    }


def _load_cache() -> dict[str, Any]:
    if not _CACHE_PATH.is_file():
        return {}
    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(payload: dict[str, Any]) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=0) + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def get_cached_summary() -> dict[str, Any] | None:
    data = _load_cache()
    if not data.get("summary_text"):
        return None
    return data


def load_summary_addon(
    history: list | None,
    *,
    session_id: str | None = None,
) -> str:
    """Faz F bağlamına eklenecek uzun oturum özeti."""
    if not tek_beyin_ozet_enabled():
        return ""
    cached = get_cached_summary()
    if not cached:
        fresh = rebuild_session_summary(history=history, session_id=session_id)
        if not fresh:
            return ""
        cached = fresh
    turns = _turns_merged(history=history)
    if len(turns) < _min_turns():
        return ""
    text = str(cached.get("summary_text") or "").strip()
    if not text:
        return ""
    return (
        "\n\n[UZUN OTURUM ÖZETİ — kullanıcıya aynen okuma]\n"
        + text
        + f"\n(Tur sayısı: {cached.get('turn_count', '?')})\n"
        "[/UZUN OTURUM ÖZETİ]\n"
    )


def _sync_to_oturum_ozet_hafiza(summary: dict[str, Any]) -> dict[str, Any]:
    """Periyodik köprü — OturumOzet motor tipine yaz."""
    try:
        from ilim_assistant.ana_motor_oturum_ozet import oturum_ozet_enabled

        if not oturum_ozet_enabled():
            return {"ok": True, "stored": False, "reason": "oturum_ozet_off"}
    except Exception:
        return {"ok": True, "stored": False, "reason": "import"}
    text = str(summary.get("summary_text") or "").strip()
    if not text:
        return {"ok": True, "stored": False, "reason": "empty"}
    soru = "Tek beyin oturum özeti — güncel"
    cevap = (
        f"Ümit abi ile oturum özeti ({time.strftime('%Y-%m-%d %H:%M')}):\n"
        f"{text}\n\n"
        f"Konular: {'; '.join(summary.get('topics') or [])[:400]}"
    )
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        get_hafiza_motor().ekle_bilgi(soru, cevap[:4000], motor_tipi="OturumOzet")
        return {"ok": True, "stored": True, "version": TEK_BEYIN_OZET_VERSION}
    except Exception as exc:
        return {"ok": False, "stored": False, "error": str(exc)[:120]}


def maybe_refresh_tek_beyin_ozet(
    *,
    user_message: str,
    assistant_message: str,
    history: list | None = None,
    session_id: str | None = None,
    mode_norm: str = "genel",
) -> dict[str, Any]:
    """Tur sonrası önbelleği güncelle; N turda OturumOzet'e yaz."""
    if not tek_beyin_ozet_enabled():
        return {"ok": True, "refreshed": False, "reason": "disabled"}
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return {"ok": True, "refreshed": False, "reason": "mode"}
    user = (user_message or "").strip()
    reply = (assistant_message or "").strip()
    if len(user) < 4 or len(reply) < 8:
        return {"ok": True, "refreshed": False, "reason": "short"}

    summary = rebuild_session_summary(history=history, session_id=session_id)
    if not summary:
        return {"ok": True, "refreshed": False, "reason": "min_turns"}
    _save_cache(summary)

    synced = False
    n = summary.get("turn_count") or 0
    if n >= _min_turns() and n % _sync_every_n() == 0:
        sync_res = _sync_to_oturum_ozet_hafiza(summary)
        synced = bool(sync_res.get("stored"))

    return {
        "ok": True,
        "refreshed": True,
        "synced_hafiza": synced,
        "turn_count": n,
        "version": TEK_BEYIN_OZET_VERSION,
    }


def try_tek_beyin_summary_reply(
    message: str,
    *,
    history: list | None = None,
    session_id: str | None = None,
) -> str | None:
    """«Bugün ne konuştuk özetle» — anında yanıt."""
    if not tek_beyin_ozet_enabled():
        return None
    if not looks_like_session_summary_query(message):
        return None

    summary = rebuild_session_summary(history=history, session_id=session_id)
    if not summary:
        cached = get_cached_summary()
        if cached:
            summary = cached
    if not summary:
        return (
            "Ümit abi, henüz özet çıkaracak kadar uzun bir sohbet yok — "
            "birkaç tur daha konuşunca otomatik özet tutmaya başlarım."
        )

    text = str(summary.get("summary_text") or "").strip()
    topics = summary.get("topics") or []
    lines = [
        "Ümit abi, bugünkü sohbetimizin özeti:",
        "",
        text,
        "",
    ]
    if topics:
        lines.append("**Başlıklar:** " + " · ".join(_clip(t, 48) for t in topics[-6:]))
    lines.append("")
    lines.append(
        f"(Kayıtlı {summary.get('turn_count', '?')} tur; özet otomatik güncellenir.)"
    )
    return "\n".join(lines).strip()


def persist_tek_beyin_turn(
    *,
    user_message: str,
    assistant_message: str,
    history: list | None = None,
    mode_norm: str = "genel",
    session_id: str | None = None,
    plan_primary: str = "",
) -> dict[str, Any]:
    """Erken tek beyin yolları — jsonl + özet önbelleği."""
    out: dict[str, Any] = {"ok": True}
    try:
        from ilim_assistant.ana_motor_sohbet_gecmis import append_chat_turn

        out["chat"] = append_chat_turn(
            user_message=user_message,
            assistant_message=assistant_message,
            mode_norm=mode_norm,
            session_id=session_id,
            plan_primary=plan_primary,
        )
    except Exception as exc:
        out["chat"] = {"ok": False, "error": str(exc)[:80]}
    try:
        out["ozet"] = maybe_refresh_tek_beyin_ozet(
            user_message=user_message,
            assistant_message=assistant_message,
            history=history,
            session_id=session_id,
            mode_norm=mode_norm,
        )
    except Exception as exc:
        out["ozet"] = {"ok": False, "error": str(exc)[:80]}
    return out


def tek_beyin_ozet_status() -> dict[str, Any]:
    cached = get_cached_summary()
    return {
        "enabled": tek_beyin_ozet_enabled(),
        "version": TEK_BEYIN_OZET_VERSION,
        "min_turns": _min_turns(),
        "sync_every_n": _sync_every_n(),
        "cached": bool(cached),
        "cached_turns": int((cached or {}).get("turn_count") or 0),
    }
