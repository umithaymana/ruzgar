# Created by Ümit & Gökçenur
"""Yerel TTS: Edge-TTS (öncelikli), isteğe bağlı Coqui. Çıktıya mimar metadata.

RUZGAR_TTS_MP=1 (varsayılan): MP3 üretimi ayrı süreçte (ProcessPool); ana FastAPI thread’i bloklanmaz.
"""

from __future__ import annotations

import asyncio
import atexit
import json
import multiprocessing as mp
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

_ILIM_ROOT = Path(__file__).resolve().parents[1]
_SES_AYAR = _ILIM_ROOT / ".ruzgar_ses_ayarlari.json"

_MIMAR = "Ümit & Gökçenur"

_TTS_POOL: ProcessPoolExecutor | None = None
_TTS_ATEXIT_DONE = False


def _atexit_shutdown_tts_pool() -> None:
    global _TTS_POOL
    p = _TTS_POOL
    if p is not None:
        p.shutdown(wait=False)
        _TTS_POOL = None


def get_tts_process_pool() -> ProcessPoolExecutor:
    global _TTS_POOL, _TTS_ATEXIT_DONE
    if _TTS_POOL is None:
        n = max(1, int(os.environ.get("RUZGAR_TTS_MP_WORKERS", "1")))
        ctx = mp.get_context("spawn")
        _TTS_POOL = ProcessPoolExecutor(max_workers=n, mp_context=ctx)
        if not _TTS_ATEXIT_DONE:
            atexit.register(_atexit_shutdown_tts_pool)
            _TTS_ATEXIT_DONE = True
    return _TTS_POOL


def _tts_pool_smoke() -> int:
    """Alt süreç havuzunu uyandır (ilk istek gecikmesini startup’a al). Ümit & Gökçenur."""
    return 1


def prime_tts_process_pool() -> None:
    if os.environ.get("RUZGAR_TTS_MP", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return
    if not edge_available():
        return
    pool = get_tts_process_pool()
    pool.submit(_tts_pool_smoke).result(timeout=45)


def _edge_synth_mp3_bytes(job: tuple[str, str, str, str]) -> bytes:
    """
    Alt işlem: Edge-TTS → ham mp3 baytı (pickle için üst düzey fonksiyon).
    Ümit & Gökçenur paralel seslendirme.
    """
    text, voice, rate, pitch = job
    import tempfile

    import edge_tts

    async def _run() -> bytes:
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            comm = edge_tts.Communicate(text.strip(), voice, rate=rate, pitch=pitch)
            await comm.save(path)
            return Path(path).read_bytes()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    return asyncio.run(_run())


async def synthesize_edge_mp3_in_process(
    text: str,
    *,
    voice: str,
    rate: str,
    pitch: str,
    meta: dict[str, Any],
) -> Path:
    """Ana süreçte metadata; sentez alt süreçte (GIL dışı ağ/CPU)."""
    from starlette.concurrency import run_in_threadpool

    pool = get_tts_process_pool()
    to = float(os.environ.get("RUZGAR_TTS_MP_TIMEOUT", "120"))

    def _sync() -> bytes:
        return pool.submit(
            _edge_synth_mp3_bytes,
            (text.strip(), voice, rate, pitch),
        ).result(timeout=to)

    data = await run_in_threadpool(_sync)
    fd, tmp = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    out = Path(tmp)
    out.write_bytes(data)
    meta_full = {**meta, "engine": "edge-tts", "mimarlar": _MIMAR, "tts_process": True}
    apply_mp3_metadata(out, meta_full)
    return out


def edge_tts_import():
    import edge_tts  # type: ignore

    return edge_tts


def coqui_available() -> bool:
    try:
        from TTS.api import TTS  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def edge_available() -> bool:
    try:
        edge_tts_import()
        return True
    except Exception:
        return False


def read_ses_ayarlari() -> dict[str, Any]:
    from ilim_assistant.motorlar.ses_motoru import normalize_ses_karakteri

    defaults = {
        "karakter": "asistan",
        "hiz": 0.92,
        "huzur": 0.88,
        "prosody": True,
        "durak": 1.0,
        "tilavet": True,
        "referans": {},
        "mimarlar": _MIMAR,
        "created_by": _MIMAR,
    }
    if not _SES_AYAR.is_file():
        return dict(defaults)
    try:
        cur = json.loads(_SES_AYAR.read_text(encoding="utf-8"))
        cur["karakter"] = normalize_ses_karakteri(
            str(cur.get("karakter", "asistan"))
        ).value
        if "prosody" not in cur:
            cur["prosody"] = True
        if "durak" not in cur:
            cur["durak"] = 1.0
        if "referans" not in cur or not isinstance(cur.get("referans"), dict):
            cur["referans"] = {}
        if "tilavet" not in cur:
            cur["tilavet"] = True
        cur["mimarlar"] = _MIMAR
        cur["created_by"] = _MIMAR
        return cur
    except Exception:
        return dict(defaults)


def write_ses_ayarlari(data: dict[str, Any]) -> Path:
    cur = read_ses_ayarlari()
    cur.update(data)
    cur["mimarlar"] = _MIMAR
    cur["created_by"] = _MIMAR
    _SES_AYAR.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    return _SES_AYAR


def apply_mp3_metadata(path: Path, meta: dict[str, Any]) -> None:
    """ID3: sanatçı, başlık, metin içinde tam JSON kimlik."""
    try:
        from mutagen.id3 import ID3, TIT2, TPE1, COMM, TXXX  # type: ignore
        from mutagen.mp3 import MP3  # type: ignore
    except ImportError:
        return

    try:
        audio = MP3(str(path))
    except Exception:
        return
    try:
        if audio.tags is None:
            audio.add_tags()
    except Exception:
        try:
            audio.tags = ID3()
        except Exception:
            return

    audio.tags.delall("TIT2")
    audio.tags.delall("TPE1")
    audio.tags.add(
        TIT2(encoding=3, text=f"RÜZGAR TTS — Created by {_MIMAR}")
    )
    audio.tags.add(TPE1(encoding=3, text=f"RÜZGAR — {_MIMAR}"))
    body = json.dumps(meta, ensure_ascii=False)
    audio.tags.add(COMM(encoding=3, lang="tur", desc="RuzgarMeta", text=body))
    audio.tags.add(TXXX(encoding=3, desc="Mimarlar", text=_MIMAR))
    try:
        audio.save()
    except Exception:
        pass


async def _edge_save(
    text: str,
    out_path: Path,
    voice: str,
    rate: str,
    pitch: str,
) -> None:
    edge_tts = edge_tts_import()
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await comm.save(str(out_path))


async def synthesize_edge_mp3(
    text: str,
    *,
    voice: str,
    rate: str,
    pitch: str,
    meta: dict[str, Any],
) -> Path:
    """Geçici mp3 üretir; ID3 metadata’da Ümit & Gökçenur kimliği."""
    fd, tmp = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    out = Path(tmp)
    await _edge_save(text.strip(), out, voice, rate, pitch)
    meta_full = {**meta, "engine": "edge-tts", "mimarlar": _MIMAR}
    apply_mp3_metadata(out, meta_full)
    return out


async def list_edge_voices_tr() -> list[dict[str, Any]]:
    """Türkçe neural sesler (Edge), TTS seçimi için."""
    try:
        edge_tts = edge_tts_import()
        all_v = await edge_tts.list_voices()
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for v in all_v:
        loc = str(v.get("Locale", ""))
        if loc.startswith("tr-"):
            out.append(
                {
                    "name": v.get("ShortName", ""),
                    "locale": loc,
                    "gender": v.get("Gender", ""),
                }
            )
    return out


def try_coqui_wav(
    text: str,
    *,
    model_name: str | None = None,
    meta: dict[str, Any],
) -> Path | None:
    """
    Coqui TTS (opsiyonel; `pip install TTS` ve model indirmesi gerekir).
    RUZGAR_COQUI_MODEL ile model adı.
    """
    if not coqui_available():
        return None
    try:
        from TTS.api import TTS  # type: ignore
    except Exception:
        return None

    model = (
        model_name
        or os.environ.get("RUZGAR_COQUI_MODEL", "").strip()
        or "tts_models/tr/common-voice/glow-tts"
    )
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    out = Path(tmp)
    try:
        use_gpu = torch_gpu_if_any()
        tts = TTS(model_name=model, progress_bar=False, gpu=use_gpu)
        tts.tts_to_file(text=text, file_path=str(out))
        meta_full = {**meta, "engine": "coqui-tts", "mimarlar": _MIMAR, "model": model}
        side = out.with_suffix(".ruzgar_meta.json")
        side.write_text(json.dumps(meta_full, ensure_ascii=False, indent=2), encoding="utf-8")
        return out
    except Exception:
        try:
            out.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def torch_gpu_if_any() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False


async def _synth_chunk_mp3_bytes(
    text: str,
    *,
    voice: str,
    rate: str,
    pitch: str,
) -> bytes:
    """Tek parça Edge-TTS (metadata yok — prosody birleştirme)."""
    from starlette.concurrency import run_in_threadpool

    pool = get_tts_process_pool()
    to = float(os.environ.get("RUZGAR_TTS_MP_TIMEOUT", "120"))

    def _sync() -> bytes:
        return pool.submit(
            _edge_synth_mp3_bytes,
            (text.strip(), voice, rate, pitch),
        ).result(timeout=to)

    return await run_in_threadpool(_sync)


async def synthesize_edge_mp3_prosody(
    text: str,
    *,
    voice: str,
    rate: str,
    pitch: str,
    meta: dict[str, Any],
    icerik_yolu: str,
    hiz_carpani: float = 0.92,
    huzur_carpani: float = 0.88,
    durak_carpani: float = 1.0,
) -> Path:
    """
    Faz S1: metni parçalara böl, parçalar arası sessizlik ekle, MP3 birleştir.
    FFmpeg yoksa tek parça senteze düşer.
    """
    from ilim_assistant.motorlar.ses_motoru import IcerikYolu
    from ilim_assistant.motorlar.ses_prosody import (
        DurakTuru,
        durak_suresi_ms,
        metin_parcala,
        prosody_ozet,
    )
    from ilim_assistant.video_ffmpeg import (
        concat_audio_files,
        ffmpeg_available,
        generate_silence_mp3,
    )

    try:
        icerik = IcerikYolu(icerik_yolu)
    except ValueError:
        icerik = IcerikYolu.genel

    parcalar = metin_parcala(text, icerik)
    if len(parcalar) <= 1 and (
        not parcalar or parcalar[0].sonraki_durak == DurakTuru.yok
    ):
        return await synthesize_edge_mp3_in_process(
            text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            meta=meta,
        )

    if not ffmpeg_available():
        birlesik = " ".join(p.metin for p in parcalar)
        return await synthesize_edge_mp3_in_process(
            birlesik,
            voice=voice,
            rate=rate,
            pitch=pitch,
            meta={**meta, "prosody_fallback": "no_ffmpeg"},
        )

    gecici: list[Path] = []
    birlestir: list[Path] = []
    try:
        for i, parca in enumerate(parcalar):
            chunk_bytes = await _synth_chunk_mp3_bytes(
                parca.metin,
                voice=voice,
                rate=rate,
                pitch=pitch,
            )
            fd, tmp_chunk = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            chunk_path = Path(tmp_chunk)
            chunk_path.write_bytes(chunk_bytes)
            gecici.append(chunk_path)
            birlestir.append(chunk_path)

            if parca.sonraki_durak == DurakTuru.yok:
                continue
            pause_ms = durak_suresi_ms(
                parca.sonraki_durak,
                icerik=icerik,
                durak_carpani=durak_carpani,
                huzur_carpani=huzur_carpani,
            )
            if pause_ms <= 0:
                continue
            fd2, tmp_sil = tempfile.mkstemp(suffix=".mp3")
            os.close(fd2)
            sil_path = Path(tmp_sil)
            generate_silence_mp3(sil_path, pause_ms)
            gecici.append(sil_path)
            birlestir.append(sil_path)

        if len(birlestir) == 1:
            out_single = birlestir[0]
            fd_out, tmp_out = tempfile.mkstemp(suffix=".mp3")
            os.close(fd_out)
            final = Path(tmp_out)
            final.write_bytes(out_single.read_bytes())
        else:
            fd_out, tmp_out = tempfile.mkstemp(suffix=".mp3")
            os.close(fd_out)
            final = Path(tmp_out)
            try:
                concat_audio_files(birlestir, final, copy_streams=True)
            except Exception:
                concat_audio_files(birlestir, final, copy_streams=False)

        ozet = prosody_ozet(parcalar)
        meta_full = {
            **meta,
            "engine": "edge-tts-prosody",
            "mimarlar": _MIMAR,
            "tts_process": True,
            "prosody": True,
            "prosody_parcalar": ozet.get("parcalar"),
            "prosody_durak": ozet.get("durak_sayisi"),
        }
        apply_mp3_metadata(final, meta_full)
        return final
    finally:
        for p in gecici:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass


async def synthesize_clone_mp3(
    text: str,
    *,
    karakter: str,
    language: str = "tr",
    speaker_rel: str | None = None,
    meta: dict[str, Any],
    ayar: dict[str, Any] | None = None,
) -> Path:
    """Faz S4: XTTS klon ses → MP3 (ffmpeg)."""
    from ilim_assistant.motorlar.ses_klon_motoru import (
        coz_referans_yolu,
        synthesize_clone_wav,
        wav_to_mp3,
    )

    ref = coz_referans_yolu(karakter, ayar=ayar, speaker_rel=speaker_rel)
    if ref is None:
        raise FileNotFoundError(
            "Klon referans sesi yok. Ses atölyesinden 30–120 sn .wav yükleyin "
            "(arsiv/ses-referans/{alim|edip|asistan}.wav)."
        )

    wav_tmp: Path | None = None

    def _run() -> Path:
        nonlocal wav_tmp
        wav_tmp = synthesize_clone_wav(text, ref, language=language)
        fd, mp3_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        mp3_out = Path(mp3_path)
        wav_to_mp3(wav_tmp, mp3_out)
        meta_full = {
            **meta,
            "engine": "xtts-clone",
            "mimarlar": _MIMAR,
            "referans": ref.name,
            "language": language,
        }
        apply_mp3_metadata(mp3_out, meta_full)
        return mp3_out

    from starlette.concurrency import run_in_threadpool

    try:
        return await run_in_threadpool(_run)
    finally:
        if wav_tmp and wav_tmp.is_file():
            try:
                wav_tmp.unlink(missing_ok=True)
            except OSError:
                pass


async def synthesize_tilavet_mp3(
    text: str,
    *,
    karakter: str = "alim",
    meta: dict[str, Any],
    ayar: dict[str, Any] | None = None,
) -> Path:
    """Faz S5: tilavet parcalama + uzun durak + Arapca/TR vakur Edge ses."""
    from ilim_assistant.motorlar.ses_prosody import DurakTuru, prosody_ozet
    from ilim_assistant.motorlar.ses_tilavet import (
        edge_ses_tilavet,
        tespit_tilavet_modu,
        tilavet_durak_ms,
        tilavet_parcala,
        tilavet_rate_pitch,
    )
    from ilim_assistant.video_ffmpeg import (
        concat_audio_files,
        ffmpeg_available,
        generate_silence_mp3,
    )

    ay = ayar or read_ses_ayarlari()
    mod = tespit_tilavet_modu(text)
    voice = edge_ses_tilavet(text, karakter=karakter, mod=mod)
    rate, pitch = tilavet_rate_pitch(
        text,
        karakter=karakter,
        hiz_carpani=float(ay.get("hiz", 0.88)),
        huzur_carpani=float(ay.get("huzur", 0.82)),
    )
    parcalar = tilavet_parcala(text, mod)
    if not parcalar:
        raise ValueError("Tilavet metni bos.")

    if len(parcalar) <= 1 and parcalar[0].sonraki_durak == DurakTuru.yok:
        return await synthesize_edge_mp3_in_process(
            text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            meta={**meta, "engine": "edge-tts-tilavet", "tilavet_mod": mod.value},
        )

    if not ffmpeg_available():
        birlesik = " ".join(p.metin for p in parcalar)
        return await synthesize_edge_mp3_in_process(
            birlesik,
            voice=voice,
            rate=rate,
            pitch=pitch,
            meta={**meta, "engine": "edge-tts-tilavet", "tilavet_fallback": "no_ffmpeg"},
        )

    gecici: list[Path] = []
    birlestir: list[Path] = []
    durak_c = float(ay.get("durak", 1.0))
    huzur = float(ay.get("huzur", 0.82))
    try:
        for parca in parcalar:
            chunk_bytes = await _synth_chunk_mp3_bytes(
                parca.metin,
                voice=voice,
                rate=rate,
                pitch=pitch,
            )
            fd, tmp_chunk = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            chunk_path = Path(tmp_chunk)
            chunk_path.write_bytes(chunk_bytes)
            gecici.append(chunk_path)
            birlestir.append(chunk_path)

            if parca.sonraki_durak == DurakTuru.yok:
                continue
            pause_ms = tilavet_durak_ms(
                parca.sonraki_durak,
                mod=mod,
                durak_carpani=durak_c,
                huzur_carpani=huzur,
            )
            if pause_ms <= 0:
                continue
            fd2, tmp_sil = tempfile.mkstemp(suffix=".mp3")
            os.close(fd2)
            sil_path = Path(tmp_sil)
            generate_silence_mp3(sil_path, pause_ms)
            gecici.append(sil_path)
            birlestir.append(sil_path)

        fd_out, tmp_out = tempfile.mkstemp(suffix=".mp3")
        os.close(fd_out)
        final = Path(tmp_out)
        try:
            concat_audio_files(birlestir, final, copy_streams=True)
        except Exception:
            concat_audio_files(birlestir, final, copy_streams=False)

        ozet = prosody_ozet(parcalar)
        meta_full = {
            **meta,
            "engine": "edge-tts-tilavet",
            "mimarlar": _MIMAR,
            "tts_process": True,
            "tilavet": True,
            "tilavet_mod": mod.value,
            "tilavet_parcalar": ozet.get("parcalar"),
            "edge_voice": voice,
        }
        apply_mp3_metadata(final, meta_full)
        return final
    finally:
        for p in gecici:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
