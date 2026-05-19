# Created by Umit & Gokcenur
"""Faz 14 — Rüzgar kendi kendini kontrol etsin."""

from __future__ import annotations

from typing import Any


def run_self_tests() -> dict[str, Any]:
    tests: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        tests.append({"name": name, "ok": bool(ok), "detail": detail})

    try:
        from ilim_assistant.idrak_on_islem import pretreat_user_turn

        pt = pretreat_user_turn("birsey soyle", [])
        add("idrak_pretreat", "bir şey" in pt.text, pt.text)
    except Exception as exc:
        add("idrak_pretreat", False, str(exc))

    try:
        from ilim_assistant.chat_core import _NO_RAG_MODES

        add(
            "programlama_no_rag_mode",
            "programlama" in _NO_RAG_MODES,
            str(sorted(_NO_RAG_MODES)),
        )
    except Exception as exc:
        add("programlama_no_rag_mode", False, str(exc))

    try:
        from ilim_assistant.llm_gemini import gemini_configured

        configured = gemini_configured()
        add(
            "gemini_configured",
            configured,
            "configured" if configured else "api key yok",
        )
    except Exception as exc:
        add("gemini_configured", False, str(exc))

    try:
        from ilim_assistant.main_engine import run_retrieval_with_status_events

        _, evs = run_retrieval_with_status_events(
            "selam",
            "programlama",
            weather_q=False,
            ilim_rag=True,
            rag_top_k=2,
        )
        heavy = any("bilgi + arşiv" in str(e.get("text") or "") for e in evs)
        add("programlama_retrieval_skip", not heavy, f"events={len(evs)}")
    except Exception as exc:
        add("programlama_retrieval_skip", False, str(exc))

    try:
        from ilim_assistant.dinamit_hatirlatici import init_hatirlatici_db
        from ilim_assistant.gorev_yoneticisi import init_tasks_db

        init_hatirlatici_db()
        init_tasks_db()
        add("sqlite_aux_dbs", True, "hatırlatıcı + görev DB hazır")
    except Exception as exc:
        add("sqlite_aux_dbs", False, str(exc))

    ok = all(t["ok"] for t in tests if t["name"] != "gemini_configured")
    return {"ok": ok, "tests": tests}
