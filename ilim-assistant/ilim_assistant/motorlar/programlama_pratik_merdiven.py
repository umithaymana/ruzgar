# -*- coding: utf-8 -*-
"""
S3 — Kontrollü pratik merdiveni (izinli projects/ alanı).

Basamaklar:
  1 tek dosya  → projects/ruzgar_pratik/hello.py
  2 iskelet    → projects/ruzgar_pratik_iskelet (python_package scaffold)
  3 yama       → core.py'ye ekstra fonksiyon
  4 doğrula    → pytest + rapor
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRATIK_VERSION = "programlama-pratik-merdiven-v1-2026-11-03"
SLUG_TEK = "ruzgar_pratik"
SLUG_ISKELET = "ruzgar_pratik_iskelet"
PKG = "ruzgar_pratik_iskelet"

_YARDIM = (
    "Kontrollü pratik merdiveni (izinli `projects/`):\n"
    "· pratik 1 — tek dosya yaz (hello.py)\n"
    "· pratik 2 — paket iskeleti kur\n"
    "· pratik 3 — yama uygula (greet_ruzgar)\n"
    "· pratik 4 — doğrula ve raporla\n"
    "· pratik durum — hangi basamaktayız\n"
    "Zincir: `pratik 1 sonra pratik 2` gibi sırayla da olur."
)


def _root() -> Path:
    from ilim_assistant.motorlar.programlama_motoru import repo_root

    return Path(repo_root())


def _state_path(root: Path) -> Path:
    return root / "projects" / ".ruzgar_pratik_state.json"


def _load_state(root: Path) -> dict[str, Any]:
    import json

    p = _state_path(root)
    if not p.exists():
        return {"basamak": 0, "ok": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"basamak": 0, "ok": {}}


def _save_state(root: Path, state: dict[str, Any]) -> None:
    import json

    p = _state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    state["updated_utc"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_allowed(root: Path, rel: str) -> tuple[bool, str]:
    from ilim_assistant.motorlar.programlama_faz3 import programlama_write_allowed

    return programlama_write_allowed(root, rel)


def basamak1_tek_dosya(root: Path | None = None) -> dict[str, Any]:
    root = root or _root()
    rel = f"projects/{SLUG_TEK}/hello.py"
    ok, reason = _write_allowed(root, rel)
    if not ok:
        return {"ok": False, "basamak": 1, "reply": f"Yazım reddedildi: {reason}"}
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = (
        '# -*- coding: utf-8 -*-\n'
        '"""Rüzgar kontrollü pratik — basamak 1 (tek dosya)."""\n\n'
        "def merhaba(isim: str = \"Mimar\") -> str:\n"
        '    return f"Merhaba {isim}, pratik 1 tamam."\n\n'
        'if __name__ == "__main__":\n'
        "    print(merhaba())\n"
    )
    dest.write_text(body, encoding="utf-8")
    st = _load_state(root)
    st["basamak"] = max(int(st.get("basamak") or 0), 1)
    st.setdefault("ok", {})["1"] = True
    st["hello"] = rel.replace("\\", "/")
    _save_state(root, st)
    return {
        "ok": True,
        "basamak": 1,
        "reply": (
            f"Basamak 1 OK — tek dosya yazıldı.\n"
            f"· Dosya: `{rel}`\n"
            f"· Çalıştır: `python {rel}`\n"
            f"Sonraki: `pratik 2`"
        ),
        "path": rel,
    }


def basamak2_iskelet(root: Path | None = None) -> dict[str, Any]:
    root = root or _root()
    from ilim_assistant.motorlar.programlama_faz6 import run_scaffold

    # force=False: varsa dokunma; yoksa kur
    result = run_scaffold("python_package", SLUG_ISKELET, root, force=False)
    ok = bool(result.get("ok"))
    # zaten varsa da pratik için OK say
    scope = f"projects/{SLUG_ISKELET}"
    if (root / scope / "pyproject.toml").exists():
        ok = True
    st = _load_state(root)
    if ok:
        st["basamak"] = max(int(st.get("basamak") or 0), 2)
        st.setdefault("ok", {})["2"] = True
        st["iskelet"] = scope
        _save_state(root, st)
        return {
            "ok": True,
            "basamak": 2,
            "reply": (
                f"Basamak 2 OK — paket iskeleti hazır.\n"
                f"· Klasör: `{scope}`\n"
                f"· Şablon: python_package\n"
                f"Sonraki: `pratik 3`"
            ),
            "scaffold": result,
        }
    return {
        "ok": False,
        "basamak": 2,
        "reply": f"Basamak 2 başarısız: {result.get('error') or result.get('report') or result}",
        "scaffold": result,
    }


def basamak3_yama(root: Path | None = None) -> dict[str, Any]:
    root = root or _root()
    rel = f"projects/{SLUG_ISKELET}/{PKG}/core.py"
    ok, reason = _write_allowed(root, rel)
    if not ok:
        return {"ok": False, "basamak": 3, "reply": f"Yazım reddedildi: {reason}"}
    path = root / rel
    if not path.exists():
        return {
            "ok": False,
            "basamak": 3,
            "reply": "Önce `pratik 2` ile iskeleti kur (core.py yok).",
        }
    text = path.read_text(encoding="utf-8")
    if "def greet_ruzgar" in text:
        note = "Yama zaten vardı — yeniden uygulandı sayıldı."
    else:
        text = text.rstrip() + (
            "\n\n\ndef greet_ruzgar() -> str:\n"
            '    """Kontrollü pratik yaması — basamak 3."""\n'
            '    return greet("Rüzgar")\n'
        )
        path.write_text(text + "\n", encoding="utf-8")
        note = "core.py içine `greet_ruzgar()` eklendi."

    test_rel = f"projects/{SLUG_ISKELET}/tests/test_core.py"
    tok, treason = _write_allowed(root, test_rel)
    if tok:
        tpath = root / test_rel
        if tpath.exists():
            tt = tpath.read_text(encoding="utf-8")
            if "greet_ruzgar" not in tt:
                if "from " in tt and "greet" in tt and "greet_ruzgar" not in tt.split("import", 1)[-1]:
                    tt = tt.replace("from ruzgar_pratik_iskelet.core import greet",
                                    "from ruzgar_pratik_iskelet.core import greet, greet_ruzgar")
                if "def test_greet_ruzgar" not in tt:
                    tt = tt.rstrip() + (
                        "\n\ndef test_greet_ruzgar():\n"
                        '    assert "Rüzgar" in greet_ruzgar()\n'
                    )
                tpath.write_text(tt + "\n", encoding="utf-8")
                note += " Test güncellendi."

    st = _load_state(root)
    st["basamak"] = max(int(st.get("basamak") or 0), 3)
    st.setdefault("ok", {})["3"] = True
    _save_state(root, st)
    return {
        "ok": True,
        "basamak": 3,
        "reply": (
            f"Basamak 3 OK — yama uygulandı.\n"
            f"· {note}\n"
            f"· Dosya: `{rel}`\n"
            f"Sonraki: `pratik 4`"
        ),
    }


def basamak4_dogrula(root: Path | None = None) -> dict[str, Any]:
    root = root or _root()
    scope = f"projects/{SLUG_ISKELET}"
    if not (root / scope).exists():
        return {
            "ok": False,
            "basamak": 4,
            "reply": "Önce `pratik 2` ve `pratik 3` gerekir.",
        }
    from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

    rep = run_project_verify(root, scope, goal="pratik merdiven doğrula")
    ok = bool(rep and getattr(rep, "ok", False))
    detail = ""
    if rep is not None:
        detail = (
            f"preset={getattr(rep, 'preset', '?')} "
            f"exit={getattr(rep, 'exit_code', '?')}"
        )
        out = (getattr(rep, "stdout", "") or "")[-400:]
        err = (getattr(rep, "stderr", "") or "")[-400:]
        if out:
            detail += f"\n--- stdout ---\n{out}"
        if err:
            detail += f"\n--- stderr ---\n{err}"
    st = _load_state(root)
    if ok:
        st["basamak"] = 4
        st.setdefault("ok", {})["4"] = True
    _save_state(root, st)
    return {
        "ok": ok,
        "basamak": 4,
        "reply": (
            f"Basamak 4 {'OK' if ok else 'FAIL'} — doğrulama.\n"
            f"· Kapsam: `{scope}`\n"
            f"· {detail or 'rapor yok'}\n"
            + (
                "Merdiven tamam. Rüzgar kontrollü pratikte 1→4 geçti.\n"
                "Sonraki hedef: gerçek küçük görev (S3+)."
                if ok
                else "Düzeltip `pratik 4` de."
            )
        ),
        "verify_ok": ok,
    }


def durum(root: Path | None = None) -> dict[str, Any]:
    root = root or _root()
    st = _load_state(root)
    ok = st.get("ok") or {}
    lines = [
        f"Pratik merdiven durumu (v={PRATIK_VERSION})",
        f"· Son basamak işareti: {st.get('basamak', 0)}",
        f"· 1 tek dosya: {'✓' if ok.get('1') else '·'}",
        f"· 2 iskelet: {'✓' if ok.get('2') else '·'}",
        f"· 3 yama: {'✓' if ok.get('3') else '·'}",
        f"· 4 doğrula: {'✓' if ok.get('4') else '·'}",
    ]
    return {"ok": True, "basamak": st.get("basamak", 0), "reply": "\n".join(lines), "state": st}


def _tek_adim(cmd: str, root: Path) -> dict[str, Any] | None:
    c = cmd.strip().lower()
    c = re.sub(r"\s+", " ", c)
    if c in ("pratik", "pratik merdiven", "pratik yardim", "pratik yardım", "kontrollu pratik"):
        return {"ok": True, "basamak": 0, "reply": _YARDIM}
    if c in ("pratik durum", "pratik status", "merdiven durum"):
        return durum(root)
    if c in ("pratik 1", "tek dosya", "tek dosya yaz", "pratik bir"):
        return basamak1_tek_dosya(root)
    if c in ("pratik 2", "iskelet", "iskelet kur", "pratik iki"):
        return basamak2_iskelet(root)
    if c in ("pratik 3", "yama", "yama uygula", "pratik uc", "pratik üç"):
        return basamak3_yama(root)
    if c in ("pratik 4", "dogrula", "doğrula", "pratik dort", "pratik dört", "raporla"):
        return basamak4_dogrula(root)
    return None


def pratik_sohbet_yaniti(msg: str) -> str | None:
    """Sohbetten yakala — modelden önce."""
    raw = re.sub(r"\s+", " ", str(msg or "")).strip()
    raw = re.sub(r"[.!?…]+$", "", raw).strip()
    if not raw or len(raw) > 200:
        return None
    # yalnız pratik niyeti
    low = raw.lower()
    if not re.match(
        r"^(pratik|tek dosya|iskelet|yama|doğrula|dogrula|kontrollu pratik|kontrollü pratik)",
        low,
    ):
        return None
    root = _root()
    # zincir: "pratik 1 sonra pratik 2"
    parcalar = [p.strip() for p in re.split(r"\s+sonra\s+|\s*,\s*", raw) if p.strip()]
    if len(parcalar) >= 2:
        notes = []
        for p in parcalar:
            hit = _tek_adim(p, root)
            if not hit:
                return None if not notes else (
                    "Zincir durdu.\n" + "\n---\n".join(notes)
                    + f"\nAnlaşılmayan: {p}"
                )
            notes.append(str(hit.get("reply") or ""))
            if not hit.get("ok") and p.lower() not in ("pratik", "pratik merdiven"):
                return "\n---\n".join(notes)
        return "\n---\n".join(notes)
    hit = _tek_adim(raw, root)
    if not hit:
        return None
    return str(hit.get("reply") or "") or None
