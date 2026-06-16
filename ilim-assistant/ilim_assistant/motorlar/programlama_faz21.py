# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 21: hafif bağlam (Cursor hızı).

Kod/programlama turunda ağır RAG, dinamit, orkestra ve geniş repo haritası atlanır.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

FAZ21_VERSION = "programlama-faz21-v2-2026-06-16"

_PY_FROM_IMPORT_RE = re.compile(
    r"^\s*from\s+([\w.]+)\s+import\s+",
    re.M,
)
_PY_IMPORT_RE = re.compile(
    r"^\s*import\s+([\w.]+)",
    re.M,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_LIGHT_CONTEXT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def light_context_enabled() -> bool:
    return _enabled()


def max_context_lines() -> int:
    try:
        return max(20, min(int(os.environ.get("RUZGAR_PROG_CONTEXT_LINES", "48")), 120))
    except ValueError:
        return 48


def build_light_programming_context(
    message: str,
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
    editor_snippet: str | None = None,
    include_tools: bool = True,
) -> str:
    """Cursor-benzeri kompakt bağlam — hedef < 8K karakter."""
    from ilim_assistant.prompts import pick_system

    t0 = time.perf_counter()
    parts: list[str] = [
        "[PROGRAMLAMA — hafif bağlam — Faz 21]",
        pick_system(True, "programlama").strip()[:2500],
    ]
    try:
        from ilim_assistant.motorlar.programlama_faz5 import (
            format_session_context_block,
            usta_coding_directive,
        )

        parts.append(usta_coding_directive().strip()[:800])
        sess = format_session_context_block(workspace_root).strip()
        if sess:
            parts.append(sess[:1200])
    except Exception:
        pass

    scope = None
    try:
        from ilim_assistant.motorlar.programlama_faz13 import (
            build_project_summary_block,
            resolve_scope_rel,
        )

        scope = resolve_scope_rel(
            workspace_root, active_file=active_file, message=message
        )
        summary = build_project_summary_block(
            workspace_root, scope_rel=scope
        ).strip()
        if summary:
            parts.append(summary[:3500])
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz79 import format_handoff_context_block

        h79 = format_handoff_context_block(
            message,
            workspace_root,
            active_file=active_file,
        )
        if h79:
            parts.append(h79[:4000])
    except Exception:
        pass

    if scope:
        try:
            from ilim_assistant.motorlar.programlama_faz44 import (
                build_context_v3_block,
                context_v3_enabled,
            )

            if context_v3_enabled():
                v3 = build_context_v3_block(
                    workspace_root,
                    scope_rel=scope,
                    message=message,
                    active_file=active_file,
                ).strip()
                if v3:
                    parts.append(v3[:5500])
        except Exception:
            pass

    if active_file:
        parts.append(f"[AKTİF DOSYA]\n`{active_file}`")
        try:
            from ilim_assistant.motorlar.programlama_context_budget import max_file_read_chars
            from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

            cap = max_file_read_chars()
            rep = ProgramlamaAraclari(workspace_root).read(active_file, max_chars=cap)
            if rep.ok and rep.content.strip():
                parts.append(f"[AKTİF DOSYA İÇERİK]\n```\n{rep.content[:cap]}\n```")
        except Exception:
            pass
        try:
            chain = build_import_chain_block(
                workspace_root,
                active_file=active_file,
                scope_rel=scope,
            )
            if chain:
                parts.append(chain)
        except Exception:
            pass
    snip = (editor_snippet or "").strip()
    if snip:
        parts.append(f"[EDİTÖR]\n```\n{snip[:2000]}\n```")

    if scope:
        try:
            from ilim_assistant.motorlar.programlama_faz10 import build_workspace_index

            idx = build_workspace_index(
                workspace_root,
                scope_rel=scope,
                max_lines=max_context_lines(),
            ).strip()
            if idx:
                parts.append(f"[İNDEKS]\n{idx}")
        except Exception:
            pass

    if scope:
        try:
            from ilim_assistant.motorlar.programlama_faz53 import (
                symbol_lite_enabled,
                augment_agent_context_parts,
            )

            if symbol_lite_enabled():
                parts = augment_agent_context_parts(
                    parts,
                    workspace_root,
                    scope_rel=scope,
                    message=message,
                )
            else:
                from ilim_assistant.motorlar.programlama_faz22 import compact_symbol_context

                sym_hint = compact_symbol_context(workspace_root, scope, message).strip()
                if sym_hint:
                    parts.append(sym_hint[:2000])
        except Exception:
            try:
                from ilim_assistant.motorlar.programlama_faz22 import compact_symbol_context

                sym_hint = compact_symbol_context(workspace_root, scope, message).strip()
                if sym_hint:
                    parts.append(sym_hint[:2000])
            except Exception:
                pass

    if scope and message and len((message or "").split()) >= 2:
        try:
            from ilim_assistant.motorlar.programlama_root_cause_learn import (
                build_root_cause_learn_block,
                root_cause_learn_enabled,
            )

            if root_cause_learn_enabled():
                rc = build_root_cause_learn_block(
                    workspace_root, scope_rel=scope
                )
                if rc:
                    parts.append(rc[:3500])
        except Exception:
            pass

    if scope and message and len((message or "").split()) >= 2:
        try:
            from ilim_assistant.motorlar.programlama_code_index import (
                code_index_enabled,
                format_semantic_block,
            )

            if code_index_enabled():
                sem = format_semantic_block(
                    workspace_root, message, scope_rel=scope, top_k=4
                )
                if sem:
                    parts.append(sem[:4000])
        except Exception:
            pass

    for directive_fn in (
        "programlama_faz46.faz46_directive",
        "programlama_faz45.faz45_directive",
        "programlama_faz44.faz44_directive",
        "programlama_faz43.faz43_directive",
        "programlama_faz42.faz42_directive",
        "programlama_faz41.faz41_directive",
        "programlama_faz40.faz40_directive",
        "programlama_faz39.faz39_directive",
        "programlama_faz38.faz38_directive",
        "programlama_faz37.faz37_directive",
        "programlama_faz36.faz36_directive",
        "programlama_faz35.faz35_directive",
        "programlama_faz34.faz34_directive",
        "programlama_faz33.faz33_directive",
        "programlama_faz32.faz32_directive",
        "programlama_faz31.faz31_directive",
        "programlama_faz30.faz30_directive",
        "programlama_faz29.faz29_directive",
        "programlama_faz28.faz28_directive",
        "programlama_faz27.faz27_directive",
        "programlama_faz26.faz26_directive",
        "programlama_faz25.faz25_directive",
        "programlama_faz24.faz24_directive",
        "programlama_faz23.faz23_directive",
        "programlama_faz22.faz22_directive",
        "programlama_faz20.faz20_tool_directive",
        "programlama_faz14.faz14_directive",
        "programlama_faz16.faz16_directive",
        "programlama_faz17.faz17_directive",
        "programlama_faz79.faz79_directive",
        "programlama_faz84.faz84_directive",
        "programlama_faz85.faz85_directive",
        "programlama_faz86.faz86_directive",
        "programlama_faz97.faz97_directive",
        "programlama_faz98.faz98_directive",
    ):
        try:
            mod, fn = directive_fn.rsplit(".", 1)
            import importlib

            d = getattr(importlib.import_module(f"ilim_assistant.motorlar.{mod}"), fn)()
            parts.append(d.strip()[:600])
        except Exception:
            pass

    if include_tools and (message or "").strip():
        try:
            from ilim_assistant.motorlar.programlama_motoru import run_tools_for_message

            _, tools_block = run_tools_for_message(
                message, workspace_root, run_presets=False
            )
            if tools_block.strip():
                try:
                    from ilim_assistant.motorlar.programlama_context_budget import (
                        max_context_chars,
                        max_file_read_chars,
                    )

                    tools_cap = min(max_file_read_chars(), max_context_chars() // 2)
                except Exception:
                    tools_cap = 12000
                parts.append(tools_block[:tools_cap])
        except Exception:
            pass

    parts.append(f"\n[Kullanıcı]\n{(message or '').strip()}\n")
    elapsed = time.perf_counter() - t0
    parts.append(f"({FAZ21_VERSION} · {elapsed:.2f}s hazırlık)")

    try:
        from ilim_assistant.motorlar.programlama_patch import patch_directive

        parts.append(patch_directive()[:500])
    except Exception:
        pass

    raw = "\n\n".join(p for p in parts if p.strip())
    try:
        from ilim_assistant.motorlar.programlama_context_budget import (
            assemble_context,
            ContextPart,
            context_budget_enabled,
            directive_priority_map,
        )

        if context_budget_enabled():
            pri = directive_priority_map()
            ctx_parts: list[ContextPart] = []
            for i, chunk in enumerate(raw.split("\n\n")):
                key = "misc_directive"
                head = chunk[:40].lower()
                if "faz 21" in head or "[programlama" in head:
                    key = "system"
                elif "[kullanıcı]" in head or "[kullanici]" in head:
                    key = "user"
                elif "[proje" in head or "özet" in head:
                    key = "summary"
                elif "[aktif" in head:
                    key = "active_file"
                elif "import zincir" in head or "[import" in head:
                    key = "import_chain"
                elif "[i̇ndeks]" in head or "[indeks]" in head:
                    key = "index"
                elif "hafiza" in head or "havuz" in head:
                    key = "session"
                elif "patch" in head:
                    key = "patch"
                ctx_parts.append(
                    ContextPart(
                        key=f"p{i}",
                        text=chunk,
                        priority=pri.get(key, 50),
                    )
                )
            raw, _ = assemble_context(ctx_parts)
            footer = f"({FAZ21_VERSION} · {elapsed:.2f}s hazırlık)"
            if FAZ21_VERSION not in raw:
                raw = raw.rstrip() + "\n\n" + footer
    except Exception:
        pass
    return raw


def wrap_prepare_turn_light(
    *,
    skip_super_brain: bool = True,
    skip_idrak_layer: bool = True,
    skip_bilissel: bool = True,
) -> dict[str, bool]:
    return {
        "skip_super_brain": skip_super_brain,
        "skip_idrak_layer": skip_idrak_layer,
        "skip_bilissel": skip_bilissel,
    }


def apply_light_prepare_flags() -> dict[str, bool]:
    """chat_core prepare_turn için bayraklar."""
    return wrap_prepare_turn_light()


def import_chain_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_IMPORT_CHAIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _import_chain_max_files() -> int:
    try:
        return max(1, min(int(os.environ.get("RUZGAR_PROG_IMPORT_CHAIN_MAX", "4")), 8))
    except ValueError:
        return 4


def _local_import_targets(active_file: str, source: str, scope_rel: str | None) -> list[str]:
    """Aktif dosyadaki yerel importları göreli yollara çevir."""
    active = (active_file or "").replace("\\", "/").lstrip("/")
    scope = (scope_rel or "").replace("\\", "/").strip("/")
    if not active.endswith(".py"):
        return []
    active_dir = "/".join(active.split("/")[:-1])
    scope_prefix = f"{scope}/" if scope and not active.startswith(f"{scope}/") else ""
    if scope and active.startswith(f"{scope}/"):
        scope_prefix = ""
    targets: list[str] = []
    seen: set[str] = set()

    def _add(rel: str) -> None:
        n = rel.replace("\\", "/").lstrip("/")
        if n and n not in seen and n != active:
            seen.add(n)
            targets.append(n)

    for m in _PY_FROM_IMPORT_RE.finditer(source):
        mod = (m.group(1) or "").strip()
        if not mod or mod.startswith(("fastapi", "pydantic", "typing", "os", "sys", "re")):
            continue
        parts = mod.split(".")
        if scope and parts[0] in ("app", "src", "tests") and scope:
            base = f"{scope}/{parts[0]}"
            if len(parts) > 1:
                _add(f"{base}/{'/'.join(parts[1:])}.py")
            else:
                _add(f"{base}/__init__.py")
            continue
        if active_dir and not mod.startswith("."):
            _add(f"{active_dir}/{mod.replace('.', '/')}.py")
    return targets[: _import_chain_max_files()]


def build_import_chain_block(
    workspace_root: str | Path | None,
    *,
    active_file: str | None,
    scope_rel: str | None = None,
) -> str:
    """Aktif dosyanın import ettiği yerel modülleri oku (Adım 5)."""
    if not import_chain_enabled() or not active_file:
        return ""
    try:
        from ilim_assistant.motorlar.programlama_context_budget import (
            max_file_read_chars,
            parallel_read_cap,
        )
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        tools = ProgramlamaAraclari(workspace_root)
        if tools.root is None:
            return ""
        cap = min(max_file_read_chars(), parallel_read_cap())
        head = tools.read(active_file, max_chars=cap)
        if not head.ok:
            return ""
        rels = _local_import_targets(active_file, head.content, scope_rel)
        if not rels:
            return ""
        blocks = [f"[İMPORT ZİNCİRİ — {FAZ21_VERSION}]"]
        for rel in rels:
            rep = tools.read(rel, max_chars=cap)
            if rep.ok:
                blocks.append(f"=== import: {rel} ===\n{rep.content[:cap]}")
        if len(blocks) <= 1:
            return ""
        return "\n\n".join(blocks)[: max_file_read_chars() * 2]
    except Exception:
        return ""


def faz21_directive() -> str:
    return (
        "[BAĞLAM — Faz 21]\n"
        "Programlama turunda ağır ilim RAG ve geniş orkestra kapalı; "
        "yalnızca proje özeti + araçlar.\n"
        f"Kapat: RUZGAR_PROG_LIGHT_CONTEXT=0\n"
    )
