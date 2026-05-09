"""
Kuvve-i Hafıza — kalıcı hatıra ve kişisel veri (SQLite).
Ümit & Gökçenur — RÜZGAR çekirdeği.
"""

from __future__ import annotations

import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.Lock()

# ilim-assistant/hafiza/gecmis_sohbetler.db (ASCII klasör — Windows uyumu)
_PKG_ROOT = Path(__file__).resolve().parent.parent
_HAFIZA_DIR = _PKG_ROOT / "hafiza"
DB_PATH = _HAFIZA_DIR / "gecmis_sohbetler.db"

_KISISEL_KEYS = (
    "umit_arastirma",
    "gokcenur_eserler",
    "notlar",
)


def _enabled() -> bool:
    return os.environ.get("KUVVE_HAFIZA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _connect() -> sqlite3.Connection:
    _HAFIZA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    if not _enabled():
        return
    with _LOCK:
        conn = _connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sohbet (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts TEXT NOT NULL,
                  role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                  content TEXT NOT NULL,
                  mode TEXT,
                  altin INTEGER NOT NULL DEFAULT 0,
                  silindi INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_sohbet_ts ON sohbet(ts DESC);
                CREATE INDEX IF NOT EXISTS idx_sohbet_silindi ON sohbet(silindi);

                CREATE TABLE IF NOT EXISTS kisisel_veri (
                  k TEXT PRIMARY KEY,
                  v TEXT,
                  guncelleme TEXT
                );
                """
            )
            conn.commit()
        finally:
            conn.close()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_PIN_RE = re.compile(
    r"^(?:\s*)(bunu\s+unutma|şunu\s+unutma|bunu\s+kalıcı\s+tut|"
    r"kalıcıya\s+al|unutma\s+bunu|hatırla\s+bunu)(\s*[.!?…]*)?\s*$",
    re.IGNORECASE | re.UNICODE,
)


def is_pin_only_message(text: str) -> bool:
    t = (text or "").strip()
    if len(t) > 80:
        return False
    return bool(_PIN_RE.match(t))


def _pin_latest_assistant_row(conn: sqlite3.Connection) -> int | None:
    cur = conn.execute(
        """
        SELECT id FROM sohbet
        WHERE silindi = 0 AND role = 'assistant'
        ORDER BY id DESC LIMIT 1
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    aid = int(row["id"])
    conn.execute(
        "UPDATE sohbet SET altin = 1 WHERE id = ? AND silindi = 0",
        (aid,),
    )
    return aid


def persist_turn(
    user_text: str,
    assistant_full: str,
    mode: str,
    *,
    also_pin_previous_assistant: bool = False,
) -> None:
    """Konuşma turunu kaydeder; pin niyetinde önceki asistan cevabını altınlar."""
    if not _enabled():
        return
    init_db()
    u = (user_text or "").strip()
    a = assistant_full or ""
    m = (mode or "genel").strip()
    with _LOCK:
        conn = _connect()
        try:
            if also_pin_previous_assistant and u:
                _pin_latest_assistant_row(conn)
            conn.execute(
                """
                INSERT INTO sohbet (ts, role, content, mode, altin, silindi)
                VALUES (?, 'user', ?, ?, 0, 0)
                """,
                (_utc_now_iso(), u, m),
            )
            conn.execute(
                """
                INSERT INTO sohbet (ts, role, content, mode, altin, silindi)
                VALUES (?, 'assistant', ?, ?, 0, 0)
                """,
                (_utc_now_iso(), a, m),
            )
            conn.commit()
        finally:
            conn.close()


def mark_turn_altin(sohbet_id: int, altin: bool = True) -> bool:
    if not _enabled():
        return False
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                UPDATE sohbet SET altin = ?
                WHERE id = ? AND silindi = 0
                """,
                (1 if altin else 0, sohbet_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def soft_delete_turn(sohbet_id: int) -> bool:
    if not _enabled():
        return False
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                "UPDATE sohbet SET silindi = 1 WHERE id = ?",
                (sohbet_id,),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def list_sohbet(limit: int = 80) -> list[dict]:
    if not _enabled():
        return []
    init_db()
    lim = max(1, min(int(limit), 500))
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                SELECT id, ts, role, content, mode, altin
                FROM sohbet
                WHERE silindi = 0
                ORDER BY id DESC
                LIMIT ?
                """,
                (lim,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
    out: list[dict] = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "ts": r["ts"],
                "role": r["role"],
                "content": r["content"],
                "mode": r["mode"] or "",
                "altin": bool(r["altin"]),
            }
        )
    return out


def get_last_exchange_summary() -> tuple[str | None, str | None]:
    """Son tur: kullanıcı sorusu + asistan yanıtı (hatırlatma özeti için)."""
    if not _enabled():
        return None, None
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                SELECT role, content FROM sohbet
                WHERE silindi = 0
                ORDER BY id DESC
                LIMIT 2
                """
            )
            rows = list(cur.fetchall())
        finally:
            conn.close()
    if len(rows) >= 2:
        newest, prev = rows[0], rows[1]
        if newest["role"] == "assistant" and prev["role"] == "user":
            return (prev["content"] or "").strip(), (newest["content"] or "").strip()
    if len(rows) == 1:
        r0 = rows[0]
        if r0["role"] == "user":
            return (r0["content"] or "").strip(), None
        return None, (r0["content"] or "").strip()
    return None, None


def _local_date(iso_ts: str) -> str | None:
    try:
        if iso_ts.endswith("Z"):
            dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d")
    except Exception:
        return None


def get_startup_reminder() -> str | None:
    """Son oturumdan kısa hatırlatma; boşsa None."""
    if not _enabled():
        return None
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                SELECT ts FROM sohbet
                WHERE silindi = 0
                ORDER BY id DESC LIMIT 1
                """
            )
            last = cur.fetchone()
        finally:
            conn.close()
    if not last:
        return None
    last_ts = last["ts"]
    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    last_day = _local_date(last_ts)
    if not last_day:
        return None
    try:
        gap_days = (
            datetime.strptime(today, "%Y-%m-%d")
            - datetime.strptime(last_day, "%Y-%m-%d")
        ).days
    except Exception:
        gap_days = 0

    user_text, asst_text = get_last_exchange_summary()
    if not user_text and not asst_text:
        return None

    if gap_days >= 1:
        gun = "dün" if gap_days == 1 else f"{gap_days} gün önce"
    else:
        # aynı gün: yine de son konuşmayı nazikçe an
        gun = "biraz önce"

    snippet = (user_text or "")[:160]
    if len(user_text or "") > 160:
        snippet += "…"
    if not snippet.strip() and asst_text:
        snippet = (asst_text or "")[:160]
        if len(asst_text or "") > 160:
            snippet += "…"

    return (
        f"Mimar, {gun} şu konuda kalmıştık — «{snippet}» — devam edelim mi? "
        f"(Kuvve-i Hafıza — Ümit & Gökçenur)"
    )


def _get_kisisel_map() -> dict[str, str]:
    init_db()
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute("SELECT k, v FROM kisisel_veri")
            rows = cur.fetchall()
        finally:
            conn.close()
    return {r["k"]: (r["v"] or "") for r in rows}


def set_kisisel(data: dict[str, str | None]) -> dict[str, str]:
    if not _enabled():
        return {}
    init_db()
    now = _utc_now_iso()
    with _LOCK:
        conn = _connect()
        try:
            for key in _KISISEL_KEYS:
                if key not in data:
                    continue
                val = data.get(key)
                if val is None:
                    continue
                conn.execute(
                    """
                    INSERT INTO kisisel_veri (k, v, guncelleme)
                    VALUES (?, ?, ?)
                    ON CONFLICT(k) DO UPDATE SET v = excluded.v, guncelleme = excluded.guncelleme
                    """,
                    (key, str(val), now),
                )
            conn.commit()
        finally:
            conn.close()
    return get_kisisel_panel()


def get_kisisel_panel() -> dict[str, str]:
    m = _get_kisisel_map()
    return {
        "umit_arastirma": m.get("umit_arastirma", ""),
        "gokcenur_eserler": m.get("gokcenur_eserler", ""),
        "notlar": m.get("notlar", ""),
    }


def format_prompt_memory_block() -> str:
    """MODEle gidecek kısa [HAFIZA] bloğu — altın kayıtlar + kişisel panel."""
    if not _enabled():
        return ""
    init_db()
    parts: list[str] = []

    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                SELECT role, content FROM sohbet
                WHERE silindi = 0 AND altin = 1
                ORDER BY id DESC
                LIMIT 8
                """
            )
            gold = cur.fetchall()
        finally:
            conn.close()

    if gold:
        lines = []
        for r in gold:
            role = r["role"]
            c = (r["content"] or "").strip()
            if not c:
                continue
            c = c[:600]
            if len(r["content"] or "") > 600:
                c += "…"
            lines.append(f"- ({role}) {c}")
        if lines:
            parts.append(
                "[HAFIZA — altın (kalıcı hatırlat)]\n" + "\n".join(lines)
            )

    k = get_kisisel_panel()
    kv_bits: list[str] = []
    if k.get("umit_arastirma", "").strip():
        kv_bits.append(
            f"Ümit araştırma tercihleri: {k['umit_arastirma'].strip()[:800]}"
        )
    if k.get("gokcenur_eserler", "").strip():
        kv_bits.append(
            f"Gökçenur sevdiği eserler: {k['gokcenur_eserler'].strip()[:800]}"
        )
    if k.get("notlar", "").strip():
        kv_bits.append(f"Notlar: {k['notlar'].strip()[:600]}")
    if kv_bits:
        parts.append(
            "[HAFIZA — kişisel veri paneli — Ümit & Gökçenur]\n"
            + "\n".join(kv_bits)
        )

    if not parts:
        return ""
    return (
        "\n\n".join(parts)
        + "\n\n[TALİMAT — HAFIZA]\n"
        "Bu blok kullanıcının kaydettiği tercih ve kalıcı hatırlatlardır; "
        "doğrudan çelişki yoksa yanıtta nazikçe dikkate al.\n"
    )


# İlk importta tabloları oluştur
try:
    if _enabled():
        init_db()
except Exception:
    pass
