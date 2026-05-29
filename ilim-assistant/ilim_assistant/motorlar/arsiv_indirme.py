# Created by Ümit & Gökçenur
"""Arşiv klasörlerine güvenli URL indirme (manifest + tek tek)."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ARSIV_INDIRME_VERSION = "arsiv-indirme-v1-2026-05-29"
_MANIFEST_NAME = "arsiv_indirme_manifest.json"
# Manifest önizleme indirmeleri (küçük/orta)
_MAX_BYTES_MANIFEST = 110_000_000
_ALLOWED_HOST_SUFFIX = (
    "archive.org",
    "archive.org",
    "wikisource.org",
    "gutenberg.org",
    "al-eman.com",
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


def _arsiv_base() -> Path:
    root = _repo_root()
    p = root / "ilim-assistant" / "arsiv"
    if p.is_dir():
        return p
    return root / "arsiv"


def manifest_path() -> Path:
    return _arsiv_base() / _MANIFEST_NAME


def _normalize_rel(raw: str) -> str:
    return (raw or "").strip().replace("\\", "/").lstrip("/")


def arsiv_dir_allowed(rel: str) -> bool:
    r = _normalize_rel(rel).rstrip("/")
    if not r:
        return False
    return r.startswith("ilim-assistant/arsiv/") or r == "ilim-assistant/arsiv"


def resolve_arsiv_dir(rel: str) -> Path:
    if not arsiv_dir_allowed(rel):
        raise ValueError("Hedef yalnızca ilim-assistant/arsiv/ altında olmalı.")
    root = _repo_root()
    rel_n = _normalize_rel(rel)
    if rel_n.startswith("arsiv/") and not rel_n.startswith("ilim-assistant/"):
        rel_n = "ilim-assistant/" + rel_n
    target = (root / rel_n.replace("/", os.sep)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        raise ValueError("Geçersiz yol (proje dışı).") from None
    target.mkdir(parents=True, exist_ok=True)
    return target


def _host_ok(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    if not host:
        return False
    for suf in _ALLOWED_HOST_SUFFIX:
        if host == suf or host.endswith("." + suf):
            return True
    return host.endswith(".edu") or host.endswith(".gov")


def archive_org_download_url(identifier: str, file_name: str) -> str:
    aid = (identifier or "").strip()
    fn = (file_name or "").strip()
    if not aid or not fn:
        return ""
    return f"https://archive.org/download/{quote(aid, safe='')}/{quote(fn, safe='')}"


def resolve_item_url(item: dict[str, Any]) -> str:
    u = str(item.get("url") or "").strip()
    if u:
        return u
    aid = str(item.get("archive_id") or "").strip()
    af = str(item.get("archive_file") or "").strip()
    return archive_org_download_url(aid, af)


def safe_filename(name: str, fallback_ext: str = ".pdf") -> str:
    base = re.sub(r"[^a-zA-Z0-9._\-]+", "_", (name or "").strip()).strip("._")
    if not base:
        base = f"indir_{uuid.uuid4().hex[:8]}"
    if "." not in base and fallback_ext:
        base += fallback_ext
    return base[:180]


def _host_ok_public(url: str) -> bool:
    if _host_ok(url):
        return True
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    if not host or host in ("localhost", "127.0.0.1", "::1"):
        return False
    if host.endswith(".local"):
        return False
    return True


def download_url_stream(
    url: str,
    target: Path,
    *,
    timeout_sec: float = 7200.0,
    chunk_size: int = 1024 * 1024,
) -> dict[str, Any]:
    """Büyük dosyalar için akışlı indirme — üst boyut sınırı yok."""
    u = (url or "").strip()
    if not u:
        return {"ok": False, "error": "url boş"}
    p = urlparse(u)
    if p.scheme not in ("http", "https"):
        return {"ok": False, "error": "Yalnızca http/https"}
    if not _host_ok_public(u):
        return {"ok": False, "error": "Geçersiz veya yerel adres."}

    target.parent.mkdir(parents=True, exist_ok=True)
    req = Request(u, headers={"User-Agent": "RuzgarArsiv/2.0"})
    total = 0
    try:
        with urlopen(req, timeout=timeout_sec) as r:
            ctype = str(r.headers.get("Content-Type") or "")
            with target.open("wb") as out:
                while True:
                    chunk = r.read(chunk_size)
                    if not chunk:
                        break
                    out.write(chunk)
                    total += len(chunk)
    except Exception as exc:
        try:
            if target.is_file():
                target.unlink()
        except OSError:
            pass
        return {"ok": False, "error": f"İndirme başarısız: {str(exc)[:220]}"}

    if total < 64:
        try:
            target.unlink()
        except OSError:
            pass
        return {"ok": False, "error": "İndirilen içerik çok kısa."}

    root = _repo_root()
    try:
        rel = target.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = target.as_posix()
    return {
        "ok": True,
        "rel": rel,
        "abs": str(target.resolve()),
        "bytes": total,
        "content_type": ctype,
        "skipped": False,
    }


def download_url_to_arsiv(
    url: str,
    target_dir_rel: str,
    *,
    filename_hint: str = "",
    timeout_sec: float = 120.0,
    use_stream: bool = True,
) -> dict[str, Any]:
    u = (url or "").strip()
    if not u:
        return {"ok": False, "error": "url boş"}
    p = urlparse(u)
    if p.scheme not in ("http", "https"):
        return {"ok": False, "error": "Yalnızca http/https"}
    if not _host_ok(u):
        return {
            "ok": False,
            "error": "Bu alan adı listede yok. archive.org / wikisource / gutenberg veya manifest kullanın.",
        }

    out_dir = resolve_arsiv_dir(target_dir_rel)
    hint = (filename_hint or "").strip() or Path(p.path).name or ""
    fname = safe_filename(hint)
    target = out_dir / fname
    if target.is_file() and target.stat().st_size > 0:
        rel = target.relative_to(_repo_root()).as_posix()
        return {
            "ok": True,
            "rel": rel,
            "bytes": target.stat().st_size,
            "skipped": True,
            "message": "Dosya zaten var",
        }

    if use_stream:
        return download_url_stream(u, target, timeout_sec=max(timeout_sec, 300.0))

    req = Request(u, headers={"User-Agent": "RuzgarArsiv/1.0"})
    try:
        with urlopen(req, timeout=timeout_sec) as r:
            data = r.read(_MAX_BYTES_MANIFEST + 1)
            ctype = str(r.headers.get("Content-Type") or "")
    except Exception as exc:
        return {"ok": False, "error": f"İndirme başarısız: {str(exc)[:220]}"}

    if len(data) > _MAX_BYTES_MANIFEST:
        return {
            "ok": False,
            "error": f"Dosya çok büyük (>{_MAX_BYTES_MANIFEST // 1_000_000} MB); akışlı indirme kullanın.",
        }
    if len(data) < 64:
        return {"ok": False, "error": "İndirilen içerik çok kısa (boş veya hata sayfası olabilir)."}

    try:
        target.write_bytes(data)
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:200]}

    rel = target.relative_to(_repo_root()).as_posix()
    return {
        "ok": True,
        "rel": rel,
        "bytes": len(data),
        "content_type": ctype,
        "skipped": False,
    }


def download_url_to_folder(
    url: str,
    target_dir: Path,
    *,
    filename_hint: str = "",
    timeout_sec: float = 7200.0,
) -> dict[str, Any]:
    """Mutlak veya göreli klasöre akışlı indirme (boyut sınırı yok)."""
    u = (url or "").strip()
    if not u:
        return {"ok": False, "error": "url boş"}
    hint = (filename_hint or "").strip() or Path(urlparse(u).path).name or ""
    fname = safe_filename(hint)
    target = Path(target_dir) / fname
    if target.is_file() and target.stat().st_size > 0:
        root = _repo_root()
        try:
            rel = target.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = target.as_posix()
        return {
            "ok": True,
            "rel": rel,
            "abs": str(target.resolve()),
            "bytes": target.stat().st_size,
            "skipped": True,
            "message": "Dosya zaten var",
        }
    return download_url_stream(u, target, timeout_sec=timeout_sec)


def load_manifest() -> dict[str, Any]:
    path = manifest_path()
    if not path.is_file():
        return {"version": 1, "items": [], "note": "Manifest yok"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"version": 1, "items": [], "error": str(exc)[:120]}


def catalog_with_status() -> dict[str, Any]:
    data = load_manifest()
    root = _repo_root()
    items_out: list[dict[str, Any]] = []
    for it in data.get("items") or []:
        if not isinstance(it, dict):
            continue
        folder = str(it.get("folder") or "")
        fname = str(it.get("filename") or "")
        rel = f"{folder.rstrip('/')}/{fname}" if folder and fname else ""
        full = root / rel.replace("/", os.sep) if rel else None
        exists = bool(full and full.is_file() and full.stat().st_size > 0)
        items_out.append(
            {
                **it,
                "rel": rel,
                "downloaded": exists,
                "size_bytes": full.stat().st_size if exists and full else 0,
            }
        )
    pending = sum(1 for x in items_out if not x.get("downloaded"))
    return {
        "ok": True,
        "version": data.get("version", 1),
        "manifest": str(manifest_path().relative_to(root).as_posix()),
        "items": items_out,
        "pending_count": pending,
        "total": len(items_out),
    }


def import_manifest_item(item_id: str) -> dict[str, Any]:
    data = load_manifest()
    for it in data.get("items") or []:
        if str(it.get("id") or "") != item_id:
            continue
        url = resolve_item_url(it)
        if not url:
            return {"ok": False, "error": "URL veya archive_id/archive_file eksik", "item_id": item_id}
        folder = str(it.get("folder") or "ilim-assistant/arsiv/tercume-imports")
        fname = str(it.get("filename") or "")
        res = download_url_to_arsiv(url, folder, filename_hint=fname)
        res["item_id"] = item_id
        res["title"] = it.get("title") or item_id
        return res
    return {"ok": False, "error": f"Manifest kaydı yok: {item_id}"}


def import_next_pending(*, limit: int = 1, delay_sec: float = 1.5) -> dict[str, Any]:
    cat = catalog_with_status()
    results: list[dict[str, Any]] = []
    for it in cat.get("items") or []:
        if it.get("downloaded"):
            continue
        if len(results) >= max(1, min(limit, 5)):
            break
        r = import_manifest_item(str(it.get("id") or ""))
        results.append(r)
        if r.get("ok") and delay_sec > 0:
            time.sleep(delay_sec)
    return {
        "ok": True,
        "results": results,
        "remaining": max(0, int(cat.get("pending_count") or 0) - len(results)),
    }
