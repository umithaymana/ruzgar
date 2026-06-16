"""Ön tanımlı, politika ile sınırlı komut çalıştırma (Windows odaklı)."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from typing import List, Tuple

from ilim_assistant.safety_policy import validate_custom_winget_line

_MODULE_NAME_RE = re.compile(r"^[a-zA-Z_][\w.]*$")


@dataclass
class Preset:
    key: str
    label: str
    description: str
    argv: List[str]
    shell: bool = False
    timeout_sec: int = 600
    use_project_cwd: bool = False


def _defender_path() -> str:
    p = os.path.expandvars(r"%ProgramFiles%\Windows Defender\MpCmdRun.exe")
    return p if os.path.isfile(p) else ""


def _exec_cwd() -> str | None:
    """Geliştirme preset'leri için çalışma dizini (proje kökü)."""
    raw = (
        os.environ.get("RUZGAR_EXEC_CWD", "").strip()
        or os.environ.get("LOCAL_TOOLS_ROOT", "").strip()
    )
    if raw and os.path.isdir(raw):
        return os.path.abspath(raw)
    try:
        from ilim_assistant.ruzgar_hafiza_koprusu import ilim_assistant_root

        parent = ilim_assistant_root().parent
        if parent.is_dir():
            return str(parent.resolve())
    except Exception:
        pass
    return None


def _python_module_argv() -> List[str]:
    """``python -m <modül>`` — modül adı env ile (güvenli karakter kümesi)."""
    mod = os.environ.get("RUZGAR_PYTHON_MODULE", "pytest").strip() or "pytest"
    if not _MODULE_NAME_RE.match(mod):
        mod = "pytest"
    extra = os.environ.get("RUZGAR_PYTHON_MODULE_ARGS", "").strip()
    argv = ["python", "-m", mod]
    if extra:
        for part in extra.split():
            if part and re.match(r"^[\w./\\\-=:]+$", part):
                argv.append(part)
    return argv


def _pytest_argv() -> List[str]:
    target = os.environ.get("RUZGAR_PYTEST_TARGET", "").strip()
    argv = ["python", "-m", "pytest"]
    if target and re.match(r"^[\w./\\\-]+$", target):
        argv.append(target)
    return argv


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

    out.append(
        Preset(
            key="pytest_run",
            label="pytest — proje testleri",
            description=(
                "python -m pytest; traceback hata ayıklama döngüsü için. "
                "Kök: RUZGAR_EXEC_CWD veya LOCAL_TOOLS_ROOT. "
                "Hedef: RUZGAR_PYTEST_TARGET (örn. ilim-assistant)."
            ),
            argv=_pytest_argv(),
            timeout_sec=900,
            use_project_cwd=True,
        )
    )

    out.append(
        Preset(
            key="python_module_run",
            label="python -m (smoke)",
            description=(
                "python -m <modül> smoke test. Modül: RUZGAR_PYTHON_MODULE (varsayılan pytest). "
                "Ek argüman: RUZGAR_PYTHON_MODULE_ARGS."
            ),
            argv=["python", "-m", "pytest"],
            timeout_sec=600,
            use_project_cwd=True,
        )
    )

    out.append(
        Preset(
            key="ruff_check",
            label="ruff / flake8 — static analiz",
            description=(
                "Önce python -m ruff check .; ruff yoksa python -m flake8 . "
                "Çalışma kökü: proje kökü."
            ),
            argv=["python", "-m", "ruff", "check", "."],
            timeout_sec=300,
            use_project_cwd=True,
        )
    )

    out.append(
        Preset(
            key="mypy_check",
            label="mypy — tip kontrolü",
            description=(
                "python -m mypy --ignore-missing-imports <hedef>. "
                "Hedef: RUZGAR_MYPY_TARGET (varsayılan projects)."
            ),
            argv=["python", "-m", "mypy", "--ignore-missing-imports", "projects"],
            timeout_sec=300,
            use_project_cwd=True,
        )
    )

    return out


_ALL_PRESETS = build_presets()
PRESETS = {p.key: p for p in _ALL_PRESETS}


def run_argv(
    argv: List[str],
    timeout_sec: int = 600,
    shell: bool = False,
    cwd: str | None = None,
) -> Tuple[int, str, str]:
    """Çıkış kodu, stdout+stderr birleşik çıktı, ayrı hata metni."""
    if not argv:
        return -1, "", "Boş argv."
    try:
        kw: dict = {
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "timeout": timeout_sec,
            "shell": shell,
        }
        if cwd:
            kw["cwd"] = cwd
        r = subprocess.run(argv, **kw)
        out = (r.stdout or "") + ("\n" + r.stderr if r.stderr else "")
        return r.returncode, out.strip(), ""
    except subprocess.TimeoutExpired:
        return -1, "", "Zaman aşımı."
    except FileNotFoundError as e:
        return -1, "", str(e)
    except Exception as e:
        return -1, "", str(e)


def _lint_missing_tool(combined: str, tool: str) -> bool:
    low = combined.lower()
    return (
        "no module named" in low
        and tool in low
    ) or (
        "not found" in low
        and tool in low
    )


def _scoped_lint_target() -> str:
    raw = (os.environ.get("RUZGAR_RUFF_TARGET") or ".").strip().replace("\\", "/")
    if not raw or raw == ".":
        return "."
    if re.match(r"^[\w./\-]+$", raw):
        return raw.lstrip("/")
    return "."


def _scoped_mypy_target() -> str:
    raw = (os.environ.get("RUZGAR_MYPY_TARGET") or "projects").strip().replace("\\", "/")
    if raw and re.match(r"^[\w./\-]+$", raw):
        return raw.lstrip("/")
    return "projects"


def _run_ruff_or_flake8(cwd: str | None, timeout_sec: int) -> Tuple[int, str]:
    """ruff check <hedef> → yoksa flake8 ."""
    target = _scoped_lint_target()
    ruff_argv = ["python", "-m", "ruff", "check", target]
    code, out, err = run_argv(ruff_argv, timeout_sec=timeout_sec, cwd=cwd)
    combined = f"{out}\n{err}".strip()
    if code >= 0 and not _lint_missing_tool(combined, "ruff"):
        tail = f"[Araç: ruff]\n[Çıkış kodu: {code}]\n{out}"
        if err:
            tail += f"\n[Hata] {err}"
        return code, tail

    flake_argv = ["python", "-m", "flake8", "."]
    code2, out2, err2 = run_argv(flake_argv, timeout_sec=timeout_sec, cwd=cwd)
    combined2 = f"{out2}\n{err2}".strip()
    if _lint_missing_tool(combined2, "flake8"):
        msg = (
            "[Araç: ruff → flake8]\n"
            "Ne ruff ne flake8 bulunamadı. Kurulum: pip install ruff veya pip install flake8\n"
            f"[ruff çıktısı]\n{combined}\n"
            f"[flake8 çıktısı]\n{combined2}"
        )
        return -1, msg

    tail = f"[Araç: flake8 (ruff yok)]\n[Çıkış kodu: {code2}]\n{out2}"
    if err2:
        tail += f"\n[Hata] {err2}"
    return code2, tail


def _run_mypy_scoped(cwd: str | None, timeout_sec: int) -> Tuple[int, str]:
    """mypy --ignore-missing-imports <hedef>; kurulu değilse atla (exit 0)."""
    if not cwd:
        return -1, "Proje çalışma kökü yok."
    target = _scoped_mypy_target()
    abs_target = os.path.join(cwd, target.replace("/", os.sep))
    if not os.path.exists(abs_target):
        return 0, f"[Araç: mypy]\n`{target}` yok — atlandı."

    scope_cwd = cwd
    check_paths: list[str] = []
    norm = target.replace("\\", "/").strip("/")
    parts = norm.split("/")
    if len(parts) == 2 and parts[0] == "projects" and os.path.isdir(abs_target):
        scope_cwd = abs_target
        for sub in ("app", "src", "tests"):
            if os.path.isdir(os.path.join(scope_cwd, sub)):
                check_paths.append(sub)
        if not check_paths:
            check_paths = ["."]
    else:
        check_paths = [target]

    argv = ["python", "-m", "mypy", "--ignore-missing-imports"] + check_paths
    code, out, err = run_argv(argv, timeout_sec=timeout_sec, cwd=scope_cwd)
    combined = f"{out}\n{err}".strip()
    if _lint_missing_tool(combined, "mypy"):
        return 0, (
            "[Araç: mypy]\n"
            "Kurulu değil — atlandı (kurulum: pip install mypy).\n"
            f"{combined[:800]}"
        )
    tail = (
        f"[Araç: mypy]\n[Hedef: {target}]\n"
        f"[Cwd: {scope_cwd}]\n[Çıkış kodu: {code}]\n{out}"
    )
    if err:
        tail += f"\n[Hata] {err}"
    return code, tail


def _resolve_preset_argv(p: Preset) -> List[str]:
    if p.key == "python_module_run":
        return _python_module_argv()
    if p.key == "pytest_run":
        return _pytest_argv()
    return list(p.argv)


def run_preset(key: str) -> Tuple[int, str]:
    p = PRESETS.get(key)
    if not p:
        return -1, "Bilinmeyen işlem."

    cwd = _exec_cwd() if p.use_project_cwd else None
    if p.use_project_cwd and not cwd:
        return -1, (
            "Proje çalışma kökü bulunamadı. "
            "LOCAL_TOOLS_ROOT veya RUZGAR_EXEC_CWD ayarlayın."
        )

    if p.key == "ruff_check":
        return _run_ruff_or_flake8(cwd, p.timeout_sec)

    if p.key == "mypy_check":
        return _run_mypy_scoped(cwd, p.timeout_sec)

    argv = _resolve_preset_argv(p)
    code, out, err = run_argv(
        argv,
        timeout_sec=p.timeout_sec,
        shell=p.shell,
        cwd=cwd,
    )
    tail = f"[Komut: {' '.join(argv)}]\n[Çıkış kodu: {code}]\n{out}"
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
