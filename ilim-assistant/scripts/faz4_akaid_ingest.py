# -*- coding: utf-8 -*-
"""Akaid Faz 4 — Arapça OCR metinlerini knowledge/ilim/din/04_akaid altına paketle.

Kaynaklar (staging OCR):
  - Mâtürîdî Kitâbü't-Tevhîd (Topaloğlu–Aruçi tahkik OCR, birincil)
  - Mâtürîdî Kitâbü't-Tevhîd (Huleyf 1970 OCR, yedek)
  - Eş'arî Makâlâtu'l-İslâmiyyîn (Archive OCR)
  - Eş'arî el-Luma': PDF staging'de; metin katmanı yok → konu iskeleti (TR)

Çıktı:
  knowledge/ilim/din/04_akaid/
    kavramlar_akaid.jsonl
    incremental/*.md
    manifest.json
    README.md
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "arsiv" / "_ilim_staging" / "04_akaid"
OCR_RAW = STAGING / "_ocr_raw"
OUT = ROOT / "knowledge" / "ilim" / "din" / "04_akaid"
INCR = OUT / "incremental"

CHUNK_TARGET = 1400
CHUNK_OVERLAP = 120

_KAYNAK_FOOTER = (
    "Kaynak: klasik akaid/kelâm özeti (Mâtürîdî Kitâbü't-Tevhîd, Eş'arî el-Luma'/Makâlât "
    "literatürü). Fetva değildir; mezhep içi nüanslar ihtilaflı olabilir."
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def _clean_ocr(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Archive OCR sık bozmaları
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]{2,}", " ", text)
    return text.strip()


def _arabic_ratio(s: str) -> float:
    ar = len(re.findall(r"[\u0600-\u06FF]", s))
    lat = len(re.findall(r"[A-Za-z]", s))
    tot = ar + lat
    return (ar / tot) if tot else 0.0


def _chunk_text(text: str, *, target: int = CHUNK_TARGET) -> list[str]:
    text = _clean_ocr(text)
    if not text:
        return []
    # Prefer paragraph breaks; fall back to length windows
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > target * 2:
            if buf:
                chunks.append(buf.strip())
                buf = ""
            for i in range(0, len(p), target - CHUNK_OVERLAP):
                piece = p[i : i + target].strip()
                if piece and _arabic_ratio(piece) >= 0.35:
                    chunks.append(piece)
            continue
        if not buf:
            buf = p
        elif len(buf) + 2 + len(p) <= target:
            buf = buf + "\n\n" + p
        else:
            if _arabic_ratio(buf) >= 0.35:
                chunks.append(buf.strip())
            buf = p
    if buf.strip() and _arabic_ratio(buf) >= 0.35:
        chunks.append(buf.strip())
    return chunks


def _write_batches(
    chunks: list[str],
    *,
    eser_id: str,
    title: str,
    muellif: str,
    dil: str,
    kaynak_url: str,
    prefix: str,
) -> list[dict]:
    INCR.mkdir(parents=True, exist_ok=True)
    meta_rows: list[dict] = []
    for i, body in enumerate(chunks, start=1):
        name = f"{prefix}_batch_{i:04d}.md"
        path = INCR / name
        header = (
            f"# {title}\n\n"
            f"- **Müellif:** {muellif}\n"
            f"- **Eser kimliği:** `{eser_id}`\n"
            f"- **Dil:** {dil}\n"
            f"- **Parça:** {i}/{len(chunks)}\n"
            f"- **Kaynak:** {kaynak_url}\n"
            f"- **Not:** OCR metni; yazım hataları olabilir. Fetva değildir.\n\n"
            f"---\n\n"
        )
        path.write_text(header + body + "\n", encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        meta_rows.append(
            {
                "file": f"incremental/{name}",
                "eser_id": eser_id,
                "parca": i,
                "chars": len(body),
                "sha256": digest,
            }
        )
    return meta_rows


def _kavramlar() -> list[dict]:
    rows = [
        {
            "id": "akaid",
            "baslik": "akaid",
            "aliases": ["akaid nedir", "akâid", "itikad", "itikât", "inanç ilmi"],
            "metin": (
                "Akaid (akâid), İslâm'ın inanç esaslarını konu alan ilimdir. "
                "Tevhid, nübüvvet, ahiret, kader, iman–küfür sınırları gibi konuları ele alır. "
                "Ehl-i sünnet içinde Mâtürîdîlik ve Eş'arîlik iki ana kelâm/akaid ekolüdür. "
                "Rüzgar akaid cevaplarında klasik eserlerden (Kitâbü't-Tevhîd, el-Luma', Makâlât) "
                "kaynaklı özet verir; kişisel fetva vermez."
            ),
        },
        {
            "id": "kelam",
            "baslik": "kelam",
            "aliases": ["kelam nedir", "kelâm", "ilm-i kelam"],
            "metin": (
                "Kelâm, akaid konularını aklî ve naklî delillerle tartışan ilimdir. "
                "Akaid daha çok inanç özetini; kelâm usûl ve muhakemeyi vurgular. "
                "İkisi iç içedir. Rüzgar'da akaid kütüphanesi kelâm eserlerini de kapsar."
            ),
        },
        {
            "id": "tevhid",
            "baslik": "tevhid",
            "aliases": ["tevhid nedir", "tevhîd", "allah birliği", "vahdaniyet"],
            "metin": (
                "Tevhid, Allah'ın birliği ve ortak kabul edilmemesidir (ulûhiyyet, rubûbiyyet, "
                "esmâ ve sıfât). Mâtürîdî'nin Kitâbü't-Tevhîd'i bu konunun klasik ana metinlerindendir. "
                "Şirk, tevhidin zıddıdır."
            ),
        },
        {
            "id": "maturidi",
            "baslik": "maturidi",
            "aliases": [
                "imam maturidi",
                "mâtürîdî",
                "matüridi",
                "ebu mansur maturidi",
                "maturidilik",
                "mâtürîdiyye",
            ],
            "metin": (
                "Ebû Mansûr el-Mâtürîdî (ö. 333/944), Semerkantlı Ehl-i sünnet kelâmcısıdır. "
                "Hanefî çizgide akaidi sistemleştirmiştir. Ana eseri Kitâbü't-Tevhîd; tefsiri "
                "Te'vîlâtü'l-Kur'ân'dır. Özellikle akıl–nakil dengesinde aklî delile geniş yer verir. "
                "Rüzgar kütüphanesinde Kitâbü't-Tevhîd Arapça metni vardır."
            ),
        },
        {
            "id": "esari",
            "baslik": "esari",
            "aliases": [
                "imam esari",
                "eşari",
                "eş'arî",
                "ebul hasan esari",
                "ebü'l-hasan",
                "esarilik",
                "eş'ariyye",
            ],
            "metin": (
                "Ebü'l-Hasan el-Eş'arî (ö. 324/935), Ehl-i sünnet kelâmının kurucu imamlarındandır. "
                "Mu'tezile'den ayrıldıktan sonra Ehl-i sünnet akaidini savundu. Günümüze ulaşan "
                "başlıca eserleri: Kitâbü'l-Luma', Makâlâtu'l-İslâmiyyîn, el-İbâne. "
                "Rüzgar'da Luma (PDF) ve Makâlât (Arapça metin) vardır."
            ),
        },
        {
            "id": "maturidi_esari_fark",
            "baslik": "maturidi_esari_fark",
            "aliases": [
                "maturidi esari fark",
                "mâtürîdî eş'arî fark",
                "iki mezhep farkı",
                "maturidilik esarilik",
            ],
            "metin": (
                "Mâtürîdîlik ve Eş'arîlik Ehl-i sünnetin iki kelâm ekolüdür; temelde tevhid, "
                "nübüvvet ve ahirette ortaktır. Farklar çoğunlukla usûl ve ifade tarzındadır: "
                "Mâtürîdîler aklî delile daha geniş yer verir; Eş'arîler nakli vurgulayıp aklı "
                "destekleyici kullanır. Kader–kesb, sıfatlar, iman tanımı gibi konularda nüanslar vardır. "
                "Bunlar tekfir sebebi sayılmaz; klasik ihtilaf alanıdır."
            ),
        },
        {
            "id": "iman",
            "baslik": "iman",
            "aliases": ["iman nedir", "inanç", "îmân", "iman artar azalır"],
            "metin": (
                "İman, Allah'a, peygamberlerine, kitaplarına, meleklere, ahirete ve kadere "
                "kalp ile tasdiktir (dil ile ikrar da eklenir). Ehl-i sünnette iman–amel ilişkisi "
                "ve imanın artıp azalması tartışılır; Mâtürîdî ve Eş'arî ekollerinde nüanslar vardır. "
                "Fetva değil; özet bilgidir."
            ),
        },
        {
            "id": "kader",
            "baslik": "kader",
            "aliases": ["kader nedir", "kaza kader", "kesb", "cebir"],
            "metin": (
                "Kader, Allah'ın ezelî bilgisi ve takdiri; kaza, bunun vukûudur. "
                "Ehl-i sünnet cebir (zorlama) ile mutlak insan yaratıcılığı arasında orta yolu "
                "kesb/iktisab diliyle anlatır: fiili Allah yaratır, kul kesbeder. "
                "Eş'arî el-Luma' ve Mâtürîdî Tevhîd bu konuyu işler."
            ),
        },
        {
            "id": "sifatullah",
            "baslik": "sifatullah",
            "aliases": ["sıfatlar", "allah sifatlari", "esmâ", "esma sifât", "sıfâtullah"],
            "metin": (
                "Allah'ın sıfatları (hayat, ilim, kudret, irade, kelâm…) zâtından ayrı yaratılmış "
                "değildir; teşbih ve ta'tîle düşmeden kabul edilir. Müteşâbih sıfat ayetlerinde "
                "Ehl-i sünnet te'vil / tefvîz yaklaşımları görülür. Ayrıntı klasik kelâm eserlerindedir."
            ),
        },
        {
            "id": "nubuvvet",
            "baslik": "nubuvvet",
            "aliases": ["nübüvvet", "peygamberlik", "risalet", "risâlet"],
            "metin": (
                "Nübüvvet, Allah'ın insanlara peygamber göndermesidir. Son peygamber Hz. Muhammed'dir "
                "(s.a.v.). Mucize nübüvvetin delillerindendir. Akaidde nübüvvet inkârı küfür sayılır "
                "(klasik tanım); kişisel hüküm Rüzgar'ın işi değildir."
            ),
        },
        {
            "id": "ahiret",
            "baslik": "ahiret",
            "aliases": ["ahiret nedir", "ba's", "haşr", "cennet cehennem", "kıyamet"],
            "metin": (
                "Ahiret inancı: ölüm sonrası diriliş (ba's), hesap, cennet ve cehennem. "
                "Ehl-i sünnet akaidinin temel rükünlerindendir. Detaylar kelâm ve tefsirde işlenir."
            ),
        },
        {
            "id": "kitab_tevhid",
            "baslik": "kitab_tevhid",
            "aliases": ["kitabü tevhid", "kitabu't-tevhid", "tevhid kitabı maturidi"],
            "metin": (
                "Kitâbü't-Tevhîd, İmam Mâtürîdî'nin kelâm/akaid ana eseridir. "
                "Tevhid, bilginin kaynakları, sıfatlar, nübüvvet ve karşıt görüşlerin eleştirisini içerir. "
                "Rüzgar'da Arapça OCR metni (Topaloğlu–Aruçi tahkik nüshası öncelikli) yüklüdür; "
                "soruda orijinal pasaja dayanarak anlatır."
            ),
        },
        {
            "id": "el_luma",
            "baslik": "el_luma",
            "aliases": ["el luma", "kitabül luma", "luma esari", "el-luma'"],
            "metin": (
                "Kitâbü'l-Luma' fî er-redd alâ ehli'z-zeyğ ve'l-bida', İmam Eş'arî'nin kısa kelâm "
                "özetidir. Konular: Yaratıcının varlığı, sıfatlar, Kur'an/kelâm, irade, rü'yet, "
                "kader–kesb, istitaat, iman, va'd–vaîd, imamet. PDF staging'dedir; tam OCR sonraki adım."
            ),
        },
        {
            "id": "maqalat",
            "baslik": "maqalat",
            "aliases": ["makalat", "makâlâtu'l-islamiyyin", "mezhepler kitabı esari"],
            "metin": (
                "Makâlâtu'l-İslâmiyyîn, Eş'arî'nin İslâm fırkaları ve kelâm meseleleri ansiklopedisidir. "
                "Mezhepler tarihi kaynağıdır; Eş'arî'nin kendi akaid özeti el-Luma'dadır. "
                "Rüzgar'da Arapça OCR metni yüklüdür."
            ),
        },
        {
            "id": "ehl_i_sunnet",
            "baslik": "ehl_i_sunnet",
            "aliases": ["ehl-i sünnet", "ehli sünnet", "sünni akaid"],
            "metin": (
                "Ehl-i sünnet ve'l-cemaat, sahabe yoluna bağlı çoğunluk inanç çizgisidir. "
                "Kelâmda Mâtürîdîlik ve Eş'arîlik bu çizginin iki koludur. "
                "Rüzgar akaid cevaplarını bu çerçevede, kaynaklı özet olarak verir."
            ),
        },
        {
            "id": "shirk",
            "baslik": "shirk",
            "aliases": ["şirk", "şirk nedir", "ortak koşmak"],
            "metin": (
                "Şirk, Allah'a ortak koşmaktır; tevhidin zıddıdır. Büyük şirk ile küçük şirk "
                "ayrımı fıkıh/akaid literatüründe işlenir. Rüzgar tanım verir; kişi hakkında hüküm vermez."
            ),
        },
        {
            "id": "ru_yetullah",
            "baslik": "ru_yetullah",
            "aliases": ["rüyetullah", "allah görmek", "ahirette görme", "ru'yet"],
            "metin": (
                "Rü'yetullah, müminlerin ahirette Allah'ı görmesi meselesidir. "
                "Ehl-i sünnet (Eş'arî ve Mâtürîdî) bunu kabul eder; keyfiyeti bilinemeyen bir görmedir "
                "(teşbihsiz). Mu'tezile reddeder. Klasik ihtilaf konusudur."
            ),
        },
        {
            "id": "kurani_kelam",
            "baslik": "kurani_kelam",
            "aliases": ["kuran mahluk", "kelamullah mahluk", "halku'l-kuran"],
            "metin": (
                "Kur'an'ın mahlûk olup olmadığı klasik kelâmın büyük tartışmasıdır. "
                "Ehl-i sünnet Allah'ın kelâm sıfatını kabul eder; lafız–mana ayrımı ekollere göre nüanslıdır. "
                "Rüzgar özet bilgi verir; polemik yürütmez."
            ),
        },
    ]
    out: list[dict] = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "collection": "din_04_akaid_kavram",
                "baslik": r["baslik"],
                "aliases": r["aliases"],
                "metin": r["metin"],
                "kaynak_notu": _KAYNAK_FOOTER,
            }
        )
    return out


def _luma_outline_md() -> str:
    return """# Kitâbü'l-Luma' — konu iskeleti (TR)

- **Müellif:** Ebü'l-Hasan el-Eş'arî
- **Eser:** Kitâbü'l-Luma' fî er-redd alâ ehli'z-zeyğ ve'l-bida'
- **Tahkik (staging PDF):** Hammûde Gurâbe, Kahire 1955
- **Durum:** PDF görüntü tarama; tam OCR henüz yok. Aşağıdaki iskelet bibliyografik/bilinen konu haritasıdır (uydurma alıntı yok).

## Bilinen ana konular
1. Yaratıcının varlığı ve delilleri
2. Allah'ın sıfatları (teşbih ve ta'tîlden uzak)
3. Kelâmullah / Kur'an meselesi
4. İrade
5. Rü'yetullah
6. Kader, kesb, istitaat
7. Adalet / ta'dîl–tecvîr tartışmalarına cevap
8. İman
9. Va'd ve vaîd
10. İmamet

## Kullanım
Soru geldiğinde Rüzgar önce akaid kavram özetine + Makâlât/Tevhîd Arapça corpusuna bakar; Luma PDF metne çevrilince parçalar buraya eklenecek.
"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    INCR.mkdir(parents=True, exist_ok=True)

    # Clear previous incremental akaid batches from this script prefix only
    for old in INCR.glob("*_batch_*.md"):
        old.unlink()

    sources = [
        {
            "txt": OCR_RAW / "maturidi_tawhid_topaloglu_2001.txt",
            "eser_id": "maturidi_kitab_al_tawhid_topaloglu_aruci",
            "title": "Kitâbü't-Tevhîd (Mâtürîdî) — Arapça OCR",
            "muellif": "Ebû Mansûr el-Mâtürîdî",
            "dil": "ar",
            "url": "https://archive.org/details/Al-MaturidiKitabAt-Tauhid",
            "prefix": "maturidi_tevhid",
            "priority": 1,
        },
        {
            "txt": OCR_RAW / "ashari_maqalat.txt",
            "eser_id": "ashari_maqalat_al_islamiyyin",
            "title": "Makâlâtu'l-İslâmiyyîn (Eş'arî) — Arapça OCR",
            "muellif": "Ebü'l-Hasan el-Eş'arî",
            "dil": "ar",
            "url": "https://archive.org/details/Maghalat_AlIslamyin",
            "prefix": "ashari_maqalat",
            "priority": 2,
        },
    ]

    all_meta: list[dict] = []
    for src in sources:
        if not src["txt"].is_file():
            print(f"SKIP missing {src['txt']}")
            continue
        raw = src["txt"].read_text(encoding="utf-8", errors="replace")
        chunks = _chunk_text(raw)
        print(f"{src['eser_id']}: {len(chunks)} chunks from {src['txt'].name}")
        rows = _write_batches(
            chunks,
            eser_id=src["eser_id"],
            title=src["title"],
            muellif=src["muellif"],
            dil=src["dil"],
            kaynak_url=src["url"],
            prefix=src["prefix"],
        )
        all_meta.extend(rows)

    # Luma outline
    luma_path = INCR / "ashari_luma_konu_iskeleti.md"
    luma_path.write_text(_luma_outline_md(), encoding="utf-8")

    # Kavramlar
    kav = _kavramlar()
    kav_path = OUT / "kavramlar_akaid.jsonl"
    with kav_path.open("w", encoding="utf-8") as f:
        for row in kav:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Also human-readable MD for RAG
    kav_md = OUT / "incremental" / "akaid_kavramlar_tr.md"
    parts = ["# Akaid — temel kavramlar (TR)\n", f"\n{_KAYNAK_FOOTER}\n"]
    for row in kav:
        parts.append(f"\n## {row['baslik']}\n\n{row['metin']}\n")
        if row.get("aliases"):
            parts.append(f"\n*Anahtarlar:* {', '.join(row['aliases'])}\n")
    kav_md.write_text("".join(parts), encoding="utf-8")

    readme = OUT / "README.md"
    readme.write_text(
        """# Din / 04 — Akaid kütüphanesi

| Katman | İçerik |
|--------|--------|
| **Kavramlar (TR)** | `kavramlar_akaid.jsonl` + `incremental/akaid_kavramlar_tr.md` — anlık tanımlar |
| **Mâtürîdî** | Kitâbü't-Tevhîd Arapça OCR paketleri (`maturidi_tevhid_batch_*.md`) |
| **Eş'arî** | Makâlâtu'l-İslâmiyyîn Arapça OCR (`ashari_maqalat_batch_*.md`) |
| **el-Luma'** | PDF staging; konu iskeleti (`ashari_luma_konu_iskeleti.md`) — tam OCR sonra |

**Politika:** Fetva yok. Kaynaklı özet + orijinal Arapça pasaj. Modern TR çeviriler (`bekleyen_tr/`) Mimar yasal dosya koyunca eklenir.

**Modül:** `ilim_assistant.ruzgar_akaid_kutuphane`
""",
        encoding="utf-8",
    )

    manifest = {
        "collection": "din_04_akaid",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "kavram_adet": len(kav),
        "arapca_parca": len(all_meta),
        "eserler": [
            "maturidi_kitab_al_tawhid_topaloglu_aruci",
            "ashari_maqalat_al_islamiyyin",
            "ashari_kitab_al_luma_outline",
        ],
        "chunks": all_meta,
        "politika": "fetva_degil_kaynakli_ozet",
        "staging_pdf": str(STAGING.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK kavram={len(kav)} arapca_parca={len(all_meta)} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
