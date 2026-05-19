from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_LAST_REPORT: dict[str, Any] | None = None


def _interesting_lines(output: str, limit: int = 18) -> list[str]:
    lines = (output or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    keep: list[str] = []
    rx = re.compile(
        r"(FAILED|ERROR|Traceback|AssertionError|ImportError|ModuleNotFoundError|"
        r"SyntaxError|TypeError|ValueError|File \".+\", line \d+|E\s+)",
        re.I,
    )
    for line in lines:
        s = line.rstrip()
        if rx.search(s):
            keep.append(s[:260])
        if len(keep) >= limit:
            break
    if not keep:
        keep = [x[:260] for x in lines[-limit:] if x.strip()]
    return keep[:limit]


def build_debug_report(
    *,
    message: str,
    workspace_root: str | None,
    pytest_report: Any,
    writes_count: int = 0,
    retries_left: int = 0,
) -> dict[str, Any]:
    output = str(getattr(pytest_report, "output", "") or "")
    exit_code = int(getattr(pytest_report, "exit_code", -1) or -1)
    preset = str(getattr(pytest_report, "preset", "pytest_run") or "pytest_run")
    lines = _interesting_lines(output)
    likely = "Test çıktısındaki hata satırlarını incele."
    blob = "\n".join(lines).casefold()
    if "modulenotfounderror" in blob or "importerror" in blob:
        likely = "Eksik import, yanlış paket yolu veya çalışma dizini problemi görünüyor."
    elif "syntaxerror" in blob:
        likely = "Sözdizimi hatası var; önce işaretlenen dosya/satır düzeltilmeli."
    elif "assertionerror" in blob or "failed" in blob:
        likely = "Davranış testi beklenen sonucu alamıyor; ilgili assertion ve iş mantığı karşılaştırılmalı."
    elif "traceback" in blob:
        likely = "Runtime traceback var; en alttaki exception ve dosya/satır esas alınmalı."

    report = {
        "ok": False,
        "preset": preset,
        "exit_code": exit_code,
        "workspace_root": workspace_root or "",
        "writes_count": writes_count,
        "retries_left": retries_left,
        "likely_cause": likely,
        "highlights": lines,
        "user_message": (message or "")[:500],
    }
    return report


def format_debug_report(report: dict[str, Any]) -> str:
    lines = [
        "[RÜZGAR OTONOM DEBUG v2 RAPORU]",
        f"Preset: {report.get('preset')} | exit={report.get('exit_code')}",
        f"Workspace: {report.get('workspace_root') or '(yok)'}",
        f"Yazım sayısı: {report.get('writes_count', 0)} | Kalan deneme: {report.get('retries_left', 0)}",
        f"İlk teşhis: {report.get('likely_cause')}",
        "Öne çıkan log satırları:",
    ]
    for item in report.get("highlights") or []:
        lines.append(f"- {item}")
    lines.append("[/RÜZGAR OTONOM DEBUG v2 RAPORU]")
    return "\n".join(lines)


def publish_debug_report(report: dict[str, Any]) -> None:
    """Terminale/log'a basar ve son raporu hafif bir dosyaya yazar."""
    global _LAST_REPORT
    _LAST_REPORT = dict(report)
    text = format_debug_report(report)
    print(text, flush=True)
    try:
        out = Path(__file__).resolve().parents[1] / "hafiza" / "son_debug_raporu.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    except OSError:
        pass


def last_debug_report() -> dict[str, Any] | None:
    return dict(_LAST_REPORT) if _LAST_REPORT else None
