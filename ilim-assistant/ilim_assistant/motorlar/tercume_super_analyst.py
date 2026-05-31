# Created by Ümit & Gökçenur
"""Tercüme Faz 8/12 — süper analist tam zincir (ara → al → oku → çevir → rapor)."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable

SUPER_ANALYST_VERSION = "tercume-super-analyst-v9-faz12-2026-05-31"
_PREVIEW_DIR_REL = "ilim-assistant/arsiv/tercume-output/super"


def super_analyst_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_SUPER", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def checkpoint_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_SUPER_CHECKPOINT", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
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


def _run_translate_step(
    read_rel: str,
    read_hit: dict[str, Any],
    *,
    query: str,
    src_lang: str,
    tgt_lang: str,
) -> tuple[dict[str, Any] | None, str, dict[str, Any]]:
    from ilim_assistant.motorlar.tercume_atolye import translate_chunk

    pages = list(read_hit.get("pages") or [])
    src_text, page_idx = _pick_translate_source(pages)
    translate_hit: dict[str, Any] | None = None
    preview_rel = ""
    step: dict[str, Any] = {"step": "translate", "ok": False}
    if src_text:
        translate_hit = translate_chunk(
            src_text,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            source_file=read_rel,
            page_index=page_idx,
        )
        step["ok"] = bool(translate_hit.get("ok"))
        if translate_hit.get("ok"):
            preview_rel = _save_translate_preview(
                read_rel,
                str(translate_hit.get("text") or ""),
                query,
            )
    else:
        step["error"] = "Çevrilecek metin yok"
    return translate_hit, preview_rel, step


def run_super_analyst(
    user_query: str,
    *,
    rel: str = "",
    read_pages: int = 5,
    translate: bool = True,
    tgt_lang: str = "tr",
    src_lang: str = "auto",
    on_step: Callable[[str, str], None] | None = None,
    checkpoint: bool | None = None,
    resume_state: dict[str, Any] | None = None,
    skip_translate: bool = False,
) -> dict[str, Any]:
    """Tam zincir — adım adım sonuç döner. Checkpoint modunda rapordan sonra durur."""
    if not super_analyst_enabled():
        return {"ok": False, "error": "Süper analist kapalı (RUZGAR_TERCUME_SUPER=0)."}

    use_checkpoint = checkpoint if checkpoint is not None else checkpoint_enabled()

    if resume_state:
        return _resume_super_from_state(resume_state, skip_translate=skip_translate, on_step=on_step)

    query = (user_query or "").strip()
    if not query and not (rel or "").strip():
        return {"ok": False, "error": "query veya rel gerekli"}

    from ilim_assistant.motorlar.tercume_preflight import run_tercume_preflight

    pf = run_tercume_preflight(rel=rel, need_internet=not bool((rel or "").strip()))
    if not pf.get("ready"):
        return {
            "ok": False,
            "error": "Kapı kontrolü geçmedi — hazırlık eksik.",
            "preflight": pf,
            "hints": pf.get("hints") or [],
        }

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

    if on_step:
        on_step("report", "Rapor yazılıyor…")
    report = generate_analyst_report(query or Path(read_rel).stem, rel=read_rel, read_pages=read_pages)
    if not report.get("ok"):
        return {**report, "steps": steps, "rel": read_rel}

    md = str(report.get("markdown") or "")
    saved = save_report_file(report)
    steps.append({"step": "report", "ok": True, "report_rel": saved.get("report_rel")})

    pause_before_translate = use_checkpoint and translate and not skip_translate
    if pause_before_translate:
        qs = read_hit.get("meta", {}).get("quality_summary") or {}
        return {
            "ok": True,
            "paused": True,
            "checkpoint": "before_translate",
            "version": SUPER_ANALYST_VERSION,
            "query": query,
            "rel": read_rel,
            "analysis": analysis,
            "read_meta": report.get("read_meta"),
            "report_rel": saved.get("report_rel"),
            "report_json_rel": saved.get("report_json_rel"),
            "next_steps": report.get("next_steps"),
            "markdown_preview": md[:1200],
            "steps": steps,
            "checkpoint_message": (
                f"Okuma tamam — {qs.get('ok', '?')} iyi, {qs.get('low', '?')} zayıf sayfa. "
                "Çeviriye devam edilsin mi?"
            ),
            "resume_state": {
                "query": query,
                "rel": read_rel,
                "read_pages": read_pages,
                "tgt_lang": tgt_lang,
                "src_lang": src_lang,
                "report_rel": saved.get("report_rel"),
                "report_json_rel": saved.get("report_json_rel"),
                "markdown": md,
                "steps": steps,
                "analysis": analysis,
                "read_meta": report.get("read_meta"),
                "next_steps": report.get("next_steps"),
            },
        }

    translate_hit: dict[str, Any] | None = None
    preview_rel = ""
    if translate and not skip_translate:
        if on_step:
            on_step("translate", "Örnek çeviri…")
        translate_hit, preview_rel, tr_step = _run_translate_step(
            read_rel,
            read_hit,
            query=query,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
        )
        steps.append(tr_step)
        if translate_hit and translate_hit.get("ok"):
            sample = str(translate_hit.get("text") or "").strip()[:2400]
            if sample:
                md += "\n\n## Örnek çeviri (süper analist)\n\n" + sample + "\n"
                report["markdown"] = md
                saved = save_report_file(report)

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


def _resume_super_from_state(
    state: dict[str, Any],
    *,
    skip_translate: bool = False,
    on_step: Callable[[str, str], None] | None = None,
) -> dict[str, Any]:
    from ilim_assistant.motorlar.tercume_analyst_report import save_report_file
    from ilim_assistant.motorlar.tercume_read_pipeline import extract_source_pages

    query = str(state.get("query") or "")
    read_rel = str(state.get("rel") or "")
    steps = list(state.get("steps") or [])
    md = str(state.get("markdown") or "")
    report = {
        "ok": True,
        "markdown": md,
        "rel": read_rel,
        "query": query,
        "read_meta": state.get("read_meta"),
        "next_steps": state.get("next_steps"),
        "analysis": state.get("analysis"),
    }

    translate_hit: dict[str, Any] | None = None
    preview_rel = ""
    if not skip_translate:
        if on_step:
            on_step("translate", "Onaylı örnek çeviri…")
        read_hit = extract_source_pages(read_rel)
        if read_hit.get("ok"):
            translate_hit, preview_rel, tr_step = _run_translate_step(
                read_rel,
                read_hit,
                query=query,
                src_lang=str(state.get("src_lang") or "auto"),
                tgt_lang=str(state.get("tgt_lang") or "tr"),
            )
            steps.append(tr_step)
            if translate_hit and translate_hit.get("ok"):
                sample = str(translate_hit.get("text") or "").strip()[:2400]
                if sample:
                    md += "\n\n## Örnek çeviri (süper analist — onaylı)\n\n" + sample + "\n"
                    report["markdown"] = md

    saved = save_report_file(report)
    steps.append({"step": "report", "ok": True, "report_rel": saved.get("report_rel"), "updated": True})

    return {
        "ok": True,
        "version": SUPER_ANALYST_VERSION,
        "query": query,
        "rel": read_rel,
        "analysis": state.get("analysis"),
        "read_meta": state.get("read_meta"),
        "translate": translate_hit,
        "preview_rel": preview_rel,
        "report_rel": saved.get("report_rel"),
        "report_json_rel": saved.get("report_json_rel"),
        "next_steps": state.get("next_steps"),
        "markdown_preview": md[:1200],
        "steps": steps,
        "resumed": True,
        "skipped_translate": skip_translate,
    }
