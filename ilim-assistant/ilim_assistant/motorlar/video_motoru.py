# Created by Ümit & Gökçenur
"""
Video motoru — yt-dlp indirme + Merkezi Zihin Havuzu metadata senkronu.

Omurgalar:
  - ``yt_dlp`` (Python) veya ``yt-dlp`` (PATH) ile indirme
  - ``merkezi_zihin_havuzu.get_havuz()`` paylaşımlı bellek + ``video_hafiza.json``
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ilim_assistant.motorlar.merkezi_zihin_havuzu import get_havuz

MIMAR_IMZA = "Ümit & Gökçenur"
PROJE_ADI = "RÜZGAR Video Motoru"

_URL_ALLOWED = re.compile(r"^https?://", re.IGNORECASE)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ilim_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_download_dir() -> Path:
    raw = (os.environ.get("RUZGAR_VIDEO_DOWNLOAD_DIR", "") or "").strip()
    if raw:
        p = Path(raw)
    else:
        p = _ilim_root() / "hafiza" / "video_indirilen"
    p.mkdir(parents=True, exist_ok=True)
    return p.resolve()


def _validate_url(url: str) -> str | None:
    u = (url or "").strip()
    if not u or not _URL_ALLOWED.match(u):
        return "Yalnızca http/https URL kabul edilir."
    try:
        parsed = urlparse(u)
        if not parsed.netloc:
            return "Geçersiz URL."
    except Exception:
        return "URL ayrıştırılamadı."
    return None


def _yt_dlp_cli() -> str | None:
    for name in ("yt-dlp", "yt-dlp.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _format_best() -> str:
    return os.environ.get("RUZGAR_YTDLP_FORMAT", "bestvideo+bestaudio/best").strip() or "best"


@dataclass
class VideoDownloadResult:
    ok: bool
    url: str
    title: str = ""
    file_path: str = ""
    file_size_bytes: int = 0
    downloaded_at: str = ""
    duration_sec: float | None = None
    ext: str = ""
    download_id: str = ""
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("error", None)
        d.pop("extra", None)
        if self.extra:
            d["extra"] = self.extra
        return d


def save_to_central_pool(record: VideoDownloadResult | dict[str, Any]) -> bool:
    """
    İndirme metadata'sını Merkezi Zihin Havuzu'na yazar:
    - paylaşımlı bağlam penceresi (``publish_shared``)
    - motor KV (SQLite)
    - ``video_hafiza.json`` listesi
    """
    if isinstance(record, VideoDownloadResult):
        meta = record.to_metadata()
        ok = record.ok
        title = record.title or record.url
        summary = (
            f"Video indirildi: {title}\n"
            f"Yol: {record.file_path}\n"
            f"Boyut: {record.file_size_bytes} bayt\n"
            f"Tarih: {record.downloaded_at}"
        )
        if not ok:
            summary = f"Video indirme başarısız: {record.error or 'bilinmeyen'}"
    else:
        meta = dict(record)
        ok = bool(meta.get("ok"))
        title = str(meta.get("title") or meta.get("url") or "video")
        summary = json.dumps(meta, ensure_ascii=False, indent=0)[:4000]

    try:
        havuz = get_havuz()
        dl_id = str(meta.get("download_id") or uuid.uuid4().hex[:12])
        meta["download_id"] = dl_id

        havuz.publish_shared(
            "video",
            f"indirme:{dl_id}",
            summary,
            priority=5 if ok else 2,
            ttl_sec=int(os.environ.get("RUZGAR_VIDEO_SHARED_TTL", "86400")),
        )

        havuz.motor_set("video", f"download:{dl_id}", meta)

        doc = havuz.json_load("video", default={"downloads": []})
        if not isinstance(doc, dict):
            doc = {"downloads": []}
        downloads = doc.setdefault("downloads", [])
        if not isinstance(downloads, list):
            downloads = []
            doc["downloads"] = downloads
        downloads.append(meta)
        cap = max(10, int(os.environ.get("RUZGAR_VIDEO_HAFIZA_MAX", "200")))
        if len(downloads) > cap:
            doc["downloads"] = downloads[-cap:]
        doc["updated_at"] = _utc_now_iso()
        havuz.json_save("video", doc)
        return True
    except Exception:
        return False


def _probe_file(path: Path) -> tuple[int, float | None]:
    size = path.stat().st_size if path.is_file() else 0
    duration: float | None = None
    try:
        from ilim_assistant.video_ffmpeg import ffprobe_json

        info = ffprobe_json(path)
        dur = (info.get("format") or {}).get("duration")
        if dur is not None:
            duration = float(dur)
    except Exception:
        pass
    return size, duration


def _download_via_python_api(url: str, out_dir: Path) -> VideoDownloadResult:
    import yt_dlp  # type: ignore[import-untyped]

    downloaded_at = _utc_now_iso()
    outtmpl = str(out_dir / "%(title).200B [%(id)s].%(ext)s")
    info: dict[str, Any] = {}
    final_path: Path | None = None

    def _hook(d: dict[str, Any]) -> None:
        nonlocal final_path
        if d.get("status") == "finished":
            fp = d.get("filename") or d.get("info_dict", {}).get("_filename")
            if fp:
                final_path = Path(str(fp))

    ydl_opts: dict[str, Any] = {
        "format": _format_best(),
        "outtmpl": outtmpl,
        "merge_output_format": os.environ.get("RUZGAR_YTDLP_MERGE_EXT", "mp4"),
        "quiet": os.environ.get("RUZGAR_YTDLP_QUIET", "1").strip() in ("1", "true", "yes"),
        "no_warnings": True,
        "progress_hooks": [_hook],
        "noplaylist": os.environ.get("RUZGAR_YTDLP_PLAYLIST", "0").strip() in ("1", "true", "yes"),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True) or {}

    if final_path is None or not final_path.is_file():
        candidates = sorted(
            out_dir.glob("*"),
            key=lambda p: p.stat().st_mtime if p.is_file() else 0,
            reverse=True,
        )
        for c in candidates:
            if c.is_file() and c.suffix.lower() in (".mp4", ".mkv", ".webm", ".m4a", ".mov"):
                final_path = c
                break

    if final_path is None or not final_path.is_file():
        return VideoDownloadResult(
            ok=False,
            url=url,
            downloaded_at=downloaded_at,
            error="İndirme tamamlandı ancak çıktı dosyası bulunamadı.",
        )

    title = str(info.get("title") or final_path.stem)
    size, duration = _probe_file(final_path)
    rel = _relative_path(final_path)

    result = VideoDownloadResult(
        ok=True,
        url=url,
        title=title,
        file_path=rel,
        file_size_bytes=size,
        downloaded_at=downloaded_at,
        duration_sec=duration,
        ext=final_path.suffix.lstrip(".").lower(),
        download_id=uuid.uuid4().hex[:12],
        extra={"id": info.get("id"), "uploader": info.get("uploader")},
    )
    save_to_central_pool(result)
    return result


def _download_via_cli(url: str, out_dir: Path, exe: str) -> VideoDownloadResult:
    downloaded_at = _utc_now_iso()
    outtmpl = str(out_dir / "%(title).200B [%(id)s].%(ext)s")
    merge = os.environ.get("RUZGAR_YTDLP_MERGE_EXT", "mp4")
    argv = [
        exe,
        url,
        "-f",
        _format_best(),
        "--merge-output-format",
        merge,
        "-o",
        outtmpl,
        "--no-warnings",
    ]
    if os.environ.get("RUZGAR_YTDLP_PLAYLIST", "0").strip() not in ("1", "true", "yes"):
        argv.append("--no-playlist")

    try:
        r = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=int(os.environ.get("RUZGAR_YTDLP_TIMEOUT", "7200")),
            cwd=str(out_dir),
        )
    except subprocess.TimeoutExpired:
        return VideoDownloadResult(
            ok=False,
            url=url,
            downloaded_at=downloaded_at,
            error="yt-dlp zaman aşımı.",
        )
    except Exception as e:
        return VideoDownloadResult(
            ok=False,
            url=url,
            downloaded_at=downloaded_at,
            error=str(e),
        )

    if r.returncode != 0:
        err = (r.stderr or r.stdout or "yt-dlp hata").strip()
        return VideoDownloadResult(
            ok=False,
            url=url,
            downloaded_at=downloaded_at,
            error=err[:4000],
        )

    candidates = sorted(
        out_dir.glob("*"),
        key=lambda p: p.stat().st_mtime if p.is_file() else 0,
        reverse=True,
    )
    final_path: Path | None = None
    for c in candidates:
        if c.is_file() and c.suffix.lower() in (".mp4", ".mkv", ".webm", ".m4a", ".mov"):
            final_path = c
            break

    if final_path is None:
        return VideoDownloadResult(
            ok=False,
            url=url,
            downloaded_at=downloaded_at,
            error="yt-dlp başarılı göründü ama video dosyası bulunamadı.",
        )

    title = final_path.stem
    size, duration = _probe_file(final_path)
    rel = _relative_path(final_path)

    result = VideoDownloadResult(
        ok=True,
        url=url,
        title=title,
        file_path=rel,
        file_size_bytes=size,
        downloaded_at=downloaded_at,
        duration_sec=duration,
        ext=final_path.suffix.lstrip(".").lower(),
        download_id=uuid.uuid4().hex[:12],
    )
    save_to_central_pool(result)
    return result


def _relative_path(path: Path) -> str:
    path = path.resolve()
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root()
        if root is not None:
            return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        pass
    try:
        return str(path.relative_to(_ilim_root().parent)).replace("\\", "/")
    except ValueError:
        return str(path)


def download_video_with_yt_dlp(
    url: str,
    *,
    out_dir: str | Path | None = None,
) -> VideoDownloadResult:
    """
    Verilen URL'yi yt-dlp ile en iyi kalitede indirir ve merkezi havuza kaydeder.

    Öncelik: Python ``yt_dlp`` modülü → PATH'teki ``yt-dlp`` CLI.
    Çıktı klasörü: ``RUZGAR_VIDEO_DOWNLOAD_DIR`` veya ``hafiza/video_indirilen``.
    """
    err = _validate_url(url)
    downloaded_at = _utc_now_iso()
    if err:
        result = VideoDownloadResult(
            ok=False,
            url=(url or "").strip(),
            downloaded_at=downloaded_at,
            error=err,
        )
        save_to_central_pool(result)
        return result

    target = Path(out_dir).resolve() if out_dir else _default_download_dir()
    target.mkdir(parents=True, exist_ok=True)

    try:
        import yt_dlp  # noqa: F401

        return _download_via_python_api(url.strip(), target)
    except ImportError:
        pass

    exe = _yt_dlp_cli()
    if exe:
        return _download_via_cli(url.strip(), target, exe)

    result = VideoDownloadResult(
        ok=False,
        url=url.strip(),
        downloaded_at=downloaded_at,
        error=(
            "yt-dlp bulunamadı. Kurulum: pip install yt-dlp "
            "veya sistem PATH'ine yt-dlp ekleyin."
        ),
    )
    save_to_central_pool(result)
    return result


# --- Kurgu / timeline mix (FFmpeg) — parça başına en fazla 5 dk ---
EDIT_CLIP_MAX_SEC = 300


@dataclass
class EditClipSegment:
    rel: str
    start_sec: float = 0.0
    end_sec: float | None = None
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rel": self.rel,
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "label": self.label,
        }


@dataclass
class EditMixResult:
    ok: bool
    output_rel: str = ""
    project_id: str = ""
    parts: list[dict[str, Any]] = field(default_factory=list)
    total_duration_sec: float = 0.0
    error: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "output_rel": self.output_rel,
            "project_id": self.project_id,
            "parts": self.parts,
            "total_duration_sec": self.total_duration_sec,
            "edited_at": _utc_now_iso(),
            "error": self.error,
        }


def _resolve_under_repo(rel: str, repo_root: Path | None) -> Path:
    from ilim_assistant.motorlar.programlama_motoru import repo_root as _pr

    root = repo_root or _pr() or _ilim_root().parent
    root = Path(root).resolve()
    rel_norm = rel.replace("\\", "/").lstrip("/")
    if ".." in Path(rel_norm).parts:
        raise ValueError("Göreli yolda .. kullanılamaz.")
    cand = (root / rel_norm).resolve()
    try:
        cand.relative_to(root)
    except ValueError as e:
        raise ValueError("Dosya proje kökünün dışında.") from e
    if not cand.is_file():
        raise FileNotFoundError(str(cand))
    return cand


def _clip_duration_sec(path: Path, start: float, end: float | None) -> float:
    from ilim_assistant.video_ffmpeg import ffprobe_json

    info = ffprobe_json(path)
    total = float((info.get("format") or {}).get("duration") or 0)
    if total <= 0:
        raise ValueError("Medya süresi okunamadı.")
    sp = max(0.0, float(start))
    if end is not None and float(end) > sp:
        dur = float(end) - sp
    else:
        dur = total - sp
    dur = min(dur, EDIT_CLIP_MAX_SEC, total - sp)
    if dur <= 0.01:
        raise ValueError("Geçersiz kesim aralığı.")
    return dur


def save_edit_to_central_pool(
    result: EditMixResult | dict[str, Any],
    *,
    project_name: str = "",
) -> bool:
    """Kurgu projesi ve çıktıyı Merkezi Zihin Havuzu'na yazar."""
    if isinstance(result, EditMixResult):
        meta = result.to_metadata()
        ok = result.ok
        summary = (
            f"Kurgu: {project_name or result.project_id}\n"
            f"Parça: {len(result.parts)} · Çıktı: {result.output_rel}\n"
            f"Toplam süre: {result.total_duration_sec:.1f} sn"
        )
        if not ok:
            summary = f"Kurgu hatası: {result.error}"
    else:
        meta = dict(result)
        ok = bool(meta.get("ok"))
        summary = json.dumps(meta, ensure_ascii=False)[:4000]

    try:
        havuz = get_havuz()
        pid = str(meta.get("project_id") or uuid.uuid4().hex[:12])
        meta["project_id"] = pid
        meta["project_name"] = (project_name or "").strip() or pid

        havuz.publish_shared(
            "video",
            f"kurgu:{pid}",
            summary,
            priority=6 if ok else 2,
            ttl_sec=int(os.environ.get("RUZGAR_VIDEO_EDIT_TTL", "172800")),
        )
        havuz.motor_set("video", f"edit:{pid}", meta)

        doc = havuz.json_load("video", default={"downloads": [], "edits": []})
        if not isinstance(doc, dict):
            doc = {"downloads": [], "edits": []}
        edits = doc.setdefault("edits", [])
        if not isinstance(edits, list):
            edits = []
            doc["edits"] = edits
        edits.append(meta)
        cap = max(5, int(os.environ.get("RUZGAR_VIDEO_EDITS_MAX", "80")))
        if len(edits) > cap:
            doc["edits"] = edits[-cap:]
        doc["updated_at"] = _utc_now_iso()
        havuz.json_save("video", doc)
        return True
    except Exception:
        return False


def mix_timeline_clips(
    clips: list[EditClipSegment | dict[str, Any]],
    *,
    workspace_root: str | Path | None = None,
    copy_streams: bool = True,
    project_name: str = "",
) -> EditMixResult:
    """
    Timeline parçalarını kesip FFmpeg concat ile uç uca birleştirir.
    Her parça en fazla ``EDIT_CLIP_MAX_SEC`` (5 dk) saniyedir.
    """
    from ilim_assistant.video_ffmpeg import (
        concat_many_files,
        export_directory,
        trim_media,
    )

    project_id = uuid.uuid4().hex[:12]
    if not clips:
        res = EditMixResult(ok=False, project_id=project_id, error="Parça listesi boş.")
        save_edit_to_central_pool(res, project_name=project_name)
        return res

    root = Path(workspace_root).resolve() if workspace_root else _ilim_root().parent
    export_dir = export_directory(str(root))
    part_paths: list[Path] = []
    part_meta: list[dict[str, Any]] = []
    total_dur = 0.0

    try:
        for i, raw in enumerate(clips):
            if isinstance(raw, EditClipSegment):
                seg = raw
            else:
                seg = EditClipSegment(
                    rel=str(raw.get("rel") or ""),
                    start_sec=float(raw.get("start_sec") or 0),
                    end_sec=raw.get("end_sec"),
                    label=str(raw.get("label") or f"Parça {i + 1}"),
                )
            if not seg.rel.strip():
                raise ValueError(f"Parça {i + 1}: dosya yolu boş.")

            src = _resolve_under_repo(seg.rel, root)
            dur = _clip_duration_sec(src, seg.start_sec, seg.end_sec)
            part_out = export_dir / f"ruzgar_mixpart_{project_id}_{i:02d}.mp4"
            trim_media(
                src,
                part_out,
                start_sec=seg.start_sec,
                duration_sec=dur,
                copy_streams=bool(copy_streams),
            )
            part_paths.append(part_out)
            total_dur += dur
            part_meta.append(
                {
                    **seg.to_dict(),
                    "duration_sec": dur,
                    "part_file": _relative_path(part_out),
                }
            )

        final_name = f"ruzgar_kurgu_{project_id}.mp4"
        final_path = export_dir / final_name
        concat_many_files(part_paths, final_path, copy_streams=bool(copy_streams))
        out_rel = _relative_path(final_path)

        res = EditMixResult(
            ok=True,
            output_rel=out_rel,
            project_id=project_id,
            parts=part_meta,
            total_duration_sec=total_dur,
        )
        save_edit_to_central_pool(res, project_name=project_name)
        return res
    except Exception as e:
        res = EditMixResult(
            ok=False,
            project_id=project_id,
            parts=part_meta,
            total_duration_sec=total_dur,
            error=str(e),
        )
        save_edit_to_central_pool(res, project_name=project_name)
        return res


def list_recent_edits(limit: int = 10) -> list[dict[str, Any]]:
    try:
        doc = get_havuz().json_load("video", default={"edits": []})
        rows = list(doc.get("edits") or [])
        if not isinstance(rows, list):
            return []
        return list(reversed(rows[-max(1, limit) :]))
    except Exception:
        return []


def list_recent_downloads(limit: int = 10) -> list[dict[str, Any]]:
    """Merkezi havuzdaki son video indirmeleri."""
    try:
        doc = get_havuz().json_load("video", default={"downloads": []})
        rows = list(doc.get("downloads") or [])
        if not isinstance(rows, list):
            return []
        return list(reversed(rows[-max(1, limit) :]))
    except Exception:
        return []


def build_motor_context(message: str) -> str:
    """Video modu LLM bağlamı + son indirmeler özeti."""
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    base = dinamit_heartbeat() + (
        f"[VIDEO MOTORU — {MIMAR_IMZA}]\n"
        "Bu modda cevapları sahne, çekim ve kurgu adımlarıyla planla. "
        "İndirme: ``download_video_with_yt_dlp(url)`` · Kurgu: ``mix_timeline_clips`` (FFmpeg, parça ≤5 dk). "
        "Metadata otomatik olarak Merkezi Zihin Havuzu'na yazılır.\n"
        f"Kullanici mesaji: {prompt}\n"
    )

    recent = list_recent_downloads(3)
    if recent:
        lines = ["[VIDEO MOTORU — son indirmeler]"]
        for row in recent:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('title', '?')} | {row.get('file_path', '')} | "
                f"{row.get('downloaded_at', '')} | {row.get('file_size_bytes', 0)} B"
            )
        base = base.rstrip() + "\n" + "\n".join(lines) + "\n"

    edits = list_recent_edits(2)
    if edits:
        elines = ["[VIDEO MOTORU — son kurgular]"]
        for row in edits:
            if not isinstance(row, dict):
                continue
            elines.append(
                f"- {row.get('project_name', row.get('project_id', '?'))} | "
                f"{row.get('output_rel', '')} | {row.get('total_duration_sec', 0):.0f} sn"
            )
        base = base.rstrip() + "\n" + "\n".join(elines) + "\n"

    try:
        pool_blk = get_havuz().build_motor_pool_context(
            consumer_motor="video",
            message=prompt,
            include_rag=False,
            include_sohbet=False,
        )
        if pool_blk.strip():
            base = base.rstrip() + "\n\n" + pool_blk.strip() + "\n"
    except Exception:
        pass

    return base
