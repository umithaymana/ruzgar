# -*- coding: utf-8 -*-
"""Edebiyat Faz 2 — dil/dönem katmanları (divan, Türk dönem, batı, yakın dönem).

Faz 1 OpenITI eserleri korunur. Telifli modern tam metin yok.
Politika: Fetva yok. Sayfa/cilt uydurma yasak. 2 fazlı raf kuralı.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "edebiyat_sanat"
KAT = OUT / "katmanlar"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = OUT / "kavramlar_edebiyat.jsonl"
CATALOG = OUT / "catalog.json"
CATALOG_F2 = OUT / "catalog_faz2.json"

# Faz 1 OpenITI kavramları (script yeniden yazınca kaybolmasın)
FAZ1_KAVRAMLAR = [
    {
        "id": "edebiyat",
        "baslik": "edebiyat",
        "aliases": [
            "edebiyat nedir",
            "arap edebiyati",
            "arap edebiyatı",
            "klasik edebiyat",
            "adab",
            "edebiyat sanat",
            "turk edebiyati",
            "türk edebiyatı",
        ],
        "metin": (
            "Edebiyat rafı iki fazlıdır: (1) klasik Arap adab/şiir (OpenITI); "
            "(2) divan ve Türk dönemleri, batı klasikleri (kamu malı/kavram), "
            "yakın dönem yalnızca akım/kronoloji. Telifli modern roman metni yoktur. "
            "Fetva değildir."
        ),
        "kaynak_notu": "Edebiyat rafı — Faz 1+2.",
    },
    {
        "id": "makamat",
        "baslik": "makamat",
        "aliases": ["makâme", "maqama", "maqamat", "makame türü"],
        "metin": (
            "Makâme: klasik Arap nesrinde süslü dil ve serüven anlatısı türü. "
            "Örnekler: Hemedânî ve Harîrî Makâmât. Fetva değildir."
        ),
        "kaynak_notu": "Edebiyat rafı — kavram.",
    },
    {
        "id": "ibn_muqaffa_kalila",
        "baslik": "kelile",
        "aliases": ["kelile", "kelile ve dimne", "kalila", "kalila wa dimna", "ibn mukaffa"],
        "metin": (
            "İbnü'l-Mukaffaʿ'ın Kelîle ve Dimne'si: Sanskrit kökenli hikâye zincirinin "
            "klasik Arapça edebî uyarlaması; siyaset ve ahlâk öğüdü. Fetva değildir."
        ),
        "kaynak_notu": "Edebiyat rafı — OpenITI; fetva yok.",
    },
    {
        "id": "hamadhani_maqamat",
        "baslik": "maqamat hemedani",
        "aliases": [
            "maqamat hemedani",
            "makamat hemedani",
            "bediuzzaman makamat",
            "hemedani makamat",
            "hamadhani maqamat",
        ],
        "metin": (
            "Bedîüzzaman el-Hemedânî'nin Makâmât'ı: klasik Arap nesirinin makâme türü; "
            "dil ustalığı ve hikâye. Fetva değildir."
        ),
        "kaynak_notu": "Edebiyat rafı — OpenITI; fetva yok.",
    },
    {
        "id": "hariri_maqamat",
        "baslik": "hariri makamat",
        "aliases": [
            "hariri makamat",
            "maqamat hariri",
            "makamatü hariri",
            "harîrî makâmât",
            "el hariri",
        ],
        "metin": (
            "el-Harîrî'nin Makâmât'ı: makâme türünün doruk örneklerinden; "
            "Arap edebî nesri ve dil sanatı. Fetva değildir."
        ),
        "kaynak_notu": "Edebiyat rafı — OpenITI; fetva yok.",
    },
    {
        "id": "abu_tammam_diwan",
        "baslik": "abu tammam",
        "aliases": [
            "abu tammam",
            "ebu temmam",
            "ebû temmâm",
            "diwan abu tammam",
            "divan ebu temmam",
        ],
        "metin": (
            "Ebû Temmâm'ın Dîvân'ı: Abbâsî dönemi klasik Arap şiiri. "
            "Edebî metindir; fetva değildir."
        ),
        "kaynak_notu": "Edebiyat rafı — OpenITI; fetva yok.",
    },
    {
        "id": "ibn_qutayba_shir",
        "baslik": "sir ve suara",
        "aliases": [
            "sir ve suara",
            "şiir ve şairler",
            "shicr wa shucara",
            "ibn kuteybe siir",
            "ibn qutayba poetry",
        ],
        "metin": (
            "İbn Kuteybe'nin eş-Şiʿr ve'ş-şuʿarâ'sı: klasik Arap şiir tarihi ve şair "
            "biyografileri. Edebî kaynaktır; fetva değildir."
        ),
        "kaynak_notu": "Edebiyat rafı — OpenITI; fetva yok.",
    },
    {
        "id": "buhturi_diwan",
        "baslik": "buhturi",
        "aliases": ["buhturi", "buhturî", "el buhturi", "diwan buhturi", "divan buhturi"],
        "metin": (
            "el-Buḥturî'nin Dîvân'ı: Abbâsî klasik Arap şiiri; Ebû Temmâm çizgisinin "
            "çağdaşı. Edebî metindir; fetva değildir."
        ),
        "kaynak_notu": "Edebiyat rafı — OpenITI; fetva yok.",
    },
    {
        "id": "maarri_diwan",
        "baslik": "maarri",
        "aliases": [
            "maarri",
            "maʿarrî",
            "el maarri",
            "abu ala maarri",
            "diwan maarri",
            "divan maarri",
        ],
        "metin": (
            "Ebü'l-Alâ el-Maʿarrî'nin Dîvân'ı: klasik Arap şiiri ve düşünce tonu. "
            "Edebî metindir; fetva değildir."
        ),
        "kaynak_notu": "Edebiyat rafı — OpenITI; fetva yok.",
    },
]

FAZ2_KAVRAMLAR = [
    # --- Divan / tür ---
    {
        "id": "divan_edebiyati",
        "baslik": "divan",
        "aliases": [
            "divan",
            "divan edebiyati",
            "divan edebiyatı",
            "osmanli siiri",
            "osmanlı şiiri",
            "klasik turk siiri",
        ],
        "metin": (
            "Divan edebiyatı: Osmanlı–Türk klasik şiir geleneği; aruz vezni, gazel–kaside–mesnevi "
            "biçimleri, Farsça–Arapça söz varlığı ve mazmunlar. Örnek şairler: Fuzûlî, Bâkî, "
            "Nedîm, Şeyh Gâlib. Telifli modern metin değildir; kamu malı klasik çerçevedir."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — divan katmanı.",
    },
    {
        "id": "aruz",
        "baslik": "aruz",
        "aliases": ["aruz", "aruz vezni", "arûz"],
        "metin": (
            "Aruz: hece uzunluk–kısalığına dayanan klasik vezin; divan şiirinin temel ölçüsü. "
            "Halk şiirinde hece vezni daha yaygındır."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — kavram.",
    },
    {
        "id": "gazel",
        "baslik": "gazel",
        "aliases": ["gazel", "gazel nedir"],
        "metin": (
            "Gazel: divan şiirinde çoğunlukla aşk ve güzellik temalı, beyitlerden oluşan nazım "
            "biçimi; matla ve makta gelenekseldir."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — kavram.",
    },
    {
        "id": "kaside",
        "baslik": "kaside",
        "aliases": ["kaside", "kasîde"],
        "metin": (
            "Kaside: övgü, dinî veya devlet temalı, gazelden daha uzun klasik nazım biçimi; "
            "nesib–girizgâh–medhiye bölümleri anılır."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — kavram.",
    },
    {
        "id": "mesnevi",
        "baslik": "mesnevi",
        "aliases": ["mesnevi", "mesnevî", "mesnevi nazim"],
        "metin": (
            "Mesnevi: her beyti kendi içinde kafiyeli uzun anlatı biçimi; öğretici ve hikâye "
            "konularında kullanılır (ör. Mevlânâ Mesnevî — ayrı tasavvuf rafında da geçer)."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — kavram.",
    },
    {
        "id": "fuzuli",
        "baslik": "fuzuli",
        "aliases": ["fuzuli", "fuzûlî", "fuzuli kimdir", "leyli vü mecnun"],
        "metin": (
            "Fuzûlî (ö. 963/1556): divan şiirinin büyük üstadlarından; Türkçe, Farsça, Arapça "
            "yazmıştır. Leylâ vü Mecnûn mesnevisi ve gazelleri ünlüdür. Kamu malı klasik; "
            "telifli modern roman değildir."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — divan; kamu malı.",
    },
    {
        "id": "baki",
        "baslik": "baki",
        "aliases": ["baki", "bâkî", "baki sultanus suara"],
        "metin": (
            "Bâkî (ö. 1008/1600): Osmanlı divan şiirinde «sultânü'ş-şuarâ» unvanıyla anılır; "
            "gazel üstadı. Kamu malı klasik."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — divan; kamu malı.",
    },
    {
        "id": "nedim",
        "baslik": "nedim",
        "aliases": ["nedim", "nedîm", "nedim sarkı"],
        "metin": (
            "Nedîm (ö. 1143/1730): Lâle Devri’nin şairi; İstanbul zevki, şarkı ve gazelde "
            "canlı üslûp. Kamu malı klasik."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — divan; kamu malı.",
    },
    {
        "id": "yunus_emre",
        "baslik": "yunus emre",
        "aliases": ["yunus emre", "yunus", "yunus emre kimdir"],
        "metin": (
            "Yunus Emre (13.–14. yy.): Türkçe tasavvufî–halk şiiri; sade dil, insan ve aşk "
            "teması. Divan üslûbundan ayrı halk/tekke çizgisidir. Kamu malı klasik."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — halk/tekke; kamu malı.",
    },
    {
        "id": "seyh_galib",
        "baslik": "seyh galib",
        "aliases": ["seyh galib", "şeyh gâlib", "husn u ask", "hüsn ü aşk"],
        "metin": (
            "Şeyh Gâlib (ö. 1213/1799): divan şiirinin son büyük üstadlarından; Hüsn ü Aşk "
            "mesnevisi. Kamu malı klasik."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — divan; kamu malı.",
    },
    # --- Türk dönemleri ---
    {
        "id": "halk_edebiyati",
        "baslik": "halk edebiyati",
        "aliases": ["halk edebiyati", "halk edebiyatı", "asik edebiyati", "âşık edebiyatı"],
        "metin": (
            "Halk edebiyatı: hece vezni, âşık/ozan geleneği, destan, türkü, mani. "
            "Yunus Emre, Karacaoğlan, Pir Sultan Abdal çizgisi örneklenir. "
            "Canlı yazarlardan telifli metin alınmaz."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — Türk dönem.",
    },
    {
        "id": "tanzimat",
        "baslik": "tanzimat",
        "aliases": [
            "tanzimat",
            "tanzimat edebiyati",
            "tanzimat edebiyatı",
            "tanzimat donemi",
        ],
        "metin": (
            "Tanzimat edebiyatı (yaklaşık 1860 sonrası): Batı etkisiyle roman, tiyatro, makale; "
            "Şinasi, Namık Kemal, Ziya Paşa, Ahmet Mithat. Bu katmanda kavram/özet vardır; "
            "telif süresi dolmamış eserlerin tam metni yoktur."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — dönem kavramı.",
    },
    {
        "id": "servet_i_funun",
        "baslik": "servet i funun",
        "aliases": [
            "servet i funun",
            "servet-i fünun",
            "servetifünun",
            "efdal edebiyati",
        ],
        "metin": (
            "Servet-i Fünûn (Edebiyat-ı Cedîde): Tevfik Fikret, Halit Ziya, Cenap Şahabettin "
            "çevresi; sanatlı üslûp ve bireysel temalar. Kavram katmanı; telifli tam metin yok."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — dönem kavramı.",
    },
    {
        "id": "milli_edebiyat",
        "baslik": "milli edebiyat",
        "aliases": [
            "milli edebiyat",
            "millî edebiyat",
            "milli edebiyat donemi",
            "yeni lisan",
        ],
        "metin": (
            "Millî Edebiyat: sade Türkçe ve millî konular; Ömer Seyfettin, Ziya Gökalp, "
            "Mehmet Emin Yurdakul anılır. Kavram/kronoloji; telifli roman metni yüklenmez."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — dönem kavramı.",
    },
    {
        "id": "cumhuriyet_edebiyati",
        "baslik": "cumhuriyet edebiyati",
        "aliases": [
            "cumhuriyet edebiyati",
            "cumhuriyet edebiyatı",
            "cumhuriyet donemi edebiyat",
        ],
        "metin": (
            "Cumhuriyet dönemi edebiyatı: roman, öykü, şiirde çeşitlilik; akımlar ve yazar "
            "adları kavram düzeyinde tutulur. Canlı/telifli yazarlardan metin alıntısı yoktur."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — dönem kavramı; telif sınırlı.",
    },
    # --- Batı ---
    {
        "id": "bati_edebiyati",
        "baslik": "bati edebiyati",
        "aliases": [
            "bati edebiyati",
            "batı edebiyatı",
            "bati edebiyatı",
            "western literature",
            "avrupa edebiyati",
        ],
        "metin": (
            "Batı edebiyatı katmanı: antik (Homeros), klasik tiyatro/şiir (Shakespeare kamu malı "
            "çerçeve), akımlar (klasizm, romantizm, realizm, modernizm) kavram olarak. "
            "Modern telifli roman tam metni yoktur."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — batı; kamu malı/kavram.",
    },
    {
        "id": "homeros",
        "baslik": "homeros",
        "aliases": ["homeros", "homer", "ilyada", "odysseia", "odyssey"],
        "metin": (
            "Homeros: antik Yunan destan geleneği; İlyada ve Odysseia. Kamu malı klasik; "
            "çeviri seçkisi kavram düzeyindedir."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — batı klasik.",
    },
    {
        "id": "shakespeare",
        "baslik": "shakespeare",
        "aliases": ["shakespeare", "shakespeare kimdir", "hamlet", "romeo juliet"],
        "metin": (
            "William Shakespeare (ö. 1616): İngiliz tiyatro ve şiir klasiği; eserleri kamu malı "
            "kabul edilir. Bu rafta kavram/özet vardır; uzun çeviri dump’u yoktur."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — batı klasik.",
    },
    {
        "id": "romantizm",
        "baslik": "romantizm",
        "aliases": ["romantizm", "romanticism", "romantik edebiyat"],
        "metin": (
            "Romantizm: 18.–19. yy. duygu, doğa, birey ve ulusal temalar; Avrupa edebiyatında "
            "akım. Kavram katmanıdır."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — akım.",
    },
    {
        "id": "realizm",
        "baslik": "realizm",
        "aliases": ["realizm", "realism", "gercekcilik"],
        "metin": (
            "Realizm: 19. yy. toplumsal gerçeklik ve gözlem odaklı anlatım akımı. "
            "Kavram katmanıdır; telifli roman metni yok."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — akım.",
    },
    # --- Yakın dönem ---
    {
        "id": "yakin_donem_edebiyat",
        "baslik": "yakin donem edebiyat",
        "aliases": [
            "yakin donem edebiyat",
            "yakın dönem edebiyat",
            "cagdas edebiyat",
            "çağdaş edebiyat",
            "modern turk edebiyati",
        ],
        "metin": (
            "Yakın/çağdaş edebiyat katmanı yalnızca akım, dönem ve genel yönelimleri özetler. "
            "Canlı yazarlardan veya telifli eserlerden metin alıntısı yapılmaz; isim listesi "
            "öğretici amaçlı kısa tutulur."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — yakın dönem; telif yok.",
    },
    {
        "id": "modernizm_edebiyat",
        "baslik": "modernizm edebiyat",
        "aliases": ["modernizm", "edebi modernizm", "modernist edebiyat"],
        "metin": (
            "Edebî modernizm: 20. yy. biçim denemeleri, bilinç akışı, kırık anlatı. "
            "Kavramdır; telifli eser metni yüklenmez."
        ),
        "kaynak_notu": "Edebiyat Faz 2 — akım.",
    },
]

# Kısa kamu malı / eğitim batch'leri (tam divan dump değil)
KATMAN_BATCHES: dict[str, dict] = {
    "divan": {
        "baslik": "Divan ve klasik Türk şiiri",
        "kaynak_id": "edebiyat_katman_divan",
        "parcalar": [
            (
                "Divan geleneği",
                "Divan şiiri aruz, mazmun ve nazım biçimleriyle (gazel, kaside, mesnevi) "
                "Osmanlı kültüründe yüzyıllarca sürdü. Dil: Osmanlı Türkçesi; sözlük ve şerh "
                "geleneği önemlidir. Rüzgar sayfa/cilt uydurmaz; fetva vermez.",
            ),
            (
                "Fuzûlî — çerçeve",
                "Fuzûlî (Bağdat çevresi, 16. yy.): gazel ve Leylâ vü Mecnûn ile anılır. "
                "Üç dilde yazan üstatlardan. Metinler kamu malıdır; bu paket özet/çerçevedir, "
                "tam divan değildir.",
            ),
            (
                "Bâkî ve Nedîm — çerçeve",
                "Bâkî: 16. yy. gazel üstadı. Nedîm: 18. yy. Lâle Devri zevki, şarkı ve gazel. "
                "İkisi de kamu malı klasik şairlerdir.",
            ),
            (
                "Yunus Emre — halk/tekke",
                "Yunus Emre Türkçe’de sade dil ve tasavvufî sevgi ile halk şiirinin köşe "
                "taşlarındandır; divan aruzundan ayrı bir çizgidir. Kamu malı.",
            ),
            (
                "Nazım biçimleri kısa sözlük",
                "Gazel: kısa, aşk/güzellik ağırlıklı. Kaside: övgü ve uzun biçim. "
                "Mesnevi: anlatı. Müstezat, rubai, tuyuğ gibi biçimler de görülür.",
            ),
        ],
    },
    "turk_donem": {
        "baslik": "Türk edebiyatı dönemleri",
        "kaynak_id": "edebiyat_katman_turk_donem",
        "parcalar": [
            (
                "Dönem haritası",
                "Kabaca sıra: halk ve divan (klasik) → Tanzimat → Servet-i Fünûn → "
                "Millî Edebiyat → Cumhuriyet / çağdaş. Sınırlar yumuşaktır; geçiş yazarları vardır.",
            ),
            (
                "Tanzimat",
                "Basın, tiyatro, roman ve makale ile Batı formları girer. Şinasi, Namık Kemal, "
                "Ziya Paşa, Ahmet Mithat öne çıkar. Kavram katmanı; tam roman metni yok.",
            ),
            (
                "Servet-i Fünûn ve Millî Edebiyat",
                "Servet-i Fünûn sanatlı üslûp ve bireysel temalar; Millî Edebiyat sade dil ve "
                "toplumsal/millî konular. Örnek adlar kavram düzeyinde anılır.",
            ),
            (
                "Cumhuriyet",
                "Roman, öykü, şiirde çeşitlilik artar. Bu rafta akım ve genel yönelim vardır; "
                "telifli çağdaş eser metni yüklenmez.",
            ),
        ],
    },
    "bati": {
        "baslik": "Batı edebiyatı (kamu malı / kavram)",
        "kaynak_id": "edebiyat_katman_bati",
        "parcalar": [
            (
                "Antik ve klasik",
                "Homeros destanları (İlyada, Odysseia) Batı anlatısının temelinde yer alır. "
                "Shakespeare tiyatrosu İngilizce klasiklerdendir; eserler kamu malı kabul edilir. "
                "Uzun çeviri dump’u yapılmaz.",
            ),
            (
                "Akımlar",
                "Klasizm, romantizm, realizm, natüralizm, modernizm: dönem ve üslûp çerçeveleri. "
                "Öğretici özet; telifli 20.–21. yy. roman metni yoktur.",
            ),
            (
                "Türk edebiyatına etki",
                "Tanzimat’tan itibaren çeviri ve form aktarımıyla Batı edebiyatı Türk yazınını "
                "etkilemiştir. Bu ilişki kavram olarak not edilir.",
            ),
        ],
    },
    "yakin_donem": {
        "baslik": "Yakın dönem edebiyat (yalnızca kavram)",
        "kaynak_id": "edebiyat_katman_yakin",
        "parcalar": [
            (
                "Politika",
                "Yakın/çağdaş katmanda canlı yazar metni ve telifli eser alıntısı yoktur. "
                "Yalnızca dönem, akım ve genel yönelim özeti bulunur.",
            ),
            (
                "Yönelimler",
                "Modernizm sonrası çoğulculuk, kent anlatısı, kimlik ve dil deneyleri sık anılır. "
                "Somut eser metni için kullanıcı kendi yasal kaynağına yönlendirilir.",
            ),
        ],
    },
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_katman(key: str, spec: dict) -> dict:
    dest = KAT / key
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    parts = spec["parcalar"]
    body = [
        f"# {spec['baslik']}",
        "",
        "Kaynak: Rüzgar edebiyat Faz 2 (eğitim özeti). Fetva değildir. "
        "Telifli modern tam metin yoktur. Sayfa/cilt uydurulmaz.",
        "",
    ]
    for i, (title, text) in enumerate(parts, 1):
        body += [f"## {i}. {title}", "", text, ""]
    batch = incr / f"{key}_batch_0001.md"
    batch.write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": key,
        "baslik": spec["baslik"],
        "kaynak_id": spec["kaynak_id"],
        "ilim_alani": "edebiyat_sanat",
        "faz": 2,
        "dil": "tr",
        "dosya_yolu": f"knowledge/ortak_kaynak/alanlar/edebiyat_sanat/katmanlar/{key}",
        "guvenilirlik": "orta",
        "kaynak_sinifi": "kalici",
        "durum": "hazir",
        "kaynak": "Rüzgar Faz2 özet + kamu malı çerçeve",
        "parca_sayisi": len(parts),
        "batch_sayisi": 1,
        "updated_utc": _utc(),
        "politika": "Telifli modern metin yok. Fetva yok.",
    }
    (dest / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return man


def _update_ortak(man: dict) -> None:
    data = json.loads(ORTAK.read_text(encoding="utf-8")) if ORTAK.is_file() else {"kayitlar": []}
    rows = data.get("kayitlar") or []
    entry = {
        "kaynak_id": man["kaynak_id"],
        "kaynak_adi": man["baslik"],
        "yazar": None,
        "ilim_alani": "edebiyat_sanat",
        "eser_turu": "katman",
        "dil": "tr",
        "yayin": None,
        "cilt": None,
        "bolum": None,
        "sayfa": None,
        "dosya_yolu": man["dosya_yolu"],
        "guvenilirlik": "orta",
        "kaynak_sinifi": "kalici",
        "durum": "hazir",
        "not": "Edebiyat Faz 2 katman; telifli modern metin yok.",
    }
    found = False
    for r in rows:
        if r.get("kaynak_id") == man["kaynak_id"]:
            r.update(entry)
            found = True
            break
    if not found:
        rows.append(entry)
    data["kayitlar"] = rows
    data["guncelleme"] = _utc()
    ORTAK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _merge_catalog(faz2_rows: list[dict]) -> None:
    base = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.is_file() else {
        "domain": "edebiyat_sanat",
        "eserler": [],
        "sayilar": {},
    }
    base["faz"] = {"1": "openiti_arap", "2": "dil_donem_katman"}
    base["politika"] = (
        "2 fazlı raf. Faz1 OpenITI Arapça. Faz2 divan/Türk/batı/yakın kavram. "
        "Telifli modern tam metin yok. Fetva yok. Sayfa uydurma yasak."
    )
    base["updated_utc"] = _utc()
    base["faz2_katmanlar"] = faz2_rows
    base["sayilar"] = dict(base.get("sayilar") or {})
    base["sayilar"]["faz2_katman"] = len(faz2_rows)
    base["sayilar"]["kavram_faz2"] = len(FAZ2_KAVRAMLAR)
    CATALOG.write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_F2.write_text(
        json.dumps(
            {
                "domain": "edebiyat_sanat_faz2",
                "updated_utc": _utc(),
                "katmanlar": faz2_rows,
                "kavram_sayisi": len(FAZ2_KAVRAMLAR),
                "politika": base["politika"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    KAT.mkdir(parents=True, exist_ok=True)
    faz2_rows: list[dict] = []
    for key, spec in KATMAN_BATCHES.items():
        print(f">> katman {key}")
        man = _write_katman(key, spec)
        _update_ortak(man)
        faz2_rows.append(man)
        print(f"  [ok] parca={man['parca_sayisi']}")

    all_kav = FAZ1_KAVRAMLAR + FAZ2_KAVRAMLAR
    KAV.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in all_kav) + "\n",
        encoding="utf-8",
    )
    _merge_catalog(faz2_rows)

    readme = OUT / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.is_file() else "# Edebiyat\n"
    if "Faz 2" not in prev:
        prev = prev.rstrip() + (
            "\n\n## Faz 2 — dil/dönem katmanları\n\n"
            "- `katmanlar/divan` — divan/halk klasik çerçeve\n"
            "- `katmanlar/turk_donem` — Tanzimat → Cumhuriyet kavram\n"
            "- `katmanlar/bati` — batı klasik/akım kavram\n"
            "- `katmanlar/yakin_donem` — yalnızca akım (telifli metin yok)\n"
            "- Script: `faz12b_edebiyat_katman_ingest.py`\n"
            "- Katalog: `catalog_faz2.json`\n"
        )
        readme.write_text(prev + "\n", encoding="utf-8")

    print(
        f"\nTOPLAM faz2 katman={len(faz2_rows)} kavram_faz2={len(FAZ2_KAVRAMLAR)} "
        f"kavram_toplam={len(all_kav)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
