# Created by Ümit & Gökçenur
"""
Rüzgar Kütüphanesi — yerel, raflı, kataloglu bilgi deposu.

Amaç: Nebula/TDK/Tarih yanı sıra düzenli bir «kütüphane» katmanı;
sohbetten durum/arama; RAG indeksi `knowledge/kutuphane/` altındaki
Markdown'ı otomatik tarar.

Kapatma: RUZGAR_KUTUPHANE=0
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

KUTUPHANE_VERSION = "kutuphane-v1-2026-10-05"

_PKG = Path(__file__).resolve().parent.parent
_KUTUP_ROOT = _PKG / "knowledge" / "kutuphane"
_RAFLAR = _KUTUP_ROOT / "raflar"
_KATALOG = _KUTUP_ROOT / "KATALOG.json"
_MANIFEST = _KUTUP_ROOT / "manifest.json"

_STATUS_CMDS = {
    "kütüphane durum",
    "kutuphane durum",
    "kütüphane durumu",
    "kutuphane durumu",
    "kütüphane rapor",
    "kutuphane rapor",
    "library status",
}


def kutuphane_enabled() -> bool:
    return os.environ.get("RUZGAR_KUTUPHANE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def kutuphane_root() -> Path:
    return _KUTUP_ROOT


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip().lower())
    t = t.replace("ı", "i").replace("İ", "i")
    return re.sub(r"\s+", " ", t)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class RafMeta:
    id: str
    ad: str
    aciklama: str
    etiketler: tuple[str, ...]


# Sabit raf tanımı — Mimar onayıyla genişletilir
RAF_TANIMLARI: tuple[RafMeta, ...] = (
    RafMeta(
        "01_astronomi_uzay",
        "Astronomi ve Uzay",
        "Güneş sistemi, galaksiler, yıldızlar, uzay araştırmaları.",
        ("astronomi", "uzay", "gezegen", "galaksi", "yıldız"),
    ),
    RafMeta(
        "02_fizik_kimya",
        "Fizik ve Kimya",
        "Temel fizik yasaları, maddenin halleri, elementler, enerji.",
        ("fizik", "kimya", "enerji", "atom", "ısı"),
    ),
    RafMeta(
        "03_biyoloji_dunya",
        "Biyoloji ve Canlılar",
        "Hücre, fotosentez, ekosistem, insan vücudu (genel bilgi).",
        ("biyoloji", "hücre", "fotosentez", "canlı", "doğa"),
    ),
    RafMeta(
        "04_cografya",
        "Coğrafya",
        "Türkiye ve dünya coğrafyası, iklim, kıtalar, okyanuslar.",
        ("coğrafya", "ülke", "şehir", "iklim", "kıta"),
    ),
    RafMeta(
        "05_tarih",
        "Tarih",
        "Osmanlı, Cumhuriyet, dünya tarihi özetleri (yerel ansiklopedi).",
        ("tarih", "osmanlı", "cumhuriyet", "medeniyet"),
    ),
    RafMeta(
        "06_matematik",
        "Matematik",
        "Günlük matematik, birimler, oran-orantı, basit geometri.",
        ("matematik", "sayı", "oran", "geometri", "birim"),
    ),
    RafMeta(
        "07_dil_turkce",
        "Dil ve Türkçe",
        "Yazım, anlam, dilbilgisi özetleri; TDK ile uyumlu kısa notlar.",
        ("dil", "türkçe", "yazım", "anlam", "dilbilgisi"),
    ),
    RafMeta(
        "08_teknoloji",
        "Teknoloji ve Bilgisayar",
        "Bilgisayar temelleri, internet, yapay zekâ kavramları (genel).",
        ("teknoloji", "bilgisayar", "internet", "yazılım", "yapay zeka"),
    ),
    RafMeta(
        "09_kultur_yasam",
        "Kültür ve Günlük Yaşam",
        "Türk kültürü, adetler, genel yaşam bilgisi.",
        ("kültür", "gelenek", "yaşam", "bayram"),
    ),
    RafMeta(
        "10_hizli_referans",
        "Hızlı Referans (Sık Sorulanlar)",
        "Kısa soru–cevap kartları; sohbet anında hızlı doğruluk.",
        ("sss", "nedir", "kaç", "hangi", "referans"),
    ),
)


def ensure_dirs() -> None:
    _KUTUP_ROOT.mkdir(parents=True, exist_ok=True)
    _RAFLAR.mkdir(parents=True, exist_ok=True)
    for raf in RAF_TANIMLARI:
        (_RAFLAR / raf.id).mkdir(parents=True, exist_ok=True)
        inc = _RAFLAR / raf.id / "incremental"
        inc.mkdir(parents=True, exist_ok=True)


def _iter_md_files() -> list[Path]:
    if not _RAFLAR.is_dir():
        return []
    return sorted(_RAFLAR.rglob("*.md"))


def _extract_titles(text: str) -> list[str]:
    titles: list[str] = []
    for line in (text or "").splitlines():
        m = re.match(r"^#{1,3}\s+(.+)$", line.strip())
        if m:
            titles.append(m.group(1).strip())
    return titles


def rebuild_katalog() -> dict[str, Any]:
    """Raflardaki md dosyalarından KATALOG.json + manifest yazar."""
    ensure_dirs()
    eserler: list[dict[str, Any]] = []
    raf_ozet: list[dict[str, Any]] = []
    total_chars = 0
    total_baslik = 0

    for raf in RAF_TANIMLARI:
        raf_dir = _RAFLAR / raf.id
        files = sorted(raf_dir.rglob("*.md")) if raf_dir.is_dir() else []
        raf_chars = 0
        raf_baslik = 0
        for path in files:
            try:
                body = path.read_text(encoding="utf-8")
            except OSError:
                continue
            titles = _extract_titles(body)
            rel = path.relative_to(_KUTUP_ROOT).as_posix()
            chars = len(body)
            raf_chars += chars
            raf_baslik += len(titles)
            eserler.append(
                {
                    "id": path.stem,
                    "raf": raf.id,
                    "raf_ad": raf.ad,
                    "yol": rel,
                    "basliklar": titles[:40],
                    "karakter": chars,
                    "satir": body.count("\n") + 1,
                }
            )
        total_chars += raf_chars
        total_baslik += raf_baslik
        raf_ozet.append(
            {
                "id": raf.id,
                "ad": raf.ad,
                "aciklama": raf.aciklama,
                "etiketler": list(raf.etiketler),
                "dosya": len(files),
                "karakter": raf_chars,
                "baslik": raf_baslik,
            }
        )

    katalog = {
        "ok": True,
        "version": KUTUPHANE_VERSION,
        "guncelleme": _now_iso(),
        "kok": "knowledge/kutuphane",
        "raf_sayisi": len(RAF_TANIMLARI),
        "eser_sayisi": len(eserler),
        "toplam_karakter": total_chars,
        "toplam_baslik": total_baslik,
        "raflar": raf_ozet,
        "eserler": eserler,
    }
    _KATALOG.write_text(
        json.dumps(katalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manifest = {
        "ok": True,
        "version": KUTUPHANE_VERSION,
        "guncelleme": _now_iso(),
        "raf_sayisi": len(RAF_TANIMLARI),
        "eser_sayisi": len(eserler),
        "toplam_karakter": total_chars,
        "toplam_baslik": total_baslik,
        "katalog": "KATALOG.json",
    }
    _MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return katalog


def load_katalog() -> dict[str, Any]:
    if not _KATALOG.is_file():
        return rebuild_katalog()
    try:
        return json.loads(_KATALOG.read_text(encoding="utf-8"))
    except Exception:
        return rebuild_katalog()


def load_manifest() -> dict[str, Any]:
    if not _MANIFEST.is_file():
        kat = rebuild_katalog()
        return {
            "ok": True,
            "version": KUTUPHANE_VERSION,
            "eser_sayisi": kat.get("eser_sayisi"),
            "raf_sayisi": kat.get("raf_sayisi"),
        }
    try:
        return json.loads(_MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "error": "manifest okunamadı"}


def kutuphane_status() -> dict[str, Any]:
    man = load_manifest()
    kat = load_katalog() if kutuphane_enabled() else {}
    return {
        "ok": True,
        "enabled": kutuphane_enabled(),
        "version": KUTUPHANE_VERSION,
        "root": str(_KUTUP_ROOT),
        "manifest": man,
        "raf_sayisi": kat.get("raf_sayisi") or man.get("raf_sayisi") or 0,
        "eser_sayisi": kat.get("eser_sayisi") or man.get("eser_sayisi") or 0,
        "toplam_baslik": kat.get("toplam_baslik") or 0,
        "toplam_karakter": kat.get("toplam_karakter") or 0,
        "raflar": [
            {"id": r.id, "ad": r.ad, "aciklama": r.aciklama} for r in RAF_TANIMLARI
        ],
    }


def search_kutuphane(query: str, *, limit: int = 8) -> list[dict[str, Any]]:
    """Başlık + yol + etiket üzerinde hafif arama (LLM yok)."""
    q = _norm(query)
    if not q or not kutuphane_enabled():
        return []
    terms = [t for t in re.split(r"\W+", q) if len(t) >= 2]
    if not terms:
        return []
    kat = load_katalog()
    scored: list[tuple[float, dict[str, Any]]] = []
    for eser in kat.get("eserler") or []:
        blob = _norm(
            " ".join(
                [
                    str(eser.get("id") or ""),
                    str(eser.get("raf_ad") or ""),
                    str(eser.get("yol") or ""),
                    " ".join(eser.get("basliklar") or []),
                ]
            )
        )
        hits = sum(1 for t in terms if t in blob)
        if hits <= 0:
            continue
        score = hits / max(1, len(terms))
        if any(t in blob for t in terms if len(t) >= 4):
            score += 0.15
        scored.append((score, eser))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[dict[str, Any]] = []
    for sc, eser in scored[: max(1, min(limit, 20))]:
        row = dict(eser)
        row["skor"] = round(sc, 3)
        out.append(row)
    return out


def read_eser_excerpt(yol: str, *, max_chars: int = 2400) -> str:
    """Katalogdeki göreli yoldan metin kesiti."""
    rel = (yol or "").replace("\\", "/").lstrip("/")
    if ".." in rel or not rel.endswith(".md"):
        return ""
    path = (_KUTUP_ROOT / rel).resolve()
    try:
        path.relative_to(_KUTUP_ROOT.resolve())
    except ValueError:
        return ""
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return text[: max(400, min(max_chars, 8000))]


def build_kutuphane_context(query: str, *, max_eser: int = 3, max_chars: int = 3500) -> str:
    """Sohbet bağlamı için kütüphane kesitleri."""
    if not kutuphane_enabled():
        return ""
    hits = search_kutuphane(query, limit=max_eser)
    if not hits:
        return ""
    parts = [
        "=== RÜZGAR KÜTÜPHANESİ (yerel raflar; doğrulanmış genel bilgi) ===",
        f"Soru odaklı eser: {len(hits)}",
    ]
    used = 0
    for i, h in enumerate(hits, 1):
        yol = str(h.get("yol") or "")
        excerpt = read_eser_excerpt(yol, max_chars=1400)
        if not excerpt:
            continue
        block = (
            f"\n--- Eser #{i}: {h.get('raf_ad')} / {h.get('id')} (skor={h.get('skor')}) ---\n"
            f"{excerpt}"
        )
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    if len(parts) <= 2:
        return ""
    return "\n".join(parts)


def format_status_reply() -> str:
    st = kutuphane_status()
    if not st.get("enabled"):
        return "Kütüphane şu an kapalı (`RUZGAR_KUTUPHANE=0`)."
    lines = [
        f"**Rüzgar Kütüphanesi** hazır ({KUTUPHANE_VERSION}).",
        f"- Raf: **{st.get('raf_sayisi')}** · Eser (dosya): **{st.get('eser_sayisi')}**",
        f"- Başlık: **{st.get('toplam_baslik')}** · Karakter: **{st.get('toplam_karakter')}**",
        "- Raflar:",
    ]
    for r in RAF_TANIMLARI:
        lines.append(f"  · `{r.id}` — {r.ad}")
    lines.append(
        "Komutlar: «kütüphane durum» · «kütüphane ara fotosentez» · "
        "kitap ingest için nebula komutu ayrıdır."
    )
    return "\n".join(lines)


def format_search_reply(query: str) -> str:
    hits = search_kutuphane(query, limit=6)
    if not hits:
        return (
            f"«{query}» için kütüphane rafında net eser bulamadım. "
            "Başka anahtar kelime dene veya bilgi sorusu olarak sor."
        )
    lines = [f"**Kütüphane arama:** «{query}» — {len(hits)} sonuç"]
    for h in hits:
        bas = (h.get("basliklar") or ["(başlıksız)"])[0]
        lines.append(
            f"- [{h.get('skor')}] **{bas}** — {h.get('raf_ad')} (`{h.get('yol')}`)"
        )
    return "\n".join(lines)


_SEARCH_CMD = re.compile(
    r"(?i)^\s*k[uü]t[uü]phane\s+ara\s*[:\-]?\s*(.+)$"
)


def try_consume_kutuphane_command(message: str) -> Optional[str]:
    """Sohbet erken komutu — durum / arama."""
    if not kutuphane_enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None
    low = _norm(raw)
    if low in _STATUS_CMDS or low in {"kutuphane", "kütüphane"}:
        return format_status_reply()
    m = _SEARCH_CMD.match(raw)
    if m:
        return format_search_reply(m.group(1).strip())
    return None


def lookup_hizli_referans(message: str) -> Optional[dict[str, Any]]:
    """
    10_hizli_referans rafındaki SSS kartlarından kısa eşleşme.
    Biçim: ## Soru
    Cevap satırları...
    """
    if not kutuphane_enabled():
        return None
    raf = _RAFLAR / "10_hizli_referans"
    if not raf.is_dir():
        return None
    qn = _norm(message)
    if len(qn) < 6:
        return None
    best: Optional[dict[str, Any]] = None
    best_sc = 0.0
    for path in sorted(raf.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        sections = re.split(r"(?m)^##\s+", text)
        for sec in sections[1:]:
            lines = sec.strip().splitlines()
            if not lines:
                continue
            soru = lines[0].strip()
            cevap = "\n".join(lines[1:]).strip()
            if len(cevap) < 20:
                continue
            sn = _norm(soru)
            # Basit örtüşme
            qw = set(re.findall(r"[a-z0-9çğıöşü]{3,}", qn))
            sw = set(re.findall(r"[a-z0-9çğıöşü]{3,}", sn))
            if not qw or not sw:
                continue
            inter = len(qw & sw)
            if inter <= 0:
                continue
            sc = inter / max(len(qw), 1)
            if sn in qn or qn in sn:
                sc += 0.35
            if sc > best_sc and sc >= 0.45:
                best_sc = sc
                best = {
                    "soru": soru,
                    "cevap": cevap,
                    "skor": round(sc, 3),
                    "kaynak": path.relative_to(_KUTUP_ROOT).as_posix(),
                    "eslesme": "kutuphane_sss",
                }
    return best


def try_kutuphane_instant_reply(message: str) -> Optional[str]:
    """Hızlı referans SSS — anında cevap (web/hafıza değil)."""
    cmd = try_consume_kutuphane_command(message)
    if cmd:
        return cmd
    # Canlı haber/spor kütüphane SSS'ye düşmesin
    try:
        from ilim_assistant.ruzgar_web_arastirma_pro import looks_like_live_web_needed

        if looks_like_live_web_needed(message):
            return None
    except Exception:
        pass
    hit = lookup_hizli_referans(message)
    if not hit:
        return None
    return str(hit.get("cevap") or "").strip() or None
