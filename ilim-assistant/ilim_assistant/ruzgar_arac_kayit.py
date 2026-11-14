# -*- coding: utf-8 -*-
"""
Rüzgâr araç kayıt defteri (Şehir İkiz Faz 2).

Cursor / sistemde kurulan programlar buraya yazılır.
Rüzgâr yetenek etiketine göre hangi aracı seçeceğini buradan okur.
Kurulum yapmaz — sadece tarar ve kaydeder.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
ILIM = Path(__file__).resolve().parents[1]
KAYIT_YOLU = ILIM / "knowledge" / "ortak_kaynak" / "alanlar" / "bilgisayar_eserleri" / "RUZGAR_ARAC_KAYIT.json"

# Bilinen araç şablonları — tarama kuralları
_SABLONLAR: list[dict[str, Any]] = [
    {
        "id": "ffmpeg",
        "ad": "FFmpeg",
        "yetenekler": ["video", "ses", "medya"],
        "komutlar": {"which": ["ffmpeg"], "env": ["RUZGAR_FFMPEG"]},
        "ornek": "ffmpeg -i girdi.mp4 -c:v libx264 cikti.mp4",
    },
    {
        "id": "ffprobe",
        "ad": "FFprobe",
        "yetenekler": ["video", "medya", "meta"],
        "komutlar": {"which": ["ffprobe"], "env": ["RUZGAR_FFPROBE"]},
        "ornek": "ffprobe -v quiet -print_format json -show_format dosya.mp4",
    },
    {
        "id": "ollama",
        "ad": "Ollama",
        "yetenekler": ["llm", "yerel_model"],
        "komutlar": {"which": ["ollama"], "paths": [
            r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe",
            r"D:\ÜMİT\14-) PROGRAMLAR\Ollama\ollama.exe",
        ]},
        "ornek": "ollama run llama3",
    },
    {
        "id": "python",
        "ad": "Python",
        "yetenekler": ["script", "rag", "gis_boru"],
        "komutlar": {"which": ["python", "python3"], "env": ["RUZGAR_PYTHON"]},
        "ornek": "python script.py",
    },
    {
        "id": "node",
        "ad": "Node.js",
        "yetenekler": ["script", "electron", "web"],
        "komutlar": {"which": ["node"]},
        "ornek": "node app.js",
    },
    {
        "id": "cesium",
        "ad": "CesiumJS (yerel vendor)",
        "yetenekler": ["harita", "3d", "sehir", "globe"],
        "komutlar": {
            "files": [
                str(REPO / "ruzgar-desktop" / "vendor" / "cesium" / "Cesium.js"),
            ]
        },
        "ornek": "harita-viewer mode=3d | tur",
    },
    {
        "id": "leaflet",
        "ad": "Leaflet (yerel vendor)",
        "yetenekler": ["harita", "2d"],
        "komutlar": {
            "files": [
                str(REPO / "ruzgar-desktop" / "vendor" / "leaflet" / "leaflet.js"),
            ]
        },
        "ornek": "harita-viewer mode=2d | uydu | 4d",
    },
    {
        "id": "gdal",
        "ad": "GDAL / ogr2ogr",
        "yetenekler": ["gis", "donusturme", "vektor"],
        "komutlar": {"which": ["gdalinfo", "ogr2ogr"], "paths": [
            r"C:\OSGeo4W\bin\ogr2ogr.exe",
            r"C:\Program Files\QGIS 3.44.15\bin\ogr2ogr.exe",
            r"C:\Program Files\QGIS*\bin\ogr2ogr.exe",
        ]},
        "ornek": "ogr2ogr -f GeoJSON out.geojson in.shp",
        "plan_faz": 3,
    },
    {
        "id": "qgis",
        "ad": "QGIS",
        "yetenekler": ["gis", "harita_hazirlik", "masaüstü"],
        "komutlar": {"which": ["qgis"], "paths": [
            r"C:\Program Files\QGIS 3.44.15\bin\qgis-ltr-bin.exe",
            r"C:\Program Files\QGIS 3.44.15\bin\qgis-bin.exe",
            r"C:\Program Files\QGIS*\bin\qgis-ltr-bin.exe",
            r"C:\Program Files\QGIS*\bin\qgis-bin.exe",
            r"C:\OSGeo4W\bin\qgis.exe",
        ]},
        "ornek": "qgis proje.qgz",
        "plan_faz": 3,
    },
    {
        "id": "mediamtx",
        "ad": "MediaMTX",
        "yetenekler": ["kamera", "hls", "webrtc", "yayin"],
        "komutlar": {"paths": [
            r"D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz\tools\mediamtx.exe",
        ]},
        "ornek": "mediamtx.exe",
        "plan_faz": 9,
    },
    {
        "id": "psql",
        "ad": "PostgreSQL / psql",
        "yetenekler": ["db", "postgis", "sehir_veri"],
        "komutlar": {"which": ["psql"], "paths": [
            r"D:\RuzgarSehirIkiz\pgsql\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\*\bin\psql.exe",
        ]},
        "ornek": "psql -U postgres -h 127.0.0.1 -d sehir_ikiz",
        "plan_faz": 3,
    },
    {
        "id": "blender",
        "ad": "Blender",
        "yetenekler": ["3d_model", "gltf", "mimari"],
        "komutlar": {"which": ["blender"], "paths": [
            r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender*\blender.exe",
        ]},
        "ornek": "blender -b model.blend --python export_gltf.py",
        "plan_faz": 5,
    },
    {
        "id": "ifcopenshell",
        "ad": "IfcOpenShell (Python)",
        "yetenekler": ["bim", "ifc", "mimari"],
        "komutlar": {"python_mod": ["ifcopenshell"]},
        "ornek": "import ifcopenshell",
        "plan_faz": 6,
    },
    {
        "id": "unreal",
        "ad": "Unreal Engine 5",
        "yetenekler": ["render", "cinematic", "ue5"],
        "komutlar": {"paths": [
            r"C:\Program Files\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
            r"C:\Program Files\Epic Games\UE_5*\Engine\Binaries\Win64\UnrealEditor.exe",
        ]},
        "ornek": "EpicGamesLauncher.exe → Unreal Engine kur / UnrealEditor.exe",
        "plan_faz": 10,
    },
]


def _expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


def _glob_first(pattern: str) -> Path | None:
    """Basit * içeren yol — tek seviye parent glob."""
    p = _expand(pattern)
    if "*" not in str(p):
        return p if p.is_file() else None
    parts = p.parts
    # C:\Program Files\QGIS*\bin\ogr2ogr.exe
    base = Path(parts[0] + os.sep) if os.name == "nt" else Path("/")
    idx = 1
    cur = [base]
    while idx < len(parts):
        part = parts[idx]
        nxt: list[Path] = []
        if "*" in part:
            for c in cur:
                if c.is_dir():
                    nxt.extend(c.glob(part))
        else:
            for c in cur:
                nxt.append(c / part)
        cur = nxt
        idx += 1
        if not cur:
            return None
    for c in cur:
        if c.is_file():
            return c
    return None


def _find_exe(spec: dict[str, Any]) -> tuple[str | None, str]:
    """(yol, kaynak) — kaynak: env|which|path|file|python_mod|yok."""
    kom = spec.get("komutlar") or {}
    for env_k in kom.get("env") or []:
        v = (os.environ.get(env_k) or "").strip()
        if v and Path(v).is_file():
            return v, "env"
    for name in kom.get("which") or []:
        hit = shutil.which(name)
        if hit:
            return hit, "which"
    for pat in kom.get("paths") or []:
        found = _glob_first(pat)
        if found:
            return str(found), "path"
    for f in kom.get("files") or []:
        fp = Path(f)
        if fp.is_file():
            return str(fp), "file"
    for mod in kom.get("python_mod") or []:
        try:
            __import__(mod)
            return mod, "python_mod"
        except Exception:
            pass
    return None, "yok"


def tara() -> dict[str, Any]:
    """Tüm şablonları tara; kayıt dosyasını güncelle."""
    araclar: list[dict[str, Any]] = []
    for s in _SABLONLAR:
        yol, kaynak = _find_exe(s)
        kayitli = bool(yol)
        araclar.append(
            {
                "id": s["id"],
                "ad": s["ad"],
                "yetenekler": list(s.get("yetenekler") or []),
                "kurulu": kayitli,
                "yol": yol,
                "kaynak": kaynak,
                "ornek_komut": s.get("ornek"),
                "plan_faz": s.get("plan_faz"),
            }
        )
    doc = {
        "surum": 1,
        "guncelleme": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "aciklama": "Rüzgâr araç kayıt defteri — Cursor kurulumları tarama ile eklenir.",
        "araclar": araclar,
        "kurulu_sayisi": sum(1 for a in araclar if a["kurulu"]),
        "toplam": len(araclar),
    }
    KAYIT_YOLU.parent.mkdir(parents=True, exist_ok=True)
    KAYIT_YOLU.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc


def oku() -> dict[str, Any]:
    if not KAYIT_YOLU.is_file():
        return tara()
    try:
        return json.loads(KAYIT_YOLU.read_text(encoding="utf-8"))
    except Exception:
        return tara()


def sec(yetenek: str) -> dict[str, Any] | None:
    """Yetenek etiketine göre kurulu ilk aracı seç."""
    y = (yetenek or "").strip().lower()
    if not y:
        return None
    doc = oku()
    for a in doc.get("araclar") or []:
        if not a.get("kurulu"):
            continue
        tags = [str(t).lower() for t in (a.get("yetenekler") or [])]
        if y in tags or y == str(a.get("id") or "").lower():
            return a
    return None


def kaydet_manuel(arac_id: str, yol: str, yetenekler: list[str] | None = None) -> dict[str, Any]:
    """Cursor kurulum sonrası manuel kayıt."""
    doc = oku()
    found = False
    for a in doc.get("araclar") or []:
        if a.get("id") == arac_id:
            a["kurulu"] = True
            a["yol"] = yol
            a["kaynak"] = "manuel"
            if yetenekler:
                a["yetenekler"] = yetenekler
            found = True
            break
    if not found:
        (doc.setdefault("araclar", [])).append(
            {
                "id": arac_id,
                "ad": arac_id,
                "yetenekler": yetenekler or [],
                "kurulu": True,
                "yol": yol,
                "kaynak": "manuel",
            }
        )
    doc["guncelleme"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    doc["kurulu_sayisi"] = sum(1 for a in doc["araclar"] if a.get("kurulu"))
    doc["toplam"] = len(doc["araclar"])
    KAYIT_YOLU.parent.mkdir(parents=True, exist_ok=True)
    KAYIT_YOLU.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc


def smoke_arac_kayit() -> dict[str, Any]:
    doc = tara()
    fails: list[str] = []
    if not KAYIT_YOLU.is_file():
        fails.append("kayıt dosyası yazılmadı")
    # Cesium / leaflet vendor zorunlu (Faz 1)
    by_id = {a["id"]: a for a in doc.get("araclar") or []}
    if not (by_id.get("cesium") or {}).get("kurulu"):
        fails.append("cesium vendor kayıtlı değil")
    if not (by_id.get("leaflet") or {}).get("kurulu"):
        fails.append("leaflet vendor kayıtlı değil")
    if not sec("3d"):
        fails.append("sec(3d) boş")
    if not sec("harita"):
        fails.append("sec(harita) boş")
    return {"ok": not fails, "fails": fails, "kurulu": doc.get("kurulu_sayisi"), "toplam": doc.get("toplam")}
