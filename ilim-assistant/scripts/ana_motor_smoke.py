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

    print("\n=== Faz E2 — patch onay + nebula kart ===")
    from ilim_assistant.ana_motor_arastirma import (
        build_research_card_payload,
        classify_hit_bucket,
    )
    from ilim_assistant.ana_motor_patch_bridge import (
        build_patch_approval_card,
        patch_approval_bridge_enabled,
        should_force_patch_staging,
    )

    if not patch_approval_bridge_enabled():
        _fail("patch_bridge", "kapali")
        fails += 1
    else:
        _ok("patch onay koprusu acik")
    if not should_force_patch_staging(delegated_from_genel=True):
        _fail("force_stage", "delege")
        fails += 1
    else:
        _ok("delege -> zorunlu staging")
    card = build_patch_approval_card(
        {
            "action": "staged",
            "count": 2,
            "items": [{"path": "a.py"}, {"path": "b.py"}],
            "counts": {"pending": 2},
            "approval_required": True,
        }
    )
    if not card.get("has_pending") or card.get("count") != 2:
        _fail("patch_card", str(card))
        fails += 1
    else:
        _ok("patch onay karti")
    if classify_hit_bucket("knowledge/nebula/tarih/x.md") != "nebula":
        _fail("bucket_nebula", "")
        fails += 1
    else:
        _ok("nebula bucket")
    if classify_hit_bucket("knowledge/TARIH_VE_KULTUR/x.md") != "tarih":
        _fail("bucket_tarih", "")
        fails += 1
    else:
        _ok("tarih bucket")
    rc = build_research_card_payload(
        "Osmanli padisahlari",
        hits=[("osman bey kurucu", "knowledge/nebula/t/x.md", 0.6), ("padisah", "knowledge/TARIH_VE_KULTUR/y.md", 0.5)],
        web_extra="",
        question_plan=plan_question("Osmanli padisahlari", "genel", {}),
        mode_norm="genel",
    )
    if not rc.get("ok") or rc.get("totals", {}).get("nebula", 0) < 1:
        _fail("research_card", str(rc.get("totals")))
        fails += 1
    else:
        _ok(f"arastirma karti nebula={rc['totals'].get('nebula')}")

    print("\n=== Faz E — denge70 hazirlik / canli retrieval / progress ===")
    from ilim_assistant.llm_brain import denge70_readiness, denge70_ready_for_chain
    from ilim_assistant.ana_motor_progress import enrich_status_text, progress_enabled
    from ilim_assistant.stream_orchestra import iter_main_engine_retrieval_stream

    p_bilim_e = plan_question(
        "Osmanli Fatih donemi detayli acikla", "genel", {"bilim": True}
    )
    d70 = denge70_readiness()
    if not d70.get("model"):
        _fail("denge70_readiness model", str(d70))
        fails += 1
    else:
        _ok(f"denge70 readiness model={d70.get('model')} ready={d70.get('ready')}")
    if d70.get("ready") and not denge70_ready_for_chain():
        _fail("denge70_ready_for_chain", "True bekleniyordu")
        fails += 1
    else:
        _ok("denge70 zincir kapisi tutarli")
    if progress_enabled():
        enriched = enrich_status_text("Indeks taranıyor", phase="bilim_derin")
        if "sn geçti" not in enriched and "sn / ~" not in enriched:
            _fail("progress_eta", enriched)
            fails += 1
        else:
            _ok("progress ETA metni")
    else:
        _ok("progress ETA kapali (env)")
    stream_evs = []
    for item in iter_main_engine_retrieval_stream(
        "Osmanli Fatih donemi detayli acikla",
        [],
        "genel",
        question_plan=p_bilim_e,
    ):
        if item.get("type") == "status":
            stream_evs.append(item)
    if not any(e.get("phase") == "bilim_derin" for e in stream_evs):
        _fail("bilim_derin stream status", [e.get("phase") for e in stream_evs])
        fails += 1
    else:
        _ok("canli retrieval bilim_derin status")

    print("\n=== Faz F — dosya ingest / nebula oneri / kaynak matrisi ===")
    from ilim_assistant.ana_motor_dosya_ingest import (
        ingest_enabled,
        save_upload_bytes,
        search_upload_context,
    )
    from ilim_assistant.ana_motor_kaynak_matrisi import (
        classify_retrieval_profile,
        matrix_enabled,
        retrieve_encyclopedic_matrix,
    )
    from ilim_assistant.ana_motor_nebula_oneri import (
        build_nebula_oneri_card,
        oneri_enabled,
        suggest_nebula_collection,
    )
    from ilim_assistant.rag_store import search_nebula_hafiza, search_tdk_hafiza

    if not ingest_enabled():
        _fail("upload_ingest", "kapali")
        fails += 1
    else:
        _ok("dosya ingest acik")
    up = save_upload_bytes(
        b"# Test\n\nOsmanli devleti 1299 yilinda kuruldu.\n",
        "test_faz_f.md",
    )
    if not up.get("ok") or not up.get("upload_id"):
        _fail("upload_save", str(up))
        fails += 1
    else:
        _ok(f"upload kayit id={up['upload_id']}")
        uh = search_upload_context("Osmanli kurulus", [up["upload_id"]], top_k=2)
        if not uh:
            _fail("upload_search", "hit yok")
            fails += 1
        else:
            _ok("upload baglam aramasi")

    if not matrix_enabled():
        _fail("kaynak_matris", "kapali")
        fails += 1
    else:
        _ok("kaynak matrisi acik")
    prof = classify_retrieval_profile("hayalet kelimesinin anlami nedir", "dilbilgisi")
    if prof != "tdk":
        _fail("matris profil tdk", prof)
        fails += 1
    else:
        _ok("matris: dilbilgisi -> tdk")
    prof_t = classify_retrieval_profile("Osmanli padisahlari kimlerdir", "bilgi")
    if prof_t != "tarih":
        _fail("matris profil tarih", prof_t)
        fails += 1
    else:
        _ok("matris: tarih profili")
    try:
        _ = search_tdk_hafiza("test", top_k=1)
        _ = search_nebula_hafiza("test", top_k=1)
        _ok("tdk/nebula alt arama fonksiyonlari")
    except Exception as e:
        _fail("tdk/nebula search", str(e)[:80])
        fails += 1
    _mh, _mp = retrieve_encyclopedic_matrix(
        "Osmanli padisahlari kimlerdir", primary="bilgi", k_ar=2, k_ix=3
    )
    if not isinstance(_mh, list):
        _fail("matris retrieve", type(_mh).__name__)
        fails += 1
    else:
        _ok(f"matris retrieve profil={_mp} hit={len(_mh)}")

    if not oneri_enabled():
        _fail("nebula_oneri", "kapali")
        fails += 1
    else:
        _ok("nebula oneri acik")
    sug = suggest_nebula_collection(
        "cok nadir bir konu hakkinda bilgi",
        hits=[],
        guven="düşük",
        web_was_used=False,
    )
    if not sug or not sug.get("collection"):
        _fail("nebula_oneri_sug", str(sug))
        fails += 1
    else:
        _ok(f"nebula oneri koleksiyon={sug.get('collection')}")
    _low_reply = "Kisa cevap.\n\n**Güven: düşük** — otomatik kalite geçidi (kaynak sayısı: 0)."
    noc = build_nebula_oneri_card(
        _low_reply,
        "cok nadir konu nedir",
        hits=[],
        web_was_used=False,
    )
    if not noc or not noc.get("ok"):
        _fail("nebula_oneri_card", str(noc))
        fails += 1
    else:
        _ok("nebula oneri karti")

    print("\n=== Faz G — oturum paketi / nebula apply ===")
    from ilim_assistant.ana_motor_dosya_ingest import (
        resolve_upload_ids,
        session_enabled,
    )
    from ilim_assistant.ana_motor_nebula_apply import (
        apply_nebula_oneri,
        nebula_apply_enabled,
    )

    if not session_enabled():
        _fail("upload_session", "kapali")
        fails += 1
    else:
        _ok("upload oturum paketi acik")
    up_a = save_upload_bytes(b"# A\n\nOsmanli 1299.\n", "a.md")
    up_b = save_upload_bytes(
        b"# B\n\nFatih Istanbul.\n",
        "b.md",
        session_id=up_a.get("session_id"),
    )
    if not up_a.get("session_id") or up_a.get("session_id") != up_b.get("session_id"):
        _fail("session_id", f"{up_a.get('session_id')} vs {up_b.get('session_id')}")
        fails += 1
    else:
        _ok(f"oturum 2 dosya sid={up_a['session_id']}")
    sid = up_a["session_id"]
    resolved = resolve_upload_ids(None, sid)
    if len(resolved) < 2:
        _fail("resolve_session", str(resolved))
        fails += 1
    else:
        _ok(f"resolve_upload_ids -> {len(resolved)}")
    pack_hits = search_upload_context("Fatih Istanbul", None, session_id=sid, top_k=3)
    if not pack_hits:
        _fail("session_search", "hit yok")
        fails += 1
    else:
        _ok("oturum paketi aramasi")

    if not nebula_apply_enabled():
        _fail("nebula_apply", "kapali")
        fails += 1
    else:
        _ok("nebula tek tik apply acik")
    nap = apply_nebula_oneri(
        "tarih_kaynak",
        "Test konu G2",
        upload_ids=[up_a["upload_id"]],
        background=False,
    )
    if not nap.get("ok") or not nap.get("batch_path"):
        _fail("nebula_apply_upload", str(nap)[:120])
        fails += 1
    else:
        _ok(f"nebula apply upload -> {nap.get('batch_path')}")
    nap2 = apply_nebula_oneri("tarih_kaynak", "Stub konu G2", background=False)
    if not nap2.get("ok"):
        _fail("nebula_apply_stub", str(nap2)[:120])
        fails += 1
    else:
        _ok("nebula apply stub")

    print("\n=== Faz H — nebula bg / session remember / virus scan ===")
    from ilim_assistant.ana_motor_dosya_ingest import upload_virus_scan_enabled
    from ilim_assistant.ana_motor_nebula_apply import (
        get_nebula_apply_job_status,
        nebula_apply_bg_enabled,
        start_nebula_apply_background,
        write_nebula_batch,
    )
    from ilim_assistant.ana_motor_session_hafiza import (
        remember_upload_session,
        session_remember_enabled,
    )

    if not nebula_apply_bg_enabled():
        _fail("nebula_apply_bg", "kapali")
        fails += 1
    else:
        _ok("nebula arka plan indeks acik")
    wb = write_nebula_batch("tarih_kaynak", "H1 yaz test", upload_ids=None)
    if not wb.get("ok"):
        _fail("write_nebula_batch", str(wb)[:80])
        fails += 1
    else:
        _ok("nebula batch yazildi")
    bg = start_nebula_apply_background(
        "tarih_kaynak", "H1 bg test", upload_ids=[up_a["upload_id"]]
    )
    if not bg.get("ok") or not bg.get("async"):
        _fail("nebula_bg_start", str(bg)[:100])
        fails += 1
    else:
        _ok("nebula bg kuyruk")
    st = get_nebula_apply_job_status()
    if not isinstance(st, dict):
        _fail("nebula_job_status", type(st).__name__)
        fails += 1
    else:
        _ok(f"nebula job running={st.get('running')}")

    if not session_remember_enabled():
        _fail("session_remember", "kapali")
        fails += 1
    else:
        _ok("oturum hatirla acik")
    mem = remember_upload_session(sid, topic="Faz H test")
    if not mem.get("ok") or not mem.get("remembered"):
        _fail("session_remember_write", str(mem)[:100])
        fails += 1
    else:
        _ok(f"hafiza yazildi files={mem.get('file_count')}")

    if not upload_virus_scan_enabled():
        _ok("upload virus scan kapali (env)")
    else:
        _ok("upload virus scan acik")

    print("\n=== Faz I — paket sihirbaz / arşiv / TTL ===")
    from ilim_assistant.ana_motor_dosya_ingest import (
        archive_enabled,
        archive_session_package,
        extend_session_ttl,
        ttl_extend_enabled,
    )
    from ilim_assistant.ana_motor_paket_sihirbaz import run_paket_sihirbaz, wizard_enabled

    if not wizard_enabled():
        _fail("paket_sihirbaz", "kapali")
        fails += 1
    else:
        _ok("paket sihirbaz acik")
    if not archive_enabled():
        _fail("upload_archive", "kapali")
        fails += 1
    else:
        _ok("oturum arsivi acik")
    ar = archive_session_package(sid, topic="Faz I arsiv test")
    if not ar.get("ok") or not ar.get("archive_path"):
        _fail("archive_session", str(ar)[:100])
        fails += 1
    else:
        _ok(f"arsiv -> {ar.get('archive_path')}")
    if not ttl_extend_enabled():
        _fail("upload_ttl_extend", "kapali")
        fails += 1
    else:
        _ok("TTL uzatma acik")
    ttl = extend_session_ttl(sid)
    if not ttl.get("ok") or not ttl.get("extended_until"):
        _fail("extend_ttl", str(ttl)[:100])
        fails += 1
    else:
        _ok(f"TTL uzatildi files={ttl.get('files')}")
    wiz = run_paket_sihirbaz(
        session_id=sid,
        topic="Faz I wizard test",
        do_archive=False,
        do_ttl_extend=False,
        do_remember=True,
        do_nebula=True,
    )
    if not wiz.get("ok") or not wiz.get("steps"):
        _fail("paket_sihirbaz_run", str(wiz)[:120])
        fails += 1
    else:
        _ok(f"paket sihirbaz {len(wiz.get('steps') or [])} adim")

    print("\n=== Faz J — otomatik paket / arşiv restore / oturum merge ===")
    import json
    import uuid

    from ilim_assistant.ana_motor_dosya_ingest import (
        archive_restore_enabled,
        list_archived_sessions,
        merge_upload_sessions,
        restore_archive_session,
        session_merge_enabled,
    )
    from ilim_assistant.ana_motor_paket_auto import (
        get_paket_auto_job_status,
        maybe_queue_auto_paket,
        paket_auto_enabled,
    )

    if not paket_auto_enabled():
        _fail("paket_auto", "kapali")
        fails += 1
    else:
        _ok("otomatik paket acik")

    class _ReqStub:
        ana_motor_upload_ids = [up_a["upload_id"]]
        ana_motor_session_id = sid
        coding_mode = False
        mode = "genel"
        message = "Faz J auto test"

    done_stub = {"user_message": "Faz J auto test", "full_reply": "test"}
    auto_done = maybe_queue_auto_paket(_ReqStub(), done_stub)
    if not auto_done.get("paket_auto", {}).get("queued"):
        _fail("paket_auto_queue", str(auto_done.get("paket_auto"))[:100])
        fails += 1
    else:
        _ok("otomatik paket kuyrugu")
    st_auto = get_paket_auto_job_status()
    if not isinstance(st_auto, dict):
        _fail("paket_auto_status", type(st_auto).__name__)
        fails += 1
    else:
        _ok(f"paket auto job running={st_auto.get('running')}")

    if not archive_restore_enabled():
        _fail("archive_restore", "kapali")
        fails += 1
    else:
        _ok("arsiv restore acik")
    archives = list_archived_sessions(limit=5)
    if not archives:
        _fail("archive_list", "bos")
        fails += 1
    else:
        _ok(f"arsiv listesi {len(archives)}")
    rr = restore_archive_session(sid)
    if not rr.get("ok") or not rr.get("upload_ids"):
        _fail("archive_restore_run", str(rr)[:100])
        fails += 1
    else:
        _ok(f"arsiv restore files={rr.get('file_count')}")
    rh = search_upload_context("Osmanli kurulus", None, session_id=sid, top_k=2)
    if not rh:
        _fail("archive_restore_rag", "hit yok")
        fails += 1
    else:
        _ok("arsiv restore RAG aramasi")

    sid2 = uuid.uuid4().hex[:12]
    sess_path = _ROOT / ".ruzgar" / "ana_motor_uploads" / "sessions" / f"{sid2}.json"
    sess_path.parent.mkdir(parents=True, exist_ok=True)
    sess_path.write_text(
        json.dumps({"session_id": sid2, "upload_ids": [up_a["upload_id"]]}, ensure_ascii=False),
        encoding="utf-8",
    )
    if not session_merge_enabled():
        _fail("session_merge", "kapali")
        fails += 1
    else:
        _ok("oturum merge acik")
    mg = merge_upload_sessions([sid, sid2])
    if not mg.get("ok") or len(mg.get("upload_ids") or []) < 1:
        _fail("session_merge_run", str(mg)[:100])
        fails += 1
    else:
        _ok(f"oturum merge files={mg.get('file_count')}")

    print("\n=== Faz K — paket ozet / oturum nebula / TTL hatirlat ===")
    from ilim_assistant.ana_motor_arsiv_hatirlat import (
        archive_ttl_remind_enabled,
        collect_archive_ttl_reminders,
    )
    from ilim_assistant.ana_motor_nebula_oneri import (
        build_session_nebula_card,
        session_nebula_oneri_enabled,
    )
    from ilim_assistant.ana_motor_paket_ozet import build_paket_ozet_card, paket_ozet_enabled

    if not paket_ozet_enabled():
        _fail("paket_ozet", "kapali")
        fails += 1
    else:
        _ok("paket ozet acik")
    oz = build_paket_ozet_card(wiz, source="manual")
    if not oz or not oz.get("steps_summary"):
        _fail("paket_ozet_card", str(oz)[:100])
        fails += 1
    else:
        _ok(f"paket ozet {oz.get('ok_steps')}/{oz.get('total_steps')}")

    if not session_nebula_oneri_enabled():
        _fail("session_nebula_oneri", "kapali")
        fails += 1
    else:
        _ok("oturum nebula oneri acik")
    snb = build_session_nebula_card(session_id=mg.get("session_id"), topic="Faz K test")
    if not snb or not snb.get("collection"):
        _fail("session_nebula_card", str(snb)[:100])
        fails += 1
    else:
        _ok(f"oturum nebula -> {snb.get('collection')}")
    if not mg.get("nebula_card"):
        _fail("merge_nebula_card", "yok")
        fails += 1
    else:
        _ok("merge nebula karti")

    if not archive_ttl_remind_enabled():
        _fail("archive_ttl_remind", "kapali")
        fails += 1
    else:
        _ok("arsiv TTL hatirlat acik")
    rem = collect_archive_ttl_reminders(limit=8)
    if not rem.get("ok"):
        _fail("archive_reminders", str(rem)[:80])
        fails += 1
    else:
        _ok(f"TTL hatirlat count={rem.get('count')}")

    print("\n=== Faz L — hatirlat paket / ozet nebula / timeline ===")
    from ilim_assistant.ana_motor_oturum_timeline import (
        build_session_timeline,
        timeline_enabled,
    )
    from ilim_assistant.ana_motor_paket_ozet import (
        build_ozet_nebula_apply_payload,
        ozet_nebula_apply_enabled,
    )
    from ilim_assistant.ana_motor_reminder_wizard import (
        enrich_reminder_actions,
        reminder_wizard_enabled,
        run_reminder_paket_sihirbaz,
    )

    if not reminder_wizard_enabled():
        _fail("reminder_wizard", "kapali")
        fails += 1
    else:
        _ok("hatirlat paket koprusu acik")
    enriched = enrich_reminder_actions(rem.get("reminders") or [])
    if enriched and not any(r.get("action") for r in enriched):
        _fail("reminder_action", "aksiyon yok")
        fails += 1
    else:
        _ok("hatirlat aksiyon alanlari")
    rw = run_reminder_paket_sihirbaz(
        kind="smoke",
        session_id=mg.get("session_id"),
        upload_ids=mg.get("upload_ids"),
        topic="Faz L reminder test",
    )
    if not rw.get("ok"):
        _fail("reminder_paket_run", str(rw)[:100])
        fails += 1
    else:
        _ok("hatirlat paket sihirbaz")

    if not ozet_nebula_apply_enabled():
        _fail("ozet_nebula_apply", "kapali")
        fails += 1
    else:
        _ok("ozet nebula apply acik")
    onb = build_ozet_nebula_apply_payload(oz)
    if not onb or not onb.get("collection"):
        _fail("ozet_nebula_payload", str(onb)[:80])
        fails += 1
    else:
        _ok(f"ozet nebula payload -> {onb.get('collection')}")

    if not timeline_enabled():
        _fail("session_timeline", "kapali")
        fails += 1
    else:
        _ok("oturum timeline acik")
    tl = build_session_timeline(limit=12)
    if not tl.get("ok"):
        _fail("session_timeline_build", str(tl)[:80])
        fails += 1
    else:
        _ok(f"timeline events={tl.get('count')}")

    print("\n=== Faz M — timeline aksiyon / bildirim / CSV ===")
    from ilim_assistant.ana_motor_hatirlat_bildirim import (
        build_desktop_notifications,
        desktop_notify_enabled,
        email_notify_enabled,
    )
    from ilim_assistant.ana_motor_paket_csv import (
        export_paket_history_csv,
        paket_csv_export_enabled,
    )
    from ilim_assistant.ana_motor_timeline_actions import (
        attach_timeline_actions,
        run_timeline_action,
        timeline_actions_enabled,
    )

    if not timeline_actions_enabled():
        _fail("timeline_actions", "kapali")
        fails += 1
    else:
        _ok("timeline aksiyon acik")
    with_actions = attach_timeline_actions(tl.get("events") or [])
    if with_actions and not any(e.get("actions") for e in with_actions):
        _fail("timeline_action_fields", "aksiyon yok")
        fails += 1
    else:
        _ok("timeline aksiyon alanlari")
    ta = run_timeline_action("restore", sid)
    if not ta.get("ok"):
        _fail("timeline_restore", str(ta)[:100])
        fails += 1
    else:
        _ok("timeline restore")

    if not desktop_notify_enabled():
        _fail("remind_desktop", "kapali")
        fails += 1
    else:
        _ok("masaustu bildirim acik")
    dn = build_desktop_notifications(rem.get("reminders") or [])
    if not isinstance(dn, list):
        _fail("desktop_notifications", type(dn).__name__)
        fails += 1
    else:
        _ok(f"desktop notify list={len(dn)}")
    if email_notify_enabled():
        _ok("email bildirim env acik")
    else:
        _ok("email bildirim varsayilan kapali")

    if not paket_csv_export_enabled():
        _fail("paket_csv", "kapali")
        fails += 1
    else:
        _ok("paket CSV export acik")
    csv_out = export_paket_history_csv(limit=50)
    if not csv_out.get("ok") or not csv_out.get("csv"):
        _fail("paket_csv_run", str(csv_out)[:80])
        fails += 1
    else:
        _ok(f"paket CSV rows={csv_out.get('row_count')}")

    print("\n=== Faz N — CSV toplu restore / bildirim tercih / paket grafik ===")
    from ilim_assistant.ana_motor_bildirim_tercih import (
        filter_reminders_by_prefs,
        load_notify_prefs,
        notify_prefs_enabled,
        save_notify_prefs,
    )
    from ilim_assistant.ana_motor_csv_restore import (
        bulk_restore_from_csv,
        csv_bulk_restore_enabled,
        parse_session_ids_from_csv,
    )
    from ilim_assistant.ana_motor_paket_grafik import (
        build_paket_history_summary,
        paket_grafik_enabled,
    )

    if not csv_bulk_restore_enabled():
        _fail("csv_bulk_restore", "kapali")
        fails += 1
    else:
        _ok("CSV toplu restore acik")
    csv_sample = str(csv_out.get("csv") or "")
    if not csv_sample:
        csv_sample = "session_id,olay\n" + sid + ",archived\n"
    ids = parse_session_ids_from_csv(csv_sample)
    if not ids:
        _fail("csv_parse_ids", "session_id yok")
        fails += 1
    else:
        _ok(f"CSV parse ids={len(ids)}")
    br = bulk_restore_from_csv(csv_sample, max_sessions=1)
    if not br.get("ok"):
        _fail("csv_bulk_restore_run", str(br)[:100])
        fails += 1
    else:
        _ok(f"CSV bulk restore={br.get('restored_count')}")

    if not notify_prefs_enabled():
        _fail("notify_prefs", "kapali")
        fails += 1
    else:
        _ok("bildirim tercih acik")
    np_load = load_notify_prefs()
    if not np_load.get("ok") or not isinstance(np_load.get("prefs"), dict):
        _fail("notify_prefs_load", str(np_load)[:80])
        fails += 1
    else:
        _ok("notify prefs yuklendi")
    np_save = save_notify_prefs({"poll_sec": 120, "warn_only": True})
    if not np_save.get("ok"):
        _fail("notify_prefs_save", str(np_save)[:80])
        fails += 1
    else:
        _ok("notify prefs kaydedildi")
    filt = filter_reminders_by_prefs(rem.get("reminders") or [])
    if not isinstance(filt, list):
        _fail("notify_prefs_filter", type(filt).__name__)
        fails += 1
    else:
        _ok(f"notify filter list={len(filt)}")

    if not paket_grafik_enabled():
        _fail("paket_grafik", "kapali")
        fails += 1
    else:
        _ok("paket grafik acik")
    pg = build_paket_history_summary(limit=50)
    if not pg.get("ok"):
        _fail("paket_grafik_build", str(pg)[:80])
        fails += 1
    else:
        _ok(f"paket grafik total={pg.get('summary', {}).get('total', 0)}")

    print("\n=== Faz O — CSV toplu paket / bildirim geçmişi / timeline filtre ===")
    from ilim_assistant.ana_motor_bildirim_gecmis import (
        append_notify_history,
        list_notify_history,
        notify_history_enabled,
    )
    from ilim_assistant.ana_motor_csv_paket import (
        bulk_paket_from_csv,
        csv_bulk_paket_enabled,
        parse_paket_rows_from_csv,
    )
    from ilim_assistant.ana_motor_timeline_filtre import (
        apply_timeline_filters,
        build_filtered_session_timeline,
        timeline_filter_enabled,
    )

    if not csv_bulk_paket_enabled():
        _fail("csv_bulk_paket", "kapali")
        fails += 1
    else:
        _ok("CSV toplu paket acik")
    pak_rows = parse_paket_rows_from_csv(csv_sample)
    if not pak_rows:
        _fail("csv_paket_parse", "satir yok")
        fails += 1
    else:
        _ok(f"CSV paket rows={len(pak_rows)}")
    bp = bulk_paket_from_csv(csv_sample, max_sessions=1)
    if not bp.get("ok"):
        _fail("csv_bulk_paket_run", str(bp)[:100])
        fails += 1
    else:
        _ok(f"CSV bulk paket={bp.get('paket_count')}")

    if not notify_history_enabled():
        _fail("notify_history", "kapali")
        fails += 1
    else:
        _ok("bildirim gecmisi acik")
    append_notify_history(channel="desktop", title="smoke", body="Faz O test", severity="info")
    nh = list_notify_history(limit=5)
    if not nh.get("ok") or not nh.get("items"):
        _fail("notify_history_list", str(nh)[:80])
        fails += 1
    else:
        _ok(f"notify history items={nh.get('count')}")

    if not timeline_filter_enabled():
        _fail("timeline_filter", "kapali")
        fails += 1
    else:
        _ok("timeline filtre acik")
    ft = build_filtered_session_timeline(limit=8, since_days=30)
    if not ft.get("ok"):
        _fail("timeline_filter_build", str(ft)[:80])
        fails += 1
    else:
        _ok(f"timeline filter count={ft.get('count')}")
    evs = tl.get("events") or []
    archived_only = apply_timeline_filters(evs, event_type="archived")
    if not isinstance(archived_only, list):
        _fail("timeline_filter_apply", type(archived_only).__name__)
        fails += 1
    else:
        _ok(f"timeline archived filter={len(archived_only)}")

    print("\n=== Faz P — JSON/PDF export / notify export / haftalik ozet ===")
    from ilim_assistant.ana_motor_bildirim_gecmis import (
        clear_notify_history,
        export_notify_history_json,
        notify_history_export_enabled,
    )
    from ilim_assistant.ana_motor_haftalik_ozet import (
        build_weekly_timeline_summary,
        weekly_summary_enabled,
    )
    from ilim_assistant.ana_motor_paket_export import (
        export_paket_history_json,
        export_paket_history_pdf,
        paket_json_export_enabled,
        paket_pdf_export_enabled,
    )

    if not paket_json_export_enabled():
        _fail("paket_json_export", "kapali")
        fails += 1
    else:
        _ok("paket JSON export acik")
    pj = export_paket_history_json(limit=30)
    if not pj.get("ok") or not pj.get("json"):
        _fail("paket_json_run", str(pj)[:80])
        fails += 1
    else:
        _ok(f"paket JSON rows={pj.get('row_count')}")

    if not paket_pdf_export_enabled():
        _fail("paket_pdf_export", "kapali")
        fails += 1
    else:
        _ok("paket PDF export acik")
    pp = export_paket_history_pdf(limit=30)
    if not pp.get("ok") or not pp.get("pdf"):
        _fail("paket_pdf_run", str(pp)[:80])
        fails += 1
    else:
        _ok(f"paket PDF bytes={len(pp.get('pdf') or b'')}")

    if not notify_history_export_enabled():
        _fail("notify_history_export", "kapali")
        fails += 1
    else:
        _ok("notify history export acik")
    ne = export_notify_history_json(limit=20)
    if not ne.get("ok"):
        _fail("notify_export_json", str(ne)[:80])
        fails += 1
    else:
        _ok(f"notify export count={ne.get('count')}")
    clr = clear_notify_history()
    if not clr.get("ok"):
        _fail("notify_clear", str(clr)[:80])
        fails += 1
    else:
        _ok("notify history temizlendi")

    if not weekly_summary_enabled():
        _fail("weekly_summary", "kapali")
        fails += 1
    else:
        _ok("haftalik ozet acik")
    ws = build_weekly_timeline_summary(days=7, limit=20)
    if not ws.get("ok") or not ws.get("summary_card"):
        _fail("weekly_summary_build", str(ws)[:80])
        fails += 1
    else:
        _ok(f"haftalik ozet events={ws.get('event_count')}")

    print("\n=== Faz Q — haftalik bildirim / karsilastirma / timeline hatirla ===")
    from ilim_assistant.ana_motor_haftalik_bildirim import (
        attach_weekly_notifications,
        build_weekly_desktop_notifications,
        weekly_notify_enabled,
    )
    from ilim_assistant.ana_motor_paket_karsilastir import (
        build_paket_history_compare,
        paket_compare_enabled,
    )
    from ilim_assistant.ana_motor_timeline_hatirla import (
        auto_remember_from_timeline,
        run_timeline_remember,
        timeline_remember_enabled,
    )

    if not weekly_notify_enabled():
        _fail("weekly_notify", "kapali")
        fails += 1
    else:
        _ok("haftalik bildirim acik")
    wn = build_weekly_desktop_notifications(ws)
    if not isinstance(wn, list):
        _fail("weekly_desktop", type(wn).__name__)
        fails += 1
    else:
        _ok(f"weekly desktop list={len(wn)}")
    wna = attach_weekly_notifications(ws, send_desktop=True, force=True)
    if not wna.get("ok"):
        _fail("weekly_attach", str(wna)[:80])
        fails += 1
    else:
        _ok("weekly notify attach")

    if not paket_compare_enabled():
        _fail("paket_compare", "kapali")
        fails += 1
    else:
        _ok("paket karsilastirma acik")
    pc = build_paket_history_compare(period_days=7)
    if not pc.get("ok") or not pc.get("compare_card"):
        _fail("paket_compare_build", str(pc)[:80])
        fails += 1
    else:
        _ok(f"paket compare delta={pc.get('delta', {}).get('events')}")

    if not timeline_remember_enabled():
        _fail("timeline_remember", "kapali")
        fails += 1
    else:
        _ok("timeline hatirla acik")
    tr = run_timeline_remember(sid, topic="Faz Q smoke")
    if not tr.get("ok"):
        _fail("timeline_remember_run", str(tr)[:100])
        fails += 1
    else:
        _ok("timeline remember tek oturum")
    tb = auto_remember_from_timeline(limit=2)
    if not tb.get("ok"):
        _fail("timeline_remember_batch", str(tb)[:100])
        fails += 1
    else:
        _ok(f"timeline batch remember={tb.get('remembered_count')}")

    print("\n=== Faz R — compare chart / hatirla gecmisi / haftalik zamanlayici ===")
    from ilim_assistant.ana_motor_compare_grafik import (
        build_compare_dual_chart,
        compare_chart_enabled,
    )
    from ilim_assistant.ana_motor_hatirla_gecmis import (
        list_remember_history,
        remember_history_enabled,
    )
    from ilim_assistant.ana_motor_haftalik_zamanlayici import (
        get_weekly_schedule_status,
        tick_weekly_schedule,
        weekly_schedule_enabled,
    )

    if not compare_chart_enabled():
        _fail("compare_chart", "kapali")
        fails += 1
    else:
        _ok("compare chart acik")
    cc = build_compare_dual_chart(period_days=7)
    if not cc.get("ok") or not cc.get("groups"):
        _fail("compare_chart_build", str(cc)[:80])
        fails += 1
    else:
        _ok(f"compare chart groups={len(cc.get('groups'))}")

    if not remember_history_enabled():
        _fail("remember_history", "kapali")
        fails += 1
    else:
        _ok("hatirla gecmisi acik")
    rh = list_remember_history(limit=10)
    if not rh.get("ok"):
        _fail("remember_history_list", str(rh)[:80])
        fails += 1
    else:
        _ok(f"remember history items={rh.get('count')}")

    if not weekly_schedule_enabled():
        _fail("weekly_schedule", "kapali")
        fails += 1
    else:
        _ok("haftalik zamanlayici acik")
    st = get_weekly_schedule_status()
    if not st.get("ok"):
        _fail("weekly_schedule_status", str(st)[:80])
        fails += 1
    else:
        _ok(f"schedule poll={st.get('poll_sec')}")
    tk = tick_weekly_schedule(days=7)
    if not tk.get("ok"):
        _fail("weekly_schedule_tick", str(tk)[:80])
        fails += 1
    else:
        _ok(f"schedule tick skipped={tk.get('skipped')}")

    print("\n=== Faz S — compare export / hatirla export / schedule prefs ===")
    from ilim_assistant.ana_motor_compare_export import (
        compare_export_enabled,
        export_compare_csv,
        export_compare_pdf,
    )
    from ilim_assistant.ana_motor_hatirla_gecmis import (
        export_remember_history_json,
        remember_history_export_enabled,
    )
    from ilim_assistant.ana_motor_schedule_tercih import (
        load_schedule_prefs,
        save_schedule_prefs,
        schedule_prefs_enabled,
    )

    if not compare_export_enabled():
        _fail("compare_export", "kapali")
        fails += 1
    else:
        _ok("compare export acik")
    ce = export_compare_csv(period_days=7)
    if not ce.get("ok") or not ce.get("csv"):
        _fail("compare_csv", str(ce)[:80])
        fails += 1
    else:
        _ok(f"compare CSV rows={ce.get('row_count')}")
    cp = export_compare_pdf(period_days=7)
    if not cp.get("ok") or not cp.get("pdf"):
        _fail("compare_pdf", str(cp)[:80])
        fails += 1
    else:
        _ok(f"compare PDF bytes={len(cp.get('pdf') or b'')}")

    if not remember_history_export_enabled():
        _fail("remember_export", "kapali")
        fails += 1
    else:
        _ok("hatirla export acik")
    re = export_remember_history_json(limit=20)
    if not re.get("ok"):
        _fail("remember_export_json", str(re)[:80])
        fails += 1
    else:
        _ok(f"remember export count={re.get('count')}")

    if not schedule_prefs_enabled():
        _fail("schedule_prefs", "kapali")
        fails += 1
    else:
        _ok("schedule prefs acik")
    sp = save_schedule_prefs({"poll_sec": 3600, "period_days": 7})
    if not sp.get("ok"):
        _fail("schedule_prefs_save", str(sp)[:80])
        fails += 1
    else:
        _ok("schedule prefs kaydedildi")
    spl = load_schedule_prefs()
    if not spl.get("ok"):
        _fail("schedule_prefs_load", str(spl)[:80])
        fails += 1
    else:
        _ok(f"schedule poll={spl.get('prefs', {}).get('poll_sec')}")

    print("\n=== Faz T — super ozet PDF / birlesik tercih / compare email ===")
    from ilim_assistant.ana_motor_birlesik_tercih import (
        load_unified_prefs,
        save_unified_prefs,
        unified_prefs_enabled,
    )
    from ilim_assistant.ana_motor_compare_email import (
        compare_email_enabled,
        maybe_send_compare_email,
    )
    from ilim_assistant.ana_motor_super_ozet_pdf import (
        export_super_ozet_pdf,
        super_ozet_pdf_enabled,
    )

    if not super_ozet_pdf_enabled():
        _fail("super_ozet_pdf", "kapali")
        fails += 1
    else:
        _ok("super ozet PDF acik")
    sp = export_super_ozet_pdf(period_days=7)
    if not sp.get("ok") or not sp.get("pdf"):
        _fail("super_ozet_pdf_run", str(sp)[:80])
        fails += 1
    else:
        _ok(f"super PDF bytes={len(sp.get('pdf') or b'')}")

    if not unified_prefs_enabled():
        _fail("unified_prefs", "kapali")
        fails += 1
    else:
        _ok("birlesik tercih acik")
    up = save_unified_prefs(
        {
            "remind_poll_sec": 120,
            "schedule_poll_sec": 3600,
            "period_days": 7,
            "compare_email_enabled": False,
        }
    )
    if not up.get("ok"):
        _fail("unified_prefs_save", str(up)[:80])
        fails += 1
    else:
        _ok("birlesik tercih kaydedildi")
    upl = load_unified_prefs()
    if not upl.get("ok") or not upl.get("prefs"):
        _fail("unified_prefs_load", str(upl)[:80])
        fails += 1
    else:
        _ok("birlesik tercih yuklendi")

    if not compare_email_enabled():
        _fail("compare_email", "kapali")
        fails += 1
    else:
        _ok("compare email acik")
    ce = maybe_send_compare_email(period_days=7, force=False)
    if not ce.get("ok") and ce.get("error"):
        _fail("compare_email_run", str(ce)[:80])
        fails += 1
    else:
        _ok(f"compare email sent={ce.get('sent')}")

    print("\n=== Faz U — super ozet email / unified export / dashboard HTML ===")
    from ilim_assistant.ana_motor_birlesik_tercih import (
        export_unified_prefs_json,
        import_unified_prefs_json,
        unified_prefs_export_enabled,
    )
    from ilim_assistant.ana_motor_dashboard_html import (
        build_dashboard_html_summary,
        dashboard_html_enabled,
    )
    from ilim_assistant.ana_motor_super_ozet_email import (
        maybe_send_super_ozet_email,
        super_ozet_email_enabled,
    )

    if not super_ozet_email_enabled():
        _fail("super_ozet_email", "kapali")
        fails += 1
    else:
        _ok("super ozet email acik")
    se = maybe_send_super_ozet_email(period_days=7, force=False)
    if not se.get("ok") and se.get("error"):
        _fail("super_ozet_email_run", str(se)[:80])
        fails += 1
    else:
        _ok(f"super ozet email sent={se.get('sent')}")

    if not unified_prefs_export_enabled():
        _fail("unified_prefs_export", "kapali")
        fails += 1
    else:
        _ok("unified prefs export acik")
    upe = export_unified_prefs_json()
    if not upe.get("ok") or not upe.get("json"):
        _fail("unified_prefs_export_run", str(upe)[:80])
        fails += 1
    else:
        _ok(f"unified export bytes={len(upe.get('json') or '')}")
    upi = import_unified_prefs_json(upe.get("json") or "{}")
    if not upi.get("ok"):
        _fail("unified_prefs_import_run", str(upi)[:80])
        fails += 1
    else:
        _ok("unified prefs import roundtrip")

    if not dashboard_html_enabled():
        _fail("dashboard_html", "kapali")
        fails += 1
    else:
        _ok("dashboard HTML acik")
    dh = build_dashboard_html_summary(period_days=7)
    if not dh.get("ok") or not dh.get("html"):
        _fail("dashboard_html_run", str(dh)[:80])
        fails += 1
    else:
        _ok(f"dashboard HTML bytes={len(dh.get('html') or '')}")

    print("\n=== Faz V — birlesik email / dashboard PDF / tam tercih yedek ===")
    from ilim_assistant.ana_motor_birlesik_email import (
        birlesik_email_enabled,
        maybe_send_birlesik_email,
    )
    from ilim_assistant.ana_motor_dashboard_pdf import (
        dashboard_pdf_enabled,
        export_dashboard_pdf,
    )
    from ilim_assistant.ana_motor_tam_tercih_yedek import (
        export_tam_prefs_archive,
        import_tam_prefs_archive,
        tam_prefs_yedek_enabled,
    )

    if not birlesik_email_enabled():
        _fail("birlesik_email", "kapali")
        fails += 1
    else:
        _ok("birlesik email acik")
    be = maybe_send_birlesik_email(period_days=7, force=False)
    if not be.get("ok") and be.get("error"):
        _fail("birlesik_email_run", str(be)[:80])
        fails += 1
    else:
        _ok(f"birlesik email sent={be.get('sent')}")

    if not dashboard_pdf_enabled():
        _fail("dashboard_pdf", "kapali")
        fails += 1
    else:
        _ok("dashboard PDF acik")
    dp = export_dashboard_pdf(period_days=7)
    if not dp.get("ok") or not dp.get("pdf"):
        _fail("dashboard_pdf_run", str(dp)[:80])
        fails += 1
    else:
        _ok(f"dashboard PDF bytes={len(dp.get('pdf') or b'')}")

    if not tam_prefs_yedek_enabled():
        _fail("tam_prefs_yedek", "kapali")
        fails += 1
    else:
        _ok("tam tercih yedek acik")
    tpe = export_tam_prefs_archive()
    if not tpe.get("ok") or not tpe.get("json"):
        _fail("tam_prefs_export_run", str(tpe)[:80])
        fails += 1
    else:
        _ok(f"tam yedek bytes={len(tpe.get('json') or '')}")
    tpi = import_tam_prefs_archive(tpe.get("json") or "{}")
    if not tpi.get("ok"):
        _fail("tam_prefs_import_run", str(tpi)[:80])
        fails += 1
    else:
        _ok(f"tam yedek restore={tpi.get('restored')}")

    print("\n=== Faz W — backend yurut / tercume instant / video url bilgi ===")
    from ilim_assistant.ana_motor_backend_yurut import (
        backend_yurut_enabled,
        execute_backend_motor,
        resolve_motor_dispatch_kind,
    )
    from ilim_assistant.ana_motor_tercume_yurut import (
        maybe_run_instant_translate,
        tercume_instant_enabled,
    )
    from ilim_assistant.ana_motor_video_bilgi import (
        maybe_video_url_info,
        video_url_info_enabled,
    )

    if not backend_yurut_enabled():
        _fail("backend_yurut", "kapali")
        fails += 1
    else:
        _ok("backend yurut acik")
    disp = resolve_motor_dispatch_kind("tercume")
    if disp != "backend:tercume_translate":
        _fail("dispatch_tercume", str(disp))
        fails += 1
    else:
        _ok("tercume dispatch backend")
    hf = execute_backend_motor("hafiza durumu", "hafiza")
    if not hf.get("handled") or not hf.get("reply"):
        _fail("backend_hafiza", str(hf)[:80])
        fails += 1
    else:
        _ok("backend hafiza durumu")

    if not tercume_instant_enabled():
        _fail("tercume_instant", "kapali")
        fails += 1
    else:
        _ok("tercume instant acik")
    ti = maybe_run_instant_translate("dil listesi")
    if ti.get("handled"):
        _fail("tercume_skip_list", "should not translate")
        fails += 1
    else:
        _ok("tercume non-translate skip")

    if not video_url_info_enabled():
        _fail("video_url_info", "kapali")
        fails += 1
    else:
        _ok("video url bilgi acik")
    vi = maybe_video_url_info("merhaba dunya")
    if vi.get("handled"):
        _fail("video_info_skip", "should skip")
        fails += 1
    else:
        _ok("video bilgi skip (no url)")

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
    if denge70_ready_for_chain():
        if "denge70" not in chain_ids:
            _fail("bilim derin 70b zincir", chain_ids)
            fails += 1
        else:
            _ok(f"bilim derin zincirde denge70: {chain_ids[:5]}")
    else:
        _ok(f"denge70 cekilmemis — zincirden atlandi: {chain_ids[:5]}")
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
    if "denge70_ready" not in am:
        _fail("faz_e denge70_ready", "health alani yok")
        fails += 1
    else:
        _ok(
            f"denge70_ready={am.get('denge70_ready')} "
            f"hint={str(am.get('denge70_hint') or '')[:48]}"
        )
    if not am.get("ana_progress_eta"):
        _fail("faz_e progress", "kapali")
        fails += 1
    else:
        _ok("progress ETA acik")
    if not am.get("patch_approval_bridge"):
        _fail("faz_e3 patch", "kapali")
        fails += 1
    else:
        _ok("Faz E3 patch onay koprusu acik")
    if not am.get("arastirma_nebula_card"):
        _fail("faz_e4 nebula", "kapali")
        fails += 1
    else:
        _ok("Faz E4 nebula kart acik")
    if not am.get("upload_ingest"):
        _fail("faz_f1 upload", "kapali")
        fails += 1
    else:
        _ok("Faz F1 upload ingest acik")
    if not am.get("nebula_oneri"):
        _fail("faz_f2 oneri", "kapali")
        fails += 1
    else:
        _ok("Faz F2 nebula oneri acik")
    if not am.get("kaynak_matris"):
        _fail("faz_f3 matris", "kapali")
        fails += 1
    else:
        _ok("Faz F3 kaynak matrisi acik")
    if not am.get("upload_session"):
        _fail("faz_g3 session", "kapali")
        fails += 1
    else:
        _ok("Faz G3 upload session acik")
    if not am.get("nebula_apply"):
        _fail("faz_g2 apply", "kapali")
        fails += 1
    else:
        _ok("Faz G2 nebula apply acik")
    if not am.get("nebula_apply_bg"):
        _fail("faz_h1 bg", "kapali")
        fails += 1
    else:
        _ok("Faz H1 nebula bg acik")
    if not am.get("session_remember"):
        _fail("faz_h2 remember", "kapali")
        fails += 1
    else:
        _ok("Faz H2 session remember acik")
    if "upload_virus_scan" not in am:
        _fail("faz_h3 virus", "health alani yok")
        fails += 1
    else:
        _ok(f"Faz H3 upload virus scan={am.get('upload_virus_scan')}")
    if not am.get("paket_sihirbaz"):
        _fail("faz_i1 wizard", "kapali")
        fails += 1
    else:
        _ok("Faz I1 paket sihirbaz acik")
    if not am.get("upload_archive"):
        _fail("faz_i2 archive", "kapali")
        fails += 1
    else:
        _ok("Faz I2 upload archive acik")
    if not am.get("upload_ttl_extend"):
        _fail("faz_i2 ttl", "kapali")
        fails += 1
    else:
        _ok("Faz I2 upload TTL extend acik")
    if "live_nebula_index_slo_sec" not in am:
        _fail("faz_i3 slo", "health alani yok")
        fails += 1
    else:
        _ok(f"Faz I3 nebula index SLO={am.get('live_nebula_index_slo_sec')}s")
    if not am.get("paket_auto"):
        _fail("faz_j1 auto", "kapali")
        fails += 1
    else:
        _ok("Faz J1 paket auto acik")
    if not am.get("archive_restore"):
        _fail("faz_j2 restore", "kapali")
        fails += 1
    else:
        _ok("Faz J2 archive restore acik")
    if not am.get("session_merge"):
        _fail("faz_j3 merge", "kapali")
        fails += 1
    else:
        _ok("Faz J3 session merge acik")
    if not am.get("paket_ozet"):
        _fail("faz_k1 ozet", "kapali")
        fails += 1
    else:
        _ok("Faz K1 paket ozet acik")
    if not am.get("archive_ttl_remind"):
        _fail("faz_k3 remind", "kapali")
        fails += 1
    else:
        _ok("Faz K3 archive TTL remind acik")
    if not am.get("session_nebula_oneri"):
        _fail("faz_k2 nebula", "kapali")
        fails += 1
    else:
        _ok("Faz K2 session nebula oneri acik")
    if not am.get("reminder_wizard"):
        _fail("faz_l1 remind", "kapali")
        fails += 1
    else:
        _ok("Faz L1 reminder wizard acik")
    if not am.get("ozet_nebula_apply"):
        _fail("faz_l2 ozet", "kapali")
        fails += 1
    else:
        _ok("Faz L2 ozet nebula apply acik")
    if not am.get("session_timeline"):
        _fail("faz_l3 timeline", "kapali")
        fails += 1
    else:
        _ok("Faz L3 session timeline acik")
    if not am.get("timeline_actions"):
        _fail("faz_m1 timeline_act", "kapali")
        fails += 1
    else:
        _ok("Faz M1 timeline actions acik")
    if not am.get("remind_desktop"):
        _fail("faz_m2 desktop", "kapali")
        fails += 1
    else:
        _ok("Faz M2 remind desktop acik")
    if not am.get("paket_csv_export"):
        _fail("faz_m3 csv", "kapali")
        fails += 1
    else:
        _ok("Faz M3 paket CSV acik")
    if not am.get("csv_bulk_restore"):
        _fail("faz_n1 csv_restore", "kapali")
        fails += 1
    else:
        _ok("Faz N1 CSV bulk restore acik")
    if not am.get("notify_prefs"):
        _fail("faz_n2 notify_prefs", "kapali")
        fails += 1
    else:
        _ok("Faz N2 notify prefs acik")
    if not am.get("paket_grafik"):
        _fail("faz_n3 paket_grafik", "kapali")
        fails += 1
    else:
        _ok("Faz N3 paket grafik acik")
    if not am.get("csv_bulk_paket"):
        _fail("faz_o1 csv_paket", "kapali")
        fails += 1
    else:
        _ok("Faz O1 CSV bulk paket acik")
    if not am.get("notify_history"):
        _fail("faz_o2 notify_hist", "kapali")
        fails += 1
    else:
        _ok("Faz O2 notify history acik")
    if not am.get("timeline_filter"):
        _fail("faz_o3 timeline_filt", "kapali")
        fails += 1
    else:
        _ok("Faz O3 timeline filter acik")
    if not am.get("paket_json_export"):
        _fail("faz_p1 json", "kapali")
        fails += 1
    else:
        _ok("Faz P1 paket JSON acik")
    if not am.get("paket_pdf_export"):
        _fail("faz_p2 pdf", "kapali")
        fails += 1
    else:
        _ok("Faz P2 paket PDF acik")
    if not am.get("notify_history_export"):
        _fail("faz_p2 notify_exp", "kapali")
        fails += 1
    else:
        _ok("Faz P2 notify export acik")
    if not am.get("weekly_summary"):
        _fail("faz_p3 weekly", "kapali")
        fails += 1
    else:
        _ok("Faz P3 weekly summary acik")
    if not am.get("weekly_notify"):
        _fail("faz_q1 weekly_notify", "kapali")
        fails += 1
    else:
        _ok("Faz Q1 weekly notify acik")
    if not am.get("paket_compare"):
        _fail("faz_q2 compare", "kapali")
        fails += 1
    else:
        _ok("Faz Q2 paket compare acik")
    if not am.get("timeline_remember"):
        _fail("faz_q3 timeline_remember", "kapali")
        fails += 1
    else:
        _ok("Faz Q3 timeline remember acik")
    if not am.get("compare_chart"):
        _fail("faz_r1 compare_chart", "kapali")
        fails += 1
    else:
        _ok("Faz R1 compare chart acik")
    if not am.get("remember_history"):
        _fail("faz_r2 remember_hist", "kapali")
        fails += 1
    else:
        _ok("Faz R2 remember history acik")
    if not am.get("weekly_schedule"):
        _fail("faz_r3 schedule", "kapali")
        fails += 1
    else:
        _ok("Faz R3 weekly schedule acik")
    if not am.get("compare_export"):
        _fail("faz_s1 compare_exp", "kapali")
        fails += 1
    else:
        _ok("Faz S1 compare export acik")
    if not am.get("remember_history_export"):
        _fail("faz_s2 remember_exp", "kapali")
        fails += 1
    else:
        _ok("Faz S2 remember export acik")
    if not am.get("schedule_prefs"):
        _fail("faz_s3 schedule_prefs", "kapali")
        fails += 1
    else:
        _ok("Faz S3 schedule prefs acik")
    if not am.get("super_ozet_pdf"):
        _fail("faz_t1 super_pdf", "kapali")
        fails += 1
    else:
        _ok("Faz T1 super ozet PDF acik")
    if not am.get("unified_prefs"):
        _fail("faz_t2 unified", "kapali")
        fails += 1
    else:
        _ok("Faz T2 unified prefs acik")
    if not am.get("compare_email"):
        _fail("faz_t3 compare_email", "kapali")
        fails += 1
    else:
        _ok("Faz T3 compare email acik")
    if not am.get("super_ozet_email"):
        _fail("faz_u1 super_email", "kapali")
        fails += 1
    else:
        _ok("Faz U1 super ozet email acik")
    if not am.get("unified_prefs_export"):
        _fail("faz_u2 unified_export", "kapali")
        fails += 1
    else:
        _ok("Faz U2 unified prefs export acik")
    if not am.get("dashboard_html"):
        _fail("faz_u3 dashboard_html", "kapali")
        fails += 1
    else:
        _ok("Faz U3 dashboard HTML acik")
    if not am.get("birlesik_email"):
        _fail("faz_v1 birlesik_email", "kapali")
        fails += 1
    else:
        _ok("Faz V1 birlesik email acik")
    if not am.get("dashboard_pdf"):
        _fail("faz_v2 dashboard_pdf", "kapali")
        fails += 1
    else:
        _ok("Faz V2 dashboard PDF acik")
    if not am.get("tam_prefs_yedek"):
        _fail("faz_v3 tam_yedek", "kapali")
        fails += 1
    else:
        _ok("Faz V3 tam tercih yedek acik")
    if not am.get("backend_yurut"):
        _fail("faz_w1 backend_yurut", "kapali")
        fails += 1
    else:
        _ok("Faz W1 backend yurut acik")
    if not am.get("tercume_instant"):
        _fail("faz_w2 tercume_inst", "kapali")
        fails += 1
    else:
        _ok("Faz W2 tercume instant acik")
    if not am.get("video_url_info"):
        _fail("faz_w3 video_info", "kapali")
        fails += 1
    else:
        _ok("Faz W3 video url bilgi acik")

    print("\n=== Canli — upload + matris SLO ===")
    chat_url = base.rstrip("/") + "/api/chat/full"
    upload_url = base.rstrip("/") + "/api/ana-motor/upload-context"
    boundary = "----RuzgarSmokeG1"
    file_body = (
        "# Canli test\n\nOsmanli devleti kurulus yili 1299.\n"
    ).encode("utf-8")
    multipart = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="g1_live.md"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode("utf-8") + file_body + f"\r\n--{boundary}--\r\n".encode("utf-8")
    upload_id = None
    t_up = time.monotonic()
    try:
        up_req = urllib.request.Request(
            upload_url,
            data=multipart,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(up_req, timeout=30) as r:
            up_j = json.loads(r.read().decode("utf-8", errors="replace"))
        if not up_j.get("ok") or not up_j.get("upload_id"):
            _fail("live upload", str(up_j)[:120])
            fails += 1
        else:
            upload_id = up_j["upload_id"]
            _ok(f"canli upload {time.monotonic() - t_up:.1f}s id={upload_id[:8]}")
    except Exception as e:
        _fail("live upload", str(e)[:120])
        fails += 1

    if upload_id:
        t_mat = time.monotonic()
        mat_body = json.dumps(
            {
                "message": "Osmanli devleti ne zaman kuruldu?",
                "mode": "genel",
                "coding_mode": False,
                "use_web": False,
                "ana_motor_upload_ids": [upload_id],
            },
            ensure_ascii=False,
        ).encode("utf-8")
        try:
            mat_req = urllib.request.Request(
                chat_url,
                data=mat_body,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(mat_req, timeout=120) as r:
                mat_j = json.loads(r.read().decode("utf-8", errors="replace"))
            elapsed_mat = time.monotonic() - t_mat
            if not mat_j.get("ok"):
                _fail("live upload+matris", str(mat_j.get("error") or "")[:120])
                fails += 1
            else:
                _ok(f"canli upload+matris turu {elapsed_mat:.1f}s")
                try:
                    slo_g = float(
                        am.get("live_upload_matris_slo_sec")
                        or os.environ.get("RUZGAR_LIVE_UPLOAD_MATRIS_SLO_SEC", "90")
                    )
                except ValueError:
                    slo_g = 90.0
                if elapsed_mat > slo_g:
                    _fail("upload+matris SLO", f"{elapsed_mat:.1f}s > {slo_g}s")
                    fails += 1
                else:
                    _ok(f"upload+matris SLO <= {slo_g:.0f}s")
                evs = mat_j.get("events") or []
                status_txt = " ".join(
                    str(e.get("text") or "") for e in evs if e.get("type") == "status"
                ).lower()
                if "matris" not in status_txt and "upload" not in status_txt:
                    _fail("live status phases", status_txt[:100])
                    fails += 1
                else:
                    _ok("canli status: matris/upload")
        except Exception as e:
            _fail("live upload+matris", str(e)[:120])
            fails += 1

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

    print("\n=== Canli — bilim derin SLO ===")
    bilim_body = json.dumps(
        {
            "message": "Osmanli Fatih donemini detayli acikla",
            "mode": "genel",
            "coding_mode": False,
            "use_web": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    t1 = time.monotonic()
    try:
        req2 = urllib.request.Request(
            chat_url,
            data=bilim_body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req2, timeout=180) as r:
            cj2 = json.loads(r.read().decode("utf-8", errors="replace"))
        elapsed2 = time.monotonic() - t1
        if not cj2.get("ok"):
            _fail("live bilim derin", str(cj2.get("error") or "")[:120])
            fails += 1
        else:
            _ok(f"canli bilim derin turu {elapsed2:.1f}s")
            try:
                slo2 = float(
                    am.get("bilim_derin_slo_sec")
                    or os.environ.get("RUZGAR_LIVE_BILIM_DERIN_SLO_SEC", "120")
                )
            except ValueError:
                slo2 = 120.0
            if elapsed2 > slo2:
                _fail("bilim derin SLO", f"{elapsed2:.1f}s > {slo2}s")
                fails += 1
            else:
                _ok(f"bilim derin SLO <= {slo2:.0f}s")
    except Exception as e:
        _fail("live bilim derin", str(e)[:120])
        fails += 1

    print("\n=== Canli — nebula indeks SLO (Faz I3) ===")
    if upload_id:
        wiz_url = base.rstrip("/") + "/api/ana-motor/paket-sihirbaz"
        status_url = base.rstrip("/") + "/api/ana-motor/nebula-apply/status"
        wiz_payload = json.dumps(
            {
                "upload_ids": [upload_id],
                "topic": "Canli I3 nebula indeks",
                "collection": "tarih_kaynak",
                "do_archive": False,
                "do_remember": False,
                "do_ttl_extend": False,
                "do_nebula": True,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        t_idx = time.monotonic()
        try:
            wiz_req = urllib.request.Request(
                wiz_url,
                data=wiz_payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(wiz_req, timeout=60) as r:
                wiz_j = json.loads(r.read().decode("utf-8", errors="replace"))
            if not wiz_j.get("ok"):
                _fail("live paket nebula", str(wiz_j)[:120])
                fails += 1
            else:
                _ok("canli paket nebula kuyrugu")
                try:
                    slo_i = float(
                        am.get("live_nebula_index_slo_sec")
                        or os.environ.get("RUZGAR_LIVE_NEBULA_INDEX_SLO_SEC", "300")
                    )
                except ValueError:
                    slo_i = 300.0
                deadline = t_idx + slo_i + 15.0
                done = False
                while time.monotonic() < deadline:
                    st_req = urllib.request.Request(status_url, method="GET")
                    with urllib.request.urlopen(st_req, timeout=15) as sr:
                        st_j = json.loads(sr.read().decode("utf-8", errors="replace"))
                    job = st_j.get("job") or {}
                    if not job.get("running"):
                        done = True
                        break
                    time.sleep(2.0)
                elapsed_idx = time.monotonic() - t_idx
                if not done:
                    _fail("nebula index SLO", f"timeout {elapsed_idx:.1f}s")
                    fails += 1
                elif elapsed_idx > slo_i:
                    _fail("nebula index SLO", f"{elapsed_idx:.1f}s > {slo_i}s")
                    fails += 1
                else:
                    _ok(f"nebula indeks SLO <= {slo_i:.0f}s ({elapsed_idx:.1f}s)")
        except Exception as e:
            _fail("live nebula index SLO", str(e)[:120])
            fails += 1
    else:
        _fail("live nebula index SLO", "upload_id yok")
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
