#!/usr/bin/env python3
"""Ana Motor duman testi — plan, retrieval, ajan (Ollama gerekmez).

Çalıştırma (ilim-assistant kökünde):
  python scripts/ana_motor_smoke.py

İsteğe bağlı canlı API:
  python scripts/ana_motor_smoke.py --live http://127.0.0.1:8777
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _ok(label: str) -> None:
    print(f"  OK  {label}")


def _fail(label: str, detail: str = "") -> None:
    msg = f"  FAIL {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def run_offline() -> int:
    from ilim_assistant.ana_motor_agent import (
        build_agent_steps,
        infer_workspace_rel_paths,
        run_agent_workspace_phase,
    )
    from ilim_assistant.ana_motor_plan import (
        maybe_clarification_reply,
        maybe_gundelik_instant_reply,
        plan_question,
        rag_top_k_for_turn,
    )
    from ilim_assistant.chat_core import local_rag_strong_enough_to_skip_web, prepare_turn
    from ilim_assistant.main_engine import run_retrieval_with_status_events

    repo = _ROOT.parent
    fails = 0

    cases = [
        ("selam nasılsın", "genel", {}, "gundelik"),
        ("Python decorator nedir", "genel", {}, "bilgi"),
        ("Osmanlı Fatih dönemi", "genel", {"bilim": True}, "bilim"),
        ("bu?", "genel", {}, None),
    ]
    from ilim_assistant.ana_motor_plan import rewrite_rag_search_query

    p_bilgi = plan_question("Nobel fizik odulu nedir", "genel", {})
    rq = rewrite_rag_search_query("Nobel fizik odulu nedir", "bilgi")
    if not rq or len(rq) < 8:
        _fail("rag_query", rq)
        fails += 1
    else:
        _ok(f"rag_query -> {rq[:48]}")

    print("=== Soru planı ===")
    for msg, mode, flags, expect in cases:
        p = plan_question(msg, mode, flags)
        if expect and p.primary != expect:
            _fail(f"plan {msg[:24]!r}", f"beklenen {expect}, gelen {p.primary}")
            fails += 1
        else:
            _ok(f"plan {msg[:32]!r} -> {p.primary}")

    clar = maybe_clarification_reply("bu?", "genel", {})
    if not clar:
        _fail("clarify", "bu? için netleştirme bekleniyordu")
        fails += 1
    else:
        _ok("clarify kısa soru")

    gund = maybe_gundelik_instant_reply(
        "Sadece sohbet — nasılsın diye sormak istedim", "genel", {}
    )
    if not gund or "İyiyim" not in gund:
        _fail("gundelik instant", gund or "boş")
        fails += 1
    else:
        _ok("gundelik: anında nasılsın yanıtı")

    print("\n=== RAG top_k (genel) ===")
    k = rag_top_k_for_turn("genel", plan_question("test", "genel", {}))
    if k < 4:
        _fail("rag_top_k genel", str(k))
        fails += 1
    else:
        _ok(f"RAG_TOP_K genel = {k}")

    print("\n=== Web / zayıf RAG ===")
    weak = local_rag_strong_enough_to_skip_web([("t", "s", 0.1)], [], archive_primary=False)
    strong = local_rag_strong_enough_to_skip_web([("t", "s", 0.5)], [], archive_primary=False)
    if weak:
        _fail("zayıf skor web kapatmasın", "True döndü")
        fails += 1
    else:
        _ok("zayif RAG: web acik kalir")
    if not strong:
        _fail("güçlü skor", "False döndü")
        fails += 1
    else:
        _ok("guclu RAG: web kapatilabilir")

    print("\n=== Retrieval (main_engine v2) ===")
    p_g = plan_question("selam", "genel", {})
    b, evs = run_retrieval_with_status_events(
        "selam", "genel", False, True, 4, p_g
    )
    if b.hits:
        _fail("gundelik retrieval", "hit beklenmiyordu")
        fails += 1
    else:
        _ok("gundelik: retrieval atlandi")

    p_b = plan_question("Nobel fizik 2024", "genel", {})
    b2, evs2 = run_retrieval_with_status_events(
        "Nobel fizik 2024", "genel", False, True, 4, p_b
    )
    if b2.suppress_main_web_search:
        _fail("bilgi web suppress", "True")
        fails += 1
    else:
        _ok("bilgi: web kapatilmaz")

    print("\n=== Workspace ajan ===")
    rels = infer_workspace_rel_paths("@@ruzgar-desktop/app.js", repo)
    if "ruzgar-desktop/app.js" not in rels:
        _fail("path infer", str(rels))
        fails += 1
    else:
        _ok(f"@@ yol -> {rels[0]}")
    ctx, step, _ = run_agent_workspace_phase(
        "@@ruzgar-desktop/app.js timeout",
        "genel",
        plan_question("app.js timeout", "genel", {"programlama": True}),
        workspace_root=str(repo),
    )
    if not ctx or not step or step.status != "done":
        _fail("workspace read", step.detail if step else "boş")
        fails += 1
    else:
        _ok(f"workspace ({len(ctx)} karakter)")

    steps = build_agent_steps(p_b, step, ["İndeks tarandı"])
    if len(steps) < 4:
        _fail("agent steps", str(len(steps)))
        fails += 1
    else:
        _ok(f"ajan adımları ({len(steps)})")

    print("\n=== prepare_turn (LLM çağrısı yok) ===")
    prep = prepare_turn(
        "selam",
        [],
        use_web=False,
        fetch_pages=0,
        coding_mode=False,
        session_wake_used=False,
        mode="genel",
        skip_ogrenme_lookup=True,
    )
    if prep is None:
        _fail("prepare_turn selam", "None")
        fails += 1
    else:
        _msg, _hits, payload, _sys, _model, direct = prep
        if direct:
            _ok("prepare_turn: dogrudan (hafiza/ozel)")
        elif payload:
            _ok("prepare_turn: LLM yuku hazir")
        else:
            _fail("prepare_turn", "boş payload")

    return fails


def run_live(base: str) -> int:
    import urllib.request

    url = base.rstrip("/") + "/api/health"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            raw = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        _fail("health", str(e))
        return 1
    import json

    j = json.loads(raw)
    if not j.get("ok"):
        _fail("health ok", raw[:200])
        return 1
    am = j.get("ana_motor") or {}
    _ok(f"API ayakta — model={am.get('ollama_chat_model')}")
    if am.get("main_only_genel_hafiza"):
        _fail("RUZGAR_MAIN_ONLY_GENEL_HAFIZA", "Genel mod LLM kapalı!")
        return 1
    _ok("main_only_genel_hafiza kapalı")
    if not am.get("question_plan_enabled"):
        _fail("question_plan", "kapalı")
        return 1
    _ok("soru planı açık")
    if not am.get("ana_motor_agent_enabled"):
        _fail("agent", "kapalı")
        return 1
    _ok("mini ajan açık")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Ana Motor smoke test")
    ap.add_argument(
        "--live",
        metavar="URL",
        help="Canlı health kontrolü (ör. http://127.0.0.1:8777)",
    )
    args = ap.parse_args()
    print("Rüzgar Ana Motor — smoke test\n")
    fails = run_offline()
    if args.live:
        print("\n=== Canlı API ===")
        fails += run_live(args.live)
    print()
    if fails:
        print(f"SONUÇ: {fails} hata")
        return 1
    print("SONUÇ: tüm kontroller geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
