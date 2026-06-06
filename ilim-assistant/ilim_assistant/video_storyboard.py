# Created by Ümit & Gökçenur
"""
Hikâye → sinematik storyboard (V6).

Gerçekçi sınır: Bu modül yönetmen planı + kahraman/mekân haritası üretir.
Hareketli AI video (karakter canlandırma) ayrı render katmanı gerektirir — bkz. render_mode.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ilim_assistant.llm_ollama import chat_completion


RENDER_MODES = ("slideshow", "motion", "generative")


def _extract_json(text: str) -> str:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("Model çıktısında JSON bulunamadı.")
    return m.group(0)


def analyze_story_for_video(
    story_text: str,
    *,
    theme: str = "",
    title: str = "",
    user_assets: list[dict[str, Any]] | None = None,
    max_scenes: int = 12,
) -> dict[str, Any]:
    """
    Hikâyeden kahramanlar, mekânlar, sahneler ve (varsa) kullanıcı görsel eşlemesi.

    user_assets örneği:
      [{"id": "001", "rel": "ilim-assistant/arsiv/...", "note": "dede portresi"}]
    """
    text = (story_text or "").strip()
    if len(text) < 20:
        raise ValueError("Hikâye en az 20 karakter olmalı.")

    assets = user_assets or []
    asset_lines = "\n".join(
        f"- {a.get('id', '?')}: {(a.get('note') or a.get('rel') or '').strip()}"
        for a in assets
        if isinstance(a, dict)
    ) or "(Kullanıcı görseli yok — sahneler metinden türetilecek.)"

    cap = max(3, min(int(max_scenes or 12), 20))

    system = f"""Sen sinema yönetmeni ve senaryo editörüsün.
Görev: hikâyeyi CANLANDIRILACAK kısa filme dönüştür — kahramanlara isim/rol ver, mekânları netleştir.

ÖNEMLİ: narration alanına sistem talimatı veya JSON açıklaması YAZMA; yalnızca seyirciye anlatılacak Türkçe metin.

JSON şeması (yalnızca geçerli JSON):
{{
  "title": "...",
  "theme": "...",
  "synopsis": "1-2 cümle",
  "characters": [
    {{"id": "c1", "name": "...", "role": "...", "description": "görünüm kısa"}}
  ],
  "locations": [
    {{"id": "l1", "name": "...", "description": "..."}}
  ],
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "bu sahnede seslendirilecek metin (hikâyedeki parça)",
      "character_ids": ["c1"],
      "location_id": "l1",
      "mood": "huzur|heyecan|hüzün|umut|saygı|merak|sevinç|neutral",
      "action": "sahnedeki hareket/eylem (kısa)",
      "visual_prompt": "İngilizce sinematik görüntü/ video prompt",
      "motion_prompt": "kamera ve hareket: pan, walk, smile, wind...",
      "asset_id": "001 veya null — kullanıcı görseli varsa en uygun id",
      "estimated_seconds": 25-90
    }}
  ],
  "render_recommendation": "slideshow|motion|generative"
}}

Kurallar:
- En fazla {cap} sahne; her sahne tek nefes/akış birimi.
- Kullanıcı görselleri varsa asset_id ile eşle (001, 002 …); uygun değilse null.
- Karakterler hikâyede geçmese bile metinden çıkar (anlatıcı, çocuk, dede vb.).
- render_recommendation: kullanıcı fotoğrafı varsa "motion"; tam uydurma yoksa "generative"; yalnız metin+tek görsel "slideshow"."""

    user = f"Tema: {(theme or 'genel').strip()}\n"
    if title:
        user += f"Başlık: {title.strip()}\n"
    user += f"\nKullanıcı görselleri:\n{asset_lines}\n\nHikâye:\n{text[:14000]}"

    raw = chat_completion(system, user)
    if raw.startswith("[HTTP") or raw.startswith("Ollama") or raw.startswith("LLM hatası"):
        raise RuntimeError(raw)

    parsed = json.loads(_extract_json(raw))
    return _normalize_storyboard(parsed, fallback_title=title, fallback_theme=theme)


def _normalize_storyboard(
    raw: dict[str, Any],
    *,
    fallback_title: str = "",
    fallback_theme: str = "",
) -> dict[str, Any]:
    chars = raw.get("characters") or []
    locs = raw.get("locations") or []
    scenes_in = raw.get("scenes") or []

    characters: list[dict[str, Any]] = []
    for i, c in enumerate(chars):
        if not isinstance(c, dict):
            continue
        cid = str(c.get("id") or f"c{i + 1}").strip()
        name = str(c.get("name") or f"Karakter {i + 1}").strip()
        characters.append(
            {
                "id": cid,
                "name": name,
                "role": str(c.get("role") or "").strip(),
                "description": str(c.get("description") or "").strip(),
            }
        )

    locations: list[dict[str, Any]] = []
    for i, loc in enumerate(locs):
        if not isinstance(loc, dict):
            continue
        lid = str(loc.get("id") or f"l{i + 1}").strip()
        locations.append(
            {
                "id": lid,
                "name": str(loc.get("name") or f"Mekân {i + 1}").strip(),
                "description": str(loc.get("description") or "").strip(),
            }
        )

    scenes: list[dict[str, Any]] = []
    for i, sc in enumerate(scenes_in):
        if not isinstance(sc, dict):
            continue
        narration = str(sc.get("narration") or "").strip()
        if not narration or narration.startswith("Her sahne için"):
            continue
        sid = int(sc.get("scene_id") or i + 1)
        asset_raw = sc.get("asset_id")
        asset_id = str(asset_raw).strip() if asset_raw not in (None, "", "null") else ""
        scenes.append(
            {
                "scene_id": sid,
                "narration": narration,
                "character_ids": sc.get("character_ids") or [],
                "location_id": str(sc.get("location_id") or "").strip(),
                "mood": str(sc.get("mood") or "neutral").strip().lower(),
                "action": str(sc.get("action") or "").strip(),
                "visual_prompt": str(sc.get("visual_prompt") or "").strip(),
                "motion_prompt": str(sc.get("motion_prompt") or "").strip(),
                "asset_id": asset_id,
                "estimated_seconds": float(sc.get("estimated_seconds") or 45),
                "transition": "fade",
            }
        )

    rec = str(raw.get("render_recommendation") or "slideshow").strip().lower()
    if rec not in RENDER_MODES:
        rec = "motion" if any(s.get("asset_id") for s in scenes) else "slideshow"

    try:
        from ilim_assistant.video_create import video_render_capabilities

        mode_caps = video_render_capabilities()
    except Exception:
        mode_caps = {"slideshow": True, "motion": True, "portrait": False, "generative": False}

    return {
        "title": str(raw.get("title") or fallback_title or "Hikâye").strip(),
        "theme": str(raw.get("theme") or fallback_theme or "").strip(),
        "synopsis": str(raw.get("synopsis") or "").strip(),
        "characters": characters,
        "locations": locations,
        "scenes": scenes,
        "render_recommendation": rec,
        "render_mode_available": mode_caps,
        "capability_note": (
            "slideshow: sabit slayt. motion: V7.1 yerel sinematik hareket. "
            "portrait: V7.2 SadTalker (RUZGAR_SADTALKER_ROOT). "
            "generative: V8 Runway API (RUNWAY_API_KEY)."
        ),
    }


def storyboard_to_video_plan(board: dict[str, Any]) -> dict[str, Any]:
    """Storyboard → mevcut video_create plan formatı."""
    scenes = []
    for sc in board.get("scenes") or []:
        scenes.append(
            {
                "scene_id": sc.get("scene_id"),
                "narration": sc.get("narration"),
                "mood": sc.get("mood"),
                "visual_prompt": sc.get("visual_prompt"),
                "motion_prompt": sc.get("motion_prompt"),
                "action": sc.get("action"),
                "asset_id": sc.get("asset_id"),
                "estimated_seconds": sc.get("estimated_seconds"),
                "transition": sc.get("transition", "fade"),
            }
        )
    return {
        "title": board.get("title"),
        "theme": board.get("theme"),
        "synopsis": board.get("synopsis"),
        "characters": board.get("characters"),
        "locations": board.get("locations"),
        "render_recommendation": board.get("render_recommendation"),
        "scenes": scenes,
    }
