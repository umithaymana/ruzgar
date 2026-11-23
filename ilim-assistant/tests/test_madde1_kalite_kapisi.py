"""Madde 1.5 — kalite kapısı (ince): boş/whitespace çıktı «başarılı» sayılmaz, zincir sonraki beyne geçer."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ilim_assistant import llm_brain as lb


def _ep(pid: str, provider: str = "ollama") -> SimpleNamespace:
    return SimpleNamespace(profile_id=pid, provider=provider, model=pid)


@pytest.fixture()
def zincir(monkeypatch):
    kullanilan: list[str] = []
    monkeypatch.setattr(lb, "_defer_cold_heavy", lambda c: list(c))
    monkeypatch.setattr(lb, "note_brain_used", lambda pid, provider="": kullanilan.append(pid))
    monkeypatch.setattr(lb, "_mark_cloud_rate_limit", lambda *a, **k: None)

    def kur(yanitlar: dict[str, list[str]]):
        def sahte(ep, *a, **k):
            for p in yanitlar[ep.profile_id]:
                yield p

        monkeypatch.setattr(lb, "_stream_endpoint", sahte)

    def calistir(zincir_idleri: list[str]):
        return "".join(
            lb._stream_brain_chain_loop(
                [_ep(i) for i in zincir_idleri],
                "sistem",
                "kullanıcı",
                prior_messages=None,
                mode_norm="genel",
                coding_mode=False,
                message="merhaba nasılsın",
                use_turn_budget=False,
            )
        )

    return SimpleNamespace(kur=kur, calistir=calistir, kullanilan=kullanilan)


def test_bos_cikti_sonraki_beyne_gecer(zincir):
    zincir.kur({"yerel": ["", "  ", "\n"], "bulut": ["Merhaba Ümit abi, iyiyim."]})
    assert zincir.calistir(["yerel", "bulut"]) == "Merhaba Ümit abi, iyiyim."
    assert zincir.kullanilan == ["bulut"]


def test_bas_bosluk_atlanir_sonra_gelen_icerik_kabul(zincir):
    zincir.kur({"yerel": ["", "Selam", " Ümit abi"], "bulut": ["YEDEK"]})
    assert zincir.calistir(["yerel", "bulut"]) == "Selam Ümit abi"
    assert zincir.kullanilan == ["yerel"]


def test_ilk_beyin_icerik_verirse_ikinciye_gecilmez(zincir):
    zincir.kur({"yerel": ["Tamam."], "bulut": ["YEDEK"]})
    assert zincir.calistir(["yerel", "bulut"]) == "Tamam."
    assert zincir.kullanilan == ["yerel"]


def test_hepsi_bossa_dogal_hata_cevabi_doner(zincir):
    zincir.kur({"yerel": [""], "bulut": ["   "]})
    cikti = zincir.calistir(["yerel", "bulut"])
    assert cikti.strip()  # sessiz boş cevap yok
    assert zincir.kullanilan == []
