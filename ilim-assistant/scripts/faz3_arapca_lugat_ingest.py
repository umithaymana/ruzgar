# -*- coding: utf-8 -*-
"""Arapça lügat / Kur'an kökleri / nahiv-sarf giriş — yerel ingest.

Kaynaklar (staging):
  - iqrossed/quran-bil-quran roots.jsonl  (Lane EN + müştak/formlar)
  - AbstractThinker0/quranRoots.json      (kök → ayet referansları)
  - mustafa0x morphology-terms-ar.json   (nahiv/sarf etiketleri)
  - Yerel nahiv_sarf_temel.jsonl         (TR usul özeti)

Çıktı: knowledge/ilim/din/03_arapca_lugat/
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "arsiv" / "_ilim_staging" / "03_arapca_lugat"
OUT = ROOT / "knowledge" / "ilim" / "din" / "03_arapca_lugat"
INCR = OUT / "incremental"

# Sık kullanılan kökler için kısa TR özet (Lane EN yanında; uydurma değil yaygın meal dili)
_TR_ROOT_HINTS: dict[str, str] = {
    "علم": "bilmek, ilim",
    "كتب": "yazmak, kitap",
    "قرأ": "okumak",
    "رحم": "merhamet, rahmet",
    "أمن": "güven, iman",
    "كفر": "örtmek, inkâr",
    "صلى": "namaz, salât, dua",
    "زكو": "temizlenmek, zekât",
    "صبر": "sabretmek",
    "شكر": "şükretmek",
    "هدى": "hidayet, yol göstermek",
    "ضل": "sapmak",
    "خلق": "yaratmak",
    "رزق": "rızık vermek",
    "ملك": "mülk, hükmetmek",
    "عبد": "kulluk etmek",
    "سبح": "tesbih etmek",
    "حمد": "hamd etmek",
    "غفر": "bağışlamak",
    "توب": "tövbe etmek",
    "شهد": "şahit olmak",
    "رسل": "göndermek, elçi",
    "نبي": "haber vermek, nebî",
    "يوم": "gün",
    "أرض": "yer, arz",
    "سما": "gök",
    "نور": "ışık, nur",
    "ظلم": "zulmetmek, karanlık",
    "حق": "hak, gerçek",
    "باطل": "bâtıl",
    "خير": "hayır, iyi",
    "شرر": "şer, kötülük",
    "حبب": "sevmek",
    "كره": "hoşlanmamak",
    "موت": "ölüm",
    "حيي": "hayat, diriltmek",
    "أكل": "yemek",
    "شرب": "içmek",
    "سمع": "işitmek",
    "بصر": "görmek",
    "قول": "söylemek",
    "فعل": "yapmak",
    "جعل": "kılmak, etmek",
    "كون": "olmak",
    "وجد": "bulmak",
    "أخذ": "almak",
    "ترك": "bırakmak",
    "دخل": "girmek",
    "خرج": "çıkmak",
    "رجع": "dönmek",
    "قام": "ayakta durmak, ikame",
    "قعد": "oturmak",
    "مشي": "yürümek",
    "جرى": "akmak, cereyan",
    "فتح": "açmak",
    "غلق": "kapamak",
    "كتب": "yazmak",
    "درس": "öğrenmek, ders",
    "فقه": "anlamak, fıkıh",
    "حكم": "hükmetmek",
    "عدل": "adalet",
    "ظلم": "zulüm",
    "صدق": "doğru olmak",
    "كذب": "yalan söylemek",
    "صوم": "oruç tutmak",
    "حجج": "hac, delil",
    "قتل": "öldürmek",
    "حيي": "yaşamak",
    "ولد": "doğmak, çocuk",
    "زوج": "eş",
    "أخو": "kardeş",
    "أب": "baba",
    "أمم": "ümmet, anne",
    "قوم": "kavim, ayağa kalkmak",
    "ناس": "insanlar",
    "رجل": "adam, yürümek",
    "مرأ": "kadın, kişi",
    "يد": "el",
    "وجه": "yüz, yönelmek",
    "قلب": "kalp, çevirmek",
    "نفس": "nefis, can",
    "روح": "ruh",
    "جنن": "cin, gizlemek",
    "ملك": "melek/mülk (bağlama göre)",
    "شيط": "şeytan",
    "إبليس": "İblis",
    "جن": "cin",
    "سمو": "isim",
    "الله": "Allah (özel isim)",
}


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _nahiv_sarf_rows() -> list[dict]:
    rows = [
        ("nahiv", "Nahiv (نحو)", "Arapça cümle bilgisidir: i‘râb, mübtedâ-haber, fâil-mef‘ûl, "
         "cer, nasb, ref‘. Kur’an kelimesinin cümledeki rolünü belirtir.",
         ["nahiv", "nahw", "i'rab", "irab"]),
        ("sarf", "Sarf (صرف)", "Kelime türetme / çekim ilmidir: kök (جذر), vezin (وزن), "
         "fiil babları (I–X…), ism-i fâil, ism-i mef‘ûl, masdar.",
         ["sarf", "sarf nedir", "morphology"]),
        ("judhur", "Kök / Cizr (جذر)", "Çoğu Arapça kelime 3 (veya 4) ünsüzden oluşan köke dayanır. "
         "Aynı kökten türeyenlere müştak denir. Örn. ك ت ب → كتب، كتاب، كاتب، مكتوب.",
         ["kök", "kok", "cizr", "judhur", "jadhr", "kök nedir"]),
        ("mushtaq", "Müştak (مشتق)", "Bir kökten türetilmiş kelimedir (fiil, isim, sıfat). "
         "Rüzgar lügatinde kök + örnek formlar birlikte verilir.",
         ["mushtaq", "müştak", "mushtak", "müştaklar", "turev", "türev"]),
        ("vezin", "Vezin (وزن)", "Kalıp: فَعَلَ، فَاعِل، مَفْعُول، تَفْعِيل… "
         "Kök harfleri ف ع ل yerine konarak okunur.",
         ["vezin", "kalıp", "kalip", "wazan"]),
        ("bab", "Bâb / fiil kalıbı", "Fiil türev kalıpları (I. mücerred, II. tef‘îl, III. müfâale, "
         "IV. if‘âl, V. tefa‘‘ul, VI. tefâ‘ul, VII. infi‘âl, VIII. ifti‘âl, X. istif‘âl…).",
         ["bab", "bâb", "fiil babi", "bablar"]),
        ("irab", "İ‘râb (إعراب)", "Kelime sonunun hareke/durumu: ref‘ (ötre), nasb (fetha), "
         "cer/hâfz (kesra), cezm. Nahvin merkezidir.",
         ["irab", "i'rab", "i‘râb", "hareke"]),
        ("fail_meful", "Fâil / Mef‘ûl", "Fâil özne; mef‘ûl nesne/tümleçtir. İsm-i fâil ‘yapan’, "
         "ism-i mef‘ûl ‘yapılan’ anlamındadır.",
         ["fail", "fâil", "meful", "mef'ul", "özne"]),
        ("masdar", "Masdar", "Fiilin isim hâli (yapmak/…mek). Örn. كِتَابَة yazma.",
         ["masdar", "masdar nedir"]),
        ("harf_cer", "Harf-i cer", "İsmi cer eden harfler: من، إلى، عن، على، في، ب، ل، ك…",
         ["harf-i cer", "harfi cer", "cer harfi"]),
        ("mudaf", "Mudâf / Mudâfun ileyh", "İzafet (tamlayan-tamlanan) yapısı: كتابُ اللهِ.",
         ["mudaf", "izafet", "izafe"]),
        ("sifat", "Sıfat / Mevsûf", "Niteleyen ve nitelenen; i‘râbda çoğunlukla uyum gösterir.",
         ["sıfat", "sifat", "mevsuf"]),
        ("mubteda", "Mübtedâ / Haber", "İsim cümlesinin öznesi ve yüklemi.",
         ["mübteda", "mubteda", "haber"]),
        ("cumle_fiiliyye", "Fiil cümlesi", "Fiil + fâil (+ mef‘ûl) sırası tipiktir.",
         ["fiil cumlesi", "fiil cümlesi"]),
        ("marife_nekre", "Marife / Nekre", "Belirli (ال، zamir, özel isim) / belirsiz isim.",
         ["marife", "nekre"]),
        ("zamir", "Zamir", "O/ben/sen… (هو، هي، أنت، أنا، هم…).",
         ["zamir", "zamirler"]),
        ("ism_fail", "İsm-i fâil", "Yapan/…en kalıbı (فاعل ve türevleri).",
         ["ism-i fail", "ismi fail", "ism fail"]),
        ("ism_meful", "İsm-i mef‘ûl", "Yapılan/…miş kalıbı (مفعول…).",
         ["ism-i meful", "ismi meful"]),
        ("lugat", "Lügat", "Sözlük anlamı. Kur’an lügati kök + form + Lane anlamı + ayet bağlamı verir.",
         ["lügat", "lugat", "sözlük", "sozluk"]),
        ("lane", "Lane Lexicon", "Edward Lane’in klasik Arapça–İngilizce sözlüğü; "
         "Rüzgar’daki kök İngilizce açıklamalarının kaynağıdır.",
         ["lane", "lane lexicon"]),
    ]
    out = []
    for kid, title, text, aliases in rows:
        out.append(
            {
                "id": kid,
                "collection": "din_03_arapca_nahiv_sarf",
                "baslik": title,
                "metin": text,
                "aliases": aliases,
            }
        )
    return out


def _load_morph_terms() -> dict[str, str]:
    p = STAGING / "morphology-terms-ar.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _ingest_roots() -> tuple[list[dict], int]:
    src = STAGING / "roots.jsonl"
    rows: list[dict] = []
    if not src.is_file():
        return rows, 0
    with src.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            root = (r.get("root") or "").strip()
            if not root:
                continue
            forms: list[str] = []
            for occ in r.get("occurrences") or []:
                for w in occ.get("word_forms") or []:
                    if w and w not in forms:
                        forms.append(w)
                for lem in occ.get("lemmas") or []:
                    if lem and lem not in forms:
                        forms.append(lem)
            meaning_en = (r.get("meaning_en") or "").strip()
            meaning_tr = _TR_ROOT_HINTS.get(root, "")
            row = {
                "collection": "din_03_kuran_kok_lugat",
                "root": root,
                "root_buckwalter": r.get("root_buckwalter") or "",
                "meaning_en": meaning_en,
                "meaning_tr": meaning_tr,
                "frequency": int(r.get("frequency") or 0),
                "verse_keys": (r.get("verse_keys") or [])[:12],
                "forms": forms[:24],
                "semantic_field": r.get("semantic_field"),
                "kaynak": "iqrossed/quran-bil-quran (Lane EN) + yerel TR ipucu",
            }
            rows.append(row)
    return rows, len(rows)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_incremental(roots: list[dict], nahiv: list[dict], morph: dict[str, str]) -> None:
    INCR.mkdir(parents=True, exist_ok=True)
    # Nahiv
    lines = ["# Arapça nahiv / sarf — giriş\n\n"]
    for r in nahiv:
        lines.append(f"## {r['baslik']}\n{r['metin']}\n\n")
    (INCR / "nahiv_sarf_giris.md").write_text("".join(lines), encoding="utf-8")

    # Morph terms
    if morph:
        ml = ["# Kur'an morfoloji etiketleri (Arapça)\n\n"]
        for k, v in sorted(morph.items(), key=lambda x: str(x[0])):
            ml.append(f"- `{k}`: {v}\n")
        (INCR / "morfoloji_etiketleri.md").write_text("".join(ml), encoding="utf-8")

    # Roots batches (~80 per file)
    batch: list[str] = []
    bi = 1
    count = 0
    header = "# Kur'an kök lügati (Lane EN + formlar)\n\n"

    def flush(i: int, buf: list[str]) -> None:
        if not buf:
            return
        (INCR / f"kok_lugat_batch_{i:04d}.md").write_text(header + "".join(buf), encoding="utf-8")

    for r in roots:
        count += 1
        forms = ", ".join(r.get("forms") or [])[:200]
        tr = r.get("meaning_tr") or ""
        batch.append(
            f"## {r['root']}\n"
            f"- Buckwalter: `{r.get('root_buckwalter')}`\n"
            f"- EN: {r.get('meaning_en')}\n"
            + (f"- TR: {tr}\n" if tr else "")
            + f"- Frekans: {r.get('frequency')}\n"
            + (f"- Formlar: {forms}\n" if forms else "")
            + f"- Ayetler: {', '.join(r.get('verse_keys') or [])}\n\n"
        )
        if count % 80 == 0:
            flush(bi, batch)
            bi += 1
            batch = []
    flush(bi, batch)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    roots, n_roots = _ingest_roots()
    nahiv = _nahiv_sarf_rows()
    morph = _load_morph_terms()

    _write_jsonl(OUT / "kuran_kok_lugat.jsonl", roots)
    _write_jsonl(OUT / "nahiv_sarf_temel.jsonl", nahiv)
    if morph:
        (OUT / "morfoloji_etiketleri.json").write_text(
            json.dumps(morph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # Lookup index: root + forms → root id
    idx: dict[str, str] = {}
    for r in roots:
        root = r["root"]
        idx[root] = root
        for form in r.get("forms") or []:
            # strip harakat for lookup key
            bare = "".join(
                c
                for c in unicodedata.normalize("NFKD", form)
                if not unicodedata.combining(c)
            )
            if bare and bare not in idx:
                idx[bare] = root
            if form not in idx:
                idx[form] = root
    (OUT / "lookup_index.json").write_text(
        json.dumps(idx, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    _write_incremental(roots, nahiv, morph)

    # Merge quranRoots occurrence counts if present
    qr = STAGING / "quranRoots.json"
    qr_n = 0
    if qr.is_file():
        try:
            data = json.loads(qr.read_text(encoding="utf-8"))
            qr_n = len(data) if isinstance(data, list) else 0
        except Exception:
            pass

    manifest = {
        "ok": True,
        "version": "din-03-arapca-lugat-v1",
        "yukleme_tarihi": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collection": "din_03_arapca_lugat",
        "qa": {
            "kuran_kok_adet": n_roots,
            "nahiv_sarf_madde": len(nahiv),
            "morfoloji_etiket": len(morph),
            "lookup_anahtar": len(idx),
            "quranRoots_kaynak_adet": qr_n,
            "tr_ipucu_adet": sum(1 for r in roots if r.get("meaning_tr")),
        },
        "kaynaklar": [
            "iqrossed/quran-bil-quran roots.jsonl (Lane Arabic-English)",
            "mustafa0x/quran-morphology morphology-terms-ar.json",
            "AbstractThinker0/quran-roots (referans)",
            "Yerel nahiv/sarf TR giriş + sık kök TR ipuçları",
        ],
        "dosyalar": {
            "kuran_kok_lugat": "kuran_kok_lugat.jsonl",
            "nahiv_sarf": "nahiv_sarf_temel.jsonl",
            "lookup_index": "lookup_index.json",
            "incremental": "incremental/",
        },
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "README.md").write_text(
        "# Din / 03 — Arapça lügat & nahiv-sarf\n\n"
        "- **Kur'an kök lügati:** Lane EN + müştak formlar + ayet anahtarları\n"
        "- **Nahiv/sarf giriş:** TR kısa usul\n"
        "- **Lookup:** harekesiz form → kök\n\n"
        f"QA: {json.dumps(manifest['qa'], ensure_ascii=False)}\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest["qa"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
