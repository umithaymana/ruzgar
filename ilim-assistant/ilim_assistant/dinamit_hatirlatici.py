"""
Zamanlanmış hatırlatıcı — doğal dil zamanı ayrıştırma + SQLite + arka plan tetik.
Dinamit Geliştirme — Ümit & Gökçenur.
"""

from __future__ import annotations

import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent
_DB = _PKG_ROOT / "hafiza" / "dinamit_hatirlatici.db"
_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_hatirlatici_db() -> None:
    with _LOCK:
        conn = _connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS hatirlatici (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fire_at REAL NOT NULL,
                  mesaj TEXT NOT NULL,
                  created REAL NOT NULL,
                  tetiklendi INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_hat_fire ON hatirlatici(fire_at);
                """
            )
            conn.commit()
        finally:
            conn.close()


@dataclass
class ParsedSchedule:
    delay_sec: float
    reminder_text: str


_REMIND_PATTERNS = [
    re.compile(
        r"(?i)(?:hat[ıi]rlat|zamanlay|alarm|kur)[^\n]{0,40}?"
        r"(?P<num>\d+)\s*(?P<unit>dakika|dk|dak\.|saat|s)\b[^\n]{0,80}?"
        r"(?::|—|-|–)?\s*(?P<msg>.+)$"
    ),
    re.compile(
        r"(?i)(?P<num>\d+)\s*(?P<unit>dakika|dk|dak\.|saat|s)\b[^\n]{0,48}?"
        r"(?:sonra|içinde)[^\n]{0,48}?(?P<msg>.+)$"
    ),
]


def try_parse_schedule(message: str) -> ParsedSchedule | None:
    """Basit Türkçe zaman + hatırlatılacak metin."""
    t = (message or "").strip()
    if not t:
        return None
    low = t.lower()
    if not any(
        k in low
        for k in (
            "hatırlat",
            "hatirlat",
            "zamanla",
            "alarm",
            "kur ",
            " sonra ",
            " dakika ",
            " dakika",
            " saat ",
            "saat",
        )
    ):
        return None

    for i, rx in enumerate(_REMIND_PATTERNS):
        m = rx.search(t)
        if not m:
            continue
        if i == 1 and not re.search(r"(?i)hat[ıi]rlat|hatirlatici", t):
            continue
        g = m.groupdict()
        try:
            num = int(g.get("num") or "0")
        except ValueError:
            continue
        if num <= 0 or num > 500:
            continue
        unit = (g.get("unit") or "dakika").lower()
        if unit in ("saat", "s"):
            sec = float(num * 3600)
        else:
            sec = float(num * 60)
        msg = (g.get("msg") or "").strip()
        msg = re.sub(r"^(?:bana|şunu|bunu|ki)\s+", "", msg, flags=re.I).strip()
        msg = re.sub(r"(?i)hat[ıi]rlat\s*[.:]?\s*", "", msg).strip()
        msg = msg.strip(" \t.:;!?")
        if len(msg) < 2:
            msg = "Hatırlatma zamanı geldi."
        return ParsedSchedule(delay_sec=sec, reminder_text=msg[:2000])

    # "yarın" → 24 saat
    if re.search(
        r"(?i)(hat[ıi]rlat|alarm|zamanla).{0,30}yar[ıi]n", t
    ) and len(t) < 400:
        msg = re.split(r"(?i)(?:için|şu|bu|—|:)", t, maxsplit=1)
        tail = msg[1] if len(msg) > 1 else "Yarın hatırlat"
        tail = re.sub(r"^(?:şunu|bunu|ki)\s*", "", tail.strip()).strip()[:2000]
        return ParsedSchedule(delay_sec=86400.0, reminder_text=tail or "Yarın hatırlat")

    m2 = re.search(
        r"(?i)(?P<num>\d+)\s*(?P<unit>dakika|dk|dak\.|saat|s)\b\s+sonra\s*(?:[:#\-–]\s*)?(?P<msg>.+)",
        t,
    )
    if m2 and re.search(r"(?i)hat[ıi]rlat|hatirlatici", t):
        try:
            num = int(m2.group("num") or "0")
        except ValueError:
            num = 0
        if 0 < num <= 500:
            unit = (m2.group("unit") or "dakika").lower()
            sec = float(num * 3600) if unit in ("saat", "s") else float(num * 60)
            msg = (m2.group("msg") or "").strip()
            msg = re.sub(r"(?i)^(?:bana|şunu|bunu|ki)\s+", "", msg).strip()
            msg = re.sub(r"(?i)hat[ıi]rlat\s*[.:]?\s*", "", msg).strip()
            if len(msg) < 2:
                msg = "Hatırlatma zamanı geldi."
            return ParsedSchedule(delay_sec=sec, reminder_text=msg[:2000])
    return None


def insert_reminder(fire_at_epoch: float, mesaj: str) -> int:
    init_hatirlatici_db()
    now = time.time()
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO hatirlatici (fire_at, mesaj, created, tetiklendi)
                VALUES (?, ?, ?, 0)
                """,
                (fire_at_epoch, mesaj, now),
            )
            conn.commit()
            return int(cur.lastrowid or 0)
        finally:
            conn.close()


def fetch_due_reminders(now_epoch: float | None = None) -> list[dict]:
    init_hatirlatici_db()
    now = now_epoch or time.time()
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                SELECT id, fire_at, mesaj FROM hatirlatici
                WHERE tetiklendi = 0 AND fire_at <= ?
                ORDER BY fire_at ASC
                LIMIT 20
                """,
                (now,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
    return [
        {
            "id": int(r["id"]),
            "fire_at": float(r["fire_at"]),
            "mesaj": str(r["mesaj"]),
        }
        for r in rows
    ]


def mark_triggered(row_id: int) -> None:
    init_hatirlatici_db()
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE hatirlatici SET tetiklendi = 1 WHERE id = ?",
                (row_id,),
            )
            conn.commit()
        finally:
            conn.close()


_bg_started = False
_bg_lock = threading.Lock()


def start_reminder_background_thread(app_poll_interval: float = 1.0) -> None:
    """Şu an için yalnızca init; tetikleme HTTP ile client poll üzerinden."""
    global _bg_started
    with _bg_lock:
        if _bg_started:
            return
        init_hatirlatici_db()
        _bg_started = True


def ack_message_for_user(parsed: ParsedSchedule, row_id: int) -> str:
    mins = parsed.delay_sec / 60.0
    if mins >= 120:
        timestr = f"{mins / 60:.1f} saat"
    else:
        timestr = f"{mins:.0f} dakika"
    return (
        f"Mimar, hatırlatıcı kuruldu — **{timestr}** sonra: «{parsed.reminder_text[:180]}». "
        f"(id #{row_id}, Dinamit hatırlatıcı — Ümit & Gökçenur)"
    )


def try_consume_hatirlatici_intent(message: str) -> str | None:
    """Mesaj hatırlatıcı niyetiyse kaydeder ve kullanıcıya tek cümle döner; değilse None."""
    ps = try_parse_schedule(message)
    if not ps:
        return None
    when = time.time() + ps.delay_sec
    rid = insert_reminder(when, ps.reminder_text)
    return ack_message_for_user(ps, rid)
