# Created by Ümit & Gökçenur
"""Tercüme Faz 8 — süper analist tam zincir (ara → al → oku → çevir → rapor)."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable

SUPER_ANALYST_VERSION = "tercume-super-analyst-v8-faz8-2026-05-31"
_PREVIEW_DIR_REL = "ilim-assistant/arsiv/tercume-output/super"


def super_analyst_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_SUPER", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _repo_root() -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root(None)
        if r:
            return Path(r)
    except Exception:
        pass
    return Path(__file__).resolve().parents[2]


def _resolve_rel(query: str, rel: str, analysis: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    from ilim_assistant.motorlar.tercume_analyst import prepare_import_from_search, run_tercume_pipeline

    steps: list[dict[str, Any]] = []
    read_rel = (rel or "").strip().replace("\\", "/").lstrip("/")

    if read_rel:
        steps.append({"step": "import", "ok": True, "mode": "provided", "rel": read_rel})
        return read_rel, steps

    plan = prepare_import_from_search(query=query)
    if not plan.get("ok"):
        steps.append({"step": "import", "ok": False, "error": plan.get("error")})
        return "", steps

    if plan.get("mode") == "local":
        read_rel = str(plan.get("rel") or "")
        steps.append({"step": "import", "ok": bool(read_rel), "mode": "local", "rel": read_rel})
        return read_rel, steps

    url = str(plan.get("download_url") or "")
    if not url:
        steps.append({"step": "import", "ok": False, "error": "İndirilecek URL yok"})
        return "", steps

    pipe = run_tercume_pipeline(
        query,
        download=True,
        download_url=url,
        target_dir_rel="ilim-assistant/arsiv/tercume-imports",
    )
    dl = pipe.get("download") or {}
    ok = bool(isinstance(dl, dict) and dl.get("ok"))
    read_rel = str(dl.get("rel") or "") if ok else ""
    steps.append(
        {
            "step": "import",
            "ok": ok,
            "mode": "download",
            "rel": read_rel,
            "error": dl.get("error") if isinstance(dl, dict) else None,
        }
    )
    return read_rel, steps


def _pick_translate_source(pages: list[dict[str, Any]], max_chars: int = 6000) -> tuple[str, int | None]:
    for p in pages:
        if not isinstance(p, dict):
            continue
        if str(p.get("quality") or "") == "empty":
            continue
        text = str(p.get("text") or "").strip()
        if len(text) >= 40:
            return text[:max_chars], int(p.get("index") if p.get("index") is not None else 0)
    return "", None


def _save_translate_preview(rel: str, translated: str, query: str) -> str:
    if not translated.strip():
        return ""
    from ilim_assistant.motorlar.tercume_analyst_report import _safe_slug

    slug = _safe_slug(query or Path(rel).stem)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_rel = f"{_PREVIEW_DIR_REL}/{slug}_{ts}_preview.txt"
    path = (_repo_root() / out_rel.replace("/", os.sep)).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(translated.strip(), encoding="utf-8")
    return out_rel


def run_super_analyst(
    user_query: str,
    *,
    rel: str = "",
    read_pages: int = 5,
    translate: bool = True,
    tgt_lang: str = "tr",
    src_lang: str = "auto",
    on_step: Callable[[str, str], None] | None = None,
) -> dict[str, Any]:
    """Tam zincir — adım adım sonuç döner."""
    if not super_analyst_enabled():
        return {"ok": False, "error": "Süper analist kapalı (RUZGAR_TERCUME_SUPER=0)."}

    query = (user_query or "").strip()
    if not query and not (rel or "").strip():
        return {"ok": False, "error": "query veya rel gerekli"}

    from ilim_assistant.motorlar.tercume_analyst import analyze_tercume_query
    from ilim_assistant.motorlar.tercume_analyst_report import (
        generate_analyst_report,
        save_report_file,
    )
    from ilim_assistant.motorlar.tercume_read_pipeline import extract_source_pages

    steps: list[dict[str, Any]] = []

    if on_step:
        on_step("analyze", "Kaynak analizi…")
    analysis = analyze_tercume_query(query or Path(rel).stem)
    if not analysis.get("ok"):
        return analysis
    steps.append({"step": "analyze", "ok": True, "quality": analysis.get("quality")})

    if on_step:
        on_step("import", "Arşive alınıyor…")
    read_rel, import_steps = _resolve_rel(query, rel, analysis)
    steps.extend(import_steps)
    if not read_rel:
        err = import_steps[-1].get("error") if import_steps else "Dosya yok"
        return {
            "ok": False,
            "error": str(err or "Kaynak dosyası alınamadı"),
            "steps": steps,
            "analysis": analysis,
        }

    if on_step:
        on_step("read", "Okuma kalitesi…")
    read_hit = extract_source_pages(read_rel)
    steps.append({"step": "read", "ok": bool(read_hit.get("ok")), "rel": read_rel})
    if not read_hit.get("ok"):
        return {
            "ok": False,
            "error": str(read_hit.get("error") or "Okuma hatası"),
            "steps": steps,
            "analysis": analysis,
            "rel": read_rel,
        }

    translate_hit: dict[str, Any] | None = None
    preview_rel = ""
    if translate:
        if on_step:
            on_step("translate", "Örnek çeviri…")
        pages = list(read_hit.get("pages") or [])
        src_text, page_idx = _pick_translate_source(pages)
        if src_text:
            from ilim_assistant.motorlar.tercume_atolye import translate_chunk

            translate_hit = translate_chunk(
                src_text,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                source_file=read_rel,
                page_index=page_idx,
            )
            steps.append({"step": "translate", "ok": bool(translate_hit.get("ok"))})
            if translate_hit.get("ok"):
                preview_rel = _save_translate_preview(
                    read_rel,
                    str(translate_hit.get("text") or ""),
                    query,
                )
        else:
            steps.append({"step": "translate", "ok": False, "error": "Çevrilecek metin yok"})

    if on_step:
        on_step("report", "Rapor yazılıyor…")
    report = generate_analyst_report(query or Path(read_rel).stem, rel=read_rel, read_pages=read_pages)
    if not report.get("ok"):
        return {**report, "steps": steps, "rel": read_rel}

    md = str(report.get("markdown") or "")
    if translate_hit and translate_hit.get("ok"):
        sample = str(translate_hit.get("text") or "").strip()[:2400]
        if sample:
            md += "\n\n## Örnek çeviri (süper analist)\n\n" + sample + "\n"
            report["markdown"] = md

    saved = save_report_file(report)
    steps.append({"step": "report", "ok": True, "report_rel": saved.get("report_rel")})

    return {
        "ok": True,
        "version": SUPER_ANALYST_VERSION,
        "query": query,
        "rel": read_rel,
        "analysis": analysis,
        "read_meta": report.get("read_meta"),
        "translate": translate_hit,
        "preview_rel": preview_rel,
        "report_rel": saved.get("report_rel"),
        "report_json_rel": saved.get("report_json_rel"),
        "next_steps": report.get("next_steps"),
        "markdown_preview": md[:1200],
        "steps": steps,
    }
