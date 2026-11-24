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
    from ilim_assistant.ruzgar_o1_karar import attach_karar

    orch = {}
    assert attach_karar(orch, "Fotosentez nedir?") is None
    assert "karar" not in orch
