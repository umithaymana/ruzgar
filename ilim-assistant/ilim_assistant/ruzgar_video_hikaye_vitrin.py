# Created by Ümit & Gökçenur
"""
Motor D — hikâye / kayıt / cam köprüsü vitrin ölçümü (Adım 6.D).

LLM olmadan doğrulanabilir: yerel sahne bölme + ffmpeg + atölye route yüzeyi.
"""

from __future__ import annotations

import os
import re
from typing import Any

VERSION = "video-hikaye-vitrin-v1-2026-11-09"

# Kısa klasik hikâye parçaları — vitrin kartları
_VITRIN_STORIES: list[tuple[str, str]] = [
    (
        "besmele_ders",
        "Rahman ve Rahim olan Allah'ın adıyla. Öğrenci kütüphanede bir kitap açtı. "
        "Sayfalar arasında bir harita belirdi. Rüzgar camdan esince sahne aydınlandı.",
    ),
    (
        "kutuphane_gece",
        "Gece yarısı raflar sessizdi. Bir lamba yandı. Okuyucu kalktı ve koridorda yürüdü. "
        "Kapı aralandı; dışarıda yağmur vardı.",
    ),
    (
        "cam_koprü",
        "Camın ötesinde bir dünya penceresi açıldı. Resmi yayın akıyordu. "
        "İçerideki atölye kaydı aldı. Sabah olduğunda kısa bir film hazırdı.",
    ),
]


def enabled() -> bool:
    return os.environ.get("RUZGAR_VIDEO_HIKAYE_VITRIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def local_storyboard(story: str, *, title: str = "") -> dict[str, Any]:
    """LLM'siz sahne bölme — cümle / nefes birimleri."""
    text = re.sub(r"\s+", " ", (story or "").strip())
    if len(text) < 20:
        raise ValueError("Hikâye en az 20 karakter olmalı.")
    parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text) if p.strip()]
    if len(parts) < 2:
        # virgül / ve ile yedek
        parts = [p.strip() for p in re.split(r"\s*[;:]\s+|\s+—\s+", text) if len(p.strip()) > 12]
    if not parts:
        parts = [text]
    scenes = []
    for i, narr in enumerate(parts[:8], start=1):
        scenes.append(
            {
                "scene_id": i,
                "narration": narr,
                "mood": "neutral",
                "action": "anlatı",
                "estimated_seconds": max(8.0, min(40.0, len(narr) * 0.35)),
                "transition": "fade",
            }
        )
    board = {
        "title": (title or "Hikâye vitrin").strip(),
        "theme": "ilim",
        "synopsis": parts[0][:160] if parts else "",
        "characters": [{"id": "c1", "name": "Anlatıcı", "role": "ses", "description": ""}],
        "locations": [{"id": "l1", "name": "Sahne", "description": "yerel vitrin"}],
        "scenes": scenes,
        "render_recommendation": "slideshow",
        "local": True,
        "version": VERSION,
    }
    return board


def measure_vitrin() -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    ok_n = 0
    for key, story in _VITRIN_STORIES:
        try:
            board = local_storyboard(story, title=key)
            n = len(board.get("scenes") or [])
            good = n >= 2
            if good:
                ok_n += 1
            cards.append(
                {
                    "ok": good,
                    "id": key,
                    "scenes": n,
                    "title": board.get("title"),
                    "first_narration": (board["scenes"][0]["narration"][:80] if board.get("scenes") else ""),
                }
            )
        except Exception as e:
            cards.append({"ok": False, "id": key, "error": type(e).__name__})
    total = len(_VITRIN_STORIES)
    score = round(100.0 * ok_n / total, 1) if total else 0.0
    return {
        "ok": ok_n == total,
        "version": VERSION,
        "enabled": enabled(),
        "total": total,
        "hit": ok_n,
        "miss": total - ok_n,
        "score_pct": score,
        "cards": cards,
        "label_tr": "Hikâye vitrini (yerel sahne)",
    }


def atolye_mutlu_yol() -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    vit = measure_vitrin()
    steps.append(
        {
            "id": "hikaye_vitrin",
            "ok": bool(vit.get("ok")),
            "detail": f"score={vit.get('score_pct')}% hit={vit.get('hit')}/{vit.get('total')}",
        }
    )

    # ffmpeg / ffprobe
    ff_ok = False
    fp_ok = False
    try:
        from ilim_assistant.video_ffmpeg import ffmpeg_available, ffprobe_available

        ff_ok = bool(ffmpeg_available())
        fp_ok = bool(ffprobe_available())
    except Exception as e:
        steps.append({"id": "ffmpeg", "ok": False, "detail": type(e).__name__})
    else:
        steps.append(
            {
                "id": "ffmpeg",
                "ok": ff_ok,
                "detail": f"ffmpeg={ff_ok} ffprobe={fp_ok}",
            }
        )

    # plan dönüşümü (LLM import etmeden — yerel köprü)
    plan_ok = False
    plan: dict[str, Any] = {}
    try:
        board = local_storyboard(_VITRIN_STORIES[0][1], title="mutlu")
        try:
            from ilim_assistant.video_storyboard import storyboard_to_video_plan

            plan = storyboard_to_video_plan(board)
        except Exception:
            # video_storyboard → ollama bağımlılığı yoksa yerel plan
            plan = {
                "title": board.get("title"),
                "theme": board.get("theme"),
                "synopsis": board.get("synopsis"),
                "scenes": list(board.get("scenes") or []),
                "render_recommendation": board.get("render_recommendation"),
                "local_bridge": True,
            }
        plan_ok = bool(plan.get("scenes")) and len(plan["scenes"]) >= 2
        steps.append(
            {
                "id": "plan_bridge",
                "ok": plan_ok,
                "detail": f"scenes={len(plan.get('scenes') or [])}",
            }
        )
    except Exception as e:
        steps.append({"id": "plan_bridge", "ok": False, "detail": type(e).__name__})

    # route yüzeyi (cam köprüsü + hikâye)
    routes_ok = False
    missing: list[str] = []
    try:
        from pathlib import Path

        ds = Path(__file__).resolve().parent.parent / "desktop_server.py"
        text = ds.read_text(encoding="utf-8") if ds.is_file() else ""
        core = [
            "/api/video/probe",
            "/api/video/storyboard",
            "/api/video/plan",
            "/api/video/stream/prepare",
            "/api/video/hikaye-vitrin",
        ]
        missing = [p for p in core if p not in text]
        routes_ok = len(missing) == 0
    except Exception as e:
        missing = [type(e).__name__]
    steps.append(
        {
            "id": "atolye_routes",
            "ok": routes_ok,
            "detail": "ok" if routes_ok else f"eksik={missing}",
        }
    )

    all_ok = all(bool(s.get("ok")) for s in steps)
    return {
        "ok": all_ok,
        "version": VERSION,
        "steps": steps,
        "vitrin": vit,
        "label_tr": "Video atölye mutlu yolu",
    }


def public_status() -> dict[str, Any]:
    if not enabled():
        return {"enabled": False, "version": VERSION}
    vit = measure_vitrin()
    return {
        "enabled": True,
        "version": VERSION,
        "vitrin_ok": bool(vit.get("ok")),
        "vitrin_score_pct": vit.get("score_pct"),
        "vitrin_hit": vit.get("hit"),
        "vitrin_total": vit.get("total"),
    }
