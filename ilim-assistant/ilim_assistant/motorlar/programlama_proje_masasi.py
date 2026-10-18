# Created by Ümit & Gökçenur
"""Programlama çalışma sayfası — projects/ altını gör, yaz, sil, emri uygula.

Yol projects/ dışına çıkamaz. Bak kapısı bir cümle ister; modelin sözü dosyaya yazılmaz.
Kilitli klasörde sayma, metin dosyası, ara başlık, http bağlantı, başlık rengi, resim ve ad değiştirme de aynı kapıdadır. Silme yok.
Sayfa adı verilirse o sayfaya yazar. Aynı parça ikinci kez eklenmez. Var olan kopyalar teke iner. Zincir yarım kalırsa önceki yazı geri alınır.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
from pathlib import Path

PROJE_MASA_VERSION = "programlama-proje-masa-v7-2026-10-17"

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
    ozel = (os.environ.get("RUZGAR_CALISMA_PIN") or "").strip()
    if ozel:
        return Path(ozel)
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
    _defter_isle(target)
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


class _KlasorYok(Exception):
    """Kilit yok. Sayfa tarifleri projects/ ajanına düşsün."""


_KALIP: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("kilit", re.compile(r"^(?:çalışma klasörü|calisma klasoru)\s*:\s*(?P<yol>.+)$", re.I)),
    ("birak", re.compile(r"^(?:klasörü bırak|klasoru birak)$", re.I)),
    ("goster_klasor", re.compile(r"^(?:klasörü göster|klasoru goster|çalışma klasörü|calisma klasoru)$", re.I)),
    ("say", re.compile(r"^(?:klasördekileri|klasordekileri)\s+say$", re.I)),
    ("dosya_not", re.compile(r"^(?:not defteri|not defter)\s+yap$", re.I)),
    ("dosya_yap", re.compile(r"^(?P<ad>\S+)\s+dosyas[ıi]\s+yap$", re.I)),
    ("ad_degistir", re.compile(
        r"^(?P<eski>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]n[ıi]n\s+ad[ıi]n[ıi]\s+"
        r"(?P<yeni>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+yap$",
        re.I,
    )),
    ("baslik_renk_sayfa", re.compile(
        r"^(?P<sayfa_ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]n[ıi]n\s+"
        r"ba[sş]l[ıi]k\s+rengini\s+(?P<renk>siyah|mavi|kırmızı|kirmizi|yeşil|yesil)\s+yap$",
        re.I,
    )),
    ("ara_baslik_sayfa", re.compile(
        r"^(?P<sayfa_ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]na\s+"
        r"ara\s+ba[sş]l[ıi]k(?:\s+ekle)?\s*[:\-]?\s*(?P<metin>(?:(?!\s+sonra\s)[^,\n])+)$",
        re.I,
    )),
    ("baglanti_sayfa", re.compile(
        r"^(?P<sayfa_ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]na\s+"
        r"ba[gğ]lant[ıi](?:\s+ekle)?\s*[:\-]\s*(?P<soz>.+?)\s*\|\s*(?P<adres>https?://\S+)$",
        re.I,
    )),
    ("resim_sayfa", re.compile(
        r"^(?P<sayfa_ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]na\s+"
        r"resim\s+koy\s*[:\-]\s*(?P<ad>\S+)$",
        re.I,
    )),
    ("teke", re.compile(
        r"^(?:(?P<sayfa_ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]ndaki\s+)?"
        r"ayn[ıi]\s+(?P<ne>ba[gğ]lant[ıi]lar[ıi]|ara\s+ba[sş]l[ıi]klar[ıi]|resimleri)\s+teke\s+indir$",
        re.I,
    )),
    ("baslik_renk", re.compile(
        r"^ba[sş]l[ıi]k\s+rengini\s+(?P<renk>siyah|mavi|kırmızı|kirmizi|yeşil|yesil)\s+yap$",
        re.I,
    )),
    ("ara_baslik", re.compile(
        r"^ara\s+ba[sş]l[ıi]k(?:\s+ekle)?\s*[:\-]?\s*(?P<metin>(?:(?!\s+sonra\s)[^,\n])+)$",
        re.I,
    )),
    ("baglanti", re.compile(
        r"^ba[gğ]lant[ıi](?:\s+ekle)?\s*[:\-]\s*(?P<soz>.+?)\s*\|\s*(?P<adres>https?://\S+)$",
        re.I,
    )),
    ("resim", re.compile(r"^resim\s+koy\s*[:\-]\s*(?P<ad>\S+)$", re.I)),
    ("yaz_eski", re.compile(r"^(?:dosyaya yaz|dosyaya ekle)\s*:\s*(?P<ad>.+?)\s*\|\s*(?P<metin>[\s\S]+)$", re.I)),
    ("oku_eski", re.compile(r"^(?:dosyayı oku|dosyayi oku)\s*:\s*(?P<ad>.+)$", re.I)),
    ("yaz_duz", re.compile(r"^(?P<ad>\S+)\s+dosyas[ıi]na\s+(?P<metin>.+?)\s+yaz$", re.I)),
    ("oku_duz", re.compile(r"^(?P<ad>\S+)\s+dosyas[ıi]n[ıi]\s+oku$", re.I)),
    ("sayfa_goster_ad", re.compile(r"^(?P<ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]n[ıi]\s+g[öo]ster$", re.I)),
    ("sayfa_ad", re.compile(r"^(?P<ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]\s+yap$", re.I)),
    ("sayfa", re.compile(r"^(?:sayfa yap|sayfa aç|sayfa ac)$", re.I)),
    ("sayfa_goster", re.compile(r"^(?:sayfayı göster|sayfayi goster)$", re.I)),
    ("bak_sayfa", re.compile(
        r"^(?P<ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]na\s+bak\s+ve\s+s[öo]yle$",
        re.I,
    )),
    ("bak_dosya", re.compile(r"^(?P<dosya>\S+)\s+dosyas[ıi]na\s+bak\s+ve\s+s[öo]yle$", re.I)),
    ("uygula", re.compile(r"^uygula$", re.I)),
    ("py_fonksiyon", re.compile(
        r"^(?P<ad>\S+\.py)\s+i[çc]inde\s+(?P<fonk>[A-Za-z_][A-Za-z0-9_]*)\s+ne\s+yap[ıi]yor$",
        re.I,
    )),
    ("py_donus", re.compile(
        r"^(?P<ad>\S+\.py)\s+i[çc]inde\s+(?P<fonk>[A-Za-z_][A-Za-z0-9_]*)\s+ne\s+d[öo]nd[üu]r[üu]yor$",
        re.I,
    )),
    ("py_cagri", re.compile(
        r"^(?P<ad>\S+\.py)\s+i[çc]inde\s+(?P<fonk>[A-Za-z_][A-Za-z0-9_]*)\s+kimi\s+[çc]a[gğ][ıi]r[ıi]yor$",
        re.I,
    )),
    ("py_sinif", re.compile(
        r"^(?P<ad>\S+\.py)\s+i[çc]inde\s+(?P<sinif>[A-Za-z_][A-Za-z0-9_]*)\s+s[ıi]n[ıi]f[ıi]\s+ne\s+yap[ıi]yor$",
        re.I,
    )),
    ("py_yer", re.compile(
        r"^(?P<ad>\S+\.py)\s+i[çc]inde\s+(?P<fonk>[A-Za-z_][A-Za-z0-9_]*)\s+nerede$",
        re.I,
    )),
    ("py_yazar", re.compile(
        r"^(?P<ad>\S+\.py)\s+i[çc]inde\s+(?P<fonk>[A-Za-z_][A-Za-z0-9_]*)\s+neye\s+yaz[ıi]yor$",
        re.I,
    )),
    ("py_bakar", re.compile(
        r"^(?P<ad>\S+\.py)\s+i[çc]inde\s+(?P<fonk>[A-Za-z_][A-Za-z0-9_]*)\s+neye\s+bak[ıi]yor$",
        re.I,
    )),
    ("py_ice", re.compile(
        r"^(?P<ad>\S+\.py)\s+neyi\s+i[çc]e\s+al[ıi]yor$",
        re.I,
    )),
    ("py_soyle", re.compile(
        r"^(?P<ad>\S+\.py)\s+dosyas[ıi]n[ıi]n\s+ne\s+yapt[ıi][gğ][ıi]n[ıi]\s+s[öo]yle$",
        re.I,
    )),
    ("py_soyle", re.compile(r"^(?P<ad>\S+\.py)\s+ne\s+yap[ıi]yor$", re.I)),
    ("py_calistir", re.compile(
        r"^(?P<ad>\S+\.py)(?:\s+dosyas[ıi]n[ıi])?\s+[çc]al[ıi][sş]t[ıi]r$",
        re.I,
    )),
    ("baslik", re.compile(r"^(?:başlığı|basligi|başlık|baslik)\s+(?P<metin>.+?)\s+yap$", re.I)),
    ("paragraf", re.compile(
        r"^paragraf(?:\s+ekle)?\s*[:\-]?\s*(?P<metin>(?:(?!\s+sonra\s)[^,\n])+)$",
        re.I,
    )),
    ("buton", re.compile(
        r"^buton(?:\s+ekle)?\s*[:\-]?\s*(?P<metin>(?:(?!\s+sonra\s)[^,\n])+)$",
        re.I,
    )),
)
_AYIR = re.compile(
    r"\s*,\s*(?=(?:başlığı|basligi|başlık|baslik|ara\s+ba[sş]l|ba[gğ]lant|resim\s+koy|paragraf|buton|sayfayı|sayfayi|sayfa\b|\S+\s+sayfas|\S+\s+dosyas|klasördekileri|klasordekileri|not\s+defter|ayn[ıi]\s+))"
    r"|\s+sonra\s+",
    re.I,
)
_TARIF = {"baslik", "paragraf", "buton", "sayfa", "sayfa_ad", "sayfa_goster", "sayfa_goster_ad", "yerine"}
_EL = {"say", "dosya_yap", "ara_baslik", "baglanti", "baslik_renk", "resim", "ad_degistir", "teke"}
_USTA_IZ = re.compile(
    r"sayfas[ıi]na|sayfas[ıi]nda|butonu\s+(?:koy|ekle)|başlığına|basligina|baştan\s+tasarla|bastan\s+tasarla|yerine|bak\s+ve\s+s[öo]yle|\buygula\b"
    r"|klasördekileri|klasordekileri|dosyas[ıi]\s+yap|not\s+defter|ara\s+ba[sş]l|ba[gğ]lant|rengini|resim\s+koy|ad[ıi]n[ıi]|teke\s+indir",
    re.I,
)
_RENK_HEX = {"siyah": "#111111", "mavi": "#1d4e89", "kirmizi": "#9b2c2c", "yesil": "#1f7a4d"}
_RESIM_UZANTI = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
_ADRES = re.compile(r"^https?://[A-Za-z0-9._~:/?#\[\]@!$&()*+,;=%-]{1,300}$")
_ONERI = (
    ("baslik_renk", re.compile(
        r"^ba[sş]l[ıi]k\s+rengini\s+(?P<renk>siyah|mavi|kırmızı|kirmizi|yeşil|yesil)\s+yap$",
        re.I,
    )),
    ("baslik", re.compile(r"^(?:başlığı|basligi|başlık|baslik)\s+(?P<metin>.+?)\s+yap$", re.I)),
    ("paragraf", re.compile(r"^paragraf(?:\s+ekle)?\s*[:\-]\s*(?P<metin>.+)$", re.I)),
    ("buton", re.compile(r"^buton(?:\s+ekle)?\s*[:\-]\s*(?P<metin>.+)$", re.I)),
    ("sayfa_goster", re.compile(r"^(?:sayfayı göster|sayfayi goster)$", re.I)),
    ("yerine", re.compile(r"^(?P<eski>.+?)\s+yerine\s+(?P<yeni>.+?)\s+yaz$", re.I)),
    ("ara_baslik", re.compile(r"^ara\s+ba[sş]l[ıi]k(?:\s+ekle)?\s*[:\-]\s*(?P<metin>.+)$", re.I)),
)
_BEKLEYEN: dict[str, dict] = {}
_DEFTER: list[tuple[str, bytes | None]] | None = None
_SAYFA_KIND = {"baslik_renk_sayfa", "ara_baslik_sayfa", "baglanti_sayfa", "resim_sayfa"}


def _defter_ac() -> None:
    global _DEFTER
    _DEFTER = []


def _defter_kapat() -> None:
    global _DEFTER
    _DEFTER = None


def _defter_isle(path: Path) -> None:
    if _DEFTER is None:
        return
    key = str(path)
    if any(eski == key for eski, _blob in _DEFTER):
        return
    if path.is_file() and not path.is_symlink():
        _DEFTER.append((key, path.read_bytes()))
    else:
        _DEFTER.append((key, None))


def _defter_geri() -> bool:
    global _DEFTER
    kayit = list(_DEFTER or [])
    _DEFTER = None
    dokundu = False
    for key, blob in kayit:
        if blob is None:
            continue
        path = Path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
        dokundu = True
    for key, blob in kayit:
        if blob is not None:
            continue
        path = Path(key)
        if path.is_file() and not path.is_symlink():
            path.unlink()
            dokundu = True
    return dokundu


def _bekleyen_dosya() -> Path:
    return _pin_dosyasi().with_name("calisma_bekleyen.json")


def _bekleyen_oku() -> dict:
    pin = _bekleyen_dosya()
    if not pin.is_file():
        return {}
    try:
        data = json.loads(pin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _bekleyen_yaz(yol: str, kayit: dict | None) -> None:
    data = _bekleyen_oku()
    if kayit is None:
        data.pop(yol, None)
    else:
        data[yol] = kayit
    pin = _bekleyen_dosya()
    pin.parent.mkdir(parents=True, exist_ok=True)
    if data:
        pin.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    elif pin.is_file():
        pin.unlink()


def _bekleyen_al(yol: str) -> dict | None:
    kayit = _BEKLEYEN.get(yol)
    if isinstance(kayit, dict):
        return kayit
    disk = _bekleyen_oku().get(yol)
    if isinstance(disk, dict) and isinstance(disk.get("adim"), dict):
        _BEKLEYEN[yol] = disk
        return disk
    return None


def _bekleyen_koy(yol: str, kayit: dict | None) -> None:
    if kayit is None:
        _BEKLEYEN.pop(yol, None)
    else:
        _BEKLEYEN[yol] = kayit
    _bekleyen_yaz(yol, kayit)
_BAK_ISTEK = (
    "Sana sayfanın görünen yazısı verildi.\n"
    "Yalnız bir tarif cümlesi yaz. Başka söz yazma. Nokta koyma.\n"
    "Kalıplar:\n"
    "başlığı sayfadaki söz yap\n"
    "paragraf ekle: sayfadaki söz\n"
    "buton ekle: sayfadaki söz\n"
    "sayfadaki söz yerine yeni söz yaz\n"
    "ara başlık ekle: sayfadaki söz\n"
    "başlık rengini mavi yap\n"
    "sayfayı göster\n"
    "Yazı:\n"
)
_ORNEK_SOZ = re.compile(
    r"^(?:\.{2,}|…+|sayfadaki söz|sayfadaki soz|yeni söz|yeni soz|buradaki söz|buradaki soz"
    r"|gördüğün söz|gordugun soz|gördüğün değer|gordugun deger|gördüğün başlık|gordugun baslik"
    r"|gördüğün metin|gordugun metin)$",
    re.I,
)
_MASA_AD = {"belge": "belge", "tablo": "tablo", "cizim": "cizim", "çizim": "cizim", "sunum": "sunum"}
_MASA_ISTEK = {
    "belge": (
        "Yalnız bir cümle yaz. Nokta koyma.\n"
        "belgeye gördüğün söz yaz\n"
        "veya belgeye gördüğün söz ekle\n"
        "veya belgede gördüğün söz yerine gördüğün söz yaz\n"
        "Yazı:\n"
    ),
    "tablo": (
        "Yalnız bir cümle yaz. Nokta koyma.\n"
        "tabloda A1 e gördüğün değer yaz\n"
        "veya A sütununu topla\n"
        "veya A1 hücresini sil\n"
        "Yazı:\n"
    ),
    "cizim": (
        "Yalnız şunlardan birini yaz:\n"
        "çizime kutu çiz\n"
        "çizime çizgi çiz\n"
        "çizime daire çiz\n"
        "veya çizime mavi kutu çiz\n"
        "Renk: siyah, mavi, kırmızı, yeşil.\n"
        "Yazı:\n"
    ),
    "sunum": (
        "Yalnız bir cümle yaz. Nokta koyma.\n"
        "sunuma gördüğün başlık slaytı ekle: gördüğün metin\n"
        "veya slaytın başlığını gördüğün başlık yap\n"
        "Yazı:\n"
    ),
}
_USTA_YAZI_YASAK = re.compile(r"\b(dosya|klasör|klasor|sayfa|başl|basl)\b", re.I)
_USTA_RED = (
    "Bunu yapmadım. Dosya değişmedi. "
    "Şöyle söyle: deneme sayfasına başlığı selam yap, hoş geldin yaz, tıkla butonu koy, sayfayı göster."
)


class _UstaRed(Exception):
    """Cümle işe benziyor ama her parça tarife inmiyor. Dosya yazılmaz."""


def _paket(
    *,
    handled: bool = True,
    reply: str = "",
    gorunum: str = "",
    rel: str = "",
    text: str | None = None,
    onizleme: bool = False,
    klasor: str = "",
    sayfa: str = "",
) -> dict:
    out = {
        "ok": True,
        "handled": handled,
        "reply": reply,
        "gorunum": gorunum,
        "rel": rel,
        "onizleme": onizleme,
        "klasor": klasor,
    }
    if text is not None:
        out["text"] = text
    if sayfa:
        out["sayfa"] = sayfa
    return out


def _adim(text: str) -> dict | None:
    raw = (text or "").strip()
    if not raw or len(raw) > 600:
        return None
    sade = re.sub(r"\s+", " ", raw).strip()
    sade = re.sub(r"^[Ll]ütfen\s+", "", sade)
    sade = re.sub(
        r"\s+(?:lütfen|lutfen|olur mu|yapar mısın|yapar misin)\s*$",
        "",
        sade,
        flags=re.I,
    ).strip()
    for kind, cre in _KALIP:
        bulunan = cre.match(sade)
        if not bulunan:
            continue
        if kind in {"yaz_eski", "yaz_duz"}:
            cozulen = "yaz"
        elif kind in {"oku_eski", "oku_duz"}:
            cozulen = "oku"
        elif kind in {"bak_sayfa", "bak_dosya"}:
            cozulen = "bak"
        elif kind == "dosya_not":
            cozulen = "dosya_yap"
        elif kind in _SAYFA_KIND:
            cozulen = kind[: -len("_sayfa")]
        else:
            cozulen = kind
        adim = {"kind": cozulen, "ham": sade}
        if kind == "dosya_not":
            adim["ad"] = "notlar.txt"
        for anahtar, deger in bulunan.groupdict().items():
            if deger is not None:
                adim[anahtar] = deger.strip()
        if cozulen == "yaz" and "metin" in adim:
            adim["metin"] = bulunan.group("metin")
        return adim
    return None


_PY_OKU = {
    "py_soyle",
    "py_calistir",
    "py_fonksiyon",
    "py_donus",
    "py_cagri",
    "py_yer",
    "py_yazar",
    "py_bakar",
    "py_sinif",
    "py_ice",
}


def py_kilit_cumlesi(message: str) -> bool:
    """Python oku/söyle ve çalıştırma reddi. Ajan kapısından önce gelir."""
    adim = _adim(message or "")
    return bool(adim and adim.get("kind") in _PY_OKU)


def _dosya_adi(ad: str) -> str:
    temiz = (ad or "").strip().strip('"').strip("'")
    if not temiz or "/" in temiz or "\\" in temiz or ".." in temiz or ":" in temiz:
        raise ValueError("Dosya adı geçersiz.")
    if temiz.startswith("."):
        raise ValueError("Dosya adı geçersiz.")
    if "." not in temiz:
        temiz += ".txt"
    if Path(temiz).suffix.lower() not in _YAZI_UZANTI:
        raise ValueError("Bu uzantı yazılmaz.")
    return temiz


def _sayfa_dosyasi(ad: str) -> str:
    tab = str.maketrans(
        {
            "İ": "i",
            "I": "i",
            "ı": "i",
            "Ğ": "g",
            "ğ": "g",
            "Ü": "u",
            "ü": "u",
            "Ş": "s",
            "ş": "s",
            "Ö": "o",
            "ö": "o",
            "Ç": "c",
            "ç": "c",
        }
    )
    slug = re.sub(r"[^a-z0-9._-]", "", (ad or "").translate(tab).lower())
    if not slug or slug in {".", ".."} or slug.startswith("."):
        raise ValueError("Sayfa adı geçersiz.")
    if not slug.endswith((".html", ".htm")):
        slug += ".html"
    return slug


def _sayfa_html(baslik: str) -> str:
    safe = _html_kacis(baslik)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="tr">\n'
        f'<head><meta charset="utf-8"><title>{safe}</title></head>\n'
        "<body>\n"
        f"<h1>{safe}</h1>\n"
        "</body>\n"
        "</html>\n"
    )


def _kilit_yolu(repo: Path) -> str:
    kayit = klasor_oku()
    if not kayit:
        raise _KlasorYok()
    return str(klasor_guvenli(repo, kayit))


def _yaz_geri(repo: Path, ad: str, metin: str) -> dict:
    _kilit_yolu(repo)
    rel_ad = _dosya_adi(ad)
    klasor_yaz(repo, rel_ad, metin)
    okunan = klasor_oku_dosya(repo, rel_ad)
    if okunan["text"] != metin:
        raise ValueError("Yazılmadı. " + okunan["rel"])
    html = rel_ad.lower().endswith((".html", ".htm"))
    gorunen = okunan["text"] if len(okunan["text"]) <= 500 else okunan["text"][:500] + "…"
    return _paket(
        reply=f"Yazıldı: {okunan['rel']}\n{gorunen}",
        gorunum="proje" if html else "kod",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=html,
        sayfa=rel_ad if html else "",
    )


def _oku_paket(repo: Path, ad: str) -> dict:
    _kilit_yolu(repo)
    rel_ad = _dosya_adi(ad)
    not_ = ""
    try:
        okunan = klasor_oku_dosya(repo, rel_ad)
    except ValueError as exc:
        if str(exc) != "Dosya yok." or not rel_ad.lower().endswith(".txt"):
            raise
        sayfa = _sayfa_dosyasi(Path(rel_ad).stem)
        try:
            okunan = klasor_oku_dosya(repo, sayfa)
        except ValueError:
            raise exc from None
        rel_ad = sayfa
        not_ = "Metin dosyası yoktu, sayfa açıldı.\n"
    html = rel_ad.lower().endswith((".html", ".htm"))
    govde = okunan["text"] if len(okunan["text"]) <= 500 else okunan["text"][:500] + "…"
    return _paket(
        reply=f"{okunan['rel']} okundu.\n{not_}{govde or '(boş)'}",
        gorunum="proje" if html else "kod",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=html,
        sayfa=rel_ad if html else "",
    )


def _py_adi(ad: str) -> str:
    temiz = _dosya_adi(ad)
    if not temiz.lower().endswith(".py"):
        raise ValueError("Bu tarif yalnız Python dosyası içindir.")
    return temiz


def _py_ozet(kaynak: str) -> str | None:
    """Dosyayı ağaç olarak okur. Çalıştırmaz."""
    try:
        agac = ast.parse(kaynak)
    except SyntaxError:
        return None
    satirlar: list[str] = []
    belge = ast.get_docstring(agac)
    if belge:
        ilk = belge.strip().splitlines()[0].strip()
        if ilk:
            satirlar.append(ilk[:160])
    ice: list[str] = []
    fonksiyonlar: list[str] = []
    siniflar: list[str] = []
    for dugum in agac.body:
        if isinstance(dugum, ast.Import):
            ice.extend(alias.name.split(".")[0] for alias in dugum.names)
        elif isinstance(dugum, ast.ImportFrom) and dugum.module:
            ice.append(dugum.module.split(".")[0])
        elif isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fonksiyonlar.append(dugum.name)
        elif isinstance(dugum, ast.ClassDef):
            siniflar.append(dugum.name)
    if ice:
        satirlar.append("İçe alır: " + ", ".join(ice[:6]) + ".")
    if fonksiyonlar:
        satirlar.append("Fonksiyonlar: " + ", ".join(fonksiyonlar[:8]) + ".")
    if siniflar:
        satirlar.append("Sınıflar: " + ", ".join(siniflar[:6]) + ".")
    if not satirlar:
        return ""
    return " ".join(satirlar)


def _py_soyle(repo: Path, ad: str) -> dict:
    rel_ad = _py_adi(ad)
    okunan = klasor_oku_dosya(repo, rel_ad)
    ozet = _py_ozet(okunan["text"])
    if ozet is None:
        govde = "Python olarak açılmadı."
    elif not ozet:
        govde = "İçinde fonksiyon yok."
    else:
        govde = ozet
    return _paket(
        reply=rel_ad + " okundu. Çalıştırmadım.\n" + govde + "\nDosya aynı.",
        gorunum="kod",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=False,
    )


def _py_imza(fonk: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    adlar = [parca.arg for parca in list(fonk.args.posonlyargs) + list(fonk.args.args)]
    return fonk.name + "(" + ", ".join(adlar) + ")"


def _py_fonksiyon(repo: Path, ad: str, fonk_ad: str) -> dict:
    rel_ad = _py_adi(ad)
    okunan = klasor_oku_dosya(repo, rel_ad)
    try:
        agac = ast.parse(okunan["text"])
    except SyntaxError:
        govde = "Python olarak açılmadı."
    else:
        bulunan = next(
            (
                dugum
                for dugum in agac.body
                if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef))
                and dugum.name == fonk_ad
            ),
            None,
        )
        if bulunan is None:
            govde = fonk_ad + " bu dosyada yok."
        else:
            belge = ast.get_docstring(bulunan)
            ilk = belge.strip().splitlines()[0].strip()[:160] if belge else ""
            govde = _py_imza(bulunan) + "."
            if ilk:
                govde += " " + ilk
    return _paket(
        reply=rel_ad + " içinde " + fonk_ad + " okundu. Çalıştırmadım.\n" + govde + "\nDosya aynı.",
        gorunum="kod",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=False,
    )


def _py_donus_metinleri(dugumler: list[ast.stmt]) -> list[str]:
    bulunan: list[str] = []
    for dugum in dugumler:
        if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(dugum, ast.Return) and dugum.value is not None:
            bulunan.append(ast.unparse(dugum.value)[:120])
        bulunan.extend(_py_donus_metinleri(list(ast.iter_child_nodes(dugum))))
    return bulunan


def _py_donus(repo: Path, ad: str, fonk_ad: str) -> dict:
    rel_ad = _py_adi(ad)
    okunan = klasor_oku_dosya(repo, rel_ad)
    try:
        agac = ast.parse(okunan["text"])
    except SyntaxError:
        govde = "Python olarak açılmadı."
    else:
        bulunan = next(
            (
                dugum
                for dugum in agac.body
                if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef))
                and dugum.name == fonk_ad
            ),
            None,
        )
        if bulunan is None:
            govde = fonk_ad + " bu dosyada yok."
        else:
            metinler = _py_donus_metinleri(bulunan.body)
            if not metinler:
                govde = "Bir değer döndürmez."
            else:
                govde = " veya ".join(metinler[:4]) + " döndürür."
    return _paket(
        reply=rel_ad + " içinde " + fonk_ad + " okundu. Çalıştırmadım.\n" + govde + "\nDosya aynı.",
        gorunum="kod",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=False,
    )


def _py_cagri_adlari(dugumler: list[ast.AST]) -> list[str]:
    bulunan: list[str] = []
    for dugum in dugumler:
        if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(dugum, ast.Call):
            func = dugum.func
            ad = ""
            if isinstance(func, ast.Name):
                ad = func.id
            elif isinstance(func, ast.Attribute):
                ad = func.attr
            if ad and ad not in bulunan:
                bulunan.append(ad)
        bulunan.extend(_py_cagri_adlari(list(ast.iter_child_nodes(dugum))))
    return bulunan


def _py_cagri(repo: Path, ad: str, fonk_ad: str) -> dict:
    rel_ad = _py_adi(ad)
    okunan = klasor_oku_dosya(repo, rel_ad)
    try:
        agac = ast.parse(okunan["text"])
    except SyntaxError:
        govde = "Python olarak açılmadı."
    else:
        bulunan = next(
            (
                dugum
                for dugum in agac.body
                if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef))
                and dugum.name == fonk_ad
            ),
            None,
        )
        if bulunan is None:
            govde = fonk_ad + " bu dosyada yok."
        else:
            adlar = _py_cagri_adlari(bulunan.body)
            if not adlar:
                govde = "Kimseyi çağırmaz."
            else:
                govde = ", ".join(adlar[:6]) + " çağırır."
    return _paket(
        reply=rel_ad + " içinde " + fonk_ad + " okundu. Çalıştırmadım.\n" + govde + "\nDosya aynı.",
        gorunum="kod",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=False,
    )


def _py_ust_fonk(agac: ast.AST, fonk_ad: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    return next(
        (
            dugum
            for dugum in agac.body
            if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef)) and dugum.name == fonk_ad
        ),
        None,
    )


def _py_fonk_cevap(repo: Path, ad: str, fonk_ad: str, doldur) -> dict:
    rel_ad = _py_adi(ad)
    okunan = klasor_oku_dosya(repo, rel_ad)
    try:
        agac = ast.parse(okunan["text"])
    except SyntaxError:
        govde = "Python olarak açılmadı."
    else:
        bulunan = _py_ust_fonk(agac, fonk_ad)
        if bulunan is None:
            govde = fonk_ad + " bu dosyada yok."
        else:
            govde = doldur(bulunan)
    return _paket(
        reply=rel_ad + " içinde " + fonk_ad + " okundu. Çalıştırmadım.\n" + govde + "\nDosya aynı.",
        gorunum="kod",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=False,
    )


def _py_yer(repo: Path, ad: str, fonk_ad: str) -> dict:
    def doldur(fonk: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        bas = int(fonk.lineno or 0)
        bit = int(fonk.end_lineno or bas)
        if bas and bit and bit != bas:
            return str(bas) + ". satırdan " + str(bit) + ". satıra."
        if bas:
            return str(bas) + ". satır."
        return "Satır yok."

    return _py_fonk_cevap(repo, ad, fonk_ad, doldur)


def _py_yazilan_adlar(hedef: ast.AST) -> list[str]:
    if isinstance(hedef, ast.Name):
        return [hedef.id]
    if isinstance(hedef, (ast.Tuple, ast.List)):
        adlar: list[str] = []
        for parca in hedef.elts:
            adlar.extend(_py_yazilan_adlar(parca))
        return adlar
    return []


def _py_yazar_adlari(dugumler: list[ast.AST]) -> list[str]:
    bulunan: list[str] = []
    for dugum in dugumler:
        if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        hedefler: list[ast.AST] = []
        if isinstance(dugum, ast.Assign):
            hedefler = list(dugum.targets)
        elif isinstance(dugum, ast.AnnAssign) and dugum.target is not None:
            hedefler = [dugum.target]
        elif isinstance(dugum, ast.AugAssign):
            hedefler = [dugum.target]
        elif isinstance(dugum, ast.NamedExpr):
            hedefler = [dugum.target]
        for hedef in hedefler:
            for ad in _py_yazilan_adlar(hedef):
                if ad not in bulunan:
                    bulunan.append(ad)
        bulunan.extend(_py_yazar_adlari(list(ast.iter_child_nodes(dugum))))
    return bulunan


def _py_yazar(repo: Path, ad: str, fonk_ad: str) -> dict:
    def doldur(fonk: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        adlar = _py_yazar_adlari(fonk.body)
        if not adlar:
            return "Bir şeye yazmaz."
        return ", ".join(adlar[:6]) + " yazar."

    return _py_fonk_cevap(repo, ad, fonk_ad, doldur)


def _py_kosullar(dugumler: list[ast.AST]) -> list[str]:
    bulunan: list[str] = []
    for dugum in dugumler:
        if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(dugum, (ast.If, ast.While)) and dugum.test is not None:
            metin = ast.unparse(dugum.test)[:120]
            if metin and metin not in bulunan:
                bulunan.append(metin)
        bulunan.extend(_py_kosullar(list(ast.iter_child_nodes(dugum))))
    return bulunan


def _py_bakar(repo: Path, ad: str, fonk_ad: str) -> dict:
    def doldur(fonk: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        metinler = _py_kosullar(fonk.body)
        if not metinler:
            return "Bir koşula bakmaz."
        return " veya ".join(metinler[:4]) + "."

    return _py_fonk_cevap(repo, ad, fonk_ad, doldur)


def _py_sinif(repo: Path, ad: str, sinif_ad: str) -> dict:
    rel_ad = _py_adi(ad)
    okunan = klasor_oku_dosya(repo, rel_ad)
    try:
        agac = ast.parse(okunan["text"])
    except SyntaxError:
        govde = "Python olarak açılmadı."
    else:
        sinif = next(
            (dugum for dugum in agac.body if isinstance(dugum, ast.ClassDef) and dugum.name == sinif_ad),
            None,
        )
        if sinif is None:
            govde = sinif_ad + " bu dosyada yok."
        else:
            imzalar = [
                _py_imza(dugum)
                for dugum in sinif.body
                if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            if not imzalar:
                govde = "İçinde fonksiyon yok."
            else:
                govde = ". ".join(imzalar[:8]) + "."
    return _paket(
        reply=rel_ad + " içinde " + sinif_ad + " okundu. Çalıştırmadım.\n" + govde + "\nDosya aynı.",
        gorunum="kod",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=False,
    )


def _py_ice(repo: Path, ad: str) -> dict:
    rel_ad = _py_adi(ad)
    okunan = klasor_oku_dosya(repo, rel_ad)
    try:
        agac = ast.parse(okunan["text"])
    except SyntaxError:
        govde = "Python olarak açılmadı."
    else:
        ice: list[str] = []
        for dugum in agac.body:
            if isinstance(dugum, ast.Import):
                adaylar = [alias.name.split(".")[0] for alias in dugum.names]
            elif isinstance(dugum, ast.ImportFrom) and dugum.module:
                adaylar = [dugum.module.split(".")[0]]
            else:
                adaylar = []
            for parca in adaylar:
                if parca and parca not in ice:
                    ice.append(parca)
        if not ice:
            govde = "Bir şey içe almaz."
        else:
            govde = ", ".join(ice[:6]) + "."
    return _paket(
        reply=rel_ad + " okundu. Çalıştırmadım.\n" + govde + "\nDosya aynı.",
        gorunum="kod",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=False,
    )


def _sayfa_sec(repo: Path, tercih: str) -> str:
    if tercih:
        return tercih
    htmls = []
    for item in klasor_liste(repo)["dosyalar"]:
        rel = str(item["rel"])
        if rel.lower().endswith((".html", ".htm")):
            htmls.append(rel[len("klasor/") :] if rel.startswith("klasor/") else rel)
    if "index.html" in htmls:
        return "index.html"
    if len(htmls) == 1:
        return htmls[0]
    if not htmls:
        raise ValueError("Sayfa yok. Şöyle söyle: deneme sayfası yap")
    raise ValueError("Birden fazla sayfa var. Şöyle söyle: deneme sayfasını göster")


def _sayfa_yaz(repo: Path, dosya: str, html: str, reply: str) -> dict:
    klasor_yaz(repo, dosya, html)
    okunan = klasor_oku_dosya(repo, dosya)
    if okunan["text"] != html:
        raise ValueError("Yazılmadı. " + okunan["rel"])
    return _paket(
        reply=reply,
        gorunum="proje",
        rel=okunan["rel"],
        text=okunan["text"],
        onizleme=True,
        sayfa=dosya,
    )


def _renk_hex(ad: str) -> str:
    sade = (
        (ad or "")
        .lower()
        .replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )
    return _RENK_HEX.get(sade, "")


def _baslik_boya(html: str, hexcode: str) -> str:
    bulunan = re.search(r"<h1\b([^>]*)>", html, re.I)
    if bulunan:
        attrs = re.sub(r"""\sstyle\s*=\s*(?:"[^"]*"|'[^']*')""", "", bulunan.group(1), flags=re.I)
        yeni = f'<h1{attrs} style="color:{hexcode}">'
        return html[: bulunan.start()] + yeni + html[bulunan.end() :]
    baslik = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    metin = re.sub(r"\s+", " ", baslik.group(1)).strip() if baslik else ""
    if not metin:
        raise ValueError("Başlık yok.")
    h1 = f'<h1 style="color:{hexcode}">{metin}</h1>'
    govde = re.search(r"<body\b[^>]*>", html, re.I)
    if govde:
        return html[: govde.end()] + "\n" + h1 + html[govde.end() :]
    if baslik:
        return html[: baslik.end()] + "\n" + h1 + html[baslik.end() :]
    return h1 + "\n" + html


def _hedef_sayfa(repo: Path, adim: dict, sayfa: str) -> str:
    ad = str(adim.get("sayfa_ad") or "").strip()
    if ad:
        return _sayfa_dosyasi(ad)
    return _sayfa_sec(repo, sayfa)


def _bir_kez(repo: Path, dosya: str, parca: str, oldu: str) -> dict:
    html = klasor_oku_dosya(repo, dosya)["text"]
    if parca in html:
        return _paket(
            reply="Zaten var: klasor/" + dosya,
            gorunum="proje",
            rel="klasor/" + dosya,
            text=html,
            onizleme=True,
            sayfa=dosya,
        )
    html = _govdeye_ekle(html, parca)
    if parca not in html:
        raise ValueError("Yazılmadı. " + dosya)
    return _sayfa_yaz(repo, dosya, html, oldu)


def _teke_etiket(ne: str) -> str:
    sade = (ne or "").lower()
    for eski, yeni in (("ı", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"), ("ö", "o"), ("ç", "c")):
        sade = sade.replace(eski, yeni)
    if "baglanti" in sade:
        return "a"
    if "baslik" in sade:
        return "h2"
    if "resim" in sade:
        return "img"
    raise ValueError("Bu parça inmez.")


def _cift_kaldir(html: str, etiket: str) -> tuple[str, int]:
    if etiket == "img":
        cre = re.compile(r"<img\b[^>]*>", re.I)
    elif etiket in {"a", "h2"}:
        cre = re.compile(rf"<{etiket}\b[^>]*>.*?</{etiket}>", re.I | re.S)
    else:
        raise ValueError("Bu parça inmez.")
    gorulen: set[str] = set()
    adet = 0

    def degistir(bulunan: re.Match[str]) -> str:
        nonlocal adet
        parca = bulunan.group(0)
        anahtar = re.sub(r"\s+", " ", parca).strip().lower()
        if anahtar in gorulen:
            adet += 1
            return ""
        gorulen.add(anahtar)
        return parca

    yeni = cre.sub(degistir, html)
    return re.sub(r"\n{3,}", "\n\n", yeni), adet


def _adres_guvenli(adres: str) -> str:
    temiz = (adres or "").strip()
    if not _ADRES.match(temiz) or "\\" in temiz or temiz.lower().count("://") != 1:
        raise ValueError("Bağlantı yalnız http veya https olur.")
    return temiz


def _resim_adi(ad: str) -> str:
    temiz = (ad or "").strip().strip('"').strip("'")
    if not temiz or "/" in temiz or "\\" in temiz or ".." in temiz or ":" in temiz or temiz.startswith("."):
        raise ValueError("Dosya adı geçersiz.")
    if Path(temiz).suffix.lower() not in _RESIM_UZANTI:
        raise ValueError("Bu resim konmaz.")
    return Path(temiz).name


def _calistir(repo: Path, adim: dict, sayfa: str) -> dict:
    kind = adim["kind"]
    if kind == "kilit":
        try:
            data = klasor_kaydet(repo, adim.get("yol") or "")
        except ValueError as exc:
            raise ValueError("Klasör açılmadı. " + str(exc)) from exc
        goster = _calistir(repo, {"kind": "goster_klasor", "ham": "klasörü göster"}, "")
        return _paket(
            reply="Klasör kilitlendi: " + data["klasor"] + "\n" + goster["reply"],
            gorunum=goster.get("gorunum") or "proje",
            rel=goster.get("rel") or "",
            text=goster.get("text"),
            onizleme=bool(goster.get("onizleme")),
            klasor=data["klasor"],
        )
    if kind == "birak":
        klasor_kaydet(repo, "")
        return _paket(reply="Çalışma klasörü bırakıldı. Dosyalar silinmedi.")
    if kind == "goster_klasor":
        liste = klasor_liste(repo)
        if not liste["klasor"]:
            raise ValueError("Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol")
        adlar = [str(item["rel"]).replace("klasor/", "", 1) for item in liste["dosyalar"][:12]]
        html = next((ad for ad in adlar if ad.lower().endswith((".html", ".htm"))), "")
        text = klasor_oku_dosya(repo, html)["text"] if html else None
        govde = "\n".join(adlar) if adlar else "Dosya yok."
        return _paket(
            reply="Klasör açık: " + liste["klasor"] + "\n" + govde,
            gorunum="proje",
            rel=("klasor/" + html) if html else "",
            text=text,
            onizleme=bool(html),
            klasor=liste["klasor"],
            sayfa=html,
        )
    if kind in _TARIF or kind in {"yaz", "oku"}:
        try:
            _kilit_yolu(repo)
        except _KlasorYok:
            if kind in _TARIF:
                raise
            raise ValueError("Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol") from None
    if kind == "yaz":
        metin = adim.get("metin") or ""
        if metin == "":
            raise ValueError("Yazılacak metin yok.")
        return _yaz_geri(repo, adim.get("ad") or "", metin)
    if kind == "oku":
        return _oku_paket(repo, adim.get("ad") or "")
    if kind in _PY_OKU:
        try:
            _kilit_yolu(repo)
        except _KlasorYok:
            raise ValueError(
                "Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol"
            ) from None
        if kind == "py_calistir":
            return _paket(reply="Bunu yapmadım. Kodu çalıştırmadım. Dosya aynı.")
        if kind == "py_fonksiyon":
            return _py_fonksiyon(repo, adim.get("ad") or "", adim.get("fonk") or "")
        if kind == "py_donus":
            return _py_donus(repo, adim.get("ad") or "", adim.get("fonk") or "")
        if kind == "py_cagri":
            return _py_cagri(repo, adim.get("ad") or "", adim.get("fonk") or "")
        if kind == "py_yer":
            return _py_yer(repo, adim.get("ad") or "", adim.get("fonk") or "")
        if kind == "py_yazar":
            return _py_yazar(repo, adim.get("ad") or "", adim.get("fonk") or "")
        if kind == "py_bakar":
            return _py_bakar(repo, adim.get("ad") or "", adim.get("fonk") or "")
        if kind == "py_sinif":
            return _py_sinif(repo, adim.get("ad") or "", adim.get("sinif") or "")
        if kind == "py_ice":
            return _py_ice(repo, adim.get("ad") or "")
        return _py_soyle(repo, adim.get("ad") or "")
    if kind in {"sayfa", "sayfa_ad"}:
        dosya = _sayfa_dosyasi("index" if kind == "sayfa" else adim.get("ad") or "")
        try:
            mevcut = klasor_oku_dosya(repo, dosya)
        except ValueError:
            mevcut = None
        if mevcut:
            return _paket(
                reply="Sayfa duruyor: " + mevcut["rel"],
                gorunum="proje",
                rel=mevcut["rel"],
                text=mevcut["text"],
                onizleme=True,
                sayfa=dosya,
            )
        html = _sayfa_html(Path(dosya).stem)
        return _sayfa_yaz(repo, dosya, html, "Sayfa yazıldı: klasor/" + dosya)
    if kind in {"sayfa_goster", "sayfa_goster_ad"}:
        tercih = _sayfa_dosyasi(adim["ad"]) if kind == "sayfa_goster_ad" else sayfa
        dosya = _sayfa_sec(repo, tercih)
        okunan = klasor_oku_dosya(repo, dosya)
        return _paket(
            reply="Sayfa açık: " + okunan["rel"],
            gorunum="proje",
            rel=okunan["rel"],
            text=okunan["text"],
            onizleme=True,
            sayfa=dosya,
        )
    if kind == "baslik":
        metin = (adim.get("metin") or "").strip().strip("\"'")
        if _renk_hex(metin):
            boya = dict(adim)
            boya["kind"] = "baslik_renk"
            boya["renk"] = metin
            return _calistir(repo, boya, sayfa)
        if not metin or len(metin) > 180:
            raise ValueError("Başlık boş veya çok uzun.")
        dosya = _sayfa_sec(repo, sayfa)
        html = _baslik_yaz(klasor_oku_dosya(repo, dosya)["text"], metin)
        safe = _html_kacis(metin)
        if f"<title>{safe}</title>" not in html:
            raise ValueError("Yazılmadı. " + dosya)
        return _sayfa_yaz(repo, dosya, html, "Başlık yazıldı: klasor/" + dosya + "\n" + metin)
    if kind == "paragraf":
        metin = (adim.get("metin") or "").strip()
        if not metin or len(metin) > 400:
            raise ValueError("Paragraf boş veya çok uzun.")
        dosya = _sayfa_sec(repo, sayfa)
        parca = "<p>" + _html_kacis(metin) + "</p>"
        return _bir_kez(repo, dosya, parca, "Paragraf yazıldı: klasor/" + dosya + "\n" + metin)
    if kind == "buton":
        metin = (adim.get("metin") or "").strip().strip("\"'")
        if not metin or len(metin) > 80:
            raise ValueError("Buton yazısı boş veya çok uzun.")
        dosya = _sayfa_sec(repo, sayfa)
        parca = '<button type="button">' + _html_kacis(metin) + "</button>"
        return _bir_kez(repo, dosya, parca, "Buton yazıldı: klasor/" + dosya + "\n" + metin)
    if kind == "yerine":
        eski = (adim.get("eski") or "").strip().strip("\"'")
        yeni = (adim.get("yeni") or "").strip().strip("\"'")
        if not eski or len(eski) > 180:
            raise ValueError("Eski metin boş veya çok uzun.")
        if not yeni or len(yeni) > 400:
            raise ValueError("Yeni metin boş veya çok uzun.")
        if adim.get("dosya"):
            dosya = _dosya_adi(str(adim["dosya"]))
        elif adim.get("ad"):
            dosya = _sayfa_dosyasi(str(adim["ad"]))
        else:
            if not sayfa:
                htmls = [
                    str(item["rel"]).split("/", 1)[-1]
                    for item in klasor_liste(repo)["dosyalar"]
                    if str(item["rel"]).lower().endswith((".html", ".htm"))
                ]
                if len(htmls) > 1:
                    raise ValueError("Birden fazla sayfa var. Şöyle söyle: deneme sayfasında eski yerine yeni yaz")
            dosya = _sayfa_sec(repo, sayfa)
        ham = klasor_oku_dosya(repo, dosya)["text"]
        if eski not in ham:
            raise ValueError("Metin dosyada yok.")
        html_mi = dosya.lower().endswith((".html", ".htm"))
        yeni_yaz = _html_kacis(yeni) if html_mi else yeni
        guncel = ham.replace(eski, yeni_yaz, 1)
        if yeni_yaz not in guncel or guncel == ham:
            raise ValueError("Yazılmadı. " + dosya)
        reply = "Değişti: klasor/" + dosya + "\n" + eski + " yerine " + yeni
        if html_mi:
            return _sayfa_yaz(repo, dosya, guncel, reply)
        yazilan = _yaz_geri(repo, dosya, guncel)
        yazilan["reply"] = reply
        return yazilan
    if kind in _EL:
        _kilit_yolu(repo)
    if kind == "say":
        liste = klasor_liste(repo)
        adlar = [str(item["rel"]).replace("klasor/", "", 1) for item in liste["dosyalar"][:40]]
        govde = "\n".join(adlar) if adlar else "Dosya yok."
        return _paket(reply="Klasörde " + str(len(liste["dosyalar"])) + " dosya:\n" + govde, klasor=liste["klasor"])
    if kind == "dosya_yap":
        dosya = _dosya_adi(adim.get("ad") or "")
        if not dosya.lower().endswith(".txt"):
            raise ValueError("Yalnız metin dosyası açılır.")
        try:
            mevcut = klasor_oku_dosya(repo, dosya)
        except ValueError:
            mevcut = None
        if mevcut:
            return _paket(
                reply="Dosya duruyor: " + mevcut["rel"],
                gorunum="kod",
                rel=mevcut["rel"],
                text=mevcut["text"],
            )
        return _yaz_geri(repo, dosya, "")
    if kind == "ara_baslik":
        metin = (adim.get("metin") or "").strip().strip("\"'")
        if not metin or len(metin) > 180:
            raise ValueError("Ara başlık boş veya çok uzun.")
        dosya = _hedef_sayfa(repo, adim, sayfa)
        parca = "<h2>" + _html_kacis(metin) + "</h2>"
        return _bir_kez(repo, dosya, parca, "Ara başlık yazıldı: klasor/" + dosya + "\n" + metin)
    if kind == "baglanti":
        soz = (adim.get("soz") or "").strip().strip("\"'")
        if not soz or len(soz) > 180:
            raise ValueError("Bağlantı yazısı boş veya çok uzun.")
        adres = _adres_guvenli(adim.get("adres") or "")
        dosya = _hedef_sayfa(repo, adim, sayfa)
        parca = '<a href="' + _html_kacis(adres) + '">' + _html_kacis(soz) + "</a>"
        return _bir_kez(repo, dosya, parca, "Bağlantı yazıldı: klasor/" + dosya + "\n" + soz)
    if kind == "baslik_renk":
        hexcode = _renk_hex(adim.get("renk") or "")
        if not hexcode:
            raise ValueError("Renk: siyah, mavi, kırmızı, yeşil.")
        dosya = _hedef_sayfa(repo, adim, sayfa)
        html = _baslik_boya(klasor_oku_dosya(repo, dosya)["text"], hexcode)
        if f'style="color:{hexcode}"' not in html:
            raise ValueError("Yazılmadı. " + dosya)
        return _sayfa_yaz(repo, dosya, html, "Başlık rengi yazıldı: klasor/" + dosya + "\n" + hexcode)
    if kind == "resim":
        ad = _resim_adi(adim.get("ad") or "")
        kaynak, _norm = _klasor_hedef(repo, ad)
        if not kaynak.is_file() or kaynak.is_symlink():
            raise ValueError("Dosya yok.")
        dosya = _hedef_sayfa(repo, adim, sayfa)
        parca = '<img src="' + _html_kacis(ad) + '" alt="' + _html_kacis(Path(ad).stem) + '">'
        return _bir_kez(repo, dosya, parca, "Resim kondu: klasor/" + dosya + "\n" + ad)
    if kind == "ad_degistir":
        eski = _sayfa_dosyasi(adim.get("eski") or "")
        yeni = _sayfa_dosyasi(adim.get("yeni") or "")
        if eski == yeni:
            raise ValueError("Ad aynı.")
        kaynak, _eski_norm = _klasor_hedef(repo, eski)
        hedef, _yeni_norm = _klasor_hedef(repo, yeni)
        if not kaynak.is_file() or kaynak.is_symlink():
            raise ValueError("Dosya yok.")
        if hedef.exists():
            raise ValueError("Bu ad duruyor.")
        if kaynak.parent.resolve() != hedef.parent.resolve():
            raise ValueError("Klasör dışı.")
        icerik = kaynak.read_text(encoding="utf-8")
        _defter_isle(kaynak)
        _defter_isle(hedef)
        kaynak.replace(hedef)
        if kaynak.exists() or not hedef.is_file() or hedef.read_text(encoding="utf-8") != icerik:
            raise ValueError("Ad değişmedi.")
        return _paket(
            reply="Ad değişti: klasor/" + yeni,
            gorunum="proje",
            rel="klasor/" + yeni,
            text=icerik,
            onizleme=True,
            sayfa=yeni,
        )
    if kind == "teke":
        etiket = _teke_etiket(str(adim.get("ne") or ""))
        dosya = _hedef_sayfa(repo, adim, sayfa)
        html = klasor_oku_dosya(repo, dosya)["text"]
        yeni_html, adet = _cift_kaldir(html, etiket)
        if adet == 0:
            return _paket(
                reply="Zaten tek: klasor/" + dosya,
                gorunum="proje",
                rel="klasor/" + dosya,
                text=html,
                onizleme=True,
                sayfa=dosya,
            )
        if yeni_html == html:
            raise ValueError("Yazılmadı. " + dosya)
        return _sayfa_yaz(repo, dosya, yeni_html, "Tekrar kalktı: klasor/" + dosya + "\n" + str(adet) + " kopya indi.")
    if kind == "bak":
        return _bak(repo, adim)
    if kind == "uygula":
        return _uygula(repo)
    return _paket(handled=False)


def _soyle(istem: str, metin: str) -> str:
    """Yerel denge, 15 saniye. Boş dönüş öneri yok demektir."""
    import json
    import urllib.request

    parca = (metin or "")[:1200]
    base = (os.environ.get("OLLAMA_API_BASE") or "http://127.0.0.1:11434/v1").rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    model = os.environ.get("OLLAMA_CHAT_MODEL") or "llama3.1:8b"
    body = json.dumps(
        {
            "model": model,
            "prompt": istem + parca,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 60},
        }
    ).encode("utf-8")
    istek = urllib.request.Request(
        base + "/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(istek, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        return str(data.get("response") or "").strip()
    except Exception:
        return ""


def _soyleyen(metin: str) -> str:
    """Klasör bak kapısı. Test bunu değiştirir."""
    return _soyle(_BAK_ISTEK, metin)


def _masa_soyleyen(masa: str, metin: str) -> str:
    """Masa bak kapısı. Test bunu değiştirir."""
    return _soyle(_MASA_ISTEK.get(masa) or "", metin)


def _soz_var(metin: str) -> bool:
    temiz = (metin or "").strip()
    if not temiz or _ORNEK_SOZ.match(temiz):
        return False
    return re.search(r"[0-9A-Za-zÇĞİÖŞÜçğıöşü]", temiz) is not None


def _duz_metin(parca: str) -> str:
    metin = re.sub(r"<[^>]+>", " ", parca or "")
    metin = (
        metin.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
    )
    return re.sub(r"\s+", " ", metin).strip()


def _gorunen_yazi(ham: str) -> str:
    govde = ham or ""
    if "<" not in govde:
        return govde.strip()[:1200]
    satirlar: list[str] = []
    baslik = re.search(r"<title\b[^>]*>(.*?)</title>", govde, re.I | re.S)
    if baslik:
        ic = _duz_metin(baslik.group(1))
        if _soz_var(ic):
            satirlar.append("başlık: " + ic)
    for etiket, ad in (("h1", "başlık"), ("h2", "ara başlık"), ("p", "paragraf"), ("button", "buton")):
        for bulunan in re.finditer(rf"<{etiket}\b[^>]*>(.*?)</{etiket}>", govde, re.I | re.S):
            ic = _duz_metin(bulunan.group(1))
            if _soz_var(ic):
                satirlar.append(ad + ": " + ic)
    if not satirlar:
        duz = _duz_metin(govde)
        if _soz_var(duz):
            satirlar.append(duz)
    return "\n".join(satirlar)[:1200]


def _gordum_satir(ham: str) -> str:
    baslik = re.search(r"<title>(.*?)</title>", ham, re.I | re.S)
    if baslik:
        ic = re.sub(r"\s+", " ", baslik.group(1)).strip()
        if ic:
            return ic[:180]
    for satir in ham.splitlines():
        temiz = satir.strip()
        if temiz:
            return temiz[:180]
    return "(boş)"


def _tarif_satir(sade: str, hedef: str, kaynak: str) -> tuple[str, dict] | None:
    html_mi = hedef.lower().endswith((".html", ".htm"))
    for kind, cre in _ONERI:
        bulunan = cre.match(sade)
        if not bulunan:
            continue
        if kind in {"baslik", "paragraf", "buton", "sayfa_goster"} and not html_mi:
            return None
        if kind == "baslik":
            metin = bulunan.group("metin").strip().strip("\"'")
            if not _soz_var(metin) or len(metin) > 180:
                return None
            cumle = "başlığı " + metin + " yap"
            return cumle, _usta_adim("baslik", cumle, metin=metin)
        if kind == "paragraf":
            metin = bulunan.group("metin").strip()
            if not _soz_var(metin) or len(metin) > 400:
                return None
            cumle = "paragraf ekle: " + metin
            return cumle, _usta_adim("paragraf", cumle, metin=metin)
        if kind == "buton":
            metin = bulunan.group("metin").strip().strip("\"'")
            if not _soz_var(metin) or len(metin) > 80:
                return None
            cumle = "buton ekle: " + metin
            return cumle, _usta_adim("buton", cumle, metin=metin)
        if kind == "sayfa_goster":
            return "sayfayı göster", _usta_adim("sayfa_goster", "sayfayı göster")
        if kind == "ara_baslik":
            if not html_mi:
                return None
            metin = bulunan.group("metin").strip().strip("\"'")
            if not _soz_var(metin) or len(metin) > 180 or metin not in kaynak:
                return None
            cumle = "ara başlık ekle: " + metin
            return cumle, _usta_adim("ara_baslik", cumle, metin=metin)
        if kind == "baslik_renk":
            if not html_mi:
                return None
            renk = bulunan.group("renk").strip().lower()
            if not _renk_hex(renk):
                return None
            cumle = "başlık rengini " + renk + " yap"
            return cumle, _usta_adim("baslik_renk", cumle, renk=renk)
        eski = bulunan.group("eski").strip().strip("\"'")
        yeni = bulunan.group("yeni").strip().strip("\"'")
        if not _soz_var(eski) or not _soz_var(yeni) or len(eski) > 180 or len(yeni) > 400:
            return None
        if eski not in kaynak:
            return None
        cumle = eski + " yerine " + yeni + " yaz"
        return cumle, _usta_adim("yerine", cumle, dosya=hedef, eski=eski, yeni=yeni)
    return None


def _tarif_coz(ham: str, hedef: str, kaynak: str) -> tuple[str, dict] | None:
    for satir in (ham or "").splitlines():
        aday = satir.strip().strip("`").strip()
        aday = re.sub(r"^(?:önerim|onerim)\s*:\s*", "", aday, flags=re.I).strip().strip("\"'")
        denenecek = [aday]
        if aday.endswith("."):
            denenecek.append(aday[:-1].strip())
        for sade in denenecek:
            if not sade:
                continue
            cozulen = _tarif_satir(sade, hedef, kaynak)
            if cozulen is not None:
                return cozulen
    return None


def _bak(repo: Path, adim: dict) -> dict:
    yol = _kilit_yolu(repo)
    if adim.get("dosya"):
        dosya = _dosya_adi(str(adim["dosya"]))
    else:
        dosya = _sayfa_dosyasi(str(adim.get("ad") or ""))
    okunan = klasor_oku_dosya(repo, dosya)
    ham = okunan["text"]
    gordum = _gordum_satir(ham)
    _bekleyen_koy(yol, None)
    gorunen = _gorunen_yazi(ham)
    soz = _soyleyen(gorunen[:1200]) if gorunen.strip() else ""
    if not soz.strip():
        reply = "Gördüm: " + gordum + "\nÖneri çıkmadı. Dosya aynı."
    else:
        cozulen = _tarif_coz(soz, dosya, ham)
        if cozulen is None:
            reply = "Gördüm: " + gordum + "\nBu tarif değil. Dosya aynı."
        else:
            cumle, bekleyen = cozulen
            _bekleyen_koy(
                yol,
                {
                    "adim": bekleyen,
                    "sayfa": dosya if dosya.lower().endswith((".html", ".htm")) else "",
                },
            )
            reply = "Gördüm: " + gordum + "\nÖnerim: " + cumle + "\nUygula dersen bunu yaparım."
    html = dosya.lower().endswith((".html", ".htm"))
    return _paket(
        reply=reply,
        gorunum="proje" if html else "kod",
        rel=okunan["rel"],
        text=ham,
        onizleme=html,
        sayfa=dosya if html else "",
    )


def _uygula(repo: Path) -> dict:
    yol = _kilit_yolu(repo)
    bekleyen = _bekleyen_al(yol)
    if not bekleyen:
        return _paket(reply="Bekleyen öneri yok.")
    _bekleyen_koy(yol, None)
    return _calistir(repo, bekleyen["adim"], str(bekleyen.get("sayfa") or ""))


def _belge_metin(ham: str, kaynak: str) -> str:
    metin = re.sub(
        r"^(?:gördüğün söz|gordugun soz)\s*[:\-]?\s*",
        "",
        (ham or "").strip().strip("\"'"),
        flags=re.I,
    ).strip()
    if not _soz_var(metin) or len(metin) > 400 or metin not in kaynak:
        return ""
    return metin


def _masa_soz_temiz(ham: str) -> str:
    return re.sub(
        r"^(?:gördüğün söz|gordugun soz|gördüğün değer|gordugun deger|gördüğün başlık|gordugun baslik)\s*[:\-]?\s*",
        "",
        (ham or "").strip().strip("\"'"),
        flags=re.I,
    ).strip()


def _masa_cumle_eylem(masa: str, sade: str, kaynak: str) -> dict | None:
    if masa == "belge":
        yerine = re.match(r"^belgede\s+(?P<eski>.+?)\s+yerine\s+(?P<yeni>.+?)\s+yaz$", sade, re.I)
        if yerine:
            eski = _masa_soz_temiz(yerine.group("eski"))
            yeni = _masa_soz_temiz(yerine.group("yeni"))
            if _soz_var(eski) and _soz_var(yeni) and eski in kaynak and yeni in kaynak and len(eski) <= 180 and len(yeni) <= 400:
                return {
                    "eylem": "belge.yerine",
                    "eski": eski,
                    "yeni": yeni,
                    "cumle": "belgede " + eski + " yerine " + yeni + " yaz",
                }
            return None
        bulunan = re.match(r"^belgeye\s+(?P<metin>.+?)\s+(?P<tur>yaz|ekle)$", sade, re.I)
        if bulunan:
            metin = _belge_metin(bulunan.group("metin"), kaynak)
            if metin:
                tur = bulunan.group("tur").lower()
                eylem = "belge.ekle" if tur == "ekle" else "belge.yaz"
                cumle = "belgeye " + metin + (" ekle" if tur == "ekle" else " yaz")
                return {"eylem": eylem, "metin": metin, "cumle": cumle}
        serbest = re.match(r"^belgeye\s+(?P<metin>.+)$", sade, re.I)
        if serbest:
            metin = _belge_metin(serbest.group("metin"), kaynak)
            if metin:
                return {"eylem": "belge.yaz", "metin": metin, "cumle": "belgeye " + metin + " yaz"}
        return None
    if masa == "tablo":
        bulunan = re.match(
            r"^(?:tabloda|tabloya)\s+(?P<sutun>[A-La-l])(?P<satir>\d{1,2})\s*(?:e|ye)?\s+(?P<deger>.+?)\s+yaz$",
            sade,
            re.I,
        )
        if bulunan:
            satir = int(bulunan.group("satir"))
            deger = bulunan.group("deger").strip().strip("\"'")
            if satir < 1 or satir > 28 or not _soz_var(deger) or len(deger) > 80 or deger not in kaynak:
                return None
            hucre = bulunan.group("sutun").upper() + str(satir)
            return {"eylem": "tablo.hucre", "hucre": hucre, "deger": deger, "cumle": "tabloda " + hucre + " e " + deger + " yaz"}
        sil = re.match(
            r"^(?:tabloda\s+)?(?P<sutun>[A-La-l])(?P<satir>\d{1,2})\s+h[üu]cresini\s+sil$",
            sade,
            re.I,
        )
        if sil:
            satir = int(sil.group("satir"))
            hucre = sil.group("sutun").upper() + str(satir)
            if satir < 1 or satir > 28 or hucre not in kaynak:
                return None
            return {"eylem": "tablo.sil", "hucre": hucre, "cumle": hucre + " hücresini sil"}
        topla = re.match(r"^(?P<sutun>[A-La-l])\s+s[üu]tununu\s+topla$", sade, re.I)
        if topla:
            sutun = topla.group("sutun").upper()
            if sutun not in kaynak:
                return None
            return {"eylem": "tablo.topla", "sutun": sutun, "cumle": sutun + " sütununu topla"}
        return None
    if masa == "cizim":
        yerli = re.search(
            r"(?:çizime|cizime)\s+(?P<yer>ortaya|üste|uste|alta)\s+"
            r"(?:(?P<renk>siyah|mavi|kırmızı|kirmizi|yeşil|yesil)\s+)?"
            r"(?P<tur>kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)",
            sade,
            re.I,
        )
        if yerli:
            yer = yerli.group("yer").lower()
            tur = yerli.group("tur").lower().replace("ç", "c")
            renk = (yerli.group("renk") or "").lower()
            if renk and not _renk_hex(renk):
                return None
            if yer == "ortaya" and tur == "kutu":
                eylem = {"eylem": "cizim.kutu", "x": 680, "y": 430, "w": 240, "h": 140}
            elif yer == "ortaya" and tur == "daire":
                eylem = {"eylem": "cizim.daire", "x": 800, "y": 500, "rx": 80, "ry": 60}
            elif yer == "ortaya":
                eylem = {"eylem": "cizim.cizgi", "x1": 200, "y1": 500, "x2": 1400, "y2": 500}
            elif yer in {"üste", "uste"} and tur == "kutu":
                eylem = {"eylem": "cizim.kutu", "x": 80, "y": 40, "w": 240, "h": 140}
            elif yer in {"üste", "uste"} and tur == "daire":
                eylem = {"eylem": "cizim.daire", "x": 300, "y": 120, "rx": 80, "ry": 60}
            elif yer in {"üste", "uste"}:
                eylem = {"eylem": "cizim.cizgi", "x1": 80, "y1": 60, "x2": 1520, "y2": 60}
            elif tur == "kutu":
                eylem = {"eylem": "cizim.kutu", "x": 80, "y": 780, "w": 240, "h": 140}
            elif tur == "cizgi":
                eylem = {"eylem": "cizim.cizgi", "x1": 80, "y1": 920, "x2": 1520, "y2": 920}
            else:
                eylem = {"eylem": "cizim.daire", "x": 800, "y": 860, "rx": 80, "ry": 60}
            if renk:
                eylem["renk"] = renk
            eylem["cumle"] = "çizime " + yer + (" " + renk if renk else "") + " " + tur + " çiz"
            return eylem
        renkli = re.search(
            r"(?:çizime|cizime)\s+(?P<renk>siyah|mavi|kırmızı|kirmizi|yeşil|yesil)\s+(?P<tur>kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)",
            sade,
            re.I,
        )
        if renkli:
            tur = renkli.group("tur").lower().replace("ç", "c")
            renk = renkli.group("renk").lower()
            if not _renk_hex(renk):
                return None
            if tur == "kutu":
                eylem = {"eylem": "cizim.kutu", "x": 80, "y": 80, "w": 240, "h": 140}
            elif tur == "daire":
                eylem = {"eylem": "cizim.daire", "x": 300, "y": 220, "rx": 80, "ry": 60}
            else:
                eylem = {"eylem": "cizim.cizgi", "x1": 40, "y1": 40, "x2": 400, "y2": 200}
            eylem["renk"] = renk
            eylem["cumle"] = "çizime " + renk + " " + ("çizgi" if tur == "cizgi" else tur) + " çiz"
            return eylem
        bulunan = re.search(r"(?:çizime|cizime)\s+(?P<tur>kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)", sade, re.I)
        if not bulunan:
            return None
        tur = bulunan.group("tur").lower().replace("ç", "c")
        if tur == "kutu":
            return {"eylem": "cizim.kutu", "x": 80, "y": 80, "w": 240, "h": 140, "cumle": "çizime kutu çiz"}
        if tur == "daire":
            return {"eylem": "cizim.daire", "x": 300, "y": 220, "rx": 80, "ry": 60, "cumle": "çizime daire çiz"}
        return {"eylem": "cizim.cizgi", "x1": 40, "y1": 40, "x2": 400, "y2": 200, "cumle": "çizime çizgi çiz"}
    if masa == "sunum":
        metin_satir = re.match(r"^slayt[ıi]n\s+metnini\s+(?P<metin>.+?)\s+yap$", sade, re.I)
        if metin_satir:
            metin = _masa_soz_temiz(metin_satir.group("metin"))
            if not _soz_var(metin) or len(metin) > 400 or metin not in kaynak:
                return None
            return {"eylem": "sunum.metin", "metin": metin, "cumle": "slaytın metnini " + metin + " yap"}
        baslik_satir = re.match(r"^slayt[ıi]n\s+ba[sş]l[ıi][gğ][ıi]n[ıi]\s+(?P<baslik>.+?)\s+yap$", sade, re.I)
        if baslik_satir:
            baslik = _masa_soz_temiz(baslik_satir.group("baslik"))
            if not _soz_var(baslik) or len(baslik) > 120 or baslik not in kaynak:
                return None
            return {"eylem": "sunum.baslik", "baslik": baslik, "cumle": "slaytın başlığını " + baslik + " yap"}
        bulunan = re.match(r"^sunuma\s+(?P<baslik>.+?)\s+slayt[ıi]\s+ekle\s*[:\-]\s*(?P<metin>.+)$", sade, re.I)
        if not bulunan:
            return None
        baslik = bulunan.group("baslik").strip().strip("\"'")
        metin = bulunan.group("metin").strip().strip("\"'")
        if not _soz_var(baslik) or not _soz_var(metin) or len(baslik) > 120 or len(metin) > 400:
            return None
        if baslik not in kaynak:
            return None
        return {"eylem": "sunum.ekle", "baslik": baslik, "metin": metin, "cumle": "sunuma " + baslik + " slaytı ekle: " + metin}
    return None


def _masa_eylem(masa: str, ham: str, kaynak: str) -> dict | None:
    for satir in (ham or "").splitlines():
        aday = satir.strip().strip("`").strip()
        aday = re.sub(r"^(?:cevap|yanıt|yanit|önerim|onerim)\s*:\s*", "", aday, flags=re.I).strip().strip("\"'")
        denenecek = [aday]
        if aday.endswith("."):
            denenecek.append(aday[:-1].strip())
        for sade in denenecek:
            if not sade:
                continue
            eylem = _masa_cumle_eylem(masa, sade, kaynak)
            if eylem is not None:
                return eylem
    return None


def masa_bak_soz(masa: str, gorunen: str) -> dict:
    """Görünen yazıdan tek masa tarifi. Bu fonksiyon masayı değiştirmez."""
    anahtar = _MASA_AD.get((masa or "").strip().lower())
    if not anahtar:
        return {"ok": True, "handled": True, "reply": "Bu masa yok.", "eylem": None}
    yazi = (gorunen or "").strip()[:1200]
    gordum = next((satir.strip() for satir in yazi.splitlines() if satir.strip()), "")[:180] or "(boş)"
    if not yazi:
        return {"ok": True, "handled": True, "reply": "Gördüm: (boş)\nÖneri çıkmadı. Masa aynı.", "eylem": None}
    soz = _masa_soyleyen(anahtar, yazi)
    if not soz.strip():
        return {"ok": True, "handled": True, "reply": "Gördüm: " + gordum + "\nÖneri çıkmadı. Masa aynı.", "eylem": None}
    bulunan = _masa_eylem(anahtar, soz, yazi)
    if not bulunan:
        return {"ok": True, "handled": True, "reply": "Gördüm: " + gordum + "\nBu tarif değil. Masa aynı.", "eylem": None}
    cumle = str(bulunan.pop("cumle"))
    return {
        "ok": True,
        "handled": True,
        "reply": "Gördüm: " + gordum + "\nÖnerim: " + cumle + "\nUygula dersen bunu yaparım.",
        "eylem": bulunan,
    }


def bekleyen_birak(repo: Path) -> dict:
    """Klasör önerisini siler. Dosyaya dokunmaz."""
    try:
        yol = _kilit_yolu(repo)
    except _KlasorYok:
        return {"ok": True, "birakildi": False}
    vardi = _bekleyen_al(yol) is not None
    _bekleyen_koy(yol, None)
    return {"ok": True, "birakildi": vardi}


def _karisik_bak(adimlar: list[dict]) -> bool:
    kinds = {a.get("kind") for a in adimlar}
    return ("bak" in kinds or "uygula" in kinds) and len(adimlar) > 1


def _sade_cumle(text: str) -> str:
    sade = re.sub(r"\s+", " ", (text or "").strip())
    sade = re.sub(r"^[Ll]ütfen\s+", "", sade)
    return re.sub(
        r"\s+(?:lütfen|lutfen|olur mu|yapar mısın|yapar misin)\s*$",
        "",
        sade,
        flags=re.I,
    ).strip()


def _usta_adim(kind: str, ham: str, **alan) -> dict:
    adim = {"kind": kind, "ham": ham}
    adim.update(alan)
    return adim


def _usta_parca(parca: str) -> list[dict] | None:
    tek = _adim(parca)
    if tek is not None:
        return [tek]
    sade = _sade_cumle(parca)
    if not sade:
        return None
    oku_sayfa = re.match(
        r"^(?P<ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]n[ıi]\s+oku$",
        sade,
        re.I,
    )
    if oku_sayfa:
        return [_usta_adim("sayfa_goster_ad", sade, ad=oku_sayfa.group("ad"))]
    sayfada = re.match(
        r"^(?P<ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi]nda\s+(?P<eski>.+?)\s+yerine\s+(?P<yeni>.+?)\s+yaz$",
        sade,
        re.I,
    )
    if sayfada:
        return [
            _usta_adim(
                "yerine",
                sade,
                ad=sayfada.group("ad"),
                eski=sayfada.group("eski").strip(),
                yeni=sayfada.group("yeni").strip(),
            )
        ]
    icinde = re.match(
        r"^(?P<dosya>\S+)\s+i[çc]inde\s+(?P<eski>.+?)\s+yerine\s+(?P<yeni>.+?)\s+yaz$",
        sade,
        re.I,
    )
    if icinde:
        return [
            _usta_adim(
                "yerine",
                sade,
                dosya=icinde.group("dosya"),
                eski=icinde.group("eski").strip(),
                yeni=icinde.group("yeni").strip(),
            )
        ]
    duz_yerine = re.match(r"^(?P<eski>.+?)\s+yerine\s+(?P<yeni>.+?)\s+yaz$", sade, re.I)
    if duz_yerine:
        return [
            _usta_adim(
                "yerine",
                sade,
                eski=duz_yerine.group("eski").strip(),
                yeni=duz_yerine.group("yeni").strip(),
            )
        ]
    baslik = re.match(
        r"^(?P<ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi](?:na|nda)\s+"
        r"(?:başlığı|basligi|başlık|baslik)\s+(?P<metin>.+?)\s+(?:yap|olsun)$",
        sade,
        re.I,
    )
    if baslik:
        return [
            _usta_adim("sayfa_ad", sade, ad=baslik.group("ad")),
            _usta_adim("baslik", sade, metin=baslik.group("metin").strip().strip("\"'")),
        ]
    yazi = re.match(
        r"^(?P<ad>[A-Za-z0-9çğıöşüÇĞİÖŞÜ._-]+)\s+sayfas[ıi](?:na|nda)\s+(?P<metin>.+?)\s+yaz$",
        sade,
        re.I,
    )
    if yazi and not _USTA_YAZI_YASAK.search(yazi.group("metin")):
        return [
            _usta_adim("sayfa_ad", sade, ad=yazi.group("ad")),
            _usta_adim("paragraf", sade, metin=yazi.group("metin").strip()),
        ]
    olsun = re.match(
        r"^(?:başlığı|basligi|başlık|baslik)\s+(?P<metin>.+?)\s+olsun$",
        sade,
        re.I,
    )
    if olsun:
        return [_usta_adim("baslik", sade, metin=olsun.group("metin").strip().strip("\"'"))]
    basliga = re.match(r"^(?:başlığına|basligina)\s+(?P<metin>.+?)\s+yaz$", sade, re.I)
    if basliga:
        return [_usta_adim("baslik", sade, metin=basliga.group("metin").strip().strip("\"'"))]
    buton = re.match(r"^(?P<metin>.+?)\s+butonu\s+(?:koy|ekle)$", sade, re.I)
    if not buton:
        buton = re.match(r"^buton\s+koy\s*[:\-]?\s*(?P<metin>.+)$", sade, re.I)
    if buton:
        return [_usta_adim("buton", sade, metin=buton.group("metin").strip().strip("\"'"))]
    if re.match(r"^(?:sayfayı|sayfayi)\s+(?:aç|ac)$", sade, re.I):
        return [_usta_adim("sayfa_goster", sade)]
    duz = re.match(r"^(?P<metin>.+?)\s+yaz$", sade, re.I)
    if duz and not _USTA_YAZI_YASAK.search(duz.group("metin")):
        return [_usta_adim("paragraf", sade, metin=duz.group("metin").strip())]
    return None


def _usta_coz(raw: str) -> list[dict] | None:
    sade = _sade_cumle(raw)
    parcalar = [p.strip() for p in re.split(r"\s*,\s*|\s+sonra\s+", sade) if p.strip()]
    if not parcalar:
        return None
    benzer = _USTA_IZ.search(sade) is not None
    adimlar: list[dict] = []
    for parca in parcalar:
        bulunan = _usta_parca(parca)
        if bulunan is None:
            if benzer or adimlar:
                raise _UstaRed()
            return None
        adimlar.extend(bulunan)
        benzer = True
    return adimlar or None


def _yurut(repo: Path, adimlar: list[dict]) -> dict:
    sayfa = ""
    son = _paket(handled=True)
    cevaplar: list[str] = []
    if len(adimlar) > 1:
        _defter_ac()
    try:
        for sira, adim in enumerate(adimlar, 1):
            try:
                son = _calistir(repo, adim, sayfa)
            except ValueError as exc:
                if len(adimlar) == 1:
                    return _paket(handled=True, reply=str(exc))
                geri = _defter_geri()
                if geri:
                    ek = "\nÖnceki adımlar geri alındı."
                    return _paket(handled=True, reply=f"{sira}. adım durdu: {adim['ham']}. {exc}{ek}")
                once = "\nÖnceki adımlar yazıldı." if cevaplar else ""
                return _paket(
                    handled=True,
                    reply=f"{sira}. adım durdu: {adim['ham']}. {exc}{once}",
                    gorunum=str(son.get("gorunum") or ""),
                    rel=str(son.get("rel") or ""),
                    text=son.get("text") if isinstance(son.get("text"), str) else None,
                    onizleme=bool(son.get("onizleme")),
                    klasor=str(son.get("klasor") or ""),
                    sayfa=str(son.get("sayfa") or ""),
                )
            if son.get("sayfa"):
                sayfa = str(son["sayfa"])
            if son.get("reply"):
                cevaplar.append(str(son["reply"]))
        if len(adimlar) == 1:
            return son
        son = dict(son)
        son["reply"] = "\n".join(cevaplar)
        return son
    finally:
        _defter_kapat()


def klasor_soz(repo: Path, yazi: str) -> dict:
    """Kilitli klasörde bilinen cümle. Çözülemeyen iş dosyaya dokunmaz."""
    raw = (yazi or "").strip()
    if not raw or len(raw) > 600:
        return _paket(handled=False)
    tek = _adim(raw)
    if tek is not None:
        try:
            return _yurut(repo, [tek])
        except _KlasorYok:
            if tek.get("kind") in {"bak", "uygula"} or tek.get("kind") in _EL:
                return _paket(
                    handled=True,
                    reply="Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol",
                )
            return _paket(handled=False)
    parcalar = [p.strip() for p in _AYIR.split(raw) if p.strip()]
    if len(parcalar) >= 2:
        adimlar = []
        tam = True
        for parca in parcalar:
            bulunan = _adim(parca)
            if bulunan is None:
                tam = False
                break
            adimlar.append(bulunan)
        if tam:
            if _karisik_bak(adimlar):
                return _paket(handled=True, reply=_USTA_RED)
            try:
                return _yurut(repo, adimlar)
            except _KlasorYok:
                return _paket(
                    handled=True,
                    reply="Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol",
                )
    try:
        usta = _usta_coz(raw)
    except _UstaRed:
        return _paket(handled=True, reply=_USTA_RED)
    if usta:
        if _karisik_bak(usta):
            return _paket(handled=True, reply=_USTA_RED)
        try:
            return _yurut(repo, usta)
        except _KlasorYok:
            if (
                len(usta) == 1
                and usta[0].get("kind") == "yerine"
                and not usta[0].get("ad")
                and not usta[0].get("dosya")
            ):
                return _paket(handled=False)
            return _paket(
                handled=True,
                reply="Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol",
            )
    return _paket(handled=False)
