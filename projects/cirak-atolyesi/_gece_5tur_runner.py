# Created by Ümit & Gökçenur — gece 5 tur koşucu (Mimar emri)
"""Çırağa 5 kademeli iş ver; kart yeşil olmadan ilerleme; bitince rapor."""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(r"D:\ÜMİT\PROJELER\CURSOR PROJELER\YAPAY ZEKA")
ATOLYE = ROOT / "projects" / "cirak-atolyesi"
STATE = ROOT / ".ruzgar" / "code_agent_state.json"
COMPLIANCE = ROOT / ".ruzgar" / "agent_compliance.json"
LOG = ATOLYE / "GECE_5TUR_LOG.jsonl"
RAPOR_CIRAK = ATOLYE / "GECE_5TUR_CIRAK_RAPORU.md"
RAPOR_USTA = ATOLYE / "GECE_5TUR_USTA_ANALIZ.md"
API = "http://127.0.0.1:8779/api/chat/full"

TOURS = [
    {
        "id": 1,
        "gorev": "GOREV_GECE_T1.md",
        "zorluk": "kolay",
        "files": [
            ATOLYE / "fark_is.py",
            ATOLYE / "tests" / "test_fark.py",
        ],
        "pytest": ["tests/test_fark.py"],
        "msg": (
            "görev: projects/cirak-atolyesi cirak — GOREV_GECE_T1.md oku. "
            "fark_is.py içinde fark(a,b)->int yaz (a-b); "
            "tests/test_fark.py yaz (fark(9,4)==5, fark(3,10)==-7). "
            "Atölye dışı yazma. İki dosya da zorunlu. Kendin yaz · tam ajan"
        ),
    },
    {
        "id": 2,
        "gorev": "GOREV_GECE_T2.md",
        "zorluk": "orta",
        "files": [
            ATOLYE / "bol_is.py",
            ATOLYE / "tests" / "test_bol.py",
        ],
        "pytest": ["tests/test_bol.py"],
        "msg": (
            "görev: projects/cirak-atolyesi cirak — GOREV_GECE_T2.md oku. "
            "bol_is.py içinde bol(a,b): b==0 ise None, değilse float bölüm. "
            "tests/test_bol.py: bol(10,2)==5.0, bol(1,0) is None, bol(-6,3)==-2.0. "
            "İki dosya zorunlu. Kendin yaz · tam ajan"
        ),
    },
    {
        "id": 3,
        "gorev": "GOREV_GECE_T3.md",
        "zorluk": "zor",
        "files": [
            ATOLYE / "kelime_say.py",
            ATOLYE / "tests" / "test_kelime_say.py",
        ],
        "pytest": ["tests/test_kelime_say.py"],
        "msg": (
            "görev: projects/cirak-atolyesi cirak — GOREV_GECE_T3.md oku. "
            "kelime_say.py içinde kelime_say(metin)->int yaz. "
            "tests/test_kelime_say.py: "
            "kelime_say('Merhaba güzel dünya')==3, ''==0, '  a  b  '==2. "
            "İki dosya zorunlu. Kendin yaz · tam ajan"
        ),
    },
    {
        "id": 4,
        "gorev": "GOREV_GECE_T4.md",
        "zorluk": "daha_zor",
        "files": [
            ATOLYE / "json_ozet.py",
            ATOLYE / "tests" / "test_json_ozet.py",
        ],
        "pytest": ["tests/test_json_ozet.py"],
        "msg": (
            "görev: projects/cirak-atolyesi cirak — GOREV_GECE_T4.md oku. "
            "json_ozet.py içinde json_ozet(dict)->str (sort_keys=True, ensure_ascii=False). "
            "tests/test_json_ozet.py yeşil. İki dosya zorunlu. Kendin yaz · tam ajan"
        ),
    },
    {
        "id": 5,
        "gorev": "GOREV_GECE_T5.md",
        "zorluk": "en_zor",
        "files": [
            ATOLYE / "filtre_yardim.py",
            ATOLYE / "filtre_satir.py",
            ATOLYE / "tests" / "test_filtre.py",
        ],
        "pytest": ["tests/test_filtre.py"],
        "msg": (
            "görev: projects/cirak-atolyesi cirak — GOREV_GECE_T5.md oku. "
            "filtre_yardim.py: normalize(s). filtre_satir.py: filtre_satirlar generator. "
            "tests/test_filtre.py yeşil. Üç dosya zorunlu. Kendin yaz · tam ajan"
        ),
    },
]

# Son çare şablonları (yalnız LLM 2 denemede yeşil olmazsa — dürüst kurtarma)
KURTARMA = {
    1: {
        ATOLYE / "fark_is.py": (
            "# Created by Ümit & Gökçenur — gece T1 kurtarma\n"
            "def fark(a: int, b: int) -> int:\n"
            "    return int(a) - int(b)\n"
        ),
        ATOLYE / "tests" / "test_fark.py": (
            "# Created by Ümit & Gökçenur — gece T1 kurtarma\n"
            "from fark_is import fark\n\n"
            "def test_fark():\n"
            "    assert fark(9, 4) == 5\n"
            "    assert fark(3, 10) == -7\n"
        ),
    },
    2: {
        ATOLYE / "bol_is.py": (
            "# Created by Ümit & Gökçenur — gece T2 kurtarma\n"
            "def bol(a, b):\n"
            "    if b == 0:\n"
            "        return None\n"
            "    return float(a) / float(b)\n"
        ),
        ATOLYE / "tests" / "test_bol.py": (
            "# Created by Ümit & Gökçenur — gece T2 kurtarma\n"
            "from bol_is import bol\n\n"
            "def test_bol():\n"
            "    assert bol(10, 2) == 5.0\n"
            "    assert bol(1, 0) is None\n"
            "    assert bol(-6, 3) == -2.0\n"
        ),
    },
    3: {
        ATOLYE / "kelime_say.py": (
            "# Created by Ümit & Gökçenur — gece T3 kurtarma\n"
            "def kelime_say(metin: str) -> int:\n"
            "    if not metin:\n"
            "        return 0\n"
            "    return len(str(metin).split())\n"
        ),
        ATOLYE / "tests" / "test_kelime_say.py": (
            "# Created by Ümit & Gökçenur — gece T3 kurtarma\n"
            "from kelime_say import kelime_say\n\n"
            "def test_kelime_say():\n"
            "    assert kelime_say('Merhaba güzel dünya') == 3\n"
            "    assert kelime_say('') == 0\n"
            "    assert kelime_say('  a  b  ') == 2\n"
        ),
    },
    4: {
        ATOLYE / "json_ozet.py": (
            "# Created by Ümit & Gökçenur — gece T4 kurtarma\n"
            "import json\n\n"
            "def json_ozet(veri: dict) -> str:\n"
            "    return json.dumps(veri or {}, sort_keys=True, ensure_ascii=False)\n"
        ),
        ATOLYE / "tests" / "test_json_ozet.py": (
            "# Created by Ümit & Gökçenur — gece T4 kurtarma\n"
            "from json_ozet import json_ozet\n\n"
            "def test_json_ozet():\n"
            "    assert json_ozet({'b': 2, 'a': 1}) == '{\"a\": 1, \"b\": 2}'\n"
            "    assert json_ozet({}) == '{}'\n"
        ),
    },
    5: {
        ATOLYE / "filtre_yardim.py": (
            "# Created by Ümit & Gökçenur — gece T5 kurtarma\n"
            "def normalize(s: str) -> str:\n"
            "    return (s or '').strip().lower()\n"
        ),
        ATOLYE / "filtre_satir.py": (
            "# Created by Ümit & Gökçenur — gece T5 kurtarma\n"
            "from filtre_yardim import normalize\n\n"
            "def filtre_satirlar(satirlar, anahtar: str):\n"
            "    key = normalize(anahtar)\n"
            "    for s in satirlar or []:\n"
            "        if key and key in normalize(str(s)):\n"
            "            yield s\n"
        ),
        ATOLYE / "tests" / "test_filtre.py": (
            "# Created by Ümit & Gökçenur — gece T5 kurtarma\n"
            "from filtre_satir import filtre_satirlar\n\n"
            "def test_filtre():\n"
            "    assert list(filtre_satirlar(['Merhaba', 'x', 'MERHABA dünya'], 'merhaba')) == "
            "['Merhaba', 'MERHABA dünya']\n"
            "    assert list(filtre_satirlar([], 'a')) == []\n"
        ),
    },
}


def log(event: dict) -> None:
    event = {"ts": time.time(), **event}
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps(event, ensure_ascii=False), flush=True)


def clear_agent() -> None:
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "ilim-assistant")
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; from ilim_assistant.motorlar.programlama_faz14 import clear_agent_state; "
            f"clear_agent_state(Path(r'{ROOT}'))",
        ],
        cwd=str(ROOT / "ilim-assistant"),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    stop_body = {
        "message": "görev durdur",
        "coding_mode": True,
        "mode": "programlama",
        "workspace_root": str(ROOT),
        "use_web": False,
    }
    try:
        post_json(stop_body, timeout=40)
    except Exception:
        pass


def post_json(body: dict, timeout: int = 600) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def launch_async(msg: str, gorev: str) -> None:
    """Fire-and-forget via subprocess so we can poll disk."""
    body = {
        "message": msg,
        "coding_mode": True,
        "mode": "programlama",
        "workspace_root": str(ROOT),
        "use_web": False,
        "programlama_active_file": f"projects/cirak-atolyesi/{gorev}",
    }
    payload = json.dumps(body, ensure_ascii=False)
    script = (
        "import json,urllib.request,sys\n"
        f"body={payload!r}\n"
        "req=urllib.request.Request("
        f"{API!r},data=body.encode('utf-8'),"
        "headers={'Content-Type':'application/json; charset=utf-8'},method='POST')\n"
        "try:\n"
        "  urllib.request.urlopen(req,timeout=900).read()\n"
        "  print('API_DONE')\n"
        "except Exception as e:\n"
        "  print('API_ERR',e)\n"
    )
    subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=str(ROOT / "ilim-assistant"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def files_ready(files: list[Path]) -> bool:
    return all(p.is_file() and p.stat().st_size > 0 for p in files)


def run_pytest(args: list[str]) -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *args],
        cwd=str(ATOLYE),
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode == 0, out[-2000:]


def read_state() -> dict:
    if not STATE.is_file():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def last_cirak_tools(n: int = 5) -> list[dict]:
    if not COMPLIANCE.is_file():
        return []
    try:
        d = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = []
    for s in d.get("sessions", []):
        if s.get("scope_rel") != "projects/cirak-atolyesi":
            continue
        rows.extend(s.get("turns") or [])
    return rows[-n:]


def diagnose(tour: dict, attempt: int) -> dict:
    st = read_state()
    tools = last_cirak_tools(8)
    missing = [str(p.relative_to(ROOT)).replace("\\", "/") for p in tour["files"] if not p.is_file()]
    only_grep = bool(tools) and all(
        set(t.get("tools") or []) <= {"grep", "read"} for t in tools[-3:]
    )
    return {
        "attempt": attempt,
        "state": {k: st.get(k) for k in ("status", "turn", "last_verify_ok")},
        "missing": missing,
        "recent_tools": [
            {"turn": t.get("turn"), "tools": t.get("tools"), "writes": t.get("writes_ok"), "viol": t.get("violations")}
            for t in tools[-5:]
        ],
        "likely": (
            "grep_dongusu"
            if only_grep
            else ("eksik_dosya" if missing else "pytest_veya_icerik")
        ),
    }


def wipe_targets(files: list[Path]) -> None:
    for p in files:
        try:
            if p.is_file():
                p.unlink()
        except Exception:
            pass


def apply_kurtarma(tid: int) -> None:
    for path, content in KURTARMA[tid].items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def wait_green(tour: dict, timeout_sec: int = 720) -> tuple[bool, str]:
    t0 = time.time()
    last = ""
    while time.time() - t0 < timeout_sec:
        ready = files_ready(tour["files"])
        st = read_state()
        last = f"ready={ready} state={st.get('status')} t={st.get('turn')}"
        if ready:
            ok, out = run_pytest(tour["pytest"])
            last = f"{last} pytest={ok}"
            if ok:
                return True, out
            log({"event": "pytest_red", "tour": tour["id"], "out": out[-800:]})
        time.sleep(15)
    return False, last


def run_tour(tour: dict) -> dict:
    result = {
        "id": tour["id"],
        "zorluk": tour["zorluk"],
        "ok": False,
        "who": None,
        "attempts": [],
        "diag": [],
    }
    for attempt in (1, 2):
        clear_agent()
        wipe_targets(tour["files"])
        log({"event": "tour_start", "tour": tour["id"], "attempt": attempt, "zorluk": tour["zorluk"]})
        launch_async(tour["msg"], tour["gorev"])
        ok, info = wait_green(tour, timeout_sec=780 if attempt == 1 else 600)
        diag = diagnose(tour, attempt)
        result["attempts"].append({"attempt": attempt, "ok": ok, "info": info})
        result["diag"].append(diag)
        log({"event": "tour_attempt_end", "tour": tour["id"], "attempt": attempt, "ok": ok, "diag": diag})
        if ok:
            # kim yazdı? kurtarma imzası yoksa çırak/LLM
            texts = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in tour["files"])
            who = "usta_kurtarma" if "gece T" in texts and "kurtarma" in texts else "cirak_llm"
            # eğer önceki kurtarma kalıntısı değilse ve yeni yazıldıysa
            if "kurtarma" not in texts:
                who = "cirak_llm"
            result["ok"] = True
            result["who"] = who
            clear_agent()
            return result
        # teşhis: grep döngüsü — stop + yeniden dene (kapılar zaten var)
        clear_agent()
        time.sleep(5)

    # 2 LLM denemesi kırmızı → usta kurtarma (kart yeşil, dürüst kayıt)
    log({"event": "kurtarma", "tour": tour["id"], "reason": result["diag"][-1] if result["diag"] else {}})
    apply_kurtarma(tour["id"])
    ok, out = run_pytest(tour["pytest"])
    result["ok"] = ok
    result["who"] = "usta_kurtarma"
    result["kurtarma_pytest"] = out[-500:]
    clear_agent()
    return result


def write_reports(results: list[dict]) -> None:
    lines = [
        "# Çırak raporu — Gece 5 tur",
        "",
        f"Tarih: {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "| Tur | Zorluk | Yeşil | Kim yaptı |",
        "|-----|--------|-------|-----------|",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['zorluk']} | {'EVET' if r['ok'] else 'HAYIR'} | {r.get('who') or '-'} |"
        )
    lines += [
        "",
        "## Çırak notu",
        "",
        "Her turda dosya + pytest kapısı uygulandı. "
        "Yazamadığım turda usta kurtardı; bunu saklamıyorum.",
        "",
    ]
    for r in results:
        lines.append(f"### Tur {r['id']}")
        lines.append(f"- Sonuç: {'yeşil' if r['ok'] else 'kırmızı'}")
        lines.append(f"- Kim: {r.get('who')}")
        if r.get("diag"):
            last = r["diag"][-1]
            lines.append(f"- Son teşhis: `{last.get('likely')}` missing={last.get('missing')}")
        lines.append("")
    RAPOR_CIRAK.write_text("\n".join(lines), encoding="utf-8")

    yesil = sum(1 for r in results if r["ok"])
    cirak = sum(1 for r in results if r.get("who") == "cirak_llm")
    kurt = sum(1 for r in results if r.get("who") == "usta_kurtarma")
    usta = [
        "# Usta analizi — Gece 5 tur",
        "",
        f"Tarih: {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Özet",
        f"- Kart yeşil: **{yesil}/5**",
        f"- Çırak LLM kendi yazdı: **{cirak}**",
        f"- Usta kurtarma: **{kurt}**",
        "",
        "## Ne gördük",
        "1. Yazım kapısı / dosya kapısı olmadan çırak grep döngüsüne düşüp yarıda bitirebiliyordu.",
        "2. Bu gece her turda zorunlu dosya + hedefli pytest ile kart kilitlendi.",
        "3. LLM hâlâ güvenilir değil: timeout / salt keşif riski var; 2 deneme sonrası kurtarma devreye girdi.",
        "",
        "## Tur tur",
        "",
    ]
    for r in results:
        usta.append(f"### Tur {r['id']} ({r['zorluk']})")
        usta.append(f"- Yeşil: {r['ok']} · Kim: {r.get('who')}")
        for a in r.get("attempts") or []:
            usta.append(f"  - deneme {a['attempt']}: ok={a['ok']} · {a.get('info')}")
        for d in r.get("diag") or []:
            usta.append(
                f"  - teşhis{d.get('attempt')}: {d.get('likely')} missing={d.get('missing')} tools={d.get('recent_tools')}"
            )
        usta.append("")
    usta += [
        "## Sonraki sıkılaştırma (öneri)",
        "- Eksik dosyayı aynı turda mid-turn ile zorla yazdır.",
        "- Atölye pytest'ini yalnızca hedef test dosyasına kilitle (scope-wide yalan yeşil kalmasın).",
        "- Tur başına daha kısa hedef + yazım şablonu örneği (cevabı değil, formatı).",
        "",
    ]
    RAPOR_USTA.write_text("\n".join(usta), encoding="utf-8")


def main() -> int:
    if LOG.exists():
        LOG.unlink()
    log({"event": "night_start", "tours": len(TOURS)})
    results = []
    for tour in TOURS:
        r = run_tour(tour)
        results.append(r)
        log({"event": "tour_done", "result": {k: r[k] for k in ("id", "ok", "who", "zorluk")}})
        if not r["ok"]:
            log({"event": "abort_not_green", "tour": tour["id"]})
            break
    write_reports(results)
    log({"event": "night_end", "results": [{k: r[k] for k in ("id", "ok", "who")} for r in results]})
    return 0 if all(r["ok"] for r in results) and len(results) == 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
