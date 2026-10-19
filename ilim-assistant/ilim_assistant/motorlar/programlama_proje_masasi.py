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


def _pin_data() -> dict:
    pin = _pin_dosyasi()
    if not pin.is_file() or pin.is_symlink():
        return {}
    try:
        data = json.loads(pin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _pin_yaz(data: dict) -> None:
    pin = _pin_dosyasi()
    if pin.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    temiz = {anahtar: str(deger) for anahtar, deger in data.items() if deger and anahtar in {"klasor", "dis"}}
    if not temiz:
        if pin.is_file():
            pin.unlink()
        return
    pin.parent.mkdir(parents=True, exist_ok=True)
    pin.write_text(json.dumps(temiz, ensure_ascii=False), encoding="utf-8")


def klasor_kaydet(repo: Path, klasor: str) -> dict:
    data = _pin_data()
    if not (klasor or "").strip():
        data.pop("klasor", None)
        _pin_yaz(data)
        return {"ok": True, "klasor": ""}
    hedef = klasor_guvenli(repo, klasor)
    data["klasor"] = str(hedef)
    _pin_yaz(data)
    return {"ok": True, "klasor": str(hedef)}


def klasor_oku() -> str:
    return str(_pin_data().get("klasor") or "")


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
    ("orta_is", re.compile(r"^orta\s+i[şs]\s+yap$", re.I)),
    ("orta_soyle", re.compile(r"^orta\s+i[şs]i\s+s[öo]yle$", re.I)),
    ("orta_not", re.compile(
        r"^orta\s+notu\s+yaz\s*[:\-]\s*(?P<metin>.+)$",
        re.I,
    )),
    ("orta_not_oku", re.compile(r"^orta\s+notunu\s+oku$", re.I)),
    ("orta_not_satir", re.compile(
        r"^orta\s+notuna\s+sat[ıi]r\s+ekle\s*[:\-]\s*(?P<metin>.+)$",
        re.I,
    )),
    ("orta_arac_not", re.compile(r"^orta\s+arac[ıi]nda\s+notu\s+say$", re.I)),
    ("orta_arac_not", re.compile(r"^orta\s+arac[ıi]nda\s+sat[ıi]r\s+say$", re.I)),
    ("orta_arac_satir", re.compile(
        r"^orta\s+arac[ıi]nda\s+sat[ıi]r\s+say\s*[:\-]\s*(?P<metin>.+)$",
        re.I,
    )),
    ("orta_tur_baslat", re.compile(r"^orta\s+turu\s+ba[sş]lat$", re.I)),
    ("orta_tur_duzelt_fazla", re.compile(r"^orta\s+turu\s+d[üu]zelt\b.+$", re.I)),
    ("orta_tur_duzelt", re.compile(r"^orta\s+turu\s+d[üu]zelt$", re.I)),
    ("orta_tur_bak_fazla", re.compile(r"^orta\s+turu\s+bak\b.+$", re.I)),
    ("orta_tur_bak", re.compile(r"^orta\s+turu\s+bak$", re.I)),
    ("orta_tur_kapat_fazla", re.compile(r"^orta\s+turu\s+kapat\b.+$", re.I)),
    ("orta_tur_kapat", re.compile(r"^orta\s+turu\s+kapat$", re.I)),
    ("orta_tur_soyle_fazla", re.compile(r"^orta\s+turu\s+s[öo]yle\b.+$", re.I)),
    ("orta_tur_soyle", re.compile(r"^orta\s+turu\s+s[öo]yle$", re.I)),
    ("orta_kayit_fazla", re.compile(r"^orta\s+ara[çc]\s+kayd[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("orta_kayit", re.compile(r"^orta\s+ara[çc]\s+kayd[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("orta_arac_soyle_fazla", re.compile(r"^orta\s+arac[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("orta_arac_soyle", re.compile(r"^orta\s+arac[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("arac_dosya_satir_fazla", re.compile(r"^ara[çc]\s+dosyas[ıi]n[ıi]n\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("arac_dosya_satir", re.compile(r"^ara[çc]\s+dosyas[ıi]n[ıi]n\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("hazir_iki_fazla", re.compile(r"^haz[ıi]r\s+ikisini\s+s[öo]yle\b.+$", re.I)),
    ("hazir_iki", re.compile(r"^haz[ıi]r\s+ikisini\s+s[öo]yle$", re.I)),
    ("olcu_soyle_fazla", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]n[üu]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_soyle", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]n[üu]\s+s[öo]yle$", re.I)),
    ("olcu_say_metin", re.compile(
        r"^orta\s+[öo]l[çc][üu]s[üu]nde\s+kelime\s+say\s*:\s*(?P<metin>.+)$",
        re.I,
    )),
    ("olcu_say", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]nde\s+kelime\s+say$", re.I)),
    ("olcu_say_fazla", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]nde\s+kelime\s+say\b.+$", re.I)),
    ("olcu_neden", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]\s+neden\s+kald[ıi]$", re.I)),
    ("olcu_duzelt_fazla", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]n[üu]\s+d[üu]zelt\b.+$", re.I)),
    ("olcu_duzelt", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]n[üu]\s+d[üu]zelt$", re.I)),
    ("olcu_bak_fazla", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]ne\s+bak\b.+$", re.I)),
    ("olcu_bak", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]ne\s+bak$", re.I)),
    ("olcu_kapat_fazla", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]n[üu]\s+kapat\b.+$", re.I)),
    ("olcu_kapat", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]n[üu]\s+kapat$", re.I)),
    ("olcu_test_fazla", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]n[üu]\s+[çc]al[ıi][sş]t[ıi]r\b.+$", re.I)),
    ("olcu_test", re.compile(r"^orta\s+[öo]l[çc][üu]s[üu]n[üu]\s+[çc]al[ıi][sş]t[ıi]r$", re.I)),
    ("olcu_sira_fazla", re.compile(r"^orta\s+[öo]l[çc][üu]\s+s[ıi]ras[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_sira", re.compile(r"^orta\s+[öo]l[çc][üu]\s+s[ıi]ras[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_kayit_fazla", re.compile(r"^orta\s+[öo]l[çc][üu]\s+kayd[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_kayit", re.compile(r"^orta\s+[öo]l[çc][üu]\s+kayd[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_dosya_satir_fazla", re.compile(r"^[öo]l[çc][üu]\s+dosyas[ıi]n[ıi]n\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_dosya_satir", re.compile(r"^[öo]l[çc][üu]\s+dosyas[ıi]n[ıi]n\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_notu_var_fazla", re.compile(r"^[öo]l[çc][üu]\s+notu\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_notu_var", re.compile(r"^[öo]l[çc][üu]\s+notu\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_satir_soyle_fazla", re.compile(r"^[öo]l[çc][üu]\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_satir_soyle", re.compile(r"^[öo]l[çc][üu]\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_satir_yaz_fazla", re.compile(r"^[öo]l[çc][üu]\s+sat[ıi]r[ıi]\s+yaz\b.+$", re.I)),
    ("olcu_satir_yaz", re.compile(r"^[öo]l[çc][üu]\s+sat[ıi]r[ıi]\s+yaz$", re.I)),
    ("orta_neden", re.compile(r"^orta\s+testi\s+neden\s+kald[ıi]$", re.I)),
    ("orta_duzelt_eksik", re.compile(r"^orta\s+arac[ıi]n[ıi]\s+d[üu]zelt\s*:?\s*$", re.I)),
    ("orta_duzelt", re.compile(
        r"^orta\s+arac[ıi]n[ıi]\s+d[üu]zelt\s*:\s*(?P<metin>.+)$",
        re.I,
    )),
    ("orta_bakis", re.compile(r"^orta\s+testine\s+ikinci\s+bak$", re.I)),
    ("tahta_bitti", re.compile(r"^a[çc][ıi]k\s+sat[ıi]r[ıi]\s+bitti\s+yap$", re.I)),
    ("tahta_say_fazla", re.compile(r"^a[çc][ıi]k\s+sat[ıi]r\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("tahta_say", re.compile(r"^a[çc][ıi]k\s+sat[ıi]r\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("tahta_bitti_say_fazla", re.compile(r"^bitti\s+sat[ıi]r\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("tahta_bitti_say", re.compile(r"^bitti\s+sat[ıi]r\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("kilit_soyle_fazla", re.compile(r"^kilitli\s+klas[öo]r[üu]\s+s[öo]yle\b.+$", re.I)),
    ("kilit_soyle", re.compile(r"^kilitli\s+klas[öo]r[üu]\s+s[öo]yle$", re.I)),
    ("orta_test", re.compile(r"^orta\s+testini\s+[çc]al[ıi][sş]t[ıi]r$", re.I)),
    ("uygulama_not", re.compile(
        r"^uygulama\s+notu\s+yaz\s*[:\-]\s*(?P<metin>.+)$",
        re.I,
    )),
    ("uygulama_not_oku", re.compile(r"^uygulama\s+notunu\s+oku$", re.I)),
    ("uygulama_not_say_fazla", re.compile(r"^uygulama\s+notunun\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("uygulama_not_say", re.compile(r"^uygulama\s+notunun\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("uygulama_not_son_fazla", re.compile(r"^uygulama\s+notunun\s+son\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("uygulama_not_son", re.compile(r"^uygulama\s+notunun\s+son\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("uygulama_not_satir", re.compile(
        r"^uygulama\s+notuna\s+sat[ıi]r\s+ekle\s*[:\-]\s*(?P<metin>.+)$",
        re.I,
    )),
    ("uygulama_not_satir_fazla", re.compile(r"^uygulama\s+notuna\s+sat[ıi]r\s+ekle\b.+$", re.I)),
    ("kaynak_satir_soyle_fazla", re.compile(r"^kaynak\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("kaynak_satir_soyle", re.compile(r"^kaynak\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("kapi_var_fazla", re.compile(r"^kap[ıi]\s+notu\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("kapi_var", re.compile(r"^kap[ıi]\s+notu\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("kaynak_satir", re.compile(
        r"^kaynak\s+sat[ıi]r[ıi]\s+yaz\s*[:\-]\s*(?P<metin>.+)$",
        re.I,
    )),
    ("dis_klasor", re.compile(r"^d[ıi]ş\s+klas[öo]r\s*:\s*(?P<yol>.+)$", re.I)),
    ("dis_say", re.compile(r"^d[ıi]ş\s+klas[öo]r[üu]\s+say$", re.I)),
    ("dis_oku", re.compile(r"^d[ıi]ş\s+dosyay[ıi]\s+oku\s*:\s*(?P<ad>\S+)$", re.I)),
    ("dis_olcu_fazla", re.compile(r"^d[ıi]ş\s+[öo]l[çc][üu]\s+dosyas[ıi]n[ıi]\s+oku\b.+$", re.I)),
    ("dis_olcu", re.compile(r"^d[ıi]ş\s+[öo]l[çc][üu]\s+dosyas[ıi]n[ıi]\s+oku$", re.I)),
    ("dis_olcu_yaz_fazla", re.compile(r"^d[ıi]ş\s+[öo]l[çc][üu]\s+dosyas[ıi]na\s+yaz\b.+$", re.I)),
    ("dis_olcu_yaz", re.compile(r"^d[ıi]ş\s+[öo]l[çc][üu]\s+dosyas[ıi]na\s+yaz$", re.I)),
    ("dis_olcu_yer_fazla", re.compile(r"^d[ıi]ş\s+[öo]l[çc][üu]\s+yerini\s+s[öo]yle\b.+$", re.I)),
    ("dis_olcu_yer", re.compile(r"^d[ıi]ş\s+[öo]l[çc][üu]\s+yerini\s+s[öo]yle$", re.I)),
    ("dis_klasor_soyle_fazla", re.compile(r"^d[ıi]ş\s+klas[öo]r[üu]\s+s[öo]yle\b.+$", re.I)),
    ("dis_klasor_soyle", re.compile(r"^d[ıi]ş\s+klas[öo]r[üu]\s+s[öo]yle$", re.I)),
    ("dis_adet_fazla", re.compile(r"^d[ıi]ş\s+klas[öo]r[üu]n\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("dis_adet", re.compile(r"^d[ıi]ş\s+klas[öo]r[üu]n\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("dis_yaz", re.compile(
        r"^d[ıi]ş\s+dosyaya\s+yaz\s*:\s*(?P<ad>[^:\s]+)\s*:\s*(?P<metin>.+)$",
        re.I,
    )),
    ("git_durum", re.compile(r"^git\s+ne\s+durumda$", re.I)),
    ("git_olcu_fark_fazla", re.compile(r"^git\s+[öo]l[çc][üu]\s+fark[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("git_olcu_fark", re.compile(r"^git\s+[öo]l[çc][üu]\s+fark[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("git_fark_fazla", re.compile(r"^git\s+fark[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("git_fark", re.compile(r"^git\s+fark[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("git_son_fazla", re.compile(r"^git\s+son\s+kayd[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("git_son", re.compile(r"^git\s+son\s+kayd[ıi]\s+s[öo]yle$", re.I)),
    ("git_dal_fazla", re.compile(r"^git\s+dal[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("git_dal", re.compile(r"^git\s+dal[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("git_depo_fazla", re.compile(r"^git\s+deposu\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("git_depo", re.compile(r"^git\s+deposu\s+mu\s+s[öo]yle$", re.I)),
    ("git_temiz_fazla", re.compile(r"^git\s+temiz\s+mi\s+s[öo]yle\b.+$", re.I)),
    ("git_temiz", re.compile(r"^git\s+temiz\s+mi\s+s[öo]yle$", re.I)),
    ("uygulama_not_ilk_fazla", re.compile(r"^uygulama\s+notunun\s+ilk\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("uygulama_not_ilk", re.compile(r"^uygulama\s+notunun\s+ilk\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("uygulama_not_var_fazla", re.compile(r"^uygulama\s+notu\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("uygulama_not_var", re.compile(r"^uygulama\s+notu\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_dosya_var_fazla", re.compile(r"^[öo]l[çc][üu]\s+dosyas[ıi]\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_dosya_var", re.compile(r"^[öo]l[çc][üu]\s+dosyas[ıi]\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("arac_dosya_var_fazla", re.compile(r"^ara[çc]\s+dosyas[ıi]\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("arac_dosya_var", re.compile(r"^ara[çc]\s+dosyas[ıi]\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_kayit_var_fazla", re.compile(r"^[öo]l[çc][üu]\s+kayd[ıi]\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_kayit_var", re.compile(r"^[öo]l[çc][üu]\s+kayd[ıi]\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("arac_kayit_var_fazla", re.compile(r"^ara[çc]\s+kayd[ıi]\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("arac_kayit_var", re.compile(r"^ara[çc]\s+kayd[ıi]\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("tahta_var_fazla", re.compile(r"^tahta\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("tahta_var", re.compile(r"^tahta\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("tahta_satir_fazla", re.compile(r"^tahta\s+sat[ıi]r\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("tahta_satir", re.compile(r"^tahta\s+sat[ıi]r\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("kilit_adet_fazla", re.compile(r"^kilitli\s+klas[öo]r[üu]n\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("kilit_adet", re.compile(r"^kilitli\s+klas[öo]r[üu]n\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("hazir_olcu_satir_fazla", re.compile(r"^haz[ıi]r\s+[öo]l[çc][üu]\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("hazir_olcu_satir", re.compile(r"^haz[ıi]r\s+[öo]l[çc][üu]\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("hazir_arac_satir_fazla", re.compile(r"^haz[ıi]r\s+ara[çc]\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("hazir_arac_satir", re.compile(r"^haz[ıi]r\s+ara[çc]\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("hazir_olcu_fazla", re.compile(r"^haz[ıi]r\s+[öo]l[çc][üu]y[üu]\s+s[öo]yle\b.+$", re.I)),
    ("hazir_olcu", re.compile(r"^haz[ıi]r\s+[öo]l[çc][üu]y[üu]\s+s[öo]yle$", re.I)),
    ("kapi_satir_fazla", re.compile(r"^kap[ıi]\s+notunun\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("kapi_satir", re.compile(r"^kap[ıi]\s+notunun\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_notu_satir_fazla", re.compile(r"^[öo]l[çc][üu]\s+notunun\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_notu_satir", re.compile(r"^[öo]l[çc][üu]\s+notunun\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_bakis_fazla", re.compile(r"^[öo]l[çc][üu]\s+bak[ıi][sş][ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_bakis", re.compile(r"^[öo]l[çc][üu]\s+bak[ıi][sş][ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("arac_bakis_fazla", re.compile(r"^ara[çc]\s+bak[ıi][sş][ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("arac_bakis", re.compile(r"^ara[çc]\s+bak[ıi][sş][ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_kapandi_fazla", re.compile(r"^[öo]l[çc][üu]\s+kapand[ıi]\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_kapandi", re.compile(r"^[öo]l[çc][üu]\s+kapand[ıi]\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_duzeltme_fazla", re.compile(r"^[öo]l[çc][üu]\s+d[üu]zeltmesini\s+s[öo]yle\b.+$", re.I)),
    ("olcu_duzeltme", re.compile(r"^[öo]l[çc][üu]\s+d[üu]zeltmesini\s+s[öo]yle$", re.I)),
    ("olcu_gecti_fazla", re.compile(r"^[öo]l[çc][üu]\s+ge[çc]ti\s+mi\s+s[öo]yle\b.+$", re.I)),
    ("olcu_gecti", re.compile(r"^[öo]l[çc][üu]\s+ge[çc]ti\s+mi\s+s[öo]yle$", re.I)),
    ("olcu_durdu_fazla", re.compile(r"^[öo]l[çc][üu]\s+durdu\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("olcu_durdu", re.compile(r"^[öo]l[çc][üu]\s+durdu\s+mu\s+s[öo]yle$", re.I)),
    ("hazir_olcu_kaldi_fazla", re.compile(r"^haz[ıi]r\s+[öo]l[çc][üu]\s+kald[ıi]\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("hazir_olcu_kaldi", re.compile(r"^haz[ıi]r\s+[öo]l[çc][üu]\s+kald[ıi]\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("olcu_kaldi_fazla", re.compile(r"^[öo]l[çc][üu]\s+kald[ıi]\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("olcu_kaldi", re.compile(r"^[öo]l[çc][üu]\s+kald[ıi]\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("arac_duzeltme_fazla", re.compile(r"^ara[çc]\s+d[üu]zeltmesini\s+s[öo]yle\b.+$", re.I)),
    ("arac_duzeltme", re.compile(r"^ara[çc]\s+d[üu]zeltmesini\s+s[öo]yle$", re.I)),
    ("arac_gecti_fazla", re.compile(r"^ara[çc]\s+ge[çc]ti\s+mi\s+s[öo]yle\b.+$", re.I)),
    ("arac_gecti", re.compile(r"^ara[çc]\s+ge[çc]ti\s+mi\s+s[öo]yle$", re.I)),
    ("arac_durdu_fazla", re.compile(r"^ara[çc]\s+durdu\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("arac_durdu", re.compile(r"^ara[çc]\s+durdu\s+mu\s+s[öo]yle$", re.I)),
    ("arac_kaldi_fazla", re.compile(r"^ara[çc]\s+kald[ıi]\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("arac_kaldi", re.compile(r"^ara[çc]\s+kald[ıi]\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("arac_tur_fazla", re.compile(r"^ara[çc]\s+turunu\s+s[öo]yle\b.+$", re.I)),
    ("arac_tur", re.compile(r"^ara[çc]\s+turunu\s+s[öo]yle$", re.I)),
    ("hazir_arac_fazla", re.compile(r"^haz[ıi]r\s+arac[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("hazir_arac", re.compile(r"^haz[ıi]r\s+arac[ıi]\s+s[öo]yle$", re.I)),
    ("tek_acik_fazla", re.compile(r"^tek\s+a[çc][ıi]k\s+sat[ıi]r\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("tek_acik", re.compile(r"^tek\s+a[çc][ıi]k\s+sat[ıi]r\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("tahta_ilk_fazla", re.compile(r"^tahtan[ıi]n\s+ilk\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("tahta_ilk", re.compile(r"^tahtan[ıi]n\s+ilk\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("tahta_son_fazla", re.compile(r"^tahtan[ıi]n\s+son\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("tahta_son", re.compile(r"^tahtan[ıi]n\s+son\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("tahta_bos_fazla", re.compile(r"^tahta\s+bo[sş]\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("tahta_bos", re.compile(r"^tahta\s+bo[sş]\s+mu\s+s[öo]yle$", re.I)),
    ("kilit_bos_fazla", re.compile(r"^kilitli\s+klas[öo]r\s+bo[sş]\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("kilit_bos", re.compile(r"^kilitli\s+klas[öo]r\s+bo[sş]\s+mu\s+s[öo]yle$", re.I)),
    ("dis_bos_fazla", re.compile(r"^d[ıi][sş]\s+klas[öo]r\s+bo[sş]\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("dis_bos", re.compile(r"^d[ıi][sş]\s+klas[öo]r\s+bo[sş]\s+mu\s+s[öo]yle$", re.I)),
    ("uygulama_not_bos_fazla", re.compile(r"^uygulama\s+notu\s+bo[sş]\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("uygulama_not_bos", re.compile(r"^uygulama\s+notu\s+bo[sş]\s+mu\s+s[öo]yle$", re.I)),
    ("orta_not_var_fazla", re.compile(r"^orta\s+notu\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("orta_not_var", re.compile(r"^orta\s+notu\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("orta_not_satir_say_fazla", re.compile(r"^orta\s+notunun\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("orta_not_satir_say", re.compile(r"^orta\s+notunun\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("kapi_ilk_fazla", re.compile(r"^kap[ıi]\s+notunun\s+ilk\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("kapi_ilk", re.compile(r"^kap[ıi]\s+notunun\s+ilk\s+sat[ıi]r[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("git_uzak_fazla", re.compile(r"^git\s+uzak\s+var\s+m[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("git_uzak", re.compile(r"^git\s+uzak\s+var\s+m[ıi]\s+s[öo]yle$", re.I)),
    ("git_bas_fazla", re.compile(r"^git\s+ba[sş][ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("git_bas", re.compile(r"^git\s+ba[sş][ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("git_kayit_say_fazla", re.compile(r"^git\s+kay[ıi]t\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle\b.+$", re.I)),
    ("git_kayit_say", re.compile(r"^git\s+kay[ıi]t\s+say[ıi]s[ıi]n[ıi]\s+s[öo]yle$", re.I)),
    ("git_dal_temiz_fazla", re.compile(r"^git\s+dal[ıi]\s+temiz\s+mi\s+s[öo]yle\b.+$", re.I)),
    ("git_dal_temiz", re.compile(r"^git\s+dal[ıi]\s+temiz\s+mi\s+s[öo]yle$", re.I)),
    ("olcu_kayit_bos_fazla", re.compile(r"^[öo]l[çc][üu]\s+kayd[ıi]\s+bo[sş]\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("olcu_kayit_bos", re.compile(r"^[öo]l[çc][üu]\s+kayd[ıi]\s+bo[sş]\s+mu\s+s[öo]yle$", re.I)),
    ("arac_kayit_bos_fazla", re.compile(r"^ara[çc]\s+kayd[ıi]\s+bo[sş]\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("arac_kayit_bos", re.compile(r"^ara[çc]\s+kayd[ıi]\s+bo[sş]\s+mu\s+s[öo]yle$", re.I)),
    ("olcu_dosya_bos_fazla", re.compile(r"^[öo]l[çc][üu]\s+dosyas[ıi]\s+bo[sş]\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("olcu_dosya_bos", re.compile(r"^[öo]l[çc][üu]\s+dosyas[ıi]\s+bo[sş]\s+mu\s+s[öo]yle$", re.I)),
    ("arac_dosya_bos_fazla", re.compile(r"^ara[çc]\s+dosyas[ıi]\s+bo[sş]\s+mu\s+s[öo]yle\b.+$", re.I)),
    ("arac_dosya_bos", re.compile(r"^ara[çc]\s+dosyas[ıi]\s+bo[sş]\s+mu\s+s[öo]yle$", re.I)),
    ("git_kaydet", re.compile(r"^git\s+kaydet\s*:\s*(?P<metin>.+)$", re.I)),
    ("git_gonder", re.compile(r"^git\s+g[öo]nder$", re.I)),
    ("git_yazma", re.compile(r"^git\s+kaydet$", re.I)),
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
    "orta_is",
    "orta_soyle",
    "orta_not",
    "orta_not_oku",
    "orta_not_satir",
    "orta_arac_not",
    "orta_arac_satir",
    "orta_tur_baslat",
    "orta_tur_duzelt_fazla",
    "orta_tur_duzelt",
    "orta_tur_bak_fazla",
    "orta_tur_bak",
    "orta_tur_kapat_fazla",
    "orta_tur_kapat",
    "orta_tur_soyle_fazla",
    "orta_tur_soyle",
    "orta_kayit_fazla",
    "orta_kayit",
    "orta_arac_soyle_fazla",
    "orta_arac_soyle",
    "arac_dosya_satir_fazla",
    "arac_dosya_satir",
    "hazir_iki_fazla",
    "hazir_iki",
    "olcu_soyle_fazla",
    "olcu_soyle",
    "olcu_say_metin",
    "olcu_say",
    "olcu_say_fazla",
    "olcu_neden",
    "olcu_duzelt_fazla",
    "olcu_duzelt",
    "olcu_bak_fazla",
    "olcu_bak",
    "olcu_kapat_fazla",
    "olcu_kapat",
    "olcu_test_fazla",
    "olcu_test",
    "olcu_sira_fazla",
    "olcu_sira",
    "olcu_kayit_fazla",
    "olcu_kayit",
    "olcu_dosya_satir_fazla",
    "olcu_dosya_satir",
    "olcu_notu_var_fazla",
    "olcu_notu_var",
    "olcu_satir_soyle_fazla",
    "olcu_satir_soyle",
    "olcu_satir_yaz_fazla",
    "olcu_satir_yaz",
    "orta_neden",
    "orta_duzelt_eksik",
    "orta_duzelt",
    "orta_bakis",
    "tahta_bitti",
    "tahta_say_fazla",
    "tahta_say",
    "tahta_bitti_say_fazla",
    "tahta_bitti_say",
    "kilit_soyle_fazla",
    "kilit_soyle",
    "orta_test",
    "uygulama_not",
    "uygulama_not_oku",
    "uygulama_not_say_fazla",
    "uygulama_not_say",
    "uygulama_not_son_fazla",
    "uygulama_not_son",
    "uygulama_not_satir",
    "uygulama_not_satir_fazla",
    "kaynak_satir_soyle_fazla",
    "kaynak_satir_soyle",
    "kapi_var_fazla",
    "kapi_var",
    "kaynak_satir",
    "dis_klasor",
    "dis_say",
    "dis_oku",
    "dis_olcu_fazla",
    "dis_olcu",
    "dis_olcu_yaz_fazla",
    "dis_olcu_yaz",
    "dis_olcu_yer_fazla",
    "dis_olcu_yer",
    "dis_klasor_soyle_fazla",
    "dis_klasor_soyle",
    "dis_adet_fazla",
    "dis_adet",
    "dis_yaz",
    "git_durum",
    "git_olcu_fark_fazla",
    "git_olcu_fark",
    "git_fark_fazla",
    "git_fark",
    "git_son_fazla",
    "git_son",
    "git_dal_fazla",
    "git_dal",
    "git_depo_fazla",
    "git_depo",
    "git_temiz_fazla",
    "git_temiz",
    "uygulama_not_ilk_fazla",
    "uygulama_not_ilk",
    "uygulama_not_var_fazla",
    "uygulama_not_var",
    "olcu_dosya_var_fazla",
    "olcu_dosya_var",
    "arac_dosya_var_fazla",
    "arac_dosya_var",
    "olcu_kayit_var_fazla",
    "olcu_kayit_var",
    "arac_kayit_var_fazla",
    "arac_kayit_var",
    "tahta_var_fazla",
    "tahta_var",
    "tahta_satir_fazla",
    "tahta_satir",
    "kilit_adet_fazla",
    "kilit_adet",
    "hazir_olcu_satir_fazla",
    "hazir_olcu_satir",
    "hazir_arac_satir_fazla",
    "hazir_arac_satir",
    "hazir_olcu_fazla",
    "hazir_olcu",
    "kapi_satir_fazla",
    "kapi_satir",
    "olcu_notu_satir_fazla",
    "olcu_notu_satir",
    "olcu_bakis_fazla",
    "olcu_bakis",
    "arac_bakis_fazla",
    "arac_bakis",
    "olcu_kapandi_fazla",
    "olcu_kapandi",
    "olcu_duzeltme_fazla",
    "olcu_duzeltme",
    "olcu_gecti_fazla",
    "olcu_gecti",
    "olcu_durdu_fazla",
    "olcu_durdu",
    "hazir_olcu_kaldi_fazla",
    "hazir_olcu_kaldi",
    "olcu_kaldi_fazla",
    "olcu_kaldi",
    "arac_duzeltme_fazla",
    "arac_duzeltme",
    "arac_gecti_fazla",
    "arac_gecti",
    "arac_durdu_fazla",
    "arac_durdu",
    "arac_kaldi_fazla",
    "arac_kaldi",
    "arac_tur_fazla",
    "arac_tur",
    "hazir_arac_fazla",
    "hazir_arac",
    "tek_acik_fazla",
    "tek_acik",
    "tahta_ilk_fazla",
    "tahta_ilk",
    "tahta_son_fazla",
    "tahta_son",
    "tahta_bos_fazla",
    "tahta_bos",
    "kilit_bos_fazla",
    "kilit_bos",
    "dis_bos_fazla",
    "dis_bos",
    "uygulama_not_bos_fazla",
    "uygulama_not_bos",
    "orta_not_var_fazla",
    "orta_not_var",
    "orta_not_satir_say_fazla",
    "orta_not_satir_say",
    "kapi_ilk_fazla",
    "kapi_ilk",
    "git_uzak_fazla",
    "git_uzak",
    "git_bas_fazla",
    "git_bas",
    "git_kayit_say_fazla",
    "git_kayit_say",
    "git_dal_temiz_fazla",
    "git_dal_temiz",
    "olcu_kayit_bos_fazla",
    "olcu_kayit_bos",
    "arac_kayit_bos_fazla",
    "arac_kayit_bos",
    "olcu_dosya_bos_fazla",
    "olcu_dosya_bos",
    "arac_dosya_bos_fazla",
    "arac_dosya_bos",
    "git_kaydet",
    "git_gonder",
    "git_yazma",
}


def py_kilit_cumlesi(message: str) -> bool:
    """Python oku/söyle ve çalıştırma reddi. Ajan kapısından önce gelir."""
    adim = _adim(message or "")
    return bool(adim and adim.get("kind") in _PY_OKU)


def tarif_cumlesi(message: str) -> bool:
    """Kilitli klasörün bildiği cümle. Ses kartından ve ajandan önce gelir."""
    raw = (message or "").strip()
    if _adim(raw):
        return True
    parcalar = [p.strip() for p in _AYIR.split(raw) if p.strip()]
    if len(parcalar) < 2:
        return False
    return all(_adim(parca) for parca in parcalar)


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


_ORTA_DOSYA = {
    "orta/index.html": """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>Orta iş</title>
  <link rel="stylesheet" href="site.css">
</head>
<body>
  <h1 id="baslik">Orta iş</h1>
  <button id="dugme" type="button">Say</button>
  <script src="site.js"></script>
</body>
</html>
""",
    "orta/site.css": """body { font-family: sans-serif; margin: 2rem; }
h1 { color: #1a365d; }
button { padding: 0.5rem 1rem; }
""",
    "orta/site.js": """var dugme = document.getElementById("dugme");
var baslik = document.getElementById("baslik");
if (dugme && baslik) {
  dugme.addEventListener("click", function () {
    baslik.textContent = "Sayıldı";
  });
}
""",
    "orta/arac.py": '''"""Satir sayar. Calistirilmaz; el yalniz okur."""


def satir_say(metin):
    """Bos olmayan satirlari sayar."""
    return len([satir for satir in metin.splitlines() if satir.strip()])
''',
}


def _orta_is(repo: Path) -> dict:
    yazilan: list[str] = []
    duran: list[str] = []
    for rel, metin in _ORTA_DOSYA.items():
        try:
            klasor_oku_dosya(repo, rel)
        except ValueError:
            klasor_yaz(repo, rel, metin)
            yazilan.append(rel)
        else:
            duran.append(rel)
    if not yazilan:
        govde = "Orta iş duruyor."
    else:
        govde = "Yazıldı: " + ", ".join(yazilan) + "."
        if duran:
            govde += " Duruyor: " + ", ".join(duran) + "."
    return _paket(reply=govde + "\nÇalıştırmadım. Dosya şablondan geldi.")


def _orta_ozet(rel: str, metin: str) -> str:
    if rel.endswith(".html"):
        bulunan = re.search(r"<h1[^>]*>(.*?)</h1>", metin, re.I | re.S)
        baslik = re.sub(r"<[^>]+>", "", bulunan.group(1)).strip() if bulunan else ""
        dugme = "düğme var" if "<button" in metin.lower() else "düğme yok"
        return f"başlık {baslik or 'yok'}. {dugme}."
    if rel.endswith(".css"):
        return f"{metin.count('{')} görünüş kuralı."
    if rel.endswith(".js"):
        if "textContent" in metin:
            return "düğme yazısını değiştirir. Çalıştırmadım."
        return "betik var. Çalıştırmadım."
    if rel.endswith(".py"):
        try:
            agac = ast.parse(metin)
        except SyntaxError:
            return "Python dosyası okunmadı. Çalıştırmadım."
        adlar = [d.name for d in agac.body if isinstance(d, ast.FunctionDef)]
        if adlar:
            return "fonksiyon: " + ", ".join(adlar) + ". Çalıştırmadım."
        return "fonksiyon yok. Çalıştırmadım."
    return "dosya var. Çalıştırmadım."


_ORTA_NOT = "orta/not.txt"
_ORTA_NOT_TAVAN = 8


def _orta_soyle(repo: Path) -> dict:
    satirlar: list[str] = []
    for rel in _ORTA_DOSYA:
        try:
            bulunan = klasor_oku_dosya(repo, rel)
        except ValueError:
            satirlar.append(rel + " yok.")
            continue
        satirlar.append(rel + ": " + _orta_ozet(rel, bulunan.get("text") or ""))
    satirlar.append(_orta_not_satiri(repo))
    return _paket(reply="\n".join(satirlar) + "\nÇalıştırmadım. Dosya aynı.")


def _not_satiri(metin: str) -> str:
    satir = re.sub(r"\s+", " ", metin or "").strip()
    if not satir or len(satir) > 180:
        raise ValueError("Not bir satır olsun. En çok 180 karakter.")
    return satir


def _not_satirlari(metin: str) -> list[str]:
    return [satir.strip() for satir in (metin or "").splitlines() if satir.strip()]


def _orta_not_satiri(repo: Path) -> str:
    try:
        duran = klasor_oku_dosya(repo, _ORTA_NOT)
    except ValueError:
        return _ORTA_NOT + " yok."
    govde = " | ".join(_not_satirlari(duran.get("text") or ""))
    return _ORTA_NOT + ": " + (govde or "boş") + "."


def _orta_not(repo: Path, metin: str) -> dict:
    satir = _not_satiri(metin)
    try:
        duran = klasor_oku_dosya(repo, _ORTA_NOT)
    except ValueError:
        klasor_yaz(repo, _ORTA_NOT, satir + "\n")
        return _paket(reply="Yazıldı: " + _ORTA_NOT + ".\nÇalıştırmadım.")
    govde = (duran.get("text") or "").strip()
    return _paket(reply="Orta not duruyor: " + govde + "\nÜstüne yazmadım. Çalıştırmadım.")


def _orta_not_oku(repo: Path) -> dict:
    try:
        duran = klasor_oku_dosya(repo, _ORTA_NOT)
    except ValueError:
        return _paket(reply=_ORTA_NOT + " yok.\nÇalıştırmadım.")
    govde = duran.get("text") or ""
    return _paket(
        reply=_ORTA_NOT + " okundu.\n" + (govde.strip() or "(boş)") + "\nÇalıştırmadım. Dosya aynı.",
        gorunum="kod",
        rel=duran["rel"],
        text=govde,
    )


def _orta_not_satir(repo: Path, metin: str) -> dict:
    satir = _not_satiri(metin)
    try:
        duran = klasor_oku_dosya(repo, _ORTA_NOT)
    except ValueError:
        return _paket(
            reply="Not yok. Şöyle söyle: orta notu yaz: " + satir + "\nÇalıştırmadım."
        )
    eski = duran.get("text") or ""
    satirlar = _not_satirlari(eski)
    if satir in satirlar:
        return _paket(reply="Bu satır duruyor: " + satir + "\nÜstüne yazmadım. Çalıştırmadım.")
    if len(satirlar) >= _ORTA_NOT_TAVAN:
        return _paket(reply="Not doldu. Üstüne yazmadım. Çalıştırmadım.")
    taban = eski if eski.endswith("\n") or eski == "" else eski + "\n"
    yeni = taban + satir + "\n"
    if not yeni.startswith(eski):
        raise ValueError("Üstüne yazmadım.")
    klasor_yaz(repo, _ORTA_NOT, yeni)
    okunan = klasor_oku_dosya(repo, _ORTA_NOT)
    if okunan.get("text") != yeni or not (okunan.get("text") or "").startswith(eski):
        raise ValueError("Yazılmadı. " + _ORTA_NOT)
    return _paket(
        reply="Satır eklendi: " + _ORTA_NOT + ".\n" + satir + "\nÇalıştırmadım.",
        gorunum="kod",
        rel=okunan["rel"],
        text=okunan["text"],
    )


def _arac_donusu(node: ast.AST | None) -> bool:
    if not isinstance(node, ast.Call) or node.keywords or len(node.args) != 1:
        return False
    if not isinstance(node.func, ast.Name) or node.func.id != "len":
        return False
    comp = node.args[0]
    if not isinstance(comp, ast.ListComp) or len(comp.generators) != 1:
        return False
    if not isinstance(comp.elt, ast.Name) or comp.elt.id != "satir":
        return False
    gen = comp.generators[0]
    if gen.is_async or len(gen.ifs) != 1 or not isinstance(gen.target, ast.Name) or gen.target.id != "satir":
        return False
    cagri = gen.iter
    if not isinstance(cagri, ast.Call) or cagri.args or cagri.keywords:
        return False
    if not isinstance(cagri.func, ast.Attribute) or cagri.func.attr != "splitlines":
        return False
    if not isinstance(cagri.func.value, ast.Name) or cagri.func.value.id != "metin":
        return False
    kond = gen.ifs[0]
    if not isinstance(kond, ast.Call) or kond.args or kond.keywords:
        return False
    if not isinstance(kond.func, ast.Attribute) or kond.func.attr != "strip":
        return False
    return isinstance(kond.func.value, ast.Name) and kond.func.value.id == "satir"


def _arac_hazir(agac: ast.AST) -> bool:
    if not isinstance(agac, ast.Module):
        return False
    govde = list(agac.body)
    if (
        govde
        and isinstance(govde[0], ast.Expr)
        and isinstance(govde[0].value, ast.Constant)
        and isinstance(govde[0].value.value, str)
    ):
        govde = govde[1:]
    if len(govde) != 1 or not isinstance(govde[0], ast.FunctionDef):
        return False
    fn = govde[0]
    args = fn.args
    if (
        fn.name != "satir_say"
        or fn.decorator_list
        or args.posonlyargs
        or args.kwonlyargs
        or args.vararg
        or args.kwarg
        or args.defaults
        or args.kw_defaults
        or len(args.args) != 1
        or args.args[0].arg != "metin"
    ):
        return False
    ic = list(fn.body)
    if (
        ic
        and isinstance(ic[0], ast.Expr)
        and isinstance(ic[0].value, ast.Constant)
        and isinstance(ic[0].value.value, str)
    ):
        ic = ic[1:]
    return len(ic) == 1 and isinstance(ic[0], ast.Return) and _arac_donusu(ic[0].value)


def _arac_ayni(yol: Path, once: bytes) -> bool:
    try:
        return yol.is_file() and not yol.is_symlink() and yol.read_bytes() == once
    except OSError:
        return False


def _orta_arac_calistir(repo: Path, metin: str) -> dict:
    try:
        yol, _norm = _klasor_hedef(repo, "orta/arac.py")
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply="orta/arac.py yok.\nÇalıştırmadım.")
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="orta/arac.py yok.\nÇalıştırmadım.")
    once = yol.read_bytes()
    try:
        agac = ast.parse(once.decode("utf-8"))
    except (UnicodeError, SyntaxError):
        return _paket(reply="Bunu çalıştırmadım. Hazır araç değil.\nDosya aynı.")
    if not _arac_hazir(agac):
        return _paket(reply="Bunu çalıştırmadım. Hazır araç değil.\nDosya aynı.")
    sonuc = None
    try:
        ns: dict = {}
        exec(compile(agac, "orta/arac.py", "exec"), {"__builtins__": {"len": len}}, ns)
        fn = ns.get("satir_say")
        if callable(fn):
            sonuc = fn(metin)
    except Exception:
        sonuc = None
    if not _arac_ayni(yol, once):
        return _paket(reply="Dosya değişti. Sayıyı söylemedim.")
    if type(sonuc) is not int:
        return _paket(reply="Çalışmadı.\nDosya aynı.")
    return _paket(reply="Sayı: " + str(sonuc) + "\norta/arac.py içinde satir_say bir kez çalıştı.\nDosya aynı.")


def _orta_arac_not(repo: Path) -> dict:
    try:
        arac, _norm = _klasor_hedef(repo, "orta/arac.py")
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply="orta/arac.py yok.\nÇalıştırmadım.")
    if not arac.is_file() or arac.is_symlink():
        return _paket(reply="orta/arac.py yok.\nÇalıştırmadım.")
    try:
        not_yol, _norm = _klasor_hedef(repo, _ORTA_NOT)
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply=_ORTA_NOT + " yok.\nÇalıştırmadım.")
    if not not_yol.is_file() or not_yol.is_symlink():
        return _paket(reply=_ORTA_NOT + " yok.\nÇalıştırmadım.")
    once = not_yol.read_bytes()
    paket = _orta_arac_calistir(repo, once.decode("utf-8"))
    if not _arac_ayni(not_yol, once):
        return _paket(reply="Not değişti. Sayıyı söylemedim.")
    return paket


def _orta_arac_satir(repo: Path, metin: str) -> dict:
    return _orta_arac_calistir(repo, _not_satiri(metin))


_ORTA_KONTROL = (
    ("selam", 1, "1. kontrol: selam"),
    ("selam\nikinci", 2, "2. kontrol: selam ve ikinci"),
    ("\n\n", 0, "3. kontrol: boş satır"),
)


def _kontrol_kaldi(fn) -> str:
    for metin, sayi, ad in _ORTA_KONTROL:
        try:
            gelen = fn(metin)
        except Exception:
            return ad + " kaldı. Çalışmadı."
        if type(gelen) is not int or gelen != sayi:
            gelen_yazi = str(gelen) if type(gelen) is int else "sayı değil"
            return ad + " kaldı. Beklenen " + str(sayi) + ", gelen " + gelen_yazi + "."
    return ""


def _orta_arac_yukle(repo: Path) -> tuple[Path, bytes, dict] | dict:
    try:
        yol, _norm = _klasor_hedef(repo, "orta/arac.py")
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply="orta/arac.py yok.\nÇalıştırmadım.")
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="orta/arac.py yok.\nÇalıştırmadım.")
    once = yol.read_bytes()
    try:
        agac = ast.parse(once.decode("utf-8"))
    except (UnicodeError, SyntaxError):
        return _paket(reply="Bunu çalıştırmadım. Hazır araç değil.\nDosya aynı. Düzeltmedim.")
    if not _arac_hazir(agac):
        return _paket(reply="Bunu çalıştırmadım. Hazır araç değil.\nDosya aynı. Düzeltmedim.")
    ns: dict = {}
    try:
        exec(compile(agac, "orta/arac.py", "exec"), {"__builtins__": {"len": len}}, ns)
    except Exception:
        ns = {}
    if not _arac_ayni(yol, once):
        return _paket(reply="Dosya değişti. Sonucu söylemedim. Düzeltmedim.")
    return yol, once, ns


def _orta_tur_baslat(repo: Path) -> dict:
    tur = _orta_tur_oku(repo)
    sonuc = _orta_test_neden(repo)
    cevap = str(sonuc.get("reply") or "")
    if "Üç kontrol de geçti." in cevap:
        _orta_tur_yaz(repo, {**tur, "durdu": "1", "kaldi": "0"})
        return _paket(reply="Üç kontrol de geçti. Tur durdu.\nDosya aynı. Düzeltmedim.")
    if "orta/arac.py yok." in cevap or "Dosya değişti" in cevap:
        return sonuc
    _orta_tur_yaz(repo, {"kaldi": "1"})
    return sonuc


def _orta_test_neden(repo: Path) -> dict:
    yuklu = _orta_arac_yukle(repo)
    if isinstance(yuklu, dict):
        cevap = str(yuklu.get("reply") or "")
        if "Hazır araç değil" in cevap:
            return _paket(reply="Hazır araç değil. Kontrol çalışmadı.\nDosya aynı. Düzeltmedim.")
        return yuklu
    yol, once, ns = yuklu
    fn = ns.get("satir_say")
    if not callable(fn):
        cevap = "Çalışmadı.\nDosya aynı. Düzeltmedim."
    else:
        kalan = _kontrol_kaldi(fn)
        if kalan:
            cevap = kalan + "\nDosya aynı. Düzeltmedim."
        else:
            cevap = "Üç kontrol de geçti.\nDosya aynı. Düzeltmedim."
    if not _arac_ayni(yol, once):
        return _paket(reply="Dosya değişti. Sonucu söylemedim. Düzeltmedim.")
    return _paket(reply=cevap)


_ARAC_SATIR = "return len([satir for satir in metin.splitlines() if satir.strip()])"


def _orta_tur_yolu(repo: Path) -> Path:
    kok = repo.resolve()
    ust = kok / "ilim-assistant" / ".ruzgar"
    hedef = ust / "orta_tur.txt"
    if ust.is_symlink() or hedef.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    gercek = hedef.resolve()
    if gercek.name != "orta_tur.txt" or not _icinde(gercek, kok):
        raise ValueError("Bu yere yazılmaz.")
    return gercek


_TUR_ANAHTAR = ("duzeltme", "bakis", "gecti", "durdu", "kaldi", "tur")


def _orta_tur_oku(repo: Path) -> dict[str, str]:
    veri = {anahtar: "0" for anahtar in _TUR_ANAHTAR}
    try:
        yol = _orta_tur_yolu(repo)
    except ValueError:
        return veri
    if not yol.is_file():
        return veri
    for satir in yol.read_text(encoding="utf-8").splitlines():
        if "=" not in satir:
            continue
        anahtar, deger = satir.split("=", 1)
        deger = deger.strip()
        if anahtar in veri and deger in {"0", "1"}:
            veri[anahtar] = deger
    return veri


def _orta_tur_yaz(repo: Path, veri: dict[str, str]) -> None:
    yol = _orta_tur_yolu(repo)
    yol.parent.mkdir(parents=True, exist_ok=True)
    govde = "".join(
        anahtar + "=" + ("1" if veri.get(anahtar) == "1" else "0") + "\n"
        for anahtar in _TUR_ANAHTAR
    )
    yol.write_text(govde, encoding="utf-8")


def _orta_tur_duzelt(repo: Path) -> dict:
    tur = _orta_tur_oku(repo)
    if tur.get("durdu") == "1":
        if _arac_sablon_duruyor(repo):
            return _paket(reply="Tur geçti. Yazmadım.\nDosya aynı. Çalıştırmadım.")
        return _paket(reply="Hazır araç değil. Yazmadım.\nDosya aynı. Çalıştırmadım.")
    if _arac_sablon_duruyor(repo):
        _orta_tur_yaz(repo, {**tur, "tur": "1", "duzeltme": "1", "kaldi": "0"})
        return _paket(
            reply="Bilinen satır duruyor: " + _ARAC_SATIR + "\nÜstüne yazmadım. Çalıştırmadım."
        )
    if tur.get("kaldi") != "1":
        return _paket(reply="Tur kalmadı. Yazmadım.\nDosya aynı. Çalıştırmadım.")
    sablon = _ORTA_DOSYA["orta/arac.py"]
    if _ARAC_SATIR not in sablon:
        return _paket(reply="Bilinen satır yok. Yazmadım.\nDosya aynı. Çalıştırmadım.")
    yol, _norm = _klasor_hedef(repo, "orta/arac.py")
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    klasor_yaz(repo, "orta/arac.py", sablon)
    okunan = klasor_oku_dosya(repo, "orta/arac.py")
    if okunan.get("text") != sablon:
        raise ValueError("Yazılmadı. orta/arac.py")
    _orta_tur_yaz(
        repo,
        {"tur": "1", "duzeltme": "1", "bakis": "0", "gecti": "0", "kaldi": "0", "durdu": "0"},
    )
    return _paket(
        reply="Yazıldı: orta/arac.py.\nBilinen satır: " + _ARAC_SATIR + "\nÇalıştırmadım."
    )


def _orta_tur_bak(repo: Path) -> dict:
    tur = _orta_tur_oku(repo)
    if (tur.get("tur") != "1" or tur.get("duzeltme") != "1") and not _arac_sablon_duruyor(repo):
        return _paket(reply="Düzeltme yok. Bakmadım.")
    tur = {**tur, "tur": "1", "duzeltme": "1"}
    if tur.get("bakis") == "1":
        return _paket(reply="İkinci bakış duruyor. Üçüncüye geçmedim.")
    sonuc = _orta_test(repo)
    cevap = str(sonuc.get("reply") or "")
    tur["bakis"] = "1"
    tur["gecti"] = "1" if "Test geçti." in cevap else "0"
    _orta_tur_yaz(repo, tur)
    return sonuc


def _orta_tur_kapat(repo: Path) -> dict:
    tur = _orta_tur_oku(repo)
    if tur.get("tur") != "1" or tur.get("gecti") != "1":
        return _paket(reply="Bakış geçmedi. Tahtaya yazmadım.")
    return _acik_satiri_bitti(repo)


def _arac_sablon_duruyor(repo: Path) -> bool:
    try:
        yol, _norm = _klasor_hedef(repo, "orta/arac.py")
    except ValueError:
        return False
    if not yol.is_file() or yol.is_symlink():
        return False
    try:
        return yol.read_text(encoding="utf-8") == _ORTA_DOSYA["orta/arac.py"]
    except OSError:
        return False


def _orta_tur_soyle(repo: Path) -> dict:
    tur = _orta_tur_oku(repo)
    if tur.get("durdu") == "1":
        simdi = "Şimdi: tur durdu."
    elif tur.get("bakis") == "1" and tur.get("gecti") == "1":
        simdi = "Şimdi: bakış geçti."
    elif tur.get("bakis") == "1":
        simdi = "Şimdi: bakış kaldı."
    elif tur.get("duzeltme") == "1":
        simdi = "Şimdi: düzeltildi, bakış yok."
    elif tur.get("kaldi") == "1":
        simdi = "Şimdi: tur kaldı, düzeltme yok."
    elif _arac_sablon_duruyor(repo):
        simdi = "Şimdi: dosya hazır, bakış yok."
    else:
        simdi = "Şimdi: tur yok."
    return _paket(
        reply=(
            "Sıra: orta turu başlat, orta turu düzelt, orta turu bak, orta turu kapat.\n"
            + simdi
            + "\nYazmadım. Tahtaya yazmadım."
        )
    )


_OLCU_REL = "orta/olcu.py"
_OLCU_SATIR = "return len([kelime for kelime in metin.split() if kelime.strip()])"
_OLCU_SABLON = '''"""Kelime sayar. Calistirilmaz; el yalniz okur."""


def kelime_say(metin):
    """Bos olmayan kelimeleri sayar."""
    return len([kelime for kelime in metin.split() if kelime.strip()])
'''
_OLCU_KONTROL = (
    ("selam", 1, "1. kontrol: selam"),
    ("selam ikinci", 2, "2. kontrol: selam ikinci"),
    ("  \n  ", 0, "3. kontrol: boş"),
)
_OLCU_ANAHTAR = ("kaldi", "durdu", "duzeltme", "bakis", "gecti", "kapandi")


def _olcu_donusu(node: ast.AST | None) -> bool:
    if not isinstance(node, ast.Call) or node.keywords or len(node.args) != 1:
        return False
    if not isinstance(node.func, ast.Name) or node.func.id != "len":
        return False
    comp = node.args[0]
    if not isinstance(comp, ast.ListComp) or len(comp.generators) != 1:
        return False
    if not isinstance(comp.elt, ast.Name) or comp.elt.id != "kelime":
        return False
    gen = comp.generators[0]
    if gen.is_async or len(gen.ifs) != 1 or not isinstance(gen.target, ast.Name) or gen.target.id != "kelime":
        return False
    cagri = gen.iter
    if not isinstance(cagri, ast.Call) or cagri.args or cagri.keywords:
        return False
    if not isinstance(cagri.func, ast.Attribute) or cagri.func.attr != "split":
        return False
    if not isinstance(cagri.func.value, ast.Name) or cagri.func.value.id != "metin":
        return False
    kond = gen.ifs[0]
    if not isinstance(kond, ast.Call) or kond.args or kond.keywords:
        return False
    if not isinstance(kond.func, ast.Attribute) or kond.func.attr != "strip":
        return False
    return isinstance(kond.func.value, ast.Name) and kond.func.value.id == "kelime"


def _olcu_hazir(agac: ast.AST) -> bool:
    if not isinstance(agac, ast.Module):
        return False
    govde = list(agac.body)
    if (
        govde
        and isinstance(govde[0], ast.Expr)
        and isinstance(govde[0].value, ast.Constant)
        and isinstance(govde[0].value.value, str)
    ):
        govde = govde[1:]
    if len(govde) != 1 or not isinstance(govde[0], ast.FunctionDef):
        return False
    fn = govde[0]
    args = fn.args
    if (
        fn.name != "kelime_say"
        or fn.decorator_list
        or args.posonlyargs
        or args.kwonlyargs
        or args.vararg
        or args.kwarg
        or args.defaults
        or args.kw_defaults
        or len(args.args) != 1
        or args.args[0].arg != "metin"
    ):
        return False
    ic = list(fn.body)
    if (
        ic
        and isinstance(ic[0], ast.Expr)
        and isinstance(ic[0].value, ast.Constant)
        and isinstance(ic[0].value.value, str)
    ):
        ic = ic[1:]
    return len(ic) == 1 and isinstance(ic[0], ast.Return) and _olcu_donusu(ic[0].value)


def _olcu_tur_yolu(repo: Path) -> Path:
    kok = repo.resolve()
    ust = kok / "ilim-assistant" / ".ruzgar"
    hedef = ust / "olcu_tur.txt"
    if ust.is_symlink() or hedef.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    gercek = hedef.resolve()
    if gercek.name != "olcu_tur.txt" or not _icinde(gercek, kok):
        raise ValueError("Bu yere yazılmaz.")
    return gercek


def _olcu_tur_oku(repo: Path) -> dict[str, str]:
    veri = {anahtar: "0" for anahtar in _OLCU_ANAHTAR}
    try:
        yol = _olcu_tur_yolu(repo)
    except ValueError:
        return veri
    if not yol.is_file():
        return veri
    for satir in yol.read_text(encoding="utf-8").splitlines():
        if "=" not in satir:
            continue
        anahtar, deger = satir.split("=", 1)
        deger = deger.strip()
        if anahtar in veri and deger in {"0", "1"}:
            veri[anahtar] = deger
    return veri


def _olcu_tur_yaz(repo: Path, veri: dict[str, str]) -> None:
    yol = _olcu_tur_yolu(repo)
    yol.parent.mkdir(parents=True, exist_ok=True)
    govde = "".join(
        anahtar + "=" + ("1" if veri.get(anahtar) == "1" else "0") + "\n"
        for anahtar in _OLCU_ANAHTAR
    )
    yol.write_text(govde, encoding="utf-8")


def _olcu_yukle(repo: Path) -> tuple[Path, bytes, dict] | dict:
    try:
        yol, _norm = _klasor_hedef(repo, _OLCU_REL)
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply=_OLCU_REL + " yok.\nÇalıştırmadım.")
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply=_OLCU_REL + " yok.\nÇalıştırmadım.")
    once = yol.read_bytes()
    try:
        agac = ast.parse(once.decode("utf-8"))
    except (UnicodeError, SyntaxError):
        return _paket(reply="Bunu çalıştırmadım. Hazır ölçü değil.\nDosya aynı.")
    if not _olcu_hazir(agac):
        return _paket(reply="Bunu çalıştırmadım. Hazır ölçü değil.\nDosya aynı.")
    ns: dict = {}
    try:
        exec(compile(agac, _OLCU_REL, "exec"), {"__builtins__": {"len": len}}, ns)
    except Exception:
        ns = {}
    if not _arac_ayni(yol, once):
        return _paket(reply="Dosya değişti. Sonucu söylemedim.")
    return yol, once, ns


def _olcu_soyle(repo: Path) -> dict:
    try:
        yol, _norm = _klasor_hedef(repo, _OLCU_REL)
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply=_OLCU_REL + " yok.\nYazmadım. Çalıştırmadım.")
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply=_OLCU_REL + " yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    try:
        agac = ast.parse(once.decode("utf-8"))
        hazir = _olcu_hazir(agac)
    except (UnicodeError, SyntaxError):
        hazir = False
    if not _arac_ayni(yol, once):
        return _paket(reply="Dosya değişti. Söylemedim.")
    if not hazir:
        return _paket(reply="Hazır ölçü değil.\nDosya aynı. Yazmadım. Çalıştırmadım.")
    return _paket(
        reply=(
            _OLCU_REL
            + " içinde kelime_say.\nBilinen satır: "
            + _OLCU_SATIR
            + "\nYazmadım. Çalıştırmadım."
        )
    )


def _olcu_say(repo: Path, metin: str) -> dict:
    yuklu = _olcu_yukle(repo)
    if isinstance(yuklu, dict):
        return yuklu
    yol, once, ns = yuklu
    fn = ns.get("kelime_say")
    sonuc = None
    if callable(fn):
        try:
            sonuc = fn(metin)
        except Exception:
            sonuc = None
    if not _arac_ayni(yol, once):
        return _paket(reply="Dosya değişti. Sayıyı söylemedim.")
    if type(sonuc) is not int:
        return _paket(reply="Çalışmadı.\nDosya aynı.")
    return _paket(
        reply="Sayı: " + str(sonuc) + "\n" + _OLCU_REL + " içinde kelime_say bir kez çalıştı.\nDosya aynı."
    )


def _olcu_say_not(repo: Path) -> dict:
    try:
        not_yol, _norm = _klasor_hedef(repo, _ORTA_NOT)
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply=_ORTA_NOT + " yok.\nÇalıştırmadım.")
    if not not_yol.is_file() or not_yol.is_symlink():
        return _paket(reply=_ORTA_NOT + " yok.\nÇalıştırmadım.")
    once = not_yol.read_bytes()
    paket = _olcu_say(repo, once.decode("utf-8"))
    if not _arac_ayni(not_yol, once):
        return _paket(reply="Not değişti. Sayıyı söylemedim.")
    return paket


def _olcu_neden(repo: Path) -> dict:
    tur = _olcu_tur_oku(repo)
    yuklu = _olcu_yukle(repo)
    if isinstance(yuklu, dict):
        cevap = str(yuklu.get("reply") or "")
        if _OLCU_REL + " yok." in cevap or "Hazır ölçü değil" in cevap:
            _olcu_tur_yaz(repo, {"kaldi": "1", "durdu": "0"})
            if "Hazır ölçü değil" in cevap:
                return _paket(reply="Hazır ölçü değil. Kontrol çalışmadı.\nDosya aynı. Düzeltmedim.")
            return _paket(reply=_OLCU_REL + " yok.\nKontrol çalışmadı.\nYazmadım.")
        return yuklu
    yol, once, ns = yuklu
    fn = ns.get("kelime_say")
    if not callable(fn):
        cevap = "Çalışmadı.\nDosya aynı. Düzeltmedim."
        kaldi = "1"
        durdu = "0"
        gecti = False
    else:
        kalan = ""
        for metin, sayi, ad in _OLCU_KONTROL:
            try:
                gelen = fn(metin)
            except Exception:
                kalan = ad + " kaldı. Çalışmadı."
                break
            if type(gelen) is not int or gelen != sayi:
                gelen_yazi = str(gelen) if type(gelen) is int else "sayı değil"
                kalan = ad + " kaldı. Beklenen " + str(sayi) + ", gelen " + gelen_yazi + "."
                break
        if kalan:
            cevap = kalan + "\nDosya aynı. Düzeltmedim."
            kaldi = "1"
            durdu = "0"
            gecti = False
        else:
            cevap = "Üç kontrol de geçti.\nDosya aynı. Düzeltmedim."
            kaldi = "0"
            durdu = "1"
            gecti = True
    if not _arac_ayni(yol, once):
        return _paket(reply="Dosya değişti. Sonucu söylemedim. Düzeltmedim.")
    if gecti:
        _olcu_tur_yaz(repo, {**tur, "kaldi": kaldi, "durdu": durdu})
    else:
        _olcu_tur_yaz(repo, {"kaldi": kaldi, "durdu": durdu})
    return _paket(reply=cevap)


def _olcu_duzelt(repo: Path) -> dict:
    tur = _olcu_tur_oku(repo)
    if tur.get("durdu") == "1":
        if _olcu_sablon_duruyor(repo):
            return _paket(reply="Ölçü geçti. Yazmadım.\nDosya aynı. Çalıştırmadım.")
        return _paket(reply="Hazır ölçü değil. Yazmadım.\nDosya aynı. Çalıştırmadım.")
    if _olcu_sablon_duruyor(repo):
        _olcu_tur_yaz(repo, {**tur, "duzeltme": "1", "kaldi": "0"})
        return _paket(reply="Bilinen satır duruyor: " + _OLCU_SATIR + "\nÜstüne yazmadım. Çalıştırmadım.")
    if tur.get("kaldi") != "1":
        return _paket(reply="Ölçü kalmadı. Yazmadım.\nDosya aynı. Çalıştırmadım.")
    if _OLCU_SATIR not in _OLCU_SABLON:
        return _paket(reply="Bilinen satır yok. Yazmadım.\nDosya aynı. Çalıştırmadım.")
    yol, _norm = _klasor_hedef(repo, _OLCU_REL)
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    klasor_yaz(repo, _OLCU_REL, _OLCU_SABLON)
    okunan = klasor_oku_dosya(repo, _OLCU_REL)
    if okunan.get("text") != _OLCU_SABLON:
        raise ValueError("Yazılmadı. orta/olcu.py")
    _olcu_tur_yaz(repo, {**tur, "duzeltme": "1", "kaldi": "0"})
    return _paket(reply="Yazıldı: " + _OLCU_REL + ".\nBilinen satır: " + _OLCU_SATIR + "\nÇalıştırmadım.")


def _olcu_sablon_duruyor(repo: Path) -> bool:
    try:
        yol, _norm = _klasor_hedef(repo, _OLCU_REL)
    except ValueError:
        return False
    if not yol.is_file() or yol.is_symlink():
        return False
    try:
        return yol.read_text(encoding="utf-8") == _OLCU_SABLON
    except OSError:
        return False


def _olcu_bak(repo: Path) -> dict:
    tur = _olcu_tur_oku(repo)
    if tur.get("duzeltme") != "1" and not _olcu_sablon_duruyor(repo):
        return _paket(reply="Düzeltme yok. Bakmadım.")
    tur = {**tur, "duzeltme": "1"}
    if tur.get("bakis") == "1":
        return _paket(reply="İkinci bakış duruyor. Üçüncüye geçmedim.")
    yuklu = _olcu_yukle(repo)
    if isinstance(yuklu, dict):
        cevap = str(yuklu.get("reply") or "")
        gecti = "0"
    else:
        yol, once, ns = yuklu
        fn = ns.get("kelime_say")
        kalan = ""
        if not callable(fn):
            kalan = "Çalışmadı."
        else:
            for metin, sayi, ad in _OLCU_KONTROL:
                try:
                    gelen = fn(metin)
                except Exception:
                    kalan = ad + " kaldı. Çalışmadı."
                    break
                if type(gelen) is not int or gelen != sayi:
                    gelen_yazi = str(gelen) if type(gelen) is int else "sayı değil"
                    kalan = ad + " kaldı. Beklenen " + str(sayi) + ", gelen " + gelen_yazi + "."
                    break
        if not _arac_ayni(yol, once):
            return _paket(reply="Dosya değişti. Sonucu söylemedim. Düzeltmedim.")
        if kalan:
            cevap = kalan + "\nDosya aynı. Düzeltmedim."
            gecti = "0"
        else:
            cevap = "Üç kontrol de geçti.\nDosya aynı. Düzeltmedim."
            gecti = "1"
    _olcu_tur_yaz(repo, {**tur, "duzeltme": "1", "bakis": "1", "gecti": gecti})
    return _paket(reply=cevap)


def _olcu_kapat(repo: Path) -> dict:
    tur = _olcu_tur_oku(repo)
    if tur.get("bakis") != "1" or tur.get("gecti") != "1":
        return _paket(reply="Bakış geçmedi. Tahtaya yazmadım.")
    _olcu_tur_yaz(repo, {**tur, "kapandi": "1"})
    tahta = _tahta_tek_satiri_bitti(repo)
    return _paket(reply="Ölçü kapandı.\n" + str(tahta.get("reply") or ""))


def _olcu_test(repo: Path) -> dict:
    yuklu = _olcu_yukle(repo)
    if isinstance(yuklu, dict):
        cevap = str(yuklu.get("reply") or "")
        if _OLCU_REL + " yok." in cevap:
            return _paket(reply=_OLCU_REL + " yok.\nÇalıştırmadım.")
        if "Hazır ölçü değil" in cevap:
            return _paket(reply="Bunu çalıştırmadım. Hazır ölçü değil.\nDosya aynı. Düzeltmedim.")
        return yuklu
    yol, once, ns = yuklu
    fn = ns.get("kelime_say")
    kaldi = not callable(fn)
    if not kaldi:
        for metin, sayi, _ad in _OLCU_KONTROL:
            try:
                gelen = fn(metin)
            except Exception:
                kaldi = True
                break
            if type(gelen) is not int or gelen != sayi:
                kaldi = True
                break
    if not _arac_ayni(yol, once):
        return _paket(reply="Dosya değişti. Sonucu söylemedim. Düzeltmedim.")
    if kaldi:
        return _paket(reply="Test kaldı.\nDosya aynı. Düzeltmedim.")
    return _paket(reply="Test geçti.\nDosya aynı. Düzeltmedim.")


def _olcu_sira(repo: Path) -> dict:
    tur = _olcu_tur_oku(repo)
    if tur.get("kapandi") == "1":
        simdi = "Şimdi: ölçü kapandı."
    elif tur.get("bakis") == "1" and tur.get("gecti") == "1":
        simdi = "Şimdi: bakış geçti."
    elif tur.get("bakis") == "1":
        simdi = "Şimdi: bakış kaldı."
    elif tur.get("duzeltme") == "1":
        simdi = "Şimdi: düzeltildi, bakış yok."
    elif tur.get("kaldi") == "1":
        simdi = "Şimdi: ölçü kaldı, düzeltme yok."
    elif tur.get("durdu") == "1":
        simdi = "Şimdi: ölçü durdu."
    elif _olcu_sablon_duruyor(repo):
        simdi = "Şimdi: dosya hazır, bakış yok."
    else:
        simdi = "Şimdi: ölçü yok."
    return _paket(
        reply=(
            "Sıra: orta ölçüsü neden kaldı, orta ölçüsünü düzelt, orta ölçüsüne bak, orta ölçüsünü kapat.\n"
            + simdi
            + "\nYazmadım. Tahtaya yazmadım."
        )
    )


def _olcu_notu_yolu(repo: Path) -> Path:
    kok = repo.resolve()
    ust = kok / "ilim-assistant" / "ilim_assistant"
    hedef = ust / "olcu_notu.py"
    if ust.is_symlink() or hedef.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    gercek = hedef.resolve()
    if gercek.name != "olcu_notu.py" or not _icinde(gercek, kok):
        raise ValueError("Bu yere yazılmaz.")
    return gercek


def _olcu_notu_govde() -> str:
    return '"""Ölçü notu. Çalıştırılmaz."""\n\nSATIR = "' + _OLCU_SATIR + '"\n'


def _olcu_satir_soyle(repo: Path) -> dict:
    yol = _olcu_notu_yolu(repo)
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="ilim-assistant/ilim_assistant/olcu_notu.py yok.\nYazmadım. Çalıştırmadım.")
    govde = yol.read_text(encoding="utf-8")
    return _paket(reply="Ölçü satırı okundu.\n" + govde.strip() + "\nYazmadım. Çalıştırmadım.")


def _olcu_satir_yaz(repo: Path) -> dict:
    yol = _olcu_notu_yolu(repo)
    if yol.is_file():
        return _paket(
            reply="Ölçü satırı duruyor.\n" + yol.read_text(encoding="utf-8").strip() + "\nÜstüne yazmadım. Çalıştırmadım."
        )
    govde = _olcu_notu_govde()
    if _OLCU_SATIR not in govde:
        return _paket(reply="Bilinen satır yok. Yazmadım.\nÇalıştırmadım.")
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(govde, encoding="utf-8")
    if yol.read_text(encoding="utf-8") != govde:
        raise ValueError("Yazılmadı. olcu_notu.py")
    return _paket(reply="Yazıldı: ilim-assistant/ilim_assistant/olcu_notu.py.\nBilinen satır: " + _OLCU_SATIR + "\nÇalıştırmadım.")


def _orta_arac_duzelt_eksik(repo: Path) -> dict:
    return _paket(
        reply=(
            "Satır yok. Şöyle söyle: orta aracını düzelt: "
            + _ARAC_SATIR
            + "\nDosya aynı. Çalıştırmadım."
        )
    )


def _orta_arac_duzelt(repo: Path, metin: str) -> dict:
    satir = _not_satiri(metin)
    if satir != _ARAC_SATIR:
        return _paket(reply="Bu satır yazılmaz.\nDosya aynı. Çalıştırmadım.")
    sablon = _ORTA_DOSYA["orta/arac.py"]
    yol, _norm = _klasor_hedef(repo, "orta/arac.py")
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if yol.is_file() and yol.read_text(encoding="utf-8") == sablon:
        return _paket(reply="Bu satır duruyor.\nÜstüne yazmadım. Çalıştırmadım.")
    klasor_yaz(repo, "orta/arac.py", sablon)
    okunan = klasor_oku_dosya(repo, "orta/arac.py")
    if okunan.get("text") != sablon:
        raise ValueError("Yazılmadı. orta/arac.py")
    _orta_tur_yaz(repo, {"duzeltme": "1", "bakis": "0", "gecti": "0"})
    return _paket(reply="Yazıldı: orta/arac.py.\nÇalıştırmadım.")


_TAHTA_SATIR = re.compile(r"^(\|\s*\d+\s*\|[^|]*\|)\s*([^|\n]*?)\s*(\|.*)$")


def _tahta_yolu(repo: Path) -> Path:
    kok = repo.resolve()
    hedef = kok / "RUZGAR_SIRA.md"
    if hedef.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    gercek = hedef.resolve()
    if gercek.name != "RUZGAR_SIRA.md" or not _icinde(gercek, kok):
        raise ValueError("Bu yere yazılmaz.")
    return gercek


def _acik_satiri_bitti(repo: Path) -> dict:
    if _orta_tur_oku(repo).get("gecti") != "1":
        return _paket(reply="Test geçmedi. Tahtaya yazmadım.")
    return _tahta_tek_satiri_bitti(repo)


def _tahta_acik_say(repo: Path) -> dict:
    yol = _tahta_yolu(repo)
    if not yol.is_file():
        return _paket(reply="Tahta yok.\nYazmadım.")
    once = yol.read_bytes()
    adet = 0
    for satir in once.decode("utf-8").splitlines():
        bulunan = _TAHTA_SATIR.match(satir)
        if bulunan and bulunan.group(2).strip().lower() != "bitti":
            adet += 1
    if yol.read_bytes() != once:
        return _paket(reply="Tahta değişti. Sayıyı söylemedim.")
    return _paket(reply="Açık satır: " + str(adet) + "\nYazmadım. Tahtaya yazmadım.")


def _tahta_bitti_say(repo: Path) -> dict:
    yol = _tahta_yolu(repo)
    if not yol.is_file():
        return _paket(reply="Tahta yok.\nYazmadım.")
    once = yol.read_bytes()
    adet = 0
    for satir in once.decode("utf-8").splitlines():
        bulunan = _TAHTA_SATIR.match(satir)
        if bulunan and bulunan.group(2).strip().lower() == "bitti":
            adet += 1
    if yol.read_bytes() != once:
        return _paket(reply="Tahta değişti. Sayıyı söylemedim.")
    return _paket(reply="Bitti satır: " + str(adet) + "\nYazmadım. Tahtaya yazmadım.")


def _kilit_soyle(repo: Path) -> dict:
    try:
        yol = _kilit_yolu(repo)
    except _KlasorYok:
        raise ValueError("Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol") from None
    return _paket(reply="Kilitli klasör: " + yol + "\nYazmadım. Çalıştırmadım.")


def _tahta_tek_satiri_bitti(repo: Path) -> dict:
    yol = _tahta_yolu(repo)
    if not yol.is_file():
        return _paket(reply="Tahta yok. Tahtaya yazmadım.")
    metin = yol.read_text(encoding="utf-8")
    satirlar = metin.splitlines()
    acik: list[int] = []
    for i, satir in enumerate(satirlar):
        bulunan = _TAHTA_SATIR.match(satir)
        if bulunan and bulunan.group(2).strip().lower() != "bitti":
            acik.append(i)
    if not acik:
        return _paket(reply="Açık satır yok. Tahtaya yazmadım.")
    if len(acik) > 1:
        return _paket(reply="Birden fazla açık satır var. Tahtaya yazmadım.")
    yer = acik[0]
    bulunan = _TAHTA_SATIR.match(satirlar[yer])
    if not bulunan:
        return _paket(reply="Açık satır yok. Tahtaya yazmadım.")
    yeni = bulunan.group(1) + " bitti " + bulunan.group(3)
    if yeni == satirlar[yer]:
        return _paket(reply="Açık satır yok. Tahtaya yazmadım.")
    onceki = list(satirlar)
    satirlar[yer] = yeni
    if len(satirlar) != len(onceki):
        return _paket(reply="Tahtaya yazmadım.")
    for i, (eski, guncel) in enumerate(zip(onceki, satirlar)):
        if i != yer and eski != guncel:
            return _paket(reply="Tahtaya yazmadım.")
    son = "\n".join(satirlar)
    if metin.endswith("\n"):
        son += "\n"
    yol.write_text(son, encoding="utf-8")
    if yol.read_text(encoding="utf-8").splitlines() != satirlar:
        raise ValueError("Yazılmadı. RUZGAR_SIRA.md")
    return _paket(reply="Açık satır bitti oldu.\nBaşka satır silinmedi. Satır eklenmedi.")


def _orta_ikinci_bak(repo: Path) -> dict:
    tur = _orta_tur_oku(repo)
    if tur.get("duzeltme") != "1":
        return _paket(reply="Düzeltme yok. İkinci bakışa geçmedim.")
    if tur.get("bakis") == "1":
        return _paket(reply="İkinci bakış duruyor. Üçüncüye geçmedim.")
    sonuc = _orta_test(repo)
    cevap = str(sonuc.get("reply") or "")
    tur["bakis"] = "1"
    tur["gecti"] = "1" if "Test geçti." in cevap else "0"
    _orta_tur_yaz(repo, tur)
    return sonuc


def _orta_test(repo: Path) -> dict:
    import subprocess
    import sys

    try:
        yol, _norm = _klasor_hedef(repo, "orta/arac.py")
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply="orta/arac.py yok.\nÇalıştırmadım.")
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="orta/arac.py yok.\nÇalıştırmadım.")
    once = yol.read_bytes()
    try:
        agac = ast.parse(once.decode("utf-8"))
    except (UnicodeError, SyntaxError):
        return _paket(reply="Bunu çalıştırmadım. Hazır araç değil.\nDosya aynı. Düzeltmedim.")
    if not _arac_hazir(agac):
        return _paket(reply="Bunu çalıştırmadım. Hazır araç değil.\nDosya aynı. Düzeltmedim.")
    kod = (
        "import pathlib,sys\n"
        "src=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')\n"
        "ns={}\n"
        "exec(compile(src,'orta/arac.py','exec'),{'__builtins__':{'len':len}},ns)\n"
        "fn=ns.get('satir_say')\n"
        "beklenen=[('selam',1),('selam\\nikinci',2),('\\n\\n',0)]\n"
        "for metin,sayi in beklenen:\n"
        "    gelen=fn(metin)\n"
        "    if type(gelen) is not int or gelen!=sayi:\n"
        "        print('KALDI')\n"
        "        raise SystemExit(0)\n"
        "print('GECTI')\n"
    )
    try:
        sonuc = subprocess.run(
            [sys.executable, "-c", kod, str(yol)],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        sonuc = None
    if not _arac_ayni(yol, once):
        return _paket(reply="Dosya değişti. Sonucu söylemedim. Düzeltmedim.")
    cikti = "" if sonuc is None else (sonuc.stdout or "").strip()
    if cikti == "GECTI":
        return _paket(reply="Test geçti.\nDosya aynı. Düzeltmedim.")
    if cikti == "KALDI":
        return _paket(reply="Test kaldı.\nDosya aynı. Düzeltmedim.")
    return _paket(reply="Çalışmadı.\nDosya aynı. Düzeltmedim.")


def _uygulama_not_yolu(repo: Path) -> Path:
    kok = repo.resolve()
    ust = kok / "ilim-assistant" / ".ruzgar"
    hedef = ust / "uygulama_notu.txt"
    if ust.is_symlink() or hedef.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    gercek = hedef.resolve()
    if gercek.name != "uygulama_notu.txt" or not _icinde(gercek, kok):
        raise ValueError("Bu yere yazılmaz.")
    return gercek


def _uygulama_not(repo: Path, metin: str) -> dict:
    satir = _not_satiri(metin)
    yol = _uygulama_not_yolu(repo)
    if yol.is_file():
        govde = yol.read_text(encoding="utf-8").strip()
        return _paket(reply="Uygulama notu duruyor: " + govde + "\nÜstüne yazmadım. Çalıştırmadım.")
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(satir + "\n", encoding="utf-8")
    okunan = yol.read_text(encoding="utf-8")
    if okunan != satir + "\n":
        raise ValueError("Yazılmadı. uygulama notu")
    return _paket(reply="Yazıldı: ilim-assistant/.ruzgar/uygulama_notu.txt.\nÇalıştırmadım.")


def _uygulama_not_oku(repo: Path) -> dict:
    yol = _uygulama_not_yolu(repo)
    if not yol.is_file():
        return _paket(reply="ilim-assistant/.ruzgar/uygulama_notu.txt yok.\nÇalıştırmadım.")
    govde = yol.read_text(encoding="utf-8")
    return _paket(
        reply="Uygulama notu okundu.\n" + (govde.strip() or "(boş)") + "\nÇalıştırmadım. Dosya aynı.",
        gorunum="kod",
        rel="ilim-assistant/.ruzgar/uygulama_notu.txt",
        text=govde,
    )


def _uygulama_not_say(repo: Path) -> dict:
    yol = _uygulama_not_yolu(repo)
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="Not yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    adet = len([satir for satir in once.decode("utf-8").splitlines() if satir.strip()])
    if yol.read_bytes() != once:
        return _paket(reply="Not değişti. Sayıyı söylemedim.")
    return _paket(reply="Satır: " + str(adet) + "\nYazmadım. Çalıştırmadım.")


def _uygulama_not_son(repo: Path) -> dict:
    yol = _uygulama_not_yolu(repo)
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="Not yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    satirlar = [satir for satir in once.decode("utf-8").splitlines() if satir.strip()]
    if yol.read_bytes() != once:
        return _paket(reply="Not değişti. Söylemedim.")
    if not satirlar:
        return _paket(reply="Son satır yok.\nYazmadım. Çalıştırmadım.")
    return _paket(reply="Son satır: " + satirlar[-1] + "\nYazmadım. Çalıştırmadım.")


def _kilit_dosya_satir(repo: Path, rel: str) -> dict:
    try:
        yol, _norm = _klasor_hedef(repo, rel)
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply=rel + " yok.\nYazmadım. Çalıştırmadım.")
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply=rel + " yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    try:
        adet = len(once.decode("utf-8").splitlines())
    except UnicodeError:
        return _paket(reply="Satır okunmadı.\nDosya aynı. Yazmadım.")
    if yol.read_bytes() != once:
        return _paket(reply="Dosya değişti. Sayıyı söylemedim.")
    return _paket(reply="Satır: " + str(adet) + "\n" + rel + "\nYazmadım. Çalıştırmadım.")


def _not_var(yol: Path, ad: str) -> dict:
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if yol.is_file():
        return _paket(reply=ad + " var.\nYazmadım. Çalıştırmadım.")
    return _paket(reply=ad + " yok.\nYazmadım. Çalıştırmadım.")


def _hazir_ikisi(repo: Path) -> dict:
    arac = _arac_sablon_duruyor(repo)
    olcu = _olcu_sablon_duruyor(repo)
    if arac and olcu:
        govde = "İkisi hazır.\norta/arac.py satir_say.\norta/olcu.py kelime_say."
    elif arac:
        govde = "Araç hazır. Ölçü yok."
    elif olcu:
        govde = "Ölçü hazır. Araç yok."
    else:
        govde = "İkisi de yok."
    return _paket(reply=govde + "\nYazmadım. Çalıştırmadım.")


def _uygulama_not_ilk(repo: Path) -> dict:
    yol = _uygulama_not_yolu(repo)
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="Not yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    satirlar = [satir for satir in once.decode("utf-8").splitlines() if satir.strip()]
    if yol.read_bytes() != once:
        return _paket(reply="Not değişti. Söylemedim.")
    if not satirlar:
        return _paket(reply="İlk satır yok.\nYazmadım. Çalıştırmadım.")
    return _paket(reply="İlk satır: " + satirlar[0] + "\nYazmadım. Çalıştırmadım.")


def _klasor_var(repo: Path, rel: str, ad: str) -> dict:
    try:
        yol, _norm = _klasor_hedef(repo, rel)
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply=ad + " yok.\nYazmadım. Çalıştırmadım.")
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if yol.is_dir():
        raise ValueError("Bu yer dosya değil.")
    if yol.is_file():
        return _paket(reply=ad + " var.\nYazmadım. Çalıştırmadım.")
    return _paket(reply=ad + " yok.\nYazmadım. Çalıştırmadım.")


def _repo_satir(yol: Path, ad: str) -> dict:
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if not yol.is_file():
        return _paket(reply=ad + " yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    try:
        adet = len(once.decode("utf-8").splitlines())
    except UnicodeError:
        return _paket(reply="Satır okunmadı.\nDosya aynı. Yazmadım.")
    if yol.read_bytes() != once:
        return _paket(reply="Dosya değişti. Sayıyı söylemedim.")
    return _paket(reply="Satır: " + str(adet) + "\n" + ad + "\nYazmadım. Çalıştırmadım.")


def _tahta_satir_say(repo: Path) -> dict:
    yol = _tahta_yolu(repo)
    if not yol.is_file():
        return _paket(reply="Tahta yok.\nYazmadım.")
    once = yol.read_bytes()
    adet = sum(1 for satir in once.decode("utf-8").splitlines() if _TAHTA_SATIR.match(satir))
    if yol.read_bytes() != once:
        return _paket(reply="Tahta değişti. Sayıyı söylemedim.")
    return _paket(reply="Tahta satır: " + str(adet) + "\nYazmadım. Tahtaya yazmadım.")


def _kilit_adet(repo: Path) -> dict:
    try:
        kok = Path(_kilit_yolu(repo))
    except _KlasorYok:
        raise ValueError("Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol") from None
    adet = 0
    for path in kok.iterdir():
        if path.name.startswith(".") or path.is_symlink():
            continue
        if path.name in {"__pycache__", "node_modules", ".git"}:
            continue
        adet += 1
        if adet >= 200:
            break
    yazi = "Sayı: 200 ve fazlası." if adet >= 200 else "Sayı: " + str(adet) + "."
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _hazir_soyle(duruyor: bool, hazir: str) -> dict:
    govde = hazir if duruyor else "Ölçü yok."
    return _paket(reply=govde + "\nYazmadım. Çalıştırmadım.")


def _hazir_bilinen(repo: Path, rel: str, duruyor: bool, bilinen: str, degil: str) -> dict:
    try:
        yol, _norm = _klasor_hedef(repo, rel)
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply=rel + " yok.\nYazmadım. Çalıştırmadım.")
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if not yol.is_file():
        return _paket(reply=rel + " yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    if yol.read_bytes() != once:
        return _paket(reply="Dosya değişti. Söylemedim.")
    if duruyor:
        return _paket(reply="Satır: " + bilinen + "\nYazmadım. Çalıştırmadım.")
    return _paket(reply=degil + "\nYazmadım. Çalıştırmadım.")


def _bayrak_bir(repo: Path, yol_fn, oku_fn) -> dict:
    try:
        yol = yol_fn(repo)
    except ValueError:
        return _paket(reply="Kayıt dosyası yok.\nYazmadım. Çalıştırmadım.")
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if not yol.is_file():
        return _paket(reply="Kayıt dosyası yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    tur = oku_fn(repo)
    if yol.read_bytes() != once:
        return _paket(reply="Kayıt değişti. Söylemedim.")
    return _paket(reply="Bakış: " + tur.get("bakis", "0") + "\nYazmadım. Çalıştırmadım.")


def _olcu_kapandi_soyle(repo: Path) -> dict:
    try:
        yol = _olcu_tur_yolu(repo)
    except ValueError:
        return _paket(reply="Kayıt dosyası yok.\nYazmadım. Çalıştırmadım.")
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if not yol.is_file():
        return _paket(reply="Kayıt dosyası yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    tur = _olcu_tur_oku(repo)
    if yol.read_bytes() != once:
        return _paket(reply="Kayıt değişti. Söylemedim.")
    yazi = "Kapandı." if tur.get("kapandi") == "1" else "Açık."
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _kayit_tur(repo: Path, yol_fn, oku_fn):
    try:
        yol = yol_fn(repo)
    except ValueError:
        return _paket(reply="Kayıt dosyası yok.\nYazmadım. Çalıştırmadım.")
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if not yol.is_file():
        return _paket(reply="Kayıt dosyası yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    tur = oku_fn(repo)
    if yol.read_bytes() != once:
        return _paket(reply="Kayıt değişti. Söylemedim.")
    return tur


def _bayrak_etiket(repo: Path, yol_fn, oku_fn, anahtar: str, etiket: str) -> dict:
    tur = _kayit_tur(repo, yol_fn, oku_fn)
    if isinstance(tur, dict) and "reply" in tur:
        return tur
    return _paket(reply=etiket + ": " + tur.get(anahtar, "0") + "\nYazmadım. Çalıştırmadım.")


def _bayrak_evet(repo: Path, yol_fn, oku_fn, anahtar: str, evet: str, hayir: str) -> dict:
    tur = _kayit_tur(repo, yol_fn, oku_fn)
    if isinstance(tur, dict) and "reply" in tur:
        return tur
    yazi = evet if tur.get(anahtar) == "1" else hayir
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _tahta_satirlar(repo: Path):
    yol = _tahta_yolu(repo)
    if not yol.is_file():
        return _paket(reply="Tahta yok.\nYazmadım. Tahtaya yazmadım.")
    once = yol.read_bytes()
    satirlar: list[tuple[str, str]] = []
    for satir in once.decode("utf-8").splitlines():
        bulunan = _TAHTA_SATIR.match(satir)
        if not bulunan:
            continue
        num = re.search(r"\d+", bulunan.group(1))
        if not num:
            continue
        satirlar.append((num.group(0), bulunan.group(2).strip()))
    if yol.read_bytes() != once:
        return _paket(reply="Tahta değişti. Söylemedim.")
    return satirlar


def _tahta_kenar(repo: Path, son: bool) -> dict:
    gelen = _tahta_satirlar(repo)
    if isinstance(gelen, dict):
        return gelen
    if not gelen:
        return _paket(reply="Satır yok.\nYazmadım. Tahtaya yazmadım.")
    num, durum = gelen[-1] if son else gelen[0]
    return _paket(reply=num + " " + durum + "\nYazmadım. Tahtaya yazmadım.")


def _tek_acik(repo: Path) -> dict:
    gelen = _tahta_satirlar(repo)
    if isinstance(gelen, dict):
        return gelen
    adet = sum(1 for _num, durum in gelen if durum.lower() != "bitti")
    if adet == 0:
        yazi = "Açık yok."
    elif adet == 1:
        yazi = "Tek açık."
    else:
        yazi = "Birden fazla."
    return _paket(reply=yazi + "\nYazmadım. Tahtaya yazmadım.")


def _tahta_bos(repo: Path) -> dict:
    gelen = _tahta_satirlar(repo)
    if isinstance(gelen, dict):
        return gelen
    yazi = "Boş." if not gelen else "Dolu."
    return _paket(reply=yazi + "\nYazmadım. Tahtaya yazmadım.")


def _giris_var(kok: Path) -> bool:
    for path in kok.iterdir():
        if path.name.startswith(".") or path.is_symlink():
            continue
        if path.name in {"__pycache__", "node_modules", ".git"}:
            continue
        return True
    return False


def _kilit_bos(repo: Path) -> dict:
    try:
        kok = Path(_kilit_yolu(repo))
    except _KlasorYok:
        raise ValueError("Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol") from None
    yazi = "Dolu." if _giris_var(kok) else "Boş."
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _uygulama_not_bos(repo: Path) -> dict:
    yol = _uygulama_not_yolu(repo)
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if not yol.is_file():
        return _paket(reply="Not yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    bos = not once.strip()
    if yol.read_bytes() != once:
        return _paket(reply="Not değişti. Söylemedim.")
    yazi = "Boş." if bos else "Dolu."
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _kapi_ilk(repo: Path) -> dict:
    yol = _kapi_notu_yolu(repo)
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if not yol.is_file():
        return _paket(reply="Kapı notu yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    try:
        satirlar = [satir for satir in once.decode("utf-8").splitlines() if satir.strip()]
    except UnicodeError:
        return _paket(reply="Satır okunmadı.\nDosya aynı. Yazmadım.")
    if yol.read_bytes() != once:
        return _paket(reply="Dosya değişti. Söylemedim.")
    if not satirlar:
        return _paket(reply="İlk satır yok.\nYazmadım. Çalıştırmadım.")
    return _paket(reply="İlk satır: " + satirlar[0] + "\nYazmadım. Çalıştırmadım.")


def _kayit_bos(repo: Path, yol_fn) -> dict:
    try:
        yol = yol_fn(repo)
    except ValueError:
        return _paket(reply="Kayıt dosyası yok.\nYazmadım. Çalıştırmadım.")
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if not yol.is_file():
        return _paket(reply="Kayıt dosyası yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    bos = not once.strip()
    if yol.read_bytes() != once:
        return _paket(reply="Kayıt değişti. Söylemedim.")
    yazi = "Boş." if bos else "Dolu."
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _klasor_bos(repo: Path, rel: str, ad: str) -> dict:
    try:
        yol, _norm = _klasor_hedef(repo, rel)
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply=ad + " yok.\nYazmadım. Çalıştırmadım.")
    if yol.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    if yol.is_dir():
        raise ValueError("Bu yer dosya değil.")
    if not yol.is_file():
        return _paket(reply=ad + " yok.\nYazmadım. Çalıştırmadım.")
    once = yol.read_bytes()
    bos = not once.strip()
    if yol.read_bytes() != once:
        return _paket(reply="Dosya değişti. Söylemedim.")
    yazi = "Boş." if bos else "Dolu."
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _hazir_olcu_kaldi(repo: Path) -> dict:
    yazi = "Kalmadı." if _olcu_sablon_duruyor(repo) else "Hazır ölçü değil."
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _olcu_kayit_soyle(repo: Path) -> dict:
    try:
        yol = _olcu_tur_yolu(repo)
    except ValueError:
        yol = None
    vardi = bool(yol and yol.is_file())
    tur = _olcu_tur_oku(repo)
    if yol is not None and yol.is_file() != vardi:
        return _paket(reply="Kayıt değişti. Söylemedim.")
    parca = " ".join(anahtar + "=" + tur[anahtar] for anahtar in _OLCU_ANAHTAR)
    ek = "" if vardi else "\nKayıt dosyası yok."
    return _paket(reply="Ölçü kaydı: " + parca + ek + "\nYazmadım.")


def _arac_kayit_soyle(repo: Path) -> dict:
    try:
        yol = _orta_tur_yolu(repo)
    except ValueError:
        yol = None
    vardi = bool(yol and yol.is_file())
    tur = _orta_tur_oku(repo)
    if yol is not None and yol.is_file() != vardi:
        return _paket(reply="Kayıt değişti. Söylemedim.")
    parca = " ".join(anahtar + "=" + tur[anahtar] for anahtar in _TUR_ANAHTAR)
    ek = "" if vardi else "\nKayıt dosyası yok."
    return _paket(reply="Araç kaydı: " + parca + ek + "\nYazmadım.")


def _arac_soyle(repo: Path) -> dict:
    if _arac_sablon_duruyor(repo):
        return _paket(
            reply=(
                "orta/arac.py içinde satir_say.\nBilinen satır: "
                + _ARAC_SATIR
                + "\nYazmadım. Çalıştırmadım."
            )
        )
    try:
        yol, _norm = _klasor_hedef(repo, "orta/arac.py")
    except ValueError as exc:
        if "seçilmedi" in str(exc):
            raise
        return _paket(reply="orta/arac.py yok.\nYazmadım. Çalıştırmadım.")
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="orta/arac.py yok.\nYazmadım. Çalıştırmadım.")
    return _paket(reply="Hazır araç değil.\nDosya aynı. Yazmadım. Çalıştırmadım.")


def _uygulama_not_satir(repo: Path, metin: str) -> dict:
    satir = _not_satiri(metin)
    yol = _uygulama_not_yolu(repo)
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="Not yok. Şöyle söyle: uygulama notu yaz: " + satir + "\nÇalıştırmadım.")
    eski = yol.read_text(encoding="utf-8")
    satirlar = _not_satirlari(eski)
    if satir in satirlar:
        return _paket(reply="Bu satır duruyor: " + satir + "\nÜstüne yazmadım. Çalıştırmadım.")
    if len(satirlar) >= _ORTA_NOT_TAVAN:
        return _paket(reply="Not doldu. Üstüne yazmadım. Çalıştırmadım.")
    taban = eski if eski.endswith("\n") or eski == "" else eski + "\n"
    yeni = taban + satir + "\n"
    if not yeni.startswith(eski):
        raise ValueError("Üstüne yazmadım.")
    yol.write_text(yeni, encoding="utf-8")
    if yol.read_text(encoding="utf-8") != yeni:
        raise ValueError("Yazılmadı. uygulama notu")
    return _paket(reply="Satır eklendi: ilim-assistant/.ruzgar/uygulama_notu.txt.\n" + satir + "\nÇalıştırmadım.")


def _kapi_notu_yolu(repo: Path) -> Path:
    kok = repo.resolve()
    ust = kok / "ilim-assistant" / "ilim_assistant"
    hedef = ust / "kapi_notu.py"
    if ust.is_symlink() or hedef.is_symlink():
        raise ValueError("Bu yere yazılmaz.")
    gercek = hedef.resolve()
    if gercek.name != "kapi_notu.py" or not _icinde(gercek, kok):
        raise ValueError("Bu yere yazılmaz.")
    return gercek


def _kaynak_satir(repo: Path, metin: str) -> dict:
    satir = _not_satiri(metin)
    if any(im in satir for im in ('"', "\\", "'")):
        raise ValueError("Satırda tırnak olmasın.")
    yol = _kapi_notu_yolu(repo)
    if yol.is_file():
        govde = yol.read_text(encoding="utf-8").strip()
        return _paket(reply="Kaynak satırı duruyor.\n" + govde + "\nÜstüne yazmadım. Çalıştırmadım.")
    govde = '"""Kapı notu. Çalıştırılmaz."""\n\nSATIR = "' + satir + '"\n'
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(govde, encoding="utf-8")
    if yol.read_text(encoding="utf-8") != govde:
        raise ValueError("Yazılmadı. kapi_notu.py")
    return _paket(reply="Yazıldı: ilim-assistant/ilim_assistant/kapi_notu.py.\nÇalıştırmadım.")


def _kaynak_satir_soyle(repo: Path) -> dict:
    yol = _kapi_notu_yolu(repo)
    if not yol.is_file() or yol.is_symlink():
        return _paket(reply="ilim-assistant/ilim_assistant/kapi_notu.py yok.\nYazmadım. Çalıştırmadım.")
    govde = yol.read_text(encoding="utf-8")
    return _paket(reply="Kaynak satırı okundu.\n" + govde.strip() + "\nYazmadım. Çalıştırmadım.")


_DIS_OKU = {".txt", ".md"}


def _dis_kok(repo: Path) -> Path:
    kayit = str(_pin_data().get("dis") or "")
    if not kayit:
        raise ValueError("Dış klasör seçilmedi. Şöyle söyle: dış klasör: tam yol")
    return klasor_guvenli(repo, kayit)


def _dis_klasor(repo: Path, yol: str) -> dict:
    hedef = klasor_guvenli(repo, yol)
    kilit = klasor_oku()
    if kilit:
        kilit_yol = klasor_guvenli(repo, kilit)
        if hedef == kilit_yol or _icinde(hedef, kilit_yol):
            raise ValueError("Bu kilitli klasörün içi. Dış klasör başka yer olsun.")
    data = _pin_data()
    data["dis"] = str(hedef)
    _pin_yaz(data)
    return _paket(reply="Dış klasör: " + str(hedef) + "\nYazmadım. Çalıştırmadım.")


def _dis_olcu(repo: Path) -> dict:
    return _dis_oku(repo, "olcu.txt")


def _dis_ayni_klasor(kok: Path, hedef: Path) -> bool:
    if hedef.is_symlink() or not _icinde(hedef, kok):
        return False
    ust = hedef.parent.resolve()
    if ust == kok.resolve():
        return True
    try:
        return ust.samefile(kok)
    except OSError:
        return False


def _dis_olcu_yaz(repo: Path) -> dict:
    kok = _dis_kok(repo)
    hedef = (kok / "olcu.txt").resolve()
    if not _dis_ayni_klasor(kok, hedef):
        raise ValueError("Bu yere yazılmaz.")
    if hedef.is_dir():
        raise ValueError("Bu yer dosya değil.")
    if hedef.exists():
        if not hedef.is_file():
            raise ValueError("Bu yere yazılmaz.")
        govde = hedef.read_text(encoding="utf-8").strip()
        return _paket(reply="Dış dosya duruyor: " + govde + "\nÜstüne yazmadım. Çalıştırmadım.")
    hedef.write_text(_OLCU_SATIR + "\n", encoding="utf-8")
    if hedef.read_text(encoding="utf-8") != _OLCU_SATIR + "\n":
        raise ValueError("Yazılmadı. olcu.txt")
    return _paket(reply="Yazıldı: olcu.txt.\nBilinen satır: " + _OLCU_SATIR + "\nÇalıştırmadım.")


def _dis_olcu_yer(repo: Path) -> dict:
    kok = _dis_kok(repo)
    hedef = (kok / "olcu.txt").resolve()
    if not _dis_ayni_klasor(kok, hedef):
        raise ValueError("Bu yere yazılmaz.")
    if hedef.is_dir():
        yer = "klasör"
    elif hedef.is_file():
        yer = "dosya"
    else:
        yer = "yok"
    return _paket(reply="olcu.txt " + yer + ".\nYazmadım. Çalıştırmadım.")


def _dis_klasor_soyle(repo: Path) -> dict:
    kok = _dis_kok(repo)
    return _paket(reply="Dış klasör: " + str(kok) + "\nYazmadım. Çalıştırmadım.")


def _dis_say(repo: Path) -> dict:
    kok = _dis_kok(repo)
    adlar: list[str] = []
    for path in sorted(kok.iterdir(), key=lambda item: item.name.lower()):
        if path.name.startswith(".") or path.is_symlink():
            continue
        if path.name in {"__pycache__", "node_modules", ".git"}:
            continue
        adlar.append(path.name)
        if len(adlar) >= 12:
            break
    govde = "\n".join(adlar) if adlar else "Dosya yok."
    return _paket(reply="Dış klasör: " + str(kok) + "\n" + govde + "\nYazmadım. Çalıştırmadım.")


def _dis_adet(repo: Path) -> dict:
    kok = _dis_kok(repo)
    adet = 0
    for path in kok.iterdir():
        if path.name.startswith(".") or path.is_symlink():
            continue
        if path.name in {"__pycache__", "node_modules", ".git"}:
            continue
        adet += 1
        if adet >= 200:
            break
    yazi = "Sayı: 200 ve fazlası." if adet >= 200 else "Sayı: " + str(adet) + "."
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _dis_oku(repo: Path, ad: str) -> dict:
    temiz = (ad or "").strip().strip('"').strip("'")
    if (
        not temiz
        or "/" in temiz
        or "\\" in temiz
        or ".." in temiz
        or ":" in temiz
        or temiz.startswith(".")
    ):
        raise ValueError("Dosya adı geçersiz.")
    if Path(temiz).suffix.lower() not in _DIS_OKU:
        raise ValueError("Bu dosya okunmaz.")
    kok = _dis_kok(repo)
    hedef = (kok / Path(temiz).name).resolve()
    if hedef.is_symlink() or not _icinde(hedef, kok):
        raise ValueError("Dosya yok.")
    if hedef.is_dir():
        raise ValueError("Bu yer dosya değil.")
    if not hedef.is_file():
        raise ValueError("Dosya yok.")
    once = hedef.read_bytes()
    if len(once) > 20_000:
        raise ValueError("Dosya çok büyük.")
    if hedef.read_bytes() != once:
        return _paket(reply="Dosya değişti. Okumadım.")
    govde = once.decode("utf-8")
    goster = govde if len(govde) <= 500 else govde[:500] + "…"
    return _paket(
        reply=temiz + " okundu.\n" + (goster.strip() or "(boş)") + "\nYazmadım. Çalıştırmadım. Dosya aynı.",
        gorunum="kod",
        text=govde,
    )


def _dis_ad(ad: str, uzantilar: set[str]) -> str:
    temiz = (ad or "").strip().strip('"').strip("'")
    if (
        not temiz
        or "/" in temiz
        or "\\" in temiz
        or ".." in temiz
        or ":" in temiz
        or temiz.startswith(".")
        or temiz != Path(temiz).name
    ):
        raise ValueError("Dosya adı geçersiz.")
    if Path(temiz).suffix.lower() not in uzantilar:
        raise ValueError("Bu dosya yazılmaz.")
    return Path(temiz).name


def _dis_yaz(repo: Path, ad: str, metin: str) -> dict:
    satir = _not_satiri(metin)
    ad = _dis_ad(ad, {".txt"})
    kok = _dis_kok(repo)
    hedef = (kok / ad).resolve()
    if not _dis_ayni_klasor(kok, hedef):
        raise ValueError("Bu yere yazılmaz.")
    if hedef.exists():
        if not hedef.is_file():
            raise ValueError("Bu yere yazılmaz.")
        govde = hedef.read_text(encoding="utf-8").strip()
        return _paket(reply="Dış dosya duruyor: " + govde + "\nÜstüne yazmadım. Çalıştırmadım.")
    hedef.write_text(satir + "\n", encoding="utf-8")
    if hedef.read_text(encoding="utf-8") != satir + "\n":
        raise ValueError("Yazılmadı. " + ad)
    return _paket(reply="Yazıldı: " + ad + ".\nÇalıştırmadım.")


_KAPI_NOTU = "ilim-assistant/ilim_assistant/kapi_notu.py"
_OLCU_NOTU = "ilim-assistant/ilim_assistant/olcu_notu.py"


def _git_calis(repo: Path, args: list[str], timeout: int = 8):
    import subprocess

    kok = repo.resolve()
    try:
        return subprocess.run(
            ["git", "--no-optional-locks", "-C", str(kok), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_satir(repo: Path, args: list[str]) -> str:
    sonuc = _git_calis(repo, args)
    if sonuc is None or sonuc.returncode != 0:
        return ""
    return (sonuc.stdout or "").strip()


def _git_kimlik(repo: Path) -> tuple[str, str] | None:
    satir = _git_satir(repo, ["log", "-1", "--format=%an%x00%ae"])
    if "\x00" not in satir:
        return None
    ad, posta = satir.split("\x00", 1)
    ad, posta = ad.strip(), posta.strip()
    if not ad or "@" not in posta:
        return None
    return ad, posta


def _git_kaydet(repo: Path, metin: str) -> dict:
    mesaj = _not_satiri(metin)
    if mesaj.startswith("-"):
        raise ValueError("Kayıt cümlesi olmaz.")
    try:
        yol = _kapi_notu_yolu(repo)
    except ValueError:
        return _paket(reply="Kaynak satırı yok. Kaydetmedim.")
    if not yol.is_file():
        return _paket(reply="Kaynak satırı yok. Kaydetmedim.")
    kimlik = _git_kimlik(repo)
    if not kimlik:
        return _paket(reply="Kimlik yok. Kaydetmedim.")
    once = _git_satir(repo, ["rev-parse", "HEAD"])
    if not once:
        return _paket(reply="Bu depo değil. Kaydetmedim.")
    ad, posta = kimlik
    kim = ["-c", "user.name=" + ad, "-c", "user.email=" + posta]
    ekle = _git_calis(repo, [*kim, "add", "--", _KAPI_NOTU])
    if ekle is None or ekle.returncode != 0:
        return _paket(reply="Kaydetmedim. Göndermedim.")
    kayit = _git_calis(repo, [*kim, "commit", "-m", mesaj, "--", _KAPI_NOTU])
    if kayit is None or kayit.returncode != 0:
        return _paket(reply="Değişen kaynak satırı yok. Kaydetmedim. Göndermedim.")
    sonra = _git_satir(repo, ["rev-parse", "HEAD"])
    adlar = _git_satir(repo, ["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"])
    if not sonra or sonra == once or adlar != _KAPI_NOTU:
        return _paket(reply="Kayıt tek dosya değil. Göndermedim.")
    kisa = _git_satir(repo, ["rev-parse", "--short", "HEAD"]) or sonra[:8]
    return _paket(reply="Kaydedildi: " + kisa + "\nYalnız " + _KAPI_NOTU + ".\nGöndermedim.")


def _git_gonder(repo: Path) -> dict:
    if not _git_satir(repo, ["rev-parse", "--abbrev-ref", "HEAD"]):
        return _paket(reply="Bu depo değil.\nGöndermedim.")
    if not _git_satir(repo, ["remote", "get-url", "origin"]):
        return _paket(reply="Uzak yok. Göndermedim.")
    sonuc = _git_calis(repo, ["push", "origin", "HEAD"], timeout=20)
    if sonuc is None or sonuc.returncode != 0:
        return _paket(reply="Gönderilmedi.")
    return _paket(reply="Gönderildi: origin HEAD.\nZorlamadım.")


def _git_durum(repo: Path) -> dict:
    dal = _git_satir(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    if not dal:
        return _paket(reply="Bu depo değil.\nYazmadım. Göndermedim.")
    kayit = _git_satir(repo, ["log", "-1", "--format=%h %s"]) or "kayıt yok"
    durum = _git_satir(repo, ["status", "--porcelain", "--untracked-files=normal"])
    satirlar = [satir for satir in durum.splitlines() if satir.strip()]
    if not satirlar:
        fark = "Değişen dosya yok."
    else:
        goster = satirlar[:20]
        fark = "Değişen:\n" + "\n".join(goster)
        kalan = len(satirlar) - len(goster)
        if kalan:
            fark += f"\nve {kalan} dosya daha."
    return _paket(reply=f"Dal: {dal}\nSon kayıt: {kayit}\n{fark}\nYazmadım. Göndermedim.")


def _git_son(repo: Path) -> dict:
    if not _git_satir(repo, ["rev-parse", "--is-inside-work-tree"]):
        return _paket(reply="Bu depo değil.\nYazmadım. Göndermedim.")
    kayit = _git_satir(repo, ["log", "-1", "--format=%h %s"])
    if not kayit:
        return _paket(reply="Kayıt yok.\nYazmadım. Göndermedim.")
    return _paket(reply="Son kayıt: " + kayit + "\nYazmadım. Göndermedim.")


def _git_dal(repo: Path) -> dict:
    dal = _git_satir(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    if not dal:
        return _paket(reply="Bu depo değil.\nYazmadım. Göndermedim.")
    return _paket(reply="Dal: " + dal + "\nYazmadım. Göndermedim.")


def _git_depo(repo: Path) -> dict:
    icinde = _git_satir(repo, ["rev-parse", "--is-inside-work-tree"]) == "true"
    yazi = "Bu depo." if icinde else "Bu depo değil."
    return _paket(reply=yazi + "\nYazmadım. Göndermedim.")


def _git_temiz(repo: Path) -> dict:
    if _git_satir(repo, ["rev-parse", "--is-inside-work-tree"]) != "true":
        return _paket(reply="Bu depo değil.\nYazmadım. Göndermedim.")
    bas = _git_satir(repo, ["rev-parse", "HEAD"])
    durum = _git_satir(repo, ["status", "--porcelain", "--untracked-files=normal"])
    sonra = _git_satir(repo, ["rev-parse", "HEAD"])
    if sonra != bas:
        return _paket(reply="Baş değişti. Söylemedim.\nYazmadım. Göndermedim.")
    yazi = "Temiz." if not durum.strip() else "Kirli."
    return _paket(reply=yazi + "\nYazmadım. Göndermedim.")


def _git_uzak(repo: Path) -> dict:
    if _git_satir(repo, ["rev-parse", "--is-inside-work-tree"]) != "true":
        return _paket(reply="Bu depo değil.\nYazmadım. Göndermedim.")
    bas = _git_satir(repo, ["rev-parse", "HEAD"])
    uzak = _git_satir(repo, ["remote", "get-url", "origin"])
    sonra = _git_satir(repo, ["rev-parse", "HEAD"])
    if sonra != bas:
        return _paket(reply="Baş değişti. Söylemedim.\nYazmadım. Göndermedim.")
    yazi = "Uzak var." if uzak else "Uzak yok."
    return _paket(reply=yazi + "\nYazmadım. Göndermedim.")


def _git_bas(repo: Path) -> dict:
    if _git_satir(repo, ["rev-parse", "--is-inside-work-tree"]) != "true":
        return _paket(reply="Bu depo değil.\nYazmadım. Göndermedim.")
    bas = _git_satir(repo, ["rev-parse", "HEAD"])
    kisa = _git_satir(repo, ["rev-parse", "--short", "HEAD"])
    sonra = _git_satir(repo, ["rev-parse", "HEAD"])
    if sonra != bas:
        return _paket(reply="Baş değişti. Söylemedim.\nYazmadım. Göndermedim.")
    if not kisa:
        return _paket(reply="Kayıt yok.\nYazmadım. Göndermedim.")
    return _paket(reply="Baş: " + kisa + "\nYazmadım. Göndermedim.")


def _git_kayit_say(repo: Path) -> dict:
    if _git_satir(repo, ["rev-parse", "--is-inside-work-tree"]) != "true":
        return _paket(reply="Bu depo değil.\nYazmadım. Göndermedim.")
    bas = _git_satir(repo, ["rev-parse", "HEAD"])
    sayi = _git_satir(repo, ["rev-list", "--count", "--max-count=201", "HEAD"])
    sonra = _git_satir(repo, ["rev-parse", "HEAD"])
    if sonra != bas:
        return _paket(reply="Baş değişti. Söylemedim.\nYazmadım. Göndermedim.")
    if not sayi.isdigit():
        return _paket(reply="Kayıt yok.\nYazmadım. Göndermedim.")
    adet = int(sayi)
    yazi = "Kayıt: 200 ve fazlası." if adet >= 200 else "Kayıt: " + str(adet) + "."
    return _paket(reply=yazi + "\nYazmadım. Göndermedim.")


def _git_dal_temiz(repo: Path) -> dict:
    dal = _git_satir(repo, ["symbolic-ref", "--short", "HEAD"])
    if not dal:
        dal = _git_satir(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    if not dal:
        return _paket(reply="Bu depo değil.\nYazmadım. Göndermedim.")
    bas = _git_satir(repo, ["rev-parse", "HEAD"])
    durum = _git_satir(repo, ["status", "--porcelain", "--untracked-files=normal"])
    sonra = _git_satir(repo, ["rev-parse", "HEAD"])
    if sonra != bas:
        return _paket(reply="Baş değişti. Söylemedim.\nYazmadım. Göndermedim.")
    yazi = "Temiz." if not durum.strip() else "Kirli."
    return _paket(reply="Dal: " + dal + "\n" + yazi + "\nYazmadım. Göndermedim.")


def _dis_bos(repo: Path) -> dict:
    kok = _dis_kok(repo)
    yazi = "Dolu." if _giris_var(kok) else "Boş."
    return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")


def _git_fark(repo: Path, yol_rel: str = _KAPI_NOTU) -> dict:
    if yol_rel not in {_KAPI_NOTU, _OLCU_NOTU}:
        return _paket(reply="Bu dosyanın farkı söylenmez.\nYazmadım. Göndermedim.")
    once = _git_satir(repo, ["rev-parse", "HEAD"])
    if not once:
        return _paket(reply="Bu depo değil.\nYazmadım. Göndermedim.")
    fark = _git_satir(repo, ["diff", "--unified=1", "--", yol_rel])
    sonra = _git_satir(repo, ["rev-parse", "HEAD"])
    if sonra != once:
        return _paket(reply="Baş değişti. Farkı söylemedim.\nYazmadım. Göndermedim.")
    if fark:
        goster = fark if len(fark) <= 800 else fark[:800] + "…"
        return _paket(reply="Fark: " + yol_rel + "\n" + goster + "\nYazmadım. Göndermedim.")
    durum = _git_satir(repo, ["status", "--porcelain", "--", yol_rel])
    yol = repo / yol_rel
    if durum.startswith("??") and yol.is_file() and not yol.is_symlink():
        govde = yol.read_text(encoding="utf-8")
        goster = govde if len(govde) <= 500 else govde[:500] + "…"
        return _paket(reply="İzlenmeyen dosya.\n" + goster.strip() + "\nYazmadım. Göndermedim.")
    if yol_rel in {_KAPI_NOTU, _OLCU_NOTU} and not yol.is_file():
        return _paket(reply=yol_rel + " yok.\nYazmadım. Göndermedim.")
    return _paket(reply="Fark yok.\nYazmadım. Göndermedim.")


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
        if kind == "orta_is":
            return _orta_is(repo)
        if kind == "orta_soyle":
            return _orta_soyle(repo)
        if kind == "orta_not":
            return _orta_not(repo, adim.get("metin") or "")
        if kind == "orta_not_oku":
            return _orta_not_oku(repo)
        if kind == "orta_not_satir":
            return _orta_not_satir(repo, adim.get("metin") or "")
        if kind == "orta_arac_not":
            return _orta_arac_not(repo)
        if kind == "orta_arac_satir":
            return _orta_arac_satir(repo, adim.get("metin") or "")
        if kind == "orta_tur_baslat":
            return _orta_tur_baslat(repo)
        if kind == "orta_tur_duzelt_fazla":
            return _paket(reply="Bu cümle yazmaz. Şöyle söyle: orta turu düzelt\nDosya aynı. Çalıştırmadım.")
        if kind == "orta_tur_duzelt":
            return _orta_tur_duzelt(repo)
        if kind == "orta_tur_bak_fazla":
            return _paket(reply="Bu cümle bakmaz. Şöyle söyle: orta turu bak\nDosya aynı. Düzeltmedim.")
        if kind == "orta_tur_bak":
            return _orta_tur_bak(repo)
        if kind == "orta_tur_kapat_fazla":
            return _paket(reply="Bu cümle kapatmaz. Şöyle söyle: orta turu kapat\nTahtaya yazmadım.")
        if kind == "orta_tur_kapat":
            return _orta_tur_kapat(repo)
        if kind == "orta_tur_soyle_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: orta turu söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "orta_tur_soyle":
            return _orta_tur_soyle(repo)
        if kind == "orta_kayit_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: orta araç kaydını söyle\nYazmadım.")
        if kind == "orta_kayit":
            return _arac_kayit_soyle(repo)
        if kind == "orta_arac_soyle_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: orta aracını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "orta_arac_soyle":
            return _arac_soyle(repo)
        if kind == "arac_dosya_satir_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç dosyasının satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_dosya_satir":
            return _kilit_dosya_satir(repo, "orta/arac.py")
        if kind == "hazir_iki_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: hazır ikisini söyle\nYazmadım. Çalıştırmadım.")
        if kind == "hazir_iki":
            return _hazir_ikisi(repo)
        if kind == "olcu_soyle_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: orta ölçüsünü söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_soyle":
            return _olcu_soyle(repo)
        if kind == "olcu_say_fazla":
            return _paket(reply="Bu cümle saymaz. Şöyle söyle: orta ölçüsünde kelime say\nDosya aynı. Çalıştırmadım.")
        if kind == "olcu_say_metin":
            return _olcu_say(repo, _not_satiri(adim.get("metin") or ""))
        if kind == "olcu_say":
            return _olcu_say_not(repo)
        if kind == "olcu_neden":
            return _olcu_neden(repo)
        if kind == "olcu_duzelt_fazla":
            return _paket(reply="Bu cümle yazmaz. Şöyle söyle: orta ölçüsünü düzelt\nDosya aynı. Çalıştırmadım.")
        if kind == "olcu_duzelt":
            return _olcu_duzelt(repo)
        if kind == "olcu_bak_fazla":
            return _paket(reply="Bu cümle bakmaz. Şöyle söyle: orta ölçüsüne bak\nDosya aynı. Düzeltmedim.")
        if kind == "olcu_bak":
            return _olcu_bak(repo)
        if kind == "olcu_kapat_fazla":
            return _paket(reply="Bu cümle kapatmaz. Şöyle söyle: orta ölçüsünü kapat\nTahtaya yazmadım.")
        if kind == "olcu_kapat":
            return _olcu_kapat(repo)
        if kind == "olcu_test_fazla":
            return _paket(reply="Bu cümle çalıştırmaz. Şöyle söyle: orta ölçüsünü çalıştır\nDosya aynı. Düzeltmedim.")
        if kind == "olcu_test":
            return _olcu_test(repo)
        if kind == "olcu_sira_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: orta ölçü sırasını söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "olcu_sira":
            return _olcu_sira(repo)
        if kind == "olcu_kayit_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: orta ölçü kaydını söyle\nYazmadım.")
        if kind == "olcu_kayit":
            return _olcu_kayit_soyle(repo)
        if kind == "olcu_dosya_satir_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü dosyasının satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_dosya_satir":
            return _kilit_dosya_satir(repo, _OLCU_REL)
        if kind == "olcu_notu_var_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü notu var mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_notu_var":
            return _not_var(_olcu_notu_yolu(repo), "Ölçü notu")
        if kind == "olcu_satir_soyle_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_satir_soyle":
            return _olcu_satir_soyle(repo)
        if kind == "olcu_satir_yaz_fazla":
            return _paket(reply="Bu cümle yazmaz. Bilinen satır: " + _OLCU_SATIR + "\nŞöyle söyle: ölçü satırı yaz\nDosya aynı. Çalıştırmadım.")
        if kind == "olcu_satir_yaz":
            return _olcu_satir_yaz(repo)
        if kind == "orta_neden":
            return _orta_test_neden(repo)
        if kind == "orta_duzelt_eksik":
            return _orta_arac_duzelt_eksik(repo)
        if kind == "orta_duzelt":
            return _orta_arac_duzelt(repo, adim.get("metin") or "")
        if kind == "orta_bakis":
            return _orta_ikinci_bak(repo)
        if kind == "tahta_bitti":
            return _acik_satiri_bitti(repo)
        if kind == "tahta_say_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: açık satır sayısını söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "tahta_say":
            return _tahta_acik_say(repo)
        if kind == "tahta_bitti_say_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: bitti satır sayısını söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "tahta_bitti_say":
            return _tahta_bitti_say(repo)
        if kind == "kilit_soyle_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: kilitli klasörü söyle\nYazmadım. Çalıştırmadım.")
        if kind == "kilit_soyle":
            return _kilit_soyle(repo)
        if kind == "orta_test":
            return _orta_test(repo)
        if kind == "uygulama_not":
            return _uygulama_not(repo, adim.get("metin") or "")
        if kind == "uygulama_not_oku":
            return _uygulama_not_oku(repo)
        if kind == "uygulama_not_say_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: uygulama notunun satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "uygulama_not_say":
            return _uygulama_not_say(repo)
        if kind == "uygulama_not_son_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: uygulama notunun son satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "uygulama_not_son":
            return _uygulama_not_son(repo)
        if kind == "uygulama_not_satir_fazla":
            return _paket(reply="Bu cümle eklemez. Şöyle söyle: uygulama notuna satır ekle: metin\nÜstüne yazmadım. Çalıştırmadım.")
        if kind == "uygulama_not_satir":
            return _uygulama_not_satir(repo, adim.get("metin") or "")
        if kind == "kaynak_satir_soyle_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: kaynak satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "kaynak_satir_soyle":
            return _kaynak_satir_soyle(repo)
        if kind == "kapi_var_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: kapı notu var mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "kapi_var":
            return _not_var(_kapi_notu_yolu(repo), "Kapı notu")
        if kind == "kaynak_satir":
            return _kaynak_satir(repo, adim.get("metin") or "")
        if kind == "dis_klasor":
            return _dis_klasor(repo, adim.get("yol") or "")
        if kind == "dis_say":
            return _dis_say(repo)
        if kind == "dis_oku":
            return _dis_oku(repo, adim.get("ad") or "")
        if kind == "dis_olcu_fazla":
            return _paket(reply="Bu cümle okumaz. Şöyle söyle: dış ölçü dosyasını oku\nYazmadım. Çalıştırmadım.")
        if kind == "dis_olcu":
            return _dis_olcu(repo)
        if kind == "dis_olcu_yaz_fazla":
            return _paket(reply="Bu cümle yazmaz. Şöyle söyle: dış ölçü dosyasına yaz\nDosya aynı. Çalıştırmadım.")
        if kind == "dis_olcu_yaz":
            return _dis_olcu_yaz(repo)
        if kind == "dis_olcu_yer_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: dış ölçü yerini söyle\nYazmadım. Çalıştırmadım.")
        if kind == "dis_olcu_yer":
            return _dis_olcu_yer(repo)
        if kind == "dis_klasor_soyle_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: dış klasörü söyle\nYazmadım. Çalıştırmadım.")
        if kind == "dis_klasor_soyle":
            return _dis_klasor_soyle(repo)
        if kind == "dis_adet_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: dış klasörün sayısını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "dis_adet":
            return _dis_adet(repo)
        if kind == "dis_yaz":
            return _dis_yaz(repo, adim.get("ad") or "", adim.get("metin") or "")
        if kind == "git_durum":
            return _git_durum(repo)
        if kind == "git_olcu_fark_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git ölçü farkını söyle\nYazmadım. Göndermedim.")
        if kind == "git_olcu_fark":
            return _git_fark(repo, _OLCU_NOTU)
        if kind == "git_fark_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git farkını söyle\nYazmadım. Göndermedim.")
        if kind == "git_fark":
            return _git_fark(repo)
        if kind == "git_son_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git son kaydı söyle\nYazmadım. Göndermedim.")
        if kind == "git_son":
            return _git_son(repo)
        if kind == "git_dal_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git dalını söyle\nYazmadım. Göndermedim.")
        if kind == "git_dal":
            return _git_dal(repo)
        if kind == "git_depo_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git deposu mu söyle\nYazmadım. Göndermedim.")
        if kind == "git_depo":
            return _git_depo(repo)
        if kind == "git_temiz_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git temiz mi söyle\nYazmadım. Göndermedim.")
        if kind == "git_temiz":
            return _git_temiz(repo)
        if kind == "uygulama_not_ilk_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: uygulama notunun ilk satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "uygulama_not_ilk":
            return _uygulama_not_ilk(repo)
        if kind == "uygulama_not_var_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: uygulama notu var mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "uygulama_not_var":
            return _not_var(_uygulama_not_yolu(repo), "Uygulama notu")
        if kind == "olcu_dosya_var_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü dosyası var mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_dosya_var":
            return _klasor_var(repo, _OLCU_REL, "Ölçü dosyası")
        if kind == "arac_dosya_var_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç dosyası var mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_dosya_var":
            return _klasor_var(repo, "orta/arac.py", "Araç dosyası")
        if kind == "olcu_kayit_var_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü kaydı var mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_kayit_var":
            return _not_var(_olcu_tur_yolu(repo), "Ölçü kaydı")
        if kind == "arac_kayit_var_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç kaydı var mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_kayit_var":
            return _not_var(_orta_tur_yolu(repo), "Araç kaydı")
        if kind == "tahta_var_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: tahta var mı söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "tahta_var":
            return _not_var(_tahta_yolu(repo), "Tahta")
        if kind == "tahta_satir_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: tahta satır sayısını söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "tahta_satir":
            return _tahta_satir_say(repo)
        if kind == "kilit_adet_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: kilitli klasörün sayısını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "kilit_adet":
            return _kilit_adet(repo)
        if kind == "hazir_olcu_satir_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: hazır ölçü satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "hazir_olcu_satir":
            return _hazir_bilinen(repo, _OLCU_REL, _olcu_sablon_duruyor(repo), _OLCU_SATIR, "Hazır ölçü değil.")
        if kind == "hazir_arac_satir_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: hazır araç satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "hazir_arac_satir":
            return _hazir_bilinen(repo, "orta/arac.py", _arac_sablon_duruyor(repo), _ARAC_SATIR, "Hazır araç değil.")
        if kind == "hazir_olcu_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: hazır ölçüyü söyle\nYazmadım. Çalıştırmadım.")
        if kind == "hazir_olcu":
            return _hazir_soyle(_olcu_sablon_duruyor(repo), "Ölçü hazır.")
        if kind == "kapi_satir_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: kapı notunun satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "kapi_satir":
            return _repo_satir(_kapi_notu_yolu(repo), "Kapı notu")
        if kind == "olcu_notu_satir_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü notunun satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_notu_satir":
            return _repo_satir(_olcu_notu_yolu(repo), "Ölçü notu")
        if kind == "olcu_bakis_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü bakışını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_bakis":
            return _bayrak_bir(repo, _olcu_tur_yolu, _olcu_tur_oku)
        if kind == "arac_bakis_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç bakışını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_bakis":
            return _bayrak_bir(repo, _orta_tur_yolu, _orta_tur_oku)
        if kind == "olcu_kapandi_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü kapandı mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_kapandi":
            return _olcu_kapandi_soyle(repo)
        if kind == "olcu_duzeltme_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü düzeltmesini söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_duzeltme":
            return _bayrak_etiket(repo, _olcu_tur_yolu, _olcu_tur_oku, "duzeltme", "Düzeltme")
        if kind == "olcu_gecti_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü geçti mi söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_gecti":
            return _bayrak_evet(repo, _olcu_tur_yolu, _olcu_tur_oku, "gecti", "Geçti.", "Geçmedi.")
        if kind == "olcu_durdu_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü durdu mu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_durdu":
            return _bayrak_evet(repo, _olcu_tur_yolu, _olcu_tur_oku, "durdu", "Durdu.", "Durmadı.")
        if kind == "hazir_olcu_kaldi_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: hazır ölçü kaldı mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "hazir_olcu_kaldi":
            return _hazir_olcu_kaldi(repo)
        if kind == "olcu_kaldi_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü kaldı mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_kaldi":
            return _bayrak_evet(repo, _olcu_tur_yolu, _olcu_tur_oku, "kaldi", "Kaldı.", "Kalmadı.")
        if kind == "arac_duzeltme_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç düzeltmesini söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_duzeltme":
            return _bayrak_etiket(repo, _orta_tur_yolu, _orta_tur_oku, "duzeltme", "Düzeltme")
        if kind == "arac_gecti_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç geçti mi söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_gecti":
            return _bayrak_evet(repo, _orta_tur_yolu, _orta_tur_oku, "gecti", "Geçti.", "Geçmedi.")
        if kind == "arac_durdu_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç durdu mu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_durdu":
            return _bayrak_evet(repo, _orta_tur_yolu, _orta_tur_oku, "durdu", "Durdu.", "Durmadı.")
        if kind == "arac_kaldi_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç kaldı mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_kaldi":
            return _bayrak_evet(repo, _orta_tur_yolu, _orta_tur_oku, "kaldi", "Kaldı.", "Kalmadı.")
        if kind == "arac_tur_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç turunu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_tur":
            return _bayrak_etiket(repo, _orta_tur_yolu, _orta_tur_oku, "tur", "Tur")
        if kind == "hazir_arac_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: hazır aracı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "hazir_arac":
            yazi = "Araç hazır." if _arac_sablon_duruyor(repo) else "Araç yok."
            return _paket(reply=yazi + "\nYazmadım. Çalıştırmadım.")
        if kind == "tek_acik_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: tek açık satır var mı söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "tek_acik":
            return _tek_acik(repo)
        if kind == "tahta_ilk_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: tahtanın ilk satırını söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "tahta_ilk":
            return _tahta_kenar(repo, False)
        if kind == "tahta_son_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: tahtanın son satırını söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "tahta_son":
            return _tahta_kenar(repo, True)
        if kind == "tahta_bos_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: tahta boş mu söyle\nYazmadım. Tahtaya yazmadım.")
        if kind == "tahta_bos":
            return _tahta_bos(repo)
        if kind == "kilit_bos_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: kilitli klasör boş mu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "kilit_bos":
            return _kilit_bos(repo)
        if kind == "dis_bos_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: dış klasör boş mu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "dis_bos":
            return _dis_bos(repo)
        if kind == "uygulama_not_bos_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: uygulama notu boş mu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "uygulama_not_bos":
            return _uygulama_not_bos(repo)
        if kind == "orta_not_var_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: orta notu var mı söyle\nYazmadım. Çalıştırmadım.")
        if kind == "orta_not_var":
            return _klasor_var(repo, _ORTA_NOT, "Orta notu")
        if kind == "orta_not_satir_say_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: orta notunun satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "orta_not_satir_say":
            return _kilit_dosya_satir(repo, _ORTA_NOT)
        if kind == "kapi_ilk_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: kapı notunun ilk satırını söyle\nYazmadım. Çalıştırmadım.")
        if kind == "kapi_ilk":
            return _kapi_ilk(repo)
        if kind == "git_uzak_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git uzak var mı söyle\nYazmadım. Göndermedim.")
        if kind == "git_uzak":
            return _git_uzak(repo)
        if kind == "git_bas_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git başını söyle\nYazmadım. Göndermedim.")
        if kind == "git_bas":
            return _git_bas(repo)
        if kind == "git_kayit_say_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git kayıt sayısını söyle\nYazmadım. Göndermedim.")
        if kind == "git_kayit_say":
            return _git_kayit_say(repo)
        if kind == "git_dal_temiz_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: git dalı temiz mi söyle\nYazmadım. Göndermedim.")
        if kind == "git_dal_temiz":
            return _git_dal_temiz(repo)
        if kind == "olcu_kayit_bos_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü kaydı boş mu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_kayit_bos":
            return _kayit_bos(repo, _olcu_tur_yolu)
        if kind == "arac_kayit_bos_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç kaydı boş mu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_kayit_bos":
            return _kayit_bos(repo, _orta_tur_yolu)
        if kind == "olcu_dosya_bos_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: ölçü dosyası boş mu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "olcu_dosya_bos":
            return _klasor_bos(repo, _OLCU_REL, "Ölçü dosyası")
        if kind == "arac_dosya_bos_fazla":
            return _paket(reply="Bu cümle söylemez. Şöyle söyle: araç dosyası boş mu söyle\nYazmadım. Çalıştırmadım.")
        if kind == "arac_dosya_bos":
            return _klasor_bos(repo, "orta/arac.py", "Araç dosyası")
        if kind == "git_kaydet":
            return _git_kaydet(repo, adim.get("metin") or "")
        if kind == "git_gonder":
            return _git_gonder(repo)
        if kind == "git_yazma":
            return _paket(reply="Bunu yapmadım. Göndermedim. Dosya aynı.")
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
