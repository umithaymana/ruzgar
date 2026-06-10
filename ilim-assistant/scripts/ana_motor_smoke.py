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
        looks_like_encyclopedic_fact_question,
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
        ("Osmanlı devletini kim kurdu?", "genel", {}, "bilgi"),
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

    print("=== Faz 11 — idrak yüzey ön-işlem ===")
    from ilim_assistant.idrak_on_islem import pretreat_user_turn

    pt = pretreat_user_turn("birsey söyle", [])
    if "bir şey" not in pt.text:
        _fail("idrak_pretreat birşey", pt.text)
        fails += 1
    else:
        _ok(f"idrak_pretreat -> {pt.text!r}")
    pt2 = pretreat_user_turn(
        "devam et",
        [{"role": "assistant", "content": "Faz 11 planı"}],
    )
    if not pt2.continuation:
        _fail("idrak_continuation", pt2.text)
        fails += 1
    else:
        _ok("idrak_continuation -> history_context")

    print("=== Faz 14/16 — self-test + görev çekirdeği ===")
    from ilim_assistant.ruzgar_selftest import run_self_tests
    from ilim_assistant.gorev_yoneticisi import (
        create_task,
        delete_task,
        list_tasks,
        update_task,
    )

    st = run_self_tests()
    if not st.get("ok"):
        _fail("self_test", str(st.get("tests"))[:200])
        fails += 1
    else:
        _ok("self_test çekirdeği")
    task = create_task("smoke-test görev")
    if not update_task(int(task["id"]), "done"):
        _fail("task_manager", str(task))
        fails += 1
    elif not list_tasks(1):
        _fail("task_manager list", "boş")
        fails += 1
    else:
        _ok("task_manager create/update/list")
    delete_task(int(task["id"]))

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
    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import dogal_sohbet_enabled

        _dogal_on = dogal_sohbet_enabled()
    except Exception:
        _dogal_on = False
    if _dogal_on:
        if gund is not None:
            _fail("gundelik instant (Faz 91)", "şablon kapalı olmalıydı")
            fails += 1
        else:
            _ok("gundelik: Faz 91 — şablon yok, LLM yolu")
    elif not gund or "İyiyim" not in gund:
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

    msg_os = "Osmanlı devletini kim kurdu?"
    if not looks_like_encyclopedic_fact_question(msg_os):
        _fail("encyclopedic detector", "True bekleniyordu")
        fails += 1
    else:
        _ok("encyclopedic detector (kim kurdu)")
    p_os = plan_question(msg_os, "genel", {})
    b_os, evs_os = run_retrieval_with_status_events(
        msg_os, "genel", False, True, 4, p_os
    )
    texts_os = " ".join(str(e.get("text") or "") for e in evs_os)
    if "Mektubat" in texts_os or "mektubat" in texts_os.lower():
        _fail("Faz9 retrieval osmanli", "ağır arşiv (Mektubat) beklenmiyordu")
        fails += 1
    else:
        _ok("Faz9 retrieval: mektubat yok (hizli encyclopedic turu)")

    if "birleştir" not in texts_os.lower() and "ansiklopedik" not in texts_os.lower():
        _fail("encyclopedic merge status", texts_os[:120])
        fails += 1
    else:
        _ok("encyclopedic: hizli merge status")

    print("\n=== Süper beyin modülleri ===")
    from ilim_assistant.ana_motor_kaynak import citation_directive_for_turn, format_context_blocks
    from ilim_assistant.ana_motor_reflection import apply_answer_quality_pass
    from ilim_assistant.ana_motor_super import append_super_brain_directive

    bl = format_context_blocks([("metin", "kaynak.md", 0.55)])
    if not bl or "[K1]" not in bl[0][0]:
        _fail("format_context_blocks", str(bl))
        fails += 1
    else:
        _ok("numarali kaynak [K1]")
    cit = citation_directive_for_turn(source_count=1, archive_primary=False, web_present=False)
    if "Güven:" not in cit:
        _fail("citation_directive", cit[:80])
        fails += 1
    else:
        _ok("kaynak talimati + Guven")
    sup = append_super_brain_directive("SORU:\ntest", question_plan=p_os, mode_norm="genel")
    if "SÜPER BEYİN" not in sup:
        _fail("super_brain_directive", sup[:80])
        fails += 1
    else:
        _ok("super brain talimati")
    ref = apply_answer_quality_pass("Kisa.", msg_os, hits=[], question_plan=p_os)
    if "Güven:" not in ref:
        _fail("reflection guven", ref)
        fails += 1
    else:
        _ok("reflection: Guven satiri eklendi")

    msg_ilk = "İlk Osmanlı padişahı kimdir?"
    if not looks_like_encyclopedic_fact_question(msg_ilk):
        _fail("encyclopedic detector ilk padişah", "True bekleniyordu")
        fails += 1
    else:
        _ok("encyclopedic detector (ilk padişah kimdir)")

    prep_os = prepare_turn(
        msg_os,
        [],
        use_web=False,
        fetch_pages=0,
        coding_mode=False,
        session_wake_used=False,
        mode="genel",
        skip_ogrenme_lookup=True,
        reuse_main_engine_bundle=b_os,
        question_plan=p_os,
    )
    if prep_os is None:
        _fail("prepare_turn Faz9 tarih+bundle", "None")
        fails += 1
    else:
        _ok("prepare_turn: prefetch bundle korundu (tarih çift tarama yok)")

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

    print("\n=== Faz 92 — Ana Motor ajan döngüsü ===")
    from ilim_assistant.ana_motor_agent_loop import (
        agent_loop_enabled,
        should_run_ana_motor_agent_loop,
    )

    if not agent_loop_enabled():
        _fail("agent_loop enabled", "kapalı")
        fails += 1
    else:
        _ok("agent_loop açık")
    p_patch = plan_question("README dosyasına not ekle", "genel", {"programlama": True})
    if should_run_ana_motor_agent_loop(
        "ilim-assistant/README.md dosyasına kısa not ekle",
        "genel",
        p_patch,
        workspace_root=str(repo),
    ):
        _ok("agent_loop: dosya işlemi algılandı")
    else:
        _fail("agent_loop dosya", "True bekleniyordu")
        fails += 1
    if not should_run_ana_motor_agent_loop(
        "Osmanlı padişahı kimdir",
        "genel",
        plan_question("Osmanlı padişahı kimdir", "genel", {}),
    ):
        _ok("agent_loop: bilgi sorusu atlandı")
    else:
        _fail("agent_loop bilgi", "False bekleniyordu")
        fails += 1

    print("\n=== Faz 93 — checkpoint ===")
    from ilim_assistant.ana_motor_checkpoint import (
        clear_checkpoint,
        is_resume_message,
        load_checkpoint,
        save_checkpoint,
    )

    cp = save_checkpoint(
        str(repo),
        turn_index=1,
        last_user="test görev",
        last_reply="@@write test",
        plan_primary="islem",
        agent_phase="planning",
    )
    if cp and load_checkpoint(str(repo)) and is_resume_message("devam et"):
        _ok("checkpoint kaydet/yükle")
    else:
        _fail("checkpoint", "kayıt okunamadı")
        fails += 1
    clear_checkpoint(str(repo))

    print("\n=== Faz 94 — routing KPI ===")
    from ilim_assistant.ana_motor_routing_kpi import collect_routing_kpi

    kpi = collect_routing_kpi()
    rate = kpi.pass_rate_pct
    print(f"  Routing: {kpi.passed}/{kpi.total} ({rate:.1f}%) hedef >=90%")
    for line in kpi.failed[:6]:
        print(f"    · {line}")
    if kpi.meets_target:
        _ok(f"routing KPI >= {kpi.pass_rate_pct:.0f}%")
    else:
        _fail("routing KPI", f"{rate:.1f}% < 90%")
        fails += 1

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
