"""Madde 2.3 — Edge-TTS gerçek ses akışı (``POST /api/tts/stream``).

``/api/tts`` tüm MP3'ü dosyaya yazıp ``FileResponse`` döner (kısa parça için yeterli ama
ilk bayt = tüm parça sentezi). Bu modül aynı Edge sesini **parça parça** (chunked MP3)
gönderir: ilk ses baytı Edge'in ilk audio chunk'ı gelir gelmez istemciye çıkar.

Kapsam (bilinçli dar): yalnız Edge + sohbet profilleri (muhabbet/edip), köşeli etiket
prosodisi yok, klon yok. Uygun olmayan istek → ``AkisYok`` → uç 409 döner; istemci
``/api/tts`` yoluna düşer (mevcut davranış korunur). ``RUZGAR_TTS_AKIS=0`` ile kapanır.
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, AsyncIterator, Callable

VERSION = "ses-tts-akis-v1-2026-11-23"

# Akışta sunulan profiller (alim/tilavet prosodi+durak ister → /api/tts yolu)
_AKIS_PROFILLER = ("muhabbet", "edip", "asistan", "sohbet")


class AkisYok(Exception):
    """Bu istek akışa uygun değil — istemci /api/tts yoluna düşsün."""

    def __init__(self, neden: str):
        super().__init__(neden)
        self.neden = neden


def akis_etkin() -> bool:
    return os.environ.get("RUZGAR_TTS_AKIS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def coz_edge_paket(
    *,
    text: str,
    karakter: str | None = None,
    profil: str | None = None,
    emotion: str | None = None,
    backend: str | None = "auto",
    speaker_rel: str | None = None,
    prosody: bool | None = None,
) -> dict[str, Any]:
    """``api_tts`` Edge dalının (V3 hızlı yol) parametre çözümünün aynısı; yan etkisiz."""
    if not akis_etkin():
        raise AkisYok("akis_kapali")

    from ilim_assistant.dinamit_gelisme import (
        emotion_ses_adjustments,
        infer_emotion_from_text,
        merge_pitch,
    )
    from ilim_assistant.motorlar.ses_klon_motoru import (
        should_use_clone,
        xtts_runtime_available,
    )
    from ilim_assistant.motorlar.ses_motoru import (
        EDGE_VOICES,
        analiz_icerik_yolu,
        edge_pitch_string,
        edge_rate_yuzdesi,
        normalize_ses_karakteri,
    )
    from ilim_assistant.ses_etiket_prosodi import (
        apply_rate_pitch_extras,
        parse_ses_etiketleri,
    )
    from ilim_assistant.tts_service import edge_available, read_ses_ayarlari

    raw = (text or "").strip()
    if len(raw) > 12_000:
        raw = raw[:12_000]
    etiket = parse_ses_etiketleri(raw)
    temiz = (etiket.temiz_metin or "").strip()
    if len(temiz) < 1 or len(raw) < 2:
        raise AkisYok("metin_kisa")
    if etiket.force_prosody:
        raise AkisYok("etiket_prosodi")
    if prosody is True:
        raise AkisYok("prosodi_istendi")
    if not edge_available():
        raise AkisYok("edge_yok")

    emo_ok = {"yorgun", "mutlu", "ciddi", "notr"}
    emo_raw = (emotion or etiket.emotion_hint or "").strip().lower()
    if emo_raw in emo_ok and emo_raw != "notr":
        emotion_kind = emo_raw
    else:
        emotion_kind = infer_emotion_from_text(temiz)
    emo_hiz, emo_huzur, emo_pitch_extra = emotion_ses_adjustments(emotion_kind)

    ayar = read_ses_ayarlari()
    kar = normalize_ses_karakteri(profil or karakter or ayar.get("karakter"))
    if kar.value not in _AKIS_PROFILLER:
        raise AkisYok("profil_" + kar.value)
    icerik = analiz_icerik_yolu(temiz)

    use_clone = should_use_clone(
        backend=backend or "auto",
        karakter=kar.value,
        ayar=ayar,
        speaker_rel=speaker_rel,
    )
    if use_clone and xtts_runtime_available():
        raise AkisYok("klon")

    voice = EDGE_VOICES[kar]
    try:
        from ilim_assistant.ses_s2_prosodi_tavan import (
            ayarla_pitch_string,
            ayarla_rate_string,
            coz_tts_tavan_paketi,
        )

        s2 = coz_tts_tavan_paketi(kar.value, ayar=ayar)
        hiz_s2 = float(s2["hiz"])
        huzur_s2 = float(s2["huzur"])
    except Exception:
        s2 = None
        ayarla_pitch_string = ayarla_rate_string = None  # type: ignore
        hiz_s2 = float(ayar.get("hiz", 0.92))
        huzur_s2 = float(ayar.get("huzur", 0.88))
    hiz_s2 = hiz_s2 * float(emo_hiz) * float(etiket.hiz_carpani)
    huzur_s2 = huzur_s2 * float(emo_huzur) * float(etiket.huzur_carpani)
    rate = edge_rate_yuzdesi(
        karakter=kar,
        icerik=icerik,
        hiz_carpani=hiz_s2,
        huzur_carpani=huzur_s2,
    )
    pitch = edge_pitch_string(kar, icerik)
    if s2 is not None and ayarla_rate_string is not None and ayarla_pitch_string is not None:
        rate = ayarla_rate_string(rate, kar.value)
        pitch = ayarla_pitch_string(pitch, kar.value)
    pitch = merge_pitch(pitch, emo_pitch_extra)
    rate, pitch = apply_rate_pitch_extras(rate, pitch, etiket)

    # V3/D ile aynı hız önceliği (duygu/etiket varsa hesaplanan rate)
    v3_rate = os.environ.get("RUZGAR_TTS_V3_RATE", "").strip()
    if not v3_rate:
        try:
            from ilim_assistant.ses_asama_d import default_rate

            v3_rate = (default_rate() or "").strip()
        except Exception:
            v3_rate = ""
    if not v3_rate or emotion_kind != "notr" or etiket.etiketler:
        v3_rate = rate

    return {
        "text": temiz,
        "voice": voice,
        "rate": v3_rate,
        "pitch": pitch,
        "profil": kar.value,
        "emotion": emotion_kind,
    }


async def edge_akis(
    text: str,
    *,
    voice: str,
    rate: str,
    pitch: str,
    retries: int | None = None,
    iptal_mi: Callable[[], bool] | None = None,
    comm_factory: Callable[..., Any] | None = None,
) -> AsyncIterator[bytes]:
    """Edge MP3 parçalarını geldikçe ver. Yalnız İLK bayttan önce hata/boşsa yeniden dener.

    Tüketici kapanınca (``aclose``) alttaki Edge akışı da kapatılır (kaynak sızmaz).
    ``iptal_mi()`` True olursa akış sessizce biter (tur iptali).
    """
    if retries is None:
        try:
            from ilim_assistant.ses_v3_tts_ilk_byte import v3_retries

            retries = v3_retries()
        except Exception:
            retries = 2
    if comm_factory is None:
        from ilim_assistant.tts_service import edge_tts_import

        edge_tts = edge_tts_import()
        comm_factory = edge_tts.Communicate

    last_err: BaseException | None = None
    for attempt in range(int(retries) + 1):
        if iptal_mi and iptal_mi():
            return
        gen = None
        yielded = False
        try:
            comm = comm_factory(text.strip(), voice, rate=rate, pitch=pitch)
            gen = comm.stream()
            async for chunk in gen:
                if iptal_mi and iptal_mi():
                    return
                if chunk.get("type") != "audio":
                    continue
                data = chunk.get("data") or b""
                if not data:
                    continue
                yielded = True
                yield bytes(data)
            if yielded:
                return
            last_err = RuntimeError("stream:no_audio_chunk")
        except (GeneratorExit, asyncio.CancelledError):
            raise
        except Exception as exc:  # noqa: BLE001
            if yielded:
                # Akış ortasında koptu: istemci kısmi MP3'ü çalar; ikinci başlangıç çift ses olur.
                return
            last_err = exc
        finally:
            if gen is not None:
                try:
                    await gen.aclose()
                except BaseException:  # noqa: BLE001
                    pass
        await asyncio.sleep(0.08 * (attempt + 1))
    raise RuntimeError(f"edge_akis: {type(last_err).__name__ if last_err else 'bos'}: {last_err}"[:200])


async def ilk_parca_ile(
    agen: AsyncIterator[bytes],
) -> tuple[bytes, float, AsyncIterator[bytes]]:
    """İlk baytı bekle (hata varsa HTTP hatasına çevrilebilsin) → (ilk, ms, kalan_akis)."""
    t0 = time.perf_counter()
    first = await agen.__anext__()
    ms = round((time.perf_counter() - t0) * 1000.0, 1)

    async def _devam() -> AsyncIterator[bytes]:
        try:
            yield first
            async for b in agen:
                yield b
        finally:
            try:
                await agen.aclose()  # type: ignore[attr-defined]
            except BaseException:  # noqa: BLE001
                pass

    return first, ms, _devam()
