"""Madde 2.3 — Edge TTS gerçek ses akışı (ses_tts_akis) birim testleri (ağ yok)."""

from __future__ import annotations

import asyncio

import pytest

from ilim_assistant import ses_tts_akis as ak


class _FakeComm:
    """edge_tts.Communicate sahte: scripts = her deneme için olay listesi."""

    kapandi = 0
    denemeler = 0

    def __init__(self, scripts):
        self._scripts = scripts

    def __call__(self, text, voice, rate=None, pitch=None):
        _FakeComm.denemeler += 1
        sc = self._scripts[min(_FakeComm.denemeler - 1, len(self._scripts) - 1)]
        outer = self

        class _C:
            def stream(self_inner):
                async def _g():
                    try:
                        for ev in sc:
                            if isinstance(ev, BaseException):
                                raise ev
                            await asyncio.sleep(0)
                            yield ev
                    finally:
                        _FakeComm.kapandi += 1

                return _g()

        return _C()


def _reset():
    _FakeComm.kapandi = 0
    _FakeComm.denemeler = 0


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


async def _topla(agen):
    out = []
    async for b in agen:
        out.append(b)
    return out


def test_parcalar_geldikce_akar_ve_metadata_atlanir():
    _reset()
    sc = [
        [
            {"type": "WordBoundary", "x": 1},
            {"type": "audio", "data": b"AA"},
            {"type": "audio", "data": b""},
            {"type": "audio", "data": b"BB"},
        ]
    ]
    out = _run(_topla(ak.edge_akis("merhaba", voice="v", rate="+0%", pitch="+0Hz", comm_factory=_FakeComm(sc))))
    assert out == [b"AA", b"BB"]
    assert _FakeComm.kapandi == 1  # alttaki Edge akışı kapandı


def test_ilk_bayttan_once_hata_yeniden_dener():
    _reset()
    sc = [
        [RuntimeError("NoAudioReceived")],
        [{"type": "audio", "data": b"OK"}],
    ]
    out = _run(
        _topla(
            ak.edge_akis("x y", voice="v", rate="+0%", pitch="+0Hz", retries=2, comm_factory=_FakeComm(sc))
        )
    )
    assert out == [b"OK"] and _FakeComm.denemeler == 2


def test_ilk_bayttan_sonra_kopma_ikinci_baslangic_yok():
    _reset()
    sc = [
        [{"type": "audio", "data": b"AA"}, RuntimeError("ag koptu")],
        [{"type": "audio", "data": b"DUPLICATE"}],
    ]
    out = _run(
        _topla(
            ak.edge_akis("x y", voice="v", rate="+0%", pitch="+0Hz", retries=2, comm_factory=_FakeComm(sc))
        )
    )
    assert out == [b"AA"] and _FakeComm.denemeler == 1  # çift ses yok


def test_hepsi_bos_ise_hata_firlatir():
    _reset()
    sc = [[{"type": "WordBoundary"}]]
    with pytest.raises(RuntimeError):
        _run(
            _topla(
                ak.edge_akis("x y", voice="v", rate="+0%", pitch="+0Hz", retries=1, comm_factory=_FakeComm(sc))
            )
        )
    assert _FakeComm.denemeler == 2


def test_iptal_akisi_sessizce_bitirir():
    _reset()
    sayac = {"n": 0}

    def iptal():
        sayac["n"] += 1
        return sayac["n"] > 2

    sc = [[{"type": "audio", "data": bytes([i])} for i in range(10)]]
    out = _run(
        _topla(
            ak.edge_akis(
                "x y", voice="v", rate="+0%", pitch="+0Hz", iptal_mi=iptal, comm_factory=_FakeComm(sc)
            )
        )
    )
    assert len(out) < 10
    assert _FakeComm.kapandi == 1


def test_ilk_parca_ile_ve_kapanis_serbest_birakir():
    _reset()
    sc = [[{"type": "audio", "data": b"1"}, {"type": "audio", "data": b"2"}, {"type": "audio", "data": b"3"}]]

    async def senaryo():
        agen = ak.edge_akis("x y", voice="v", rate="+0%", pitch="+0Hz", comm_factory=_FakeComm(sc))
        first, ms, rest = await ak.ilk_parca_ile(agen)
        assert first == b"1" and ms >= 0
        got = []
        async for b in rest:
            got.append(b)
            break  # tüketici erken ayrıldı
        await rest.aclose()
        return got

    got = _run(senaryo())
    assert got == [b"1"]
    assert _FakeComm.kapandi == 1


def test_coz_edge_paket_uygunsuz_istekler(monkeypatch):
    # akış kapalı
    monkeypatch.setenv("RUZGAR_TTS_AKIS", "0")
    with pytest.raises(ak.AkisYok):
        ak.coz_edge_paket(text="Merhaba nasılsın")
    monkeypatch.delenv("RUZGAR_TTS_AKIS", raising=False)
    # köşeli etiket prosodisi → /api/tts yolu
    with pytest.raises(ak.AkisYok):
        ak.coz_edge_paket(text="[duraksama:300] Merhaba nasılsın", profil="muhabbet")
    # prosodi açıkça istendi
    with pytest.raises(ak.AkisYok):
        ak.coz_edge_paket(text="Merhaba nasılsın", profil="muhabbet", prosody=True)
    # âlim/tilavet → akış dışı
    with pytest.raises(ak.AkisYok) as e:
        ak.coz_edge_paket(text="Merhaba nasılsın, bugün nasılsın", profil="alim")
    assert "alim" in e.value.neden


def test_coz_edge_paket_muhabbet_edge_parametreleri():
    p = ak.coz_edge_paket(text="Merhaba, bugün nasılsın?", profil="muhabbet", backend="edge")
    assert p["voice"].startswith("tr-TR") or "-" in p["voice"]
    assert p["rate"].endswith("%") and (p["pitch"].endswith("Hz") or "st" in p["pitch"])
    assert p["profil"] == "muhabbet"
    assert p["text"].startswith("Merhaba")
