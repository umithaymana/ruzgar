"""O1 — aynı soru aynı Karar kaydını üretir."""
from ilim_assistant.ana_motor_plan import plan_question
from ilim_assistant.ruzgar_o1_karar import karar_uret


def test_ayni_soru_ayni_karar():
    q = "Abdesti bozan şeyler nelerdir?"
    p = plan_question(q, "genel")
    a = karar_uret(q, question_plan=p).as_dict()
    b = karar_uret(q, question_plan=p).as_dict()
    assert a == b
    assert a["niyet"] == "bilgi"
    assert a["uslup"] == "alim"
    assert a["kutuphane"] is True
    assert a["canli"] is False


def test_fizik_sade_ogretmen():
    q = "Fotosentez nedir?"
    p = plan_question(q, "genel")
    k = karar_uret(q, question_plan=p)
    assert k.niyet == "bilgi"
    assert k.uslup == "sade_ogretmen"
    assert k.hedef_motor == "ana_motor"


def test_kapatma(monkeypatch):
    monkeypatch.setenv("RUZGAR_O1_KARAR", "0")
    from ilim_assistant.ruzgar_o1_karar import attach_karar, kestirme_izinli

    orch = {}
    assert attach_karar(orch, "Fotosentez nedir?") is None
    assert "karar" not in orch
    assert kestirme_izinli("akaid", None, "Matris nedir?") is True


def test_capraz_raf_susar():
    from ilim_assistant.ruzgar_o1_karar import karar_uret, kestirme_izinli

    matris = karar_uret("Matris nedir?")
    assert matris.alan == "matematik"
    assert matris.hedef_motor == "ana_motor"
    assert kestirme_izinli("akaid", matris, "Matris nedir?") is False
    assert kestirme_izinli("bilim", matris, "Matris nedir?") is False
    assert kestirme_izinli("programlama", matris, "Matris nedir?") is False

    hukuk_q = "Medeni hukuk ile ceza hukuku arasındaki fark nedir?"
    hukuk = karar_uret(hukuk_q)
    assert hukuk.alan == "hukuk"
    assert kestirme_izinli("kuran", hukuk, hukuk_q) is False
    from ilim_assistant.ruzgar_kuran_anlik import try_kuran_instant_reply

    assert try_kuran_instant_reply(hukuk_q) is None
    mekki = try_kuran_instant_reply("Bakara suresi mekki mi?")
    assert mekki is None or "Mekk" in mekki or "mekk" in mekki.lower() or "Meden" in mekki

    sifat = karar_uret("Sıfat nedir?")
    assert sifat.alan != "akaid"
    assert kestirme_izinli("akaid", sifat, "Sıfat nedir?") is False

    zekat = karar_uret("Zekât kimlere verilir?")
    assert zekat.alan in ("fikh", "din")
    assert kestirme_izinli("fikh", zekat, "Zekât kimlere verilir?") is True
    assert kestirme_izinli("lugat", zekat, "Zekât kimlere verilir?") is False


def test_sohbet_ve_hava_ayri_kalir():
    from ilim_assistant.ruzgar_o1_karar import delege_sonrasi_mod, karar_uret, kestirme_izinli

    selam = karar_uret("selam")
    assert selam.niyet == "sohbet"
    assert kestirme_izinli("sohbet", selam, "selam") is True
    assert kestirme_izinli("fikh", selam, "selam") is False

    hava = karar_uret("Bugün hava nasıl?")
    assert hava.niyet == "canli"
    assert hava.canli is True
    assert kestirme_izinli("hava", hava, "Bugün hava nasıl?") is True
    assert kestirme_izinli("akaid", hava, "Bugün hava nasıl?") is False

    sinus = karar_uret("Sinüs ve kosinüs nedir?", mode_norm="programlama")
    assert sinus.hedef_motor == "ana_motor"
    assert delege_sonrasi_mod("genel", "programlama", sinus) == "genel"
    from ilim_assistant.motorlar.programlama_motoru import maybe_programlama_instant_reply

    assert maybe_programlama_instant_reply("Sinüs ve kosinüs nedir?", "genel") is None
    assert maybe_programlama_instant_reply("Sinüs ve kosinüs nedir?", "programlama") is None


def test_envanter_yonlendirici():
    from ilim_assistant.ruzgar_o1_karar import kestirme_envanteri

    rows = kestirme_envanteri()
    yon = [r for r in rows if r["tur"] == "yonlendirici"]
    assert len(yon) == 6
    assert {r["ad"] for r in yon} == {
        "sohbet",
        "hava",
        "programlama",
        "lugat",
        "kutuphane",
        "web",
    }
