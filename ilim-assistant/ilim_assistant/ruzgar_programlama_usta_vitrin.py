# Created by Ümit & Gökçenur
"""
Motor F — usta/atölye vitrin ölçümü (Adım 6.F).

Sözden ürün omurgası: brifing · şablon · güvenlik kapısı · route yüzeyi.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

VERSION = "programlama-usta-vitrin-v1-2026-11-09"


def enabled() -> bool:
    return os.environ.get("RUZGAR_PROGRAMLAMA_USTA_VITRIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def measure_vitrin() -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    ok_n = 0

    # 1) brifing
    try:
        from ilim_assistant.motorlar.programlama_faz2 import build_startup_briefing

        br = build_startup_briefing(None)
        good = bool(br) and (br.get("ok") is not False) and len(str(br)) > 40
        if good:
            ok_n += 1
        cards.append({"ok": good, "id": "briefing", "keys": list(br.keys())[:8] if isinstance(br, dict) else []})
    except Exception as e:
        cards.append({"ok": False, "id": "briefing", "error": type(e).__name__})

    # 2) şablon listesi
    try:
        from ilim_assistant.motorlar.programlama_faz6 import list_templates

        tpls = list_templates() or []
        good = len(tpls) >= 1
        if good:
            ok_n += 1
        cards.append({"ok": good, "id": "templates", "n": len(tpls)})
    except Exception as e:
        cards.append({"ok": False, "id": "templates", "error": type(e).__name__})

    # 3) güvenlik denetimi yüzeyi
    try:
        from ilim_assistant.motorlar.programlama_faz4 import run_security_audit

        au = run_security_audit(None)
        good = isinstance(au, dict) and ("ok" in au or "checks" in au or "findings" in au)
        if good:
            ok_n += 1
        cards.append({"ok": good, "id": "security_audit", "keys": list(au.keys())[:8] if isinstance(au, dict) else []})
    except Exception as e:
        cards.append({"ok": False, "id": "security_audit", "error": type(e).__name__})

    # 4) yazma kapısı (onaylı güç)
    try:
        from ilim_assistant.motorlar.programlama_faz3 import programlama_write_allowed

        root = Path(__file__).resolve().parents[1]
        allow_ok, _msg_ok = programlama_write_allowed(root, "workspace/projects/demo/main.py")
        deny_ok, _msg_deny = programlama_write_allowed(root, "../etc/passwd")
        # güvenli yol kabul / traversal red
        good = bool(allow_ok) and (not bool(deny_ok))
        if good:
            ok_n += 1
        cards.append(
            {
                "ok": good,
                "id": "write_gate",
                "allow_safe": bool(allow_ok),
                "deny_traversal": not bool(deny_ok),
            }
        )
    except Exception as e:
        cards.append({"ok": False, "id": "write_gate", "error": type(e).__name__})

    # 5) scaffold komut ayrıştırma
    try:
        from ilim_assistant.motorlar.programlama_faz6 import parse_scaffold_command

        parsed = parse_scaffold_command("şablon oluştur: fastapi_api demo_proje")
        good = parsed is not None
        if good:
            ok_n += 1
        cards.append({"ok": good, "id": "scaffold_parse", "parsed": list(parsed) if parsed else None})
    except Exception as e:
        cards.append({"ok": False, "id": "scaffold_parse", "error": type(e).__name__})

    total = 5
    score = round(100.0 * ok_n / total, 1) if total else 0.0
    return {
        "ok": ok_n == total,
        "version": VERSION,
        "enabled": enabled(),
        "total": total,
        "hit": ok_n,
        "miss": total - ok_n,
        "score_pct": score,
        "cards": cards,
        "label_tr": "Programlama usta vitrini",
    }


def atolye_mutlu_yol() -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    vit = measure_vitrin()
    steps.append(
        {
            "id": "usta_vitrin",
            "ok": bool(vit.get("ok")),
            "detail": f"score={vit.get('score_pct')}% hit={vit.get('hit')}/{vit.get('total')}",
        }
    )

    env_ok = False
    try:
        from ilim_assistant.motorlar.programlama_faz3 import run_windows_env_scan

        tests = run_windows_env_scan(None) or []
        # en az bir test satırı dönsün
        env_ok = isinstance(tests, list) and len(tests) >= 1
        detail = f"tests={len(tests)}"
    except Exception as e:
        detail = type(e).__name__
    steps.append({"id": "environment", "ok": env_ok, "detail": detail})

    session_ok = False
    try:
        from ilim_assistant.motorlar.programlama_faz5 import build_session_api_payload

        ses = build_session_api_payload(None)
        session_ok = isinstance(ses, dict) and len(ses) >= 1
        detail = f"keys={list(ses.keys())[:6]}"
    except Exception as e:
        detail = type(e).__name__
    steps.append({"id": "session", "ok": session_ok, "detail": detail})

    routes_ok = False
    missing: list[str] = []
    try:
        ds = Path(__file__).resolve().parent.parent / "desktop_server.py"
        text = ds.read_text(encoding="utf-8") if ds.is_file() else ""
        core = [
            "/api/programlama/briefing",
            "/api/programlama/templates",
            "/api/programlama/security-audit",
            "/api/programlama/scaffold",
            "/api/programlama/usta-vitrin",
        ]
        missing = [p for p in core if p not in text]
        routes_ok = len(missing) == 0
    except Exception as e:
        missing = [type(e).__name__]
    steps.append(
        {
            "id": "atolye_routes",
            "ok": routes_ok,
            "detail": "ok" if routes_ok else f"eksik={missing}",
        }
    )

    all_ok = all(bool(s.get("ok")) for s in steps)
    return {
        "ok": all_ok,
        "version": VERSION,
        "steps": steps,
        "vitrin": vit,
        "label_tr": "Programlama atölye mutlu yolu",
    }


def public_status() -> dict[str, Any]:
    if not enabled():
        return {"enabled": False, "version": VERSION}
    vit = measure_vitrin()
    return {
        "enabled": True,
        "version": VERSION,
        "vitrin_ok": bool(vit.get("ok")),
        "vitrin_score_pct": vit.get("score_pct"),
        "vitrin_hit": vit.get("hit"),
        "vitrin_total": vit.get("total"),
    }
