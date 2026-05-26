# Created by Ümit & Gökçenur
"""
Okuma motoru — Kültür ve İlim Hazinesi (geniş külliyat vizyonu).
RAG: Tasavvuf, Hadis, Klasik Türk Edebiyatı, Tarih-Kültür arşiv ağaçları.
Kullanıcı metnini hadis / gazel / tasavvufî açıklama gibi türlere ayırır.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from ilim_assistant.ruzgar_perf import RUZGAR_PERF_MIMAR

MetinTuruKodu = Literal["hadis", "gazel", "tasavvufi_aciklama", "belirsiz"]

_ROOT = Path(__file__).resolve().parents[1]
_ARSIV = _ROOT / "arsiv"
_TK = _ARSIV / "Tasavvuf_Kulliyati"
_KURAN = _TK / "Kuran_i_Kerim"
_MEKTUBAT = _TK / "Mektubat_i_Rabbani"
# Eski yapı ile uyumluluk
_LEGACY_KURAN = _ARSIV / "kuran"
_LEGACY_MEKTUBAT = _ARSIV / "mektubat"

ARSIV_VIZYONU = (
    f"{RUZGAR_PERF_MIMAR} kapsamında RÜZGAR; Tasavvuf_Kulliyati, Hadis_Kulliyati, "
    "Klasik_Turk_Edebiyati ve Tarih_ve_Kultur arşivleriyle çok katmanlı ilim hazinesidir."
)

# --- Metin türü skorları (anahtar eşleşme; çoklu türde üst skor kazanır)
_HADIS_GUCLU = (
    "rivayet",
    "isnad",
    "isnadı",
    "ravi",
    "ravisi",
    "hadis",
    "ahadis",
    "kutub",
    "sitte",
    "buhari",
    "muslim",
    "ebu davud",
    "tirmizi",
    "nesai",
    "ibn mace",
    "sahih",
    "sened",
    "radiyallahu",
    "r.a.",
    "radıyallahu",
)
_GAZEL_GUCLU = (
    "gazel",
    "beyit",
    "beyitler",
    "misra",
    "mısra",
    "divan",
    "aruz",
    "redif",
    "kafiye",
    "kaside",
    "nazim",
    "nazım",
    "siir",
    "şiir",
    "rubai",
    "mesnevi",
)
_TASAVVUF_GUCLU = (
    "tasavvuf",
    "tarikat",
    "tarîkat",
    "marifet",
    "hakikat",
    "zikir",
    "zikr",
    "halvet",
    "seyr",
    "suluk",
    "sülûk",
    "mursid",
    "mürşid",
    "seyyid",
    "tefekkur",
    "tedebbür",
    "kalbi",
    "ihlas",
    "fenafillah",
    "vecd",
    "rabita",
    "rabıta",
)


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _tokenize(s: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9çğıöşüÇĞİÖŞÜ]{3,}", _normalize(s)))


def _skor_kw(low: str, kelimeler: tuple[str, ...]) -> float:
    n = 0.0
    for kw in kelimeler:
        if kw in low:
            n += 3.0 if len(kw) >= 5 else 2.0
    return n


def kategorize_metin_parcastipi(metin: str) -> tuple[MetinTuruKodu, str]:
    """
    Kullanıcının ilettiği metin parçasının türünü kabaca sınıflandırır.
    Dönüş: (kod, kısa Türkçe açıklama)
    """
    if not (metin or "").strip():
        return "belirsiz", "Metin boş; tür çıkarılamadı."

    low = _normalize(metin)
    h = _skor_kw(low, _HADIS_GUCLU)
    g = _skor_kw(low, _GAZEL_GUCLU)
    t = _skor_kw(low, _TASAVVUF_GUCLU)

    # Hadiste rivayet zinciri / isnad ipuçları
    if re.search(r"\b(hz\.|hazret|peygamber|resul|nebi)\b", low):
        h += 2.0
    if "dedi ki" in low or "buyurdu ki" in low:
        h += 1.0
    # Gazel: kısa nazım satırları / dizeler
    if low.count("\n") >= 2 and g > 0:
        g += 1.5
    # Tasavvufî düzyazı: uzun açıklama + tasavvuf kelimesi değil ama terim yoğunluğu
    if len(metin) > 400 and t > h and t > g:
        t += 1.0

    m = max(h, g, t)
    if m < 2.0:
        return "belirsiz", "İpucu yetersiz; metin hadis, gazel veya tasavvufî düzyazı olabilir."

    if h >= g and h >= t:
        return "hadis", "Rivayet/isnad veya hadis literatürü izleri; metin hadis vasfında."
    if g >= h and g >= t:
        return "gazel", "Nazım/beyit/gazel veya divan şiiri izleri."
    return "tasavvufi_aciklama", "Tasavvuf terimleri veya sülûk–marifet düzyazısı izleri."


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        t = line.strip()
        if not t:
            continue
        try:
            row = json.loads(t)
            if isinstance(row, dict):
                out.append(row)
        except Exception:
            continue
    return out


def _best_match(message: str, rows: list[dict], source: str) -> tuple[float, str] | None:
    if not rows:
        return None
    q = _tokenize(message)
    if not q:
        return None
    best_score = 0.0
    best_ref = ""
    for row in rows:
        text = str(row.get("text", ""))
        if not text:
            continue
        toks = _tokenize(text)
        if not toks:
            continue
        inter = len(q.intersection(toks))
        if inter <= 0:
            continue
        score = inter / max(1, len(q))
        if score > best_score:
            best_score = score
            if source == "kuran":
                sure = str(row.get("sure", "")).strip()
                ayet = str(row.get("ayet", "")).strip()
                best_ref = f"{sure}:{ayet}".strip(":")
            else:
                mektup_no = str(row.get("mektup_no", "")).strip()
                best_ref = f"Mektup {mektup_no}" if mektup_no else "Mektup (numara yok)"
    if best_score <= 0:
        return None
    return best_score, best_ref


def _infer_source(message: str) -> str:
    low = _normalize(message)
    if any(x in low for x in ("ayet", "sure", "kuran", "kuran-ı", "quran")):
        return "kuran"
    if any(x in low for x in ("mektubat", "imam-ı rabbani", "imam rabbani", "mektup")):
        return "mektubat"
    kuran_rows = _read_jsonl(_KURAN / "index.jsonl") + _read_jsonl(
        _LEGACY_KURAN / "index.jsonl"
    )
    mektubat_rows = _read_jsonl(_MEKTUBAT / "index.jsonl") + _read_jsonl(
        _LEGACY_MEKTUBAT / "index.jsonl"
    )
    k = _best_match(message, kuran_rows, "kuran")
    m = _best_match(message, mektubat_rows, "mektubat")
    if k and m:
        return "kuran" if k[0] >= m[0] else "mektubat"
    if k:
        return "kuran"
    if m:
        return "mektubat"
    return "belirsiz"


def build_motor_context(message: str) -> str:
    """Okuma — ilim_ve_idrak ile PDF derin okuma chat_core üzerinden birleşir (Ümit & Gökçenur)."""
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    source = _infer_source(prompt)
    tur_kod, tur_aciklama = kategorize_metin_parcastipi(prompt)
    tur_etiket = {
        "hadis": "Hadis metni (tahmini)",
        "gazel": "Gazel / nazım (tahmini)",
        "tasavvufi_aciklama": "Tasavvufî açıklama (tahmini)",
        "belirsiz": "Tür belirsiz",
    }[tur_kod]

    kuran_rows = _read_jsonl(_KURAN / "index.jsonl") + _read_jsonl(
        _LEGACY_KURAN / "index.jsonl"
    )
    mektubat_rows = _read_jsonl(_MEKTUBAT / "index.jsonl") + _read_jsonl(
        _LEGACY_MEKTUBAT / "index.jsonl"
    )
    k = _best_match(prompt, kuran_rows, "kuran")
    m = _best_match(prompt, mektubat_rows, "mektubat")

    ref_hint = "Kaynak kesin bulunamadi."
    if source == "kuran" and k:
        ref_hint = f"Muhtemel kaynak: Sure/Ayet {k[1]} (skor={k[0]:.2f})"
    elif source == "mektubat" and m:
        ref_hint = f"Muhtemel kaynak: {m[1]} (skor={m[0]:.2f})"
    elif source == "kuran":
        ref_hint = "Kur'an kaynagi gibi gorunuyor; Sure/Ayet icin arsiv taramasi surdur."
    elif source == "mektubat":
        ref_hint = "Mektubat kaynagi gibi gorunuyor; Mektup no icin arsiv taramasi surdur."

    base = dinamit_heartbeat() + (
        "[OKUMA MOTORU — Kültür ve İlim Hazinesi]\n"
        f"{ARSIV_VIZYONU}\n"
        "Arşiv kökleri: Tasavvuf_Kulliyati, Hadis_Kulliyati, Klasik_Turk_Edebiyati, Tarih_ve_Kultur (RAG).\n"
        "Kullanıcı metnini önce şu başlıklardan biriyle sınıflandır: Hadis metni mi, Gazel/şiir mi, "
        "Tasavvufî açıklama mı; emin değilsen belirsiz de ve nedenini kısaca yaz.\n"
        f"Otomatik tur tahmini: {tur_etiket} — {tur_aciklama}\n"
        "Kur'an / Mektubat ipucu icin: Kur'an icin Sure/Ayet, Mektubat icin Mektup no; "
        "RAG kaynak dosya yolunu belirt.\n"
        f"Kaynak sınıfı (Kur'an/Mektubat ipucu): {source}\n"
        f"{ref_hint}\n"
        f"Kullanici mesaji: {prompt}"
    )
    try:
        from ilim_assistant.motorlar.okuma_faz73 import augment_okuma_context

        return augment_okuma_context(base)
    except Exception:
        return base
