"""
RUZGAR tek tık başlatıcı (Python): yerel API (uvicorn) + Electron kabuğu.

Mimar emri (Ümit & Gökçenur):
  - Açılışta 8777 portundaki "ölü" uvicorn süreçleri (health 200 vermiyor) tespit edilip
    sonlandırılır → siyah ekran zombisi yaşanmaz.
  - Electron pencere kapatıldığında launcher uvicorn'u nazikçe sonlandırır → arka planda
    artık kalmaz; bir sonraki açılışta port temiz olur.

NOT: Bu dosya .cursorrules / desktop_server.py içindeki KİLİTLİ motor başlatma sırasına
dokunmaz; sadece API ile Electron'un yaşam döngüsünü orkestre eder.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


ILIM_ASSISTANT = Path(__file__).resolve().parent
PROJECT_ROOT = ILIM_ASSISTANT.parent
ELECTRON_DIR = PROJECT_ROOT / "ruzgar-desktop"
API_PORT = 8777
API_HEALTH = f"http://127.0.0.1:{API_PORT}/api/health"
WAIT_SEC = 180.0
ZOMBI_HEALTH_GRACE_SEC = 4.0  # Açık ama henüz hazır olmayan sağlıklı uvicorn'a tolerans

# Bu launcher'ın açtığı uvicorn süreci (Electron kapanınca onu sonlandırırız).
_API_PROC: subprocess.Popen | None = None


def _log(msg: str) -> None:
    p = Path(tempfile.gettempdir()) / "ruzgar-launch.log"
    try:
        from datetime import datetime

        line = f"{datetime.now().isoformat()} {msg}\n"
        with p.open("a", encoding="utf-8", errors="replace") as f:
            f.write(line)
    except OSError:
        pass


def _api_up(timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(API_HEALTH, timeout=timeout) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


# ---------------------------------------------------------------------------
# 1) Port-zombi temizleme: 8777'i dinleyen ama health 200 vermeyen uvicorn'ları öldürür.
# ---------------------------------------------------------------------------

_NETSTAT_RE = re.compile(
    r"^\s*TCP\s+\S+:" + str(API_PORT) + r"\s+\S+\s+LISTENING\s+(\d+)\s*$",
    re.IGNORECASE,
)


def _pids_listening_on_port() -> list[int]:
    """Windows: ``netstat -ano`` çıktısında 8777 LISTENING olanların PID listesi."""
    try:
        cp = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=8,
            shell=False,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        _log(f"netstat hata: {e}")
        return []
    pids: set[int] = set()
    for line in (cp.stdout or "").splitlines():
        m = _NETSTAT_RE.match(line)
        if m:
            try:
                pids.add(int(m.group(1)))
            except ValueError:
                continue
    # 0 PID (System Idle) veya negatif olamaz; yine de filtreyelim.
    return sorted(p for p in pids if p > 4)


def _kill_pid(pid: int) -> bool:
    """Windows ``taskkill /F``; yetki yetmezse False döner."""
    if pid <= 0:
        return False
    try:
        cp = subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
            text=True,
            timeout=8,
            shell=False,
            creationflags=0x08000000 if sys.platform == "win32" else 0,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        _log(f"taskkill PID={pid} hata: {e}")
        return False
    if cp.returncode == 0:
        _log(f"taskkill PID={pid} OK")
        return True
    _log(f"taskkill PID={pid} basarisiz rc={cp.returncode} stderr={(cp.stderr or '').strip()[:200]}")
    return False


def _kill_port_zombies() -> None:
    """8777'de LISTENING ama health 200 vermeyen 'ölü' uvicorn'ları sonlandırır.

    Önce bir health 200 ihtimaline tolerans verilir (yeni açılan sağlıklı uvicorn boğulmasın).
    """
    deadline = time.monotonic() + ZOMBI_HEALTH_GRACE_SEC
    while time.monotonic() < deadline:
        if _api_up(timeout=1.5):
            _log("Port saglikli (health 200) — zombi yok, dokunulmadi")
            return
        time.sleep(0.4)

    pids = _pids_listening_on_port()
    if not pids:
        _log("8777 bos — temizlik gerekmiyor")
        return

    _log(f"Zombi tespit edildi PID(ler)={pids} → sonlandiriliyor")
    for pid in pids:
        ok = _kill_pid(pid)
        if not ok:
            _log(f"UYARI: PID {pid} sonlandirilamadi (yetki/yonetici izni gerekebilir)")
    # Soketin Windows tarafindan tam serbest birakilmasi icin kisa bekleme.
    time.sleep(1.0)


# ---------------------------------------------------------------------------
# 2) API + Electron yaşam döngüsü.
# ---------------------------------------------------------------------------


def _win_popen_no_window(
    args: list[str],
    *,
    cwd: str,
    env: dict | None = None,
) -> subprocess.Popen:
    kw: dict = {"cwd": cwd, "env": env or os.environ.copy()}
    if sys.platform == "win32":
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    return subprocess.Popen(args, **kw)


def _resolve_python() -> str:
    return sys.executable


def _ensure_api() -> None:
    """Sağlıklıysa dokunma; değilse zombileri temizle ve yeni uvicorn aç."""
    global _API_PROC

    _kill_port_zombies()

    if _api_up():
        _log("API zaten ayakta (saglikli)")
        return

    py = _resolve_python()
    args = [py, "-m", "uvicorn", "desktop_server:app", "--host", "127.0.0.1", "--port", str(API_PORT)]
    _log(f"API baslatiliyor: {' '.join(args)}")
    _API_PROC = _win_popen_no_window(args, cwd=str(ILIM_ASSISTANT))

    deadline = time.monotonic() + WAIT_SEC
    while time.monotonic() < deadline:
        # Erken çıkış: uvicorn çoktan öldüyse beklemenin anlamı yok.
        rc = _API_PROC.poll()
        if rc is not None:
            raise RuntimeError(
                f"uvicorn beklenmedik şekilde sonlandı (rc={rc}). "
                f"Log: {Path(tempfile.gettempdir()) / 'ruzgar-api.err'}"
            )
        if _api_up():
            _log("API hazir")
            return
        time.sleep(0.5)
    raise RuntimeError(
        f"API {WAIT_SEC:.0f} sn icinde acilmadi. Log: {Path(tempfile.gettempdir()) / 'ruzgar-api.err'}"
    )


def _terminate_api() -> None:
    """Bu launcher'ın açtığı uvicorn'u kibarca, gerekirse sert kapatır."""
    global _API_PROC
    proc = _API_PROC
    if proc is None:
        _log("API'yi biz acmadik — terminate atlandi")
        return
    if proc.poll() is not None:
        _log(f"API zaten sonlanmis (rc={proc.returncode})")
        _API_PROC = None
        return
    _log("API sonlandiriliyor (terminate)…")
    try:
        proc.terminate()
    except OSError as e:
        _log(f"terminate hata: {e}")
    try:
        proc.wait(timeout=8)
        _log(f"API kapatildi (rc={proc.returncode})")
    except subprocess.TimeoutExpired:
        _log("terminate cevap vermedi → kill")
        try:
            proc.kill()
            proc.wait(timeout=4)
        except (OSError, subprocess.TimeoutExpired) as e:
            _log(f"kill hata: {e}")
    _API_PROC = None


def _electron_cmd() -> Path:
    return ELECTRON_DIR / "node_modules" / ".bin" / "electron.cmd"


def _run_electron_blocking() -> int:
    """Electron'u **bekleyerek** çalıştırır; pencere kapatılınca rc döner."""
    if not (ELECTRON_DIR / "package.json").is_file():
        raise RuntimeError(f"ruzgar-desktop eksik: {ELECTRON_DIR}")
    cmd = _electron_cmd()
    if not cmd.is_file():
        _log("npm install (electron)...")
        npm_exe = shutil.which("npm.cmd") or shutil.which("npm")
        if not npm_exe:
            raise RuntimeError("npm bulunamadi (Node.js LTS kurun).")
        r = subprocess.run(
            [npm_exe, "install"],
            cwd=str(ELECTRON_DIR),
            shell=False,
            env=os.environ.copy(),
        )
        if r.returncode != 0 or not cmd.is_file():
            raise RuntimeError("npm install basarisiz veya electron.cmd yok")
    _log("Electron aciliyor (blocking)…")
    # subprocess.run = pencere kapanana kadar burada bloklanır.
    cp = subprocess.run(
        [str(cmd), "."],
        cwd=str(ELECTRON_DIR),
        env=os.environ.copy(),
    )
    _log(f"Electron kapandi (rc={cp.returncode})")
    return cp.returncode


def _msg_err(text: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("RUZGAR", text)
        root.destroy()
    except Exception:
        print(text, file=sys.stderr)


def _install_signal_cleanup() -> None:
    """Süreç bir sinyalle (Ctrl+C, kapatma vs.) sonlandırılırsa uvicorn'u da temizle."""
    def _handler(signum, _frame):
        _log(f"Sinyal alindi ({signum}) → API temizlenecek")
        _terminate_api()
        # Standart çıkış kodu.
        sys.exit(128 + int(signum))

    for sig_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            try:
                signal.signal(sig, _handler)
            except (ValueError, OSError):
                pass


def main() -> int:
    _install_signal_cleanup()
    try:
        os.chdir(ILIM_ASSISTANT)
        try:
            from ilim_assistant.ruzgar_hafiza_koprusu import ensure_hafiza_bridge_ready

            ensure_hafiza_bridge_ready()
        except Exception:
            pass
        _ensure_api()
        try:
            rc = _run_electron_blocking()
        finally:
            # Electron kapandı (veya patladı) — yaşam döngüsü bitti, uvicorn'u kapat.
            _terminate_api()
        return rc
    except Exception as e:
        _log(f"HATA: {e}")
        _terminate_api()
        _msg_err(f"RUZGAR baslatilamadi:\n{e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
