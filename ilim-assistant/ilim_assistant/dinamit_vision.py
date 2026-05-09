"""
Görsel analiz altyapısı — PIL (+ isteğe bağlı OpenCV). Dinamit Geliştirme — Ümit & Gökçenur.
"""

from __future__ import annotations

import io
import os
from typing import Any

_MIMAR = "Ümit & Gökçenur"


def analyze_image_bytes(raw: bytes) -> dict[str, Any]:
    """
    Hafif görüntü özeti (LLM’e verilecek metin üretir); tam nesne tanıma yoktur.
    """
    if not raw or len(raw) < 16:
        return {
            "ok": False,
            "summary": "Görüntü verisi çok kısa veya boş.",
            "mimarlar": _MIMAR,
        }
    try:
        from PIL import Image
        from PIL import ImageStat
    except ImportError:
        return {
            "ok": False,
            "summary": "Pillow kurulu değil: pip install pillow",
            "mimarlar": _MIMAR,
        }

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception as e:
        return {
            "ok": False,
            "summary": f"Görüntü açılamadı: {e}",
            "mimarlar": _MIMAR,
        }

    fmt = fmt_label = img.format or "?"
    w, h = img.size
    mode = img.mode
    stat = ImageStat.Stat(img.convert("RGB"))
    mean_r, mean_g, mean_b = stat.mean[:3]

    edges_hint = ""
    try:
        if os.environ.get("RUZGAR_OPENCV", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        ):
            import cv2  # type: ignore
            import numpy as np

            rgb = np.array(img.convert("RGB"))
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 60, 180)
            edge_density = float(np.mean(edges > 0))
            edges_hint = (
                f"Kenevre kenar yoğunluğu (OpenCV Canny, kabaca): {edge_density*100:.1f}%."
            )
    except Exception:
        edges_hint = (
            "(OpenCV isteğe bağlı: pip install opencv-python-headless — kapalı veya yüklenemedi.)"
        )

    summary = (
        f"[DİNAMİT — GÖRSEL — {_MIMAR}]\n"
        f"Biçim: {fmt}; boyut: {w}×{h} piksel; kanal modu: {mode}.\n"
        f"Ortalama renk (RGB): ({mean_r:.0f}, {mean_g:.0f}, {mean_b:.0f}).\n"
        f"{edges_hint}\n"
        "Bu özet yapısaldir; içerik anlamı için model bağlamına kullanıcı açıklamasını bekleyin "
        "veya metinle soru ekleyin.\n[/DİNAMİT]"
    )
    return {
        "ok": True,
        "summary": summary,
        "width": w,
        "height": h,
        "format": fmt_label,
        "mode": mode,
        "mimarlar": _MIMAR,
    }
