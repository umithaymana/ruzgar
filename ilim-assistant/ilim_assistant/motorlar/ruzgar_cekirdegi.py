# Created by Ümit & Gökçenur
"""Rüzgar Çekirdeği — ara motor orkestra + hub ile hizalı envanter (F5.3).

Boot sırası kilitli (`.cursorrules` / `_boot_motorlar_anaonce`):
  ana motor → bu çekirdek → ses → video → okuma → mimar → tercüme → hafıza → programlama

Hub (Faz 76) panelli motorlar: programlama, video, hafiza, tercume, ses, mimar, hizir.
İlim/bilim/okuma sohbeti → Ana Motor (`genel`); görsel atölye ayrı (`mimar`).

`build_core_context` tüm motorları her turda yüklemez — yalnızca niyet/flag ile seçilenler
(gereksiz şişme kesilir).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from ilim_assistant.dinamit_gelisme import dinamit_heartbeat
from ilim_assistant.ruzgar_perf import RUZGAR_PERF_MIMAR

CEKIRDEK_VERSION = "ruzgar-cekirdek-f5-v1-2026-11-17"

# Boot sırası (ara motorlar) — kilitli; değiştirmek için Mimar `evet`
ARA_MOTOR_BOOT_ORDER: tuple[str, ...] = (
    "ses",
    "video",
    "okuma",
    "mimar",
    "tercume",
    "hafiza",
    "programlama",
)

# Hub panelli / ROK hedefleri (faz76 `_HUB_MOTORS`)
HUB_MOTOR_IDS: tuple[str, ...] = (
    "programlama",
    "video",
    "hafiza",
    "tercume",
    "ses",
    "mimar",
    "hizir",
)

# F5.4 — yardımcı; hub paneli / ROK hedefi değil
HUB_DISI_YARDIMCILAR: dict[str, str] = {
    "gelisim": "yardimci_hub_disi",
    "duzen": "yardimci_hub_disi",
    "dinamit": "yardimci_hub_disi",
    "dinleme": "ses_stt_alt_katman",  # F5.5
}

# Sohbet kimliği Ana Motor'da (F5.1/F5.2)
SOHBET_ANA_MOTOR_ALIAS: tuple[str, ...] = ("okuma", "bilim", "ilim", "bilgi")


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.replace("ı", "i").replace("İ", "i").lower()


def hub_disi_role(mode_or_id: str) -> str | None:
    """F5.4 — mühür: hub dışı yardımcı mı?"""
    mid = (mode_or_id or "").strip().lower()
    return HUB_DISI_YARDIMCILAR.get(mid)


def is_hub_disi_yardimci(mode_or_id: str) -> bool:
    role = hub_disi_role(mode_or_id)
    return bool(role and role.startswith("yardimci"))


def cekirdek_envanter() -> dict[str, Any]:
    """F5.3 — hub + boot hizalı envanter (öz-bilgi / health)."""
    return {
        "version": CEKIRDEK_VERSION,
        "ana_motor": "ilim_assistant.main_engine",
        "cekirdek": "ilim_assistant.motorlar.ruzgar_cekirdegi",
        "ara_motor_boot_order": list(ARA_MOTOR_BOOT_ORDER),
        "hub_motors": list(HUB_MOTOR_IDS),
        "sohbet_ana_motor_alias": list(SOHBET_ANA_MOTOR_ALIAS),
        "hub_disi_yardimcilar": dict(HUB_DISI_YARDIMCILAR),
        "notlar": {
            "okuma_bilim": "Sohbet/ilim sorusu → genel (Ana Motor); mimar = görsel atölye",
            "hizir": "Boot listesinde yok; hub ROK + çekirdek tool_bridge bağlamı",
            "bilim_motoru": "Külliyat bağlamı — hub paneli değil; okuma_motoru sarmalayıcı",
            "okuma_dal": "Çekirdek pick bilim tercih eder; okuma dalı doğrudan da bağlanır",
            "dinleme": "STT alt katmanı (Ses); çift yüzey yok — /api/stt → ses_stt_pipeline",
        },
    }


def _pick_motors_for_message(
    message: str,
    *,
    motor_flags: dict[str, bool] | None = None,
) -> list[str]:
    """Mesaja göre hangi motor bağlamları yüklensin (şişme kes)."""
    flags = motor_flags or {}
    low = _fold(message)
    picked: list[str] = []

    def _add(mid: str) -> None:
        if mid not in picked:
            picked.append(mid)

    if flags.get("ses") or re.search(
        r"\b(ses|tts|stt|whisper|transkript|metne\s+dok|seslendir|klon)\b", low
    ):
        _add("ses")
    if flags.get("video") or re.search(
        r"\b(video|youtube|indir|ffmpeg|altyazi|kurgu|montaj)\b", low
    ):
        _add("video")
    if flags.get("tercume") or re.search(
        r"\b(cevir|çevir|tercume|tercüme|translate|meal)\b", low
    ):
        _add("tercume")
    if flags.get("programlama") or re.search(
        r"\b(kod|pytest|commit|python|javascript|debug|repo)\b", low
    ):
        _add("programlama")
    if flags.get("mimar") or re.search(
        r"\b(fotograf|fotoğraf|galeri|tasarim|tasarım|restore|sanat)\b", low
    ):
        # Bilgi «nedir» mimar bağlamı yüklemesin
        if not re.search(r"\b(nedir|ne demek|kimdir)\b", low):
            _add("mimar")
    if flags.get("hafiza") or flags.get("bellek") or re.search(
        r"\b(hatirla|hatırla|hafiza|hafıza|gorev|görev)\b", low
    ):
        _add("hafiza")
    if flags.get("hizir") or re.search(r"\b(hizir|hızır|ticaret|pazar)\b", low):
        _add("hizir")
    # İlim/tarih — bilim külliyat bağlamı (hub paneli değil)
    if flags.get("bilim") or re.search(
        r"\b(hadis|ayet|kuran|fikih|tarih|osmanli|osmanlı|siyer|akaid|nedir|kimdir)\b",
        low,
    ):
        _add("bilim")

    # Hiç ipucu yoksa çekirdek iskeleti yeter (boş motor yükleme yok)
    return picked


def _motor_context(mid: str, prompt: str) -> str:
    try:
        if mid == "ses":
            from ilim_assistant.ses_motoru import build_motor_context as fn
        elif mid == "video":
            from ilim_assistant.motorlar.video_motoru import build_motor_context as fn
        elif mid == "tercume":
            from ilim_assistant.tercume_motoru import build_motor_context as fn
        elif mid == "programlama":
            from ilim_assistant.motorlar.programlama_motoru import (
                build_motor_context as fn,
            )
        elif mid == "bilim":
            from ilim_assistant.bilim_motoru import build_motor_context as fn
        elif mid == "mimar":
            from ilim_assistant.mimar_motoru import build_motor_context as fn
        elif mid == "hafiza":
            from ilim_assistant.motorlar.hafiza_motoru import build_motor_context as fn
        elif mid == "hizir":
            # hizir_faz84'te build_motor_context yok — tool_bridge + sabit yüz
            try:
                from ilim_assistant.hizir.tool_bridge import (
                    build_dynamic_operasyon_context,
                )

                dyn = (
                    build_dynamic_operasyon_context(prompt, mode_norm="hizir") or ""
                ).strip()
            except Exception:
                dyn = ""
            head = (
                "[HIZIR MOTORU — Ümit & Gökçenur]\n"
                "Ticaret / pazar / fırsat turu. Uydurma fiyat veya stok yazma; "
                "yalnız araç/bellek çıktısına dayan."
            )
            return (head + ("\n\n" + dyn if dyn else "")).strip()
        elif mid == "okuma":
            # Ölü dal değil: bilim yolu tercih; doğrudan okuma da bağlanır
            from ilim_assistant.okuma_motoru import build_motor_context as fn
        else:
            return ""
        return (fn(prompt) or "").strip()
    except Exception:
        return ""


def build_core_context(
    message: str,
    *,
    motor_flags: dict[str, bool] | None = None,
) -> str:
    """Seçimli orkestra bağlamı — hub ile hizalı, tembel yükleme."""
    prompt = (message or "").strip()
    parts: list[str] = []
    _dh = dinamit_heartbeat()
    if _dh.strip():
        parts.append(_dh.strip())
    parts.append(f"[RUZGAR CEKIRDEGI — {RUZGAR_PERF_MIMAR} · {CEKIRDEK_VERSION}]")
    parts.append(
        "Merkez: Ana Motor + çekirdek. Hub panelleri: "
        + ", ".join(HUB_MOTOR_IDS)
        + ". İlim/okuma/bilim sohbeti Ana Motor'da kalır; mimar görsel atölyedir."
    )
    gelisim_note = hub_disi_role("gelisim")
    if gelisim_note:
        parts.append(
            f"Gelişim mühür: {gelisim_note} — panelli ROK hedefi değil; menü/ajan yardımcısı."
        )

    for mid in _pick_motors_for_message(prompt, motor_flags=motor_flags):
        block = _motor_context(mid, prompt)
        if block:
            parts.append("")
            parts.append(block)
    return "\n".join(parts)
