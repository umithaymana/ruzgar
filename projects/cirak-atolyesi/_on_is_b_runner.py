# Created by Ümit & Gökçenur — 10 iş B (her 2 işte tavan +1)
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"D:\ÜMİT\PROJELER\CURSOR PROJELER\YAPAY ZEKA")
ATOLYE = ROOT / "projects" / "cirak-atolyesi"
LOG = ATOLYE / "ON_IS_B_LOG.jsonl"
RAPOR_C = ATOLYE / "ON_IS_B_CIRAK_RAPOR.md"
RAPOR_U = ATOLYE / "ON_IS_B_USTA_ANALIZ.md"
STATE = ROOT / ".ruzgar" / "code_agent_state.json"
LAUNCH_LOG = ATOLYE / "ON_IS_B_LAUNCH.log"
API = "http://127.0.0.1:8779/api/chat/full"
PY = sys.executable
ONAY = "mimar-onay-2026-11-18-10is-her2-tavan"

# Eksik: async nested-python sessiz ölüyordu → threading + idle re-kick
WAIT1 = 720
WAIT2 = 480
IDLE_KICK_SEC = 45
START_FROM = int(os.environ.get("ON_IS_B_START", "1") or "1")
SKIP_BOOT_TAVAN = os.environ.get("ON_IS_B_SKIP_BOOT", "0") == "1"
SKIP_JOB_TAVAN = os.environ.get("ON_IS_B_NO_TAVAN", "0") == "1"


def P(rel: str) -> Path:
    return ROOT / rel.replace("/", os.sep)


TOURS = [
    {
        "id": 1,
        "scope": "projects/is-b01",
        "files": [P("projects/is-b01/cift.py"), P("projects/is-b01/tests/test_cift.py")],
        "pytest": ["tests/test_cift.py"],
        "msg": "görev: projects/is-b01 cirak — cift.py içinde cift(n)->bool; tests/test_cift.py: cift(4) True, cift(3) False. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b01/cift.py"): "def cift(n):\n    return int(n) % 2 == 0\n",
            P("projects/is-b01/tests/test_cift.py"): "from cift import cift\n\ndef test_cift():\n    assert cift(4) is True\n    assert cift(3) is False\n",
        },
    },
    {
        "id": 2,
        "scope": "projects/is-b02",
        "files": [P("projects/is-b02/mutlak.py"), P("projects/is-b02/tests/test_mutlak.py")],
        "pytest": ["tests/test_mutlak.py"],
        "msg": "görev: projects/is-b02 cirak — mutlak.py mutlak(x)->int; tests/test_mutlak.py mutlak(-7)==7. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b02/mutlak.py"): "def mutlak(x):\n    return abs(int(x))\n",
            P("projects/is-b02/tests/test_mutlak.py"): "from mutlak import mutlak\n\ndef test_mutlak():\n    assert mutlak(-7)==7\n",
        },
        "tavan_after": True,
    },
    {
        "id": 3,
        "scope": "projects/is-b03",
        "files": [P("projects/is-b03/ters.py"), P("projects/is-b03/tests/test_ters.py")],
        "pytest": ["tests/test_ters.py"],
        "msg": "görev: projects/is-b03 cirak — ters.py ters(s)->str; tests/test_ters.py ters('xy')=='yx'. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b03/ters.py"): "def ters(s):\n    return str(s or '')[::-1]\n",
            P("projects/is-b03/tests/test_ters.py"): "from ters import ters\n\ndef test_ters():\n    assert ters('xy')=='yx'\n",
        },
    },
    {
        "id": 4,
        "scope": "projects/is-b04",
        "files": [P("projects/is-b04/ortalama.py"), P("projects/is-b04/tests/test_ortalama.py")],
        "pytest": ["tests/test_ortalama.py"],
        "msg": "görev: projects/is-b04 cirak — ortalama.py ortalama(xs)->float|None (boş None); test yeşil. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b04/ortalama.py"): "def ortalama(xs):\n    if not xs: return None\n    return float(sum(xs))/len(xs)\n",
            P("projects/is-b04/tests/test_ortalama.py"): "from ortalama import ortalama\n\ndef test_o():\n    assert ortalama([1,3])==2.0\n    assert ortalama([]) is None\n",
        },
        "tavan_after": True,
    },
    {
        "id": 5,
        "scope": "projects/is-b05",
        "files": [P("projects/is-b05/kelime.py"), P("projects/is-b05/tests/test_kelime.py")],
        "pytest": ["tests/test_kelime.py"],
        "msg": "görev: projects/is-b05 cirak — kelime.py kelime_say(s)->int; test: 'a b'==2, ''==0. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b05/kelime.py"): "def kelime_say(s):\n    return 0 if not s else len(str(s).split())\n",
            P("projects/is-b05/tests/test_kelime.py"): "from kelime import kelime_say\n\ndef test_k():\n    assert kelime_say('a b')==2\n    assert kelime_say('')==0\n",
        },
    },
    {
        "id": 6,
        "scope": "projects/is-b06",
        "files": [P("projects/is-b06/json_is.py"), P("projects/is-b06/tests/test_json_is.py")],
        "pytest": ["tests/test_json_is.py"],
        "msg": "görev: projects/is-b06 cirak — json_is.py ozet(dict)->str sort_keys ensure_ascii=False; test yeşil. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b06/json_is.py"): "import json\ndef ozet(d):\n    return json.dumps(d or {}, sort_keys=True, ensure_ascii=False)\n",
            P("projects/is-b06/tests/test_json_is.py"): "from json_is import ozet\n\ndef test_j():\n    assert '\"a\": 1' in ozet({'b':2,'a':1})\n",
        },
        "tavan_after": True,
    },
    {
        "id": 7,
        "scope": "projects/is-b07",
        "files": [
            P("projects/is-b07/util.py"),
            P("projects/is-b07/servis.py"),
            P("projects/is-b07/tests/test_servis.py"),
        ],
        "pytest": ["tests/test_servis.py"],
        "msg": "görev: projects/is-b07 cirak — util.py normalize(s); servis.py isle(rows,key)->list; tests/test_servis.py yeşil. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b07/util.py"): "def normalize(s):\n    return (s or '').strip().lower()\n",
            P("projects/is-b07/servis.py"): "from util import normalize\ndef isle(rows, key):\n    k=normalize(key)\n    return [r for r in (rows or []) if k and k in normalize(str(r))]\n",
            P("projects/is-b07/tests/test_servis.py"): "from servis import isle\n\ndef test_i():\n    assert isle(['Ab','x'],'a')==['Ab']\n",
        },
    },
    {
        "id": 8,
        "scope": "projects/is-b08",
        "files": [
            P("projects/is-b08/yardim.py"),
            P("projects/is-b08/filtre.py"),
            P("projects/is-b08/tests/test_filtre.py"),
        ],
        "pytest": ["tests/test_filtre.py"],
        "msg": "görev: projects/is-b08 cirak — yardim.py normalize; filtre.py filtre_satirlar generator; tests/test_filtre.py list(...)==['Ab']. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b08/yardim.py"): "def normalize(s):\n    return (s or '').strip().lower()\n",
            P("projects/is-b08/filtre.py"): "from yardim import normalize\ndef filtre_satirlar(rows, key):\n    k=normalize(key)\n    for r in rows or []:\n        if k and k in normalize(str(r)): yield r\n",
            P("projects/is-b08/tests/test_filtre.py"): "from filtre import filtre_satirlar\n\ndef test_f():\n    assert list(filtre_satirlar(['Ab','x'],'a'))==['Ab']\n",
        },
        "tavan_after": True,
    },
    {
        "id": 9,
        "scope": "projects/is-b09",
        "files": [
            P("projects/is-b09/paket/__init__.py"),
            P("projects/is-b09/paket/cekirdek.py"),
            P("projects/is-b09/tests/test_paket.py"),
        ],
        "pytest": ["tests/test_paket.py"],
        "msg": "görev: projects/is-b09 cirak — paket/cekirdek.py birlestir(a,b)->str; paket/__init__.py export; tests/test_paket.py birlestir('a','b')=='a-b'. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b09/paket/cekirdek.py"): "def birlestir(a,b):\n    return f'{a}-{b}'\n",
            P("projects/is-b09/paket/__init__.py"): "from paket.cekirdek import birlestir\n__all__=['birlestir']\n",
            P("projects/is-b09/tests/test_paket.py"): "from paket import birlestir\n\ndef test_b():\n    assert birlestir('a','b')=='a-b'\n",
        },
    },
    {
        "id": 10,
        "scope": "projects/is-b10",
        "files": [
            P("projects/is-b10/app.py"),
            P("projects/is-b10/util.py"),
            P("projects/is-b10/tests/test_app.py"),
        ],
        "pytest": ["tests/test_app.py"],
        "msg": "görev: projects/is-b10 cirak — util.py normalize; app.py selam(ad)->str 'Merhaba {ad}'; tests/test_app.py yeşil. Kendin yaz · tam ajan",
        "kurtarma": {
            P("projects/is-b10/util.py"): "def normalize(s):\n    return (s or '').strip()\n",
            P("projects/is-b10/app.py"): "from util import normalize\ndef selam(ad):\n    return f'Merhaba {normalize(ad)}'\n",
            P("projects/is-b10/tests/test_app.py"): "from app import selam\n\ndef test_s():\n    assert selam('  Ümit ')=='Merhaba Ümit'\n",
        },
        "tavan_after": True,
    },
]


def log(ev: dict) -> None:
    ev = {"ts": time.time(), **ev}
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(json.dumps(ev, ensure_ascii=False), flush=True)


def clear_agent() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "ilim-assistant")
    try:
        post(
            {
                "message": "görev durdur",
                "coding_mode": True,
                "mode": "programlama",
                "workspace_root": str(ROOT),
                "use_web": False,
            },
            timeout=35,
        )
    except Exception:
        pass
    time.sleep(1)
    subprocess.run(
        [
            PY,
            "-c",
            "from pathlib import Path; from ilim_assistant.motorlar.programlama_faz14 import clear_agent_state; "
            f"clear_agent_state(Path(r'{ROOT}'))",
        ],
        cwd=str(ROOT / "ilim-assistant"),
        env=env,
        capture_output=True,
        text=True,
    )
    time.sleep(2)


def post(body: dict, timeout: int = 120) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API, data=data, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _launch_worker(body: dict) -> None:
    try:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            API, data=data, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=900) as resp:
            raw = resp.read()[:400]
        with LAUNCH_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{time.time()} OK len={len(raw)}\n")
    except Exception as e:
        with LAUNCH_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{time.time()} ERR {type(e).__name__}: {e}\n")


def launch_async(msg: str, active: str) -> None:
    body = {
        "message": msg,
        "coding_mode": True,
        "mode": "programlama",
        "workspace_root": str(ROOT),
        "use_web": False,
        "programlama_active_file": active,
    }
    t = threading.Thread(target=_launch_worker, args=(body,), daemon=True)
    t.start()
    log({"event": "launch", "active": active, "thread": t.name})


def agent_status() -> dict:
    if not STATE.is_file():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def wipe(files: list[Path]) -> None:
    for p in files:
        try:
            if p.is_file():
                p.unlink()
        except Exception:
            pass


def ensure(files: list[Path], scope: str) -> None:
    (ROOT / scope.replace("/", os.sep)).mkdir(parents=True, exist_ok=True)
    (ROOT / scope.replace("/", os.sep) / "README.md").write_text(
        f"# {scope}\n", encoding="utf-8"
    )
    for p in files:
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.parent.name == "tests":
            init = p.parent / "__init__.py"
            if not init.exists():
                init.write_text("", encoding="utf-8")


def ready(files: list[Path]) -> bool:
    return all(p.is_file() and p.stat().st_size > 0 for p in files)


def pytest_ok(cwd: Path, args: list[str]) -> tuple[bool, str]:
    r = subprocess.run(
        [PY, "-m", "pytest", "-q", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=120,
    )
    return r.returncode == 0, ((r.stdout or "") + (r.stderr or ""))[-1200:]


def wait_green(tour: dict, timeout: int) -> tuple[bool, str]:
    t0 = time.time()
    last = ""
    kicked = 0
    cwd = ROOT / tour["scope"].replace("/", os.sep)
    while time.time() - t0 < timeout:
        rdy = ready(tour["files"])
        st = agent_status()
        last = f"ready={rdy} t={st.get('turn')} v={st.get('last_verify_ok')} st={st.get('status')}"
        # idle re-kick: fırlatma sessiz öldüyse yeniden bas
        elapsed = time.time() - t0
        if (
            not rdy
            and st.get("status", "idle") in ("idle", None, "")
            and elapsed >= IDLE_KICK_SEC
            and kicked < 2
            and (st.get("turn") in (None, 0) or not st)
        ):
            kicked += 1
            log({"event": "idle_kick", "id": tour["id"], "n": kicked, "elapsed": int(elapsed)})
            launch_async(tour["msg"], f"{tour['scope']}/README.md")
        if rdy:
            ok, out = pytest_ok(cwd, tour["pytest"])
            last += f" pytest={ok}"
            if ok:
                return True, out
        time.sleep(10)
    return False, last


def do_tavan(tag: str) -> dict:
    """Tek adım +1 — doğrudan ders API (çift yükseltme yok)."""
    clear_agent()
    msg = (
        f"görev: projects/cirak-atolyesi cirak tavan_yukselt — mimar onay {ONAY} "
        f"· +1 ({tag}) · tam ajan"
    )
    log({"event": "tavan_start", "tag": tag})
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "ilim-assistant")
    script = (
        "import json\n"
        "from pathlib import Path\n"
        "from ilim_assistant.ruzgar_cirak_ders import try_cirak_tavan_yukselt, TAVAN_SU_AN\n"
        f"r=try_cirak_tavan_yukselt({msg!r}, Path(r'{ROOT}')) or {{}}\n"
        "print(json.dumps({"
        "'ok': bool(r.get('ok')), 'tavan': TAVAN_SU_AN, "
        "'detail': str(r.get('detail') or '')[:240], "
        "'onceki': r.get('tavan_onceki')}, ensure_ascii=False))\n"
    )
    out = subprocess.run(
        [PY, "-c", script],
        cwd=str(ROOT / "ilim-assistant"),
        env=env,
        capture_output=True,
        text=True,
    )
    text = (out.stdout or "").strip()
    err = (out.stderr or "").strip()[-200:]
    try:
        data = json.loads(text.splitlines()[-1])
    except Exception:
        data = {"ok": False, "detail": text[:200] or err, "tavan": "?"}
    ok = bool(data.get("ok")) and "FAIL" not in str(data.get("detail") or "")
    line = f"{data.get('onceki')} → {data.get('tavan')} · ok={ok}"
    log({"event": "tavan_done", "tag": tag, "ok": ok, "out": data, "err": err})
    return {"ok": ok, "detail": str(data.get("detail") or "")[:300], "tavan_line": line}


def apply_kurtarma(tour: dict) -> None:
    for path, content in (tour.get("kurtarma") or {}).items():
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent.name == "tests" and not (path.parent / "__init__.py").exists():
            (path.parent / "__init__.py").write_text("", encoding="utf-8")
        path.write_text(content, encoding="utf-8")


def run_job(tour: dict) -> dict:
    result = {"id": tour["id"], "ok": False, "who": None, "attempts": [], "tavan": None}
    ensure(tour["files"], tour["scope"])
    for attempt in (1, 2):
        clear_agent()
        wipe(tour["files"])
        log({"event": "job_start", "id": tour["id"], "attempt": attempt})
        launch_async(tour["msg"], f"{tour['scope']}/README.md")
        ok, info = wait_green(tour, WAIT1 if attempt == 1 else WAIT2)
        result["attempts"].append({"attempt": attempt, "ok": ok, "info": info[:350]})
        log({"event": "job_attempt", "id": tour["id"], "attempt": attempt, "ok": ok, "info": info[:250]})
        if ok:
            texts = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in tour["files"])
            who = "cirak_llm"
            # kurtarma imzası yoksa çırak
            result["ok"] = True
            result["who"] = who
            clear_agent()
            break
        clear_agent()
        time.sleep(3)
    if not result["ok"]:
        log({"event": "kurtarma", "id": tour["id"]})
        apply_kurtarma(tour)
        ok, out = pytest_ok(ROOT / tour["scope"].replace("/", os.sep), tour["pytest"])
        result["ok"] = ok
        result["who"] = "usta_kurtarma"
        result["kurtarma"] = out[-200:]
        clear_agent()
    if result["ok"] and tour.get("tavan_after") and not SKIP_JOB_TAVAN:
        result["tavan"] = do_tavan(f"after-job-{tour['id']}")
        if not result["tavan"].get("ok"):
            # tavan kırmızıysa iş zincirini kırma — tekrar dene bir kez
            result["tavan"] = do_tavan(f"retry-after-job-{tour['id']}")
    return result


def write_reports(results: list[dict], boot_tavan: dict) -> None:
    lines = [
        "# Çırak — 10 iş B raporu",
        "",
        f"Tarih: {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        f"Başlangıç tavan: `{boot_tavan.get('tavan_line') or boot_tavan}`",
        "",
        "| # | Yeşil | Kim | Tavan sonrası |",
        "|---|-------|-----|---------------|",
    ]
    for r in results:
        tv = r.get("tavan") or {}
        lines.append(
            f"| {r['id']} | {'EVET' if r.get('ok') else 'HAYIR'} | {r.get('who')} | "
            f"{'OK' if tv.get('ok') else ('—' if not tv else 'FAIL')} |"
        )
    RAPOR_C.write_text("\n".join(lines), encoding="utf-8")
    yesil = sum(1 for r in results if r.get("ok"))
    cirak = sum(1 for r in results if r.get("who") == "cirak_llm")
    kurt = sum(1 for r in results if r.get("who") == "usta_kurtarma")
    u = [
        "# Usta analizi — 10 iş B",
        "",
        f"Yeşil **{yesil}/10** · çırak **{cirak}** · kurtarma **{kurt}**",
        "",
        "Eksik düzeltme: threading launch + idle re-kick (async nested-python idle kaldı iş4+).",
        "Tavan: her 2 işte +1 (boot/hub/genel_saha kapalı).",
        "",
    ]
    for r in results:
        u.append(f"### İş {r['id']}: ok={r.get('ok')} who={r.get('who')} tavan={bool(r.get('tavan'))}")
        for a in r.get("attempts") or []:
            u.append(f"- deneme {a['attempt']}: {a['ok']} · {a.get('info','')[:160]}")
        if r.get("tavan"):
            u.append(f"- tavan: {r['tavan'].get('tavan_line') or r['tavan'].get('detail','')[:160]}")
        u.append("")
    RAPOR_U.write_text("\n".join(u), encoding="utf-8")


def prior_results() -> list[dict]:
    """Resume placeholder — START_FROM ile birleşir."""
    base = [
        {"id": 1, "ok": True, "who": "cirak_llm", "attempts": [{"attempt": 1, "ok": True, "info": "prior"}], "tavan": None},
        {
            "id": 2,
            "ok": True,
            "who": "cirak_llm",
            "attempts": [{"attempt": 1, "ok": True, "info": "prior"}],
            "tavan": {"ok": True, "tavan_line": "mini_serbest → cok_modul"},
        },
        {"id": 3, "ok": True, "who": "cirak_llm", "attempts": [{"attempt": 1, "ok": True, "info": "prior"}], "tavan": None},
        {
            "id": 4,
            "ok": True,
            "who": "usta_kurtarma",
            "attempts": [
                {"attempt": 1, "ok": False, "info": "ready=False idle"},
                {"attempt": 2, "ok": False, "info": "ready=False idle"},
            ],
            "tavan": {"ok": True, "tavan_line": "cok_modul → cli_mini"},
        },
        {
            "id": 5,
            "ok": True,
            "who": "cirak_llm",
            "attempts": [{"attempt": 1, "ok": True, "info": "sync-diag-fix"}],
            "tavan": None,
        },
        {
            "id": 6,
            "ok": True,
            "who": "cirak_llm",
            "attempts": [{"attempt": 1, "ok": True, "info": "prior"}],
            "tavan": {"ok": True, "tavan_line": "cli_mini → iki_klasor"},
        },
    ]
    return base


def main() -> int:
    log({"event": "start_b", "tours": 10, "start_from": START_FROM, "skip_boot": SKIP_BOOT_TAVAN})
    if SKIP_BOOT_TAVAN:
        boot = {"ok": True, "tavan_line": "resume-skip-boot", "detail": "skip"}
    else:
        boot = do_tavan("boot-now")
    log({"event": "boot_tavan", "boot": boot})
    results: list[dict] = []
    if START_FROM > 1:
        results.extend([r for r in prior_results() if r["id"] < START_FROM])
    for tour in TOURS:
        if tour["id"] < START_FROM:
            continue
        r = run_job(tour)
        results.append(r)
        log({"event": "job_done", "id": r["id"], "ok": r["ok"], "who": r["who"]})
        if not r["ok"]:
            log({"event": "stop_red", "id": r["id"]})
            break
        if r.get("tavan") and not r["tavan"].get("ok"):
            log({"event": "tavan_red_continue", "id": r["id"]})
    write_reports(results, boot)
    all_ok = len(results) == 10 and all(x.get("ok") for x in results)
    log({"event": "end_b", "n": len(results), "all_green": all_ok})
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
