# -*- coding: utf-8 -*-
"""Hadis Faz 5b — usûl + tarihçe + muhaddis biyografileri.

Kaynaklar (staging):
  - مقدمة ابن الصلاح (hdith full.md + Archive OCR yedek)
  - نخبة الفكر (Archive OCR)

Çıktı:
  knowledge/ilim/din/05_hadis/
    usul_tarih/{ibn_salah,nukhba}/incremental/*.md
    incremental/hadis_tarihce_tr.md
    incremental/muhaddisler_tr.md
    kavramlar_hadis.jsonl  (genişletilmiş)
    catalog_usul.json
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "05_hadis" / "usul_tarih"
OUT = ROOT / "knowledge" / "ilim" / "din" / "05_hadis"
USUL = OUT / "usul_tarih"
INCR = OUT / "incremental"
KAV = OUT / "kavramlar_hadis.jsonl"

CHUNK = 1600
OVERLAP = 120


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _arabic_ratio(s: str) -> float:
    ar = len(re.findall(r"[\u0600-\u06FF]", s))
    lat = len(re.findall(r"[A-Za-z]", s))
    tot = ar + lat
    return (ar / tot) if tot else 0.0


def _clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]{2,}", " ", text)
    return text.strip()


def _chunk(text: str, target: int = CHUNK) -> list[str]:
    text = _clean(text)
    if not text:
        return []
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > target * 2:
            if buf:
                chunks.append(buf.strip())
                buf = ""
            for i in range(0, len(p), target - OVERLAP):
                piece = p[i : i + target].strip()
                if piece and (_arabic_ratio(piece) >= 0.25 or len(piece) > 80):
                    chunks.append(piece)
            continue
        if len(buf) + len(p) + 2 <= target:
            buf = f"{buf}\n\n{p}".strip() if buf else p
        else:
            if buf:
                chunks.append(buf.strip())
            buf = p
    if buf:
        chunks.append(buf.strip())
    return chunks


def _write_batches(
    dest: Path,
    *,
    eser_id: str,
    title: str,
    yazar: str,
    chunks: list[str],
    kaynak: str,
) -> int:
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    n = 0
    for i, ch in enumerate(chunks, 1):
        n += 1
        body = (
            f"# {title} — paket {i:04d}\n\n"
            f"Yazar: {yazar}\n"
            f"Kaynak: {kaynak}\n\n"
            f"{ch}\n"
        )
        (incr / f"{eser_id}_batch_{i:04d}.md").write_text(body, encoding="utf-8")
    return n


def _extract_hdith_ibn_salah(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    # YAML ön yüzü atla
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            raw = parts[2]
    # blockquote satırlarını düz metne çevir
    lines: list[str] = []
    for line in raw.splitlines():
        if line.startswith("> "):
            lines.append(line[2:])
        elif line.startswith(">"):
            lines.append(line[1:].lstrip())
        elif line.startswith("#") or line.startswith("**") or line.startswith("###"):
            # başlıkları koru ama sadeleştir
            lines.append(re.sub(r"^#+\s*", "", line).strip())
        else:
            lines.append(line)
    text = "\n".join(lines)
    # İngilizce/ön meta kırp
    text = re.sub(r"title:.*\n", "", text)
    return _clean(text)


def _extract_ocr(path: Path, *, min_ar: float = 0.20) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    # Archive djvu.txt bazen HTML/meta taşır
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"https?://\S+", " ", raw)
    paras = []
    for p in re.split(r"\n{2,}", raw):
        p = _clean(p)
        if len(p) < 40:
            continue
        if _arabic_ratio(p) >= min_ar:
            paras.append(p)
    return "\n\n".join(paras)


def _ingest_arabic_books() -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    USUL.mkdir(parents=True, exist_ok=True)

    # 1) Ibn Salah — hdith birincil (OCR HTML tuzaklarını atla)
    hdith = STAGE / "ibn_salah_muqaddima.hdith.md"
    dest = USUL / "ibn_salah"
    dest.mkdir(parents=True, exist_ok=True)
    if not hdith.is_file():
        raise FileNotFoundError("İbnü's-Salâh hdith metni staging'de yok")
    text = _extract_hdith_ibn_salah(hdith)
    chunks = _chunk(text)
    n = _write_batches(
        dest,
        eser_id="ibn_salah",
        title="Mukaddimetü İbnü's-Salâh (Ulûmü'l-hadîs)",
        yazar="İbnü's-Salâh (Osmân b. Abdirrahmân eş-Şehrezûrî, ö. 643/1245)",
        chunks=chunks,
        kaynak=f"staging:{hdith.name}",
    )
    man = {
        "eser_id": "ibn_salah",
        "eser_tr": "Mukaddimetü İbnü's-Salâh",
        "eser_ar": "مقدمة ابن الصلاح / علوم الحديث",
        "yazar": "İbnü's-Salâh",
        "konu": "usul_hadis",
        "hadis_ilmi_turleri": 65,
        "batch_sayisi": n,
        "char_count": len(text),
        "sha256": _sha(hdith),
        "updated_utc": _utc(),
    }
    (dest / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifests.append(man)
    print(f"  [ok] ibn_salah: {n} paket, {len(text)} char")

    # 2) Nukhba — temiz matın dosyası
    nukhba = STAGE / "nukhba_matn_ar.md"
    dest2 = USUL / "nukhba"
    dest2.mkdir(parents=True, exist_ok=True)
    if nukhba.is_file():
        text2 = _clean(nukhba.read_text(encoding="utf-8"))
        chunks2 = _chunk(text2, target=1200)
        n2 = _write_batches(
            dest2,
            eser_id="nukhba",
            title="Nuhbetü'l-fiker (İbn Hacer)",
            yazar="İbn Hacer el-Askalânî (ö. 852/1449)",
            chunks=chunks2,
            kaynak=f"staging:{nukhba.name}",
        )
        man2 = {
            "eser_id": "nukhba",
            "eser_tr": "Nuhbetü'l-fiker",
            "eser_ar": "نخبة الفكر في مصطلح أهل الأثر",
            "yazar": "İbn Hacer el-Askalânî",
            "konu": "usul_hadis",
            "batch_sayisi": n2,
            "char_count": len(text2),
            "sha256": _sha(nukhba),
            "updated_utc": _utc(),
        }
        (dest2 / "manifest.json").write_text(
            json.dumps(man2, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifests.append(man2)
        print(f"  [ok] nukhba: {n2} paket, {len(text2)} char")
    else:
        print("  [skip] nukhba_matn_ar.md yok")

    # 3) Beykûniyye
    bayq = STAGE / "bayquniyya_matn_ar.md"
    dest3 = USUL / "bayquniyya"
    dest3.mkdir(parents=True, exist_ok=True)
    if bayq.is_file():
        text3 = _clean(bayq.read_text(encoding="utf-8"))
        chunks3 = _chunk(text3, target=1000)
        n3 = _write_batches(
            dest3,
            eser_id="bayquniyya",
            title="el-Manzûmetü'l-Beykûniyye",
            yazar="Ömer b. Muhammed el-Beykûnî",
            chunks=chunks3,
            kaynak=f"staging:{bayq.name}",
        )
        man3 = {
            "eser_id": "bayquniyya",
            "eser_tr": "Beykûniyye manzumesi",
            "eser_ar": "المنظومة البيقونية",
            "yazar": "el-Beykûnî",
            "konu": "usul_hadis",
            "batch_sayisi": n3,
            "char_count": len(text3),
            "sha256": _sha(bayq),
            "updated_utc": _utc(),
        }
        (dest3 / "manifest.json").write_text(
            json.dumps(man3, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifests.append(man3)
        print(f"  [ok] bayquniyya: {n3} paket, {len(text3)} char")
    else:
        print("  [skip] bayquniyya yok")

    return manifests


def _kavram_rows() -> list[dict[str, Any]]:
    note = (
        "Kaynak: klasik hadis usûlü/tarihçe özeti (İbnü's-Salâh Mukaddime, "
        "İbn Hacer Nuhbe, Kutüb-i Sitte literatürü). Fetva değildir."
    )
    rows: list[dict[str, Any]] = [
        {
            "id": "hadis",
            "baslik": "hadis",
            "aliases": ["hadis nedir", "hadîs", "sünnet nedir", "hadis ilmi"],
            "metin": (
                "Hadis (حديث), Hz. Peygamber'in söz, fiil, takrir ve sıfatlarını "
                "nakleden rivayettir. Hadis ilmi isnad, metin, cerh-ta'dil ve "
                "tasnif usûllerini kapsar. Rüzgar'da Kutüb-i Sitte matınları "
                "ayrı raflarda; usûl/tarihçe İbnü's-Salâh ve Nuhbe ile desteklenir."
            ),
        },
        {
            "id": "kutub_i_sitte",
            "baslik": "kutub-i sitte",
            "aliases": ["kütüb-i sitte", "kutubi sitte", "altı kitap"],
            "metin": (
                "Kutüb-i Sitte: Buhârî, Müslim, Ebû Dâvûd, Tirmizî, Nesâî, İbn Mâce. "
                "İlk ikisi Sahîhayn; diğerleri sünen/câmi geleneğindedir."
            ),
        },
        {
            "id": "tedvin",
            "baslik": "tedvin",
            "aliases": [
                "tedvin nedir",
                "hadis tedvini",
                "hadislerin toplanması",
                "hadis nasıl toplandı",
                "sünnetin yazılması",
            ],
            "metin": (
                "Tedvin (تدوين), hadislerin sistemli yazıya geçirilmesidir. "
                "Sahâbe döneminde bireysel yazım vardı; yaygın resmi tedvin "
                "Ömer b. Abdülazîz (ö. 101/720) emriyle hızlandı. Sonra "
                "musned, musannef, câmi ve sünen tasnifleri doğdu; III/IX. "
                "asırda Kutüb-i Sitte olgunlaştı."
            ),
        },
        {
            "id": "hadis_tarihce",
            "baslik": "hadis tarihcesi",
            "aliases": [
                "hadis tarihi",
                "hadis tarihçesi",
                "hadislerin tarihi",
                "sünnet tarihi",
                "ulum hadis tarihi",
            ],
            "metin": (
                "Hadis tarihçesi kabaca: (1) Peygamber ve sahâbe rivayeti, "
                "(2) tâbiîn seyahat ve semâ, (3) II. asırda resmi tedvin ve "
                "musnedler, (4) III. asırda sahih/sünen külliyatı, (5) "
                "sonraki asırlarda şerh, ricâl ve mustalah kitapları. "
                "Kimlerin nasıl topladığı: semâ/kitâbet, rihle, şeyh listeleri "
                "ve cerh-ta'dil ile süzülür."
            ),
        },
        {
            "id": "rihle",
            "baslik": "rihle",
            "aliases": ["rihle nedir", "hadis yolculugu", "talepül ilm"],
            "metin": (
                "Rihle: isnadı yükseltmek ve semâ almak için yapılan ilim "
                "yolculuğu. Muhaddisler şehir şehir dolaşarak şeyhlerden "
                "hadis yazdı; bu, külliyatların birikmesinin ana yoludur."
            ),
        },
        {
            "id": "sema",
            "baslik": "sema",
            "aliases": ["semâ", "sema nedir", "tahammul", "edâ"],
            "metin": (
                "Semâ (سماع): şeyhin okuması/okutmasıyla hadisi işiterek almak. "
                "Tahammül (alma) ve edâ (nakletme) usûlleri İbnü's-Salâh'ta "
                "ayrı türler halinde işlenir; kitâbet, icâzet, münâvele vb. "
                "yöntemler de vardır."
            ),
        },
        {
            "id": "isnad",
            "baslik": "isnad",
            "aliases": ["isnad nedir", "sened", "senet"],
            "metin": (
                "İsnad, metne ulaşan râviler zinciridir. «Haddesenâ / ahberenâ» "
                "kalıplarıyla başlar; cerh-ta'dil ile değerlendirilir."
            ),
        },
        {
            "id": "metin_hadis",
            "baslik": "metin",
            "aliases": ["metin nedir", "hadis metni", "matn"],
            "metin": (
                "Metin (متن), hadisin söz/fiil kısmıdır. Rüzgar cevabında "
                "Arapça matın kaynak numarasıyla verilir."
            ),
        },
        {
            "id": "cerh_tadil",
            "baslik": "cerh tadil",
            "aliases": ["cerh", "ta'dil", "tadil", "ricâl", "rical ilmi"],
            "metin": (
                "Cerh ve ta'dil: râvilerin güvenilirliğini tenkit veya "
                "tescil etmektir. Sikât, zayıf, metrûk vb. hükümler ricâl "
                "kitaplarında toplanır; bu süzgeç olmadan külliyat olmaz."
            ),
        },
        {
            "id": "sahih",
            "baslik": "sahih",
            "aliases": ["sahih hadis", "sahîh"],
            "metin": (
                "Sahih: adâletli ve zabtı kuvvetli râvilerle muttasıl isnad; "
                "şâz ve muallel olmayan rivayet. Buhârî-Müslim şartları "
                "klasikte en yüksek kabul görmüştür."
            ),
        },
        {
            "id": "hasen",
            "baslik": "hasen",
            "aliases": ["hasen hadis"],
            "metin": (
                "Hasen: sahihe yakın; zabtı biraz daha zayıf kabul edilen "
                "ama isnadı muttasıl rivayet. Tirmizî tasnifinde sık geçer."
            ),
        },
        {
            "id": "zaif",
            "baslik": "zayıf",
            "aliases": ["zaif", "zayıf hadis", "daif"],
            "metin": (
                "Zayıf: sahih/hasen şartlarını taşımayan rivayet. Türleri "
                "çoktur (munkatı', mürsel…). Rüzgar hüküm vermez; kaynak "
                "gösterir."
            ),
        },
        {
            "id": "mevzu",
            "baslik": "mevzu",
            "aliases": ["mevzû", "uydurma hadis", "mevzu hadis"],
            "metin": (
                "Mevzû: uydurma hadis. İbnü's-Salâh'ta ayrı türdür; "
                "isnad/metin belirtileri ve mevzûât literatürü vardır."
            ),
        },
        {
            "id": "mutawatir",
            "baslik": "mutevatir",
            "aliases": ["mütevâtir", "mutawatir hadis"],
            "metin": (
                "Mütevâtir: yalan üzere birleşmeleri âdeten imkânsız "
                "kalabalık yollarla gelen haber. Âhâd ise bundan aşağı "
                "sayıdaki yollardır."
            ),
        },
        {
            "id": "ahad",
            "baslik": "ahad",
            "aliases": ["âhâd", "haber-i vahid", "haber i vahid"],
            "metin": (
                "Âhâd (haber-i vâhid): mütevâtir seviyesine ulaşmayan "
                "rivayet. Sahih, hasen veya zayıf olabilir; usûlde hüküm "
                "tartışmaları bu ayrımla bağlantılıdır."
            ),
        },
        {
            "id": "sahihayn",
            "baslik": "sahihayn",
            "aliases": ["sahîhayn", "iki sahih"],
            "metin": (
                "Sahîhayn: Sahîh-i Buhârî ve Sahîh-i Müslim. Ehl-i sünnet "
                "geleneğinde en sahih mecmualar kabul edilir."
            ),
        },
        {
            "id": "musned",
            "baslik": "musned",
            "aliases": ["müsned", "musned nedir"],
            "metin": (
                "Müsned: hadisleri sahâbî adlarına göre dizmek. Ahmed b. "
                "Hanbel'in Müsned'i en meşhur örnektir; Kutüb-i Sitte'den "
                "farklı bir tasnif tarzıdır."
            ),
        },
        {
            "id": "musannef",
            "baslik": "musannef",
            "aliases": ["musannef nedir", "tasnif"],
            "metin": (
                "Musannef/câmi/sünen: konuya göre (kitâb/bâb) düzenlenmiş "
                "külliyat. Abdurrezzâk ve İbn Ebî Şeybe musannefleri; "
                "sonra Buhârî-Müslim câmi', sünenler bu çizgidedir."
            ),
        },
        {
            "id": "ibn_salah",
            "baslik": "ibn salah",
            "aliases": [
                "ibnü salah",
                "ibnü's-salâh",
                "mukaddime ibn salah",
                "ulumul hadis",
                "ulûmü'l-hadîs",
            ],
            "metin": (
                "İbnü's-Salâh (ö. 643/1245): «Ulûmü'l-hadîs / Mukaddime» "
                "yazarı. 65 tür mustalahı bir araya getirdi; sonraki usûl "
                "kitaplarının omurgası oldu. Rüzgar raftı: `usul_tarih/ibn_salah`."
            ),
        },
        {
            "id": "ibn_hacer",
            "baslik": "ibn hacer",
            "aliases": ["ibn hacer", "ibn hajar", "nuhbe", "nukhba", "nuhbetül fiker"],
            "metin": (
                "İbn Hacer el-Askalânî (ö. 852/1449): «Nuhbetü'l-fiker» "
                "ile mustalahı özetledi; Fethu'l-Bârî ile Buhârî şerhi "
                "yazdı. Rüzgar raftı: `usul_tarih/nukhba`."
            ),
        },
        {
            "id": "buhari_eser",
            "baslik": "sahih-i buhari",
            "aliases": ["buhari nedir", "buhârî", "imam buhari", "sahih buhari"],
            "metin": (
                "İmam Buhârî (194–256/810–870): Buhara doğumlu. Rihle ile "
                "çok şeyhten semâ aldı; «el-Câmiu's-sahîh»i en sahih "
                "mecmua kabul edilir. Şartı sıkıdır (ittisâl + râvi "
                "güveni). Rüzgar raftı: `buhari`."
            ),
        },
        {
            "id": "muslim_eser",
            "baslik": "sahih-i muslim",
            "aliases": ["müslim", "muslim nedir", "imam muslim", "sahih muslim"],
            "metin": (
                "İmam Müslim (206–261/821–875): Nişabur. Buhârî çizgisinde "
                "sahih mecmua derledi; mukaddimesinde isnadın önemi ve "
                "râvi tenkidi vurgulanır. Rüzgar raftı: `muslim`."
            ),
        },
        {
            "id": "ebu_davud_eser",
            "baslik": "sunen ebu davud",
            "aliases": ["ebu davud", "ebû dâvûd", "sünen ebu davud"],
            "metin": (
                "Ebû Dâvûd (202–275/817–889): Sünen'inde fıkhî ahkâma "
                "ağırlık verdi; bazen sened hakkında kısa not düşer. "
                "Rüzgar raftı: `ebu_davud`."
            ),
        },
        {
            "id": "tirmizi_eser",
            "baslik": "cami tirmizi",
            "aliases": ["tirmizi", "tirmizî", "câmiu tirmizi"],
            "metin": (
                "Tirmizî (209–279/824–892): Câmi'inde hadis + hüküm/iller "
                "ve bazen «hasen» vb. notlar verir. Rüzgar raftı: `tirmizi`."
            ),
        },
        {
            "id": "nesai_eser",
            "baslik": "sunen nesai",
            "aliases": ["nesai", "nesâî", "sünen nesai"],
            "metin": (
                "Nesâî (215–303/830–915): el-Müctebâ süneni isnad "
                "titizliğiyle bilinir. Rüzgar raftı: `nesai`."
            ),
        },
        {
            "id": "ibn_mace_eser",
            "baslik": "sunen ibn mace",
            "aliases": ["ibn mace", "ibn mâce", "ibn majah"],
            "metin": (
                "İbn Mâce (209–273/824–887): Sünen'i Kutüb-i Sitte'nin "
                "altıncı kitabı kabul edilir. Rüzgar raftı: `ibn_mace`."
            ),
        },
        {
            "id": "omer_b_abdulaziz",
            "baslik": "omer bin abdulaziz",
            "aliases": [
                "ömer b. abdülaziz",
                "omer bin abdülaziz",
                "resmi tedvin",
            ],
            "metin": (
                "Ömer b. Abdülazîz (ö. 101/720): Medine ve vilayetlere "
                "hadislerin toplanıp yazılması yönünde resmi teşvikte "
                "bulundu; tedvin tarihinde dönüm noktası kabul edilir."
            ),
        },
        {
            "id": "zuhri",
            "baslik": "zuhri",
            "aliases": ["ibn şihab", "ibn şihab ez-zührî", "imam zuhri"],
            "metin": (
                "İbn Şihâb ez-Zührî (ö. 124/742): erken tedvin ve yazılı "
                "rivayet geleneğinin önde gelen tâbiîn muhaddislerindendir; "
                "sonraki külliyatlara giden yolların köprüsüdür."
            ),
        },
    ]
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "collection": "din_05_hadis_kavram",
                "baslik": r["baslik"],
                "aliases": r["aliases"],
                "metin": r["metin"],
                "kaynak_notu": note,
            }
        )
    return out


def _write_tr_layers(rows: list[dict[str, Any]]) -> None:
    INCR.mkdir(parents=True, exist_ok=True)
    with KAV.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    tarih = """# Hadis tedvini ve tarihçe (TR özet)

## 1. Sözlü–yazılı dönem (sahâbe)

Peygamber hayattayken ve hemen sonrasında hadisler hem ezber hem bireysel yazımla korundu. Bazı sahâbîler sahîfe tuttu; genel yazım yasağı tartışmaları bağlamlıdır (Kur'an ile karışma endişesi). Asıl ölçü isnad ve semâdır.

## 2. Resmi tedvin (I–II. asır)

Ömer b. Abdülazîz'in teşvikiyle vilayetlerde hadislerin toplanması hızlandı. Zührî gibi tâbiîn imamları yazılı birikimi sistemleştirdi. Rihle (ilim yolculuğu) ile şehirler arası semâ ağı kuruldu.

## 3. Tasnif çağları

- **Müsned**: sahâbî adına göre (Ahmed b. Hanbel).
- **Musannef / câmi' / sünen**: konuya (kitâb/bâb) göre.
- **III/IX. asır**: Buhârî ve Müslim sahih şartıyla; Ebû Dâvûd, Tirmizî, Nesâî, İbn Mâce sünen/câmi çizgisinde Kutüb-i Sitte'yi oluşturdu.

## 4. Usûl ve şerh çağı

İbnü's-Salâh Mukaddime'sinde 65 tür mustalah topladı. İbn Hacer Nuhbe ile özetledi; Buhârî'ye Fethu'l-Bârî yazdı. Ricâl, ilel ve şerh literatürü külliyatın nasıl okunacağını belirledi.

## 5. Rüzgar'da kullanım

Matın soruları: «buhari 1». Tarihçe/usûl: «tedvin nedir», «buhari kimdir», «ibn salah nedir». Fetva verilmez; kaynaklı özet + Arapça metin.

_Kaynak omurgası: İbnü's-Salâh, İbn Hacer, Kutüb-i Sitte literatürü._
"""
    (INCR / "hadis_tarihce_tr.md").write_text(tarih, encoding="utf-8")

    muh = """# Kutüb-i Sitte muhaddisleri — kısa tarihçe

## İmam Buhârî (194–256)

Buhara doğumlu. Genç yaşta rihleye çıktı; çok şeyhten semâ aldı. el-Câmiu's-sahîh'i kitâb/bâb düzeninde, sıkı ittisâl şartıyla derledi. «Sahih» ölçütünün pratik zirvesi kabul edilir.

## İmam Müslim (206–261)

Nişabur. Buhârî ile aynı çağın sahih mecmuası. Mukaddimesinde isnadın dindeki yeri ve râvi sınıfları anlatılır. Rivayetleri konulara göre gruplar.

## Ebû Dâvûd (202–275)

Sünen'inde ahkâm hadislerine ağırlık verdi. Bazı bâblarda sened hakkında kısa değerlendirme yapar; fıkıh talebesinin hadis kaynağıdır.

## Tirmizî (209–279)

Câmi': hadis + fıkhî yön ve bazen hasen/sahih notları. Mezhep görüşlerine kısa değinmeler klasik özelliğidir.

## Nesâî (215–303)

el-Müctebâ: isnad seçiminde titizliğiyle anılır. Sünen geleneğinin olgun örneği.

## İbn Mâce (209–287)

Sünen'i sonradan Kutüb-i Sitte'nin altıncısı kabul edildi. Diğer beşliye ek zengin bâblar içerir.

## Nasıl topladılar?

1. Semâ / kitâbet ile şeyhlerden alma  
2. Rihle ile coğrafi ağ  
3. Cerh-ta'dil süzgeci  
4. Kitâb-bâb (veya müsned) tasnifi  
5. İhtisar, seçme (sahih şartı) veya sünen kapsamı  

_Rüzgar: her eser ayrı raftadır; matın Arapça, biyografi/usûl TR+klasik metin._
"""
    (INCR / "muhaddisler_tr.md").write_text(muh, encoding="utf-8")

    kav_md = ["# Hadis kavramları (TR, geniş)", ""]
    for row in rows:
        kav_md.append(f"## {row['baslik']}")
        kav_md.append("")
        kav_md.append(row["metin"])
        kav_md.append("")
        kav_md.append(f"_{row['kaynak_notu']}_")
        kav_md.append("")
    (INCR / "hadis_kavramlar_tr.md").write_text("\n".join(kav_md), encoding="utf-8")


def main() -> int:
    print("=== Faz 5b — Hadis usûl + tarihçe ===")
    if not STAGE.is_dir():
        raise SystemExit(f"Staging yok: {STAGE}")
    man = _ingest_arabic_books()
    rows = _kavram_rows()
    _write_tr_layers(rows)
    print(f"kavramlar: {len(rows)}")

    catalog = {
        "domain": "din_05_hadis_usul_tarih",
        "updated_utc": _utc(),
        "eserler": man,
        "tr_layers": [
            "incremental/hadis_tarihce_tr.md",
            "incremental/muhaddisler_tr.md",
            "incremental/hadis_kavramlar_tr.md",
            "kavramlar_hadis.jsonl",
        ],
    }
    (OUT / "catalog_usul.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    readme = OUT / "README.md"
    extra = """

## Usûl + tarihçe

| Raf | İçerik |
|-----|--------|
| `usul_tarih/ibn_salah/` | Mukaddimetü İbnü's-Salâh (Arapça) |
| `usul_tarih/nukhba/` | Nuhbetü'l-fiker (Arapça matın) |
| `usul_tarih/bayquniyya/` | Beykûniyye manzumesi (Arapça) |
| `incremental/hadis_tarihce_tr.md` | Tedvin tarihçesi (TR) |
| `incremental/muhaddisler_tr.md` | Altı imam nasıl topladı (TR) |

İncegest: `python scripts/faz5b_hadis_usul_tarih_ingest.py`
"""
    base = readme.read_text(encoding="utf-8") if readme.is_file() else "# Din / 05 — Hadis\n"
    if "Usûl + tarihçe" not in base:
        readme.write_text(base.rstrip() + "\n" + extra, encoding="utf-8")
    print(f"çıkış: {USUL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
