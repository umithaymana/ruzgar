#!/usr/bin/env python3
"""Ana Motor duman testi — plan, retrieval, ajan (Ollama gerekmez).

Çalıştırma (ilim-assistant kökünde):
  python scripts/ana_motor_smoke.py

İsteğe bağlı canlı API:
  python scripts/ana_motor_smoke.py --live http://127.0.0.1:8777
"""

from __future__ import annotations

import argparse
import os
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

    print("\n=== Faz B — sentez / reflection / plan / havuz ===")
    from ilim_assistant.ana_motor_plan import plan_question as _plan_q
    from ilim_assistant.ana_motor_programlama_havuz import (
        persist_programlama_turn,
        programlama_havuz_enabled,
    )
    from ilim_assistant.ana_motor_reflection import (
        apply_answer_quality_pass,
        detect_source_answer_mismatch,
    )
    from ilim_assistant.ana_motor_sentez import (
        build_research_summary,
        sentez_enabled,
        should_synthesize_turn,
    )

    if not sentez_enabled():
        _fail("sentez enabled", "kapali")
        fails += 1
    else:
        _ok("sentez modulu acik")
    _hits_mix = [("osmanli kurulus", "tarih_ve_kultur/x.md", 0.55), ("1299", "indeks/y.md", 0.48)]
    _web = "Web aramasi: Osmanli devleti 1299"
    if not should_synthesize_turn(
        question_plan=_plan_q("Osmanli kim kurdu", "genel", {}),
        hits=_hits_mix,
        web_extra=_web,
        mode_norm="genel",
    ):
        _fail("sentez should_run", "True bekleniyordu")
        fails += 1
    else:
        _ok("sentez: yerel+web tetik")
    if should_synthesize_turn(
        question_plan=_plan_q("selam", "genel", {}),
        hits=[],
        web_extra="",
        mode_norm="genel",
    ):
        _fail("sentez gundelik", "False bekleniyordu")
        fails += 1
    else:
        _ok("sentez: gundelik atlanir")
    _sentez_off = build_research_summary(
        "test",
        hits=[],
        web_extra="",
        mode_norm="genel",
    )
    if _sentez_off:
        _fail("sentez bos kaynak", "bos olmali")
        fails += 1
    else:
        _ok("sentez: kaynak yoksa bos")

    _mis, _note = detect_source_answer_mismatch(
        "Osmanli 1453 yilinda kuruldu kesinlikle.",
        hits=[("1299", "tarih.md", 0.6)],
        web_was_used=False,
    )
    if not _mis or "emin" not in _note.lower():
        _fail("reflection mismatch", _note or "bos")
        fails += 1
    else:
        _ok("reflection B2: kaynak uyumsuzlugu")

    p_kisa = _plan_q("Python nedir?", "genel", {})
    if p_kisa.primary != "bilgi":
        _fail("B3 kisa bilgi plan", p_kisa.primary)
        fails += 1
    elif not p_kisa.prefer_web:
        _fail("B3 prefer_web", "False")
        fails += 1
    else:
        _ok(f"B3: kisa soru -> {p_kisa.primary} + web")

    if programlama_havuz_enabled():
        _ok("programlama havuz acik")
    else:
        _fail("programlama havuz", "kapali")
        fails += 1

    print("\n=== Super beyin modulleri ===")
    from ilim_assistant.ana_motor_kaynak import citation_directive_for_turn, format_context_blocks
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

    print("\n=== Hava vs tarih yönlendirme ===")
    from ilim_assistant.ana_motor_plan import plan_question
    from ilim_assistant.chat_core import _tarih_intent
    from ilim_assistant.tarih_fast import iter_tarih_hafiza_reply
    from ilim_assistant.weather_live import maybe_weather_instant_reply

    wx_msg = "istanbulda bugün hava nasıl olacak"
    wx_plan = plan_question(wx_msg, "genel", {})
    if wx_plan.primary != "hava":
        _fail("weather_plan", f"primary={wx_plan.primary}")
        fails += 1
    else:
        _ok(f"hava planı: {wx_plan.primary}")
    if _tarih_intent(wx_msg):
        _fail("weather_tarih_intent", "istanbul+hava tarih sayılmamalı")
        fails += 1
    else:
        _ok("hava sorusu tarih niyetine düşmüyor")
    if iter_tarih_hafiza_reply(wx_msg, [], mode_norm="genel") is not None:
        _fail("weather_tarih_fast", "tarih_fast atlanmalıydı")
        fails += 1
    else:
        _ok("tarih_fast hava sorusunu atlıyor")

    print("\n=== Tarih bilgi — Ana Motor yolu (padisah listesi) ===")
    from ilim_assistant.tarih_fast import (
        is_tarih_fast_teach_fallback,
        should_defer_tarih_fast_to_ana_motor,
    )

    pad_msg = "Osmanli padisahlari kimlerdir"
    if not should_defer_tarih_fast_to_ana_motor(pad_msg, mode_norm="genel"):
        _fail("tarih_defer_padisah", "True bekleniyordu")
        fails += 1
    else:
        _ok("padisah listesi: tarih_fast atlanir")
    if iter_tarih_hafiza_reply(pad_msg, [], mode_norm="genel") is not None:
        _fail("tarih_fast_padisah", "None bekleniyordu")
        fails += 1
    else:
        _ok("padisah: iter_tarih None (Ana Motor)")
    if not is_tarih_fast_teach_fallback(
        "Umit abi, yerel tarih kaydi var ama net ozet cikaramadim. Ogretir misin?"
    ):
        _fail("teach_fallback_detect", "algilanmadi")
        fails += 1
    else:
        _ok("teach fallback algisi")

    print("\n=== Faz C — arastirma raporu / guncellik / bilgi zinciri ===")
    from ilim_assistant.ana_motor_plan import plan_question as _plan_q
    from ilim_assistant.ana_motor_arastirma import (
        arastirma_report_enabled,
        build_unified_research_report,
    )
    from ilim_assistant.ana_motor_guncellik import (
        append_reply_freshness_stamp,
        freshness_stamp_enabled,
        web_scan_stamp_line,
    )
    from ilim_assistant.llm_brain import select_brain_chain

    if not arastirma_report_enabled():
        _fail("arastirma enabled", "kapali")
        fails += 1
    else:
        _ok("arastirma raporu acik")
    _hits = [("osmanli kurulus", "tarih/x.md", 0.55)]
    _web = "**Guncellik:** test\n=== Web aramasi ===\n1. test"
    rap = build_unified_research_report(
        "Osmanli padisahlari kimlerdir",
        hits=_hits,
        web_extra=_web,
        question_plan=_plan_q("Osmanli padisahlari kimlerdir", "genel", {}),
        mode_norm="genel",
    )
    if not rap or "[Y1]" not in rap or "BİRLEŞİK ARAŞTIRMA" not in rap:
        _fail("arastirma rapor", rap[:80] if rap else "bos")
        fails += 1
    else:
        _ok("birlesik arastirma raporu [Y1]")
    if not freshness_stamp_enabled() or "Güncellik:" not in web_scan_stamp_line():
        _fail("web stamp", web_scan_stamp_line())
        fails += 1
    else:
        _ok("web guncellik damgasi")
    ref_g = append_reply_freshness_stamp("Cevap.", web_was_used=True, user_message="bugun haber")
    if "Güncellik:" not in ref_g:
        _fail("reply freshness", ref_g)
        fails += 1
    else:
        _ok("cevap guncellik damgasi")
    sel = select_brain_chain(
        message="Python nedir",
        mode_norm="genel",
        question_plan=_plan_q("Python nedir", "genel", {}),
    )
    if not sel.chain or sel.chain[0].profile_id not in ("gemini", "groq", "denge", "hizli"):
        _fail("bilgi brain", [e.profile_id for e in sel.chain])
        fails += 1
    else:
        _ok(f"bilgi zinciri: {sel.chain[0].profile_id}")

    print("\n=== Faz D — bilim derin / denge70 / otonom debug ===")
    from ilim_assistant.ana_motor_bilim_derin import (
        apply_bilim_derin_rag_top_k,
        bilim_derin_enabled,
        is_bilim_derin_turn,
    )
    from ilim_assistant.ana_motor_otonom_debug import (
        detect_otonom_debug_intent,
        should_delegate_genel_debug,
        should_enable_code_debug_loop,
    )
    from ilim_assistant.llm_brain import _normalize_forced_profile, all_profiles

    p_bilim = _plan_q("Osmanli Fatih donemi detayli acikla", "genel", {"bilim": True})
    if not bilim_derin_enabled():
        _fail("bilim_derin enabled", "kapali")
        fails += 1
    else:
        _ok("bilim derin acik")
    bilim_msg = "Osmanli Fatih donemi detayli acikla"
    if not is_bilim_derin_turn(p_bilim, bilim_msg, "genel"):
        _fail("bilim_derin_turn", p_bilim.primary)
        fails += 1
    else:
        _ok("bilim derin tur algilandi")
    k_deep = apply_bilim_derin_rag_top_k(4, p_bilim, bilim_msg, "genel")
    if k_deep < 8:
        _fail("bilim_derin_rag_k", str(k_deep))
        fails += 1
    else:
        _ok(f"bilim derin rag_top_k={k_deep}")
    profs = all_profiles()
    if "denge70" not in profs:
        _fail("denge70 profile", list(profs.keys()))
        fails += 1
    else:
        _ok(f"denge70 profil: {profs['denge70'].model}")
    if _normalize_forced_profile("denge-70b") != "denge70":
        _fail("denge70 alias", "denge-70b")
        fails += 1
    else:
        _ok("denge-70b alias -> denge70")
    sel70 = select_brain_chain(
        message=bilim_msg,
        mode_norm="genel",
        question_plan=p_bilim,
    )
    chain_ids = [e.profile_id for e in sel70.chain]
    if "denge70" not in chain_ids:
        _fail("bilim derin 70b zincir", chain_ids)
        fails += 1
    else:
        _ok(f"bilim derin zincirde denge70: {chain_ids[:5]}")
    tb_msg = 'Traceback (most recent call last):\n  File "app.py", line 42'
    if not detect_otonom_debug_intent(tb_msg):
        _fail("otonom_debug traceback", "")
        fails += 1
    else:
        _ok("traceback -> otonom debug")
    if not should_delegate_genel_debug("pytest kirmizi duzelt", "genel"):
        _fail("delegate debug", "")
        fails += 1
    else:
        _ok("genel -> programlama debug delege")
    if not should_enable_code_debug_loop(tb_msg, "programlama"):
        _fail("debug loop", "")
        fails += 1
    else:
        _ok("programlama debug dongusu")

    print("\n=== Selam — pytest / kod modu sızıntısı ===")
    from ilim_assistant.motorlar.programlama_faz10 import (
        extract_user_intent_message,
        wants_project_verify_cmd,
    )
    from ilim_assistant.motorlar.programlama_faz92 import build_task_plan, render_plan_directive
    from ilim_assistant.ruzgar_dogal_sohbet_faz91 import is_pure_short_greeting

    for greet in ("merhaba", "selam", "selamünaleyküm"):
        if not is_pure_short_greeting(greet):
            _fail("pure_greeting", greet)
            fails += 1
        else:
            _ok(f"kısa selam: {greet}")
        plan = render_plan_directive(build_task_plan(greet))
        aug = f"{plan}\n\n[Kullanici istegi]\n{greet}"
        if wants_project_verify_cmd(aug):
            _fail("verify_augmented", greet)
            fails += 1
        else:
            _ok(f"Faz92 doğrula sızıntısı yok: {greet}")
        if extract_user_intent_message(aug) != greet:
            _fail("extract_user_intent", greet)
            fails += 1
    try:
        from desktop_server import ChatRequest, iter_chat_turn_events

        req = ChatRequest(
            message="merhaba",
            mode="genel",
            coding_mode=True,
            workspace_root=os.environ.get("LOCAL_TOOLS_ROOT") or str(_ROOT.parent),
            programlama_active_file="projects/smoke-parity-crud-54104/app/__init__.py",
        )
        out = ""
        for ev in iter_chat_turn_events(req):
            if ev.get("type") == "token":
                out += ev.get("text", "")
            elif ev.get("type") == "done":
                out = ev.get("full_reply") or out
        if "doğrulama" in out.lower() and "pytest" in out.lower():
            _fail("coding_merhaba_pytest", out[:120])
            fails += 1
        else:
            _ok("Kod modu + merhaba: pytest yok")
    except Exception as exc:
        _fail("coding_merhaba_turn", str(exc)[:120])
        fails += 1

    print("\n=== Egitim — bilgi sorusu anlik atlama (Faz B) ===")
    from ilim_assistant.ruzgar_egitim import (
        maybe_egitim_learned_reply,
        taught_reply_for_message,
    )

    if taught_reply_for_message("osman bey kimdir"):
        if maybe_egitim_learned_reply("osman bey kimdir") is not None:
            _fail("egitim_bilgi_instant", "kimdir sorusu anlik donmemeli")
            fails += 1
        else:
            _ok("kimdir: egitim instant atlandi (Ana Motor yolu)")
    else:
        _ok("kimdir: ogretilmis kayit yok (atlanacak test)")

    print("\n=== Eğitim — kimlik sorusu / öğretim onayı sızıntısı ===")
    from ilim_assistant.ruzgar_egitim import (
        clear_pending,
        set_pending,
        try_consume_egitim_command,
    )
    from ilim_assistant.ruzgar_owner_lock import (
        is_owner_identity_question,
        maybe_owner_instant_reply,
    )
    from ilim_assistant.ruzgar_umed_kurallari import SAVED_TEACH

    if not is_owner_identity_question("ben kimim?"):
        _fail("owner_identity", "ben kimim? tanınmadı")
        fails += 1
    else:
        _ok("ben kimim? kimlik sorusu")
    id_reply = maybe_owner_instant_reply("ben kimim?", "genel")
    if not id_reply or "Ümit" not in id_reply:
        _fail("owner_identity_reply", id_reply or "")
        fails += 1
    else:
        _ok("kimlik anında yanıt")
    set_pending("await_teaching", "selam")
    steal = try_consume_egitim_command("ben kimim?", [])
    if steal == SAVED_TEACH:
        _fail("egitim_pending_steal", "ben kimim? öğretim cevabı sanıldı")
        fails += 1
    else:
        _ok("bekleyen öğretimde bilgi sorusu çalınmıyor")
    clear_pending()
    if taught_reply_for_message("ben kimim?") == SAVED_TEACH:
        _fail("egitim_lookup_saved", SAVED_TEACH)
        fails += 1
    else:
        _ok("hafızadan öğretim onayı dönmüyor")

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
    import json
    import time
    import urllib.request

    fails = 0
    url = base.rstrip("/") + "/api/health"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            raw = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        _fail("health", str(e))
        return 1

    j = json.loads(raw)
    if not j.get("ok"):
        _fail("health ok", raw[:200])
        return 1
    am = j.get("ana_motor") or {}
    _ok(f"API ayakta — model={am.get('ollama_chat_model')}")
    if am.get("main_only_genel_hafiza"):
        _fail("RUZGAR_MAIN_ONLY_GENEL_HAFIZA", "Genel mod LLM kapalı!")
        fails += 1
    else:
        _ok("main_only_genel_hafiza kapalı")
    if not am.get("question_plan_enabled"):
        _fail("question_plan", "kapalı")
        fails += 1
    else:
        _ok("soru planı açık")
    if not am.get("ana_motor_agent_enabled"):
        _fail("agent", "kapalı")
        fails += 1
    else:
        _ok("mini ajan açık")
    if not am.get("ana_motor_arastirma"):
        _fail("faz_c arastirma", "kapalı")
        fails += 1
    else:
        _ok("Faz C arastirma raporu acik")
    if not am.get("web_freshness_stamp"):
        _fail("faz_c freshness", "kapalı")
        fails += 1
    else:
        _ok("Faz C web guncellik damgasi acik")
    if not am.get("bilim_derin"):
        _fail("faz_d bilim_derin", "kapalı")
        fails += 1
    else:
        _ok("Faz D bilim derin acik")
    if not am.get("otonom_debug_bridge"):
        _fail("faz_d otonom_debug", "kapalı")
        fails += 1
    else:
        _ok("Faz D otonom debug koprusu acik")
    if not am.get("brain_denge70_model"):
        _fail("faz_d denge70", "model yok")
        fails += 1
    else:
        _ok(f"denge70 model: {am.get('brain_denge70_model')}")

    t0 = time.monotonic()
    chat_url = base.rstrip("/") + "/api/chat/full"
    body = json.dumps(
        {
            "message": "Python nedir?",
            "mode": "genel",
            "coding_mode": False,
            "use_web": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    try:
        req = urllib.request.Request(
            chat_url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            cj = json.loads(r.read().decode("utf-8", errors="replace"))
        elapsed = time.monotonic() - t0
        if not cj.get("ok"):
            _fail("live bilgi tur", str(cj.get("error") or "")[:120])
            fails += 1
        else:
            _ok(f"canli bilgi turu {elapsed:.1f}s")
            try:
                slo = float(os.environ.get("RUZGAR_LIVE_BILGI_SLO_SEC", "75"))
            except ValueError:
                slo = 75.0
            if elapsed > slo:
                _fail("latency SLO", f"{elapsed:.1f}s > {slo}s")
                fails += 1
            else:
                _ok(f"latency SLO <= {slo:.0f}s")
    except Exception as e:
        _fail("live bilgi tur", str(e)[:120])
        fails += 1

    return fails


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
