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
import tempfile
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


def ytdlp_available() -> bool:
    """Python yt_dlp modülü veya PATH'te yt-dlp CLI."""
    try:
        import yt_dlp  # type: ignore[import-untyped]  # noqa: F401

        return True
    except ImportError:
        return bool(_yt_dlp_cli())


def _format_best() -> str:
    return os.environ.get("RUZGAR_YTDLP_FORMAT", "bestvideo+bestaudio/best").strip() or "best"


def _ytdlp_cookie_opts() -> dict[str, Any]:
    """
    YouTube bot engeli için tarayıcı çerezleri.
    RUZGAR_YTDLP_COOKIES_BROWSER=edge|chrome|firefox (Windows'ta varsayılan: edge)
    Kapat: RUZGAR_YTDLP_COOKIES_BROWSER=0
    Alternatif: RUZGAR_YTDLP_COOKIES_FILE=path/to/cookies.txt
    """
    raw = (os.environ.get("RUZGAR_YTDLP_COOKIES_BROWSER", "") or "").strip()
    if raw.lower() in ("0", "false", "no", "off", "none"):
        return {}
    cookie_file = (os.environ.get("RUZGAR_YTDLP_COOKIES_FILE", "") or "").strip()
    if cookie_file:
        p = Path(cookie_file)
        if p.is_file():
            return {"cookiefile": str(p.resolve())}
    browser = raw
    if not browser and os.name == "nt":
        browser = "edge"
    if not browser:
        return {}
    if ":" in browser:
        name, profile = browser.split(":", 1)
        return {"cookiesfrombrowser": (name.strip(), profile.strip(), None, None)}
    return {"cookiesfrombrowser": (browser,)}


def _ytdlp_cookie_cli_args() -> list[str]:
    opts = _ytdlp_cookie_opts()
    if "cookiefile" in opts:
        return ["--cookies", str(opts["cookiefile"])]
    cfb = opts.get("cookiesfrombrowser")
    if not cfb:
        return []
    if isinstance(cfb, tuple) and len(cfb) >= 2 and cfb[1]:
        return [f"--cookies-from-browser", f"{cfb[0]}:{cfb[1]}"]
    return ["--cookies-from-browser", str(cfb[0])]


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


_VIDEO_FILE_SUFFIXES = frozenset({".mp4", ".mkv", ".webm", ".m4a", ".mov", ".m4v", ".avi"})
_FRAGMENT_SUFFIX_RE = re.compile(r"\.f\d+\.[a-z0-9]+$", re.IGNORECASE)


def _is_video_output_file(path: Path) -> bool:
    if not path.is_file():
        return False
    name = path.name.lower()
    if name.endswith((".part", ".ytdl", ".tmp")):
        return False
    if _FRAGMENT_SUFFIX_RE.search(name):
        return False
    return path.suffix.lower() in _VIDEO_FILE_SUFFIXES


def _resolve_ytdlp_output_path(
    info: dict[str, Any],
    out_dir: Path,
    *,
    ydl: Any | None = None,
    hook_path: Path | None = None,
) -> Path | None:
    """yt-dlp birleştirme sonrası nihai dosyayı bul (Windows/merge uyumlu)."""
    candidates: list[Path] = []

    if hook_path and _is_video_output_file(hook_path):
        candidates.append(hook_path)

    for rd in reversed(info.get("requested_downloads") or []):
        if not isinstance(rd, dict):
            continue
        for key in ("filepath", "filename"):
            raw = rd.get(key)
            if raw:
                candidates.append(Path(str(raw)))

    if ydl is not None:
        try:
            candidates.append(Path(str(ydl.prepare_filename(info))))
        except Exception:
            pass
        merge_ext = (os.environ.get("RUZGAR_YTDLP_MERGE_EXT", "mp4") or "mp4").strip().lstrip(".")
        vid = str(info.get("id") or "").strip()
        if vid:
            for p in out_dir.glob(f"*{vid}*"):
                if _is_video_output_file(p):
                    candidates.append(p)
        for cand in list(candidates):
            if cand.suffix.lower().lstrip(".") != merge_ext:
                alt = cand.with_suffix(f".{merge_ext}")
                candidates.append(alt)

    seen: set[str] = set()
    for cand in candidates:
        for p in (cand, cand.resolve()):
            key = str(p).lower()
            if key in seen:
                continue
            seen.add(key)
            if _is_video_output_file(p):
                return p

    best: Path | None = None
    best_mtime = 0.0
    for p in out_dir.rglob("*"):
        if not _is_video_output_file(p):
            continue
        try:
            mt = p.stat().st_mtime
        except OSError:
            continue
        if mt >= best_mtime:
            best_mtime = mt
            best = p
    return best


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


def _format_ytdlp_error(exc: Exception) -> str:
    raw = str(exc or "").strip()
    while raw.upper().startswith("ERROR:"):
        raw = raw[6:].strip()
    if not raw:
        raw = exc.__class__.__name__
    low = raw.lower()
    if "could not copy" in low and "cookie" in low:
        return (
            "Tarayıcı çerezleri okunamadı (Edge/Chrome açık olabilir — tarayıcıyı kapatıp tekrar deneyin). "
            "Alternatif: YouTube'a giriş yapıp cookies.txt dışa aktarın → "
            "RUZGAR_YTDLP_COOKIES_FILE=... (RUZGAR_BRAIN.env)."
        )
    if "video unavailable" in low:
        return (
            "YouTube videosu erişilemiyor (kaldırılmış, gizli, bölge kısıtı veya yaş sınırı olabilir). "
            "Başka bir link deneyin veya yt-dlp güncelleyin: pip install -U yt-dlp"
        )
    if "sign in" in low or "login" in low or "cookies" in low or "not a bot" in low:
        browser = (os.environ.get("RUZGAR_YTDLP_COOKIES_BROWSER", "") or "").strip()
        if not browser and os.name == "nt":
            browser = "edge (varsayılan)"
        hint = (
            f" RUZGAR_BRAIN.env içine RUZGAR_YTDLP_COOKIES_BROWSER=edge ekleyin "
            f"(Chrome kullanıyorsan chrome). Şu an: {browser or 'kapalı'}."
        )
        return (
            "YouTube oturum/çerez istiyor (bot koruması)."
            + hint
        )
    return raw[:4000]


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
        "restrictfilenames": True,
        **_ytdlp_cookie_opts(),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True) or {}
    except Exception as e:
        return VideoDownloadResult(
            ok=False,
            url=url,
            downloaded_at=downloaded_at,
            error=_format_ytdlp_error(e),
        )

    final_path = _resolve_ytdlp_output_path(info, out_dir, ydl=ydl, hook_path=final_path)

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
    argv.extend(_ytdlp_cookie_cli_args())

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

    final_path = _resolve_ytdlp_output_path({}, out_dir)

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


def download_audio_with_yt_dlp(
    url: str,
    *,
    max_duration_sec: int = 90,
    out_dir: str | Path | None = None,
) -> VideoDownloadResult:
    """URL'den yalnızca ses (referans klon için) — tam video indirmez."""
    err = _validate_url(url)
    downloaded_at = _utc_now_iso()
    if err:
        return VideoDownloadResult(
            ok=False,
            url=(url or "").strip(),
            downloaded_at=downloaded_at,
            error=err,
        )

    target = Path(out_dir).resolve() if out_dir else _default_download_dir()
    target.mkdir(parents=True, exist_ok=True)
    max_d = max(15, min(120, int(max_duration_sec or 90)))
    info: dict[str, Any] = {}

    try:
        import yt_dlp  # type: ignore[import-untyped]
    except ImportError:
        exe = _yt_dlp_cli()
        if not exe:
            return VideoDownloadResult(
                ok=False,
                url=url.strip(),
                downloaded_at=downloaded_at,
                error="yt-dlp bulunamadı.",
            )
        outtmpl = str(target / "ref-audio-%(id)s.%(ext)s")
        argv = [
            exe,
            url.strip(),
            "-f",
            "bestaudio/best",
            "-x",
            "--audio-format",
            "wav",
            "-o",
            outtmpl,
            "--no-playlist",
            "--no-warnings",
        ]
        argv.extend(_ytdlp_cookie_cli_args())
        try:
            r = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=int(os.environ.get("RUZGAR_YTDLP_TIMEOUT", "7200")),
                cwd=str(target),
            )
        except subprocess.TimeoutExpired:
            return VideoDownloadResult(
                ok=False,
                url=url.strip(),
                downloaded_at=downloaded_at,
                error="yt-dlp ses indirme zaman aşımı.",
            )
        if r.returncode != 0:
            return VideoDownloadResult(
                ok=False,
                url=url.strip(),
                downloaded_at=downloaded_at,
                error=(r.stderr or r.stdout or "yt-dlp ses hatası")[:4000],
            )
        wavs = sorted(target.glob("ref-audio-*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not wavs:
            return VideoDownloadResult(
                ok=False,
                url=url.strip(),
                downloaded_at=downloaded_at,
                error="Ses dosyası oluşmadı.",
            )
        final_path = wavs[0]
    else:
        outtmpl = str(target / "ref-audio-%(id)s.%(ext)s")
        final_path: Path | None = None

        def _hook(d: dict[str, Any]) -> None:
            nonlocal final_path
            if d.get("status") == "finished":
                fp = d.get("filename") or d.get("info_dict", {}).get("_filename")
                if fp:
                    final_path = Path(str(fp))

        ydl_opts: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "quiet": os.environ.get("RUZGAR_YTDLP_QUIET", "1").strip() in ("1", "true", "yes"),
            "no_warnings": True,
            "noplaylist": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "progress_hooks": [_hook],
            **_ytdlp_cookie_opts(),
        }
        info: dict[str, Any] = {}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url.strip(), download=True) or {}
        except Exception as e:
            return VideoDownloadResult(
                ok=False,
                url=url.strip(),
                downloaded_at=downloaded_at,
                error=_format_ytdlp_error(e),
            )
        final_path = _resolve_ytdlp_output_path(info, target, ydl=ydl, hook_path=final_path)
        if final_path and final_path.suffix.lower() != ".wav":
            alt = final_path.with_suffix(".wav")
            if alt.is_file():
                final_path = alt

    if final_path is None or not final_path.is_file():
        return VideoDownloadResult(
            ok=False,
            url=url.strip(),
            downloaded_at=downloaded_at,
            error="Ses indirme tamamlandı ancak dosya bulunamadı.",
        )

    trimmed = final_path
    try:
        from ilim_assistant.video_ffmpeg import ffmpeg_available, run_ffmpeg_args

        if ffmpeg_available() and max_d > 0:
            fd, tmp = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            tmp_path = Path(tmp)
            run_ffmpeg_args(
                [
                    "-y",
                    "-t",
                    str(max_d),
                    "-i",
                    str(final_path.resolve()),
                    "-ar",
                    "22050",
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    str(tmp_path.resolve()),
                ],
                timeout_sec=300,
            )
            trimmed = tmp_path
            if final_path.name.startswith("ref-audio-"):
                try:
                    final_path.unlink(missing_ok=True)
                except OSError:
                    pass
            dest = target / f"ref-audio-trim-{uuid.uuid4().hex[:8]}.wav"
            shutil.move(str(trimmed), str(dest))
            final_path = dest
    except Exception:
        pass

    size, duration = _probe_file(final_path)
    rel = _relative_path(final_path)
    result = VideoDownloadResult(
        ok=True,
        url=url.strip(),
        title=str(info.get("title") or final_path.stem),
        file_path=rel,
        file_size_bytes=size,
        downloaded_at=downloaded_at,
        duration_sec=min(duration, float(max_d)) if duration else float(max_d),
        ext="wav",
        download_id=uuid.uuid4().hex[:12],
        extra={"audio_only": True, "max_duration_sec": max_d},
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

    try:
        from ilim_assistant.motorlar.video_faz71 import augment_video_context

        return augment_video_context(base)
    except Exception:
        return base
