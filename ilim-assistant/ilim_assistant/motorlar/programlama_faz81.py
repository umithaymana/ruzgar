# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 81: Deterministik araç kurtarma (E3, Groq'suz).

LLM metnindeki @@read / @@write bloklarını API olmadan uygular.
"""

from __future__ import annotations

import os
import re
from typing import Any

FAZ81_VERSION = "programlama-faz81-v1-2026-05-26"

_WRITE_BLOCK_RE = re.compile(
    r"@@write\s+(\S+)\s*\r?\n```(?:[\w+-]+)?\s*\r?\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)
_READ_RE = re.compile(r"@@read\s+(\S+)", re.I)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ81", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz81_enabled() -> bool:
    return _enabled()


def extract_deterministic_ops(text: str) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for m in _WRITE_BLOCK_RE.finditer(text or ""):
        ops.append({"op": "write", "path": m.group(1), "content": m.group(2)})
    for m in _READ_RE.finditer(text or ""):
        ops.append({"op": "read", "path": m.group(1)})
    return ops


def rescue_text_only_turn(
    llm_body: str,
    workspace_root: str | None,
    *,
    message: str = "",
    scope_rel: str | None = None,
) -> tuple[str, list[dict[str, Any]], str]:
    """
    Metin-only turda @@ bloklarını çalıştır.
    Dönüş: (güncellenmiş metin, tool_results, blok özeti)
    """
    if not _enabled():
        return llm_body, [], ""
    ops = extract_deterministic_ops(llm_body)
    if not ops:
        return llm_body, [], ""

    try:
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        tools = ProgramlamaAraclari(workspace_root)
    except Exception:
        return llm_body, [], ""

    results: list[dict[str, Any]] = []
    lines: list[str] = ["[Faz 81 — deterministik kurtarma]"]

    for op in ops[:12]:
        path = str(op.get("path") or "").strip()
        if not path:
            continue
        try:
            from ilim_assistant.motorlar.programlama_faz78 import augment_write_policy

            root = tools.root
            if root and op["op"] == "write":
                ok, reason = augment_write_policy(root, path, message)
                if not ok:
                    lines.append(f"· write `{path}` — RED: {reason}")
                    results.append({"tool": "write", "ok": False, "path": path})
                    continue
        except Exception:
            pass

        if op["op"] == "read":
            rep = tools.read(path, max_chars=12000)
            results.append(
                {
                    "tool": "read",
                    "ok": rep.ok,
                    "path": path,
                    "output": (rep.content or rep.error or "")[:4000],
                }
            )
            lines.append(f"· read `{path}` — {'OK' if rep.ok else 'HATA'}")
        elif op["op"] == "write":
            rep = tools.write(path, str(op.get("content") or ""))
            results.append(
                {
                    "tool": "write",
                    "ok": rep.ok,
                    "path": path,
                    "output": rep.detail,
                }
            )
            lines.append(f"· write `{path}` — {'OK' if rep.ok else rep.detail}")

    block = "\n".join(lines)
    if len(results) == 0:
        return llm_body, [], ""
    combined = (llm_body or "").rstrip() + "\n\n" + block
    return combined, results, block


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz81"] = faz81_enabled()
    return out


def faz81_directive() -> str:
    return (
        "[FAZ 81 — DETERMİNİSTİK KURTARMA]\n"
        "Metin-only turda @@read/@@write blokları API olmadan uygulanır.\n"
    )
