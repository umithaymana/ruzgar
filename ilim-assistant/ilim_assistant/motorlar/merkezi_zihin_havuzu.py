# Created by Ümit & Gökçenur
"""
Merkezi Zihin Havuzu — birleşik bellek yönetim merkezi.

SQLite (motor notları + paylaşımlı bağlam) + JSON depoları + RAG köprüsü.
Tüm yardımcı motorlar ``get_havuz()`` üzerinden okur/yazar.

Uyum: ``local_tools`` (güvenli dosya I/O), ``approved_executor`` (onaylı preset'ler).
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Literal

from ilim_assistant.approved_executor import run_preset as _run_preset
from ilim_assistant.local_tools import (
    safe_read_file_under_root,
    safe_write_file_under_root,
)

MIMAR_IMZA = "Ümit & Gökçenur"
SCHEMA_VERSION = 1

MotorAdi = Literal[
    "ses",
    "video",
    "okuma",
    "bilim",
    "tercume",
    "programlama",
    "gelisim",
    "hizir",
    "ana_motor",
    "sistem",
]

_JSON_STORE_FILES: dict[str, str] = {
    "merkezi_bellek": "merkezi_bellek.json",
    "ruzgar_genel": "ruzgar_genel_hafiza.json",
    "programlama": "programlama_hafiza.json",
    "video": "video_hafiza.json",
    "hafiza_arsivi": "hafiza_arsivi.json",
}

_LOCK = threading.RLock()
_INSTANCE: MerkeziZihinHavuzu | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _enabled() -> bool:
    return os.environ.get("RUZGAR_MERKEZI_ZIHIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def merkezi_zihin_defaults_enabled() -> bool:
    return _enabled()


def include_all_modes_in_pool() -> bool:
    return os.environ.get(
        "RUZGAR_MERKEZI_ZIHIN_INCLUDE_ALL_MODES", "0"
    ).strip().lower() in ("1", "true", "yes")


def no_rag_modes() -> frozenset[str]:
    if merkezi_zihin_defaults_enabled() and include_all_modes_in_pool():
        return frozenset()
    return frozenset({"ses", "uretim", "video", "hizli"})


def model_directive_for_unified_retrieval() -> str:
    if not merkezi_zihin_defaults_enabled():
        return ""
    return (
        "\n\n[TALİMAT — Merkezi Zihin Havuzu — Ümit & Gökçenur]\n"
        "Yerel metin bağlamı **tek indeks**: Genel külliyat, İlim Hazinesi ve "
        "**Arşiv** (tasavvuf vb.) ortak havuzdadır — uygun olduğunda bu kaynakları dikkate al. "
        "Kullanıcı yalın günlük sohbet ediyorsa gereksiz ders / tahlil açma.\n"
    )


@dataclass
class SharedContextEntry:
    source_motor: str
    key: str
    value: str
    ts: str
    priority: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_motor": self.source_motor,
            "key": self.key,
            "value": self.value,
            "ts": self.ts,
            "priority": self.priority,
        }


@dataclass
class ExecResult:
    preset: str
    exit_code: int
    output: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


@dataclass
class HavuzSnapshot:
    shared_context: list[SharedContextEntry] = field(default_factory=list)
    rag_hits: list[tuple[str, str, float]] = field(default_factory=list)
    json_stores_loaded: list[str] = field(default_factory=list)


class MerkeziZihinHavuzu:
    """
    Merkezi bellek yönetim merkezi.

    - SQLite: paylaşımlı bağlam penceresi + motor bazlı anahtar-değer
    - JSON: bilinen havuz dosyalarına birleşik erişim
    - RAG: ``rag_store`` köprüsü
    - Dosya/exec: ``local_tools`` + ``approved_executor``
    """

    def __init__(self, workspace_root: str | Path | None = None) -> None:
        self._pkg_root = Path(__file__).resolve().parents[1]
        self._ilim_root = self._pkg_root.parent
        self._repo_root = self._resolve_repo_root(workspace_root)
        self._db_path = self._ilim_root / "hafiza" / "merkezi_zihin_havuzu.db"
        self._buffer_hot: deque[SharedContextEntry] = deque(
            maxlen=max(16, int(os.environ.get("RUZGAR_SHARED_BUFFER_HOT", "48")))
        )
        self._init_sqlite()
        self._hydrate_buffer_from_db()

    @property
    def ilim_root(self) -> Path:
        return self._ilim_root

    @property
    def repo_root(self) -> Path | None:
        return self._repo_root

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _resolve_repo_root(self, workspace_root: str | Path | None) -> Path | None:
        raw = (
            str(workspace_root).strip()
            if workspace_root is not None
            else ""
        )
        if not raw:
            raw = (
                os.environ.get("RUZGAR_EXEC_CWD", "").strip()
                or os.environ.get("LOCAL_TOOLS_ROOT", "").strip()
            )
        if raw:
            p = Path(raw)
            if p.is_dir():
                return p.resolve()
        parent = self._ilim_root.parent
        return parent.resolve() if parent.is_dir() else None

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self) -> None:
        with _LOCK:
            conn = self._connect()
            try:
                conn.executescript(
                    f"""
                    PRAGMA journal_mode=WAL;
                    CREATE TABLE IF NOT EXISTS meta (
                      k TEXT PRIMARY KEY,
                      v TEXT NOT NULL
                    );
                    INSERT OR IGNORE INTO meta (k, v) VALUES ('schema_version', '{SCHEMA_VERSION}');

                    CREATE TABLE IF NOT EXISTS shared_context (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ts TEXT NOT NULL,
                      source_motor TEXT NOT NULL,
                      ctx_key TEXT NOT NULL,
                      value TEXT NOT NULL,
                      priority INTEGER NOT NULL DEFAULT 0,
                      expires_at TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_shared_ts ON shared_context(ts DESC);
                    CREATE INDEX IF NOT EXISTS idx_shared_motor ON shared_context(source_motor);

                    CREATE TABLE IF NOT EXISTS motor_kv (
                      motor TEXT NOT NULL,
                      kv_key TEXT NOT NULL,
                      value TEXT NOT NULL,
                      updated_at TEXT NOT NULL,
                      PRIMARY KEY (motor, kv_key)
                    );
                    """
                )
                conn.commit()
            finally:
                conn.close()

    def _hydrate_buffer_from_db(self) -> None:
        for row in self._fetch_shared_rows(limit=int(os.environ.get("RUZGAR_BUFFER_HYDRATE", "24"))):
            self._buffer_hot.append(row)

    def _fetch_shared_rows(self, limit: int = 20) -> list[SharedContextEntry]:
        now = _utc_now_iso()
        with _LOCK:
            conn = self._connect()
            try:
                cur = conn.execute(
                    """
                    SELECT ts, source_motor, ctx_key, value, priority
                    FROM shared_context
                    WHERE expires_at IS NULL OR expires_at > ?
                    ORDER BY priority DESC, ts DESC
                    LIMIT ?
                    """,
                    (now, max(1, min(limit, 200))),
                )
                return [
                    SharedContextEntry(
                        source_motor=str(r["source_motor"]),
                        key=str(r["ctx_key"]),
                        value=str(r["value"]),
                        ts=str(r["ts"]),
                        priority=int(r["priority"] or 0),
                    )
                    for r in cur.fetchall()
                ]
            finally:
                conn.close()

    # --- Paylaşımlı bağlam penceresi (Shared Context Buffer) ---

    def publish_shared(
        self,
        source_motor: str,
        key: str,
        value: str,
        *,
        priority: int = 0,
        ttl_sec: int | None = None,
    ) -> SharedContextEntry:
        """Bir motorun kritik bulgusunu tüm motorların görebileceği havuza yazar."""
        ts = _utc_now_iso()
        expires: str | None = None
        if ttl_sec is not None and ttl_sec > 0:
            exp = datetime.now(timezone.utc) + timedelta(seconds=ttl_sec)
            expires = exp.strftime("%Y-%m-%dT%H:%M:%SZ")

        entry = SharedContextEntry(
            source_motor=(source_motor or "sistem").strip()[:64],
            key=(key or "not").strip()[:128],
            value=(value or "").strip()[:12000],
            ts=ts,
            priority=int(priority),
        )

        with _LOCK:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO shared_context (ts, source_motor, ctx_key, value, priority, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (ts, entry.source_motor, entry.key, entry.value, entry.priority, expires),
                )
                conn.commit()
            finally:
                conn.close()

        self._buffer_hot.appendleft(entry)
        return entry

    def read_shared(self, limit: int = 20) -> list[SharedContextEntry]:
        """Paylaşımlı bağlam girdileri (SQLite + sıcak önbellek birleşimi)."""
        db_rows = self._fetch_shared_rows(limit=limit)
        seen: set[tuple[str, str, str]] = set()
        out: list[SharedContextEntry] = []
        for e in list(self._buffer_hot) + db_rows:
            sig = (e.ts, e.source_motor, e.key)
            if sig in seen:
                continue
            seen.add(sig)
            out.append(e)
            if len(out) >= limit:
                break
        out.sort(key=lambda x: (-x.priority, x.ts), reverse=False)
        return out[:limit]

    def format_shared_context_block(
        self,
        *,
        consumer_motor: str | None = None,
        limit: int = 12,
    ) -> str:
        """LLM / motor bağlamına eklenecek paylaşımlı pencere metni."""
        rows = self.read_shared(limit=limit)
        if not rows:
            return ""

        lines = [
            "[MERKEZİ ZİHİN — Paylaşımlı Bağlam Penceresi — Ümit & Gökçenur]",
        ]
        if consumer_motor:
            lines.append(f"Tüketici motor: {consumer_motor}")
        for e in rows:
            preview = e.value if len(e.value) <= 900 else e.value[:900] + "…"
            lines.append(
                f"• [{e.source_motor}] {e.key} (öncelik={e.priority}, {e.ts})\n{preview}"
            )
        lines.append(
            "[/MERKEZİ ZİHİN — Paylaşımlı Bağlam]\n"
            "Üstteki maddeler diğer motorların bu oturumda yayınladığı kritik bulgulardır; "
            "çelişki varsa belirt ve birleştir.\n"
        )
        return "\n".join(lines) + "\n"

    def clear_expired_shared(self) -> int:
        now = _utc_now_iso()
        with _LOCK:
            conn = self._connect()
            try:
                cur = conn.execute(
                    "DELETE FROM shared_context WHERE expires_at IS NOT NULL AND expires_at <= ?",
                    (now,),
                )
                conn.commit()
                return int(cur.rowcount)
            finally:
                conn.close()

    # --- Motor KV (SQLite) ---

    def motor_set(self, motor: str, key: str, value: Any) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        ts = _utc_now_iso()
        with _LOCK:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO motor_kv (motor, kv_key, value, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(motor, kv_key) DO UPDATE SET
                      value = excluded.value,
                      updated_at = excluded.updated_at
                    """,
                    ((motor or "sistem")[:64], (key or "default")[:128], payload, ts),
                )
                conn.commit()
            finally:
                conn.close()

    def motor_get(self, motor: str, key: str, default: Any = None) -> Any:
        with _LOCK:
            conn = self._connect()
            try:
                cur = conn.execute(
                    "SELECT value FROM motor_kv WHERE motor = ? AND kv_key = ?",
                    ((motor or "sistem")[:64], (key or "default")[:128]),
                )
                row = cur.fetchone()
            finally:
                conn.close()
        if not row:
            return default
        try:
            return json.loads(str(row["value"]))
        except json.JSONDecodeError:
            return default

    # --- JSON katmanı ---

    def json_store_path(self, store_name: str) -> Path:
        fname = _JSON_STORE_FILES.get(store_name)
        if not fname:
            raise KeyError(f"Bilinmeyen JSON havuzu: {store_name}")
        return self._ilim_root / fname

    def json_load(self, store_name: str, default: Any | None = None) -> Any:
        p = self.json_store_path(store_name)
        if not p.is_file():
            return default if default is not None else {}
        try:
            raw = p.read_text(encoding="utf-8")
            if not raw.strip():
                return default if default is not None else {}
            return json.loads(raw)
        except (OSError, json.JSONDecodeError):
            return default if default is not None else {}

    def json_save(self, store_name: str, data: Any) -> bool:
        p = self.json_store_path(store_name)
        try:
            text = json.dumps(data, ensure_ascii=False, indent=2)
            tmp = p.parent / f".{p.name}.{os.getpid()}.tmp"
            tmp.write_text(text, encoding="utf-8", newline="\n")
            tmp.replace(p)
            return True
        except OSError:
            return False

    def json_patch_key(self, store_name: str, key: str, value: Any) -> bool:
        doc = self.json_load(store_name, default={})
        if not isinstance(doc, dict):
            doc = {}
        doc[key] = value
        return self.json_save(store_name, doc)

    def load_merkezi_bellek(self) -> dict[str, Any]:
        """HIZIR ``merkezi_bellek.json`` — mevcut migrasyon mantığı korunur."""
        try:
            from ilim_assistant.hizir.bellek import load_merkezi_bellek

            return load_merkezi_bellek()
        except Exception:
            return self.json_load("merkezi_bellek", default={})

    def save_merkezi_bellek(self, doc: dict[str, Any]) -> None:
        try:
            from ilim_assistant.hizir.bellek import save_merkezi_bellek

            save_merkezi_bellek(doc)
        except Exception:
            self.json_save("merkezi_bellek", doc)

    # --- RAG katmanı ---

    def rag_search(
        self,
        query: str,
        *,
        top_k: int = 4,
        archive: bool = False,
    ) -> list[tuple[str, str, float]]:
        if not _enabled() or not (query or "").strip():
            return []
        k = max(1, min(int(top_k), 12))
        try:
            if archive:
                from ilim_assistant.rag_store import search_arsiv

                return list(search_arsiv(query, top_k=k))
            from ilim_assistant.rag_store import search

            return list(search(query, top_k=k))
        except Exception:
            return []

    def rag_context_block(self, query: str, *, top_k: int = 4, archive: bool = False) -> str:
        hits = self.rag_search(query, top_k=top_k, archive=archive)
        if not hits:
            return ""
        lines = ["[MERKEZİ ZİHİN — RAG bağlamı]"]
        for i, (text, src, score) in enumerate(hits, 1):
            t = (text or "").strip()
            if len(t) > 2000:
                t = t[:2000] + "…"
            lines.append(f"({i}) [{src}] skor~{score:.3f}\n{t}")
        lines.append("[/MERKEZİ ZİHİN — RAG]")
        return "\n\n".join(lines) + "\n\n"

    # --- Kuvve-i Hafıza köprüsü (mevcut sohbet DB) ---

    def recent_sohbet_snippet(self, limit: int = 6) -> str:
        try:
            from ilim_assistant.kuvve_hafiza import format_prompt_memory_block

            block = (format_prompt_memory_block() or "").strip()
            if block:
                return block
            from ilim_assistant.kuvve_hafiza import list_sohbet

            rows = list_sohbet(limit=max(2, limit * 2))
            if not rows:
                return ""
            lines: list[str] = []
            for r in reversed(rows[: limit * 2]):
                role = str(r.get("role") or "")
                content = str(r.get("content") or "").strip()
                if not content:
                    continue
                if len(content) > 400:
                    content = content[:400] + "…"
                lines.append(f"{role}: {content}")
            return "\n".join(lines)
        except Exception:
            return ""

    # --- local_tools + approved_executor köprüsü ---

    def read_project_file(
        self,
        rel_path: str,
        max_chars: int | None = None,
    ) -> tuple[str, str | None]:
        if self._repo_root is None:
            return "", "Proje kökü bulunamadı."
        cap = max_chars or max(500, int(os.environ.get("LOCAL_TOOLS_FILE_MAX_CHARS", "6000")))
        return safe_read_file_under_root(self._repo_root, rel_path, cap)

    def write_project_file(self, rel_path: str, content: str) -> bool:
        if self._repo_root is None:
            return False
        ok = safe_write_file_under_root(self._repo_root, rel_path, content)
        if ok:
            self.publish_shared(
                "sistem",
                f"dosya_yazildi:{rel_path}",
                f"Dosya güncellendi: {rel_path}",
                priority=2,
                ttl_sec=3600,
            )
        return ok

    def run_exec_preset(self, preset_key: str) -> ExecResult:
        code, out = _run_preset(preset_key)
        result = ExecResult(preset=preset_key, exit_code=code, output=out)
        if out.strip():
            self.publish_shared(
                "sistem",
                f"exec:{preset_key}",
                out[:8000],
                priority=3 if not result.ok else 1,
                ttl_sec=1800,
            )
        return result

    # --- Birleşik tur bağlamı (motorlar için) ---

    def build_motor_pool_context(
        self,
        *,
        consumer_motor: str,
        message: str = "",
        include_rag: bool = True,
        include_sohbet: bool = False,
        rag_top_k: int = 3,
    ) -> str:
        """Tek çağrıda paylaşımlı pencere + isteğe bağlı RAG + sohbet özeti."""
        if not _enabled():
            return ""

        parts: list[str] = []
        shared = self.format_shared_context_block(consumer_motor=consumer_motor)
        if shared.strip():
            parts.append(shared.strip())

        q = (message or "").strip()
        if include_rag and q and consumer_motor not in no_rag_modes():
            rag_blk = self.rag_context_block(q, top_k=rag_top_k, archive=False)
            if rag_blk.strip():
                parts.append(rag_blk.strip())

        if include_sohbet:
            snip = self.recent_sohbet_snippet()
            if snip:
                parts.append("[MERKEZİ ZİHİN — Son sohbet özeti]\n" + snip)

        if not parts:
            return ""
        return "\n\n".join(parts) + "\n"

    def snapshot(self, query: str = "") -> HavuzSnapshot:
        snap = HavuzSnapshot(
            shared_context=self.read_shared(limit=16),
            json_stores_loaded=list(_JSON_STORE_FILES.keys()),
        )
        if query.strip():
            snap.rag_hits = self.rag_search(query, top_k=4)
        return snap


def get_havuz(workspace_root: str | Path | None = None) -> MerkeziZihinHavuzu:
    """Süreç genelinde tek havuz örneği (thread-safe lazy init)."""
    global _INSTANCE
    with _LOCK:
        if _INSTANCE is None:
            _INSTANCE = MerkeziZihinHavuzu(workspace_root=workspace_root)
        return _INSTANCE


def reset_havuz_singleton() -> None:
    """Test / yeniden başlatma için."""
    global _INSTANCE
    with _LOCK:
        _INSTANCE = None
