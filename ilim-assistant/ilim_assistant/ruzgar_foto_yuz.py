"""Rüzgar Foto / Yüz — yerel kütüphane + yüz eşleştirme.

Katmanlar (atlanmaz):
  1. katalog  — görselleri listele
  2. yuz      — OpenCV YuNet (OpenCV 5) veya Haar (OpenCV 4) ile yüz kutuları
  3. gomme    — yüz kırpımından yerel görünüm vektörü
  4. eslesme  — tek referans → kosinüs benzerliği (top-k)

Politika: yalnız yerel disk; bulut yüz API yok; sahte eşleşme yok.
Not: Bu, kimlik doğrulama modeli değil; aynı kişinin benzer karelerini bulmaya yardım eder.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

SCHEMA = 2
IMAGE_EXT = {
    ".jpg",
    ".jpeg",
    ".jfif",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".gif",
    ".heic",
    ".heif",
    ".avif",
}
MAX_FILES = 20_000
MAX_DEPTH = 12
MAX_FACES_PER_IMG = 8
EMBED_SIZE = 32  # 32x32 gri + hist → vektör
MATCH_TOP = 24
MATCH_MIN_SCORE = 0.62
REF_MAX_SIDE = 2048  # kutuya / eşleşmeye uygun üst kenar
REF_JPEG_QUALITY = 92
REF_RAW_MAX_BYTES = 80_000_000

_DATA_DIR = Path(__file__).resolve().parent / "data"
_INDEX_DIR = Path(__file__).resolve().parent.parent / ".ruzgar_foto_index"
_CATALOG = _INDEX_DIR / "katalog.json"
_YUZ = _INDEX_DIR / "yuz.json"
_GOMME = _INDEX_DIR / "gomme.json"
_REF_FILE = _INDEX_DIR / "referans_secilen"
_REF_META = _INDEX_DIR / "referans_secilen.json"
_YUNET_NAMES = (
    "face_detection_yunet_2023mar.onnx",
    "face_detection_yunet_2026may.onnx",
)


def index_dir() -> Path:
    _INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return _INDEX_DIR


def _empty_catalog() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "kok": "",
        "guncelleme": 0,
        "dosya_sayisi": 0,
        "katman": {
            "katalog": False,
            "yuz": False,
            "gomme": False,
            "eslesme": False,
        },
        "dosyalar": [],
    }


def opencv_hazir() -> bool:
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401

        return True
    except Exception:
        return False


def durum() -> dict[str, Any]:
    data = _load_catalog()
    kat = data.get("katman") or {}
    yuz_n = 0
    gomme_n = 0
    if _YUZ.is_file():
        try:
            yuz_n = int(json.loads(_YUZ.read_text(encoding="utf-8")).get("yuz_sayisi") or 0)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            yuz_n = 0
    if _GOMME.is_file():
        try:
            gomme_n = int(json.loads(_GOMME.read_text(encoding="utf-8")).get("vektor_sayisi") or 0)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            gomme_n = 0
    sonraki = _next_layer(kat)
    notlar = []
    if not opencv_hazir():
        notlar.append("OpenCV yok: pip install opencv-python-headless numpy")
    if not kat.get("katalog"):
        notlar.append("Önce fotoğraf klasörünü tara (katalog).")
    elif sonraki == "yuz":
        notlar.append("Sırada: yüz algılama (Yüz tara).")
    elif sonraki == "gomme":
        notlar.append(f"Yüzler hazır ({yuz_n}). Sırada: gömme kur.")
    elif sonraki == "eslesme":
        notlar.append(f"Gömme hazır ({gomme_n}). Referans bırakıp Yüz ara.")
    else:
        notlar.append(f"Hazır · {data.get('dosya_sayisi') or 0} foto · {yuz_n} yüz · {gomme_n} vektör.")
    return {
        "ok": True,
        "schema": SCHEMA,
        "kok": data.get("kok") or "",
        "dosya_sayisi": int(data.get("dosya_sayisi") or 0),
        "yuz_sayisi": yuz_n,
        "vektor_sayisi": gomme_n,
        "guncelleme": int(data.get("guncelleme") or 0),
        "opencv": opencv_hazir(),
        "katman": {
            "katalog": bool(kat.get("katalog")),
            "yuz": bool(kat.get("yuz")),
            "gomme": bool(kat.get("gomme")),
            "eslesme": bool(kat.get("eslesme")),
        },
        "sonraki": sonraki,
        "not": " ".join(notlar),
    }


def _next_layer(kat: dict[str, Any]) -> str:
    if not kat.get("katalog"):
        return "katalog"
    if not kat.get("yuz"):
        return "yuz"
    if not kat.get("gomme"):
        return "gomme"
    if not kat.get("eslesme"):
        return "eslesme"
    return "hazir"


def _load_catalog() -> dict[str, Any]:
    if not _CATALOG.is_file():
        return _empty_catalog()
    try:
        raw = json.loads(_CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_catalog()
    if not isinstance(raw, dict):
        return _empty_catalog()
    base = _empty_catalog()
    base.update({k: raw.get(k, base[k]) for k in base})
    if not isinstance(base.get("dosyalar"), list):
        base["dosyalar"] = []
    if not isinstance(base.get("katman"), dict):
        base["katman"] = _empty_catalog()["katman"]
    return base


def _save_catalog(data: dict[str, Any]) -> None:
    index_dir()
    tmp = _CATALOG.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
    tmp.replace(_CATALOG)


def _safe_root(kok: str) -> Path:
    text = (kok or "").strip()
    if not text:
        raise ValueError("Klasör yolu boş.")
    root = Path(text).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Klasör bulunamadı.")
    return root


def _file_hash(path: Path, *, nbytes: int = 256_000) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        chunk = f.read(nbytes)
        h.update(chunk)
        st = path.stat()
        h.update(str(st.st_size).encode("ascii"))
        h.update(str(int(st.st_mtime)).encode("ascii"))
    return h.hexdigest()[:24]


def katalog_tara(kok: str, *, limit: int = MAX_FILES) -> dict[str, Any]:
    """Katman 1: görselleri listele."""
    root = _safe_root(kok)
    lim = max(1, min(int(limit or MAX_FILES), MAX_FILES))
    found: list[dict[str, Any]] = []
    skipped = 0
    for dirpath, dirnames, filenames in os.walk(root):
        depth = Path(dirpath).relative_to(root).parts
        if len(depth) >= MAX_DEPTH:
            dirnames[:] = []
            continue
        dirnames[:] = [
            d
            for d in dirnames
            if not d.startswith(".") and d.lower() not in {"node_modules", "__pycache__"}
        ]
        for name in filenames:
            if len(found) >= lim:
                break
            ext = Path(name).suffix.lower()
            if ext not in IMAGE_EXT:
                continue
            path = Path(dirpath) / name
            try:
                st = path.stat()
                if st.st_size < 32 or st.st_size > 80_000_000:
                    skipped += 1
                    continue
                rel = str(path.relative_to(root)).replace("\\", "/")
                found.append(
                    {
                        "rel": rel,
                        "bytes": int(st.st_size),
                        "mtime": int(st.st_mtime),
                        "hash": _file_hash(path),
                        "ext": ext,
                    }
                )
            except OSError:
                skipped += 1
                continue
        if len(found) >= lim:
            break

    data = _empty_catalog()
    data["kok"] = str(root)
    data["guncelleme"] = int(time.time())
    data["dosya_sayisi"] = len(found)
    data["dosyalar"] = found
    data["katman"]["katalog"] = len(found) > 0
    data["katman"]["yuz"] = False
    data["katman"]["gomme"] = False
    data["katman"]["eslesme"] = False
    _save_catalog(data)
    for p in (_YUZ, _GOMME):
        try:
            if p.is_file():
                p.unlink()
        except OSError:
            pass
    return {
        "ok": True,
        "kok": str(root),
        "dosya_sayisi": len(found),
        "atlanan": skipped,
        "limit": lim,
        "katman": data["katman"],
        "sonraki": "yuz",
        "ornek": [f["rel"] for f in found[:12]],
        "not": (
            f"{len(found)} fotoğraf kataloglandı. "
            "Sıradaki katman: yüz algılama."
        ),
    }


def katalog_ornek(limit: int = 24) -> dict[str, Any]:
    data = _load_catalog()
    lim = max(1, min(int(limit or 24), 200))
    files = data.get("dosyalar") or []
    return {
        "ok": True,
        "kok": data.get("kok") or "",
        "dosya_sayisi": int(data.get("dosya_sayisi") or 0),
        "ornek": files[:lim],
        "katman": data.get("katman") or {},
    }


def coz_katalog_dosya(rel: str) -> Path:
    """Katalog kökü altındaki göreli yolu güvenli çöz (önizleme için)."""
    data = _load_catalog()
    kok = str(data.get("kok") or "").strip()
    if not kok:
        raise ValueError("Önce katalog tara.")
    root = Path(kok).resolve()
    if not root.is_dir():
        raise ValueError("Katalog kökü yok.")
    raw = str(rel or "").strip().replace("\\", "/")
    if not raw or raw.startswith("/") or ".." in raw.split("/"):
        raise ValueError("Geçersiz dosya yolu.")
    target = (root / raw.replace("/", os.sep)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Dosya katalog dışında.") from exc
    if not target.is_file():
        raise FileNotFoundError("Fotoğraf bulunamadı.")
    if target.suffix.lower() not in IMAGE_EXT:
        raise ValueError("Desteklenmeyen dosya türü.")
    return target


def referans_secilen_yol() -> Path:
    """Electron'un seçtiği referans kopyası."""
    if not _REF_FILE.is_file() or _REF_FILE.stat().st_size < 32:
        raise FileNotFoundError("Referans seçilmedi.")
    return _REF_FILE


def referans_secilen_meta() -> dict[str, Any]:
    if not _REF_META.is_file():
        return {"name": "referans.jpg", "mime": "image/jpeg"}
    try:
        data = json.loads(_REF_META.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return {"name": "referans.jpg", "mime": "image/jpeg"}


def _decode_image_bytes(raw: bytes):
    """Her türlü baytı BGR görüntüye çevir (OpenCV → PIL yedek)."""
    if not raw or len(raw) < 32:
        raise ValueError("Dosya boş veya çok küçük.")
    import numpy as np

    try:
        import cv2

        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is not None and getattr(img, "size", 0) > 0:
            return img
    except Exception:
        pass
    try:
        from io import BytesIO

        from PIL import Image

        im = Image.open(BytesIO(raw))
        im = im.convert("RGB")
        rgb = np.asarray(im)
        import cv2

        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as exc:
        raise ValueError(
            "Resim okunamadı. JPG/PNG/WEBP deneyin (HEIC ise Telefon’dan JPG kaydedin)."
        ) from exc


def referans_yaz_normalize(raw: bytes, name: str = "referans.jpg") -> dict[str, Any]:
    """Boyut/uzantı ne olursa olsun kutuya sığacak JPEG referans üret."""
    import cv2

    if len(raw) > REF_RAW_MAX_BYTES:
        raise ValueError("Dosya 80 MB üstü — daha küçük bir kopya dene.")
    img = _decode_image_bytes(raw)
    h, w = img.shape[:2]
    if h < 8 or w < 8:
        raise ValueError("Görüntü çok küçük.")
    scale = 1.0
    long_side = max(h, w)
    if long_side > REF_MAX_SIDE:
        scale = REF_MAX_SIDE / float(long_side)
        img = cv2.resize(
            img,
            (max(1, int(w * scale)), max(1, int(h * scale))),
            interpolation=cv2.INTER_AREA,
        )
    ok, enc = cv2.imencode(
        ".jpg",
        img,
        [int(cv2.IMWRITE_JPEG_QUALITY), REF_JPEG_QUALITY],
    )
    if not ok:
        raise ValueError("JPEG yazılamadı.")
    index_dir()
    data = enc.tobytes()
    tmp = _REF_FILE.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(_REF_FILE)
    stem = Path(str(name or "referans")).stem or "referans"
    meta = {
        "name": f"{stem}.jpg",
        "mime": "image/jpeg",
        "w": int(img.shape[1]),
        "h": int(img.shape[0]),
        "bytes": len(data),
        "normalized": True,
        "source_name": str(name or "")[:180],
    }
    _REF_META.write_text(json.dumps(meta, ensure_ascii=False, indent=0), encoding="utf-8")
    return {"ok": True, **meta}


def referans_hazirla_diskten() -> dict[str, Any]:
    """Electron'un kopyaladığı ham dosyayı normalize et."""
    path = referans_secilen_yol()
    meta = referans_secilen_meta()
    return referans_yaz_normalize(path.read_bytes(), str(meta.get("name") or path.name))


def _yunet_model_path() -> Path | None:
    env = (os.environ.get("RUZGAR_YUNET_MODEL") or "").strip()
    if env and Path(env).is_file():
        return Path(env)
    for name in _YUNET_NAMES:
        p = _DATA_DIR / name
        if p.is_file():
            return p
    return None


def _haar_cascade_path() -> Path | None:
    """opencv-python-headless bazen XML taşımaz; projedeki kopya öncelikli."""
    bundled = _DATA_DIR / "haarcascade_frontalface_default.xml"
    if bundled.is_file():
        return bundled
    try:
        import cv2

        pkg = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        if pkg.is_file():
            return pkg
    except Exception:
        pass
    env = (os.environ.get("RUZGAR_HAAR_CASCADE") or "").strip()
    if env and Path(env).is_file():
        return Path(env)
    return None


def _make_face_detector() -> tuple[str, Any]:
    """(motor, nesne) — OpenCV 5: YuNet; OpenCV 4: Haar.

    Not: Windows'ta Unicode yol (Ü/İ) ONNX okuyucuyu bozar → model bayt olarak yüklenir.
    """
    import cv2

    if hasattr(cv2, "FaceDetectorYN_create"):
        model = _yunet_model_path()
        if model is not None:
            raw = model.read_bytes()
            if len(raw) < 1000:
                raise RuntimeError(f"YuNet model bozuk: {model.name}")
            try:
                det = cv2.FaceDetectorYN_create(
                    "onnx",
                    raw,
                    b"",
                    (320, 320),
                    0.7,
                    0.3,
                    5000,
                )
            except Exception:
                # bazı sürümlerde buffer imzası farklı — ASCII geçici dosya
                import tempfile

                tmp = Path(tempfile.gettempdir()) / "ruzgar_face_yunet.onnx"
                tmp.write_bytes(raw)
                det = cv2.FaceDetectorYN_create(
                    str(tmp),
                    "",
                    (320, 320),
                    0.7,
                    0.3,
                    5000,
                )
            return "yunet", det
    if hasattr(cv2, "CascadeClassifier"):
        path = _haar_cascade_path()
        if path is not None:
            # Haar XML de Unicode yolda bozulabilir → ASCII kopya
            try:
                cascade = cv2.CascadeClassifier(str(path))
            except Exception:
                cascade = None
            if cascade is None or cascade.empty():
                import tempfile

                tmp = Path(tempfile.gettempdir()) / "ruzgar_haar_face.xml"
                tmp.write_bytes(path.read_bytes())
                cascade = cv2.CascadeClassifier(str(tmp))
            if not cascade.empty():
                return "haar", cascade
    raise RuntimeError(
        "Yüz algılayıcı yok. OpenCV 5 için "
        "ilim_assistant/data/face_detection_yunet_2023mar.onnx "
        "veya OpenCV 4 + Haar XML gerekli."
    )


def _read_bgr(path: Path):
    import cv2
    import numpy as np

    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size < 16:
        return None
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return img


def _detect_faces_bgr(img, detector_kind: str, detector) -> list[tuple[int, int, int, int]]:
    import cv2

    h, w = img.shape[:2]
    if detector_kind == "yunet":
        # büyük arşiv: uzun kenarı ~960
        scale = 1.0
        work = img
        if max(h, w) > 960:
            scale = 960.0 / float(max(h, w))
            work = cv2.resize(img, (int(w * scale), int(h * scale)))
        wh, ww = work.shape[:2]
        detector.setInputSize((ww, wh))
        _ok, faces = detector.detect(work)
        out: list[tuple[int, int, int, int]] = []
        if faces is None:
            return out
        inv = 1.0 / scale if scale else 1.0
        for row in faces[:MAX_FACES_PER_IMG]:
            x, y, fw, fh = float(row[0]), float(row[1]), float(row[2]), float(row[3])
            out.append(
                (
                    max(0, int(x * inv)),
                    max(0, int(y * inv)),
                    max(1, int(fw * inv)),
                    max(1, int(fh * inv)),
                )
            )
        return out

    # Haar
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    scale = 1.0
    if max(h, w) > 960:
        scale = 960.0 / float(max(h, w))
        gray_s = cv2.resize(gray, (int(w * scale), int(h * scale)))
    else:
        gray_s = gray
    faces = detector.detectMultiScale(
        gray_s,
        scaleFactor=1.12,
        minNeighbors=5,
        minSize=(48, 48),
        flags=getattr(cv2, "CASCADE_SCALE_IMAGE", 0),
    )
    out = []
    inv = 1.0 / scale if scale else 1.0
    for x, y, fw, fh in faces[:MAX_FACES_PER_IMG]:
        out.append(
            (
                int(x * inv),
                int(y * inv),
                int(fw * inv),
                int(fh * inv),
            )
        )
    return out


def yuz_tara(*, limit: int | None = None) -> dict[str, Any]:
    """Katman 2: katalogdaki fotoğraflarda yüz kutuları."""
    if not opencv_hazir():
        raise RuntimeError("OpenCV gerekli: pip install opencv-python-headless numpy")
    data = _load_catalog()
    if not data["katman"].get("katalog") or not data.get("kok"):
        raise ValueError("Önce katalog tara.")
    root = Path(data["kok"])
    if not root.is_dir():
        raise ValueError("Katalog kökü bulunamadı; yeniden tara.")
    det_kind, detector = _make_face_detector()
    files = list(data.get("dosyalar") or [])
    if limit is not None:
        files = files[: max(1, int(limit))]
    kayitlar: list[dict[str, Any]] = []
    yuz_toplam = 0
    hatali = 0
    t0 = time.time()
    for item in files:
        rel = str(item.get("rel") or "")
        path = root / rel.replace("/", os.sep)
        try:
            img = _read_bgr(path)
            if img is None:
                hatali += 1
                continue
            faces = _detect_faces_bgr(img, det_kind, detector)
            if not faces:
                kayitlar.append({"rel": rel, "hash": item.get("hash"), "faces": []})
                continue
            face_list = [{"x": x, "y": y, "w": w, "h": h} for x, y, w, h in faces]
            yuz_toplam += len(face_list)
            kayitlar.append({"rel": rel, "hash": item.get("hash"), "faces": face_list})
        except Exception:
            hatali += 1
            continue
    payload = {
        "schema": SCHEMA,
        "kok": str(root),
        "motor": det_kind,
        "guncelleme": int(time.time()),
        "dosya_sayisi": len(files),
        "yuz_sayisi": yuz_toplam,
        "hatali": hatali,
        "sure_sn": round(time.time() - t0, 2),
        "kayitlar": kayitlar,
    }
    index_dir()
    tmp = _YUZ.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")
    tmp.replace(_YUZ)
    data["katman"]["yuz"] = yuz_toplam > 0
    data["katman"]["gomme"] = False
    data["katman"]["eslesme"] = False
    data["guncelleme"] = int(time.time())
    _save_catalog(data)
    try:
        if _GOMME.is_file():
            _GOMME.unlink()
    except OSError:
        pass
    return {
        "ok": True,
        "yuz_sayisi": yuz_toplam,
        "dosya_sayisi": len(files),
        "yuzsuz": sum(1 for k in kayitlar if not k.get("faces")),
        "hatali": hatali,
        "sure_sn": payload["sure_sn"],
        "motor": det_kind,
        "katman": data["katman"],
        "sonraki": "gomme" if yuz_toplam > 0 else "yuz",
        "not": (
            f"{yuz_toplam} yüz bulundu ({len(files)} foto, {det_kind}). Sırada: gömme."
            if yuz_toplam
            else "Yüz bulunamadı. Farklı klasör / net yüz fotoğrafları dene."
        ),
    }


def _embed_face(gray_face) -> list[float]:
    import cv2
    import numpy as np

    face = cv2.resize(gray_face, (EMBED_SIZE, EMBED_SIZE), interpolation=cv2.INTER_AREA)
    face = face.astype(np.float32) / 255.0
    flat = face.reshape(-1)
    hist = cv2.calcHist([ (face * 255).astype(np.uint8) ], [0], None, [32], [0, 256])
    hist = hist.reshape(-1).astype(np.float32)
    hist = hist / (float(np.sum(hist)) + 1e-6)
    vec = np.concatenate([flat, hist])
    n = float(np.linalg.norm(vec))
    if n < 1e-8:
        return [0.0] * int(vec.size)
    vec = vec / n
    return [float(x) for x in vec.tolist()]


def gomme_kur() -> dict[str, Any]:
    """Katman 3: yüz kırpımlarından yerel gömme vektörleri."""
    if not opencv_hazir():
        raise RuntimeError("OpenCV gerekli: pip install opencv-python-headless numpy")
    import cv2

    data = _load_catalog()
    if not data["katman"].get("yuz"):
        raise ValueError("Önce yüz tara.")
    if not _YUZ.is_file():
        raise ValueError("Yüz indeksi yok; yüz tara.")
    yuz = json.loads(_YUZ.read_text(encoding="utf-8"))
    root = Path(str(yuz.get("kok") or data.get("kok") or ""))
    if not root.is_dir():
        raise ValueError("Kök klasör yok.")
    vektorler: list[dict[str, Any]] = []
    t0 = time.time()
    for kayit in yuz.get("kayitlar") or []:
        rel = str(kayit.get("rel") or "")
        faces = kayit.get("faces") or []
        if not faces:
            continue
        path = root / rel.replace("/", os.sep)
        img = _read_bgr(path)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gh, gw = gray.shape[:2]
        for i, f in enumerate(faces):
            x, y, w, h = int(f["x"]), int(f["y"]), int(f["w"]), int(f["h"])
            if w < 24 or h < 24:
                continue
            x2, y2 = min(gw, x + w), min(gh, y + h)
            x, y = max(0, x), max(0, y)
            crop = gray[y:y2, x:x2]
            if crop.size < 64:
                continue
            vec = _embed_face(crop)
            vektorler.append(
                {
                    "id": f"{rel}#{i}",
                    "rel": rel,
                    "face_i": i,
                    "box": {"x": x, "y": y, "w": w, "h": h},
                    "v": vec,
                }
            )
    payload = {
        "schema": SCHEMA,
        "kok": str(root),
        "guncelleme": int(time.time()),
        "vektor_sayisi": len(vektorler),
        "dim": len(vektorler[0]["v"]) if vektorler else 0,
        "sure_sn": round(time.time() - t0, 2),
        "vektorler": vektorler,
    }
    index_dir()
    tmp = _GOMME.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")
    tmp.replace(_GOMME)
    data["katman"]["gomme"] = len(vektorler) > 0
    data["katman"]["eslesme"] = len(vektorler) > 0
    data["guncelleme"] = int(time.time())
    _save_catalog(data)
    return {
        "ok": True,
        "vektor_sayisi": len(vektorler),
        "dim": payload["dim"],
        "sure_sn": payload["sure_sn"],
        "katman": data["katman"],
        "sonraki": "eslesme" if vektorler else "gomme",
        "not": (
            f"{len(vektorler)} yüz vektörü hazır. Referans fotoğraf bırakıp Yüz ara."
            if vektorler
            else "Gömme boş kaldı."
        ),
    }


def katman_kur(*, limit: int | None = None) -> dict[str, Any]:
    """Katalog varsa yuz → gömme sırayla."""
    st = durum()
    if not st["katman"]["katalog"]:
        raise ValueError("Önce katalog tara.")
    ozet: list[dict[str, Any]] = []
    if not st["katman"]["yuz"]:
        y = yuz_tara(limit=limit)
        ozet.append({"katman": "yuz", "yuz_sayisi": y.get("yuz_sayisi"), "not": y.get("not")})
    if not durum()["katman"]["gomme"]:
        g = gomme_kur()
        ozet.append({"katman": "gomme", "vektor_sayisi": g.get("vektor_sayisi"), "not": g.get("not")})
    st2 = durum()
    if not ozet:
        ozet = [{"katman": "hazir", "not": "Yüz ve gömme zaten hazır."}]
    return {
        "ok": True,
        "adimlar": ozet,
        "katman": st2["katman"],
        "sonraki": st2["sonraki"],
        "not": st2["not"],
        "yuz_sayisi": st2["yuz_sayisi"],
        "vektor_sayisi": st2["vektor_sayisi"],
    }


def _cosine(a: list[float], b: list[float]) -> float:
    import numpy as np

    va = np.asarray(a, dtype=np.float32)
    vb = np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom < 1e-8:
        return 0.0
    return float(np.dot(va, vb) / denom)


def eslestir_bytes(
    raw: bytes,
    *,
    referans_adi: str = "",
    top_k: int = MATCH_TOP,
) -> dict[str, Any]:
    """Katman 4: referans görsel → kütüphanede en yakın yüzler."""
    st = durum()
    if not st["katman"]["katalog"]:
        return {
            "ok": False,
            "handled": True,
            "katman_hazir": False,
            "sonraki": "katalog",
            "reply": "Önce fotoğraf klasörünü tara (katalog).",
            "sonuclar": [],
        }
    if not st["katman"]["yuz"]:
        return {
            "ok": False,
            "handled": True,
            "katman_hazir": False,
            "sonraki": "yuz",
            "reply": "Önce yüz tara (katman 2).",
            "sonuclar": [],
        }
    if not st["katman"]["gomme"] or not _GOMME.is_file():
        return {
            "ok": False,
            "handled": True,
            "katman_hazir": False,
            "sonraki": "gomme",
            "reply": "Önce gömme kur (katman 3).",
            "sonuclar": [],
        }
    if not opencv_hazir():
        return {
            "ok": False,
            "handled": True,
            "katman_hazir": False,
            "sonraki": "yuz",
            "reply": "OpenCV yok: pip install opencv-python-headless numpy",
            "sonuclar": [],
        }
    import cv2
    import numpy as np

    if not raw or len(raw) < 32:
        return {
            "ok": False,
            "handled": True,
            "katman_hazir": True,
            "reply": "Referans görsel boş.",
            "sonuclar": [],
        }
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {
            "ok": False,
            "handled": True,
            "katman_hazir": True,
            "reply": "Referans görsel okunamadı.",
            "sonuclar": [],
        }
    det_kind, detector = _make_face_detector()
    faces = _detect_faces_bgr(img, det_kind, detector)
    if not faces:
        return {
            "ok": False,
            "handled": True,
            "katman_hazir": True,
            "reply": "Referansta yüz bulunamadı. Net, önden yüz dene.",
            "sonuclar": [],
        }
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    x, y, w, h = faces[0]
    crop = gray[y : y + h, x : x + w]
    ref_vec = _embed_face(crop)
    gomme = json.loads(_GOMME.read_text(encoding="utf-8"))
    skorlar: list[tuple[float, dict[str, Any]]] = []
    for item in gomme.get("vektorler") or []:
        v = item.get("v")
        if not isinstance(v, list) or not v:
            continue
        sc = _cosine(ref_vec, v)
        skorlar.append((sc, item))
    skorlar.sort(key=lambda t: t[0], reverse=True)
    k = max(1, min(int(top_k or MATCH_TOP), 50))
    # en iyi skor dosya başına bir kez
    seen: set[str] = set()
    sonuclar: list[dict[str, Any]] = []
    for sc, item in skorlar:
        if sc < MATCH_MIN_SCORE:
            break
        rel = str(item.get("rel") or "")
        if not rel or rel in seen:
            continue
        seen.add(rel)
        sonuclar.append(
            {
                "rel": rel,
                "skor": round(sc, 4),
                "box": item.get("box"),
                "id": item.get("id"),
            }
        )
        if len(sonuclar) >= k:
            break
    ad = (referans_adi or "").strip()[:180]
    if not sonuclar:
        return {
            "ok": True,
            "handled": True,
            "katman_hazir": True,
            "referans": ad,
            "referans_yuz": 1,
            "sonuclar": [],
            "reply": (
                "Eşik üstü eşleşme yok (yerel görünüm gömmesi). "
                "Daha net referans veya aynı kişinin daha çok fotoğrafı dene."
            ),
        }
    return {
        "ok": True,
        "handled": True,
        "katman_hazir": True,
        "referans": ad,
        "referans_yuz": len(faces),
        "sonuclar": sonuclar,
        "reply": (
            f"{len(sonuclar)} aday bulundu (yerel yüz + görünüm gömmesi). "
            f"En yüksek skor: {sonuclar[0]['skor']}."
        ),
    }


def eslestir_istem(referans_adi: str = "") -> dict[str, Any]:
    """Yerel yol varsa eşleştir; yoksa durum (uydurma sonuç yok)."""
    st = durum()
    ad = (referans_adi or "").strip()[:420]
    if not st["katman"]["katalog"]:
        return {
            "ok": False,
            "handled": True,
            "katman_hazir": False,
            "sonraki": "katalog",
            "reply": "Önce fotoğraf klasörünü tara (katalog).",
            "sonuclar": [],
        }
    if not st["katman"]["yuz"] or not st["katman"]["gomme"]:
        return {
            "ok": False,
            "handled": True,
            "katman_hazir": False,
            "sonraki": st["sonraki"],
            "referans": ad[:180],
            "katalog_sayisi": st["dosya_sayisi"],
            "reply": (
                f"Katalogda {st['dosya_sayisi']} foto var. "
                f"Sıradaki katman: {st['sonraki']}. "
                "«Katmanları kur» veya Yüz tara → Gömme kur."
            ),
            "sonuclar": [],
        }
    # Yerel dosya yolu verildiyse gerçek eşleşme
    if ad:
        p = Path(ad)
        if p.is_file() and p.suffix.lower() in IMAGE_EXT:
            try:
                raw = p.read_bytes()
            except OSError:
                raw = b""
            if raw:
                return eslestir_bytes(raw, referans_adi=p.name)
    return {
        "ok": False,
        "handled": True,
        "katman_hazir": True,
        "sonraki": "eslesme",
        "referans": ad[:180],
        "reply": "Referans fotoğrafı yükle / bırak, sonra Yüz ara.",
        "sonuclar": [],
    }
