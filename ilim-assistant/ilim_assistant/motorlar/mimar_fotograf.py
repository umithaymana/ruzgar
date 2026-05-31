"""
Mimar — Fotoğraf stüdyosu (Faz 4F-1 moderasyon, 4F-2 restorasyon, 4F-3 ses).
Pillow zorunlu; OpenCV isteğe bağlı; OCR için pytesseract+tesseract.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_MIMAR = "Ümit & Gökçenur"
_FOTO_SUB = "ilim-assistant/arsiv/mimar-fotograf"
_MAX_BYTES = 25_000_000
_IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2].parent


def foto_dir(repo_root: Path | None = None) -> Path:
    root = (repo_root or _repo_root()).resolve()
    d = root / "ilim-assistant" / "arsiv" / "mimar-fotograf"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _catalog_path(repo_root: Path | None = None) -> Path:
    return foto_dir(repo_root) / "_catalog.json"


def _load_catalog(repo_root: Path | None = None) -> dict[str, Any]:
    p = _catalog_path(repo_root)
    if not p.is_file():
        return {"version": 1, "items": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "items": []}


def _save_catalog(data: dict[str, Any], repo_root: Path | None = None) -> None:
    p = _catalog_path(repo_root)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_name(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9._\-]+", "_", (name or "foto").strip()).strip("._")
    return base[:120] or "foto"


def resolve_foto_rel(rel: str, repo_root: Path | None = None) -> Path:
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw.startswith(_FOTO_SUB):
        raise ValueError("Yalnızca mimar-fotograf arşivi.")
    root = (repo_root or _repo_root()).resolve()
    target = (root / raw.replace("/", os.sep)).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError("Geçersiz yol.") from None
    foto_base = foto_dir(repo_root).resolve()
    try:
        target.relative_to(foto_base)
    except ValueError:
        raise ValueError("Dosya mimar-fotograf dışında.") from None
    if not target.is_file():
        raise FileNotFoundError("Dosya yok.")
    return target


def opencv_available() -> bool:
    if os.environ.get("RUZGAR_OPENCV", "1").strip().lower() in ("0", "false", "no"):
        return False
    try:
        import cv2  # noqa: F401

        return True
    except ImportError:
        return False


def pillow_available() -> bool:
    try:
        from PIL import Image  # noqa: F401

        return True
    except ImportError:
        return False


def _open_image(path: Path):
    from PIL import Image

    img = Image.open(path)
    img.load()
    return img


def _save_image(img, path: Path, *, quality: int = 92) -> Path:
    out = img.convert("RGB") if img.mode not in ("RGB", "L") else img
    if out.mode == "L":
        out = out.convert("RGB")
    ext = path.suffix.lower()
    out_path = path
    if ext in (".jpg", ".jpeg"):
        out.save(out_path, format="JPEG", quality=quality, optimize=True)
    elif ext == ".png":
        out.save(out_path, format="PNG", optimize=True)
    else:
        out_path = path.with_suffix(".jpg")
        out.save(out_path, format="JPEG", quality=quality, optimize=True)
    return out_path


def _backup_original(path: Path) -> None:
    bak = path.with_name(path.stem + "._original" + path.suffix)
    if not bak.is_file() and path.is_file():
        shutil.copy2(path, bak)


def capabilities() -> dict[str, Any]:
    return {
        "ok": True,
        "pillow": pillow_available(),
        "opencv": opencv_available(),
        "mimarlar": _MIMAR,
        "moderation_ops": [
            "rotate_left",
            "rotate_right",
            "rotate_180",
            "preset_auto",
            "preset_bright",
            "preset_contrast",
            "preset_sharp",
            "preset_bw",
            "crop_square",
            "exposure_up",
            "exposure_down",
        ],
        "restoration_ops": [
            "restore_fade",
            "restore_vintage",
            "restore_denoise",
            "restore_scratches",
            "restore_sharpen",
            "restore_upscale",
            "restore_full",
        ],
        "voice_modes": ["read", "speak"],
        "ocr": ocr_available(),
        "max_bytes": _MAX_BYTES,
    }


def upload_bytes(data: bytes, filename: str, repo_root: Path | None = None) -> dict[str, Any]:
    if not data:
        raise ValueError("Boş dosya.")
    if len(data) > _MAX_BYTES:
        raise ValueError(f"Dosya çok büyük ({_MAX_BYTES // 1_000_000} MB sınırı).")
    if not pillow_available():
        raise RuntimeError("Pillow kurulu değil: pip install pillow")

    from PIL import Image

    d = foto_dir(repo_root)
    stem = _safe_name(Path(filename or "foto").stem)
    fid = uuid.uuid4().hex[:10]
    rel_name = f"{fid}_{stem}.jpg"
    target = d / rel_name

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:
        raise ValueError(f"Görüntü açılamadı: {e}") from e

    w, h = img.size
    _save_image(img, target)
    root = (repo_root or _repo_root()).resolve()
    rel = target.relative_to(root).as_posix()

    cat = _load_catalog(repo_root)
    items: list[dict[str, Any]] = list(cat.get("items") or [])
    entry = {
        "id": fid,
        "rel": rel,
        "name": filename or rel_name,
        "width": w,
        "height": h,
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    items = [x for x in items if x.get("rel") != rel] + [entry]
    cat["items"] = items[-200:]
    _save_catalog(cat, repo_root)

    return {"ok": True, "item": entry, "rel": rel, "bytes": len(data)}


def list_photos(repo_root: Path | None = None) -> dict[str, Any]:
    cat = _load_catalog(repo_root)
    items = list(cat.get("items") or [])
    d = foto_dir(repo_root)
    known = {x.get("rel") for x in items}
    root = (repo_root or _repo_root()).resolve()
    for p in sorted(d.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if p.name.startswith("_"):
            continue
        if p.suffix.lower() not in _IMAGE_EXTS:
            continue
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            continue
        if rel in known:
            continue
        try:
            from PIL import Image

            with Image.open(p) as im:
                w, h = im.size
        except Exception:
            w, h = 0, 0
        items.append(
            {
                "id": p.stem.split("_")[0][:10],
                "rel": rel,
                "name": p.name,
                "width": w,
                "height": h,
                "updated": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    items.sort(key=lambda x: x.get("updated") or "", reverse=True)
    return {"ok": True, "items": items[:200], "pillow": pillow_available(), "opencv": opencv_available()}


def _to_rgb(img):
    return img.convert("RGB") if img.mode != "RGB" else img


def _restore_fade(img):
    from PIL import Image, ImageEnhance, ImageOps

    rgb = _to_rgb(img)
    r, g, b = rgb.split()
    b = ImageEnhance.Brightness(b).enhance(1.1)
    g = ImageEnhance.Brightness(g).enhance(1.03)
    rgb = Image.merge("RGB", (r, g, b))
    rgb = ImageOps.autocontrast(rgb, cutoff=1)
    return ImageEnhance.Color(rgb).enhance(1.1)


def _restore_vintage(img):
    from PIL import ImageEnhance, ImageFilter

    rgb = _restore_fade(img)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.1)
    return rgb.filter(ImageFilter.UnsharpMask(radius=1.6, percent=110, threshold=3))


def _restore_denoise(img):
    if opencv_available():
        import cv2
        import numpy as np
        from PIL import Image

        arr = np.array(_to_rgb(img))
        den = cv2.fastNlMeansDenoisingColored(arr, None, 5, 5, 7, 21)
        return Image.fromarray(den)
    from PIL import ImageFilter

    return img.filter(ImageFilter.MedianFilter(size=3))


def _restore_scratches(img):
    if opencv_available():
        import cv2
        import numpy as np
        from PIL import Image

        arr = np.array(_to_rgb(img))
        out = cv2.medianBlur(arr, 3)
        out = cv2.bilateralFilter(out, 7, 50, 50)
        return Image.fromarray(out)
    from PIL import ImageFilter

    return img.filter(ImageFilter.MedianFilter(size=5))


def _restore_sharpen(img):
    from PIL import ImageFilter

    return _to_rgb(img).filter(ImageFilter.UnsharpMask(radius=2.0, percent=130, threshold=2))


def _restore_upscale(img):
    from PIL import Image

    w, h = img.size
    nw, nh = w * 2, h * 2
    cap = 4096
    if max(nw, nh) > cap:
        ratio = cap / max(nw, nh)
        nw, nh = int(nw * ratio), int(nh * ratio)
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def _restore_full(img):
    out = _restore_denoise(img)
    out = _restore_fade(out)
    out = _restore_sharpen(out)
    return out


def _apply_restoration_op(img, op: str):
    o = (op or "").strip().lower()
    if o in ("restore_fade", "fade", "soluk"):
        return _restore_fade(img), o
    if o in ("restore_vintage", "vintage", "eski"):
        return _restore_vintage(img), o
    if o in ("restore_denoise", "denoise", "gurultu"):
        return _restore_denoise(img), o
    if o in ("restore_scratches", "scratches", "cizik"):
        return _restore_scratches(img), o
    if o in ("restore_sharpen", "deblur"):
        return _restore_sharpen(img), o
    if o in ("restore_upscale", "upscale", "buyut"):
        return _restore_upscale(img), o
    if o in ("restore_full", "full", "tam"):
        return _restore_full(img), o
    raise ValueError(f"Bilinmeyen restorasyon: {op}")


def _catalog_touch(rel_out: str, path: Path, w: int, h: int, repo_root: Path | None) -> None:
    cat = _load_catalog(repo_root)
    items: list[dict[str, Any]] = list(cat.get("items") or [])
    for it in items:
        if it.get("rel") == rel_out:
            it["width"] = w
            it["height"] = h
            it["updated"] = datetime.now(timezone.utc).isoformat()
            break
    else:
        items.append(
            {
                "id": path.stem.split("_")[0][:10],
                "rel": rel_out,
                "name": path.name,
                "width": w,
                "height": h,
                "updated": datetime.now(timezone.utc).isoformat(),
            }
        )
    cat["items"] = items
    _save_catalog(cat, repo_root)


def _commit_image(path: Path, img, op: str, repo_root: Path | None) -> dict[str, Any]:
    saved = _save_image(img, path)
    w, h = img.size
    root = (repo_root or _repo_root()).resolve()
    rel_out = saved.relative_to(root).as_posix()
    _catalog_touch(rel_out, saved, w, h, repo_root)
    return {
        "ok": True,
        "rel": rel_out,
        "op": op,
        "width": w,
        "height": h,
        "label_tr": _op_label(op),
    }


def apply_restoration(rel: str, op: str, repo_root: Path | None = None) -> dict[str, Any]:
    if not pillow_available():
        raise RuntimeError("Pillow kurulu değil: pip install pillow")
    path = resolve_foto_rel(rel, repo_root)
    _backup_original(path)
    img = _open_image(path)
    out, o = _apply_restoration_op(img, op)
    return _commit_image(path, out, o, repo_root)


def preview_restoration(rel: str, op: str, repo_root: Path | None = None) -> dict[str, Any]:
    """Kaydetmeden JPEG önizleme (base64)."""
    if not pillow_available():
        raise RuntimeError("Pillow kurulu değil: pip install pillow")
    path = resolve_foto_rel(rel, repo_root)
    img = _open_image(path)
    out, o = _apply_restoration_op(img, op)
    buf = io.BytesIO()
    _to_rgb(out).save(buf, format="JPEG", quality=85, optimize=True)
    import base64

    w, h = out.size
    return {
        "ok": True,
        "op": o,
        "width": w,
        "height": h,
        "label_tr": _op_label(o),
        "preview_b64": base64.b64encode(buf.getvalue()).decode("ascii"),
        "opencv_used": opencv_available()
        and o in ("restore_denoise", "restore_scratches", "restore_full"),
    }


def apply_moderation(rel: str, op: str, repo_root: Path | None = None) -> dict[str, Any]:
    if not pillow_available():
        raise RuntimeError("Pillow kurulu değil: pip install pillow")
    path = resolve_foto_rel(rel, repo_root)
    _backup_original(path)

    from PIL import ImageEnhance, ImageFilter, ImageOps

    img = _open_image(path)
    o = (op or "").strip().lower()

    if o in ("rotate_left", "rot_left", "left"):
        img = img.rotate(90, expand=True)
    elif o in ("rotate_right", "rot_right", "right"):
        img = img.rotate(-90, expand=True)
    elif o in ("rotate_180", "flip"):
        img = img.rotate(180, expand=True)
    elif o in ("preset_auto", "auto"):
        img = ImageOps.autocontrast(img.convert("RGB"))
    elif o in ("preset_bright", "bright"):
        img = ImageEnhance.Brightness(img).enhance(1.18)
    elif o in ("preset_contrast", "contrast"):
        img = ImageEnhance.Contrast(img).enhance(1.22)
    elif o in ("preset_sharp", "sharp"):
        img = img.filter(ImageFilter.SHARPEN)
    elif o in ("preset_bw", "bw", "grayscale"):
        img = img.convert("L").convert("RGB")
    elif o in ("crop_square", "square"):
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
    elif o in ("exposure_up", "brighter"):
        img = ImageEnhance.Brightness(img).enhance(1.08)
        img = ImageEnhance.Contrast(img).enhance(1.05)
    elif o in ("exposure_down", "darker"):
        img = ImageEnhance.Brightness(img).enhance(0.92)
    else:
        raise ValueError(f"Bilinmeyen işlem: {op}")

    return _commit_image(path, img, o, repo_root)


def _op_label(op: str) -> str:
    labels = {
        "rotate_left": "90° sola döndürüldü",
        "rotate_right": "90° sağa döndürüldü",
        "rotate_180": "180° döndürüldü",
        "preset_auto": "Otomatik denge",
        "preset_bright": "Parlaklık artırıldı",
        "preset_contrast": "Kontrast artırıldı",
        "preset_sharp": "Keskinleştirildi",
        "preset_bw": "Siyah-beyaz",
        "crop_square": "Kare kırpıldı",
        "exposure_up": "Pozlama açıldı",
        "exposure_down": "Pozlama kapatıldı",
        "restore_fade": "Soluk renk düzeltildi",
        "restore_vintage": "Eski foto tonu yenilendi",
        "restore_denoise": "Gürültü azaltıldı",
        "restore_scratches": "Çizik/leke yumuşatıldı",
        "restore_sharpen": "Netlik artırıldı",
        "restore_upscale": "2× büyütüldü (LANCZOS)",
        "restore_full": "Tam restorasyon uygulandı",
    }
    return labels.get(op, op)


def restore_original(rel: str, repo_root: Path | None = None) -> dict[str, Any]:
    path = resolve_foto_rel(rel, repo_root)
    bak = path.with_name(path.stem + "._original" + path.suffix)
    if not bak.is_file():
        raise FileNotFoundError("Orijinal yedek yok.")
    shutil.copy2(bak, path)
    img = _open_image(path)
    w, h = img.size
    _catalog_touch(rel, path, w, h, repo_root)
    return {"ok": True, "rel": rel, "width": w, "height": h, "label_tr": "Orijinal geri yüklendi"}


def ocr_available() -> bool:
    try:
        from PIL import Image  # noqa: F401
        import pytesseract  # noqa: F401

        return True
    except ImportError:
        return False


def _clean_ocr_text(text: str) -> str:
    t = (text or "").strip()
    if not t or t == "[OCR boş sonuç verdi]":
        return ""
    return t


def _strip_dinamit_summary(summary: str) -> str:
    s = (summary or "").strip()
    s = re.sub(r"\[DİNAMİT[^\]]*\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\[/DİNAMİT\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def ocr_photo(rel: str, repo_root: Path | None = None, lang: str = "tur+eng") -> dict[str, Any]:
    if not ocr_available():
        raise RuntimeError("OCR için: pip install pillow pytesseract ve Tesseract OCR kurulumu.")
    path = resolve_foto_rel(rel, repo_root)
    from PIL import Image
    import pytesseract

    img = _open_image(path)
    tess_lang = (lang or "tur+eng").strip()
    try:
        txt = pytesseract.image_to_string(img, lang=tess_lang)
    except Exception as e:
        raise ValueError(f"OCR başarısız: {e}") from e
    text = _clean_ocr_text(txt)
    hard_cap = 12_000
    truncated = False
    if len(text) > hard_cap:
        text = text[:hard_cap] + "\n\n… (kısaltıldı)"
        truncated = True
    return {
        "ok": True,
        "text": text,
        "empty": not bool(text),
        "lang": tess_lang,
        "truncated": truncated,
        "label_tr": "Metin çıkarıldı" if text else "OCR metin bulamadı",
    }


def _vision_summary(rel: str, repo_root: Path | None = None) -> str:
    path = resolve_foto_rel(rel, repo_root)
    from ilim_assistant.dinamit_vision import analyze_image_bytes

    raw = path.read_bytes()
    if len(raw) > _MAX_BYTES:
        raise ValueError("Görsel çok büyük.")
    info = analyze_image_bytes(raw)
    if not info.get("ok"):
        return str(info.get("summary") or "Görsel açıklanamadı.")
    return _strip_dinamit_summary(str(info.get("summary") or ""))


def prepare_voice_text(rel: str, mode: str, repo_root: Path | None = None) -> dict[str, Any]:
    m = (mode or "read").strip().lower()
    if m not in ("read", "speak", "oku", "konus", "konustur"):
        raise ValueError("mode: read veya speak")

    ocr_text = ""
    ocr_ok = False
    ocr_err = ""
    if ocr_available():
        try:
            oc = ocr_photo(rel, repo_root)
            ocr_text = str(oc.get("text") or "")
            ocr_ok = not oc.get("empty")
        except Exception as e:
            ocr_err = str(e)
    else:
        ocr_err = "OCR kurulu değil (pytesseract + Tesseract)."

    if m in ("read", "oku"):
        if ocr_ok:
            return {
                "ok": True,
                "mode": "read",
                "source": "ocr",
                "text": ocr_text,
                "label_tr": "Fotoğraftaki metin okunacak",
            }
        vision = _vision_summary(rel, repo_root)
        if vision:
            return {
                "ok": True,
                "mode": "read",
                "source": "vision",
                "text": vision,
                "label_tr": "Yazı yok — görsel betimlemesi okunacak",
                "ocr_note": ocr_err or "OCR boş",
            }
        raise ValueError(ocr_err or "Ne OCR ne görsel betimlemesi üretilemedi.")

    # speak / konuştur
    if ocr_ok:
        speech = f"Ümit abi, fotoğraftaki yazıyı okuyorum.\n\n{ocr_text}"
        return {
            "ok": True,
            "mode": "speak",
            "source": "ocr",
            "text": speech,
            "label_tr": "Fotoğraf yazısı konuşturulacak",
        }
    vision = _vision_summary(rel, repo_root)
    if vision:
        speech = f"Ümit abi, bu fotoğraf hakkında konuşuyorum.\n\n{vision}"
        return {
            "ok": True,
            "mode": "speak",
            "source": "vision",
            "text": speech,
            "label_tr": "Fotoğraf betimlemesi konuşturulacak",
            "ocr_note": ocr_err or "OCR boş",
        }
    raise ValueError(ocr_err or "Konuşturma metni üretilemedi.")
