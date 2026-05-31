"""
Mimar — Resim · Sanat galerisi (Faz 4S-1 arşiv, 4S-2 tanıma, 4S-3 eskiz katmanı).
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_MIMAR = "Ümit & Gökçenur"
_SANAT_SUB = "ilim-assistant/arsiv/mimar-sanat"
_MAX_BYTES = 25_000_000
_IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2].parent


def sanat_dir(repo_root: Path | None = None) -> Path:
    root = (repo_root or _repo_root()).resolve()
    d = root / "ilim-assistant" / "arsiv" / "mimar-sanat"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _catalog_path(repo_root: Path | None = None) -> Path:
    return sanat_dir(repo_root) / "_catalog.json"


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
    base = re.sub(r"[^a-zA-Z0-9._\-]+", "_", (name or "eser").strip()).strip("._")
    return base[:120] or "eser"


def resolve_sanat_rel(rel: str, repo_root: Path | None = None) -> Path:
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw.startswith(_SANAT_SUB):
        raise ValueError("Yalnızca mimar-sanat arşivi.")
    root = (repo_root or _repo_root()).resolve()
    target = (root / raw.replace("/", os.sep)).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError("Geçersiz yol.") from None
    sanat_base = sanat_dir(repo_root).resolve()
    try:
        target.relative_to(sanat_base)
    except ValueError:
        raise ValueError("Dosya mimar-sanat dışında.") from None
    if not target.is_file():
        raise FileNotFoundError("Dosya yok.")
    return target


def pillow_available() -> bool:
    try:
        from PIL import Image  # noqa: F401

        return True
    except ImportError:
        return False


def gemini_available() -> bool:
    try:
        from ilim_assistant.llm_gemini import gemini_configured

        return gemini_configured()
    except Exception:
        return False


def opencv_available() -> bool:
    if os.environ.get("RUZGAR_OPENCV", "1").strip().lower() in ("0", "false", "no"):
        return False
    try:
        import cv2  # noqa: F401

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


def _entry_defaults(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry.get("id") or "",
        "rel": entry.get("rel") or "",
        "name": entry.get("name") or "",
        "title": entry.get("title") or "",
        "artist": entry.get("artist") or "",
        "period": entry.get("period") or "",
        "technique": entry.get("technique") or "",
        "notes": entry.get("notes") or "",
        "identify_summary": entry.get("identify_summary") or "",
        "identify_source": entry.get("identify_source") or "",
        "identify_confidence": entry.get("identify_confidence") or "",
        "identify_at": entry.get("identify_at") or "",
        "identify_report": entry.get("identify_report") if isinstance(entry.get("identify_report"), dict) else {},
        "sketch_commands": entry.get("sketch_commands") if isinstance(entry.get("sketch_commands"), list) else [],
        "sketch_svg_rel": entry.get("sketch_svg_rel") or "",
        "sketch_source": entry.get("sketch_source") or "",
        "sketch_width": entry.get("sketch_width") or 0,
        "sketch_height": entry.get("sketch_height") or 0,
        "sketch_at": entry.get("sketch_at") or "",
        "copy_rel": entry.get("copy_rel") or "",
        "copy_mode": entry.get("copy_mode") or "",
        "copy_at": entry.get("copy_at") or "",
        "width": entry.get("width") or 0,
        "height": entry.get("height") or 0,
        "updated": entry.get("updated") or "",
    }


def capabilities() -> dict[str, Any]:
    return {
        "ok": True,
        "pillow": pillow_available(),
        "gemini": gemini_available(),
        "mimarlar": _MIMAR,
        "meta_fields": ["title", "artist", "period", "technique", "notes"],
        "analyze_depths": ["quick", "deep"],
        "sketch": True,
        "copy_modes": ["trace", "poster", "pencil"],
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

    d = sanat_dir(repo_root)
    stem = _safe_name(Path(filename or "eser").stem)
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
    entry = _entry_defaults(
        {
            "id": fid,
            "rel": rel,
            "name": filename or rel_name,
            "title": stem.replace("_", " "),
            "width": w,
            "height": h,
            "updated": datetime.now(timezone.utc).isoformat(),
        }
    )
    items = [x for x in items if x.get("rel") != rel] + [entry]
    cat["items"] = items[-300:]
    _save_catalog(cat, repo_root)

    return {"ok": True, "item": entry, "rel": rel, "bytes": len(data)}


def list_works(repo_root: Path | None = None) -> dict[str, Any]:
    cat = _load_catalog(repo_root)
    items = [_entry_defaults(x) for x in list(cat.get("items") or []) if isinstance(x, dict)]
    d = sanat_dir(repo_root)
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
            img = _open_image(p)
            w, h = img.size
        except Exception:
            w, h = 0, 0
        fid = p.stem.split("_")[0][:10] if "_" in p.stem else p.stem[:10]
        items.append(
            _entry_defaults(
                {
                    "id": fid or uuid.uuid4().hex[:10],
                    "rel": rel,
                    "name": p.name,
                    "title": p.stem,
                    "width": w,
                    "height": h,
                    "updated": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        )
    items.sort(key=lambda x: x.get("updated") or "", reverse=True)
    return {"ok": True, "items": items[:300], "pillow": pillow_available(), "gemini": gemini_available()}


def get_work(rel: str, repo_root: Path | None = None) -> dict[str, Any]:
    resolve_sanat_rel(rel, repo_root)
    cat = _load_catalog(repo_root)
    for x in cat.get("items") or []:
        if isinstance(x, dict) and x.get("rel") == rel:
            return {"ok": True, "item": _entry_defaults(x)}
    return {
        "ok": True,
        "item": _entry_defaults({"rel": rel, "name": Path(rel).name, "id": Path(rel).stem[:10]}),
    }


def update_metadata(
    rel: str,
    *,
    title: str | None = None,
    artist: str | None = None,
    period: str | None = None,
    technique: str | None = None,
    notes: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    resolve_sanat_rel(rel, repo_root)
    cat = _load_catalog(repo_root)
    items: list[dict[str, Any]] = list(cat.get("items") or [])
    found = False
    entry: dict[str, Any] = {}
    for i, x in enumerate(items):
        if isinstance(x, dict) and x.get("rel") == rel:
            entry = dict(x)
            found = True
            break
    if not found:
        entry = {"rel": rel, "name": Path(rel).name, "id": Path(rel).stem.split("_")[0][:10]}
    if title is not None:
        entry["title"] = str(title).strip()[:240]
    if artist is not None:
        entry["artist"] = str(artist).strip()[:240]
    if period is not None:
        entry["period"] = str(period).strip()[:240]
    if technique is not None:
        entry["technique"] = str(technique).strip()[:240]
    if notes is not None:
        entry["notes"] = str(notes).strip()[:12_000]
    entry["updated"] = datetime.now(timezone.utc).isoformat()
    entry = _entry_defaults(entry)
    items = [x for x in items if not (isinstance(x, dict) and x.get("rel") == rel)] + [entry]
    cat["items"] = items[-300:]
    _save_catalog(cat, repo_root)
    return {"ok": True, "item": entry, "label_tr": "Eser bilgisi kaydedildi"}


def _mime_for_path(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    if ext == ".gif":
        return "image/gif"
    return "image/jpeg"


def _image_bytes_for_gemini(path: Path) -> tuple[bytes, str]:
    raw = path.read_bytes()
    if len(raw) > _MAX_BYTES:
        raise ValueError("Görsel çok büyük.")
    mime = _mime_for_path(path)
    if path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        img = _open_image(path)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=90, optimize=True)
        return buf.getvalue(), "image/jpeg"
    return raw, mime


def _parse_identify_json(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return _normalize_report(obj)
        except json.JSONDecodeError:
            pass
    return _normalize_report({"summary": raw[:4000]})


def _as_str_list(val: Any) -> list[str]:
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()][:8]
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return []


def _normalize_report(obj: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": str(obj.get("title") or obj.get("baslik") or "").strip()[:240],
        "artist": str(obj.get("artist") or obj.get("sanatci") or "").strip()[:240],
        "period": str(obj.get("period") or obj.get("donem") or "").strip()[:240],
        "technique": str(obj.get("technique") or obj.get("teknik") or "").strip()[:240],
        "style": str(obj.get("style") or obj.get("stil") or "").strip()[:240],
        "movement": str(obj.get("movement") or obj.get("akim") or "").strip()[:240],
        "composition": str(obj.get("composition") or obj.get("kompozisyon") or "").strip()[:500],
        "color_palette": str(obj.get("color_palette") or obj.get("renk_paleti") or "").strip()[:240],
        "subject": str(obj.get("subject") or obj.get("konu") or "").strip()[:240],
        "confidence": str(obj.get("confidence") or obj.get("guven") or "").strip()[:40],
        "is_likely_original": str(
            obj.get("is_likely_original") or obj.get("orijinal_mi") or ""
        ).strip()[:40],
        "similar_artists": _as_str_list(obj.get("similar_artists") or obj.get("benzer_sanatcilar")),
        "historical_context": str(
            obj.get("historical_context") or obj.get("tarihsel_baglam") or ""
        ).strip()[:1200],
        "viewing_tips": str(obj.get("viewing_tips") or obj.get("inceleme_ipuclari") or "").strip()[:800],
        "summary": str(obj.get("summary") or obj.get("ozet") or "").strip()[:4000],
    }


def _report_to_notes(report: dict[str, Any]) -> str:
    lines: list[str] = []
    if report.get("summary"):
        lines.append(str(report["summary"]))
    blocks = [
        ("Stil", report.get("style")),
        ("Akım", report.get("movement")),
        ("Konu", report.get("subject")),
        ("Kompozisyon", report.get("composition")),
        ("Renk paleti", report.get("color_palette")),
        ("Tarihsel bağlam", report.get("historical_context")),
    ]
    for label, val in blocks:
        if val:
            lines.append(f"\n{label}: {val}")
    sim = report.get("similar_artists") or []
    if sim:
        lines.append("\nBenzer sanatçılar: " + ", ".join(sim))
    if report.get("viewing_tips"):
        lines.append(f"\nİnceleme: {report['viewing_tips']}")
    conf = report.get("confidence") or report.get("is_likely_original")
    if conf:
        lines.append(f"\n[Güven: {report.get('confidence') or '—'} · Orijinallik: {report.get('is_likely_original') or '—'}]")
    return "\n".join(lines).strip()[:12_000]


def _gemini_analyze(raw: bytes, mime: str, depth: str = "deep") -> dict[str, Any]:
    from ilim_assistant.llm_gemini import gemini_active_model, gemini_api_key

    key = gemini_api_key()
    if not key:
        raise RuntimeError("Gemini API anahtarı yok.")

    import requests

    model = gemini_active_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    if depth == "quick":
        prompt = (
            "Sanat eseri uzmanısın. Görseli hızlı tanı. Yanıt YALNIZCA JSON:\n"
            '{"title":"","artist":"","period":"","technique":"","summary":"2 cümle Türkçe",'
            '"confidence":"yüksek|orta|düşük"}'
        )
        max_tokens = 700
    else:
        prompt = (
            "Sanat tarihi ve görsel analiz uzmanısın. «Bu eser nedir?» sorusuna yanıt ver. "
            "Yanıt YALNIZCA JSON (başka metin yok):\n"
            '{"title":"eser adı veya betimleme","artist":"sanatçı veya Bilinmiyor",'
            '"period":"dönem","technique":"teknik","style":"stil","movement":"sanat akımı",'
            '"composition":"kompozisyon analizi","color_palette":"renkler",'
            '"subject":"konu","confidence":"yüksek|orta|düşük",'
            '"is_likely_original":"evet|hayır|belirsiz",'
            '"similar_artists":["..."],"historical_context":"...",'
            '"viewing_tips":"müze/galeri bakış ipuçları","summary":"3-5 cümle Türkçe özet"}'
        )
        max_tokens = 1800
    b64 = base64.b64encode(raw).decode("ascii")
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime, "data": b64}},
                ],
            }
        ],
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": max_tokens},
    }
    resp = requests.post(
        url,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json=payload,
        timeout=(8, 35 if depth == "deep" else 28),
    )
    if resp.status_code != 200:
        raise ValueError(f"Gemini vision: HTTP {resp.status_code} — {(resp.text or '')[:200]}")
    obj = resp.json()
    candidates = obj.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini boş yanıt.")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(str(p.get("text") or "") for p in parts if isinstance(p, dict))
    parsed = _parse_identify_json(text)
    return {"source": "gemini", "parsed": parsed, "raw": text[:8000], "depth": depth}


def _gemini_identify(raw: bytes, mime: str) -> dict[str, Any]:
    return _gemini_analyze(raw, mime, depth="quick")


def _local_analyze(rel: str, repo_root: Path | None = None, depth: str = "deep") -> dict[str, Any]:
    from ilim_assistant.dinamit_vision import analyze_image_bytes

    path = resolve_sanat_rel(rel, repo_root)
    raw = path.read_bytes()
    info = analyze_image_bytes(raw)
    summary = str(info.get("summary") or "Görsel betimlenemedi.")
    summary = re.sub(r"\[DİNAMİT[^\]]*\]", "", summary, flags=re.IGNORECASE)
    summary = re.sub(r"\[/DİNAMİT\]", "", summary, flags=re.IGNORECASE).strip()
    w = info.get("width") or 0
    h = info.get("height") or 0
    parsed = _normalize_report(
        {
            "title": Path(rel).stem.replace("_", " "),
            "technique": info.get("format") or "",
            "composition": f"Görsel boyutu {w}×{h} piksel.",
            "summary": (
                "Yapısal görsel özeti (Gemini yok veya erişilemedi):\n\n"
                f"{summary}\n\n"
                "Kesin eser tanıma için GLOBAL_API_KEY ile Gemini vision önerilir."
            ),
            "confidence": "düşük",
            "is_likely_original": "belirsiz",
        }
    )
    return {"source": "vision", "parsed": parsed, "raw": summary[:8000], "depth": depth}


def _local_identify(rel: str, repo_root: Path | None = None) -> dict[str, Any]:
    return _local_analyze(rel, repo_root, depth="quick")


def _commit_analysis(
    rel: str,
    parsed: dict[str, Any],
    source: str,
    raw_text: str,
    depth: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    notes = _report_to_notes(parsed) if depth == "deep" else (parsed.get("summary") or raw_text[:4000])
    meta = update_metadata(
        rel,
        title=parsed.get("title") or None,
        artist=parsed.get("artist") or None,
        period=parsed.get("period") or None,
        technique=parsed.get("technique") or None,
        notes=notes or None,
        repo_root=repo_root,
    )
    item = dict(meta.get("item") or {})
    item["identify_summary"] = parsed.get("summary") or raw_text[:4000]
    item["identify_source"] = source
    item["identify_confidence"] = parsed.get("confidence") or ""
    item["identify_at"] = datetime.now(timezone.utc).isoformat()
    if depth == "deep":
        item["identify_report"] = parsed
    cat = _load_catalog(repo_root)
    items: list[dict[str, Any]] = list(cat.get("items") or [])
    items = [x for x in items if not (isinstance(x, dict) and x.get("rel") == rel)] + [item]
    cat["items"] = items[-300:]
    _save_catalog(cat, repo_root)
    return _entry_defaults(item)


def analyze_work(
    rel: str,
    depth: str = "deep",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    d = (depth or "deep").strip().lower()
    if d not in ("quick", "deep"):
        raise ValueError("depth: quick veya deep")
    path = resolve_sanat_rel(rel, repo_root)
    parsed: dict[str, Any]
    source: str
    raw_text: str
    if gemini_available():
        try:
            raw_bytes, mime = _image_bytes_for_gemini(path)
            g = _gemini_analyze(raw_bytes, mime, d)
            parsed = g["parsed"]
            source = g["source"]
            raw_text = g["raw"]
        except Exception:
            loc = _local_analyze(rel, repo_root, d)
            parsed = loc["parsed"]
            source = loc["source"]
            raw_text = loc["raw"]
    else:
        loc = _local_analyze(rel, repo_root, d)
        parsed = loc["parsed"]
        source = loc["source"]
        raw_text = loc["raw"]

    item = _commit_analysis(rel, parsed, source, raw_text, d, repo_root)
    label = "Detaylı eser raporu" if d == "deep" else "Hızlı tanıma"
    if source != "gemini":
        label += " (yapısal özet)"
    return {
        "ok": True,
        "item": item,
        "report": parsed,
        "source": source,
        "depth": d,
        "summary": parsed.get("summary") or raw_text[:4000],
        "label_tr": label,
    }


def identify_work(rel: str, repo_root: Path | None = None) -> dict[str, Any]:
    out = analyze_work(rel, depth="quick", repo_root=repo_root)
    out["label_tr"] = "Eser tanındı" if out.get("source") == "gemini" else "Yapısal özet (Gemini yok)"
    return out


def _xml_attr(val: str | float) -> str:
    s = str(val).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    return s


def commands_to_svg(commands: list[dict[str, Any]], width: int, height: int) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
    ]
    for cmd in commands or []:
        if not isinstance(cmd, dict):
            continue
        t = str(cmd.get("type") or "")
        color = _xml_attr(cmd.get("color") or "#cccccc")
        if t == "line":
            lines.append(
                f'<line x1="{cmd.get("x1", 0)}" y1="{cmd.get("y1", 0)}" x2="{cmd.get("x2", 0)}" y2="{cmd.get("y2", 0)}" '
                f'stroke="{color}" stroke-width="{cmd.get("width", 1)}"/>'
            )
        elif t == "rect":
            fill = cmd.get("fill")
            if fill:
                lines.append(
                    f'<rect x="{cmd.get("x", 0)}" y="{cmd.get("y", 0)}" width="{cmd.get("w", 0)}" height="{cmd.get("h", 0)}" fill="{color}"/>'
                )
            else:
                lines.append(
                    f'<rect x="{cmd.get("x", 0)}" y="{cmd.get("y", 0)}" width="{cmd.get("w", 0)}" height="{cmd.get("h", 0)}" '
                    f'fill="none" stroke="{color}" stroke-width="1"/>'
                )
        elif t == "circle":
            fill = cmd.get("fill")
            tag = " fill" if fill else ' fill="none" stroke'
            if fill:
                lines.append(
                    f'<circle cx="{cmd.get("cx", 0)}" cy="{cmd.get("cy", 0)}" r="{cmd.get("r", 0)}" fill="{color}"/>'
                )
            else:
                lines.append(
                    f'<circle cx="{cmd.get("cx", 0)}" cy="{cmd.get("cy", 0)}" r="{cmd.get("r", 0)}" '
                    f'fill="none" stroke="{color}" stroke-width="1"/>'
                )
        elif t == "polyline":
            pts = cmd.get("points") or []
            if len(pts) >= 2:
                pt_str = " ".join(f"{p[0]},{p[1]}" for p in pts if isinstance(p, (list, tuple)) and len(p) >= 2)
                lines.append(
                    f'<polyline points="{pt_str}" fill="none" stroke="{color}" stroke-width="{cmd.get("width", 1)}"/>'
                )
        elif t == "text" and cmd.get("text"):
            lines.append(
                f'<text x="{cmd.get("x", 0)}" y="{cmd.get("y", 0)}" fill="{color}" '
                f'font-size="{cmd.get("size", 14)}" font-family="Segoe UI,sans-serif">{_xml_attr(cmd.get("text"))}</text>'
            )
    lines.append("</svg>")
    return "\n".join(lines)


def sketch_work(rel: str, repo_root: Path | None = None) -> dict[str, Any]:
    from ilim_assistant.motorlar.mimar_tasarim import (
        edge_sketch_commands,
        gemini_draw_json,
        normalize_commands,
    )

    path = resolve_sanat_rel(rel, repo_root)
    img = _open_image(path)
    iw, ih = img.size
    w = max(320, min(iw, 1200))
    h = max(240, min(ih, 1200))
    source = "edge"
    commands: list[dict[str, Any]] = []
    if gemini_available():
        try:
            raw_bytes, mime = _image_bytes_for_gemini(path)
            prompt = (
                "Bu sanat eserinin üzerine bindirilecek ince eskiz çizgileri üret. "
                "Ana konturlar, figür ve kompozisyon hatları; gölgelendirme yok. "
                "Yanıt YALNIZCA JSON:\n"
                '{"commands":[{"type":"line|polyline|circle","x1":0,...}],"label":"..."}\n'
                "Koordinatlar 0-1000 normalize; en fazla 100 komut; renk #c8c8c8 veya #3794ff."
            )
            g = gemini_draw_json(prompt, raw_bytes, mime)
            commands = normalize_commands(g.get("commands") or [], w, h)
            if commands:
                source = "gemini"
        except Exception:
            commands = []
    if not commands:
        commands = edge_sketch_commands(img, w, h)
        source = "edge"

    svg_text = commands_to_svg(commands, w, h)
    cat = _load_catalog(repo_root)
    items: list[dict[str, Any]] = list(cat.get("items") or [])
    entry: dict[str, Any] = {}
    for x in items:
        if isinstance(x, dict) and x.get("rel") == rel:
            entry = dict(x)
            break
    if not entry:
        entry = {"rel": rel, "name": path.name, "id": path.stem.split("_")[0][:10]}
    fid = str(entry.get("id") or uuid.uuid4().hex[:10])
    svg_name = f"sketch_{fid}.svg"
    svg_path = sanat_dir(repo_root) / svg_name
    svg_path.write_text(svg_text, encoding="utf-8")
    root = (repo_root or _repo_root()).resolve()
    svg_rel = svg_path.relative_to(root).as_posix()

    entry["sketch_commands"] = commands
    entry["sketch_svg_rel"] = svg_rel
    entry["sketch_source"] = source
    entry["sketch_width"] = w
    entry["sketch_height"] = h
    entry["sketch_at"] = datetime.now(timezone.utc).isoformat()
    entry["updated"] = entry["sketch_at"]
    entry = _entry_defaults(entry)
    items = [x for x in items if not (isinstance(x, dict) and x.get("rel") == rel)] + [entry]
    cat["items"] = items[-300:]
    _save_catalog(cat, repo_root)

    return {
        "ok": True,
        "item": entry,
        "commands": commands,
        "svg_rel": svg_rel,
        "source": source,
        "width": w,
        "height": h,
        "label_tr": "Eskiz katmanı üretildi",
    }


def _trace_copy(img) -> Any:
    from PIL import Image, ImageFilter, ImageOps

    gray = img.convert("L")
    if opencv_available():
        import cv2
        import numpy as np

        arr = np.array(gray)
        edges = cv2.Canny(arr, 45, 130)
        inv = 255 - edges
        return Image.merge("RGB", (Image.fromarray(inv),) * 3)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.autocontrast(edges)
    return Image.merge("RGB", (edges, edges, edges))


def _poster_copy(img) -> Any:
    from PIL import Image, ImageEnhance

    q = img.convert("RGB").quantize(colors=14, method=2).convert("RGB")
    q = ImageEnhance.Contrast(q).enhance(1.15)
    q = ImageEnhance.Color(q).enhance(1.08)
    return q


def _pencil_copy(img) -> Any:
    from PIL import Image, ImageOps

    gray = img.convert("L")
    return ImageOps.colorize(gray, black="#2b2b2b", white="#f4efe6")


def copy_work(rel: str, mode: str = "trace", repo_root: Path | None = None) -> dict[str, Any]:
    m = (mode or "trace").strip().lower()
    if m not in ("trace", "poster", "pencil"):
        raise ValueError("mode: trace, poster veya pencil")
    path = resolve_sanat_rel(rel, repo_root)
    img = _open_image(path).convert("RGB")
    if m == "poster":
        out = _poster_copy(img)
    elif m == "pencil":
        out = _pencil_copy(img)
    else:
        out = _trace_copy(img)

    cat = _load_catalog(repo_root)
    items: list[dict[str, Any]] = list(cat.get("items") or [])
    entry: dict[str, Any] = {}
    for x in items:
        if isinstance(x, dict) and x.get("rel") == rel:
            entry = dict(x)
            break
    if not entry:
        entry = {"rel": rel, "name": path.name, "id": path.stem.split("_")[0][:10]}
    fid = str(entry.get("id") or uuid.uuid4().hex[:10])
    copy_name = f"copy_{fid}_{m}.jpg"
    copy_path = sanat_dir(repo_root) / copy_name
    out.save(copy_path, format="JPEG", quality=90, optimize=True)
    root = (repo_root or _repo_root()).resolve()
    copy_rel = copy_path.relative_to(root).as_posix()
    now = datetime.now(timezone.utc).isoformat()
    entry["copy_rel"] = copy_rel
    entry["copy_mode"] = m
    entry["copy_at"] = now
    entry["updated"] = now
    entry = _entry_defaults(entry)
    items = [x for x in items if not (isinstance(x, dict) and x.get("rel") == rel)] + [entry]
    cat["items"] = items[-300:]
    _save_catalog(cat, repo_root)
    labels = {"trace": "Trace kopya", "poster": "Poster stil kopya", "pencil": "Kalem kopya"}
    return {
        "ok": True,
        "item": entry,
        "copy_rel": copy_rel,
        "mode": m,
        "label_tr": labels.get(m, "Kopya üretildi"),
    }
