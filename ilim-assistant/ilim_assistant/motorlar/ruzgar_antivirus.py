# Created by Ümit & Gökçenur
"""
Rüzgar Virüs Kalkanı v2 — çok katmanlı tarama, risk skoru, nötralizasyon.

Birincil motor (Defender yedek değil). Katmanlar:
  politika · sihirli bayt · gömülü PE · entropi · arşiv (zip) · PDF/HTML/Office heuristik
  · imza · regex · kara liste · isteğe bağlı Clam/Defender yedek
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

ENGINE_NAME = "Rüzgar Virüs Kalkanı"
ENGINE_VERSION = "ruzgar-av-v2-2026-06-04"

_SCAN_QUICK_BYTES = 8 * 1024 * 1024
_SCAN_DEEP_BYTES = 64 * 1024 * 1024
_ENTROPY_SUSPICIOUS = 7.45
_ENTROPY_CRITICAL = 7.85
_ZIP_MAX_ENTRIES = 5000
_ZIP_MAX_RATIO = 120
_ZIP_MAX_UNCOMPRESSED_MB = 512

_MAGIC: dict[str, tuple[bytes, ...]] = {
    ".pdf": (b"%PDF",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".zip": (b"PK\x03\x04", b"PK\x05\x06"),
    ".epub": (b"PK\x03\x04",),
    ".docx": (b"PK\x03\x04",),
    ".xlsx": (b"PK\x03\x04",),
    ".pptx": (b"PK\x03\x04",),
    ".md": (),
    ".txt": (),
    ".html": (),
    ".htm": (),
    ".mp4": (b"\x00\x00\x00",),
    ".webm": (b"\x1a\x45\xdf\xa3",),
    ".mkv": (b"\x1a\x45\xdf\xa3",),
    ".m4a": (),
    ".mp3": (b"ID3", b"\xff\xfb"),
    ".wav": (b"RIFF",),
    ".flac": (b"fLaC",),
}

_PE_MAGICS = (b"MZ", b"\x7fELF")
_DOUBLE_EXT_RE = re.compile(
    r"\.(pdf|docx|epub|txt|png|jpg|jpeg|mp4|zip|md|html|xlsx|pptx)\."
    r"(exe|bat|cmd|scr|js|vbs|ps1|msi|dll|hta|jar|com|pif)$",
    re.I,
)
_HOMOGRAPH_RE = re.compile(r"[^\x00-\x7F]")  # filename RTL override etc.


@dataclass
class LayerHit:
    layer: str
    threats: list[str]
    severity: str = "medium"

    @property
    def weight(self) -> int:
        return {"low": 8, "medium": 18, "high": 35, "critical": 55}.get(self.severity, 15)


@dataclass
class RuzgarScanVerdict:
    clean: bool
    risk_score: int = 0
    severity: str = "clean"
    engine: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION
    layers: list[str] = field(default_factory=list)
    layer_details: dict[str, list[str]] = field(default_factory=dict)
    threats: list[str] = field(default_factory=list)
    detail: str = ""
    sha256: str = ""
    scan_mode: str = "deep"
    bytes_scanned: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "engine": self.engine,
            "engine_version": self.engine_version,
            "layers": self.layers,
            "layer_details": self.layer_details,
            "threats": self.threats,
            "engines": [self.engine],
            "detail": self.detail,
            "sha256": self.sha256,
            "scan_mode": self.scan_mode,
            "bytes_scanned": self.bytes_scanned,
        }


def _data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def _load_json(name: str) -> dict[str, Any]:
    p = _data_dir() / name
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _scan_byte_limit(mode: str) -> int:
    if (mode or "deep").strip().lower() == "quick":
        return _SCAN_QUICK_BYTES
    return _SCAN_DEEP_BYTES


def _file_sha256(path: Path, limit: int | None = None) -> str:
    h = hashlib.sha256()
    cap = limit
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            if cap is not None:
                if len(chunk) > cap:
                    chunk = chunk[:cap]
                    h.update(chunk)
                    break
                cap -= len(chunk)
            h.update(chunk)
            if cap is not None and cap <= 0:
                break
    return h.hexdigest()


def _read_sample(path: Path, limit: int) -> bytes:
    with path.open("rb") as f:
        return f.read(limit)


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    ent = 0.0
    ln = len(data)
    for c in freq:
        if c:
            p = c / ln
            ent -= p * math.log2(p)
    return ent


def _severity_from_score(score: int) -> str:
    if score >= 55:
        return "critical"
    if score >= 35:
        return "high"
    if score >= 18:
        return "medium"
    if score >= 8:
        return "low"
    return "clean"


def check_url_reputation(url: str) -> list[str]:
    """İndirme öncesi URL itibar kontrolü."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return ["Geçersiz URL"]
    if not host:
        return ["Boş alan adı"]
    raw = _load_json("ruzgar_url_blocklist.json")
    for exact in raw.get("exact_hosts") or []:
        if host == str(exact).lower():
            return [f"Engelli alan adı: {host}"]
    for sub in raw.get("host_substrings") or []:
        s = str(sub).lower()
        if s and s in host:
            return [f"Şüpheli alan adı kalıbı: {s}"]
    return []


def _layer_extension_policy(name: str) -> list[LayerHit]:
    from ilim_assistant.motorlar.ruzgar_virus_guard import extension_blocked

    hits: list[LayerHit] = []
    ext = extension_blocked(name)
    if ext:
        hits.append(LayerHit("uzanti", [f"Engellenen uzantı: {ext}"], "critical"))
    if _DOUBLE_EXT_RE.search(name or ""):
        hits.append(LayerHit("uzanti", ["Çift uzantı tuzağı"], "critical"))
    if _HOMOGRAPH_RE.search(Path(name).stem):
        hits.append(LayerHit("uzanti", ["Dosya adında Unicode homograf"], "medium"))
    return hits


def _layer_magic_mismatch(path: Path) -> list[LayerHit]:
    ext = path.suffix.lower()
    if ext not in _MAGIC or not _MAGIC[ext]:
        return []
    head = _read_sample(path, 64)
    if not head:
        return [LayerHit("sihirli-bayt", ["Boş dosya"], "high")]
    for sig in _MAGIC[ext]:
        if head.startswith(sig):
            return []
        if ext == ".mp4" and len(head) >= 12 and head[4:8] == b"ftyp":
            return []
    return [LayerHit("sihirli-bayt", [f"İçerik {ext} ile uyuşmuyor"], "high")]


def _layer_embedded_executable(path: Path, name: str) -> list[LayerHit]:
    low = name.lower()
    if low.endswith((".exe", ".dll", ".msi", ".scr", ".com", ".bat", ".cmd")):
        return []
    data = _read_sample(path, 4096)
    hits: list[LayerHit] = []
    if data.startswith(b"MZ"):
        hits.append(LayerHit("pe", ["Gömülü MZ (Windows PE)"], "critical"))
        if len(data) >= 64:
            try:
                pe_off = struct.unpack_from("<I", data, 0x3C)[0]
                if 64 <= pe_off < len(data) - 2 and data[pe_off : pe_off + 2] == b"PE":
                    hits.append(LayerHit("pe", ["Geçerli PE başlığı gizli dosyada"], "critical"))
            except struct.error:
                pass
    if data.startswith(b"\x7fELF"):
        hits.append(LayerHit("pe", ["Gömülü ELF"], "critical"))
    return hits


def _layer_entropy(path: Path, ext: str, limit: int) -> list[LayerHit]:
    if ext in (".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".wav", ".flac", ".zip", ".jpg", ".jpeg", ".png"):
        return []
    sample = _read_sample(path, min(limit, 2 * 1024 * 1024))
    if len(sample) < 256:
        return []
    ent = _entropy(sample)
    if ent >= _ENTROPY_CRITICAL:
        return [LayerHit("entropi", [f"Çok yüksek entropi ({ent:.2f}) — şifreli/paketli"], "high")]
    if ent >= _ENTROPY_SUSPICIOUS:
        return [LayerHit("entropi", [f"Yüksek entropi ({ent:.2f})"], "medium")]
    return []


def _layer_archive(path: Path, limit: int) -> list[LayerHit]:
    if path.suffix.lower() not in (".zip", ".docx", ".xlsx", ".pptx", ".epub", ".jar"):
        return []
    hits: list[LayerHit] = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            infos = zf.infolist()
            if len(infos) > _ZIP_MAX_ENTRIES:
                hits.append(LayerHit("arsiv", [f"Zip çok fazla giriş ({len(infos)})"], "high"))
            total_uncompressed = 0
            for info in infos[:2000]:
                total_uncompressed += int(info.file_size or 0)
                n = (info.filename or "").lower()
                if n.endswith((".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".hta", ".dll")):
                    hits.append(LayerHit("arsiv", [f"Arşiv içinde yürütülebilir: {n}"], "critical"))
                if "vba" in n or "macro" in n or n.endswith(".bin") and "vba" in n:
                    hits.append(LayerHit("arsiv", [f"Arşiv içinde makro izi: {n}"], "high"))
            if path.stat().st_size > 0:
                ratio = total_uncompressed / max(path.stat().st_size, 1)
                if ratio > _ZIP_MAX_RATIO:
                    hits.append(LayerHit("arsiv", [f"Zip bomba oranı ({ratio:.0f}x)"], "critical"))
            if total_uncompressed > _ZIP_MAX_UNCOMPRESSED_MB * 1024 * 1024:
                hits.append(LayerHit("arsiv", ["Arşiv açılmış boyut sınırı aşıldı"], "high"))
    except zipfile.BadZipFile:
        if path.suffix.lower() == ".zip":
            hits.append(LayerHit("arsiv", ["Bozuk veya sahte zip"], "medium"))
    except Exception as exc:
        hits.append(LayerHit("arsiv", [f"Arşiv okunamadı: {str(exc)[:80]}"], "low"))
    return hits


def _layer_content_heuristics(path: Path, limit: int) -> list[LayerHit]:
    data = _read_sample(path, limit)
    if not data:
        return []
    hits: list[LayerHit] = []
    low = data.lower()
    if path.suffix.lower() == ".pdf":
        if b"/javascript" in low or b"/js " in low or b"/aa " in low:
            hits.append(LayerHit("pdf", ["PDF içinde JavaScript"], "high"))
        if b"/launch" in low or b"/openaction" in low:
            hits.append(LayerHit("pdf", ["PDF OpenAction/Launch"], "medium"))
        if b"/embeddedfile" in low:
            hits.append(LayerHit("pdf", ["PDF gömülü dosya"], "medium"))
    if path.suffix.lower() in (".html", ".htm", ".svg"):
        if b"<script" in low or b"javascript:" in low:
            hits.append(LayerHit("web", ["HTML/JS aktif içerik"], "high"))
    if b"<hta:application" in low:
        hits.append(LayerHit("hta", ["HTA uygulaması"], "critical"))
    if b"vbaProject.bin" in data or b"vbaData.xml" in data:
        hits.append(LayerHit("office", ["Office makro projesi"], "high"))
    return hits


def _layer_signatures(path: Path, limit: int) -> list[LayerHit]:
    data = _read_sample(path, limit)
    hits: list[LayerHit] = []
    if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in data:
        hits.append(LayerHit("imza", ["EICAR test virüs dizesi"], "critical"))
    if len(data) >= 32 and data[:32] == b"\x90" * 32:
        hits.append(LayerHit("imza", ["Uzun NOP sled (shellcode şüphesi)"], "high"))
    raw = _load_json("ruzgar_threat_signatures.json")
    text = data.decode("utf-8", errors="ignore").lower()
    for item in raw.get("signatures") or []:
        if not isinstance(item, dict):
            continue
        pat = str(item.get("pattern") or "")
        sev = str(item.get("severity") or "medium")
        if not pat:
            continue
        if pat.lower() in text or pat.encode("utf-8", errors="ignore") in data:
            nm = str(item.get("name") or item.get("id") or "imza")
            hits.append(LayerHit("imza", [f"Rüzgar imza: {nm}"], sev))
    return hits


def _layer_regex_rules(path: Path, limit: int) -> list[LayerHit]:
    raw = _load_json("ruzgar_threat_rules.json")
    rules = raw.get("rules") or []
    if not rules:
        return []
    text = _read_sample(path, min(limit, 4 * 1024 * 1024)).decode("utf-8", errors="ignore")
    hits: list[LayerHit] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        pat = str(rule.get("pattern") or "")
        if not pat:
            continue
        try:
            if re.search(pat, text, re.I | re.M):
                nm = str(rule.get("name") or rule.get("id") or "kural")
                sev = str(rule.get("severity") or "medium")
                hits.append(LayerHit("regex", [f"Rüzgar kural: {nm}"], sev))
        except re.error:
            continue
    return hits


def _layer_hash_blocklist(path: Path) -> list[LayerHit]:
    raw = _load_json("ruzgar_threat_hashes.json")
    hashes = raw.get("hashes") or []
    if not hashes:
        return []
    digest = _file_sha256(path)
    for row in hashes:
        if isinstance(row, str) and row.lower() == digest:
            return [LayerHit("kara-liste", ["Bilinen zararlı SHA-256"], "critical")]
        if isinstance(row, dict) and str(row.get("sha256", "")).lower() == digest:
            label = str(row.get("name") or "kara liste")
            return [LayerHit("kara-liste", [f"Kara liste: {label}"], "critical")]
    return []


def _layer_clam(path: Path) -> list[LayerHit]:
    if os.environ.get("RUZGAR_AV_CLAM_SUPPORT", "0").strip().lower() not in ("1", "true", "yes"):
        return []
    clam = shutil.which("clamscan") or shutil.which("clamscan.exe")
    if not clam:
        return []
    try:
        r = subprocess.run(
            [clam, "--no-summary", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=int(os.environ.get("RUZGAR_AV_CLAM_TIMEOUT", "600")),
        )
        if r.returncode == 1:
            line = (r.stdout or r.stderr or "").strip().splitlines()
            return [LayerHit("clam", [line[-1][:200] if line else "Clam tehdit"], "high")]
    except Exception as exc:
        return [LayerHit("clam", [str(exc)[:100]], "medium")]
    return []


def _layer_defender_backup(path: Path) -> list[LayerHit]:
    if os.environ.get("RUZGAR_AV_DEFENDER_BACKUP", "0").strip().lower() not in ("1", "true", "yes"):
        return []
    dp = os.path.expandvars(r"%ProgramFiles%\Windows Defender\MpCmdRun.exe")
    if not os.path.isfile(dp):
        return []
    try:
        r = subprocess.run(
            [dp, "-Scan", "-ScanType", "3", "-File", str(path.resolve())],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        out = ((r.stdout or "") + (r.stderr or "")).lower()
        if r.returncode == 2 or "threat" in out:
            return [LayerHit("defender-yedek", ["Defender yedek: tehdit"], "high")]
    except Exception:
        pass
    return []


def _is_trusted_hash(path: Path) -> bool:
    raw = _load_json("ruzgar_trusted_hashes.json")
    trusted = raw.get("hashes") or []
    if not trusted:
        return False
    digest = _file_sha256(path, limit=64 * 1024 * 1024)
    for row in trusted:
        h = row if isinstance(row, str) else str((row or {}).get("sha256") or "")
        if h.lower() == digest:
            return True
    return False


def ruzgar_scan_file(path: Path | str, *, mode: str = "deep") -> RuzgarScanVerdict:
    """Ana tarama — quick veya deep."""
    target = Path(path).resolve()
    if not target.is_file():
        return RuzgarScanVerdict(False, 100, "critical", threats=["Dosya bulunamadı"], detail="yok")

    scan_mode = (mode or "deep").strip().lower()
    if scan_mode not in ("quick", "deep"):
        scan_mode = "deep"
    limit = _scan_byte_limit(scan_mode)
    name = target.name
    ext = target.suffix.lower()

    if _is_trusted_hash(target):
        digest = _file_sha256(target, limit=limit)
        return RuzgarScanVerdict(
            True,
            0,
            "clean",
            layers=["guvenilir-ozet"],
            layer_details={"guvenilir-ozet": ["Bilinen temiz dosya özeti"]},
            detail="guvenilir özet",
            sha256=digest,
            scan_mode=scan_mode,
            bytes_scanned=min(target.stat().st_size, limit),
        )

    layer_fns: list[tuple[str, Callable[[], list[LayerHit]]]] = [
        ("uzanti-politikasi", lambda: _layer_extension_policy(name)),
        ("sihirli-bayt", lambda: _layer_magic_mismatch(target)),
        ("gömülü-pe", lambda: _layer_embedded_executable(target, name)),
        ("entropi", lambda: _layer_entropy(target, ext, limit)),
        ("icerik-heuristik", lambda: _layer_content_heuristics(target, limit)),
        ("imza", lambda: _layer_signatures(target, limit)),
        ("regex", lambda: _layer_regex_rules(target, limit)),
        ("kara-liste", lambda: _layer_hash_blocklist(target)),
    ]
    if scan_mode == "deep":
        layer_fns.insert(4, ("arsiv", lambda: _layer_archive(target, limit)))
        layer_fns.extend(
            [
                ("clam-destek", lambda: _layer_clam(target)),
                ("defender-yedek", lambda: _layer_defender_backup(target)),
            ]
        )

    layers_run: list[str] = []
    layer_details: dict[str, list[str]] = {}
    all_threats: list[str] = []
    risk = 0

    for layer_id, fn in layer_fns:
        layers_run.append(layer_id)
        for hit in fn():
            layer_details.setdefault(hit.layer, []).extend(hit.threats)
            all_threats.extend(hit.threats)
            risk = min(100, risk + hit.weight)
            if hit.severity == "critical" and os.environ.get("RUZGAR_AV_FAIL_FAST", "1") not in ("0", "false"):
                break
        if risk >= 55 and os.environ.get("RUZGAR_AV_FAIL_FAST", "1") not in ("0", "false"):
            break

    digest = _file_sha256(target, limit=limit if scan_mode == "quick" else None)
    severity = _severity_from_score(risk)
    clean = len(all_threats) == 0
    detail = "temiz" if clean else f"{len(all_threats)} sinyal · risk {risk}"

    return RuzgarScanVerdict(
        clean=clean,
        risk_score=risk,
        severity=severity,
        layers=layers_run,
        layer_details=layer_details,
        threats=all_threats,
        detail=detail,
        sha256=digest,
        scan_mode=scan_mode,
        bytes_scanned=min(target.stat().st_size, limit),
    )


def _rel_under_repo(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return str(path)


def threats_vault_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[3]
    p = root / "ilim-assistant" / "arsiv" / "_virus_guard_staging" / "threats_neutralized"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _threat_log_path(repo_root: Path) -> Path:
    p = repo_root / "ilim-assistant" / "arsiv" / "_virus_guard_staging" / "ruzgar_threat_log.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _secure_wipe_head(path: Path, nbytes: int = 65536) -> None:
    try:
        size = path.stat().st_size
        with path.open("r+b") as f:
            f.write(b"\x00" * min(nbytes, size))
            if size > 16:
                f.seek(max(0, size - 4096))
                f.write(b"\x00" * min(4096, size))
    except OSError:
        pass


def neutralize_threat(
    path: Path | str,
    verdict: RuzgarScanVerdict | dict[str, Any],
    *,
    source_url: str = "",
) -> dict[str, Any]:
    src = Path(path).resolve()
    if not src.is_file():
        return {"ok": False, "error": "Nötralize edilecek dosya yok"}

    repo = Path(__file__).resolve().parents[3]
    vault = threats_vault_dir(repo)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    nid = uuid.uuid4().hex[:10]
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", src.name)[:120]
    dest = vault / f"{stamp}_{nid}_{safe_name}.ruzgar-quarantined"

    try:
        shutil.move(str(src), str(dest))
    except OSError:
        try:
            shutil.copy2(src, dest)
            src.unlink()
        except OSError as exc:
            return {"ok": False, "error": f"Nötralize: {exc}"}

    _secure_wipe_head(dest)

    vdict = verdict.to_dict() if isinstance(verdict, RuzgarScanVerdict) else dict(verdict)
    record = {
        "ts": time.time(),
        "neutralized_id": nid,
        "vault_rel": _rel_under_repo(dest, repo),
        "original_name": src.name,
        "sha256": vdict.get("sha256") or "",
        "threats": vdict.get("threats") or [],
        "risk_score": vdict.get("risk_score", 100),
        "source_url": (source_url or "")[:500],
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
    }
    try:
        with _threat_log_path(repo).open("a", encoding="utf-8") as log:
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass

    return {
        "ok": True,
        "neutralized": True,
        "neutralized_id": nid,
        "vault_path": str(dest),
        "vault_rel": record["vault_rel"],
        "message": f"{ENGINE_NAME} tehdidi nötralize etti (güvenli kasa).",
    }


def list_threat_log(limit: int = 40) -> dict[str, Any]:
    repo = Path(__file__).resolve().parents[3]
    p = _threat_log_path(repo)
    rows: list[dict[str, Any]] = []
    if p.is_file():
        try:
            lines = p.read_text(encoding="utf-8").strip().splitlines()
            for line in lines[-limit:]:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        except OSError:
            pass
    return {"ok": True, "items": rows, "count": len(rows)}


def engine_capabilities() -> dict[str, Any]:
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "primary": True,
        "layers": [
            "uzanti-politikasi",
            "sihirli-bayt",
            "gömülü-pe",
            "entropi",
            "arsiv",
            "icerik-heuristik",
            "imza",
            "regex",
            "kara-liste",
            "clam-destek",
            "defender-yedek",
        ],
        "scan_modes": ["quick", "deep"],
        "defender_backup": os.environ.get("RUZGAR_AV_DEFENDER_BACKUP", "0"),
        "clam_support": os.environ.get("RUZGAR_AV_CLAM_SUPPORT", "0"),
        "fail_fast": os.environ.get("RUZGAR_AV_FAIL_FAST", "1"),
        "data_files": [
            "ruzgar_threat_signatures.json",
            "ruzgar_threat_rules.json",
            "ruzgar_threat_hashes.json",
            "ruzgar_trusted_hashes.json",
            "ruzgar_url_blocklist.json",
        ],
        "neutralize": True,
        "url_reputation": True,
    }
