"""Ön tanımlı, politika ile sınırlı komut çalıştırma (Windows odaklı)."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import List, Tuple

from ilim_assistant.safety_policy import validate_custom_winget_line


@dataclass
class Preset:
    key: str
    label: str
    description: str
    argv: List[str]
    shell: bool = False
    timeout_sec: int = 600


def _defender_path() -> str:
    p = os.path.expandvars(r"%ProgramFiles%\Windows Defender\MpCmdRun.exe")
    return p if os.path.isfile(p) else ""


def build_presets() -> List[Preset]:
    out: List[Preset] = []

    out.append(
        Preset(
            key="python_install_winget",
            label="Python 3.12 kur (winget)",
            description="winget ile Python.Python.3.12 kurulumu (yönetici isteyebilir).",
            argv=[
                "winget",
                "install",
                "Python.Python.3.12",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            timeout_sec=1200,
        )
    )

    out.append(
        Preset(
            key="python_version",
            label="python --version",
            description="PATH’te python var mı kontrol et.",
            argv=["cmd", "/c", "python --version"],
            shell=False,
            timeout_sec=30,
        )
    )

    out.append(
        Preset(
            key="where_python",
            label="where python",
            description="python.exe hangi yolda.",
            argv=["cmd", "/c", "where python"],
            timeout_sec=30,
        )
    )

    dp = _defender_path()
    if dp:
        out.append(
            Preset(
                key="defender_quick_scan",
                label="Windows Defender — hızlı tarama",
                description="MpCmdRun ile hızlı tarama (Quick). Sonuç Defender günlüğünde; otomatik silme YOK.",
                argv=[dp, "-Scan", "-ScanType", "1"],
                timeout_sec=3600,
            )
        )
        out.append(
            Preset(
                key="defender_full_scan",
                label="Windows Defender — tam tarama",
                description="Uzun sürebilir; otomatik silme YOK.",
                argv=[dp, "-Scan", "-ScanType", "2"],
                timeout_sec=86400,
            )
        )

    out.append(
        Preset(
            key="mp_threat_list",
            label="Defender — algılanan tehdit özeti (PowerShell)",
            description="Get-MpThreat — salt okunur liste (silmez).",
            argv=[
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-MpThreat | Select-Object ThreatName, Resources | Format-Table -AutoSize",
            ],
            timeout_sec=120,
        )
    )

    return out


_ALL_PRESETS = build_presets()
PRESETS = {p.key: p for p in _ALL_PRESETS}


def run_argv(argv: List[str], timeout_sec: int = 600, shell: bool = False) -> Tuple[int, str, str]:
    """Çıkış kodu, stdout, stderr."""
    try:
        r = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            shell=shell,
        )
        out = (r.stdout or "") + ("\n" + r.stderr if r.stderr else "")
        return r.returncode, out.strip(), ""
    except subprocess.TimeoutExpired:
        return -1, "", "Zaman aşımı."
    except Exception as e:
        return -1, "", str(e)


def run_preset(key: str) -> Tuple[int, str]:
    p = PRESETS.get(key)
    if not p:
        return -1, "Bilinmeyen işlem."
    code, out, err = run_argv(p.argv, timeout_sec=p.timeout_sec, shell=p.shell)
    tail = f"[Çıkış kodu: {code}]\n{out}"
    if err:
        tail += f"\n[Hata] {err}"
    return code, tail


def run_custom_winget(line: str) -> Tuple[int, str]:
    ok, msg = validate_custom_winget_line(line)
    if not ok:
        return -1, msg
    parts = line.strip().split()
    code, out, err = run_argv(parts, timeout_sec=1200)
    tail = f"[Çıkış kodu: {code}]\n{out}"
    if err:
        tail += f"\n[Hata] {err}"
    return code, tail


def preset_labels() -> List[Tuple[str, str]]:
    """Gradio Dropdown (görünen metin, dahili değer) için."""
    return [(f"{p.label} — {p.description}", p.key) for p in _ALL_PRESETS]
