# Created by Ümit & Gökçenur
"""Programlama çalışma sayfası — projects/ altını gör, yaz, sil, emri uygula.

Yol projects/ dışına çıkamaz. Ajan masası model çağırmaz; bilinen emri yerelde yazar.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

PROJE_MASA_VERSION = "programlama-proje-masa-v2-2026-10-16"

_DENEME = re.compile(
    r"^(smoke-|t-|agent-|_|"
    r"live-|live_|canli-|debug-|faz\d|heal-)",
    re.I,
)
_YAZI_UZANTI = {
    ".html",
    ".htm",
    ".css",
    ".js",
    ".mjs",
    ".py",
    ".json",
    ".md",
    ".txt",
    ".svg",
    ".xml",
}
_ONIZLEME_MIME = {
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".json": "application/json; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
    ".py": "text/plain; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
    ".ico": "image/x-icon",
}
_YAZI_BAYT = 1_500_000
_ONIZLEME_BAYT = 8_000_000


def normalize_proje_rel(rel: str) -> str:
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw or ":" in raw or "\x00" in raw:
        raise ValueError("Geçersiz yol.")
    parts = [p for p in raw.split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        raise ValueError("Geçersiz yol.")
    if parts[0] != "projects" or len(parts) < 2:
        raise ValueError("Yalnız projects/ altı.")
    if parts[1].startswith(".") or parts[1] in (".", ".."):
        raise ValueError("Geçersiz proje.")
    return "/".join(parts)


def resolve_proje_path(root: Path, rel: str) -> tuple[str, Path]:
    norm = normalize_proje_rel(rel)
    base = Path(root).resolve()
    projects = (base / "projects").resolve()
    target = (base / norm).resolve()
    try:
        target.relative_to(projects)
    except ValueError as exc:
        raise ValueError("Proje dışı.") from exc
    if target == projects:
        raise ValueError("projects klasörünün kendisi açılmaz.")
    return norm, target


def list_projeler(root: Path) -> list[dict]:
    base = Path(root) / "projects"
    if not base.is_dir():
        return []
    rows: list[dict] = []
    for path in base.iterdir():
        if not path.is_dir() or path.name.startswith(".") or path.is_symlink():
            continue
        has_site = (path / "index.html").is_file()
        has_py = (path / "main.py").is_file() or (path / "app" / "main.py").is_file()
        rows.append(
            {
                "name": path.name,
                "rel": f"projects/{path.name}",
                "site": has_site,
                "python": has_py,
                "deneme": bool(_DENEME.match(path.name)),
            }
        )
    rows.sort(key=lambda row: (row["deneme"], not row["site"], row["name"].lower()))
    return rows


def yaz_proje_dosyasi(root: Path, rel: str, text: str) -> dict:
    norm, target = resolve_proje_path(root, rel)
    if target.exists() and target.is_dir():
        raise ValueError("Klasörün üstüne yazılmaz.")
    if target.is_symlink() or (target.exists() and target.is_symlink()):
        raise ValueError("Bağ dosyasına yazılmaz.")
    suffix = target.suffix.lower()
    if suffix not in _YAZI_UZANTI:
        raise ValueError("Bu uzantı çalışma sayfasından yazılmaz.")
    body = text if text is not None else ""
    raw = body.encode("utf-8")
    if len(raw) > _YAZI_BAYT:
        raise ValueError("Metin çok büyük.")
    parent_rel = str(Path(norm).parent).replace("\\", "/")
    if parent_rel != "projects":
        resolve_proje_path(root, parent_rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return {"ok": True, "rel": norm, "bytes": len(raw)}


def sil_proje_yolu(root: Path, rel: str) -> dict:
    norm, target = resolve_proje_path(root, rel)
    if target.is_symlink():
        raise ValueError("Bağ silinmez.")
    if not target.exists():
        raise ValueError("Yok.")
    if target.is_file():
        target.unlink()
        return {"ok": True, "kind": "dosya", "rel": norm}
    if target.is_dir():
        shutil.rmtree(target)
        return {"ok": True, "kind": "klasor", "rel": norm}
    raise ValueError("Silinemedi.")


def proje_klasoru(rel: str) -> str:
    parts = normalize_proje_rel(rel).split("/")
    return "/".join(parts[:2])


def _html_kacis(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _oku_yazi(root: Path, rel: str) -> str:
    norm, target = resolve_proje_path(root, rel)
    if not target.is_file() or target.is_symlink():
        raise ValueError(f"Dosya yok: {norm}")
    return target.read_text(encoding="utf-8")


def _baslik_yaz(html: str, metin: str) -> str:
    safe = _html_kacis(metin)
    if re.search(r"<title\b[^>]*>.*?</title>", html, re.I | re.S):
        html = re.sub(
            r"<title\b[^>]*>.*?</title>",
            f"<title>{safe}</title>",
            html,
            count=1,
            flags=re.I | re.S,
        )
    else:
        html = f"<title>{safe}</title>\n{html}"
    if re.search(r"<h1\b[^>]*>.*?</h1>", html, re.I | re.S):
        html = re.sub(
            r"<h1\b[^>]*>.*?</h1>",
            f"<h1>{safe}</h1>",
            html,
            count=1,
            flags=re.I | re.S,
        )
    return html


def _govdeye_ekle(html: str, parca: str) -> str:
    if re.search(r"</body>", html, re.I):
        return re.sub(r"</body>", parca + "\n</body>", html, count=1, flags=re.I)
    return html + "\n" + parca


def ajan_uygula(root: Path, rel: str, emir: str, dosya: str = "") -> dict:
    """Seçili projede bilinen emri uygular. Bilinmeyen emir dosya yazmaz."""
    text = (emir or "").strip()
    if not text or len(text) > 600:
        raise ValueError("Emir boş veya çok uzun.")
    proje = proje_klasoru(rel)
    adimlar = [f"Proje kilitli: {proje}"]

    from ilim_assistant.motorlar.programlama_tarif import match_tarif, run_tarif

    hit = match_tarif(text)
    if hit is not None:
        recipe, _phrase = hit
        cevap = run_tarif(text, root)
        ilk = cevap.split("\n", 1)[0]
        if "tarif durdu" in cevap or "rafta yok" in cevap:
            raise ValueError(ilk)
        from ilim_assistant.motorlar.programlama_faz6 import _slug
        from ilim_assistant.motorlar.programlama_tarif import _project_name

        slug = _slug(_project_name(text, str(recipe["default_name"])))
        hedef = proje_klasoru(f"projects/{slug}")
        adimlar.append("Tarif yerelden yazıldı. Model yok.")
        adimlar.append(ilk)
        acilan = f"{hedef}/index.html"
        if recipe.get("template") != "static_site":
            acilan = f"{hedef}/main.py"
        _, path = resolve_proje_path(root, acilan if (Path(root) / acilan).is_file() else hedef)
        if not path.exists():
            raise ValueError("Tarif bitti ama proje açılmadı.")
        return {
            "ok": True,
            "adimlar": adimlar,
            "rel": acilan if (Path(root) / acilan).is_file() else hedef,
            "proje": hedef,
            "ozet": ilk,
        }

    baslik = re.match(
        r"^(?:başlığı|basligi|başlık|baslik)\s*(?:yap)?\s*[:\-]?\s*(.+?)(?:\s+yap)?\s*$",
        text,
        re.I,
    )
    paragraf = re.match(r"^paragraf(?:\s+ekle)?\s*[:\-]?\s*(.+)$", text, re.I)
    buton = re.match(r"^buton(?:\s+ekle)?\s*[:\-]?\s*(.+)$", text, re.I)
    yerine = re.match(r"^(.+?)\s+yerine\s+(.+?)\s+yaz\s*$", text, re.I)
    hedef_rel = f"{proje}/index.html"
    if yerine and dosya:
        aday = dosya.replace("\\", "/").lstrip("/")
        if aday.startswith(proje + "/"):
            hedef_rel = normalize_proje_rel(aday)

    if baslik or paragraf or buton or yerine:
        html = _oku_yazi(root, hedef_rel)
        adimlar.append(f"Okundu: {hedef_rel}")
        if baslik:
            metin = baslik.group(1).strip().strip("\"'")
            if not metin or len(metin) > 180:
                raise ValueError("Başlık boş veya çok uzun.")
            html = _baslik_yaz(html, metin)
            adimlar.append("Başlık ve ana satır yazıldı.")
            ozet = "Başlık güncellendi."
        elif paragraf:
            metin = paragraf.group(1).strip().strip("\"'")
            if not metin or len(metin) > 400:
                raise ValueError("Paragraf boş veya çok uzun.")
            html = _govdeye_ekle(html, f"<p>{_html_kacis(metin)}</p>")
            adimlar.append("Paragraf eklendi.")
            ozet = "Paragraf eklendi."
        elif buton:
            metin = buton.group(1).strip().strip("\"'")
            if not metin or len(metin) > 80:
                raise ValueError("Buton yazısı boş veya çok uzun.")
            html = _govdeye_ekle(html, f"<button type=\"button\">{_html_kacis(metin)}</button>")
            adimlar.append("Buton eklendi.")
            ozet = "Buton eklendi."
        else:
            eski = yerine.group(1).strip().strip("\"'")
            yeni = yerine.group(2).strip().strip("\"'")
            if not eski or len(eski) > 180 or len(yeni) > 400:
                raise ValueError("Değiştirilecek metin geçersiz.")
            if eski not in html:
                raise ValueError("Metin dosyada yok.")
            html = html.replace(eski, _html_kacis(yeni) if hedef_rel.endswith((".html", ".htm")) else yeni, 1)
            adimlar.append("Metin bir kez değiştirildi.")
            ozet = "Metin değiştirildi."
        yaz_proje_dosyasi(root, hedef_rel, html)
        adimlar.append(f"Yazıldı: {hedef_rel}")
        return {
            "ok": True,
            "adimlar": adimlar,
            "rel": hedef_rel,
            "proje": proje,
            "ozet": ozet,
        }

    raise ValueError(
        "Bu emri sayfada uygulayamam. "
        "Başlık, paragraf ekle, buton ekle, yerine yaz, basit site yap."
    )


def _pin_dosyasi() -> Path:
    kok = Path(os.environ.get("LOCALAPPDATA") or Path.home())
    return kok / "Ruzgar" / "calisma_klasoru.json"


def _icinde(yol: Path, ust: Path) -> bool:
    try:
        yol.resolve().relative_to(ust.resolve())
        return True
    except ValueError:
        return False


def klasor_guvenli(repo: Path, klasor: str) -> Path:
    """Mimarın gösterdiği klasör. Uygulama ağacı ve sürücü kökü kapalı."""
    raw = (klasor or "").strip().strip('"').strip("'")
    if not raw:
        raise ValueError("Klasör yok.")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ValueError("Klasör tam yol olmalı.")
    if not path.exists() or not path.is_dir():
        raise ValueError("Klasör bulunamadı.")
    if path.is_symlink():
        raise ValueError("Bağ klasör açılmaz.")
    resolved = path.resolve()
    if resolved.parent == resolved:
        raise ValueError("Sürücü kökü açılmaz.")
    base = Path(repo).resolve()
    kapali = (base / "ilim-assistant", base / "ruzgar-desktop", base / ".git")
    if resolved == base:
        raise ValueError("Uygulama kökü açılmaz.")
    for dal in kapali:
        if resolved == dal or _icinde(resolved, dal):
            raise ValueError("Uygulama klasörü açılmaz.")
        if dal.exists() and _icinde(dal.resolve(), resolved):
            raise ValueError("Uygulama klasörünü içeren yer açılmaz.")
    return resolved


def klasor_kaydet(repo: Path, klasor: str) -> dict:
    pin = _pin_dosyasi()
    pin.parent.mkdir(parents=True, exist_ok=True)
    if not (klasor or "").strip():
        if pin.is_file():
            pin.unlink()
        return {"ok": True, "klasor": ""}
    hedef = klasor_guvenli(repo, klasor)
    pin.write_text(json.dumps({"klasor": str(hedef)}, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "klasor": str(hedef)}


def klasor_oku() -> str:
    pin = _pin_dosyasi()
    if not pin.is_file():
        return ""
    try:
        data = json.loads(pin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(data.get("klasor") or "")


def _klasor_hedef(repo: Path, rel: str) -> tuple[Path, str]:
    kayit = klasor_oku()
    if not kayit:
        raise ValueError("Çalışma klasörü seçilmedi.")
    kok = klasor_guvenli(repo, kayit)
    temiz = (rel or "").replace("\\", "/").lstrip("/")
    if temiz.startswith("klasor/"):
        temiz = temiz[len("klasor/") :]
    if not temiz or ":" in temiz or "\x00" in temiz:
        raise ValueError("Dosya adı geçersiz.")
    parts = [p for p in temiz.split("/") if p not in ("", ".")]
    if not parts or any(p == ".." or p.startswith(".") for p in parts):
        raise ValueError("Dosya adı geçersiz.")
    norm = "/".join(parts)
    target = (kok / norm).resolve()
    if not _icinde(target, kok):
        raise ValueError("Klasör dışı.")
    if target == kok:
        raise ValueError("Klasörün kendisi dosya değildir.")
    return target, norm


def klasor_liste(repo: Path) -> dict:
    kayit = klasor_oku()
    if not kayit:
        return {"ok": True, "klasor": "", "dosyalar": []}
    kok = klasor_guvenli(repo, kayit)
    atla = {"__pycache__", "node_modules", ".git", ".pytest_cache"}
    dosyalar: list[dict] = []
    for path in kok.rglob("*"):
        if len(dosyalar) >= 80:
            break
        if any(parca in atla or parca.startswith(".") for parca in path.relative_to(kok).parts):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        dosyalar.append(
            {
                "name": path.name,
                "rel": "klasor/" + path.relative_to(kok).as_posix(),
            }
        )
    dosyalar.sort(key=lambda row: row["rel"].lower())
    return {"ok": True, "klasor": str(kok), "dosyalar": dosyalar}


def klasor_oku_dosya(repo: Path, rel: str) -> dict:
    target, norm = _klasor_hedef(repo, rel)
    if not target.is_file() or target.is_symlink():
        raise ValueError("Dosya yok.")
    if target.suffix.lower() not in _YAZI_UZANTI and target.suffix.lower() not in _ONIZLEME_MIME:
        raise ValueError("Bu dosya okunmaz.")
    if target.stat().st_size > _YAZI_BAYT:
        raise ValueError("Dosya çok büyük.")
    text = target.read_text(encoding="utf-8")
    return {"ok": True, "rel": "klasor/" + norm, "text": text}


def klasor_yaz(repo: Path, rel: str, text: str) -> dict:
    target, norm = _klasor_hedef(repo, rel)
    if target.exists() and (target.is_dir() or target.is_symlink()):
        raise ValueError("Bu yere yazılmaz.")
    if target.suffix.lower() not in _YAZI_UZANTI:
        raise ValueError("Bu uzantı yazılmaz.")
    body = text if text is not None else ""
    raw = body.encode("utf-8")
    if len(raw) > _YAZI_BAYT:
        raise ValueError("Metin çok büyük.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return {"ok": True, "rel": "klasor/" + norm, "bytes": len(raw)}


def klasor_onizleme(repo: Path, rel: str) -> tuple[Path, str]:
    target, _norm = _klasor_hedef(repo, rel)
    if not target.is_file() or target.is_symlink():
        raise ValueError("Önizlenecek dosya yok.")
    if target.stat().st_size > _ONIZLEME_BAYT:
        raise ValueError("Dosya önizleme için büyük.")
    mime = _ONIZLEME_MIME.get(target.suffix.lower())
    if not mime:
        raise ValueError("Bu dosya önizlenmez.")
    return target, mime


def onizleme_dosyasi(root: Path, rel: str) -> tuple[Path, str]:
    norm, target = resolve_proje_path(root, rel)
    if not target.is_file() or target.is_symlink():
        raise ValueError("Önizlenecek dosya yok.")
    if target.stat().st_size > _ONIZLEME_BAYT:
        raise ValueError("Dosya önizleme için büyük.")
    mime = _ONIZLEME_MIME.get(target.suffix.lower())
    if not mime:
        raise ValueError("Bu dosya önizlenmez.")
    return target, mime
