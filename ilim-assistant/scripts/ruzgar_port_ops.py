"""
Rüzgar port işlemleri: port-check, kill-process.

Kullanım:
  python scripts/ruzgar_port_ops.py port-check [--port 8777]
  python scripts/ruzgar_port_ops.py kill-process [--port 8777]

Çıkış kodları (port-check):
  0 — port dinleniyor ve /api/health 200 + ok:true
  1 — port boş (dinleyen yok)
  2 — port dolu ama sağlıksız (zombi / kilit)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

DEFAULT_PORT = 8777
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
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if r.status != 200:
                return False
            raw = r.read().decode("utf-8", errors="replace")
            data = __import__("json").loads(raw)
            return bool(data.get("ok"))
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


def _kill_pid(pid: int) -> bool:
    if pid <= 0:
        return False
    ok = False
    try:
        cp = subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
            text=True,
            timeout=8,
            shell=False,
            creationflags=0x08000000 if sys.platform == "win32" else 0,
        )
        ok = cp.returncode == 0
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"kill-process: taskkill PID {pid} hata: {e}", file=sys.stderr)
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


def cmd_kill_process(port: int) -> int:
    pids = _pids_listening_on_port(port)
    if not pids:
        print(f"kill-process: {port} zaten bos")
        return 0
    for pid in pids:
        _kill_pid(pid)
    time.sleep(1.0)
    remaining = _pids_listening_on_port(port)
    if remaining:
        print(f"kill-process: UYARI hala dinleyen PID={remaining}", file=sys.stderr)
        return 1
    print(f"kill-process: {port} bosaltildi")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Rüzgar port-check / kill-process")
    ap.add_argument(
        "command",
        choices=("port-check", "kill-process"),
        help="port-check | kill-process",
    )
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = ap.parse_args()
    if args.command == "port-check":
        return cmd_port_check(args.port)
    return cmd_kill_process(args.port)


if __name__ == "__main__":
    raise SystemExit(main())
