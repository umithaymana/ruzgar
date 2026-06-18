# Created by Ümit & Gökçenur
"""İdrak ve Entegrasyon — niyet analizi talimatı, kaynak planı, yardımcı motor önerileri (ajan köprüsü)."""

from __future__ import annotations

import os
import unicodedata
from typing import Any


def _norm_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def motor_niyeti_heuristic(message: str) -> dict[str, bool]:
    raw = (message or "").strip()
    if not raw:
        return {k: False for k in ("ses", "video", "programlama", "tercume", "bilim", "bellek", "hizir")}
    low = raw.lower()
    asc = _norm_ascii(raw)
    blob = low + " " + asc
    return {
        "ses": any(
            x in blob
            for x in (
                "seslendir",
                "tts",
                "text to speech",
                "okuyarak",
                "ses kaydı",
                "transkript",
                "stt",
                "konuşmayı yaz",
            )
        ),
        "video": any(
            x in blob
            for x in (
                "video",
                "mp4",
                "kes",
                "altyazı",
                "subtitle",
                "ffmpeg",
                "birleştir",
            )
        ),
        "programlama": any(
            x in blob
            for x in (
                "kod",
                "python",
                "javascript",
                "typescript",
                "debug",
                "refactor",
                "api",
                "fonksiyon",
                "class ",
                "def ",
                "import ",
                "terminal",
                "pytest",
                "görev",
                "gorev",
                "git ",
                "commit",
            )
        ),
        "tercume": any(
            x in blob
            for x in (
                "çevir",
                "tercüme",
                "tercume",
                "translate",
                "ingilizce",
                "arapça",
                "arabic",
                "english",
                "almanca",
            )
        ),
        "bilim": any(
            x in blob
            for x in (
                "tarih",
                "osmanlı",
                "osmanli",
                "bilim",
                "fizik",
                "kimya",
                "biyoloji",
                "astronomi",
                "coğrafya",
                "neden",
                "nasıl oluşur",
                "padişah",
                "padisah",
                "devlet",
                "medeniyet",
                "kuran",
                "hadis",
                "tecvid",
                "nahiv",
            )
        ),
        "bellek": any(
            x in blob
            for x in (
                "hatırla",
                "hafıza",
                "hafiza",
                "kaydet",
                "öğren",
                "not al",
                "geçmiş sohbet",
            )
        ),
        "hizir": any(
            x in blob
            for x in (
                "hizir",
                "hızır",
                "arbitraj",
                "dropship",
                "trendyol satıcı",
                "amazon satıcı",
                "kar marjı",
                "kâr marjı",
                "pazar komisyonu",
                "stop loss",
                "stop-loss",
                "ekonomik av",
                "fiyat farkı",
                "otomatik listeleme",
                "stok takip",
                "pazar yerini tara",
                "pazar tara",
                "ürünleri tara",
                "urunleri tara",
                "ürün tara",
                "pazarları tara",
                "hava durumuna bak",
            )
        ),
    }


def _kaynak_etiketi(
    *,
    has_rag_hits: bool,
    web_allowed: bool,
    archive_primary: bool,
    bellek: bool,
) -> str:
    parts: list[str] = []
    if bellek:
        parts.append("Bellek / kişisel hafıza veya kayıtlı özetler")
    if archive_primary and has_rag_hits:
        parts.append("İlim hazinesi arşivi (öncelikli)")
    elif has_rag_hits:
        parts.append("Yerel bilgi bankası (RAG)")
    if web_allowed:
        parts.append("İnternet özeti (gerekirse)")
    if not parts:
        parts.append("Genel bilgi ve akıl yürütme (doğrulanmış kaynak yoksa temkinli ol)")
    return " → ".join(parts)


def build_idrak_protocol_block(
    message: str,
    mode_norm: str,
    *,
    has_rag_hits: bool,
    web_on: bool,
    ilim_rag: bool,
    motor_flags: dict[str, bool],
    archive_primary: bool = False,
) -> str:
    if os.environ.get("RUZGAR_IDRAK_PROTOCOL", "1").strip().lower() in ("0", "false", "no"):
        return ""
    kaynak = _kaynak_etiketi(
        has_rag_hits=has_rag_hits,
        web_allowed=web_on and (mode_norm not in frozenset({"ses", "okuma", "tercume", "uretim", "hizli"})),
        archive_primary=archive_primary,
        bellek=motor_flags.get("bellek", False),
    )
    aktif = [k for k, v in motor_flags.items() if v]
    aktif_s = ", ".join(aktif) if aktif else "(şimdilik özel motor ipucu yok — ana motor yanıtı yeter)"
    extra_hizir = ""
    if motor_flags.get("hizir"):
        extra_hizir = (
            "E) **HIZIR / ticaret:** Mesajda **OPERASYON MERKEZİ** veya **Merkezi bellek** blokları varsa "
            "bunlar araç çıktısıdır; fiyatları **satıcı sayfasında teyit** etmeden kesin bilgi gibi sunma.\n"
        )
    return (
        "\n\n[TALİMAT — İDRAK VE ENTEGRASYON — Ümit & Gökçenur — dahili]\n"
        "Sen yalnızca metin basan bir bot değilsin; **Rüzgar temsilcisisin**: önce düşün, sonra üret.\n"
        "A) Soruyu/Emri anla: kullanıcının asıl niyeti, istenen derinlik (özet mi ayrıntı mı) ve ton (samimi / resmî / ders) nedir?\n"
        "B) Kaynak: şu tur için öncelik sırası — "
        + kaynak
        + ".\n"
        "C) Süzgeç: ham listeleri ve magazin dili kullanma; bilgiyi **Rüzgar süzgecinden** geçir: "
        "ölçülü, saygılı, gerektiğinde kısa tarihî veya kavramsal çerçeveyle zenginleştir.\n"
        "D) Çıktı biçimi: yanıt yalnız metin mi, yoksa kullanıcı ses/video/çeviri/kod atölyesine geçecek mi? "
        "Gerekirse tek cümleyle hangi motorun işine yarayacağını belirt (emir verme, nazikçe öner).\n"
        + extra_hizir
        + "Yardımcı motor ipuçları (heuristik): "
        + aktif_s
        + ".\n"
        "Liste istenmedikçe düz madde yığını verme; anlatımı insanî ve bilge bir üslupla bağla.\n"
    )


def build_orchestra_ui_payload(
    message: str,
    *,
    motor_flags: dict[str, bool],
    clip: str | None = None,
) -> dict[str, Any]:
    """Masaüstü: çalışma sayfalarına köprü düğmeleri."""
    motors: list[dict[str, str]] = []
    base = (clip or message or "").strip()
    if len(base) > 2400:
        base = base[:2397].rstrip() + "…"

    def add(mid: str, label: str) -> None:
        motors.append({"id": mid, "label": label, "handoff": base})

    if motor_flags.get("tercume"):
        add("tercume", "Tercüme atölyesi")
    if motor_flags.get("video"):
        add("video", "Video motoru")
    if motor_flags.get("ses"):
        add("ses", "Ses stüdyosu")
    if motor_flags.get("programlama"):
        add("programlama", "Programlama atölyesi")
    if motor_flags.get("bilim") or motor_flags.get("bellek"):
        add("okuma", "Bilim / okuma çalışma sayfası")
    if motor_flags.get("bellek"):
        add("hafiza", "Hafıza motoru")
    if motor_flags.get("hizir"):
        add("hizir", "HIZIR — Ekonomik avcı (fırsat / mizan)")
    return {"motors": motors, "query": (message or "").strip()[:500]}


def append_idrak_agent_layer(
    user_payload: str,
    message: str,
    mode_norm: str,
    hits: list,
    web_on: bool,
    ilim_rag: bool,
    *,
    archive_primary: bool = False,
    orchestration_out: dict[str, Any] | None = None,
) -> str:
    flags = motor_niyeti_heuristic(message)
    has_rag = bool(hits)
    block = build_idrak_protocol_block(
        message,
        mode_norm,
        has_rag_hits=has_rag,
        web_on=web_on,
        ilim_rag=ilim_rag,
        motor_flags=flags,
        archive_primary=archive_primary,
    )
    out = (user_payload or "").rstrip() + block
    if orchestration_out is not None:
        orch = build_orchestra_ui_payload(message, motor_flags=flags)
        orchestration_out.clear()
        orchestration_out.update(orch)
    return out


def strip_handoff_for_storage(text: str, max_len: int = 12000) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"
