# Created by Ümit & Gökçenur
"""Dosya bütünlük izleme (FIM) — SHA-256 baseline + değişiklik kontrolü."""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterator

# İzleme dışı (büyük / geçici / gizli indeks)
_SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".rag_index",
        ".ruff_cache",
        "venv",
        ".venv",
        "dist",
        "build",
        "_virus_guard_staging",
    }
)
_SKIP_SUFFIXES = frozenset(
    {
        ".pyc",
        ".pyo",
        ".tmp",
        ".swp",
        ".sqlite3-journal",
        ".npy",
    }
)


class FileIntegrityMonitor:
    """Belirtilen köklerdeki dosyaların SHA-256 özetlerini SQLite'ta tutar."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS file_hashes (
                    path TEXT PRIMARY KEY,
                    sha256 TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mtime REAL NOT NULL,
                    updated_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS scan_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def sha256_file(path: Path, *, chunk: int = 1024 * 1024) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            while True:
                block = f.read(chunk)
                if not block:
                    break
                h.update(block)
        return h.hexdigest()

    def iter_files(self, root: Path, *, max_files: int = 5000) -> Iterator[Path]:
        n = 0
        if root.is_file():
            yield root
            return
        if not root.is_dir():
            return
        for p in root.rglob("*"):
            if n >= max_files:
                break
            if not p.is_file():
                continue
            if any(part in _SKIP_DIR_NAMES for part in p.parts):
                continue
            if p.suffix.lower() in _SKIP_SUFFIXES:
                continue
            try:
                if p.stat().st_size > 64 * 1024 * 1024:
                    continue
            except OSError:
                continue
            yield p
            n += 1

    def baseline(self, roots: list[str | Path], *, max_files: int = 5000) -> dict[str, Any]:
        """Mevcut dosyaları baz satır olarak kaydet (üzerine yazar)."""
        now = time.time()
        stored = 0
        errors: list[str] = []
        with self._connect() as conn:
            for root in roots:
                r = Path(root)
                for path in self.iter_files(r, max_files=max_files - stored):
                    try:
                        digest = self.sha256_file(path)
                        st = path.stat()
                        conn.execute(
                            """
                            INSERT INTO file_hashes(path, sha256, size, mtime, updated_ts)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(path) DO UPDATE SET
                              sha256=excluded.sha256,
                              size=excluded.size,
                              mtime=excluded.mtime,
                              updated_ts=excluded.updated_ts
                            """,
                            (str(path.resolve()), digest, st.st_size, st.st_mtime, now),
                        )
                        stored += 1
                    except OSError as exc:
                        errors.append(f"{path}: {exc}")
            conn.execute(
                "INSERT INTO scan_meta(key, value) VALUES('last_baseline_ts', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(now),),
            )
            conn.commit()
        return {
            "mode": "baseline",
            "files_stored": stored,
            "errors": errors[:50],
            "db": str(self.db_path),
            "changes": [],
        }

    def check(self, roots: list[str | Path], *, max_files: int = 5000) -> dict[str, Any]:
        """Baz satırla karşılaştır; new / modified / deleted / ok."""
        now = time.time()
        seen: set[str] = set()
        changes: list[dict[str, Any]] = []
        ok_count = 0
        errors: list[str] = []

        with self._connect() as conn:
            known = {
                row["path"]: dict(row)
                for row in conn.execute("SELECT path, sha256, size, mtime FROM file_hashes")
            }
            scanned = 0
            for root in roots:
                r = Path(root)
                for path in self.iter_files(r, max_files=max_files - scanned):
                    scanned += 1
                    key = str(path.resolve())
                    seen.add(key)
                    try:
                        digest = self.sha256_file(path)
                        st = path.stat()
                    except OSError as exc:
                        errors.append(f"{path}: {exc}")
                        continue
                    prev = known.get(key)
                    if prev is None:
                        changes.append(
                            {
                                "status": "new",
                                "path": key,
                                "sha256": digest,
                                "size": st.st_size,
                            }
                        )
                    elif prev["sha256"] != digest:
                        changes.append(
                            {
                                "status": "modified",
                                "path": key,
                                "sha256": digest,
                                "prev_sha256": prev["sha256"],
                                "size": st.st_size,
                                "prev_size": prev["size"],
                            }
                        )
                    else:
                        ok_count += 1

            for key, prev in known.items():
                if key not in seen and any(
                    key.startswith(str(Path(r).resolve())) for r in roots if Path(r).exists()
                ):
                    changes.append(
                        {
                            "status": "deleted",
                            "path": key,
                            "prev_sha256": prev["sha256"],
                        }
                    )

            conn.execute(
                "INSERT INTO scan_meta(key, value) VALUES('last_check_ts', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(now),),
            )
            conn.commit()

        return {
            "mode": "check",
            "ok_count": ok_count,
            "change_count": len(changes),
            "changes": changes[:500],
            "errors": errors[:50],
            "db": str(self.db_path),
            "known_count": len(known),
        }
