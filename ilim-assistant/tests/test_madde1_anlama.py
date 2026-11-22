# Created by Ümit & Gökçenur
"""Madde 1 — ezber kapalı + hava genellemesi + niyet iskeleti."""

from __future__ import annotations

import os

import pytest


def test_selam_ezber_kapali():
    from ilim_assistant.chat_fast_lane import try_instant_reply
    from ilim_assistant.ruzgar_ezber_instant import ezber_instant_enabled

    assert ezber_instant_enabled() is False
    assert try_instant_reply("selam", "genel") is None
    assert try_instant_reply("nasılsın", "genel") is None


def test_selam_ezber_acilinca_doner():
    from ilim_assistant.chat_fast_lane import try_instant_reply

    prev = os.environ.get("RUZGAR_EZBER_INSTANT")
    os.environ["RUZGAR_EZBER_INSTANT"] = "1"
    try:
        # modül env'i runtime okuyor
        r = try_instant_reply("selam", "genel")
        assert r and "konuşmaya hazırım" in r
    finally:
        if prev is None:
            os.environ.pop("RUZGAR_EZBER_INSTANT", None)
        else:
            os.environ["RUZGAR_EZBER_INSTANT"] = prev


def test_niyet_selam_sohbet():
    from ilim_assistant.ruzgar_niyet_karari import decide_intent

    d = decide_intent("selam")
    assert d.kind == "sohbet"
    assert d.confidence >= 0.8


def test_niyet_hava_yer_yok():
    from ilim_assistant.ruzgar_niyet_karari import decide_intent

    d = decide_intent("hava nasıl")
    assert d.kind == "canli_hava"
    assert d.needs_clarify is True
    assert d.place is None


def test_niyet_hava_oslo():
    from ilim_assistant.ruzgar_niyet_karari import decide_intent

    d = decide_intent("Oslo hava durumu")
    assert d.kind == "canli_hava"
    assert d.place and "oslo" in d.place.lower()


def test_weather_no_default_istanbul():
    from ilim_assistant.weather_live import (
        compute_live_weather_outcome,
        fetch_live_weather_context,
    )

    ctx, inst = compute_live_weather_outcome("hava nasıl")
    assert ctx == ""
    assert inst and "hangi yer" in inst.lower()
    assert fetch_live_weather_context(None) == ""


@pytest.mark.network
def test_weather_oslo_live():
    from ilim_assistant.weather_live import compute_live_weather_outcome

    _ctx, inst = compute_live_weather_outcome("Oslo hava durumu")
    assert inst
    assert "Oslo" in inst or "bulamad" in inst.lower()


# ---------------------------------------------------------------------------
# Kısa söz anlayışı (tamam / evet / sağ ol / ok …)
# ---------------------------------------------------------------------------

_KISA_EVET = [
    "tamam", "Tamam.", "tamam abi", "ya tamam", "tamam tamam", "ok", "okey", "peki",
    "Evet", "hayır", "olur", "sağ ol", "Sağol abi", "teşekkürler", "Çok teşekkürler",
    "eyvallah", "görüşürüz", "hı", "harika", "süper", "anladım", "iyi geceler",
]
_KISA_HAYIR = [
    "Oslo hava", "hava nasıl", "tamam yap", "işlem liste", "bunu kaydet",
    "tamam ama şunu da yap", "evet hatırla", "sağ ol bir de şunu anlat",
    "hayır ben öyle demedim ki", "nasılsın", "selam", "peki ya yarın?", "erzurum",
]


@pytest.mark.parametrize("msg", _KISA_EVET)
def test_kisa_soz_taninir(msg):
    from ilim_assistant.ruzgar_kisa_soz import looks_like_short_ack

    assert looks_like_short_ack(msg) is True


@pytest.mark.parametrize("msg", _KISA_HAYIR)
def test_kisa_soz_yanlis_pozitif_yok(msg):
    from ilim_assistant.ruzgar_kisa_soz import looks_like_short_ack

    assert looks_like_short_ack(msg) is False


def test_kisa_soz_kapatilabilir():
    from ilim_assistant.ruzgar_kisa_soz import looks_like_short_ack

    prev = os.environ.get("RUZGAR_KISA_SOZ")
    os.environ["RUZGAR_KISA_SOZ"] = "0"
    try:
        assert looks_like_short_ack("tamam") is False
    finally:
        if prev is None:
            os.environ.pop("RUZGAR_KISA_SOZ", None)
        else:
            os.environ["RUZGAR_KISA_SOZ"] = prev


@pytest.mark.parametrize("msg", ["tamam", "teşekkürler", "sağ ol", "ok", "evet", "görüşürüz"])
def test_kisa_soz_netlestirme_sorusu_uretmez(msg):
    from ilim_assistant.ana_motor_plan import plan_question

    p = plan_question(msg, "genel", {})
    assert p.primary == "gundelik"
    assert p.ambiguous is False
    assert not p.clarification
    assert p.use_ilim_rag is False and p.prefer_web is False


@pytest.mark.parametrize("msg", ["tamam", "sağ ol", "ok", "peki"])
def test_kisa_soz_dogal_sohbet_turu(msg):
    from ilim_assistant.ana_motor_plan import is_casual_conversation_turn

    assert is_casual_conversation_turn(msg, "genel", None) is True


@pytest.mark.parametrize("msg", ["tamam", "evet", "olur", "hayır"])
def test_kisa_soz_hub_programlamaya_kacmaz(msg, tmp_path):
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target

    target, meta = resolve_hub_target(msg, None, str(tmp_path))
    assert target == "genel", meta


def test_kisa_soz_tek_beyin_bulanik_hafiza_yok():
    from ilim_assistant.ruzgar_tek_beyin import tek_beyin_plan_override

    hist = [{"role": "user", "content": "H7 test notu bugün C planı tamam"}]
    assert tek_beyin_plan_override("tamam", hist) is None


def test_gercek_komut_hala_calisir(tmp_path):
    """Kısa söz süzgeci gerçek işlem emrini yutmamalı."""
    from ilim_assistant.motorlar.programlama_faz98 import wants_umit_gate

    assert wants_umit_gate("işlem iste: mkdir projects/x") is True


# ---------------------------------------------------------------------------
# Sohbet gecikmesi: hedged (gecikmeli paralel) ilk-token yarışı
# ---------------------------------------------------------------------------


def _gen(pieces, *, start_delay=0.0, gap=0.0, raise_exc=None):
    import time

    def _f():
        if start_delay:
            time.sleep(start_delay)
        if raise_exc:
            raise raise_exc
        for p in pieces:
            if gap:
                time.sleep(gap)
            yield p

    return _f


def _err(p):
    return p.startswith("HATA")


def test_hedge_hizli_ilk_ikinciyi_baslatmaz():
    import time
    from ilim_assistant.llm_brain import _hedged_stream

    started = []

    def second():
        started.append(1)
        yield "ikinci"

    t0 = time.time()
    out = "".join(_hedged_stream([_gen(["a", "b"]), second], 1.0, _err))
    assert out == "ab"
    assert not started
    assert time.time() - t0 < 0.8


def test_hedge_takilan_ilk_ikinci_kazanir():
    import time
    from ilim_assistant.llm_brain import _hedged_stream

    t0 = time.time()
    out = "".join(
        _hedged_stream([_gen(["yavas"], start_delay=2.0), _gen(["hizli", "!"])], 0.3, _err)
    )
    dt = time.time() - t0
    assert out == "hizli!"
    assert dt < 1.2


def test_hedge_ilk_hata_verirse_hemen_ikinci():
    import time
    from ilim_assistant.llm_brain import _hedged_stream

    t0 = time.time()
    out = "".join(
        _hedged_stream([_gen(["HATA: 503"]), _gen(["tamam"])], 5.0, _err)
    )
    assert out == "tamam"
    assert time.time() - t0 < 1.5


def test_hedge_exception_ikinciye_gecer():
    from ilim_assistant.llm_brain import _hedged_stream

    out = "".join(
        _hedged_stream([_gen([], raise_exc=RuntimeError("x")), _gen(["ok"])], 5.0, _err)
    )
    assert out == "ok"


def test_hedge_ikisi_de_hata_ilk_hatayi_verir():
    from ilim_assistant.llm_brain import _hedged_stream

    out = list(_hedged_stream([_gen(["HATA: bir"]), _gen(["HATA: iki"])], 0.2, _err))
    assert out == ["HATA: bir"]


def test_hedge_bos_parca_icerik_sayilmaz():
    from ilim_assistant.llm_brain import _hedged_stream

    out = "".join(_hedged_stream([_gen(["  ", "\n", "merhaba"])], 0.5, _err))
    assert out == "merhaba"


def test_hedge_kazanan_parcalari_karismaz():
    """Kazanan belli olduktan sonra kaybedenin parçaları çıktıya sızmamalı."""
    from ilim_assistant.llm_brain import _hedged_stream

    out = "".join(
        _hedged_stream(
            [_gen(["A1", "A2", "A3"], start_delay=0.5, gap=0.05), _gen(["B1", "B2", "B3"], gap=0.05)],
            0.2,
            _err,
        )
    )
    assert out in ("B1B2B3", "A1A2A3")


def test_hedge_kapali_env():
    import os
    from ilim_assistant.llm_brain import casual_gemini_hedge_sec

    prev = os.environ.get("RUZGAR_CASUAL_GEMINI_HEDGE_SEC")
    os.environ["RUZGAR_CASUAL_GEMINI_HEDGE_SEC"] = "0"
    try:
        assert casual_gemini_hedge_sec() is None
    finally:
        if prev is None:
            os.environ.pop("RUZGAR_CASUAL_GEMINI_HEDGE_SEC", None)
        else:
            os.environ["RUZGAR_CASUAL_GEMINI_HEDGE_SEC"] = prev
