# Created by Ümit & Gökçenur
"""
Programlama motoru — Adım 11: çekirdek paket registry.

94+ faz dosyası tek listede gruplanır; build_motor_context directive yağmurunu sadeleştirir.
"""

from __future__ import annotations

import importlib
import os
from typing import Any, Callable

CEKIRDEK_VERSION = "programlama-cekirdek-v1-2026-06-16"

# 9 çekirdek paket — bakım ve mental model
CORE_PACKAGES: dict[str, dict[str, Any]] = {
    "runtime": {
        "label": "Çalışma zamanı",
        "modules": [
            "programlama_motoru",
            "programlama_router",
            "programlama_context_budget",
            "programlama_faz21",
        ],
    },
    "agent": {
        "label": "Otonom ajan",
        "modules": [
            "programlama_faz14",
            "programlama_faz19",
            "programlama_faz85",
            "programlama_parallel_explore",
        ],
    },
    "verify": {
        "label": "Doğrulama",
        "modules": [
            "programlama_multilingual_verify",
            "programlama_faz15",
            "programlama_faz48",
        ],
    },
    "intel": {
        "label": "Proje zekâsı",
        "modules": [
            "programlama_faz13",
            "programlama_code_index",
            "programlama_faz22",
            "programlama_faz10",
        ],
    },
    "git": {
        "label": "Git ve kapanış",
        "modules": [
            "programlama_faz17",
            "programlama_faz31",
            "programlama_git_closure",
            "programlama_faz62",
            "programlama_faz58",
        ],
    },
    "delivery": {
        "label": "Teslimat ve CI",
        "modules": [
            "programlama_faz83",
            "programlama_ci_pr_loop",
            "programlama_delivery_gate",
            "programlama_faz82",
        ],
    },
    "learn": {
        "label": "Öğrenme ve KPI",
        "modules": [
            "programlama_root_cause_learn",
            "programlama_faz55",
            "programlama_faz102_e1_live",
        ],
    },
    "bench": {
        "label": "Bench ve otomasyon",
        "modules": [
            "programlama_faz99",
            "programlama_faz54",
            "programlama_faz60",
        ],
    },
    "safety": {
        "label": "Güvenlik ve onay",
        "modules": [
            "programlama_faz4",
            "programlama_faz78",
            "programlama_faz98",
        ],
    },
}

# (modül dosya adı, directive fonksiyon adı)
_FAZ_DIRECTIVE_REGISTRY: list[tuple[str, str]] = [
    ("programlama_faz14", "faz14_directive"),
    ("programlama_faz15", "faz15_directive"),
    ("programlama_faz16", "faz16_directive"),
    ("programlama_faz17", "faz17_directive"),
    ("programlama_faz18", "faz18_directive"),
    ("programlama_faz19", "faz19_directive"),
    ("programlama_faz20", "faz20_tool_directive"),
    ("programlama_faz22", "faz22_directive"),
    ("programlama_faz23", "faz23_directive"),
    ("programlama_faz24", "faz24_directive"),
    ("programlama_faz25", "faz25_directive"),
    ("programlama_faz26", "faz26_directive"),
    ("programlama_faz27", "faz27_directive"),
    ("programlama_faz28", "faz28_directive"),
    ("programlama_faz29", "faz29_directive"),
    ("programlama_faz30", "faz30_directive"),
    ("programlama_faz31", "faz31_directive"),
    ("programlama_ci_pr_loop", "ci_pr_directive"),
    ("programlama_faz32", "faz32_directive"),
    ("programlama_faz33", "faz33_directive"),
    ("programlama_faz34", "faz34_directive"),
    ("programlama_faz35", "faz35_directive"),
    ("programlama_faz36", "faz36_directive"),
    ("programlama_faz37", "faz37_directive"),
    ("programlama_faz38", "faz38_directive"),
    ("programlama_faz39", "faz39_directive"),
    ("programlama_faz40", "faz40_directive"),
    ("programlama_faz41", "faz41_directive"),
    ("programlama_faz42", "faz42_directive"),
    ("programlama_faz43", "faz43_directive"),
    ("programlama_faz44", "faz44_directive"),
    ("programlama_faz45", "faz45_directive"),
    ("programlama_faz46", "faz46_directive"),
    ("programlama_faz47", "faz47_directive"),
    ("programlama_faz48", "faz48_directive"),
    ("programlama_faz50", "faz50_directive"),
    ("programlama_faz51", "faz51_directive"),
    ("programlama_faz52", "faz52_directive"),
    ("programlama_faz53", "faz53_directive"),
    ("programlama_faz54", "faz54_directive"),
    ("programlama_faz55", "faz55_directive"),
    ("programlama_faz56", "faz56_directive"),
    ("programlama_faz57", "faz57_directive"),
    ("programlama_faz58", "faz58_directive"),
    ("programlama_faz60", "faz60_directive"),
    ("programlama_faz61", "faz61_directive"),
    ("programlama_faz62", "faz62_directive"),
    ("programlama_faz63", "faz63_directive"),
    ("programlama_faz64", "faz64_directive"),
    ("programlama_faz65", "faz65_directive"),
    ("programlama_faz66", "faz66_directive"),
    ("programlama_faz67", "faz67_directive"),
    ("programlama_faz68", "faz68_directive"),
    ("programlama_faz69", "faz69_directive"),
    ("programlama_faz70", "faz70_directive"),
    ("programlama_faz81", "faz81_directive"),
    ("programlama_faz84", "faz84_directive"),
    ("programlama_faz98", "faz98_directive"),
]

_UPGRADE_DIRECTIVES: list[tuple[str, str]] = [
    ("programlama_multilingual_verify", "multilingual_directive"),
    ("programlama_root_cause_learn", "root_cause_learn_directive"),
]


def cekirdek_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_CEKIRDEK_REGISTRY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _import_fn(module_name: str, fn_name: str) -> Callable[..., str] | None:
    try:
        mod = importlib.import_module(f"ilim_assistant.motorlar.{module_name}")
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            return fn
    except Exception:
        return None
    return None


def _call_directive(fn: Callable[..., str], prompt: str) -> str:
    try:
        import inspect

        sig = inspect.signature(fn)
        if len(sig.parameters) >= 1:
            return str(fn(prompt) or "")
        return str(fn() or "")
    except TypeError:
        return str(fn() or "")
    except Exception:
        return ""


def append_registry_directives(
    base: str,
    *,
    prompt: str = "",
    workspace_root: Any = None,
    active_file: str | None = None,
) -> str:
    """Faz directive listesini tek döngüde ekler (+ özel kancalar)."""
    if not cekirdek_enabled():
        return base
    out = base
    for mod_name, fn_name in _FAZ_DIRECTIVE_REGISTRY + _UPGRADE_DIRECTIVES:
        fn = _import_fn(mod_name, fn_name)
        if fn is None:
            continue
        piece = _call_directive(fn, prompt)
        if piece.strip():
            out += piece.rstrip() + "\n"

    try:
        from ilim_assistant.motorlar.programlama_faz78 import (
            core_scope_directive,
            faz78_directive,
        )

        out += faz78_directive().rstrip() + "\n"
        cs = core_scope_directive(prompt)
        if cs:
            out += cs.rstrip() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz79 import (
            faz79_directive,
            format_handoff_context_block,
        )

        out += faz79_directive().rstrip() + "\n"
        h79 = format_handoff_context_block(
            prompt, workspace_root, active_file=active_file
        )
        if h79:
            out += f"\n[HANDOFF v3]\n{h79}\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz80 import (
            faz80_directive,
            mega_refactor_directive,
        )

        out += faz80_directive().rstrip() + "\n"
        mr = mega_refactor_directive(prompt)
        if mr:
            out += mr.rstrip() + "\n"
    except Exception:
        pass
    return out


def package_manifest() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for pid, meta in CORE_PACKAGES.items():
        mods = list(meta.get("modules") or [])
        ok_n = 0
        for m in mods:
            try:
                importlib.import_module(f"ilim_assistant.motorlar.{m}")
                ok_n += 1
            except Exception:
                pass
        rows.append(
            {
                "id": pid,
                "label": meta.get("label"),
                "modules": len(mods),
                "import_ok": ok_n,
            }
        )
    return {
        "version": CEKIRDEK_VERSION,
        "package_count": len(rows),
        "packages": rows,
        "directive_registry": len(_FAZ_DIRECTIVE_REGISTRY) + len(_UPGRADE_DIRECTIVES),
    }


def run_cekirdek_smoke() -> dict[str, Any]:
    manifest = package_manifest()
    directive_ok = 0
    for mod_name, fn_name in _FAZ_DIRECTIVE_REGISTRY[:12]:
        if _import_fn(mod_name, fn_name) is not None:
            directive_ok += 1
    all_imports = all(
        p.get("import_ok", 0) == p.get("modules", 0) for p in manifest.get("packages") or []
    )
    ok = (
        manifest.get("package_count") == 9
        and all_imports
        and directive_ok >= 10
    )
    return {
        "ok": ok,
        "manifest": manifest,
        "directive_sample_ok": directive_ok,
        "version": CEKIRDEK_VERSION,
    }
