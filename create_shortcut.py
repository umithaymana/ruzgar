# -*- coding: utf-8 -*-
"""
RUZGAR masaüstü kısayolu: gerçek Python yorumlayıcısı + ilim-assistant/ruzgar_launch.py
Başlama yeri (Start in): ilim-assistant. Kısayol 'Yönetici olarak çalıştır' bayrağı ile yazılır.
Ümit & Gökçenur
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

# Proje kökü
PROJECT_ROOT = Path(__file__).resolve().parent
ILIM_ASSISTANT = PROJECT_ROOT / "ilim-assistant"
ICON = PROJECT_ROOT / "ruzgar-desktop" / "assets" / "ruzgar.ico"
# Projede main.py / app.py yok; giriş: ruzgar_launch.py (API + Electron)
ENTRY = ILIM_ASSISTANT / "ruzgar_launch.py"


def resolve_python_exe() -> Path:
    """Bu betiği hangi Python çalıştırıyorsa kısayol da aynı yorumlayıcıyı kullanır."""
    return Path(sys.executable).resolve()


def desktop_candidates() -> list[Path]:
    home = Path.home()
    cand: list[Path] = []
    for rel in (
        Path("Desktop"),
        Path("OneDrive") / "Desktop",
        Path("OneDrive - Personal") / "Desktop",
    ):
        d = home / rel
        if d.is_dir():
            cand.append(d.resolve())
    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-Command",
                "(New-Object -ComObject WScript.Shell).SpecialFolders.Item('Desktop')",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        txt = proc.stdout.strip()
        if txt:
            p = Path(txt).resolve()
            if p.is_dir():
                cand.append(p)
    except (OSError, subprocess.TimeoutExpired):
        pass
    uniq: dict[str, Path] = {}
    for p in cand:
        uniq[str(p).lower()] = p
    return list(uniq.values())


def ps_single_quoted_literal(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def remove_old_shortcuts(desktops: list[Path]) -> None:
    for d in desktops:
        for name in ("RUZGAR.lnk", "RUZGAR_yedek.lnk"):
            dead = d / name
            try:
                if dead.is_file():
                    dead.unlink()
            except OSError:
                pass


def admin_shortcut_ps1_text(*, exe: Path, arguments: str, start_in: Path, icon_path: Path, outputs: list[Path]) -> str:
    exe_s = ps_single_quoted_literal(str(exe.resolve()))
    arg_s = ps_single_quoted_literal(arguments)
    cwd_s = ps_single_quoted_literal(str(start_in.resolve()))
    if icon_path.is_file():
        ico_s = ps_single_quoted_literal(str(icon_path.resolve()))
        ico_assign = f"$IconLoc = {ico_s}"
    else:
        ico_assign = "$IconLoc = $null"
    outs_lit = ",".join(ps_single_quoted_literal(str(o.resolve())) for o in outputs)
    return rf"""
$ErrorActionPreference = 'Stop'
$TargetExe = {exe_s}
$ArgLine = {arg_s}
$StartIn = {cwd_s}
{ico_assign}
$Outputs = @({outs_lit})

function Set-RuzgarAdminShortcut {{
    param([string]$OutPath)
    $w = New-Object -ComObject WScript.Shell
    $sc = $w.CreateShortcut($OutPath)
    $sc.TargetPath = $TargetExe
    $sc.Arguments = $ArgLine
    $sc.WorkingDirectory = $StartIn
    if ($IconLoc) {{ $sc.IconLocation = $IconLoc }}
    $sc.Description = 'RUZGAR (Python launcher) — Umit & Goekcenur'
    $sc.Save()
    $bytes = [System.IO.File]::ReadAllBytes($OutPath)
    $bytes[0x15] = $bytes[0x15] -bor [byte]0x20
    [System.IO.File]::WriteAllBytes($OutPath, $bytes)
}}

foreach ($o in $Outputs) {{ Set-RuzgarAdminShortcut -OutPath $o }}
""".lstrip()


def main() -> int:
    py = resolve_python_exe()
    if not ILIM_ASSISTANT.is_dir():
        print("HATA: ilim-assistant klasoru yok:", ILIM_ASSISTANT, file=sys.stderr)
        return 1
    if not ENTRY.is_file():
        print("HATA: ruzgar_launch.py bulunamadi:", ENTRY, file=sys.stderr)
        return 1

    desktops = desktop_candidates()
    if not desktops:
        print("HATA: Masaustu klasoru bulunamadi.", file=sys.stderr)
        return 1

    remove_old_shortcuts(desktops)
    out_lnks = [d / "RUZGAR.lnk" for d in desktops]

    # Python.exe + betik (yol boşluk içerebilir)
    arg_line = f'-u "{ENTRY.resolve()}"'

    ps_body = admin_shortcut_ps1_text(
        exe=py,
        arguments=arg_line,
        start_in=ILIM_ASSISTANT.resolve(),
        icon_path=ICON,
        outputs=out_lnks,
    )
    tmp = Path(tempfile.gettempdir()) / "ruzgar_create_shortcut.ps1"
    tmp.write_text(ps_body, encoding="utf-8-sig")

    r = subprocess.run(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(tmp),
        ],
        check=False,
    )
    if r.returncode != 0:
        print("HATA: PowerShell kisayol olusturamadi. Exit:", r.returncode, file=sys.stderr)
        return 1

    print("Kisayol olusturuldu (Run as Administrator bayragi ile):")
    for p in out_lnks:
        print(" ", p)

    sys.stdout.flush()
    print(
        "\n".join(
            [
                "",
                "Ümit & Gökçenur — Mimara:",
                "",
                "Mimar, artık sadece tıklaman yeterli.",
                "",
            ]
        )
    )
    print("Baslama Yeri:", ILIM_ASSISTANT.resolve())
    print("Python:", py)
    print("Komut satırı:", py.name, arg_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
