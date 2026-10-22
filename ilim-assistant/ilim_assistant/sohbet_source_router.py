"""
S1 — Tek niyet / kaynak kapısı (SourceRouter).

Zorunlu struct: tip, needs_live, needs_number, library_ok, allow_parametric, preferred_source.
S0 korpus alanlarıyla hizalı. S2/S3 bu karara bağlanır.
"""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

S1_VERSION = "sohbet-source-router-s1-v1-2026-10-23"

_NUM_RE = re.compile(
    r"(?:ka[cç]\s*(?:tane|adet|ka[cç])?|ne\s*kadar|say[ıi]s[ıi]|ka[cç]t[ıi]r|"
    r"n[uü]fus|skor|fiyat|[uü]cret|ka[cç]\s*il[cç]e)",
    re.I,
)
_SELAM_RE = re.compile(
    r"^(?:selam|merhaba|nas[ıi]ls[ıi]n|iyi\s*misin|hey)\b",
    re.I,
)
_OPINION_RE = re.compile(
    r"(?:ne\s*d[uü]ş[uü]n[uü]yorsun|sence|g[oö]r[uü]ş[uü]n|"
    r"hakk[ıi]nda\s*ne\s*d[uü]ş[uü]n)",
    re.I,
)
_META_RE = re.compile(
    r"(?:parametre|modelsin|ka[cç]\s*parametre|hangi\s*modelsin)",
    re.I,
)


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


@dataclass(frozen=True)
class SourceDecision:
    tip: str
    needs_live: bool
    needs_number: bool
    library_ok: bool
    allow_parametric: bool
    preferred_source: str
    reason: str
    elapsed_ms: float = 0.0
    version: str = S1_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _detect_live(raw: str, low: str, *, selam: bool) -> bool:
    """Selam'da 'bugün' canlı sayılmaz (S0-28)."""
    if selam:
        return False
    if re.search(r"(?:web\s*ten|webten|internetten)", low):
        return True
    if re.search(r"(?:şu\s*an|su\s*an|g[uü]ncel|canl[ıi])", low):
        return True
    if re.search(r"\bbug[uü]n\b", low):
        return True
    if re.search(r"(?:dolar|euro|bitcoin|\bbtc\b)", low):
        return True
    if re.search(r"(?:hava\s*durumu|hava\s*nas[ıi]l|\bhava\b)", low):
        return True
    if re.search(r"se[cç]im\s*sonu[cç]|t[uü]rkiye\s*se[cç]im", low):
        return True
    if re.search(r"202[4-9].*se[cç]im|se[cç]im.*202[4-9]", low):
        return True
    if re.search(r"(?:bu\s*hafta|ma[cç]).*(?:ma[cç]|skor|bitti|ka[cç])", low):
        return True
    if re.search(r"n[uü]fus", low):
        # şehir nüfusu — korpus: canlı tercih (S0-04); "nüfusu" eki dahil
        return True
    return False


def _detect_number(raw: str, low: str, *, meta: bool) -> bool:
    if meta:
        # S0-21: meta'da needs_number=false (uydurma parametre yasağı ayrı)
        return False
    if _NUM_RE.search(raw) or _NUM_RE.search(low):
        return True
    if re.search(r"\bka[cç]\b", low):
        return True
    return False


def classify_source_intent(message: str) -> SourceDecision:
    """≤1 sn hedef — saf heuristic, ağ/LLM yok."""
    t0 = time.perf_counter()
    raw = (message or "").strip()
    low = _fold(raw)

    if not raw:
        return SourceDecision(
            tip="bos",
            needs_live=False,
            needs_number=False,
            library_ok=False,
            allow_parametric=True,
            preferred_source="miss",
            reason="empty",
            elapsed_ms=0.0,
        )

    selam = bool(_SELAM_RE.search(raw) or _SELAM_RE.search(low))
    meta = bool(_META_RE.search(raw) or _META_RE.search(low))
    opinion = bool(_OPINION_RE.search(raw) or _OPINION_RE.search(low))

    needs_live = _detect_live(raw, low, selam=selam)
    needs_number = _detect_number(raw, low, meta=meta)

    tip = "genel"
    preferred = "llm_grounded"

    if selam:
        tip = "selam"
        preferred = "anlik_gundelik"
    elif meta:
        tip = "meta"
        preferred = "dürüst_miss_veya_kimlik"
    elif opinion:
        tip = "gorus"
        preferred = "ana_motor_opinion"
    elif needs_live and re.search(r"\bhava\b", low):
        tip = "guncel_hava"
        preferred = "web_veya_hava"
    elif needs_live and re.search(r"se[cç]im", low):
        tip = "guncel_siyaset"
        preferred = "web"
    elif needs_live and re.search(r"ma[cç]|galatasaray|fenerbah[cç]e", low):
        tip = "spor_guncel"
        preferred = "web"
    elif needs_live and needs_number:
        tip = "sayi_guncel"
        preferred = "web"
    elif needs_live:
        tip = "guncel"
        preferred = "web"
    elif needs_number and re.search(r"padi[sş]ah|osmanl[ıi]", low):
        tip = "sayi_tarih"
        preferred = "raf_veya_rag"
    elif needs_number and re.search(r"şart[ıi]|islam", low):
        tip = "din_sayi"
        preferred = "anlik_veya_raf"
    elif needs_number and re.search(r"y[ıi]ld[ıi]z|galaksi|g[uü]ne[sş]\s*sistem", low):
        tip = "sayi_bilim"
        preferred = "raf_veya_dürüst"
    elif needs_number and re.search(r"il[cç]e|erzurum|il\b", low):
        tip = "sayi_cografya"
        preferred = "raf_veya_web_veya_dürüst"
    elif needs_number:
        tip = "sayi"
        preferred = "raf_veya_web_veya_dürüst"
    elif re.search(r"profil\s*foto|fotosentez|ses\s+nedir", low) and (
        "nedir" in low or "anlat" in low or "foto" in low
    ):
        # S0-24 / S0-25 — motor tanımı; allow_parametric açık
        if "fotosentez" in low:
            tip = "anlat"
            preferred = "raf_grounded"
        else:
            tip = "tanim"
            preferred = "ana_motor"
    elif re.search(r"\bkimdir\b|\bkim\s*dir\b|\bkim\s*kurdu\b", low):
        tip = "kimdir"
        preferred = "raf_grounded"
    elif re.search(r"hangi\s+iller|isimlerini\s+say|\bliste\b", low):
        tip = "liste_cografya"
        preferred = "raf_grounded"
    elif re.search(r"lale\s*devri", low) and re.search(r"hangi|geli[sş]me|alan", low):
        tip = "tarih_anlat"
        preferred = "raf_grounded"
    elif re.search(r"lale\s*devri", low) and re.search(r"ne\s*zaman", low):
        tip = "tarih_kart"
        preferred = "anlik_veya_raf"
    elif re.search(r"\bne\s*zaman\b|hicret", low):
        tip = "tarih"
        preferred = "anlik_siyer" if "hicret" in low else "anlik_veya_raf"
    elif re.search(r"\banlat", low):
        tip = "anlat"
        preferred = "raf_grounded"
    elif re.search(r"\bnedir\b|\bne\s*demek\b|\btan[ıi]m\b", low):
        tip = "kisa_kavram"
        preferred = "anlik_veya_raf"
        if re.search(r"\bos\s+nedir\b", low):
            preferred = "anlik_teknoloji"
        elif "nefs" in low:
            preferred = "anlik_tasavvuf"
        elif "karadeniz" in low:
            preferred = "anlik_cografya"
    elif re.search(r"\btarih\b|osmanl[ıi]|padi[sş]ah", low):
        tip = "tarih"
        preferred = "anlik_veya_raf"

    # allow_parametric / library_ok — S0 korpus kuralları
    if tip in ("gorus", "selam"):
        allow_parametric = True
        library_ok = False
    elif tip == "tanim":
        allow_parametric = True
        library_ok = True
    elif tip == "meta":
        allow_parametric = False
        library_ok = False
    elif needs_live and needs_number and re.search(r"n[uü]fus", low):
        # S0-04: canlı + sayı ama kütüphane de kabul
        allow_parametric = False
        library_ok = True
        preferred = "web_or_raf_kaynakli"
    elif needs_live:
        allow_parametric = False
        library_ok = False
    elif needs_number:
        allow_parametric = False
        library_ok = True
    else:
        allow_parametric = False
        library_ok = tip not in ("gorus", "selam", "meta")

    ms = (time.perf_counter() - t0) * 1000.0
    return SourceDecision(
        tip=tip,
        needs_live=needs_live,
        needs_number=needs_number,
        library_ok=library_ok,
        allow_parametric=allow_parametric,
        preferred_source=preferred,
        reason=f"s1:{tip}",
        elapsed_ms=round(ms, 3),
    )


def router_enabled() -> bool:
    import os

    return os.environ.get("RUZGAR_SOURCE_ROUTER", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def blocks_faz49_fast(message: str) -> bool:
    """S2 — sayı/güncel niyette kaynaksız Faz49 hızlı LLM yasak."""
    if not router_enabled():
        # Router kapalıysa bile kaba sayı/güncel kuşağı
        low = _fold(message or "")
        return bool(
            re.search(
                r"(?:ka[cç]|n[uü]fus|istatistik|webten|bug[uü]n|şu\s*an|dolar|bitcoin)",
                low,
            )
        )
    d = classify_source_intent(message)
    return bool(d.needs_live or d.needs_number)


def attach_source_router(
    message: str,
    orchestration_out: dict[str, Any] | None,
) -> SourceDecision | None:
    """prepare_turn hafif kanca — orchestration_out['source_router'] yazar."""
    if not router_enabled():
        return None
    try:
        d = classify_source_intent(message)
    except Exception:
        return None
    if orchestration_out is not None:
        orchestration_out["source_router"] = d.to_dict()
    return d
