# Created by Ümit & Gökçenur
"""Tercüme Faz 7 — analist araştırma raporu (ara → oku → özet)."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

ANALYST_REPORT_VERSION = "tercume-analyst-report-v7-faz7-2026-05-31"
_REPORT_DIR_REL = "ilim-assistant/arsiv/tercume-output/reports"


def report_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_REPORT", "1").strip().lower() not in (
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


def _safe_slug(text: str, limit: int = 48) -> str:
    t = re.sub(r"[^\w\u0600-\u06FF\-]+", "_", (text or "").strip(), flags=re.UNICODE)
    t = re.sub(r"_+", "_", t).strip("_")
    return (t or "rapor")[:limit]


def _next_steps(analysis: dict[str, Any], read_meta: dict[str, Any] | None) -> list[str]:
    steps: list[str] = []
    if analysis.get("local_first"):
        steps.append("Arşivde dosya var — Çalışma sekmesinden açıp Çevir deyin.")
    top = (analysis.get("items") or [{}])[0] if analysis.get("items") else {}
    if top.get("local_rel"):
        steps.append(f"Yerel dosya: «{top.get('title', '')[:60]}» — listeden açın.")
    elif analysis.get("suggested_download_url"):
        steps.append("Arama sekmesinde «Arşive al» ile PDF indirin.")
    elif analysis.get("quality") == "weak":
        steps.append("Sonuç zayıf — sorguyu yazar+eser olarak kısaltın; Scholar'a bakın.")
    else:
        steps.append("En iyi satırdan siteyi açın veya Arşive al ile indirin.")

    qs = (read_meta or {}).get("quality_summary") or {}
    if qs.get("ocr_recommended"):
        steps.append("Okuma: taranmış sayfa uyarısı — OCR veya daha iyi PDF deneyin.")
    elif qs.get("low", 0) > qs.get("ok", 0):
        steps.append("Okuma: çoğu sayfa zayıf — kaynak PDF kalitesini kontrol edin.")
    elif read_meta:
        steps.append("Okuma kalitesi kabul edilebilir — sayfa sayfa çeviriye geçebilirsiniz.")

    if not steps:
        steps.append("Çalışma sekmesinde dosya açıp hedef dili seçerek çevirin.")
    return steps[:6]


def build_report_markdown(
    analysis: dict[str, Any],
    *,
    rel: str = "",
    read_meta: dict[str, Any] | None = None,
    read_pages_sample: list[dict[str, Any]] | None = None,
) -> str:
    q = str(analysis.get("query") or "")
    lines = [
        "# Tercüme analist raporu",
        "",
        f"**Sorgu:** {q}",
        f"**Kalite:** {analysis.get('quality') or '—'}",
        f"**Versiyon:** {ANALYST_REPORT_VERSION}",
        "",
        "## Özet",
        str(analysis.get("summary") or "—"),
        "",
    ]
    exp = str(analysis.get("expanded_query") or "").strip()
    if exp and exp != q:
        lines.extend([f"**Genişletilmiş arama:** {exp}", ""])

    lines.append("## En iyi kaynaklar")
    items = list(analysis.get("items") or [])[:8]
    if not items:
        lines.append("- Sonuç yok.")
    else:
        for i, it in enumerate(items, 1):
            if not isinstance(it, dict):
                continue
            title = str(it.get("title") or "—")[:100]
            src = str(it.get("source") or "")
            sc = it.get("score")
            conf = str(it.get("confidence") or "")
            tag = f" ({conf} {sc:.0f})" if sc is not None else ""
            local = " · **arşivde**" if it.get("local_rel") else ""
            lines.append(f"{i}. **{title}** — {src}{tag}{local}")

    local = list(analysis.get("local_archive_matches") or [])
    if local:
        lines.extend(["", "## Yerel arşiv eşleşmeleri"])
        for m in local[:6]:
            if isinstance(m, dict):
                lines.append(f"- `{m.get('rel', m.get('name', ''))}`")

    if rel:
        lines.extend(["", f"## Okunan dosya", f"`{rel}`", ""])
    if read_meta:
        qs = read_meta.get("quality_summary") or {}
        lines.extend(
            [
                "## Okuma kalitesi",
                f"- Toplam sayfa/parça: **{qs.get('total') or read_meta.get('pages_total') or '—'}**",
                f"- Boş: {qs.get('empty', 0)} · Zayıf: {qs.get('low', 0)} · İyi: {qs.get('ok', 0)}",
            ]
        )
        if read_meta.get("read_hint"):
            lines.append(f"- {read_meta.get('read_hint')}")
        if qs.get("ocr_recommended"):
            lines.append("- **OCR önerilir** (taranmış sayfa).")

    if read_pages_sample:
        lines.extend(["", "## Örnek parçalar (ilk sayfalar)"])
        for p in read_pages_sample[:3]:
            if not isinstance(p, dict):
                continue
            label = str(p.get("label") or f"S{int(p.get('index') or 0) + 1}")
            qv = str(p.get("quality") or "")
            snip = str(p.get("text") or "").strip()[:280]
            if snip:
                lines.append(f"### {label} ({qv})")
                lines.append(snip)
                lines.append("")

    lines.extend(["", "## Önerilen adımlar"])
    for step in _next_steps(analysis, read_meta):
        lines.append(f"- {step}")

    lines.append("")
    return "\n".join(lines)


def generate_analyst_report(
    user_query: str,
    *,
    rel: str = "",
    read_pages: int = 5,
) -> dict[str, Any]:
    """Analiz + isteğe bağlı dosya okuma → yapılandırılmış rapor."""
    if not report_enabled():
        return {"ok": False, "error": "Analist raporu kapalı (RUZGAR_TERCUME_REPORT=0)."}

    from ilim_assistant.motorlar.tercume_analyst import analyze_tercume_query

    raw = (user_query or "").strip()
    if not raw and not (rel or "").strip():
        return {"ok": False, "error": "query veya rel gerekli"}

    analysis = analyze_tercume_query(raw or Path(rel).stem)
    if not analysis.get("ok"):
        return analysis

    read_meta: dict[str, Any] | None = None
    read_pages_sample: list[dict[str, Any]] | None = None
    read_rel = (rel or "").strip().replace("\\", "/").lstrip("/")

    if not read_rel:
        for it in analysis.get("items") or []:
            if isinstance(it, dict) and it.get("local_rel"):
                read_rel = str(it.get("local_rel"))
                break

    if read_rel:
        from ilim_assistant.motorlar.tercume_read_pipeline import extract_source_pages

        hit = extract_source_pages(read_rel)
        if hit.get("ok"):
            pages = list(hit.get("pages") or [])
            read_meta = dict(hit.get("meta") or {})
            cap = max(1, min(int(read_pages or 5), 25))
            read_pages_sample = pages[:cap]
        else:
            read_meta = {"read_error": str(hit.get("error") or "okuma hatası")}

    markdown = build_report_markdown(
        analysis,
        rel=read_rel,
        read_meta=read_meta,
        read_pages_sample=read_pages_sample,
    )

    return {
        "ok": True,
        "version": ANALYST_REPORT_VERSION,
        "query": analysis.get("query"),
        "quality": analysis.get("quality"),
        "rel": read_rel,
        "analysis": analysis,
        "read_meta": read_meta,
        "markdown": markdown,
        "next_steps": _next_steps(analysis, read_meta),
        "generated_at": time.time(),
    }


def save_report_file(report: dict[str, Any]) -> dict[str, Any]:
    """Raporu arşiv reports/ altına yazar."""
    if not report.get("ok"):
        return {"ok": False, "error": "Rapor geçersiz"}

    slug = _safe_slug(str(report.get("query") or "rapor"))
    ts = time.strftime("%Y%m%d_%H%M%S")
    rel = f"{_REPORT_DIR_REL}/{slug}_{ts}_report.md"
    json_rel = f"{_REPORT_DIR_REL}/{slug}_{ts}_report.json"

    root = _repo_root()
    md_path = (root / rel.replace("/", os.sep)).resolve()
    json_path = (root / json_rel.replace("/", os.sep)).resolve()
    md_path.parent.mkdir(parents=True, exist_ok=True)

    md_path.write_text(str(report.get("markdown") or ""), encoding="utf-8")

    slim = {
        "ok": True,
        "version": ANALYST_REPORT_VERSION,
        "query": report.get("query"),
        "quality": report.get("quality"),
        "rel": report.get("rel"),
        "next_steps": report.get("next_steps"),
        "read_meta": report.get("read_meta"),
        "generated_at": report.get("generated_at"),
    }
    json_path.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "report_rel": rel,
        "report_json_rel": json_rel,
        "report_abs": str(md_path),
    }
