# Created by Ümit & Gökçenur
"""F9 — Öz-bilgi & dürüst kapasite: kart + canlı envanter; LLM uydurmaz."""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

OZ_BILGI_VERSION = "ruzgar-oz-bilgi-f9-v1.2-motor-bag-2026-11-17"
MIMAR = "Ümit & Gökçenur"

_CACHE: dict[str, Any] = {"ts": 0.0, "inv": None}
_CACHE_TTL_SEC = 45.0


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.replace("ı", "i").replace("İ", "i").lower()


def _pkg() -> Path:
    return Path(__file__).resolve().parent.parent


# --- F9.2 dürüst kapasite kartı (sabit) ---
KAPASITE_KARTI: dict[str, Any] = {
    "version": OZ_BILGI_VERSION,
    "kim": {
        "ad": "Rüzgar",
        "mimar": MIMAR,
        "ozet": "Bu bilgisayarda çalışan kişisel asistan; sohbet, kütüphane, ses, atölyeler.",
    },
    "yapabilir": [
        "Doğal sohbet (yerel Ollama öncelikli, bulut yedek)",
        "Yerel kütüphane / RAG / Şamile shard araması (İlim-A)",
        "Ses: STT (Whisper) + TTS (Edge; klon onaylıysa)",
        "Mobil sürekli sohbet (HTTPS mic + VAD)",
        "Hub ile atölye yönlendirme (programlama, video, tercüme, mimar…)",
        "Hafızaya güvenli öğrenme (learn_trust kapısı)",
    ],
    "yapamaz": [
        "Serbest dosya silme / izinsiz sistem komutu",
        "Kaynaksız kesin tarih-sayı uydurma (ilimde raftan usable yoksa öğret der)",
        "Profesyonel uzun metraj film / %100 video stüdyosu",
        "Halka açık kimlik+TLS ürünü (şimdilik bilinçli kapalı)",
        "Her şehir için özel hardcode coğrafya tablosu",
    ],
    "kuvvetli": [
        "Yerel kütüphane + local-first sohbet",
        "Ana Motor hub (bilgi atölyeye kaçmasın)",
        "Timeout / miss dürüst dili",
    ],
    "zayif": [
        "Programlama tavanı ~%70 (dürüst not)",
        "Video derin editör olgun değil",
        "Hızır canlı pazar API yok",
        "İnsan-üstü TTS yok — Edge + ölçülebilir gecikme",
        "Sahne/OSM bu planda dondurulmuş / ayrı yol",
    ],
    "tavan": {
        "programlama": "~%70",
        "video": "temel indir/kes/altyazı; süper editör yok",
        "ses": "Edge TTS + Whisper; klon isteğe bağlı onay",
        "mobil": "sürekli VAD + barge-in; saha testi şart",
    },
}


# --- F9.3 motor hüner kartları ---
MOTOR_KARTLARI: list[dict[str, Any]] = [
    {
        "id": "ana",
        "ad": "Ana Motor",
        "hub": True,
        "boot": "ilk",
        "huner": "Sohbet, plan, RAG, hub yönlendirme",
        "guclu": "Bilgi turu, kütüphane sözleşmesi",
        "zayif": "Atölye derin işleri yardımcıya bırakır",
        "ornek": "fotosentez nedir",
    },
    {
        "id": "ses",
        "ad": "Ses",
        "hub": True,
        "boot": 1,
        "huner": "STT/TTS, profil Alim/Edip/Asistan, tilavet, tek yüz handoff",
        "guclu": "Edge first-byte / VAD mobil / sohbet→ses atölye",
        "zayif": "İnsan klonu varsayılan değil",
        "ornek": "seste: merhaba",
        "tek_yuz": True,
    },
    {
        "id": "video",
        "ad": "Video",
        "hub": True,
        "boot": 2,
        "huner": "İndir, kes, altyazı, dublaj hattı",
        "guclu": "Temel ffmpeg boruları",
        "zayif": "V3+ süper editör yok",
        "ornek": "şu youtube'u indir",
    },
    {
        "id": "okuma",
        "ad": "Okuma",
        "hub": False,
        "boot": 3,
        "bag": "kismi_kasten",
        "huner": "Arşiv / metin türü; ilim sohbeti Ana Motor'da (yetim değil)",
        "guclu": "Arşiv durumu; bilinçli hub dışı sohbet",
        "zayif": "Bağımsız hub hedefi yok — kasıtlı (F5)",
        "ornek": "arsiv durumu",
        "tek_yuz": False,
    },
    {
        "id": "mimar",
        "ad": "Mimar",
        "hub": True,
        "boot": 4,
        "huner": "Fotoğraf / tasarım / sanat atölyesi, tek yüz",
        "guclu": "Görsel işler; ilim sohbeti Ana Motor'da",
        "zayif": "İlim «nedir» buraya düşmez",
        "ornek": "mimarda: logo",
        "tek_yuz": True,
    },
    {
        "id": "tercume",
        "ad": "Tercüme",
        "hub": True,
        "boot": 5,
        "huner": "Eser çeviri / OCR / batch",
        "guclu": "Atölye iş akışı",
        "zayif": "Her dil çiftinde mükemmel değil",
        "ornek": "bu sayfayı çevir",
    },
    {
        "id": "hafiza",
        "ad": "Hafıza",
        "hub": True,
        "boot": 6,
        "huner": "Hatırla, görev, sohbet arşivi, tek yüz panel",
        "guclu": "Kalıcı kartlar; panel handoff kayıt yazmaz",
        "zayif": "Zehirli otomatik kayıt kapılı (F3)",
        "ornek": "hafızada: not",
        "tek_yuz": True,
    },
    {
        "id": "programlama",
        "ad": "Programlama",
        "hub": True,
        "boot": 7,
        "huner": "Kod, pytest, git, onaylı patch",
        "guclu": "Kapılı eylem",
        "zayif": "Tavan ~%70; serbest ajan yok",
        "ornek": "pytest geçir",
    },
    {
        "id": "hizir",
        "ad": "Hızır",
        "hub": True,
        "boot": None,
        "huner": "Ticaret / tarama yardımcı, tek yüz panel",
        "guclu": "Hub ROK + sohbet→panel handoff",
        "zayif": "Canlı pazar API yok (bilinçli)",
        "ornek": "hizirda: not",
        "tek_yuz": True,
    },
]


def kapasite_karti() -> dict[str, Any]:
    return dict(KAPASITE_KARTI)


def motor_kartlari() -> list[dict[str, Any]]:
    try:
        from ilim_assistant.motorlar.ruzgar_cekirdegi import cekirdek_envanter

        env = cekirdek_envanter()
    except Exception:
        env = {}
    hub = set(env.get("hub_motors") or [])
    boot = list(env.get("ara_motor_boot_order") or [])
    out = []
    for m in MOTOR_KARTLARI:
        row = dict(m)
        if m["id"] in hub:
            row["hub_canli"] = True
        if m["id"] in boot:
            row["boot_index"] = boot.index(m["id"]) + 1
        out.append(row)
    return out


def _rag_chunk_count() -> int | None:
    try:
        idx = _pkg() / ".rag_index" / "manifest.json"
        if not idx.is_file():
            return None
        data = json.loads(idx.read_text(encoding="utf-8"))
        for k in ("num_chunks", "chunks", "n_chunks"):
            if k in data:
                return int(data[k])
        return None
    except Exception:
        return None


def _shamela_summary() -> dict[str, Any]:
    try:
        from ilim_assistant.shamela_rag_shards import public_status

        st = public_status()
        return {
            "ready": int(st.get("categories_ready") or 0),
            "total": int(st.get("categories_total") or 0),
            "pending_n": len(st.get("pending") or []),
        }
    except Exception as exc:
        return {"error": str(exc)[:120]}


def _genel_hafiza_count() -> int | None:
    try:
        p = _pkg() / "ruzgar_genel_hafiza.json"
        if not p.is_file():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            for k in ("kayitlar", "items", "entries", "bilgiler"):
                if isinstance(data.get(k), list):
                    return len(data[k])
            return len(data)
        return None
    except Exception:
        return None


def _learned_md_count() -> int | None:
    try:
        d = _pkg() / "knowledge" / "learned"
        if not d.is_dir():
            return 0
        return sum(1 for _ in d.glob("*.md"))
    except Exception:
        return None


def canli_envanter(*, force: bool = False) -> dict[str, Any]:
    """F9.1 / F9.6 — canlı sayılar; kısa TTL önbellek."""
    now = time.time()
    if (
        not force
        and _CACHE.get("inv") is not None
        and now - float(_CACHE.get("ts") or 0) < _CACHE_TTL_SEC
    ):
        return dict(_CACHE["inv"])
    inv: dict[str, Any] = {
        "version": OZ_BILGI_VERSION,
        "ts": now,
        "rag_chunks": _rag_chunk_count(),
        "shamela": _shamela_summary(),
        "genel_hafiza": _genel_hafiza_count(),
        "learned_md": _learned_md_count(),
        "cekirdek": {},
        "stt_surface": {},
        "warmup": {},
    }
    try:
        from ilim_assistant.motorlar.ruzgar_cekirdegi import cekirdek_envanter

        inv["cekirdek"] = cekirdek_envanter()
    except Exception:
        pass
    try:
        from ilim_assistant.dinleme_motoru import stt_surface_status

        inv["stt_surface"] = stt_surface_status()
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_tur_teshis_f0 import warmup_snapshot

        inv["warmup"] = warmup_snapshot()
    except Exception:
        pass
    _CACHE["ts"] = now
    _CACHE["inv"] = inv
    return dict(inv)


def invalidate_oz_bilgi_cache() -> None:
    _CACHE["ts"] = 0.0
    _CACHE["inv"] = None


# --- F9.4 niyet ---
_OZ_PATTERNS: list[tuple[str, str]] = [
    ("kimlik", r"\b(sen kimsin|seni kim (yapti|kurdu)|umit.*gokcenur|ruzgar (nedir|kim))\b"),
    ("kapasite", r"\b(neler (biliyorsun|yapabilirsin)|ne yapamazsin|yapamazsin|yapabilir misin)\b"),
    ("kuvvet_zayif", r"\b(zayif|kuvvetli|iyi oldugun|az bildigin|cok bildigin|guclu yan|zayif yan)\b"),
    ("kutuphane", r"\b(kutuphanende ne|hafizanda ne|ne tur (bilgi|eser)|rag.*kac|samile.*kac)\b"),
    ("motorlar", r"\b(motorlarin (neler|kac)|kac\s+motor|motorun\s+var|her motorun|hangi motora|okuma ile mimar)\b"),
    ("mod", r"\b(hangi moddasin|su an hangi mod|modun ne)\b"),
    ("kaynak", r"\b(cevabi nereden|nereden buldun|raftan mi|bulut mu|yerel (model|mi))\b"),
    ("web", r"\b(internete bak(iyor musun)?|ne zaman (web|internet)|offline ne)\b"),
    ("ses_mobil", r"\b(sesli sohbet|mobil.*sohbet|surekli sohbet|nasil baglanirim|hangi port)\b"),
    ("ogrenme", r"\b(bana bir sey ogretebilir|nasil hatirlar|bugun ne ogrendin|neler ogrendin)\b"),
    ("limit", r"\b(limitlerin|serbest kod|dosya silme|uydurma yasagi)\b"),
    ("warmup", r"\b(ilik misin|isiniyor|warmup|isirin|soguk musun)\b"),
    ("yardim", r"\b(^\\?$|hub durum|orkestra ozeti|kendini tara|durumunu soyle|yardim)\b"),
]


def classify_oz_bilgi_intent(message: str) -> str | None:
    low = _fold(message)
    if not low.strip() or len(low) > 220:
        return None
    for name, pat in _OZ_PATTERNS:
        if re.search(pat, low):
            return name
    return None


def looks_like_oz_bilgi_question(message: str) -> bool:
    return classify_oz_bilgi_intent(message) is not None


def format_oz_bilgi_reply(message: str, *, mode: str = "genel") -> str | None:
    """LLM’siz dürüst cevap; None = bu kapıdan değil."""
    intent = classify_oz_bilgi_intent(message)
    if not intent:
        return None
    inv = canli_envanter()
    kap = kapasite_karti()
    motors = motor_kartlari()

    if intent == "kimlik":
        return (
            f"Ben **Rüzgar**’ım — {MIMAR}'nın ortak projesi. "
            "Bu bilgisayarda çalışan kişisel asistanım; hava/esinti değilim."
        )
    if intent == "kapasite":
        yap = " · ".join(kap["yapabilir"][:5])
        yapma = " · ".join(kap["yapamaz"][:4])
        return (
            f"Ümit abi, **yapabildiklerim:** {yap}.\n\n"
            f"**Yapamadıklarım / bilerek kapalı:** {yapma}.\n\n"
            f"(Kart {OZ_BILGI_VERSION})"
        )
    if intent == "kuvvet_zayif":
        return (
            "**Kuvvetli:** "
            + " · ".join(kap["kuvvetli"])
            + "\n\n**Zayıf / tavan:** "
            + " · ".join(kap["zayif"])
            + f"\n\nProgramlama tavanı: {kap['tavan']['programlama']}."
        )
    if intent == "kutuphane":
        sh = inv.get("shamela") or {}
        return (
            "Kütüphane (canlı, abartısız):\n"
            f"· Ana RAG chunk: {inv.get('rag_chunks') if inv.get('rag_chunks') is not None else 'bilinmiyor'}\n"
            f"· Şamile: {sh.get('ready', '?')}/{sh.get('total', '?')} kategori ready"
            f" (bekleyen ~{sh.get('pending_n', '?')})\n"
            f"· Genel hafıza kayıt: {inv.get('genel_hafiza') if inv.get('genel_hafiza') is not None else '?'}\n"
            f"· learned/*.md: {inv.get('learned_md') if inv.get('learned_md') is not None else '?'}\n"
            "İlimde bilgi sahibi raftır; usable yoksa uydurmam."
        )
    if intent == "motorlar":
        lines = [f"Hub/boot motor envanteri ({len(motors)} kart):"]
        for m in motors:
            boot = m.get("boot_index") or m.get("boot") or "—"
            lines.append(
                f"· **{m['ad']}** — {m['huner']} (boot:{boot}; "
                f"{'hub' if m.get('hub') else 'hub-dışı/sohbet'}). "
                f"Güçlü: {m['guclu']}. Zayıf: {m['zayif']}."
            )
        lines.append(
            "\n**Okuma vs Mimar:** Okuma/ilim sohbeti Ana Motor'da kalır; "
            "Mimar görsel atölyedir (foto/tasarım)."
        )
        return "\n".join(lines)
    if intent == "mod":
        return f"Şu an sohbet modu ipucu: **{(mode or 'genel').strip() or 'genel'}**. Atölye işi söylersen hub yönlendirir."
    if intent == "kaynak":
        return (
            "Cevap sırası (genel): kendi hafıza → yerel RAG → Ollama → Gemini/Groq → web (niyetli). "
            "Rozet: yerel / bulut / raftan. İlimde usable raftan yoksa öğret derim; bilgi uydurmam."
        )
    if intent == "web":
        return (
            "İnternete her turda bakmam. Güncel/canlı veya «webden bak» dersen öne alınır; "
            "ansiklopedik «nedir» tek başına web demek değil (local-first)."
        )
    if intent == "ses_mobil":
        st = inv.get("stt_surface") or {}
        return (
            f"Sesli/mobil: MediaRecorder → {st.get('http_path', '/api/stt')} "
            f"({st.get('primary', 'faster-whisper')}). "
            "Sürekli sohbet: HTTPS :8443 + mic + VAD; barge-in TTS keser. "
            "PC: 8779 /ui ; mobil: https://<IP>:8443/mobil/"
        )
    if intent == "ogrenme":
        return (
            "Öğretebilirsin: yanlışımı düzelt / «hatırla». "
            "Güven kapısı (learn_trust) miss/timeout’u yazmaz; indeks arka planda bekleyebilir."
        )
    if intent == "limit":
        return " · ".join(kap["yapamaz"])
    if intent == "warmup":
        w = inv.get("warmup") or {}
        return f"Warmup durumu: {w.get('state') or w or 'bilinmiyor'} (F0 tur teşhis)."
    if intent == "yardim":
        # F9.5 — sohbet «yardım/?» ile UI hub_help aynı kart
        return format_hub_help_card()
    return None


def format_hub_help_card() -> str:
    """F9.5 — UI `?` / hub yardım: sohbet öz-bilgi kartı ile aynı gerçek."""
    kap = kapasite_karti()
    motors = motor_kartlari()
    inv = canli_envanter()
    kim = kap.get("kim") or {}
    lines = [
        f"**{kim.get('ad', 'Rüzgar')}** — {kim.get('ozet', '')}",
        f"Mimar: {kim.get('mimar', MIMAR)}",
        "",
        "**Yapabilir:**",
    ]
    for x in (kap.get("yapabilir") or [])[:6]:
        lines.append(f"· {x}")
    lines.append("")
    lines.append("**Motorlar (hub):**")
    for m in motors:
        if not m.get("hub"):
            continue
        lines.append(f"· **{m.get('ad')}** — {m.get('huner')} · örn. «{m.get('ornek')}»")
    lines.append("")
    lines.append("**Dürüst sınır:**")
    for x in (kap.get("zayif") or [])[:4]:
        lines.append(f"· {x}")
    rag = inv.get("rag_chunks")
    sham = inv.get("shamela") or {}
    if rag is not None or sham:
        lines.append("")
        lines.append(
            f"Kütüphane (canlı): RAG≈{rag if rag is not None else '?'} · "
            f"Şamile shard={sham.get('shard_count', '?')}"
        )
    lines.append("")
    lines.append("Genel moda yaz; sohbet kopmaz. «Sen kimsin / neler yapabilirsin» aynı karttır.")
    lines.append(f"({OZ_BILGI_VERSION})")
    return "\n".join(lines).strip()


def oz_bilgi_public_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "version": OZ_BILGI_VERSION,
        "kapasite": kapasite_karti(),
        "motorlar": motor_kartlari(),
        "envanter": canli_envanter(),
        "hub_help": format_hub_help_card(),
    }
