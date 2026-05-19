# Created by Umit & Gokcenur
"""Faz 16 — küçük otonom görev yöneticisi.

Kalıcı SQLite görev listesi: Rüzgar uzun işleri kendi durumuyla izleyebilsin.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent
_DB = _PKG_ROOT / "hafiza" / "ruzgar_gorevler.db"
_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_tasks_db() -> None:
    with _LOCK:
        conn = _connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS gorev (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  status TEXT NOT NULL DEFAULT 'pending',
                  created REAL NOT NULL,
                  updated REAL NOT NULL,
                  detail TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_gorev_status ON gorev(status);
                """
            )
            conn.commit()
        finally:
            conn.close()


def create_task(title: str, detail: str = "") -> dict:
    init_tasks_db()
    now = time.time()
    t = (title or "").strip()[:500]
    if not t:
        raise ValueError("Boş görev")
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO gorev (title, status, created, updated, detail)
                VALUES (?, 'pending', ?, ?, ?)
                """,
                (t, now, now, (detail or "").strip()[:2000]),
            )
            conn.commit()
            return {"id": int(cur.lastrowid or 0), "title": t, "status": "pending"}
        finally:
            conn.close()


def list_tasks(limit: int = 50) -> list[dict]:
    init_tasks_db()
    lim = max(1, min(int(limit or 50), 200))
    with _LOCK:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT id, title, status, created, updated, detail
                FROM gorev
                ORDER BY id DESC
                LIMIT ?
                """,
                (lim,),
            ).fetchall()
        finally:
            conn.close()
    return [dict(r) for r in rows]


def update_task(task_id: int, status: str, detail: str | None = None) -> bool:
    init_tasks_db()
    st = (status or "").strip().lower()
    if st not in {"pending", "in_progress", "done", "blocked", "cancelled"}:
        raise ValueError("Geçersiz görev durumu")
    with _LOCK:
        conn = _connect()
        try:
            if detail is None:
                cur = conn.execute(
                    "UPDATE gorev SET status = ?, updated = ? WHERE id = ?",
                    (st, time.time(), int(task_id)),
                )
            else:
                cur = conn.execute(
                    "UPDATE gorev SET status = ?, detail = ?, updated = ? WHERE id = ?",
                    (st, detail[:2000], time.time(), int(task_id)),
                )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def delete_task(task_id: int) -> bool:
    init_tasks_db()
    with _LOCK:
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM gorev WHERE id = ?", (int(task_id),))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def try_consume_task_command(message: str) -> str | None:
    raw = (message or "").strip()
    low = raw.casefold()
    prefixes = (
        "görev oluştur",
        "gorev olustur",
        "görev ekle",
        "gorev ekle",
    )
    if any(low.startswith(p) for p in prefixes):
        title = (
            raw.split(":", 1)[1].strip()
            if ":" in raw
            else raw.split(maxsplit=2)[-1].strip()
        )
        if len(title) < 3:
            return "Mimar, görev başlığını biraz daha açık yazar mısın?"
        task = create_task(title)
        return f"Görev oluşturdum Mimar: #{task['id']} — {task['title']}"
    list_cues = {
        "görevleri göster",
        "gorevleri goster",
        "görev listesi",
        "gorev listesi",
    }
    if low in list_cues:
        tasks = list_tasks(10)
        if not tasks:
            return "Kayıtlı görev yok Mimar."
        lines = ["Son görevler:"]
        for t in tasks:
            lines.append(f"- #{t['id']} [{t['status']}] {t['title']}")
        return "\n".join(lines)
    return None
