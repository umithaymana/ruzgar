# Created by Ümit & Gökçenur
"""
Rüzgar dinleme (STT) — SpeechRecognition + isteğe bağlı PyAudio canlı mikrofon.

- HTTP: tarayıcı ses dosyası (`/api/stt`) — arka planda thread pool (FastAPI threadpool).
- Yerel: `record_and_transcribe_pyaudio` — bloklayan dinleme ayrı iş parçacığında.

Hata ayıklama imzası: Ümit & Gökçenur — tüm RuntimeError mesajlarında tutarlı.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable, TypeVar

MIMAR_IMZA = "Ümit & Gökçenur"
MODUL_KIMLIK = {"motor": "dinleme_motoru", "created_by": MIMAR_IMZA, "proje": "RÜZGAR"}

# Dinleme işi ana isteği kilitlemesin: PyAudio kaydı bu havuzda — CPU’da paralel STT (Ümit & Gökçenur Işık Hızı)
def _stt_pool_size() -> int:
    try:
        return max(2, int(os.environ.get("RUZGAR_STT_CPU_WORKERS", "4")))
    except ValueError:
        return 4


_STT_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=_stt_pool_size(),
    thread_name_prefix="ruzgar_stt_umit_gokcenur_",
)

T = TypeVar("T")


def kimlik_json() -> str:
    return json.dumps(MODUL_KIMLIK, ensure_ascii=False)


def _ruzygar_stt_disabled() -> bool:
    return os.environ.get("RUZGAR_STT", "").strip().lower() in ("0", "false", "no")


def speech_recognition_available() -> bool:
    if _ruzygar_stt_disabled():
        return False
    try:
        import speech_recognition  # noqa: F401

        return True
    except ImportError:
        return False


def pyaudio_available() -> bool:
    try:
        import pyaudio  # noqa: F401

        return True
    except ImportError:
        return False


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def stt_backend_available() -> bool:
    """Whisper veya SpeechRecognition yolu kullanılabilir mi (STT tamamen kapalı değilse)."""
    if _ruzygar_stt_disabled():
        return False
    try:
        from ilim_assistant.stt_whisper import whisper_available

        if whisper_available():
            return True
    except Exception:
        pass
    return speech_recognition_available()


def verify_audio_imports() -> dict[str, Any]:
    """
    pyaudio / speech_recognition sistem erişimi — yükleme ve PyAudio cihaz sayısı.
    Ümit & Gökçenur hata ayıklama çıktısı.
    """
    out: dict[str, Any] = {
        "created_by": MIMAR_IMZA,
        "speech_recognition": {"ok": False, "error": None},
        "pyaudio": {"ok": False, "error": None, "input_devices": None},
    }
    try:
        import speech_recognition as sr  # noqa: F401

        out["speech_recognition"]["ok"] = True
    except Exception as e:
        out["speech_recognition"]["error"] = str(e)
    try:
        import pyaudio

        pa = pyaudio.PyAudio()
        try:
            n = pa.get_device_count()
            out["pyaudio"]["input_devices"] = n
            out["pyaudio"]["ok"] = True
        finally:
            pa.terminate()
    except Exception as e:
        out["pyaudio"]["error"] = str(e)
    return out


def probe_default_input_device() -> dict[str, Any]:
    """
    Varsayılan giriş cihazı bilgisi — PortAudio/PyAudio erişim testi (Ümit & Gökçenur).
    """
    out: dict[str, Any] = {
        "ok": False,
        "created_by": MIMAR_IMZA,
        "default_input": None,
        "error": None,
    }
    try:
        import pyaudio

        pa = pyaudio.PyAudio()
        try:
            info = pa.get_default_input_device_info()
            out["ok"] = True
            out["default_input"] = {
                "index": info.get("index"),
                "name": info.get("name"),
                "channels": info.get("maxInputChannels"),
            }
        finally:
            pa.terminate()
    except Exception as e:
        out["error"] = str(e)
        out["hint"] = (
            "PortAudio eksik olabilir: Windows’ta önceden derlenmiş PyAudio wheel veya "
            "https://www.portaudio.com/ — " + MIMAR_IMZA
        )
    return out


def engines_snapshot() -> dict[str, Any]:
    """Sağlık uçları için kısa özet."""
    try:
        from ilim_assistant.stt_whisper import whisper_available

        w = whisper_available()
    except Exception:
        w = False
    snap = {
        "whisper": w,
        "speech_recognition": speech_recognition_available(),
        "pyaudio": pyaudio_available(),
        "ffmpeg_path": ffmpeg_available(),
        "created_by": MIMAR_IMZA,
    }
    try:
        snap["audio_imports"] = verify_audio_imports()
        snap["default_input_probe"] = probe_default_input_device()
    except Exception as e:
        snap["audio_probe_error"] = str(e)
    return snap


def _to_wav_16k_mono(src: Path) -> Path:
    """webm/ogg/mp4 → geçici wav (ffmpeg)."""
    fd, out = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    out_p = Path(out)
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(src),
                "-ar",
                "16000",
                "-ac",
                "1",
                str(out_p),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return out_p
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        try:
            out_p.unlink(missing_ok=True)
        except OSError:
            pass
        raise RuntimeError(
            "Ses dosyası WAV'a çevrilemedi (ffmpeg PATH'te olmalı: "
            "https://ffmpeg.org/)"
        ) from e


def run_in_stt_worker(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Bloklayan STT/PyAudio işini worker iş parçacığında çalıştır (UI/ana döngüyü kilitleme)."""
    fut = _STT_EXECUTOR.submit(fn, *args, **kwargs)
    return fut.result(timeout=600)


def transcribe_file_speech_recognition(
    path: str | Path,
    language: str | None = "tr",
) -> tuple[str, str]:
    """
    SpeechRecognition ile dosyadan metin (Google Web Speech API — internet gerekir).
    thread_name: arama çağrısı ağ I/O — istekler thread pool istemcisinde de güvenli.
    """
    import speech_recognition as sr

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    tmp_wav: Path | None = None
    wav_path = path
    try:
        if path.suffix.lower() != ".wav":
            if not ffmpeg_available():
                raise RuntimeError(
                    "WebM/OGG için ffmpeg gerekli veya WAV gönderin."
                )
            tmp_wav = _to_wav_16k_mono(path)
            wav_path = tmp_wav

        r = sr.Recognizer()
        with sr.AudioFile(str(wav_path)) as source:
            audio = r.record(source)

        lc = (language or "tr").strip().lower()
        lang_code = "tr-TR" if lc.startswith("tr") else (lc or "tr-TR")
        try:
            text = r.recognize_google(audio, language=lang_code)
        except sr.UnknownValueError:
            text = ""
        except sr.RequestError as e:
            raise RuntimeError(
                f"SpeechRecognition ağ hatası ({MIMAR_IMZA}): {e}"
            ) from e
        return (text or "").strip(), lang_code
    finally:
        if tmp_wav and tmp_wav.is_file():
            try:
                tmp_wav.unlink()
            except OSError:
                pass


def _record_and_transcribe_pyaudio_impl(
    duration_s: float,
    language: str,
) -> str:
    """Senkron: PyAudio + SR — yalnızca worker veya doğrudan betikten çağrılmalı."""
    import speech_recognition as sr

    if not pyaudio_available():
        raise RuntimeError(f"PyAudio kurulu değil — pip install pyaudio ({MIMAR_IMZA})")

    r = sr.Recognizer()
    try:
        r.pause_threshold = float(
            os.environ.get("RUZGAR_SR_PAUSE_SEC", "0.8")
        )
    except ValueError:
        r.pause_threshold = 0.8
    last_err: Exception | None = None
    audio = None
    for idx in [None] + list(range(32)):
        try:
            mic = (
                sr.Microphone(device_index=idx)
                if idx is not None
                else sr.Microphone()
            )
            with mic as source:
                try:
                    r.adjust_for_ambient_noise(
                        source, duration=min(0.5, float(duration_s) * 0.2)
                    )
                except Exception:
                    pass
                audio = r.listen(
                    source,
                    timeout=min(12.0, float(duration_s) + 4.0),
                    phrase_time_limit=float(duration_s),
                )
            break
        except sr.WaitTimeoutError as e:
            raise RuntimeError(f"Dinleme zaman aşımı ({MIMAR_IMZA})") from e
        except Exception as e:
            last_err = e
            continue
    else:
        raise RuntimeError(
            f"Mikrofon açılamadı / dinlenemedi ({MIMAR_IMZA} STT): {last_err}"
        ) from last_err

    lang = language if "-" in language else f"{language}-{language.upper()}"
    if lang.startswith("tr"):
        lang = "tr-TR"
    try:
        text = r.recognize_google(audio, language=lang)
    except sr.UnknownValueError:
        text = ""
    except sr.RequestError as e:
        raise RuntimeError(f"SpeechRecognition ağ hatası ({MIMAR_IMZA}): {e}") from e
    return (text or "").strip()


def record_and_transcribe_pyaudio(
    duration_s: float = 6.0,
    language: str = "tr-TR",
    *,
    use_background_thread: bool = True,
) -> str:
    """
    PyAudio + SpeechRecognition ile yerel mikrofon.
    use_background_thread=True: ana iş parçacığını kilitlemez (worker'da çalışır).
    """
    if use_background_thread:
        return run_in_stt_worker(
            _record_and_transcribe_pyaudio_impl,
            duration_s,
            language,
        )
    return _record_and_transcribe_pyaudio_impl(duration_s, language)


def transcribe_with_best_backend(
    path: str | Path,
    language: str | None = "tr",
) -> tuple[str, str]:
    """
    Önce faster-whisper; yok veya hata durumunda SpeechRecognition.
    (HTTP katmanında zaten threadpool'da çağrılır — burada çift thread oluşmasın diye senkron.)
    Sonra: stt_postprocess.cilala_stt_metni — niyet/akış cilası, O(n), ek ağ gecikmesi yok.
    """
    from ilim_assistant.stt_postprocess import cilala_stt_metni

    path = Path(path)
    text = ""
    lang = (language or "tr-TR").strip() or "tr-TR"
    whisper_ok = False
    try:
        from ilim_assistant.stt_whisper import transcribe_file, whisper_available

        if whisper_available() and not _ruzygar_stt_disabled():
            text, lang = transcribe_file(path, language)
            whisper_ok = True
    except Exception:
        whisper_ok = False
    if not whisper_ok:
        if not speech_recognition_available():
            raise RuntimeError(
                f"STT yok: pip install faster-whisper ve/veya SpeechRecognition ({MIMAR_IMZA})"
            )
        text, lang = transcribe_file_speech_recognition(path, language)
    return cilala_stt_metni(text, lang), lang
