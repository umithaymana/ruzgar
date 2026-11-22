"""Donma düzeltmesi: soğuk ağır yerel model tur bütçesini yutmasın."""

from __future__ import annotations

import pytest

from ilim_assistant import llm_brain as lb
from ilim_assistant import llm_ollama as lo


def _ep(pid: str, provider: str = "ollama", model: str = "") -> lb.BrainEndpoint:
    return lb.BrainEndpoint(
        profile_id=pid,
        label=pid,
        model=model or {"denge": "qwen2.5:14b", "hizli": "llama3.2:3b"}.get(pid, pid),
        provider=provider,  # type: ignore[arg-type]
    )


def _ids(chain):
    return [e.profile_id for e in chain]


@pytest.fixture(autouse=True)
def _temiz(monkeypatch):
    monkeypatch.delenv("RUZGAR_COLD_DEFER", raising=False)
    lb._RESIDENT_CACHE["ts"] = 0.0
    lb._RESIDENT_CACHE["val"] = None
    yield
    lb._RESIDENT_CACHE["ts"] = 0.0
    lb._RESIDENT_CACHE["val"] = None


def _resident(monkeypatch, value):
    monkeypatch.setattr(lo, "ollama_resident_models", lambda timeout_sec=1.0: value)


CHAIN = [
    _ep("denge"),
    _ep("hizli"),
    _ep("gemini", "gemini"),
    _ep("groq", "openai_compat"),
]


def test_soguk_denge_sona_alinir(monkeypatch):
    _resident(monkeypatch, {"llama3.2:3b"})
    assert _ids(lb._defer_cold_heavy(list(CHAIN))) == ["hizli", "gemini", "groq", "denge"]


def test_bilgi_sorusunda_kucuk_yerel_buluttan_sonra(monkeypatch):
    _resident(monkeypatch, {"llama3.2:3b"})
    out = lb._defer_cold_heavy(list(CHAIN), small_local_after_cloud=True)
    assert _ids(out) == ["gemini", "groq", "hizli", "denge"]


def test_sicak_denge_sirayi_bozmaz(monkeypatch):
    _resident(monkeypatch, {"qwen2.5:14b", "llama3.2:3b"})
    assert _ids(lb._defer_cold_heavy(list(CHAIN), small_local_after_cloud=True)) == _ids(CHAIN)


def test_ollama_bilinmiyorsa_sira_korunur(monkeypatch):
    _resident(monkeypatch, None)
    assert _ids(lb._defer_cold_heavy(list(CHAIN), small_local_after_cloud=True)) == _ids(CHAIN)


def test_yalniz_yerel_zincirde_hizli_once(monkeypatch):
    _resident(monkeypatch, set())
    out = lb._defer_cold_heavy([_ep("denge"), _ep("hizli")], small_local_after_cloud=True)
    assert _ids(out) == ["hizli", "denge"]  # bulut yok → hizli yine önde


def test_tek_uc_ve_kapali_anahtar(monkeypatch):
    _resident(monkeypatch, set())
    assert _ids(lb._defer_cold_heavy([_ep("denge")])) == ["denge"]
    monkeypatch.setenv("RUZGAR_COLD_DEFER", "0")
    assert _ids(lb._defer_cold_heavy(list(CHAIN))) == _ids(CHAIN)


def test_hicbir_uc_silinmez(monkeypatch):
    _resident(monkeypatch, set())
    out = lb._defer_cold_heavy(list(CHAIN), small_local_after_cloud=True)
    assert sorted(_ids(out)) == sorted(_ids(CHAIN))


def test_tur_siniri():
    assert lb._ollama_turn_cap(15, is_last=False) == 7.5
    assert lb._ollama_turn_cap(22, is_last=False) == 11.0
    assert lb._ollama_turn_cap(100, is_last=False) == 12.0
    assert lb._ollama_turn_cap(2, is_last=False) == 6.0  # alt taban
    assert lb._ollama_turn_cap(15, is_last=True) == 15.5
    assert lb._ollama_turn_cap(9999, is_last=True) == 22.0  # bütçe yok → makul tavan


def test_casual_siniri_makul():
    assert lb._casual_ollama_cap_value("12") == 12.0
    assert lb._casual_ollama_cap_value("900") == 22.0
    assert lb._casual_ollama_cap_value("x") == 12.0


def test_model_bellekte_eslesme():
    res = {"qwen2.5:14b", "llama3:latest"}
    assert lo.ollama_model_resident("qwen2.5:14b", res)
    assert lo.ollama_model_resident("llama3", res)  # etiketsiz = :latest
    assert not lo.ollama_model_resident("llama3.2:3b", res)
    assert not lo.ollama_model_resident("qwen2.5:14b", None)


def test_okuma_siniri_istege_ozel_ve_env_bagimsiz(monkeypatch):
    seen: dict = {}

    class _Resp:
        status_code = 200
        encoding = "utf-8"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def iter_lines(self, decode_unicode=False):
            return iter([])

    class _Sess:
        def post(self, url, **kw):
            seen["timeout"] = kw.get("timeout")
            return _Resp()

    monkeypatch.setattr(lo, "_http_session_singleton", lambda: _Sess())
    monkeypatch.delenv("RUZGAR_OLLAMA_READ_TIMEOUT_SEC", raising=False)
    list(lo.chat_completion_stream("s", "u", model="m", read_timeout_cap=7.5))
    assert seen["timeout"][1] == 7.5
    list(lo.chat_completion_stream("s", "u", model="m", read_timeout_cap=0.5))
    assert seen["timeout"][1] == 3.0  # taban
    list(lo.chat_completion_stream("s", "u", model="m"))
    assert seen["timeout"][1] == 900.0  # sınır yoksa eski davranış
