"""
Rüzgar port işlemleri: port-check, kill-process.

Kullanım:
  python scripts/ruzgar_port_ops.py port-check [--port 8779]
  python scripts/ruzgar_port_ops.py kill-process [--port 8779]

Çıkış kodları (port-check):
  0 — port dinleniyor ve /api/health 200 + ok:true
  1 — port boş (dinleyen yok)
  2 — port dolu ama sağlıksız (zombi / kilit)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

try:
    from ilim_assistant.ruzgar_api_port import DEFAULT_API_PORT as DEFAULT_PORT
except ImportError:
    DEFAULT_PORT = 8779
_NETSTAT_RE_TEMPLATE = r"^\s*TCP\s+\S+:{port}\s+\S+\s+LISTENING\s+(\d+)\s*$"


def _pids_listening_on_port(port: int) -> list[int]:
    pattern = re.compile(_NETSTAT_RE_TEMPLATE.format(port=port), re.IGNORECASE)
    try:
        cp = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=8,
            shell=False,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"netstat hata: {e}", file=sys.stderr)
        return []
    pids: set[int] = set()
    for line in (cp.stdout or "").splitlines():
        m = pattern.match(line)
        if m:
            try:
                pids.add(int(m.group(1)))
            except ValueError:
                continue
    return sorted(p for p in pids if p > 4)


def _health_ok(port: int, timeout: float = 2.5) -> bool:
    url = f"http://127.0.0.1:{port}/api/health"
    expected_rev = (os.environ.get("RUZGAR_EXPECTED_BUILD_REV") or "").strip()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if r.status != 200:
                return False
            raw = r.read().decode("utf-8", errors="replace")
            data = __import__("json").loads(raw)
            if not bool(data.get("ok")):
                return False
            if expected_rev:
                rev = str((data.get("build") or {}).get("rev") or "")
                if rev != expected_rev:
                    print(
                        f"port-check: build.rev uyumsuz '{rev}' != '{expected_rev}'",
                        file=sys.stderr,
                    )
                    return False
            return True
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def cmd_port_check(port: int) -> int:
    pids = _pids_listening_on_port(port)
    if not pids:
        print(f"port-check: {port} BOS")
        return 1
    healthy = _health_ok(port)
    pid_str = ",".join(str(p) for p in pids)
    if healthy:
        print(f"port-check: {port} DINLENIYOR PID={pid_str} health=OK")
        return 0
    print(f"port-check: {port} KILITLI/ZOMBI PID={pid_str} health=FAIL")
    return 2


def _kill_pids_on_port_win(port: int) -> list[int]:
    """PowerShell Get-NetTCPConnection ile port sahibi PID'leri sonlandır."""
    if sys.platform != "win32":
        return []
    killed: list[int] = []
    try:
        ps = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue "
                    f"| Select-Object -ExpandProperty OwningProcess -Unique"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=12,
            shell=False,
        )
        for line in (ps.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if _kill_pid(pid):
                    killed.append(pid)
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"kill-port-win: {e}", file=sys.stderr)
    return killed


def _kill_pid(pid: int) -> bool:
    if pid <= 0:
        return False
    ok = False
    _flags = 0x08000000 if sys.platform == "win32" else 0
    for args in (
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        ["taskkill", "/F", "/PID", str(pid)],
    ):
        try:
            cp = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=12,
                shell=False,
                creationflags=_flags,
            )
            if cp.returncode == 0:
                ok = True
                break
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"kill-process: taskkill {' '.join(args)} hata: {e}", file=sys.stderr)
    if not ok and sys.platform == "win32":
        try:
            ps = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"Stop-Process -Id {pid} -Force -ErrorAction Stop",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
                creationflags=0x08000000,
            )
            ok = ps.returncode == 0
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"kill-process: Stop-Process PID {pid} hata: {e}", file=sys.stderr)
    print(f"kill-process: PID {pid} {'OK' if ok else 'FAIL (yonetici gerekebilir)'}")
    return ok


def _kill_ruzgar_api_processes() -> list[int]:
    """run_desktop_api / desktop_server dinleyen tum Python sureclerini sonlandir."""
    if sys.platform != "win32":
        return []
    killed: list[int] = []
    try:
        ps = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" -EA SilentlyContinue | "
                    "Where-Object { $_.CommandLine -match 'run_desktop_api|desktop_server:app|uvicorn' } | "
                    "Select-Object -ExpandProperty ProcessId"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            shell=False,
        )
        for line in (ps.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if _kill_pid(pid):
                    killed.append(pid)
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"kill-ruzgar-api: {e}", file=sys.stderr)
    return killed


def cmd_kill_process(port: int) -> int:
    _kill_ruzgar_api_processes()
    pids = _pids_listening_on_port(port)
    if not pids:
        print(f"kill-process: {port} zaten bos")
        return 0
    for attempt in range(1, 5):
        pids = _pids_listening_on_port(port)
        if not pids:
            break
        for pid in pids:
            _kill_pid(pid)
        if sys.platform == "win32":
            _kill_pids_on_port_win(port)
        time.sleep(0.8)
    time.sleep(0.5)
    remaining = _pids_listening_on_port(port)
    if remaining:
        print(
            f"kill-process: UYARI hala dinleyen PID={remaining} "
            "(Yonetici: .\\Ruzgar.ps1 -ForceRestart)",
            file=sys.stderr,
        )
        return 1
    print(f"kill-process: {port} bosaltildi")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Rüzgar port-check / kill-process")
    ap.add_argument(
        "command",
        choices=("port-check", "kill-process", "kill-all-api"),
        help="port-check | kill-process | kill-all-api",
    )
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = ap.parse_args()
    if args.command == "port-check":
        return cmd_port_check(args.port)
    if args.command == "kill-all-api":
        killed = _kill_ruzgar_api_processes()
        for p in (8779, 8777, args.port):
            cmd_kill_process(int(p))
        print(f"kill-all-api: {len(killed)} python API sureci")
        return 0 if not _pids_listening_on_port(args.port) else 1
    return cmd_kill_process(args.port)


if __name__ == "__main__":
    raise SystemExit(main())
