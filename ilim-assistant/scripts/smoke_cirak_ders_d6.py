# Created by Ümit & Gökçenur
"""Dilim 6 — Çırak ders sözleşmesi smoke."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ruzgar_cirak_ders import (
        CIRAK_GOREV_TURLERI,
        USTA_KIRILGAN,
        cirak_gorev_metni,
        cirak_status,
        yesil_dilim_icin_ders_gerekli,
    )

    fails = 0

    from ilim_assistant.ruzgar_cirak_ders import wants_full_code_agent

    g = cirak_gorev_metni("smoke_yesil", "ana_motor_faz_ses_smoke geçsin")
    if (
        not g.startswith("görev:")
        or "projects/cirak-atolyesi" not in g
        or "cirak smoke_yesil" not in g
        or "[cirak:" in g
        or "tam ajan" not in g
    ):
        print("FAIL gorev metni", g)
        fails += 1
    else:
        print("  OK çırak görev satırı (atölye scope)")
    if not wants_full_code_agent(g):
        print("FAIL wants_full_code_agent")
        fails += 1
    else:
        print("  OK wants_full_code_agent")

    from pathlib import Path

    from ilim_assistant.motorlar.programlama_faz14 import parse_code_agent_task
    from ilim_assistant.ruzgar_cirak_ders import try_cirak_supervised_write

    t_old = parse_code_agent_task(
        "görev: cirak tek_dosya_patch — projects/cirak-atolyesi/x.py yaz · tam ajan"
    )
    if not t_old or t_old.scope_rel.replace("\\", "/") != "projects/cirak-atolyesi":
        print("FAIL cirak→atolyesi remap", t_old)
        fails += 1
    else:
        print("  OK cirak slug → cirak-atolyesi")

    t_ml = parse_code_agent_task(
        "görev: projects/cirak-atolyesi cirak rapor_md — satır1\n"
        "projects/cirak-atolyesi/oz_analiz_raporu_v2.md yaz\n"
        "hello_cirak.py oku · tam ajan"
    )
    if (
        not t_ml
        or "oz_analiz_raporu_v2.md" not in (t_ml.goal or "")
        or "hello_cirak.py" not in (t_ml.goal or "")
    ):
        print("FAIL multiline görev goal", t_ml)
        fails += 1
    else:
        print("  OK multiline görev goal")

    root = Path(__file__).resolve().parents[2]
    probe = (
        "görev: projects/cirak-atolyesi cirak smoke_yesil — "
        "projects/cirak-atolyesi/_smoke_probe.py "
        "print PASS cirak-d9 · tam ajan"
    )
    wr = try_cirak_supervised_write(probe, root)
    probe_path = root / "projects" / "cirak-atolyesi" / "_smoke_probe.py"
    okw = bool(wr and wr.get("ok") and probe_path.is_file())
    print(f"  {'OK' if okw else 'FAIL'} supervised write")
    if not okw:
        fails += 1
    else:
        try:
            probe_path.unlink()
        except OSError:
            pass

    # Fence ile .md supervised
    md_probe = (
        "görev: projects/cirak-atolyesi cirak rapor_md — "
        "projects/cirak-atolyesi/_smoke_probe.md yaz:\n"
        "```md\n# smoke\nPASS\n```\n· tam ajan"
    )
    wr_md = try_cirak_supervised_write(md_probe, root)
    md_path = root / "projects" / "cirak-atolyesi" / "_smoke_probe.md"
    ok_md = bool(wr_md and wr_md.get("ok") and md_path.is_file() and "PASS" in md_path.read_text(encoding="utf-8"))
    print(f"  {'OK' if ok_md else 'FAIL'} supervised md fence")
    if not ok_md:
        fails += 1
    else:
        try:
            md_path.unlink()
        except OSError:
            pass

    # Kırılgan → red
    red = try_cirak_supervised_write(
        "görev: projects/cirak-atolyesi cirak — boot sırasını değiştir · tam ajan",
        root,
    )
    ok_red = bool(red and red.get("rejected") == "boot_sirasi" and not red.get("ok"))
    print(f"  {'OK' if ok_red else 'FAIL'} kırılgan red")
    if not ok_red:
        fails += 1

    from ilim_assistant.ruzgar_cirak_ders import (
        claim_yesil_gecerli,
        try_cirak_dilim_a_rapor,
        try_cirak_dilim_b_verify,
        try_cirak_dilim_c_cok_satir,
        try_cirak_dilim_d_patch,
        try_cirak_dilim_e_red,
        try_cirak_dilim_f_muhur,
        try_cirak_dilim_g_hibrit,
        try_cirak_dilim_t_tavan,
        try_cirak_tavan_yukselt,
        try_cirak_dilim_0a_bilgi,
        try_cirak_dilim_0b_vizyon,
        try_cirak_dilim_h_yardimci,
        try_cirak_dilim_p_plan,
        try_cirak_dilim_r_proje_oku,
        try_cirak_supervised_write,
        wants_llm_cirak_handoff,
    )

    da = try_cirak_dilim_a_rapor(
        "görev: projects/cirak-atolyesi cirak rapor_md — Dilim A "
        "oz_analiz_raporu_v2.md yaz · tam ajan",
        root,
    )
    v2 = root / "projects" / "cirak-atolyesi" / "oz_analiz_raporu_v2.md"
    ok_a = bool(
        da
        and da.get("ok")
        and v2.is_file()
        and "ruzgar_cirak_ders.py" in v2.read_text(encoding="utf-8")
        and "bilmiyorum" in v2.read_text(encoding="utf-8").lower()
    )
    print(f"  {'OK' if ok_a else 'FAIL'} Dilim A supervised rapor")
    if not ok_a:
        fails += 1

    db = try_cirak_dilim_b_verify(
        "görev: projects/cirak-atolyesi cirak verify_yazdim — Dilim B "
        "projects/cirak-atolyesi/verify_yazdim.py yaz · tam ajan",
        root,
    )
    vb = root / "projects" / "cirak-atolyesi" / "verify_yazdim.py"
    wrong_b = root / "ilim-assistant" / "projects" / "cirak-atolyesi" / "verify_yazdim.py"
    ok_b = bool(
        db
        and db.get("ok")
        and db.get("disk_match")
        and vb.is_file()
        and "PASS cirak-B" in vb.read_text(encoding="utf-8")
        and not wrong_b.is_file()
    )
    # self-run
    if ok_b:
        import subprocess

        pr = subprocess.run(
            [sys.executable, str(vb)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if pr.returncode != 0 or "PASS cirak-B" not in (pr.stdout or ""):
            ok_b = False
    print(f"  {'OK' if ok_b else 'FAIL'} Dilim B yazdım=disk")
    if not ok_b:
        fails += 1

    dc = try_cirak_dilim_c_cok_satir(
        "görev: projects/cirak-atolyesi cirak cok_satir — Dilim C yaz · tam ajan",
        root,
    )
    pc = root / "projects" / "cirak-atolyesi" / "cok_satir_modul.py"
    ok_c = bool(
        dc
        and dc.get("ok")
        and pc.is_file()
        and "def ozet_satir" in pc.read_text(encoding="utf-8")
    )
    print(f"  {'OK' if ok_c else 'FAIL'} Dilim C cok satir")
    if not ok_c:
        fails += 1

    dd = try_cirak_dilim_d_patch(
        "görev: projects/cirak-atolyesi cirak dar_patch — Dilim D hepsi · tam ajan",
        root,
    )
    ok_d = bool(dd and dd.get("ok"))
    print(f"  {'OK' if ok_d else 'FAIL'} Dilim D uc patch")
    if not ok_d:
        fails += 1

    de = try_cirak_dilim_e_red(
        "görev: projects/cirak-atolyesi cirak kirilgan_red — Dilim E "
        "boot sırasını değiştir · tam ajan",
        root,
    )
    ok_e = bool(
        de
        and de.get("ok")
        and de.get("writes_blocked")
        and de.get("rejected") == "boot_sirasi"
    )
    print(f"  {'OK' if ok_e else 'FAIL'} Dilim E kirilgan red")
    if not ok_e:
        fails += 1

    df = try_cirak_dilim_f_muhur(
        "görev: projects/cirak-atolyesi cirak mini_muhur — Dilim F gece_rapor · tam ajan",
        root,
    )
    gece = root / "projects" / "cirak-atolyesi" / "GECE_RAPORU_2026-11-18.md"
    muhur = root / "projects" / "cirak-atolyesi" / "MINI_MUHUR_DILIM_F.md"
    ok_f = bool(df and df.get("ok") and gece.is_file() and muhur.is_file())
    print(f"  {'OK' if ok_f else 'FAIL'} Dilim F muhur+gece")
    if not ok_f:
        fails += 1

    dg = try_cirak_dilim_g_hibrit(
        "görev: projects/cirak-atolyesi cirak hibrit_g — Dilim G hibrit doğruluk · tam ajan",
        root,
    )
    g_mod = root / "projects" / "cirak-atolyesi" / "hibrit_g_modul.py"
    g_ders = root / "projects" / "cirak-atolyesi" / "DERS_G_HIBRIT.md"
    ok_g = bool(
        dg
        and dg.get("ok")
        and dg.get("smoke_ok")
        and g_mod.is_file()
        and g_ders.is_file()
        and not claim_yesil_gecerli(written="", disk_ok=True, smoke_ok=True).get("ok")
    )
    print(f"  {'OK' if ok_g else 'FAIL'} Dilim G hibrit")
    if not ok_g:
        fails += 1

    dt = try_cirak_dilim_t_tavan(
        "görev: projects/cirak-atolyesi cirak tavan_ders — Dilim T tavan ders · tam ajan",
        root,
    )
    t_md = root / "projects" / "cirak-atolyesi" / "TAVAN_DERS.md"
    ok_t = bool(dt and dt.get("ok") and t_md.is_file() and "Tavan şimdi" in t_md.read_text(encoding="utf-8"))
    print(f"  {'OK' if ok_t else 'FAIL'} Dilim T tavan ders")
    if not ok_t:
        fails += 1

    dt_red = try_cirak_dilim_t_tavan(
        "görev: projects/cirak-atolyesi cirak tavan_ders — Dilim T "
        "tavanı kaldır deneme genel saha aç · tam ajan",
        root,
    )
    ok_tr = bool(
        dt_red
        and dt_red.get("ok")
        and dt_red.get("writes_blocked")
        and dt_red.get("rejected") == "tavan_ustu"
    )
    print(f"  {'OK' if ok_tr else 'FAIL'} Dilim T tavan red")
    if not ok_tr:
        fails += 1

    ty_no = try_cirak_tavan_yukselt(
        "görev: projects/cirak-atolyesi cirak tavan_yukselt — izinsiz · tam ajan",
        root,
    )
    ok_ty_no = bool(ty_no and ty_no.get("writes_blocked") and ty_no.get("rejected") == "tavan_ustu")
    print(f"  {'OK' if ok_ty_no else 'FAIL'} tavan_yukselt onaysiz red")
    if not ok_ty_no:
        fails += 1

    ty = try_cirak_tavan_yukselt(
        "görev: projects/cirak-atolyesi cirak tavan_yukselt — mimar onay +1 "
        "atolye_hibrit_ajan_ok · tam ajan",
        root,
    )
    ty_md = root / "projects" / "cirak-atolyesi" / "TAVAN_YUKSELTME_2026-11-18.md"
    from ilim_assistant.ruzgar_cirak_ders import TAVAN_SU_AN as _tavan

    ok_ty = bool(
        ty
        and ty.get("ok")
        and ty_md.is_file()
        and _tavan == "atolye_hibrit_ajan_ok"
        and "genel_saha" in ty_md.read_text(encoding="utf-8").lower()
    )
    print(f"  {'OK' if ok_ty else 'FAIL'} tavan +1 mimar onay")
    if not ok_ty:
        fails += 1

    d0a = try_cirak_dilim_0a_bilgi(
        "görev: projects/cirak-atolyesi cirak bilgi_kopru — Dilim 0A "
        "python def fonksiyon test · tam ajan",
        root,
    )
    k0a = root / "projects" / "cirak-atolyesi" / "BILGI_KOPRU_KANIT.md"
    ok_0a = bool(d0a and d0a.get("ok") and k0a.is_file() and "Kaynak" in k0a.read_text(encoding="utf-8"))
    print(f"  {'OK' if ok_0a else 'FAIL'} Dilim 0A bilgi kopru")
    if not ok_0a:
        fails += 1

    # Prompt köprüsü (usta)
    from ilim_assistant.ruzgar_cirak_bilgi_kopru import build_cirak_bilgi_context
    from ilim_assistant.motorlar.programlama_faz14 import (
        CodeAgentTask,
        build_agent_turn_user_message,
    )

    ctx = build_cirak_bilgi_context(
        "pytest fonksiyon",
        scope_rel="projects/cirak-atolyesi",
        message="görev: cirak",
    )
    tum = build_agent_turn_user_message(
        CodeAgentTask(
            scope_rel="projects/cirak-atolyesi",
            goal="cirak hibrit küçük fonksiyon",
            project_slug="cirak-atolyesi",
        ),
        turn=1,
        max_turns=8,
    )
    ok_inj = "ÇIRAK BİLGİ KÖPRÜSÜ" in tum
    print(f"  {'OK' if ok_inj else 'FAIL'} 0A prompt enjeksiyon")
    if not ok_inj:
        fails += 1
    print(f"  {'OK' if (ctx.get('ok') or ctx.get('block')) else 'FAIL'} 0A context fetch (kaynak veya dürüst boş)")

    d0b = try_cirak_dilim_0b_vizyon(
        "görev: projects/cirak-atolyesi cirak mimar_vizyon — Dilim 0B vizyon özet · tam ajan",
        root,
    )
    k0b = root / "projects" / "cirak-atolyesi" / "OZET_MIMAR_VIZYON.md"
    ok_0b = bool(
        d0b
        and d0b.get("ok")
        and k0b.is_file()
        and "MIMAR_VIZYON.md" in k0b.read_text(encoding="utf-8")
    )
    print(f"  {'OK' if ok_0b else 'FAIL'} Dilim 0B mimar vizyon")
    if not ok_0b:
        fails += 1

    dh = try_cirak_dilim_h_yardimci(
        "görev: projects/cirak-atolyesi cirak yardimci_is — Dilim H katman 2 · tam ajan",
        root,
    )
    ok_h = bool(dh and dh.get("ok") and dh.get("pytest_ok") and dh.get("smoke_ok"))
    print(f"  {'OK' if ok_h else 'FAIL'} Dilim H yardimci+pytest")
    if not ok_h:
        fails += 1

    dp = try_cirak_dilim_p_plan(
        "görev: projects/cirak-atolyesi cirak istek_plan — Dilim P · tam ajan",
        root,
    )
    ok_p = bool(dp and dp.get("ok") and (root / "projects/cirak-atolyesi/PLAN_ISTEK.md").is_file())
    print(f"  {'OK' if ok_p else 'FAIL'} Dilim P istek-plan")
    if not ok_p:
        fails += 1

    dr = try_cirak_dilim_r_proje_oku(
        "görev: projects/cirak-atolyesi cirak proje_oku — Dilim R baştan sona · tam ajan",
        root,
    )
    ok_r = bool(dr and dr.get("ok") and (root / "projects/cirak-atolyesi/PROJE_OKUMA.md").is_file())
    print(f"  {'OK' if ok_r else 'FAIL'} Dilim R proje oku")
    if not ok_r:
        fails += 1

    llm_msg = (
        "görev: projects/cirak-atolyesi cirak — carp_is.py carp fonksiyonu "
        "ve pytest ekle kendin yaz · tam ajan"
    )
    ok_ho = wants_llm_cirak_handoff(llm_msg) and (
        try_cirak_supervised_write(llm_msg, root) is None
    )
    print(f"  {'OK' if ok_ho else 'FAIL'} LLM handoff (supervised None)")
    if not ok_ho:
        fails += 1

    bad = yesil_dilim_icin_ders_gerekli({})
    if bad.get("ok"):
        print("FAIL boş ders yeşil olmamalı")
        fails += 1
    else:
        print("  OK ders yoksa yeşil değil")

    good = yesil_dilim_icin_ders_gerekli(
        {
            "dilim": "1",
            "ders": "profil anlığı çalma",
            "smoke_veya_dosya": "ana_motor_faz_ses_smoke.py",
        }
    )
    if not good.get("ok"):
        print("FAIL dolu ders", good)
        fails += 1
    else:
        print("  OK ders ile yeşil")

    st = cirak_status()
    if "boot_sirasi" not in USTA_KIRILGAN or "tek_dosya_patch" not in CIRAK_GOREV_TURLERI:
        print("FAIL listeler")
        fails += 1
    else:
        print("  OK usta/çırak ayrımı", st.get("version"))

    if fails:
        print(f"FAIL smoke_cirak_ders_d6 fails={fails}")
        return 1
    print("PASS smoke_cirak_ders_d6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
