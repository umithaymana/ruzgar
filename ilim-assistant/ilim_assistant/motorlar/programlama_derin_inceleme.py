# Created by Ümit & Gökçenur
"""Derin inceleme — paket, raf, dil aracı, son tarama. Yazma yok."""

from __future__ import annotations

import shutil
from pathlib import Path

DERIN_VERSION = "programlama-derin-inceleme-v1-2026-10-16"

_TOOL_CMDS: tuple[tuple[str, str], ...] = (
    ("python", "Python"),
    ("node", "Node"),
    ("go", "Go"),
    ("rustc", "Rust"),
)


def format_dil_araclari() -> str:
    lines = []
    for index, (cmd, label) in enumerate(_TOOL_CMDS, start=1):
        found = shutil.which(cmd)
        if found:
            lines.append(f"{index}. {label} — var — {found}")
        else:
            lines.append(f"{index}. {label} — yok")
    return "\n".join(lines)


def format_derin_inceleme(
    workspace_root: str | Path | None = None,
    *,
    scan_text: str | None = None,
) -> str:
    from ilim_assistant.motorlar.programlama_cekirdek_paketleri import CORE_PACKAGES
    from ilim_assistant.ruzgar_bilgisayar_kutuphane import format_raf_basliklari

    if scan_text is None:
        from ilim_assistant.motorlar.programlama_faz2 import format_self_scan_report

        scan_text = format_self_scan_report(workspace_root)

    lines = [
        "Ümit abi, derin inceleme. Bu turda dosya yazılmadı.",
        "Düzeltme ancak «onayla 1» veya «hepsini onayla düzelt» deyince başlar.",
        "",
        "1. Çekirdek paketler",
    ]
    for index, (key, spec) in enumerate(CORE_PACKAGES.items(), start=1):
        label = str(spec.get("label") or key)
        modules = ", ".join(str(m) for m in (spec.get("modules") or []))
        lines.append(f"   {index}. {label}")
        if modules:
            lines.append(f"      {modules}")
    lines.extend(
        [
            "",
            "2. Bilgi rafları",
            format_raf_basliklari(),
            "",
            "3. Dil araçları",
            format_dil_araclari(),
            "",
            "4. Son tarama",
            (scan_text or "Tarama boş.").strip(),
            "",
            f"({DERIN_VERSION})",
        ]
    )
    return "\n".join(lines)
