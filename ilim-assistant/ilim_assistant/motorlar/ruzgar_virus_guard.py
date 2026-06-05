# Created by Ümit & Gökçenur
"""
Rüzgar Virüs Koruması — internet indirmeleri için karantina + Rüzgar Virüs Kalkanı + sesli onay.

Tarama: ilim_assistant.motorlar.ruzgar_antivirus (Rüzgar'ın kendi motoru).
Windows Defender yalnızca RUZGAR_AV_DEFENDER_BACKUP=1 ile isteğe bağlı yedek katmandır.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ilim_assistant.motorlar.arsiv_indirme import (
    _host_ok_public,
    download_url_stream,
    safe_filename,
)
from ilim_assistant.motorlar.ruzgar_antivirus import (
    ENGINE_NAME,
    ENGINE_VERSION,
    check_url_reputation,
    list_threat_log,
    neutralize_threat,
    ruzgar_scan_file,
)

GUARD_VERSION = "ruzgar-virus-guard-v3-2026-06-04"

_BLOCKED_EXT = frozenset(
    {
        ".exe",
        ".msi",
        ".bat",
        ".cmd",
        ".com",
        ".scr",
        ".pif",
        ".ps1",
        ".vbs",
        ".js",
        ".jse",
        ".wsf",
        ".dll",
        ".hta",
        ".jar",
        ".lnk",
        ".reg",
        ".inf",
        ".cpl",
        ".apk",
        ".app",
        ".deb",
        ".rpm",
        ".dmg",
        ".iso",
        ".cab",
        ".sys",
        ".drv",
        ".ocx",
        ".gadget",
        ".application",
    }
)

_PENDING_TTL_SEC = 3600


def guard_enabled() -> bool:
    return os.environ.get("RUZGAR_VIRUS_GUARD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def video_auto_approve_enabled() -> bool:
    """Temiz YouTube taramasından sonra sesli onayı atla (varsayılan: açık)."""
    return os.environ.get("RUZGAR_VIRUS_GUARD_VIDEO_AUTO_APPROVE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _is_trusted_video_host(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower().strip(".")
    except Exception:
        return False
    if host in ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"):
        return True
    if host in ("youtu.be", "www.youtu.be"):
        return True
    return host.endswith(".youtube.com")


def _repo_root() -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root()
        if r:
            return Path(r)
    except Exception:
        pass
    return Path(__file__).resolve().parents[3]


def quarantine_root() -> Path:
    p = _repo_root() / "ilim-assistant" / "arsiv" / "_virus_guard_staging"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _pending_dir() -> Path:
    d = quarantine_root() / "pending"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _meta_path(pending_id: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "", pending_id or "")
    return _pending_dir() / f"{safe}.json"


def _max_stage_bytes() -> int:
    try:
        mb = int(os.environ.get("RUZGAR_VIRUS_GUARD_MAX_MB", "2048"))
    except ValueError:
        mb = 2048
    return max(32, mb) * 1024 * 1024


def extension_blocked(name_or_url: str) -> str | None:
    low = (name_or_url or "").lower().split("?")[0].split("#")[0]
    for ext in _BLOCKED_EXT:
        if low.endswith(ext):
            return ext
    return None


def scan_file_path(target: Path, *, mode: str = "deep") -> Any:
    """Rüzgar Virüs Kalkanı ile tara."""
    return ruzgar_scan_file(target, mode=mode)


def _tts_messages(filename: str, verdict: Any, *, kind: str = "file") -> dict[str, str]:
    fn = filename or "dosya"
    vdict = verdict.to_dict() if hasattr(verdict, "to_dict") else dict(verdict)
    if not vdict.get("clean", True):
        threat_hint = ""
        threats = vdict.get("threats") or []
        if threats:
            threat_hint = threats[0][:80]
        return {
            "tts_user": (
                f"Ümit abi, {fn} için {ENGINE_NAME} tehdit buldu ve dosyayı nötralize etti. "
                f"İndirmeye izin vermiyorum. {threat_hint}"
            ),
            "tts_clean_ok": "",
            "prompt_listen": "",
        }
    risk = int(vdict.get("risk_score") or 0)
    layers_n = len(vdict.get("layers") or [])
    return {
        "tts_user": (
            f"Ümit abi, {fn} dosyasını {ENGINE_NAME} ile derin taradım. "
            f"{layers_n} katman temiz, risk skoru sıfır. "
            "İndirebilir miyim? Onay için tamam indirebilirsin de."
        ),
        "tts_clean_ok": "Teşekkürler, indirmeyi tamamlıyorum.",
        "prompt_listen": "tamam indirebilirsin",
        "risk_score": risk,
    }


def _save_pending(meta: dict[str, Any]) -> None:
    pid = str(meta.get("pending_id") or "")
    _meta_path(pid).write_text(json.dumps(meta, ensure_ascii=False, indent=0), encoding="utf-8")


def _load_pending(pending_id: str) -> dict[str, Any] | None:
    p = _meta_path(pending_id)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    created = float(data.get("created_at") or 0)
    if created and (time.time() - created) > _PENDING_TTL_SEC:
        _reject_pending(pending_id, reason="süre doldu", delete_file=True)
        return None
    return data


def _drop_pending_meta(pending_id: str) -> dict[str, Any] | None:
    mp = _meta_path(pending_id)
    data = None
    if mp.is_file():
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
        except Exception:
            data = None
        try:
            mp.unlink()
        except OSError:
            pass
    return data


def _cleanup_staged(data: dict[str, Any] | None) -> None:
    if not data:
        return
    staged = Path(str(data.get("staged_abs") or ""))
    if staged.is_file():
        try:
            staged.unlink()
        except OSError:
            pass
    stage_dir = str(data.get("stage_dir") or "").strip()
    if stage_dir:
        shutil.rmtree(stage_dir, ignore_errors=True)


def _reject_pending(pending_id: str, *, reason: str = "", delete_file: bool = True) -> None:
    data = _drop_pending_meta(pending_id)
    if data is None:
        p = _meta_path(pending_id)
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                data = None
            _drop_pending_meta(pending_id)
    if delete_file:
        _cleanup_staged(data)


def _handle_threat(staged: Path, verdict: Any, url: str, fname: str) -> dict[str, Any]:
    neu = neutralize_threat(staged, verdict, source_url=url)
    msgs = _tts_messages(fname, verdict)
    return {
        "ok": False,
        "error": neu.get("message") or f"{ENGINE_NAME}: tehdit nötralize edildi.",
        "scan": verdict.to_dict() if hasattr(verdict, "to_dict") else verdict,
        "neutralized": neu,
        "tts_message": msgs["tts_user"],
        "phase": "neutralize",
    }


def preflight_url_download(
    url: str,
    *,
    filename_hint: str = "",
    scan_mode: str = "deep",
) -> dict[str, Any]:
    if not guard_enabled():
        return {"ok": False, "error": "Virüs koruması kapalı.", "guard_off": True}

    u = (url or "").strip()
    if not u:
        return {"ok": False, "error": "url boş"}
    url_hits = check_url_reputation(u)
    if url_hits:
        return {
            "ok": False,
            "error": url_hits[0],
            "phase": "url_reputation",
            "tts_message": f"Ümit abi, bu adres {ENGINE_NAME} tarafından engellendi.",
        }
    ext_block = extension_blocked(u) or extension_blocked(filename_hint)
    if ext_block:
        return {"ok": False, "error": f"Engellenen uzantı: {ext_block}", "blocked_ext": ext_block}

    p = urlparse(u)
    if p.scheme not in ("http", "https"):
        return {"ok": False, "error": "Yalnızca http/https"}
    if not _host_ok_public(u):
        return {"ok": False, "error": "Geçersiz veya yerel adres."}

    hint = (filename_hint or "").strip() or Path(p.path).name or ""
    fname = safe_filename(hint)
    pending_id = uuid.uuid4().hex[:16]
    staged = quarantine_root() / f"{pending_id}_{fname}"

    dl = download_url_stream(u, staged, timeout_sec=7200.0)
    if not dl.get("ok"):
        return {"ok": False, "error": dl.get("error") or "İndirme başarısız", "phase": "download"}

    size = int(dl.get("bytes") or 0)
    if size > _max_stage_bytes():
        try:
            staged.unlink()
        except OSError:
            pass
        return {
            "ok": False,
            "error": f"Dosya çok büyük (>{_max_stage_bytes() // (1024 * 1024)} MB karantina sınırı).",
        }

    mode = (scan_mode or "deep").strip().lower()
    verdict = ruzgar_scan_file(staged, mode=mode)
    if not verdict.clean:
        return _handle_threat(staged, verdict, u, fname)

    meta = {
        "pending_id": pending_id,
        "kind": "url",
        "url": u,
        "staged_abs": str(staged.resolve()),
        "filename": fname,
        "bytes": size,
        "content_type": dl.get("content_type"),
        "created_at": time.time(),
        "scan": verdict.to_dict(),
        "scan_mode": mode,
        "target_dir_rel": "",
        "target_abs": "",
    }
    _save_pending(meta)
    msgs = _tts_messages(fname, verdict)

    return {
        "ok": True,
        "pending_id": pending_id,
        "phase": "awaiting_user_approval",
        "scan": verdict.to_dict(),
        "risk_score": verdict.risk_score,
        "bytes": size,
        "filename": fname,
        "tts_message": msgs["tts_user"],
        "tts_after_commit": msgs["tts_clean_ok"],
        "voice_prompt_hint": msgs["prompt_listen"],
        "guard_version": GUARD_VERSION,
        "scan_engine": ENGINE_NAME,
        "scan_engine_version": ENGINE_VERSION,
    }


def preflight_video_download(url: str, *, scan_mode: str = "deep") -> dict[str, Any]:
    if not guard_enabled():
        return {"ok": False, "error": "Virüs koruması kapalı.", "guard_off": True}

    u = (url or "").strip()
    if not u:
        return {"ok": False, "error": "url boş"}
    url_hits = check_url_reputation(u)
    if url_hits:
        return {
            "ok": False,
            "error": url_hits[0],
            "phase": "url_reputation",
            "tts_message": f"Ümit abi, bu video adresi {ENGINE_NAME} tarafından engellendi.",
        }

    pending_id = uuid.uuid4().hex[:12]
    stage_dir = quarantine_root() / f"video_{pending_id}"
    stage_dir.mkdir(parents=True, exist_ok=True)

    from ilim_assistant.motorlar.video_motoru import download_video_with_yt_dlp

    result = download_video_with_yt_dlp(u, out_dir=stage_dir)
    if not result.ok or not result.file_path:
        shutil.rmtree(stage_dir, ignore_errors=True)
        return {
            "ok": False,
            "error": result.error or "Video indirme başarısız",
            "phase": "download",
        }

    staged = Path(result.file_path)
    if not staged.is_file():
        try:
            staged = (_repo_root() / result.file_path).resolve()
        except Exception:
            pass
    if not staged.is_file():
        shutil.rmtree(stage_dir, ignore_errors=True)
        return {"ok": False, "error": "Video dosyası bulunamadı", "phase": "download"}

    ext_block = extension_blocked(staged.name)
    if ext_block:
        shutil.rmtree(stage_dir, ignore_errors=True)
        return {"ok": False, "error": f"Engellenen uzantı: {ext_block}"}

    mode = (scan_mode or "deep").strip().lower()
    verdict = ruzgar_scan_file(staged, mode=mode)
    if not verdict.clean:
        out = _handle_threat(staged, verdict, u, staged.name)
        shutil.rmtree(stage_dir, ignore_errors=True)
        return out

    meta = {
        "pending_id": pending_id,
        "kind": "video",
        "url": u,
        "staged_abs": str(staged.resolve()),
        "stage_dir": str(stage_dir.resolve()),
        "filename": staged.name,
        "bytes": staged.stat().st_size,
        "video_metadata": result.to_metadata(),
        "created_at": time.time(),
        "scan": verdict.to_dict(),
        "scan_mode": mode,
        "target_dir_rel": "",
        "target_abs": "",
    }
    _save_pending(meta)
    msgs = _tts_messages(staged.name, verdict)

    auto_approve = video_auto_approve_enabled() and _is_trusted_video_host(u)
    phase = "auto_approved" if auto_approve else "awaiting_user_approval"

    return {
        "ok": True,
        "pending_id": pending_id,
        "phase": phase,
        "auto_approve": auto_approve,
        "scan": verdict.to_dict(),
        "bytes": meta["bytes"],
        "filename": staged.name,
        "tts_message": msgs["tts_user"] if not auto_approve else "",
        "tts_after_commit": msgs["tts_clean_ok"],
        "voice_prompt_hint": msgs["prompt_listen"],
        "guard_version": GUARD_VERSION,
        "video_metadata": result.to_metadata(),
        "scan_engine": ENGINE_NAME,
        "scan_engine_version": ENGINE_VERSION,
    }


def commit_pending(
    pending_id: str,
    *,
    target_dir_rel: str = "",
    target_abs: str = "",
) -> dict[str, Any]:
    data = _load_pending(pending_id)
    if not data:
        return {"ok": False, "error": "Bekleyen indirme yok veya süresi doldu."}

    staged = Path(str(data.get("staged_abs") or ""))
    if not staged.is_file():
        _reject_pending(pending_id, reason="dosya yok", delete_file=True)
        return {"ok": False, "error": "Karantina dosyası bulunamadı."}

    rescan = ruzgar_scan_file(staged, mode="deep")
    if not rescan.clean:
        neu = neutralize_threat(staged, rescan, source_url=str(data.get("url") or ""))
        _drop_pending_meta(pending_id)
        return {
            "ok": False,
            "error": "Onay öncesi yeniden taramada tehdit bulundu.",
            "scan": rescan.to_dict(),
            "neutralized": neu,
            "phase": "rescan_fail",
        }

    kind = str(data.get("kind") or "url")
    if kind == "video":
        rel = ""
        try:
            rel = staged.resolve().relative_to(_repo_root().resolve()).as_posix()
        except ValueError:
            rel = str(staged)
        _drop_pending_meta(pending_id)
        return {
            "ok": True,
            "rel": rel,
            "abs": str(staged.resolve()),
            "bytes": staged.stat().st_size,
            "committed": True,
            "kind": "video",
            "video_metadata": data.get("video_metadata"),
        }

    out_dir: Path | None = None
    if (target_abs or "").strip():
        out_dir = Path(target_abs.strip()).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
    elif (target_dir_rel or "").strip():
        from ilim_assistant.motorlar.arsiv_indirme import resolve_arsiv_dir

        try:
            out_dir = resolve_arsiv_dir(target_dir_rel.strip())
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
    else:
        return {"ok": False, "error": "target_abs veya target_dir_rel gerekli."}

    dest = out_dir / staged.name
    if dest.is_file():
        base = dest.stem
        ext = dest.suffix
        n = 2
        while dest.is_file():
            dest = out_dir / f"{base}_v{n}{ext}"
            n += 1

    shutil.move(str(staged), str(dest))
    root = _repo_root()
    try:
        rel = dest.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = str(dest)

    _drop_pending_meta(pending_id)
    return {
        "ok": True,
        "rel": rel,
        "abs": str(dest.resolve()),
        "bytes": dest.stat().st_size,
        "content_type": data.get("content_type"),
        "committed": True,
        "kind": "url",
    }


def reject_pending(pending_id: str) -> dict[str, Any]:
    _reject_pending(pending_id, reason="user_reject", delete_file=True)
    return {"ok": True, "rejected": True}


def capabilities() -> dict[str, Any]:
    from ilim_assistant.motorlar.ruzgar_antivirus import engine_capabilities

    av = engine_capabilities()
    return {
        "version": GUARD_VERSION,
        "enabled": guard_enabled(),
        "scan_engine": ENGINE_NAME,
        "scan_engine_version": ENGINE_VERSION,
        "ruzgar_antivirus": av,
        "max_stage_mb": _max_stage_bytes() // (1024 * 1024),
        "blocked_extensions": sorted(_BLOCKED_EXT),
        "scan_modes": ["quick", "deep"],
        "rescan_on_commit": True,
        "voice_phrases": [
            "tamam indirebilirsin",
            "indirebilirsin",
            "evet indir",
            "onayla",
            "tamam",
        ],
        "video_auto_approve": video_auto_approve_enabled(),
        "video_auto_approve_hosts": ["youtube.com", "youtu.be"],
        "note": (
            "Çok katmanlı Rüzgar Virüs Kalkanı: URL itibar, karantina, derin tarama, "
            "risk skoru, nötralizasyon, sesli onay (YouTube temiz taramada otomatik), "
            "commit öncesi yeniden tarama."
        ),
    }
