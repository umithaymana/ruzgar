# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 101: Bench/KPI JSON raporlarını okuma (kod görevi değil).

Kullanıcı `scripts/ruzgar_programlama_upgrade_report.json` gibi bir yol yazdığında
otomatik pytest/smoke görevi açılmaz; rapor Türkçe özetlenir.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ101_VERSION = "programlama-faz101-v1-2026-05-29"

_KNOWN_BASENAMES = frozenset(
    {
        "ruzgar_programlama_upgrade_report.json",
        "ruzgar_autonomy_benchmark_sonuc.json",
        "ruzgar_parity_smoke_sonuc.json",
        "ruzgar_cursor_seviye_sonuc.json",
    }
)

_READ_HINTS = (
    "upgrade rapor",
    "bench rapor",
    "raporu oku",
    "raporu özet",
    "raporu ozet",
    "raporu göster",
    "raporu goster",
    "raporu açıkla",
    "raporu acikla",
    "upgrade_report",
    "programlama_upgrade",
    "upgrade runner",
    "bench sonuc",
    "parity smoke",
    "cursor seviye",
    "autonomy benchmark",
    "weekly kpi",
    "task-stats",
    "görev istatistik",
    "gorev istatistik",
)

_CLARIFY_HINTS = (
    "anlamadım",
    "anlamadim",
    "ne demek",
    "ne demek istedi",
    "açıkla",
    "acikla",
    "anlamıyorum",
    "anlamiyorum",
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ101", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def normalize_report_path_guess(raw: str) -> str:
    s = (raw or "").strip().strip("\"'")
    s = s.replace("\\", "/")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"ruzgar\s+programlama", "ruzgar_programlama", s, flags=re.I)
    s = re.sub(r"upgrade\s+report", "upgrade_report", s, flags=re.I)
    s = re.sub(r"programlama\s+upgrade", "programlama_upgrade", s, flags=re.I)
    return s


def extract_json_path_refs(message: str) -> list[str]:
    msg = normalize_report_path_guess(message)
    found: list[str] = []
    for m in re.finditer(
        r"(?:[\w./\\-]+/)*[\w./\\-]+\.json",
        msg,
        flags=re.I,
    ):
        p = normalize_report_path_guess(m.group(0))
        if p and p not in found:
            found.append(p)
    return found


def wants_report_read(message: str) -> bool:
    if not _enabled():
        return False
    raw = (message or "").strip()
    if not raw:
        return False
    low = raw.lower()
    if any(h in low for h in _READ_HINTS):
        return True
    refs = extract_json_path_refs(raw)
    if refs:
        for p in refs:
            base = Path(p.replace("\\", "/")).name.lower()
            if base in _KNOWN_BASENAMES or "report" in base or "sonuc" in base:
                return True
        if len(raw) < 180 and not _looks_like_code_task(low):
            return True
    return False


def wants_clarification(message: str) -> bool:
    if not _enabled():
        return False
    raw = (message or "").strip()
    if not raw or len(raw) > 140:
        return False
    low = raw.lower()
    if not any(h in low for h in _CLARIFY_HINTS):
        return False
    return not _looks_like_code_task(low)


def _looks_like_code_task(low: str) -> bool:
    return any(
        k in low
        for k in (
            "yaz",
            "ekle",
            "sil",
            "fix",
            "düzelt",
            "duzelt",
            "refactor",
            "pytest yaz",
            "test yaz",
            "@@write",
            "patch ",
            "commit",
        )
    )


def resolve_report_path(
    workspace_root: str | Path | None,
    message: str,
) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    candidates: list[str] = []
    for ref in extract_json_path_refs(message):
        candidates.append(ref)
    low = (message or "").lower()
    if "upgrade" in low or "bench" in low or "programlama_upgrade" in low:
        candidates.append("scripts/ruzgar_programlama_upgrade_report.json")
    if "parity" in low:
        candidates.append("scripts/ruzgar_parity_smoke_sonuc.json")
    if "autonomy" in low or "faz99" in low:
        candidates.append("scripts/ruzgar_autonomy_benchmark_sonuc.json")
    if "cursor" in low and "seviye" in low:
        candidates.append("scripts/ruzgar_cursor_seviye_sonuc.json")

    seen: set[str] = set()
    for rel in candidates:
        rel = normalize_report_path_guess(rel).lstrip("/")
        if not rel or rel in seen:
            continue
        seen.add(rel)
        p = (root / rel).resolve()
        try:
            p.relative_to(root.resolve())
        except ValueError:
            continue
        if p.is_file():
            return p
        alt = rel.replace(" ", "_")
        if alt != rel:
            p2 = (root / alt).resolve()
            if p2.is_file():
                return p2
    return None


def format_upgrade_report_summary(data: dict[str, Any], *, rel: str) -> str:
    ok = bool(data.get("ok"))
    scores = data.get("scores") or {}
    checks = data.get("checks") or {}
    cmd = data.get("command_eval") or {}
    ladder = data.get("ladder") or []
    lines = [
        f"Ümit abi, **bench raporu** (`{rel}`):",
        "",
        f"· Genel: **{'OK' if ok else 'KIRMIZI'}** · süre {data.get('elapsed_sec', '?')} sn",
        "",
        "**Skorlar**",
    ]
    for key, label in (
        ("command_level", "Komut anlama"),
        ("autonomy_level", "Bağımsız proje"),
        ("approval_safety", "Onay güvenliği"),
        ("natural_language", "Doğal dil"),
        ("reliability", "Güvenilirlik"),
    ):
        if key in scores:
            lines.append(f"  · {label}: **{scores[key]}**/100")
    if checks:
        c2 = checks.get("consistency_two_runs")
        f1 = checks.get("faz99_run1_ok")
        f2 = checks.get("faz99_run2_ok")
        lines.extend(
            [
                "",
                "**Kontroller**",
                f"  · İki koşu tutarlılığı: {'✓' if c2 else '✗'}",
                f"  · Faz 99 koşu 1: {'✓' if f1 else '✗'}",
                f"  · Faz 99 koşu 2: {'✓' if f2 else '✗'}",
            ]
        )
    if cmd:
        passed = int(cmd.get("passed") or 0)
        total = int(cmd.get("total") or 0)
        lines.append(f"\n**Komut altın set:** {passed}/{total}")
        failed = cmd.get("failed_examples") or []
        if failed:
            lines.append(f"  · Başarısız örnek: {len(failed)}")
    if ladder:
        lines.append("\n**Görev merdiveni**")
        for row in ladder[:6]:
            if not isinstance(row, dict):
                continue
            mark = "✓" if row.get("pass") else "✗"
            lines.append(
                f"  {mark} `{row.get('id', '?')}` — {row.get('score', '?')}/{row.get('min_score', '?')}"
            )
    art = data.get("artifacts") or {}
    if art.get("faz99_scope_1"):
        lines.append(
            f"\nFaz 99 kapsamları: `{art.get('faz99_scope_1')}`, `{art.get('faz99_scope_2', '')}`"
        )
    lines.append(
        "\nBu dosya **kod görevi değil** — bench kanıtıdır. "
        "Yeniden ölçmek için: `scripts\\Ruzgar_Programlama_Bench.bat`"
    )
    lines.append(f"\n({FAZ101_VERSION})")
    return "\n".join(lines)


def format_generic_json_report_summary(
    data: Any,
    *,
    rel: str,
) -> str:
    if isinstance(data, dict):
        if "scores" in data and "command_eval" in data:
            return format_upgrade_report_summary(data, rel=rel)
        ok = data.get("ok")
        lines = [
            f"Ümit abi, rapor özeti (`{rel}`):",
            "",
        ]
        if ok is not None:
            lines.append(f"· ok: **{ok}**")
        for k in ("version", "elapsed_sec", "report", "message", "error"):
            if k in data and data[k] not in (None, ""):
                lines.append(f"· {k}: {data[k]}")
        if len(lines) <= 3:
            preview = json.dumps(data, ensure_ascii=False, indent=2)[:2400]
            lines.extend(["", "```json", preview, "```"])
    else:
        preview = json.dumps(data, ensure_ascii=False, indent=2)[:2400]
        lines = [
            f"Ümit abi, rapor (`{rel}`):",
            "",
            "```json",
            preview,
            "```",
        ]
    lines.append(f"\n({FAZ101_VERSION})")
    return "\n".join(lines)


def read_report_summary(
    workspace_root: str | Path | None,
    message: str,
) -> str:
    path = resolve_report_path(workspace_root, message)
    if path is None:
        return (
            "Ümit abi, rapor dosyasını bulamadım. "
            "Önce bench çalıştır: `scripts\\Ruzgar_Programlama_Bench.bat` — "
            "sonra `scripts/ruzgar_programlama_upgrade_report.json` yaz veya "
            "`upgrade raporunu özetle` de.\n\n"
            f"({FAZ101_VERSION})"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"Rapor okunamadı ({path.name}): {exc}\n\n({FAZ101_VERSION})"
    rel = str(path.name)
    try:
        root = repo_root(workspace_root)
        if root is not None:
            rel = str(path.relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        pass
    return format_generic_json_report_summary(data, rel=rel)


def clarification_hint() -> str:
    return (
        "Ümit abi, önceki satır büyük ihtimalle **projects/** altında otomatik "
        "**pytest doğrulaması**ydı (smoke-parity-crud gibi) — bench raporu değil.\n\n"
        "**Bench raporu** için şunlardan birini yaz:\n"
        "· `upgrade raporunu özetle`\n"
        "· `scripts/ruzgar_programlama_upgrade_report.json`\n\n"
        "Bench yenilemek: `scripts\\Ruzgar_Programlama_Bench.bat`\n\n"
        f"({FAZ101_VERSION})"
    )


def maybe_instant_report_read(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    if not _enabled():
        return None
    if wants_clarification(message):
        return clarification_hint()
    if not wants_report_read(message):
        return None
    return read_report_summary(workspace_root, message)
