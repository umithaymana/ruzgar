"""Whisper GPU varsayılanı + çalışma anı CPU yedeği (cublas DLL bulunamazsa)."""

from __future__ import annotations

import types

import numpy as np
import pytest

from ilim_assistant import stt_whisper as sw


class _Seg:
    def __init__(self, text: str):
        self.text = text
        self.start = 0.0
        self.end = 1.0
        self.avg_logprob = -0.1
        self.no_speech_prob = 0.01


class _KotuGpu:
    """Yükleme başarılı, ilk çözümlemede (yineleme anında) cublas hatası."""

    def transcribe(self, audio, **kw):
        def _gen():
            raise RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")
            yield  # pragma: no cover

        return _gen(), types.SimpleNamespace(language="tr", language_probability=0.99, duration=1.0)


class _IyiCpu:
    def transcribe(self, audio, **kw):
        return iter([_Seg("Merhaba Rüzgar")]), types.SimpleNamespace(
            language="tr", language_probability=0.99, duration=1.0
        )


@pytest.fixture(autouse=True)
def _temiz(monkeypatch):
    monkeypatch.setattr(sw, "_CPU_ZORLA", False)
    monkeypatch.setattr(sw, "_MODEL", None)
    monkeypatch.setattr(sw, "_MODEL_META", {})
    yield
    sw._CPU_ZORLA = False


def test_varsayilan_cihaz_auto(monkeypatch):
    monkeypatch.delenv("RUZGAR_WHISPER_DEVICE", raising=False)
    monkeypatch.delenv("RUZGAR_WHISPER_COMPUTE", raising=False)
    dev, ctype = sw.resolve_whisper_device_compute()
    assert dev in ("cuda", "cpu")
    assert ctype in ("float16", "int8")
    if dev == "cpu":
        assert ctype == "int8"


def test_cpu_env_her_zaman_cpu(monkeypatch):
    monkeypatch.setenv("RUZGAR_WHISPER_DEVICE", "cpu")
    assert sw.resolve_whisper_device_compute() == ("cpu", "int8")


def test_cpu_zorla_bayragi(monkeypatch):
    monkeypatch.setenv("RUZGAR_WHISPER_DEVICE", "auto")
    monkeypatch.setattr(sw, "_CPU_ZORLA", True)
    assert sw.resolve_whisper_device_compute() == ("cpu", "int8")


def test_gpu_calisma_hatasinda_cpuya_duser(monkeypatch, tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"x")
    monkeypatch.setattr(sw, "_decode_audio_f32", lambda *a, **k: np.zeros(16000, dtype=np.float32))

    def _get_model():
        if sw._CPU_ZORLA:
            sw._MODEL_META = {"device": "cpu"}
            return _IyiCpu()
        sw._MODEL_META = {"device": "cuda"}
        return _KotuGpu()

    monkeypatch.setattr(sw, "get_model", _get_model)
    monkeypatch.setattr(sw, "unload_model", lambda: {"ok": True})
    res = sw.transcribe_file_detailed(wav, "tr")
    assert "Rüzgar" in res.text
    assert sw._CPU_ZORLA is True


def test_cpu_hatasi_yutulmaz(monkeypatch, tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"x")
    monkeypatch.setattr(sw, "_decode_audio_f32", lambda *a, **k: np.zeros(16000, dtype=np.float32))

    def _get_model():
        sw._MODEL_META = {"device": "cpu"}
        return _KotuGpu()

    monkeypatch.setattr(sw, "get_model", _get_model)
    with pytest.raises(RuntimeError):
        sw.transcribe_file_detailed(wav, "tr")
