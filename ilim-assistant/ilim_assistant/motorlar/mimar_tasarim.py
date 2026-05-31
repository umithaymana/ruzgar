"""
Mimar — Tasarım tuvali (Faz 4T-1 proje, 4T-2 sohbet handoff, 4T-3 arşiv yenileme).
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
_TASARIM_SUB = "ilim-assistant/arsiv/mimar-tasarim"
_MAX_BYTES = 25_000_000
_IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"})
_DEFAULT_W = 960
_DEFAULT_H = 540


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2].parent


def tasarim_dir(repo_root: Path | None = None) -> Path:
    root = (repo_root or _repo_root()).resolve()
    d = root / "ilim-assistant" / "arsiv" / "mimar-tasarim"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_name(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9._\-]+", "_", (name or "proje").strip()).strip("._")
    return base[:80] or "proje"


def resolve_tasarim_rel(rel: str, repo_root: Path | None = None) -> Path:
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw.startswith(_TASARIM_SUB):
        raise ValueError("Yalnızca mimar-tasarim arşivi.")
    root = (repo_root or _repo_root()).resolve()
    target = (root / raw.replace("/", os.sep)).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError("Geçersiz yol.") from None
    base = tasarim_dir(repo_root).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError("Dosya mimar-tasarim dışında.") from None
    if not target.is_file():
        raise FileNotFoundError("Dosya yok.")
    return target


def pillow_available() -> bool:
    try:
        from PIL import Image  # noqa: F401

        return True
    except ImportError:
        return False


def opencv_available() -> bool:
    if os.environ.get("RUZGAR_OPENCV", "1").strip().lower() in ("0", "false", "no"):
        return False
    try:
        import cv2  # noqa: F401

        return True
    except ImportError:
        return False


def gemini_available() -> bool:
    try:
        from ilim_assistant.llm_gemini import gemini_configured

        return gemini_configured()
    except Exception:
        return False


def capabilities() -> dict[str, Any]:
    return {
        "ok": True,
        "pillow": pillow_available(),
        "opencv": opencv_available(),
        "gemini": gemini_available(),
        "mimarlar": _MIMAR,
        "default_width": _DEFAULT_W,
        "default_height": _DEFAULT_H,
        "command_types": ["line", "rect", "polyline", "circle", "text"],
        "chat_handoff": True,
        "archive_ops": ["duplicate", "regenerate", "export_png"],
    }


def _project_path(project_id: str, repo_root: Path | None = None) -> Path:
    pid = _safe_name(project_id)
    return tasarim_dir(repo_root) / f"{pid}.json"


def _blank_layer(layer_id: str, name: str, *, kind: str = "vector") -> dict[str, Any]:
    return {
        "id": layer_id,
        "name": name,
        "visible": True,
        "kind": kind,
        "commands": [],
    }


def new_project(
    name: str = "Yeni plan",
    width: int = _DEFAULT_W,
    height: int = _DEFAULT_H,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    pid = uuid.uuid4().hex[:10]
    now = datetime.now(timezone.utc).isoformat()
    project = {
        "version": 1,
        "id": pid,
        "name": (name or "Yeni plan").strip()[:120],
        "width": max(320, min(int(width or _DEFAULT_W), 2400)),
        "height": max(240, min(int(height or _DEFAULT_H), 1600)),
        "notes": "",
        "reference_rel": "",
        "layers": [
            _blank_layer("eskiz", "Eskiz"),
            _blank_layer("el", "El çizimi"),
        ],
        "updated": now,
    }
    save_project(project, repo_root)
    return {"ok": True, "project": project}


def save_project(project: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    if not isinstance(project, dict):
        raise ValueError("Geçersiz proje.")
    pid = _safe_name(str(project.get("id") or uuid.uuid4().hex[:10]))
    project = dict(project)
    project["id"] = pid
    project["version"] = 1
    project["updated"] = datetime.now(timezone.utc).isoformat()
    layers = project.get("layers")
    if not isinstance(layers, list):
        project["layers"] = [_blank_layer("eskiz", "Eskiz")]
    path = _project_path(pid, repo_root)
    path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    root = (repo_root or _repo_root()).resolve()
    rel = path.relative_to(root).as_posix()
    return {"ok": True, "project": project, "rel": rel, "label_tr": "Proje kaydedildi"}


def load_project(project_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    path = _project_path(project_id, repo_root)
    if not path.is_file():
        raise FileNotFoundError("Proje bulunamadı.")
    project = json.loads(path.read_text(encoding="utf-8"))
    return {"ok": True, "project": project}


def list_projects(repo_root: Path | None = None) -> dict[str, Any]:
    d = tasarim_dir(repo_root)
    items: list[dict[str, Any]] = []
    for p in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if p.name.startswith("_"):
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(obj, dict):
                continue
            items.append(
                {
                    "id": obj.get("id") or p.stem,
                    "name": obj.get("name") or p.stem,
                    "updated": obj.get("updated") or "",
                    "width": obj.get("width"),
                    "height": obj.get("height"),
                }
            )
        except Exception:
            continue
    return {"ok": True, "items": items[:100]}


def upload_reference(data: bytes, filename: str, repo_root: Path | None = None) -> dict[str, Any]:
    if not data:
        raise ValueError("Boş dosya.")
    if len(data) > _MAX_BYTES:
        raise ValueError(f"Dosya çok büyük ({_MAX_BYTES // 1_000_000} MB sınırı).")
    if not pillow_available():
        raise RuntimeError("Pillow kurulu değil: pip install pillow")

    from PIL import Image

    d = tasarim_dir(repo_root)
    stem = _safe_name(Path(filename or "ref").stem)
    fid = uuid.uuid4().hex[:8]
    target = d / f"ref_{fid}_{stem}.jpg"
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:
        raise ValueError(f"Görüntü açılamadı: {e}") from e
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        img = img.convert("RGB")
    img.save(target, format="JPEG", quality=90, optimize=True)
    root = (repo_root or _repo_root()).resolve()
    rel = target.relative_to(root).as_posix()
    return {"ok": True, "rel": rel, "width": img.size[0], "height": img.size[1]}


def _scale_coord(v: float, axis: int) -> float:
    x = float(v)
    if 0.0 <= x <= 1.0:
        return round(x * axis, 2)
    if 0.0 <= x <= 1000.0:
        return round(x / 1000.0 * axis, 2)
    return round(x, 2)


def normalize_commands(
    commands: list[Any],
    width: int,
    height: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in commands or []:
        if not isinstance(raw, dict):
            continue
        t = str(raw.get("type") or "").strip().lower()
        if t == "line":
            out.append(
                {
                    "type": "line",
                    "x1": _scale_coord(raw.get("x1", 0), width),
                    "y1": _scale_coord(raw.get("y1", 0), height),
                    "x2": _scale_coord(raw.get("x2", 0), width),
                    "y2": _scale_coord(raw.get("y2", 0), height),
                    "color": str(raw.get("color") or "#d4d4d4"),
                    "width": max(1, min(int(raw.get("width") or 1), 8)),
                }
            )
        elif t == "rect":
            out.append(
                {
                    "type": "rect",
                    "x": _scale_coord(raw.get("x", 0), width),
                    "y": _scale_coord(raw.get("y", 0), height),
                    "w": _scale_coord(raw.get("w", raw.get("width", 10)), width),
                    "h": _scale_coord(raw.get("h", raw.get("height", 10)), height),
                    "color": str(raw.get("color") or "#888888"),
                    "fill": bool(raw.get("fill")),
                }
            )
        elif t == "circle":
            r = raw.get("r", raw.get("radius", 10))
            out.append(
                {
                    "type": "circle",
                    "cx": _scale_coord(raw.get("cx", raw.get("x", 0)), width),
                    "cy": _scale_coord(raw.get("cy", raw.get("y", 0)), height),
                    "r": _scale_coord(r, min(width, height)),
                    "color": str(raw.get("color") or "#aaaaaa"),
                    "fill": bool(raw.get("fill")),
                }
            )
        elif t == "polyline":
            pts = raw.get("points") or []
            norm_pts: list[list[float]] = []
            for pt in pts:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    norm_pts.append([_scale_coord(pt[0], width), _scale_coord(pt[1], height)])
            if len(norm_pts) >= 2:
                out.append(
                    {
                        "type": "polyline",
                        "points": norm_pts,
                        "color": str(raw.get("color") or "#cccccc"),
                        "width": max(1, min(int(raw.get("width") or 1), 6)),
                    }
                )
        elif t == "text":
            txt = str(raw.get("text") or "")[:200]
            if txt:
                out.append(
                    {
                        "type": "text",
                        "x": _scale_coord(raw.get("x", 0), width),
                        "y": _scale_coord(raw.get("y", 0), height),
                        "text": txt,
                        "color": str(raw.get("color") or "#e0e0e0"),
                        "size": max(8, min(int(raw.get("size") or 14), 48)),
                    }
                )
        if len(out) >= 200:
            break
    return out


def _parse_commands_json(text: str) -> list[dict[str, Any]]:
    raw = (text or "").strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return []
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    cmds = obj.get("commands") if isinstance(obj, dict) else None
    if isinstance(cmds, list):
        return [x for x in cmds if isinstance(x, dict)]
    return []


def _edge_sketch_commands(img, width: int, height: int) -> list[dict[str, Any]]:
    if not opencv_available():
        return [
            {
                "type": "text",
                "x": width * 0.08,
                "y": height * 0.12,
                "text": "OpenCV yok — pip install opencv-python-headless",
                "color": "#888888",
                "size": 14,
            }
        ]
    import cv2
    import numpy as np

    rgb = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(gray, 40, 120)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    ih, iw = gray.shape
    commands: list[dict[str, Any]] = []
    for cnt in contours[:100]:
        if len(cnt) < 3:
            continue
        step = max(1, len(cnt) // 40)
        pts: list[list[float]] = []
        for p in cnt[::step]:
            x, y = int(p[0][0]), int(p[0][1])
            pts.append([round(x / iw * width, 1), round(y / ih * height, 1)])
        if len(pts) >= 2:
            commands.append({"type": "polyline", "points": pts, "color": "#b0b0b0", "width": 1})
        if len(commands) >= 120:
            break
    if not commands:
        commands.append(
            {
                "type": "text",
                "x": width * 0.1,
                "y": height * 0.2,
                "text": "Kenar bulunamadı — farklı referans deneyin",
                "color": "#666666",
                "size": 14,
            }
        )
    return commands


def edge_sketch_commands(img, width: int, height: int) -> list[dict[str, Any]]:
    """Faz 4S-3 / 4T-1 — kenar eskizi (public)."""
    return _edge_sketch_commands(img, width, height)


def gemini_draw_json(
    prompt: str,
    image_bytes: bytes | None = None,
    mime: str = "image/jpeg",
) -> dict[str, Any]:
    return _gemini_draw_json(prompt, image_bytes, mime)


def _gemini_draw_json(prompt: str, image_bytes: bytes | None = None, mime: str = "image/jpeg") -> dict[str, Any]:
    from ilim_assistant.llm_gemini import gemini_active_model, gemini_api_key

    key = gemini_api_key()
    if not key:
        raise RuntimeError("Gemini API anahtarı yok.")
    import requests

    model = gemini_active_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    parts: list[dict[str, Any]] = [{"text": prompt}]
    if image_bytes:
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(image_bytes).decode("ascii")}})
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096},
    }
    resp = requests.post(
        url,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json=payload,
        timeout=(8, 35),
    )
    if resp.status_code != 200:
        raise ValueError(f"Gemini: HTTP {resp.status_code} — {(resp.text or '')[:180]}")
    obj = resp.json()
    candidates = obj.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini boş yanıt.")
    c_parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(str(p.get("text") or "") for p in c_parts if isinstance(p, dict))
    cmds = _parse_commands_json(text)
    return {"source": "gemini", "commands": cmds, "raw": text[:8000]}


def _basic_shape_from_text(text: str, width: int, height: int) -> list[dict[str, Any]]:
    t = (text or "").lower()
    cx, cy = width * 0.5, height * 0.5
    cmds: list[dict[str, Any]] = []
    if any(k in t for k in ("ev", "bina", "mimari", "plan", "villa", "apartman")):
        bw, bh = width * 0.35, height * 0.28
        x, y = cx - bw / 2, cy - bh / 2
        cmds.extend(
            [
                {"type": "rect", "x": x, "y": y, "w": bw, "h": bh, "color": "#888888", "fill": False},
                {"type": "polyline", "points": [[x, y], [cx, y - bh * 0.35], [x + bw, y]], "color": "#aaaaaa", "width": 2},
                {"type": "rect", "x": x + bw * 0.38, "y": y + bh * 0.55, "w": bw * 0.24, "h": bh * 0.45, "color": "#666666", "fill": False},
            ]
        )
    elif any(k in t for k in ("daire", "circle", "yuvarlak")):
        cmds.append({"type": "circle", "cx": cx, "cy": cy, "r": min(width, height) * 0.18, "color": "#aaaaaa", "fill": False})
    elif any(k in t for k in ("ağaç", "agac", "tree")):
        cmds.extend(
            [
                {"type": "rect", "x": cx - 8, "y": cy, "w": 16, "h": height * 0.15, "color": "#8b6914", "fill": True},
                {"type": "circle", "cx": cx, "cy": cy - 20, "r": 40, "color": "#4a7c4a", "fill": True},
            ]
        )
    else:
        cmds.append(
            {
                "type": "text",
                "x": width * 0.08,
                "y": height * 0.15,
                "text": (text or "Betimleme")[:120],
                "color": "#cccccc",
                "size": 16,
            }
        )
        cmds.append({"type": "rect", "x": width * 0.1, "y": height * 0.25, "w": width * 0.8, "h": height * 0.5, "color": "#555555", "fill": False})
    return cmds


def sketch_from_image(
    rel: str,
    width: int = _DEFAULT_W,
    height: int = _DEFAULT_H,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    path = resolve_tasarim_rel(rel, repo_root)
    if path.suffix.lower() not in _IMAGE_EXTS:
        raise ValueError("Referans görsel değil.")
    w = max(320, min(int(width or _DEFAULT_W), 2400))
    h = max(240, min(int(height or _DEFAULT_H), 1600))
    img = _open_image(path)
    source = "edge"
    commands: list[dict[str, Any]] = []
    if gemini_available():
        try:
            raw = path.read_bytes()
            mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            prompt = (
                "Bu görselden mimari/teknik eskiz çiz. Yanıt YALNIZCA JSON:\n"
                '{"commands":[{"type":"line|rect|polyline|circle","x1":0,"y1":0,...}],'
                '"label":"kısa açıklama"}\n'
                "Koordinatlar 0-1000 normalize; en fazla 80 komut; renk #hex."
            )
            g = _gemini_draw_json(prompt, raw, mime)
            commands = normalize_commands(g.get("commands") or [], w, h)
            if commands:
                source = "gemini"
        except Exception:
            commands = []
    if not commands:
        commands = _edge_sketch_commands(img, w, h)
        source = "edge"
    return {
        "ok": True,
        "commands": commands,
        "source": source,
        "width": w,
        "height": h,
        "reference_rel": rel,
        "label_tr": "Referanstan eskiz üretildi",
    }


def sketch_from_text(
    text: str,
    width: int = _DEFAULT_W,
    height: int = _DEFAULT_H,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    _ = repo_root
    desc = (text or "").strip()
    if not desc:
        raise ValueError("Betimleme metni boş.")
    w = max(320, min(int(width or _DEFAULT_W), 2400))
    h = max(240, min(int(height or _DEFAULT_H), 1600))
    source = "basic"
    commands: list[dict[str, Any]] = []
    if gemini_available():
        try:
            prompt = (
                f"Kullanıcı betimlemesi: {desc[:2000]}\n\n"
                "Tuval için teknik eskiz/plan çiz. Yanıt YALNIZCA JSON:\n"
                '{"commands":[{"type":"line|rect|polyline|circle|text",...}],"label":"..."}\n'
                "Koordinatlar 0-1000; en fazla 80 komut; Türkçe metin etiketleri olabilir."
            )
            g = _gemini_draw_json(prompt, None)
            commands = normalize_commands(g.get("commands") or [], w, h)
            if commands:
                source = "gemini"
        except Exception:
            commands = []
    if not commands:
        commands = _basic_shape_from_text(desc, w, h)
        source = "basic"
    return {
        "ok": True,
        "commands": commands,
        "source": source,
        "width": w,
        "height": h,
        "label_tr": "Betimlemeden eskiz üretildi",
    }


def _open_image(path: Path):
    from PIL import Image

    img = Image.open(path)
    img.load()
    return img


def build_chat_handoff_text(user: str = "", assistant: str = "", notes: str = "") -> str:
    parts: list[str] = []
    u = (user or "").strip()
    a = (assistant or "").strip()
    n = (notes or "").strip()
    if u:
        parts.append(f"Kullanıcı isteği: {u[:1400]}")
    if a:
        parts.append(f"Asistan yanıtı: {a[:1400]}")
    if n:
        parts.append(f"Plan notu: {n[:1400]}")
    text = "\n\n".join(parts).strip()
    if not text:
        raise ValueError("Sohbet handoff metni boş — önce sohbet edin veya not yazın.")
    return text


def sketch_from_chat_handoff(
    user: str = "",
    assistant: str = "",
    notes: str = "",
    width: int = _DEFAULT_W,
    height: int = _DEFAULT_H,
    project_id: str = "",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    handoff = build_chat_handoff_text(user, assistant, notes)
    sk = sketch_from_text(handoff, width, height, repo_root)
    sk["handoff_text"] = handoff[:2500]
    sk["label_tr"] = "Sohbet handoff ile tuval güncellendi"
    pid = (project_id or "").strip()
    if pid:
        try:
            loaded = load_project(pid, repo_root)
            project = dict(loaded.get("project") or {})
            project["notes"] = (notes or project.get("notes") or handoff[:4000])[:12_000]
            for layer in project.get("layers") or []:
                if isinstance(layer, dict) and layer.get("id") == "eskiz":
                    layer["commands"] = sk.get("commands") or []
                    break
            saved = save_project(project, repo_root)
            sk["project"] = saved.get("project")
        except FileNotFoundError:
            sk["project_warning"] = "Proje bulunamadı — yalnızca komutlar döndü."
    return sk


def duplicate_project(
    project_id: str,
    name: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    loaded = load_project(project_id, repo_root)
    project = dict(loaded.get("project") or {})
    project["id"] = uuid.uuid4().hex[:10]
    base_name = str(project.get("name") or "Plan")
    project["name"] = (name or f"{base_name} kopya").strip()[:120]
    saved = save_project(project, repo_root)
    return {"ok": True, "project": saved.get("project"), "label_tr": "Proje kopyalandı"}


def regenerate_project(project_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    loaded = load_project(project_id, repo_root)
    project = dict(loaded.get("project") or {})
    w = int(project.get("width") or _DEFAULT_W)
    h = int(project.get("height") or _DEFAULT_H)
    ref = str(project.get("reference_rel") or "").strip()
    notes = str(project.get("notes") or "").strip()
    if ref:
        try:
            sk = sketch_from_image(ref, w, h, repo_root)
        except Exception:
            sk = sketch_from_text(notes or "Mimari plan", w, h, repo_root)
    elif notes:
        sk = sketch_from_text(notes, w, h, repo_root)
    else:
        raise ValueError("Yenileme için proje notu veya referans gerekli.")
    for layer in project.get("layers") or []:
        if isinstance(layer, dict) and layer.get("id") == "eskiz":
            layer["commands"] = sk.get("commands") or []
            break
    project["regenerated_at"] = datetime.now(timezone.utc).isoformat()
    saved = save_project(project, repo_root)
    return {
        "ok": True,
        "project": saved.get("project"),
        "commands": sk.get("commands") or [],
        "source": sk.get("source") or "",
        "label_tr": "Kayıtlı mimari yeniden üretildi",
    }


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    c = (color or "#cccccc").strip()
    if c.startswith("#") and len(c) >= 7:
        try:
            return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        except ValueError:
            pass
    return 204, 204, 204


def render_commands_to_image(
    project: dict[str, Any],
    repo_root: Path | None = None,
) -> Any:
    from PIL import Image, ImageDraw

    _ = repo_root
    w = max(320, min(int(project.get("width") or _DEFAULT_W), 2400))
    h = max(240, min(int(project.get("height") or _DEFAULT_H), 1600))
    img = Image.new("RGB", (w, h), "#1a1a1a")
    draw = ImageDraw.Draw(img)
    ref = str(project.get("reference_rel") or "").strip()
    if ref:
        try:
            ref_path = resolve_tasarim_rel(ref, repo_root)
            ref_img = _open_image(ref_path).convert("RGB")
            iw, ih = ref_img.size
            scale = min(w / iw, h / ih)
            dw, dh = int(iw * scale), int(ih * scale)
            ref_img = ref_img.resize((dw, dh))
            ox, oy = (w - dw) // 2, (h - dh) // 2
            bg = Image.new("RGB", (w, h), "#1a1a1a")
            bg.paste(ref_img, (ox, oy))
            img = bg
            draw = ImageDraw.Draw(img)
        except Exception:
            pass
    for layer in project.get("layers") or []:
        if not isinstance(layer, dict) or layer.get("visible") is False:
            continue
        for cmd in layer.get("commands") or []:
            if not isinstance(cmd, dict):
                continue
            t = str(cmd.get("type") or "")
            color = _hex_to_rgb(str(cmd.get("color") or "#cccccc"))
            if t == "line":
                draw.line(
                    [(cmd.get("x1", 0), cmd.get("y1", 0)), (cmd.get("x2", 0), cmd.get("y2", 0))],
                    fill=color,
                    width=max(1, int(cmd.get("width") or 1)),
                )
            elif t == "rect":
                x, y = cmd.get("x", 0), cmd.get("y", 0)
                rw, rh = cmd.get("w", 0), cmd.get("h", 0)
                if cmd.get("fill"):
                    draw.rectangle([x, y, x + rw, y + rh], fill=color)
                else:
                    draw.rectangle([x, y, x + rw, y + rh], outline=color, width=1)
            elif t == "circle":
                cx, cy, r = cmd.get("cx", 0), cmd.get("cy", 0), cmd.get("r", 0)
                if cmd.get("fill"):
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
                else:
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=1)
            elif t == "polyline":
                pts = [(p[0], p[1]) for p in (cmd.get("points") or []) if isinstance(p, (list, tuple)) and len(p) >= 2]
                if len(pts) >= 2:
                    draw.line(pts, fill=color, width=max(1, int(cmd.get("width") or 1)))
    return img


def export_project_png(project_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    loaded = load_project(project_id, repo_root)
    project = dict(loaded.get("project") or {})
    pid = _safe_name(str(project.get("id") or project_id))
    img = render_commands_to_image(project, repo_root)
    out_path = tasarim_dir(repo_root) / f"export_{pid}.png"
    img.save(out_path, format="PNG", optimize=True)
    root = (repo_root or _repo_root()).resolve()
    rel = out_path.relative_to(root).as_posix()
    return {
        "ok": True,
        "rel": rel,
        "project_id": pid,
        "label_tr": "PNG dışa aktarıldı",
    }
