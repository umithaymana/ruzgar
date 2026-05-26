# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 45: Editör cila (çok dosya sekmeleri, diff v2, birleşik UX).

- Satır bazlı renkli diff (ekle/sil/bağlam)
- Bekleyen patch sekmeleri
- Görev modu + patch onay/uygula birleşik durum
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Any

FAZ45_VERSION = "programlama-faz45-v1-2026-05-25"

_LANG_BY_EXT: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sh": "shell",
    ".ps1": "powershell",
}


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ45", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def editor_v2_enabled() -> bool:
    if _enabled():
        return True
    try:
        from ilim_assistant.motorlar.programlama_faz53 import atolye_editor_v2_enabled

        return atolye_editor_v2_enabled()
    except Exception:
        return False


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def detect_lang_from_path(rel_path: str) -> str:
    ext = Path(_norm_rel(rel_path)).suffix.lower()
    return _LANG_BY_EXT.get(ext, "plaintext")


def build_line_diff_segments(
    old_text: str,
    new_text: str,
    *,
    max_lines: int = 400,
) -> list[dict[str, Any]]:
    """Satır bazlı diff segmentleri (UI syntax renk)."""
    import difflib

    old_lines = (old_text or "").splitlines()
    new_lines = (new_text or "").splitlines()
    segments: list[dict[str, Any]] = []
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if len(segments) >= max_lines:
            segments.append({"kind": "ctx", "text": "… (diff kısaltıldı)", "old_ln": None, "new_ln": None})
            break
        if tag == "equal":
            for k, line in enumerate(old_lines[i1:i2]):
                segments.append(
                    {
                        "kind": "ctx",
                        "text": line,
                        "old_ln": i1 + k + 1,
                        "new_ln": j1 + k + 1,
                    }
                )
        elif tag == "delete":
            for k, line in enumerate(old_lines[i1:i2]):
                segments.append(
                    {"kind": "del", "text": line, "old_ln": i1 + k + 1, "new_ln": None}
                )
        elif tag == "insert":
            for k, line in enumerate(new_lines[j1:j2]):
                segments.append(
                    {"kind": "add", "text": line, "old_ln": None, "new_ln": j1 + k + 1}
                )
        elif tag == "replace":
            for k, line in enumerate(old_lines[i1:i2]):
                segments.append(
                    {"kind": "del", "text": line, "old_ln": i1 + k + 1, "new_ln": None}
                )
            for k, line in enumerate(new_lines[j1:j2]):
                segments.append(
                    {"kind": "add", "text": line, "old_ln": None, "new_ln": j1 + k + 1}
                )
    return segments


def _highlight_token(line: str, lang: str) -> str:
    """Hafif sözdizimi vurgusu (tam lexer değil)."""
    esc = html.escape(line)
    if lang == "python":
        esc = re.sub(
            r"\b(def|class|import|from|return|async|await|if|else|elif|for|while|try|except|with|as)\b",
            r'<span class="syn-kw">\1</span>',
            esc,
        )
        esc = re.sub(
            r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
            r'<span class="syn-str">\1</span>',
            esc,
        )
        esc = re.sub(r"\b(\d+)\b", r'<span class="syn-num">\1</span>', esc)
    elif lang in ("javascript", "typescript"):
        esc = re.sub(
            r"\b(const|let|var|function|export|import|return|async|await|class|if|else)\b",
            r'<span class="syn-kw">\1</span>',
            esc,
        )
        esc = re.sub(
            r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|`(?:[^`\\]|\\.)*`)',
            r'<span class="syn-str">\1</span>',
            esc,
        )
    return esc


def segments_to_html(
    segments: list[dict[str, Any]],
    *,
    lang: str = "plaintext",
    side: str = "unified",
) -> str:
    """Segment listesinden HTML satırlar."""
    rows: list[str] = []
    for seg in segments:
        kind = str(seg.get("kind") or "ctx")
        text = str(seg.get("text") or "")
        cls = f"diff-line diff-line-{kind}"
        if side == "old" and kind == "add":
            continue
        if side == "new" and kind == "del":
            continue
        body = _highlight_token(text, lang) if text else "&nbsp;"
        old_ln = seg.get("old_ln")
        new_ln = seg.get("new_ln")
        ln = ""
        if side == "old":
            ln = f'<span class="diff-ln">{old_ln or ""}</span>'
        elif side == "new":
            ln = f'<span class="diff-ln">{new_ln or ""}</span>'
        else:
            ln_num = new_ln if kind == "add" else old_ln if kind == "del" else (new_ln or old_ln or "")
            ln = f'<span class="diff-ln">{ln_num or ""}</span>'
        sign = "+" if kind == "add" else "-" if kind == "del" else " "
        rows.append(
            f'<div class="{cls}" data-kind="{kind}">{ln}<span class="diff-sign">{sign}</span><code class="diff-code lang-{lang}">{body}</code></div>'
        )
    return "\n".join(rows) if rows else '<div class="diff-line diff-line-ctx"><code>(boş)</code></div>'


def build_inline_diff_v2(
    workspace_root: str | Path | None,
    rel_path: str,
    *,
    new_content: str | None = None,
) -> dict[str, Any]:
    """Faz 27 yükü + diff v2 segmentleri."""
    from ilim_assistant.motorlar.programlama_faz27 import build_inline_diff_for_path

    base = build_inline_diff_for_path(
        workspace_root, rel_path, new_content=new_content
    )
    if not base.get("ok") or not _enabled():
        base["editor_v2"] = False
        return base
    rel = _norm_rel(rel_path)
    lang = detect_lang_from_path(rel)
    old_t = str(base.get("old_text") or "")
    new_t = str(base.get("new_text") or "")
    segments = build_line_diff_segments(old_t, new_t)
    base.update(
        {
            "editor_v2": True,
            "lang": lang,
            "segments": segments[:400],
            "html_unified": segments_to_html(segments, lang=lang, side="unified"),
            "html_old": segments_to_html(segments, lang=lang, side="old"),
            "html_new": segments_to_html(segments, lang=lang, side="new"),
            "stats": {
                "add": sum(1 for s in segments if s.get("kind") == "add"),
                "del": sum(1 for s in segments if s.get("kind") == "del"),
                "ctx": sum(1 for s in segments if s.get("kind") == "ctx"),
            },
            "version": FAZ45_VERSION,
        }
    )
    return base


def build_patch_tabs(
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    """Çok dosya patch sekmeleri."""
    from ilim_assistant.motorlar.programlama_faz16 import build_pending_bundle

    bundle = build_pending_bundle(workspace_root)
    items = list(bundle.get("items") or [])
    tabs: list[dict[str, Any]] = []
    for it in items:
        rel = _norm_rel(str(it.get("path") or ""))
        if not rel:
            continue
        st = str(it.get("status") or "pending")
        tabs.append(
            {
                "path": rel,
                "status": st,
                "lang": detect_lang_from_path(rel),
                "basename": Path(rel).name,
            }
        )
    return {
        "ok": True,
        "tabs": tabs,
        "count": len(tabs),
        "counts": bundle.get("counts") or {},
        "active": tabs[0]["path"] if tabs else None,
        "version": FAZ45_VERSION,
    }


def build_unified_patch_ux(
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    """Bekleyen patch + görev modu birleşik UX durumu."""
    from ilim_assistant.motorlar.programlama_faz16 import build_pending_bundle

    bundle = build_pending_bundle(workspace_root)
    counts = bundle.get("counts") or {}
    pending_n = int(counts.get("pending") or 0)
    accepted_n = int(counts.get("accepted") or 0)

    task_mode = False
    task_auto = False
    try:
        from ilim_assistant.motorlar.programlama_faz23 import (
            task_auto_apply_enabled,
            task_mode_active,
        )

        task_mode = task_mode_active()
        task_auto = task_auto_apply_enabled()
    except Exception:
        pass

    actions: list[str] = []
    if pending_n > 0:
        actions.append("accept_all")
    if accepted_n > 0:
        actions.append("apply_accepted")
    if pending_n > 0 and not task_auto:
        actions.append("apply_all_pending")
    if task_mode and task_auto:
        actions.append("task_auto_active")

    hint = "Bekleyen patch yok."
    if task_mode and task_auto:
        hint = "Görev modu: patch otomatik diske yazılır."
    elif pending_n and accepted_n:
        hint = f"{pending_n} bekleyen · {accepted_n} kabul — «Birleşik uygula» önerilir."
    elif pending_n:
        hint = f"{pending_n} dosya bekliyor — önce kabul veya «Tümünü kabul»."
    elif accepted_n:
        hint = f"{accepted_n} kabul edildi — «Kabul edilenleri uygula»."

    return {
        "ok": True,
        "task_mode": task_mode,
        "task_auto_apply": task_auto,
        "counts": counts,
        "pending_count": pending_n,
        "accepted_count": accepted_n,
        "recommended_actions": actions,
        "hint": hint,
        "tabs": build_patch_tabs(workspace_root).get("tabs") or [],
        "version": FAZ45_VERSION,
    }


def run_unified_apply(
    workspace_root: str | Path | None,
    *,
    run_verify: bool = True,
) -> dict[str, Any]:
    """Kabul et + kabul edilenleri uygula (tek adım)."""
    from ilim_assistant.motorlar.programlama_faz16 import (
        accept_all_pending,
        apply_pending_selective,
        build_pending_bundle,
    )

    steps: list[str] = []
    acc = accept_all_pending(workspace_root)
    if acc.get("accepted"):
        steps.append(f"kabul:{len(acc['accepted'])}")
    applied = apply_pending_selective(
        workspace_root, mode="accepted", run_verify=run_verify
    )
    if applied.get("applied"):
        steps.append(f"uygula:{len(applied['applied'])}")
    bundle = build_pending_bundle(workspace_root)
    return {
        "ok": bool(applied.get("ok")),
        "steps": steps,
        "accept": acc,
        "apply": applied,
        "bundle": bundle,
        "report": applied.get("report") or "",
        "version": FAZ45_VERSION,
    }


def enrich_pending_items_v45(
    workspace_root: str | Path | None,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not _enabled() or not items:
        return items
    out: list[dict[str, Any]] = []
    for it in items:
        row = dict(it)
        rel = _norm_rel(str(row.get("path") or ""))
        if rel:
            v2 = build_inline_diff_v2(
                workspace_root, rel, new_content=str(row.get("content") or "")
            )
            if v2.get("ok"):
                row["lang"] = v2.get("lang")
                row["diff_stats"] = v2.get("stats")
                row["editor_v2"] = True
        out.append(row)
    return out


def faz45_directive() -> str:
    return (
        "[EDİTÖR v2 — Faz 45]\n"
        "Çok dosya patch sekmesi; renkli satır diff; «birleşik uygula» = kabul+uygula.\n"
        "Kapat: RUZGAR_FAZ45=0\n"
    )
