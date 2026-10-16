# -*- coding: utf-8 -*-
"""Faz 20 — programlama dilleri.

HTML, CSS, JavaScript, Python. Her dilde: nedir, dosya düzeni, çalıştırma, sınama.
Üstüne statik site ve küçük Python uygulaması.
Eğitim özeti. Telifli tam metin yok. Saldırı/exploit yok.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilgisayar_muhendisligi"
KAT = OUT / "katmanlar" / "programlama_dilleri"
KAV = OUT / "kavramlar_bilgisayar.jsonl"
CATALOG = OUT / "catalog.json"
README = OUT / "README.md"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"

KATMAN_ID = "programlama_dilleri"
FAZ = "20"
BASLIK = "Programlama dilleri"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# (id, başlık, alias listesi, metin)
PARCALAR: list[tuple[str, str, list[str], str]] = [
    (
        "html_dili",
        "HTML dili",
        ["html", "html dili", "html nedir", "hiper metin isaretleme"],
        "HTML, tarayıcının okuduğu belge iskeletidir. Etiketler metni başlık, paragraf, bağlantı, liste ve görsele ayırır. Tarayıcı etiketleri bir ağaç kurar; görünür sayfa bu ağacın çizimidir. HTML hesap yapmaz. Stil CSS'tedir, davranış JavaScript'tedir. Bu not sayfa yapısını öğretir.",
    ),
    (
        "html_dosya_duzeni",
        "HTML dosya düzeni",
        ["html dosya duzeni", "html dosyalari", "html klasor", "html dosyalari nasil durur", "html dosyaları nasıl durur"],
        "Küçük bir sitede kökte index.html durur. css/ klasörü stilleri, js/ klasörü betikleri, images/ görselleri tutar. index.html bu dosyaları göreli yolla çağırır: css/site.css ve js/site.js. İsimler küçük harf ve tire ile kalırsa adres karışmaz. Bir sayfa bir işi anlatır. Bu düzen sunucu kurmadan klasörde durur.",
    ),
    (
        "html_calistirma",
        "HTML çalıştırma",
        ["html calistirma", "html nasil calistirilir", "html nasıl çalıştırılır", "html nasil acilir", "html tarayici"],
        "HTML çalıştırmak, dosyayı tarayıcıda açmaktır. index.html dosyasına çift tıklamak veya tarayıcıya sürüklemek yeter. Adres çubuğunda file ile yerel yol görünür. Bağlantılar aynı klasöre göreli ise sayfalar birbirini açar. Ayrı bir derleyici gerekmez. Bu yol kendi dosyanı gösterir.",
    ),
    (
        "html_sinama",
        "HTML sınama",
        ["html sinama", "html nasil sinanir", "html nasıl sınanır", "html denetim"],
        "Sınama, belgenin beklenen iskeleti taşıyıp taşımadığına bakmaktır. Başlık etiketi var mı, bağlantı gerçek bir dosyaya mı gidiyor, görselin alternatif metni yazılmış mı. Tarayıcıda sayfayı açıp başlık ve bağlantıyı kontrol etmek ilk sınavdır. Eksik kapanan etiket ağacı bozar. Bu sınama güvenlik taraması değildir.",
    ),
    (
        "css_dili",
        "CSS dili",
        ["css", "css dili", "css nedir", "basamakli stil"],
        "CSS, HTML ağacındaki kutuların görünüşünü söyler. Seçici hangi elemanı tutacağını, bildirim rengi, boşluğu, yazı boyutunu ve dizilişi söyler. Aynı seçici sonra gelirse öncekini ezer. HTML iskelet kalır; CSS değişince içerik aynı kalır, görünüş değişir. CSS dosya silmez. Bu not görünüş sözleşmesini öğretir.",
    ),
    (
        "css_dosya_duzeni",
        "CSS dosya düzeni",
        ["css dosya duzeni", "css dosyalari", "css klasor", "css dosyalari nasil durur"],
        "Stil tek dosyada durabilir veya işe göre bölünür: temel.css yazı ve boşluk, yerlesim.css sıra ve ızgara, bilesen.css düğme ve kart. HTML head içinde sırayla bağlanır; sonra gelen dosya öncekini ezer. Sınıf adı işi söyler: baslik, kart, dugme. Sayfaya özel kural ayrı dosyada kalırsa ortak stil bozulmaz.",
    ),
    (
        "css_calistirma",
        "CSS çalıştırma",
        ["css calistirma", "css nasil calistirilir", "css nasıl çalıştırılır", "css nasil yuklenir"],
        "CSS ayrı bir program olarak çalışmaz. Tarayıcı, HTML'in bağladığı css dosyasını okur ve kutuları çizer. Dosyayı kaydedip sayfayı yenilemek yeni görünüşü getirir. Yol yanlışsa stil gelmez. Canlı önizleme için dosyayı yine tarayıcıda açmak yeter.",
    ),
    (
        "css_sinama",
        "CSS sınama",
        ["css sinama", "css nasil sinanir", "css nasıl sınanır", "css denetim"],
        "Sınama, seçicinin doğru kutuyu tutup tutmadığına ve dar ekranda taşma olup olmadığına bakmaktır. Başlık boyutu, düğme kontrastı ve iki kutunun yan yana durması tarayıcıda kontrol edilir. Aynı sınıf iki yerde farklı iş görüyorsa ad ayrılır. Bozuk yol, stil dosyasının hiç yüklenmemesidir. Bu sınama başkasının sayfasını bozmak için kullanılmaz.",
    ),
    (
        "javascript_dili",
        "JavaScript dili",
        ["javascript", "javascript dili", "javascript nedir", "js dili"],
        "JavaScript, tarayıcıda sayfanın davranışıdır. Düğmeye basılınca metin değişir, listeye satır eklenir, form gönderilmeden önce boş alan uyarılır. Değerler değişkende durur, fonksiyon işi böler, koşul ve döngü tekrarlar. Sayfa yüklenince betik çalışır. Hesap ve etkileşim içindir. İşletim sistemine serbest komut vermek bu notun konusu değildir.",
    ),
    (
        "javascript_dosya_duzeni",
        "JavaScript dosya düzeni",
        ["javascript dosya duzeni", "js dosyalari", "javascript klasor", "javascript dosyalari nasil durur"],
        "Betik js/site.js içindedir. HTML sonunda script etiketi ile bağlanır ki belge önce kurulsun, betik sonra elemanı arasın. Küçük işte tek dosya yeter. Büyüyünce saf fonksiyonlar bir dosyada, sayfa bağları başka dosyada durur. İsimler işi söyler. Gizli anahtar ve parola betiğin içine yazılmaz.",
    ),
    (
        "javascript_calistirma",
        "JavaScript çalıştırma",
        ["javascript calistirma", "javascript nasil calistirilir", "javascript nasıl çalıştırılır", "js nasil calistirilir", "node ile javascript"],
        "Tarayıcı, HTML'in gösterdiği js dosyasını yükleyip çalıştırır. Sayfayı yenilemek betiği yeniden okur. Hata olursa tarayıcının konsolu satır numarasını yazar. Node kuruluysa tarayıcıya bağlı olmayan dosya node js/site.js ile de çalışır. document çağrısı Node'da yoktur. İlk deneme için sayfayı tarayıcıda açmak yeter.",
    ),
    (
        "javascript_sinama",
        "JavaScript sınama",
        ["javascript sinama", "javascript nasil sinanir", "javascript nasıl sınanır", "js nasil sinanir"],
        "Sınama, fonksiyonun belirli girdiye belirli çıktı vermesidir. Saf bir fonksiyon tarayıcı olmadan da çağrılır: boş metin yanlış, dolu metin doğru. Sayfada ise düğmeye basıp metnin değiştiği gözlenir. Konsoldaki kırmızı satır hangi çağrının kırıldığını gösterir. Bir anda hem hesabı hem sayfayı değiştirmek hatayı gizler. Bu sınama başkasının oturumunu ele geçirmez.",
    ),
    (
        "python_dili",
        "Python dili",
        ["python", "python dili", "python nedir"],
        "Python, metin olarak yazılan ve yorumlayıcının çalıştırdığı dildir. Değişkenler değeri tutar, fonksiyon işi adlandırır, liste ve sözlük veriyi taşır. Girinti bloğu belirler. Küçük araç, hesap ve dosya okuma için uygundur. Standart kütüphane dosya, yol ve tarih işini hazır getirir. Bu not dili öğretir. Sisteme zarar veren komut yazılmaz.",
    ),
    (
        "python_dosya_duzeni",
        "Python dosya düzeni",
        ["python dosya duzeni", "python dosyalari", "python klasor", "python dosyalari nasil durur"],
        "Küçük araçta kökte uygulama.py durur. İş büyüyünce paket klasörü açılır: uygulama/cekirdek.py ve tests/test_cekirdek.py. Gereken dış paket requirements.txt içine ad ve sürümle yazılır. Veri data/ altında, üretilen çıktı cikti/ altında kalır. Kaynak ile üretilen dosya karışmaz. Gizli anahtar koda yazılmaz; ortam değişkeninde durur.",
    ),
    (
        "python_calistirma",
        "Python çalıştırma",
        ["python calistirma", "python nasil calistirilir", "python nasıl çalıştırılır", "python nasil kosulur", "sanal ortam"],
        "Kurulu yorumlayıcı python uygulama.py ile dosyayı çalıştırır. Sürüm python --version ile görülür. Proje klasöründe sanal ortam açılır: python -m venv .venv. Ortam etkinleştirilir ve pip install -r requirements.txt ile bağımlılık iner. Çalıştırma o ortamın python'u ile yapılır. Böylece bu projenin paketleri sistemdekileri ezmez.",
    ),
    (
        "python_sinama",
        "Python sınama",
        ["python sinama", "python nasil sinanir", "python nasıl sınanır", "pytest nasil calisir", "python test"],
        "Sınama, küçük fonksiyonu sabit girdiye bağlar. tests/test_cekirdek.py içinde beklenen sonuç assert ile yazılır. Komut python -m pytest proje klasöründe çalışır. Önce başarısız testi görmek, sonra kodu ona uydurmak hatayı erken gösterir. Sözdizimi python -m compileall uygulama ile de okunur. Test kendi fonksiyonunu ölçer.",
    ),
    (
        "statik_site_kurulumu",
        "Statik site kurulumu",
        ["statik site", "statik site kurulumu", "site nasil kurulur", "site nasıl kurulur", "site nasil yapilir", "html site"],
        "Statik site, sunucuda hesap olmadan tarayıcının okuduğu dosya kümesidir. Kökte index.html, css/site.css ve js/site.js durur. HTML başlık ve bölümleri kurar, CSS görünüşü bağlar, JavaScript yalnız gerekli etkileşimi ekler. Sayfalar göreli bağlantı ile birbirini açar. Klasörü tarayıcıda açmak kurulumu doğrular. Yayınlamak bu klasörü bir dosya sunucusuna kopyalamaktır. Formun kalıcı kaydı ve gizli anahtar bu iskelette yoktur.",
    ),
    (
        "kucuk_python_uygulamasi",
        "Küçük Python uygulaması",
        ["kucuk python uygulamasi", "kucuk uygulama nasil kurulur", "küçük uygulama nasıl kurulur", "python uygulamasi nasil kurulur", "kucuk uygulama"],
        "Küçük uygulama tek işi yapan komut satırı aracıdır. Önce iş bir cümlede yazılır: metin dosyasındaki satır sayısını bas. uygulama.py argümanı okur, dosyayı açar, sayıyı basar. tests/ aynı sayıyı sabit bir örnek dosyayla bekler. python -m pytest geçince araç biter. Klasör düzeni, sanal ortam ve requirements.txt bir arada durur. Araç kendi dosyanı okur.",
    ),
]


def _rows() -> list[dict]:
    out = []
    for kid, title, aliases, metin in PARCALAR:
        out.append(
            {
                "id": kid,
                "baslik": title,
                "aliases": aliases,
                "metin": metin,
                "kaynak_notu": f"Faz {FAZ} — {title}.",
            }
        )
    return out


def _write_layer() -> dict:
    incr = KAT / "incremental"
    incr.mkdir(parents=True, exist_ok=True)
    body = [
        f"# {BASLIK}",
        "",
        f"Kaynak: Rüzgar bilgisayar mühendisliği Faz {FAZ}. Eğitim özeti. Exploit yok.",
        "",
    ]
    for i, (_kid, title, _aliases, metin) in enumerate(PARCALAR, 1):
        body += [f"## {i}. {title}", "", metin, ""]
    (incr / "programlama_dilleri_batch_0001.md").write_text("\n".join(body), encoding="utf-8")
    man = {
        "katman_id": KATMAN_ID,
        "baslik": BASLIK,
        "kaynak_id": "bm_katman_diller",
        "ilim_alani": "bilgisayar_muhendisligi",
        "faz": FAZ,
        "dil": "tr",
        "dosya_yolu": "knowledge/ortak_kaynak/alanlar/bilgisayar_muhendisligi/katmanlar/programlama_dilleri",
        "parca_sayisi": len(PARCALAR),
        "updated_utc": _utc(),
        "durum": "hazir",
    }
    (KAT / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return man


def _merge_kavram() -> int:
    order: list[str] = []
    raw_line: dict[str, str] = {}
    if KAV.is_file():
        for line in KAV.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            kid = str(row.get("id") or "").strip()
            if not kid or kid in raw_line:
                continue
            order.append(kid)
            raw_line[kid] = line
    for row in _rows():
        kid = row["id"]
        if kid not in raw_line:
            order.append(kid)
        raw_line[kid] = json.dumps(row, ensure_ascii=False)
    KAV.write_text("\n".join(raw_line[i] for i in order) + "\n", encoding="utf-8")
    return len(order)


def _update_catalog(kavram: int) -> None:
    cat = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.is_file() else {}
    layers = list(cat.get("katmanlar") or [])
    if KATMAN_ID not in layers:
        layers.append(KATMAN_ID)
    notes = list(OUT.glob("katmanlar/*/incremental/*.md"))
    chars = sum(len(p.read_text(encoding="utf-8")) for p in OUT.rglob("*.md"))
    cat["domain"] = "bilgisayar_muhendisligi"
    cat["updated_utc"] = _utc()
    cat["politika"] = "Eğitim özeti. Telifli tam metin yok. Saldırı/exploit yok."
    cat["katmanlar"] = layers
    cat["sayilar"] = {
        "md_dosya": len(notes),
        "karakter": chars,
        "kavram": kavram,
    }
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _update_readme(kavram: int, notes: int) -> None:
    text = README.read_text(encoding="utf-8") if README.is_file() else "# Bilgisayar mühendisliği\n"
    block = (
        "## Faz 20 — programlama dilleri\n"
        "`katmanlar/programlama_dilleri`\n\n"
        "HTML, CSS, JavaScript, Python. Her dilde dört not: nedir, dosya düzeni, çalıştırma, sınama. "
        "Ayrıca statik site kurulumu ve küçük Python uygulaması.\n"
    )
    if "Faz 20" not in text:
        needle = "`katmanlar/programlama_uzmanlik`\n"
        if needle in text:
            text = text.replace(needle, needle + "\n" + block + "\n", 1)
        else:
            text += "\n" + block
    import re

    text = re.sub(
        r"MD: \*\*\d+\*\* · Kavram: \*\*\d+\*\*",
        f"MD: **{notes}** · Kavram: **{kavram}**",
        text,
        count=1,
    )
    if "faz20_programlama_dilleri_ingest.py" not in text:
        text = text.replace(
            "`faz16_bilgisayar_muhendisligi_ingest.py`",
            "`faz16_bilgisayar_muhendisligi_ingest.py` · `faz20_programlama_dilleri_ingest.py`",
            1,
        )
    README.write_text(text, encoding="utf-8")


def _update_kayit(man: dict) -> None:
    if not ORTAK.is_file():
        return
    raw = ORTAK.read_text(encoding="utf-8")
    if '"kaynak_id": "bm_katman_diller"' in raw:
        return
    entry = (
        "    {\n"
        '      "kaynak_id": "bm_katman_diller",\n'
        f'      "kaynak_adi": "{man["baslik"]}",\n'
        '      "yazar": null,\n'
        '      "ilim_alani": "bilgisayar_muhendisligi",\n'
        '      "eser_turu": "katman",\n'
        '      "dil": "tr",\n'
        '      "yayin": null,\n'
        '      "cilt": null,\n'
        '      "bolum": null,\n'
        '      "sayfa": null,\n'
        f'      "dosya_yolu": "{man["dosya_yolu"]}",\n'
        '      "guvenilirlik": "orta",\n'
        '      "kaynak_sinifi": "kalici",\n'
        '      "durum": "hazir",\n'
        '      "not": "Faz 20; eğitim; exploit yok."\n'
        "    },\n"
    )
    needle = '"kaynak_id": "bm_katman_uzmanlik"'
    idx = raw.find(needle)
    if idx < 0:
        return
    end = raw.find("    },", idx)
    if end < 0:
        return
    end = end + len("    },")
    raw = raw[:end] + "\n" + entry + raw[end:]
    import re

    raw = re.sub(
        r'"guncelleme": "[^"]*"',
        f'"guncelleme": "{_utc()}"',
        raw,
        count=1,
    )
    ORTAK.write_text(raw, encoding="utf-8")


def main() -> int:
    man = _write_layer()
    kavram = _merge_kavram()
    _update_catalog(kavram)
    notes = len(list(OUT.glob("katmanlar/*/incremental/*.md")))
    _update_readme(kavram, notes)
    _update_kayit(man)
    print(f"Faz 20 parca={len(PARCALAR)} kavram={kavram} not={notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
