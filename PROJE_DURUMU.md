# RÜZGAR — oturum özeti (kalıcı)

**Son güncelleme:** 2026-10-07 gece — RAG ortak alan boost

Bu dosya sohbet sıfırlanınca bağlamı taşımak için tutulur. Kapatmadan önce «durumu güncelle» denmesi yeterli (çarpı ile kapanışta otomatik yazılamaz).

### Kilit politika — 2 fazlı raf

- **Faz 1:** Canonical eserler (OpenITI / kamu malı) + anlık
- **Faz 2:** Dil/dönem/kavram katmanları (aynı oturumda; iskelet bırakıp kaçma yok)
- Telif: modern/yakın dönem **tam metin yok** — yalnızca kavram/özet + kamu malı çerçeve
- Felsefe/psikoloji/edebiyat/bilim/coğrafya/teknoloji: Faz 1+2 tamam

### Şimdi kaldığımız yer (öncelik)

1. ~~P2 / Ollama / tasavvuf anlık~~ — tamam
2. ~~Kimyâ anlık sapma~~ — `kimya-yi` / `kimya yi` Gazâlî yoluna düşüyor (smoke 10/10)
3. ~~Kimyâ dolgu~~ — IA Farsça OCR + EN (~2363 chunk, 4.8 MB)
4. ~~Arapça Fütûh/Feth~~ — Fütûh AR+EN (~580 chunk); Feth zaten AR'dı (etiket düzeltildi)
5. ~~İbnü'l-Arabî şerh (Câmî)~~ — `serh_ve_aciklama/jami_sharh_fusus` (~820 chunk)
6. ~~Nebula tarih batch~~ — ayrı commit `15fac9c` (200 dosya, yalnızca `nebula_batch_*.md`)
7. ~~Kâşânî + Kayserî mukaddime~~ — Kâşânî AR ~633; mukaddime EN ~356
8. ~~P2/Ollama/tasavvuf commit+push~~ — `d9a2b81` (+ nebula `15fac9c`) → `origin/main`
9. ~~Kur’ân ayet RAG~~ — push `180c679` · 416 batch · smoke PASS
10. ~~Kayserî tam AR şerh~~ — `qaysari_sharh_fusus` **1176** chunk · smoke PASS
11. ~~09 catalog sync~~ — `e200735`
12. ~~Felsefe Faz 1+2~~ — 7 OpenITI · 3 katman · **18 kavram** · smoke OK
13. ~~Psikoloji Faz 1+2~~ — 4 OpenITI · 3 katman · **13 kavram** · smoke OK
14. ~~Edebiyat Faz 1+2~~ — 7 OpenITI eser · 4 katman · 31 kavram · smoke 9/9
15. ~~Bilim Faz 1+2 + derin~~ — **40 md · ~17 KB · 34 kavram** · smoke 10/10
16. ~~Coğrafya Faz 1+2 + derin~~ — **18 md · ~7.6 KB · 28 kavram** · smoke 9/9
17. ~~Teknoloji Faz 1+2~~ — 10 md · 3 katman · 13 kavram · smoke 7/7
18. ~~RAG incremental~~ — **302.676** chunk · 177 dosya değişti · yerel indeks
19. ~~RAG ortak alan boost~~ — `rag_store.search` domain ipucu + yol eşlemesi; din baskınlığı kesildi
20. **Sonraki:** din rafları hijyeni (isteğe bağlı) · `RUZGAR_RAG_CONTENT_FILTER=0` env gözden geçir

### 2026-10-07 — RAG ortak alan boost

- `rag_store.search`: sorgu ipucu → `ortak_kaynak/alanlar/*` / fen rafları alt küme + skor boost
- Yol token eşlemesi (örn. `nefs_gucleri`, `bilimsel_yontem`, `yapay_zeka`)
- Domain-öncelikli birleştirme — `RUZGAR_RAG_CONTENT_FILTER=0` iken de çalışır
- Kapat: `RUZGAR_RAG_ORTAK_BOOST=0` · skor: `RUZGAR_RAG_ORTAK_BOOST_SCORE` (varsayılan 0.10)
- Smoke: Karadeniz / bilimsel yöntem / nefs güçleri / divan / yapay zekâ → doğru raf

### 2026-10-07 — RAG incremental (ortak alanlar)

- `build_index(incremental=True)` → status=incremental · chunks=**302676** · changed_files=**177**
- İndekste: `ortak_kaynak/alanlar` ~6641 · edebiyat ~3222 · felsefe eser ~2477 · psikoloji eser ~920
- Script: `scripts/rag_incremental_rebuild.py`
- `embeddings.npy` / `chunks.jsonl` gitignore — commit edilmez

### 2026-10-07 — Teknoloji (2 faz)

- Faz 1: `08_teknoloji` + OS/programlama/DNS-HTTP/şifre-2FA/YZ sınır
- Faz 2: güvenlik hijyeni · yazılım · YZ sınırları (exploit yok)
- Script: `faz15_teknoloji_raf_ingest.py` · Anlık: `ruzgar_teknoloji_kutuphane.py`

### 2026-10-07 — Felsefe Faz 2

- Katman: mektepler · kavramlar · dönem/antik köprü
- Kavram: Meşşâî, işrâk, kelâm–felsefe, metafizik, mantık, siyaset, ahlâk, nedensellik, Aristoteles–Platon
- Script: `faz10b_felsefe_faz2_ingest.py` · OpenITI Faz 1 korunur

### 2026-10-07 — Psikoloji Faz 2

- Katman: nefs güçleri · ahlâk bağı · klasik/klinik sınır
- Kavram: idrak, ahlâk–nefs, duygu klasik, nâtıka, işk; klinik teşhis uyarısı
- Script: `faz11b_psikoloji_faz2_ingest.py` · OpenITI Faz 1 korunur

### 2026-10-07 — Bilim derinleştirme (13b)

- +15 md: yıldız/Büyük Patlama · ısı/asit–baz/dalga · solunum/evrim · denklem/olasılık
- Kavram: 19 → **34** · Script: `faz13b_bilim_derin_ingest.py`
- Sınır: klinik teşhis yok · tehlikeli deney protokolü yok

### 2026-10-07 — Coğrafya derinleştirme (14b)

- +7 bölge ayrıntı · komşular/deniz · göller/platolar · dünya çerçevesi · fiziki–beşeri
- Kavram: 10 → **28** (bölgeler, İstanbul/Ankara/İzmir, boğazlar, kıtalar, Ortadoğu…)
- Script: `faz14b_cografya_derin_ingest.py`
- Hâlâ yok: il ansiklopedisi, güncel TÜİK tablosu (kasıtlı)

### 2026-10-07 — Coğrafya (2 faz)

- Faz 1: `04_cografya` + bölgeler + enlem/boylam
- Faz 2: harita okuryazarlığı · beşeri · İslâm coğrafya mirası
- Script: `faz14_cografya_raf_ingest.py` · Anlık: `ruzgar_cografya_kutuphane.py`

### 2026-10-07 — Bilim (2 faz)

- Faz 1: kutuphane `01/02/03/06` katalog + ek md (kara delik, Newton, DNA, yüzde)
- Faz 2: `bilimsel_yontem` · `islam_bilim_mirasi` · `disiplinler`
- Yol: `ortak_kaynak/alanlar/bilim/` · Script: `faz13_bilim_raf_ingest.py`
- Anlık: `ruzgar_bilim_kutuphane.py` + desktop/niyet gate
- Politika: eğitim özeti · tıbbi teşhis yok

### 2026-10-07 — Edebiyat Faz 2 (dil/dönem)

- Katmanlar: `katmanlar/divan` · `turk_donem` · `bati` · `yakin_donem`
- Kavram: divan/aruz/gazel + Fuzûlî/Bâkî/Nedîm/Yunus · Tanzimat→Cumhuriyet · batı (Homeros/Shakespeare/akımlar) · yakın dönem (yalnızca akım)
- Script: `faz12b_edebiyat_katman_ingest.py` · `catalog_faz2.json`
- Anlık smoke: divan/tanzimat/fuzuli/bati/shakespeare/yunus + Arap alias’lar OK
- Telif: modern roman metni yok

### 2026-10-07 — Edebiyat genişletme

- + Buḥturî Dîvân (57) · Maʿarrî Dîvân (461)
- Toplam: **7** eser · **1612** chunk

### 2026-10-07 — Edebiyat ve sanat (klasik Arap adab)

- Yol: `ortak_kaynak/alanlar/edebiyat_sanat/eserler/`
- OpenITI: Kelîle · Hemedânî/Harîrî Makâmât · Ebû Temmâm · Buḥturî · Maʿarrî · İbn Kuteybe Şiʿr
- Script: `faz12_edebiyat_openiti_ingest.py`
- Anlık: `ruzgar_edebiyat_kutuphane.py` + desktop early path + niyet gate

### 2026-10-07 — Psikoloji (klasik nefs / ahlâk)

- Yol: `ortak_kaynak/alanlar/psikoloji/eserler/`
- OpenITI: İbn Sînâ Şifâ-Nefs (357) · Ma'rifetü'n-nefs (11) · Gazâlî Mîzânü'l-amel (133) · Mâhiyyetü'l-işk (23)
- Toplam: **4** eser · **524** chunk
- Script: `faz11_psikoloji_openiti_ingest.py`
- Anlık: `ruzgar_psikoloji_kutuphane.py` + desktop early path + niyet gate
- Politika: klinik teşhis değildir · fetva yok · sayfa uydurma yasak

### 2026-10-07 — Felsefe genişletme

- + Makâsıd (229) · Fârâbî Siyâse (18) · Necât (312) · Şifâ İlâhiyyât (378)
- Toplam: **7** eser · **1306** chunk · RAG **298.478**
- Anlık: maqasid / necat / siyasa farabi / sifa ilahiyyat

### 2026-10-07 — Felsefe (İslâm felsefesi) dolgu

- Yol: `ortak_kaynak/alanlar/felsefe/eserler/`
- OpenITI: Fârâbî Medîne-i Fâzıla · Siyâse · İbn Sînâ İşârât · Necât · Şifâ İlâhiyyât · Gazâlî Tehâfüt · Makâsıd
- Script: `faz10_felsefe_openiti_ingest.py`
- Anlık: `ruzgar_felsefe_kutuphane.py` + desktop early path

### 2026-10-07 — Kayserî tam Arapça şerh

- Kaynak: Âştiyânî nşr. PDF (IA yazma OCR bozuk → kullanılmadı)
- PDF metin + NFKC → `qaysari_sharh_fusus` (**1176** chunk / 59 batch)
- Anlık: «kayseri fusus» → tam AR; «mukaddime kayseri» → EN mukaddime
- RAG: **296.000** chunk · indeks `qaysari_sharh_*` ~2390 parça · «Dawud al-Qaysari Fusus» 8/8 hit

### 2026-10-07 — Kur’ân ayet RAG katmanı

- Zaten vardı: `ayetler.jsonl` (6236 · AR + meal) + anlık `ruzgar_kuran_anlik.py`
- Eksik: RAG yalnız `*.md` indeksler → ayetler indekste yoktu
- Script: `faz1_kuran_ayet_rag_ingest.py` → `01_kuran/incremental/ayetler/kuran_ayet_batch_*.md`
- Ortak kayıt: `kuran_ayetler` · meal=çeviri (fetva/tefsir değil)
- RAG incremental: **293.610** chunk (+~3k)
- Doğrulama: batch 416/6236 · RAG «Fatiha meal» → ayetler hit · anlık Fatiha 1:1 meal OK

### 2026-10-07 — Kâşânî / Kayserî şerh

- Kâşânî: IA `sharh-fusus-kashani` Arapça OCR → `kashani_sharh_fusus` (**633** chunk)
- Kayserî: IA mukaddime İng. çeviri → `qaysari_muqaddima_fusus` (**356** chunk; tam AR şerh yok)
- Anlık: «kashani fusus» / «kayseri fusus» / «qashani fusus»
- Script: `faz9_tasavvuf_serh_download_ingest.py` (3 şerh)
- RAG incremental: **290.573** chunk

### 2026-10-07 — Nebula tarih batch commit

- Commit: `15fac9c` — `docs(nebula): tarih kaynak incremental batch paketlerini ekle`
- 200 dosya · yalnızca `knowledge/nebula/tarih_kaynak/incremental/nebula_batch_*.md`
- Push yok (istenmedi)

### 2026-10-07 — Fusûs şerhi (Câmî)

- Kaynak: IA `sharh_al_jami_ala_fusus_al-hikam` Arapça OCR
- Script: `faz9_tasavvuf_serh_download_ingest.py`
- Anlık: «jami fusus» / «serh fusus»
- RAG incremental: **288.908** chunk

### 2026-10-07 — Fütûh / Feth Arapça

- Fütûh: `futuhul-ghaibb` Arapça OCR + mevcut EN çeviri birleştirildi (250→580 chunk)
- Feth: dosya zaten Arapça OCR imiş; dil etiketi `en`→`ar`
- Smoke tasavvuf 10/10 beklenir

### 2026-10-07 — Kimyâ-yı Saâdet dolgu

- Önce: OpenITI kısa ara1 (~13 chunk)
- Şimdi: IA Farsça ج۱+ج۲ + EN Bilal çeviri → `gazali_kimya_saadet__merged.txt` (4.8 MB)
- Ingest: **2363** chunk · dil `fa` · güven orta · sayfa uydurma yasak
- Smoke tasavvuf 10/10

### 2026-10-07 — Ollama boş liste (düzeltildi)

- Dosyalar zaten vardı: D:\\ÜMİT\\PROGRAMLAR\\Ollama\\models (~11.6 GB)
- Modeller: llama3.1:8b · llama3.2:3b · qwen2.5-coder:7b (blob eksiksiz)
- Sorun: Ollama **0.40** D:\\OllamaModels junction ile boş liste; gerçek Unicode yol ile 3 model görünür
- Ruzgar.ps1 + RuzgarMasaustuBaslat.ps1 + User OLLAMA_MODELS → Unicode yola çevrildi
- ollama list yeniden dolu; yeniden indirme yok

### 2026-10-07 — Doğal sohbet P2

- `chat_core`: `use_web=false` iken `_web_pro` / hava web zorlaması yok
- `desktop_server`: `web_used` = `use_web` + gerçek web metni (`payload_indicates_web_used`)
- `ana_motor_kaynak` + `ruzgar_dogal_sohbet_faz91`: soft citation / trust-noise suppress
- Smoke: `scripts/smoke_dogal_sohbet_p2.py` (10/10) · P0 8/8

### 2026-10-07 — RAG indeks (tamam)

- Embedding bitti; `chunks.jsonl` yazımı kilide takıldı → `.tmp` yerine kondu + manifest güncellendi
- Durum: **cached** · **282.873** chunk · tasavvuf ~32k parça
- Kavram MD’ye Latin anahtar eklendi (anlam süzgeci / TR sorgu uyumu)

### 2026-10-07 — Tasavvuf (`09_ahlak_tasavvuf`) dolum

**Kaynak:** OpenITI (Gazâlî İhyâ/Kimyâ, İbnü'l-Arabî Fütûhât/Fusûs, Geylânî Gunye) + Internet Archive (Fütûhu'l-Gayb, Feth-i Rabbânî, Mesnevî, Divân, Mektûbât — çoğunlukla EN çeviri OCR)

- **10 eser** · ~**16.892** chunk · smoke `smoke_tasavvuf.py`
- Anlık: `ruzgar_tasavvuf_kutuphane.py` (siyer sonrası early path)
- Script: `faz9_tasavvuf_download.py` + `faz9_tasavvuf_ingest.py`
- Ortak kayıt: `KAYNAK_KAYIT.json` → `durum: hazir`
- **Politika:** Fetva yok · sayfa/cilt uydurma yasak

**Dene:** «tasavvuf nedir» · «ihya nedir» · «mesnevi nedir» · «kalbin hastaliklari nelerdir»

### 2026-10-07 — Ortak kütüphane / kaynak altyapısı

- `knowledge/ortak_kaynak/` — SEMA + ALANLAR (9 alan) + KAYNAK_KAYIT + web_cache yer tutucu
- Modül: `ruzgar_ortak_kaynak.py` · köprü: `ana_motor_kaynak.py` (güvenli atıf, uydurma yasak)
- Smoke: `python scripts/smoke_ortak_kaynak.py` · Kapat: `RUZGAR_ORTAK_KAYNAK=0`

### 2026-10-06 — Ollama + anlat/dost (push `aae43ae`)

- Yerel modeller zaten `D:\ÜMİT\PROGRAMLAR\Ollama\models` (~10.8 GB: `llama3.1:8b`, `llama3.2:3b`, `qwen2.5-coder:7b`)
- Ollama Unicode `ÜMİT` yolunu saymıyordu → `D:\OllamaModels` junction + `OLLAMA_MODELS` (`Ruzgar.ps1` / `RuzgarMasaustuBaslat.ps1`)
- «hicreti daha açık anlat» dost şeridine kaçmasın: `ruzgar_tek_beyin` + `ruzgar_dogal_sohbet_faz91` (sohbet daveti hariç)
- Canlı: `instant_gundelik=False`, beyin `denge/llama3.1:8b`, `RUZGAR_OLLAMA_ONLY=1`

### 2026-10-06 — Doğal sohbet P0+P1

- P0: video panel tuzağı kapandı; lookup anlık / anlat→LLM ayrımı
- P1: kütüphane ipucu LLM’e enjekte; session echo ilim/sohbeti ezmez; devam cümleleri genişledi
- LLM yokken «anlat» için yumuşak kütüphane özeti (`soft_library_synth_fallback`)
- Smoke: `smoke_dogal_sohbet_p0.py` · Kapat: `RUZGAR_ANLIK_NIYET_GATE=0`

### 2026-10-06 — Siyer (`08_siyer`)

**Kaynak:** OpenITI (İbn Hişâm, Vâkıdî, İbn Sa'd, Taberî, İbn Kesîr)

- **9 eser** · ~**33.913** chunk · smoke `smoke_siyer.py` **8/8**
- Asıl: İbn Hişâm Sîre · Megâzî: Vâkıdî · Tabakât: İbn Sa'd · Tarih: Taberî · Muteber: Fusûl + Bidâye (İbn Kesîr) · Tercüme: Zehebî Siyer · Erken: Ridde, Fütûhu'ş-Şâm
- Anlık: `ruzgar_siyer_kutuphane.py` (hadis sonrası early path)
- **Politika:** Fetva yok

**Dene:** «siyer nedir» · «hicret nedir» · «bedir nedir» · «ibn hisham nedir»

**Sonraki kütüphane:** `09_ahlak_tasavvuf`

### 2026-10-06 — Usûl-i fıkıh (`07_usul_fikh`)

**Kaynak:** OpenITI (Cüveynî, Gazzâlî, Pezdevî, Serahsî, Âmidî, Beyzâvî, Zerkeşî)

- **10 eser** · ~**7.102** chunk · smoke `smoke_usul_fikh.py` **8/8**
- Matın: Varakât, Minhâcü'l-vusûl · Muteber: Burhân, Mustasfâ, Menhûl, Pezdevî, Serahsî, İhkâm, Bahru'l-muhît · Kavâid: Mensûr
- Anlık: `ruzgar_usul_fikh_kutuphane.py` (fıkıh sonrası early path)
- **Politika:** Fetva yok

**Dene:** «usul fıkıh nedir» · «kıyas nedir» · «varakat nedir» · «mustasfa nedir»

### 2026-10-06 — Fıkıh (`06_fikh`) 4 mezhep + ilmihal matınları · push `1d3f406` (+ RAG fix `10d3291`)

**Kaynak:** arabic-digital-humanities/fiqh (OpenITI / Şâmile kökenli Arapça)

| Mezhep | Matın / ilmihal | Muteber |
|--------|-----------------|---------|
| Hanefî | Kudûrî, İhtiyâr, Lübâb | Bedâi', Reddü'l-muhtâr |
| Mâlikî | Kâfî, Düsûkî | Muvatta', Zehîra, Tâc |
| Şâfiî | Minhâc, Kifâyetü'l-ahyâr | Ümm, Tuhfe, Nihâye |
| Hanbelî | Hırakî, Ravzü'l-murbi' | Muğnî, Müntehâ |

- **19 eser** · ~**49.514** metin parçası · smoke `smoke_fikh.py` **8/8**
- Anlık: `ruzgar_fikh_kutuphane.py` (hadis sonrası early path)
- TR: kavramlar + ilmihal rehberi + mezhep tarihçesi
- Script: `faz6_fikh_download.py` + `faz6_fikh_ingest.py`
- **Politika:** Fetva yok

**Dene:** «fıkıh nedir» · «hanefi mezhebi» · «ilmihal nedir» · «minhac nedir» · «kuduri nedir»

**Dönünce sırada:** alan süzgeci · akaid Luma OCR · veya usûl-i fıkıh genişletme

### 2026-10-06 — Hadis tamam (matın + usûl + tarihçe) · push OK

**Commit:** `bf2b1f4` → `origin/main`  
**Canlı:** `.\Ruzgar.ps1 -ForceRestart` (RAG chunks yerelde; `python -m ilim_assistant.ingest_cli --incremental`)

**Kutüb-i Sitte:** 6 raf · **34.153** hadis  
**Usûl:** İbnü's-Salâh (437 paket) · Nuhbe · Beykûniyye  
**TR:** tedvin tarihçesi · muhaddisler · 28 kavram · smoke **10/10**  
**RAG:** ~72.302 parça (chunks.jsonl gitignore — GitHub 100MB)

### 2026-10-06 — Hadis (`05_hadis`) Kutüb-i Sitte

**Bitti:**
- Kaynak: `fawazahmed0/hadith-api@1` Arapça matın (6 eser ayrı raf)
- Toplam **34.153** hadis · `kutub_i_sitte/{buhari,muslim,ebu_davud,tirmizi,nesai,ibn_mace}/`
- Anlık: `ruzgar_hadis_kutuphane.py` + early path (akaid sonrası)
- Kavramlar + usûl/tarihçe · smoke `scripts/smoke_hadis.py` **10/10**
- İncegest: `faz5_hadis_kutub_sitte_ingest.py` + `faz5b_hadis_usul_tarih_ingest.py`
- RAG: ~72.302 parça

**Usûl RAG güncelleme:** ibn_salah/nukhba/bayquniyya + TR

**Dene:** «hadis nedir» · «kutub-i sitte nedir» · «buhari 1» · «muslim 1» · «tirmizi 1»

**Akaid:** çekirdek tamam; ara verildi (Luma OCR / bekleyen_tr sonra).

### 2026-10-06 — Neredeyiz (önceki çıkış)

**Bitti (çekirdek):**
1. **Akaid** `04_akaid` — Arapça corpus + 18 TR kavram + anlık yol + RAG · smoke 8/8
2. **Sohbet karıştırma kökleri** — fuzzy özne, kimlik anlık, geçmiş `sordum`, Kur’an meta/aşır, sure adı sınırı
3. **Sistematik anlam kilidi** `ruzgar_anlam_koruma.py` — fuzzy + oturum yankısı
4. **RAG/LLM koruma:** chunk içerik süzgeci · `RAG_SCORE_MIN` varsayılan **0.32** · cevap `guard_assistant_reply` · otomatik öğrenme zehir kilidi · `smoke_anlam_koruma` 8/8

**Canlı:** `.\Ruzgar.ps1 -ForceRestart`

### Sonraki adım planı
1. Alan süzgeci (akaid/tefsir/hadis raftı)
2. Smoke setini CI’ya bağla (`smoke_hadis` + akaid + anlam)
3. el-Luma‘ OCR (akaid)
4. İsteğe bağlı: Muvatta / Müsned Ahmed (Sitte dışı)

### 2026-10-06 — Sohbet yanlış cevap kökleri (düzeltildi)

**Bulunan hatalar (Mimar sohbet kaydı):**
- «senin adın ne» → anne adı (fuzzy özne kayması)
- «…adını sordum» → geçmiş soru listesi (çıplak `sordum` cue)
- «tefsir nedir» / «aşır nedir» → yanlış yol veya kavram eksik
- «bakara … kaçıncı/kaç ayet/nüzul» → 1. ayet (örnek ayet genişletmesi)
- «cin … türkçe» → Tûr sûresi (`tur` ∈ `türkçe`)

**Düzeltme:** fuzzy özne filtresi · asistan kimlik anlık yol · geçmiş sohbet cue sıkılaştırma · Kur'an meta/aşır · `detect_sure_no` kelime sınırı

### 2026-10-06 — Akaid (`04_akaid`) tamam (çekirdek)

**Bugün bitti:**
- Staging PDF: Mâtürîdî Tevhîd (Huleyf + Topaloğlu–Aruçi), Eş‘arî Luma‘, Makâlât → `arsiv/_ilim_staging/04_akaid/`
- Archive OCR metin → knowledge paketleri: Tevhîd ~788 + Makâlât ~654 batch (`scripts/faz4_akaid_ingest.py`)
- TR kavramlar: `kavramlar_akaid.jsonl` (18 madde) — fetva değil, kaynaklı özet
- Anlık yol: `ruzgar_akaid_kutuphane.py` + `desktop_server` early path (Kur’an/Arapça sonrası, iki blok)
- Smoke: `python scripts/smoke_akaid.py` → **8/8**
- `ingest_cli` `_KNOWLEDGE_ROOT` uyumluluk düzeltmesi (`rag_store`)
- RAG incremental ingest OK — indeks **42.502** parça (akaid md indekste)

**Canlı için:** `.\Ruzgar.ps1 -ForceRestart` → dene: «akaid nedir» · «maturidi kimdir» · «tevhid nedir» · «senin adın ne» · «aşır nedir»

**Luma notu:** PDF tarama-only; konu iskeleti MD var. Tam OCR sonra (Tesseract yoktu).

**TR çeviriler:** Telifli modern baskılar Mimar’ın `bekleyen_tr/` klasörüne yasal dosya koymasıyla eklenir.

**Sırada:**
1. Luma OCR (Tesseract/ara kurulum) veya senin TR PDF’lerin
2. Daha dolu AR–TR sözlük
3. Nebula untracked batch kararı
4. Git push (yerel ahead)

### 2026-10-05 — İlim din kütüphanesi (Kur’an/tefsir/Arapça)

**Bitti:** Gizlilik gitignore · Kur’an+tefsir · Arapça lügat · early path düzeltmeleri · smoke 9/9  
**Akaid:** 6 Ekim’de tamamlandı (yukarı).

### 2026-10-03 — Bilgi sohbeti kilidi (prepare_turn hang)

**Kök neden:** `analyze_turn` ↔ `should_use_personal_hafiza_first` ↔ `should_stay_on_ana_motor_bilgi` ↔ `looks_like_encyclopedic_fact_question` ↔ `personal_hafiza_blocks_bilgi_path` sonsuz döngü.

**Düzeltme:**
- `ruzgar_tek_beyin.py` — `_idrak_reentry` + reentry’de hafif kişisel kontrol
- `ana_motor_idrak_zihin.py` — reentry bayrağı (v2)
- `ana_motor_plan.py` — ansiklopedik sınıflandırmadan kişisel-hafıza çağrısı kaldırıldı
- `chat_core.py` / `weather_live.py` — «Su kaç derecede kaynar?» hava yanlış sınıflaması düzeltildi

**Ollama:** User `OLLAMA_MODELS` = `D:\ÜMİT\PROGRAMLAR\Ollama\models` (3 model). Tray/serve bazen env görmeden boş liste veriyor → Ollama’yı env ile yeniden başlat. ASCII junction: `D:\UMIT_PROGRAMLAR_Ollama_models`.

**Doğrulama (hedef):** selam anında · fotosentez/uydu bilgi yolu kilit değil · kaynar ≠ hava.

**Devam (kalite):** `Ruzgar.ps1` OLLAMA_MODELS garantisi · arka plan `preload_primary_chat_model` · Ollama-only talimat sızıntısı yasağı · aritmetik anında (`2+2=4`) · Ay mikro gerçek · scrub güçlendirildi.

**Canlı (2026-10-03):** selam/2+2/Ay anında · kaynar/fotosentez ~3–5 sn · Ollama preload OK · push bekliyor (ahead).

### 2026-10-03 — Yeni PC taşıma + Ollama-only sohbet (ara verildi)

**Donanım:** Ryzen 5 5500 · 16 GB RAM · RTX 4060 8 GB · Ollama 0.35

**D: kurulumlar (`D:\ÜMİT\PROGRAMLAR\`):**
- Ollama modelleri → `Ollama\models` (`OLLAMA_MODELS`)
- Python 3.12 + venv → `venvs\ruzgar` (`RUZGAR_PYTHON`)
- Node LTS → `Nodejs` · cache’ler → `Caches\`
- Git → `Git\cmd`

**Modeller:** `llama3.2:3b` (hizli) · `llama3.1:8b` (denge) · `qwen2.5-coder:7b` (kod)

**`.env` (git’te yok):** `RUZGAR_OLLAMA_ONLY=1` · Gemini/Groq kapalı · RAG warmup açık · `RUZGAR_EMBED_DEVICE=cpu` · `ENABLE_WEB_SEARCH=1` + `RUZGAR_WEB_ARASTIRMA_PRO=1` + `RUZGAR_WEB_SECONDARY_ONLY_ON_EMPTY=1` (yerel-önce; yoksa/zayıfsa veya canlı kur-haber → web) · `fx_live` (DDG/doviz.com anlık kur)

**Kod (bu oturum):**
- `Ruzgar.ps1` — D: venv önceliği · lite health’te `ollama_only` döngü düzeltmesi · `py` yerine `PyExe`
- `RuzgarMasaustuBaslat.ps1` + `scripts/Masaustune_Kisayol.ps1` — masaüstü kısayol / D: yolları
- `llm_ollama.py` — `num_ctx` + `keep_alive`
- `prompts.py` — Ollama-only sohbet üslubu
- `rag_store.py` — gömme cihazı CPU (VRAM çakışması)
- `chat_core.py` — aritmetik soruda fuzzy hafıza atlama

**Doğrulama:** Selam / anlık yollar OK · bilgi sorularında `prepare_turn` hâlâ takılabiliyor (sonraki oturum hedefi).

**Masaüstü kısayol:** `C:\Users\hayma\Desktop\RUZGAR.lnk`

**Sırada (dönünce):**
1. Bilgi sohbeti kilidi — `prepare_turn` / plan / retrieval hang’ini çöz
2. Sohbet kalitesini ölç (bellek + dolu cevap)
3. İsteğe bağlı: kontrollü bulut geri açma (kota korumalı)
4. 6b–6c (programlama / tek yüz) — önceki plandan

### 2026-06-18 — Sıra 6a: bilgi turu (devam: 6b…)

**Git:** Sıra 5 push edildi (`2c66853` · `origin/main`). Sıra 6a yerelde — commit bekliyor.

**6a tamamlandı:**
- `ana_motor_bilgi_turu.py` — merkezi bilgi turu politikası (hafıza → RAG → web → LLM)
- Yerel-RAG-önce: ansiklopedik/bilgi sorularında bulut hızlı yol RAG prefetch'i atlamaz
- Zayıf RAG → web açık kalır (güçlü eşleşmede kapatılabilir)
- `MAIN_ONLY_GENEL_HAFIZA` kapalı = tam güç (health + smoke doğrulama)
- Health `/api/health` → `ana_motor.bilgi_turu` durum kartı

**Sırada:** 6b (programlama çok dosya / E2), 6c (tek yüz pilot), 6d (offline gate), 6e (isteğe bağlı temizlik).

### 2026-06-17 — Programlama motoru oturumu (kapandı)

**Git (push edildi, `origin/main`):**

| Commit | Özet |
|--------|------|
| `2d0dd7c` | Faz85 scope yönlendirme (kullanıcı niyeti > oturum kapsamı) |
| `5b91c00` | Ajan scope sabitleme + boş yazım koruması |
| `7f7f151` | Upgrade raporu S10 11/11 |
| `72a89b3` | Geçersiz Python/JSON syntax yazım koruması + `version 2.0.0` parse |
| `2ef5634` | E1 KPI, UI overlay, terminal yolu, ana motor köprüsü (sıra 1–4) |
| `cb62964` | Faz85 erken kapı + scope önceliği (`iter_fast_path_early` bağlı) |

**Faz85 durumu:** Çekirdek hızlı yol `cb62964` · anında bayraklar/UI `2ef5634` — **push edildi**, geride dosya yok.

**Offline gate (son koşu):** `programlama_upgrade_runner.py --strict` → **11/11** · parity full **8/8**.

**Canlı doğrulama (UI):** `görev: smoke-live-test health endpointine version 2.0.0 ekle pytest geçir` → **Faz 85 hızlı yol OK** (~2.3 sn, LLM yok, yeşil). `projects/smoke-live-test/app/main.py` → `version: "2.0.0"` · pytest **2/2**.

**Yerel commit edilmemiş:** sıra 6a (bilgi turu).

**Hızlı başlatma:** `.\Ruzgar.ps1 -ForceRestart` · port **8779** · build `2026-06-15-ruzgar-programlama-pro-v4`.

## Kuzey yıldızı — asıl amaç

**Rüzgar’ı dijital kayıt cihazı veya dar bir araç değil; bağlam kuran, tam teşekküllü bir asistan yapmak istiyoruz.** Hedef, ChatGPT veya Gemini’ye benzeyen çizgide: geniş bilgi ve akıl yürütme, sorulara anlamlı yanıt, problemleri çözmeye çalışma, gerektiğinde program üretip projeyi çalışır hale getirebilme — yani **her şeyi bilen tek bir devasa liste değil**, katmanlı hafıza + bilgi + dil modeli ve motorlarla **gerçek bir yapay zekâ yardımcısı** oluşturmak. Atölyeler (video, programlama, tercüme vb.) bu vizyonun **parçaları**; amaç bunların üzerinde birleşen **tek yüz ve güçlü akıl**.

## Mimar protokolü (Cursor + Rüzgar)

- **Döngü:** Planla → Uygula → Doğrula → Revize.
- **Kalıcı kurallar:** kök `.cursorrules` + bu dosya.
- **Rüzgar sohbet talimatı:** `ilim_assistant/prompts.py` — hatırla vs kitap ingest ayrımı.

## Nebula politikası (2026-05-20 — Mimar ile net)

| Kanal | Ne zaman | Nereye | Biçim |
|--------|----------|--------|--------|
| **Sohbet «hatırla»** | Siz açıkça söylediğinizde | `ruzgar_genel_hafiza.json` | Kısa kişisel not; her tur otomatik yazılmaz |
| **Kitap / ansiklopedi** | «Şu dosyayı oku, hafızana kaydet» komutu | `knowledge/nebula/<koleksiyon>/incremental/` | Konu/başlık paketleri (`##` + `nebula_batch_*.md`) + RAG |
| **TDK / Tarih (mevcut)** | Protokol veya ingest | `knowledge/tdk/`, `knowledge/TARIH_VE_KULTUR/` | Aynı kademeli paket mantığı |

Modül: `ilim_assistant.nebula_kitap_hafiza` — `desktop_server` sohbetinde kitap komutu önce işlenir.

**Ne zaman diskte ne var (2026-05-20):**
- **TDK + büyük tarih:** 11 Mayıs ingest tamam (`tdk` 185 paket, `TARIH_VE_KULTUR` 25 paket, ~10k+ RAG parça) — Rüzgar sohbetten otomatik okumadı; protokol ile alındı.
- **Nebula demo:** Geliştirme testinde yalnızca küçük `tarih_kaynak.json` (318 kayıt) → `knowledge/nebula/tarih_kaynak/`. Siz sohbetten henüz büyük kitap komutu vermediyseniz nebula’da sadece bu demo olabilir.
- **Faz 2:** `RUZGAR_FAST_LOCAL_RAG_FIRST=1` (varsayılan) — bilgi sorularında fast path RAG’i atlamaz; prefetch + tarih + nebula birleşik arama.

### Sunucu yeniden başlatma (zorunlu kontrol)

1. `Ruzgar_TemizBaslat.bat` veya `.\Ruzgar.ps1 -ForceRestart` (yönetici gerekebilir — eski PID).
2. `ruzgar-desktop/ruzgar_remote_api.txt` → `http://127.0.0.1:8779` (8777 eski).
3. Dashboard şeridi: `build 2026-06-14-ruzgar-idrak-zihin-faz-an` · **Faz AN İdrak Zihin**.
4. Smoke: `cd ilim-assistant` → `python scripts/ana_motor_smoke.py` (0 hata hedefi).
4. `tarih_kaynak_buyuk.json` komutu → **anında**: «zaten tarih hafızasında 12190 kayıt» (tekrar yükleme gerekmez). Zorla nebula kopyası: mesaja `zorla nebula` ekle (arka planda, 2–8 dk; «nebula durum» ile izle).
5. Kitap komutu «Hatırladım» **değil**; büyük dosyada zaman aşımı olmamalı (`nebula-v2-async`).

**Not:** `tarih_kaynak_buyuk.json` zaten `TARIH_VE_KULTUR` (25 paket) + RAG’te; nebula komutu isteğe bağlı ikinci kopya.

## Ana motor, hafıza önbelleği ve teknik akış (özet)

- **Genel hafıza (`ruzgar_genel_hafiza.json`):** `HafizaIRuzgar` dosyayı RAM’e alır; fuzzy + token kapsaması ile eşleşme arar. `chat_core.prepare_turn` içinde **ilk bakılan yer** burasıdır; cevap bulunursa çoğu zaman tur burada biter (RAG/web/LLM’e çıkmadan).
- **RAG / İlim hazinesi (`rag_store`, `knowledge/`):** Yerel bilgi parçaları + gömme önbelleği; `main_engine` ile arşiv önceliği ve güçlü eşleşmede doğrudan pasaj yolu mümkün.
- **Kritik anahtar — `RUZGAR_MAIN_ONLY_GENEL_HAFIZA`:** Dar mod yalnızca ortamda **açıkça** `1`, `true`, `yes` veya `on` ile açılır. **Boş string veya tanınmayan değer tam güç sayılır** (önceden boş değer yanlışlıkla dar moda düşürebiliyordu). Dar mod açıkken `genel` modda JSON eşleşmezse yalnızca “öğrenmedim”; RAG/web/LLM kapalı.
- **Genel hafıza (`chat_core.try_genel_hafiza_reply`):** «Henüz öğrenmedim» yer tutucusu anında cevap sayılmaz; `ENABLE_RUZGAR_GENEL_HAFIZA=0` (veya `ENABLE_OGRENME_MERKEZI=0`) ile JSON kısayolu tamamen kapatılabilir.
- **Genel hafıza (`hafiza_i_ruzgar.HafizaIRuzgar`):** Birebir, normalize ve **fuzzy** aramada cevabı yer tutucu (“henüz öğrenmedim…” kalıbı) olan satırlar **aday olmaz**; böylece bir soruya yanlış satır üzerinden «öğrenmedim» zorlanmaz, sıra RAG/LLM’e kalır.
- **Tam boru hattı:** Kısıt kapalıyken sıra tipik olarak: genel hafıza → (yoksa) RAG parçaları + isteğe bağlı web/bağlantı + Ollama ile üretim.

## İlk ne yapılmalı — yardımcı motorları ana motora ne zaman bağlarız?

**Tam güç ana motor:** Varsayılan kod yolu `RUZGAR_MAIN_ONLY_GENEL_HAFIZA` olmadan **RAG + web + LLM**’e izin verir. Önce **Ollama**’nın ayakta olduğunu ve bir soruda gerçekten model yanıtı geldiğini doğrula.

**Yardımcı motorların ana motora bağlanması — zamanlama:**

1. **Önce** ana sohbet boru hattı net ve güvenilir olsun (yukarıdaki kilit + model + bağlam limitleri). Atölyeler zaten ayrı sekmede güçlü; “tek yüz” birleştirmesi bunun üstüne inşa edilir.
2. **Sonra** sırayla veya önceliğe göre **niyet / tetikleyici** katmanı: kullanıcı cümlesi hangi moda (video, programlama, tercüme…) ait, `normalize_mode` veya hafif bir yönlendirici ile seçilir; ilgili `/api/...` veya mevcut masaüstü işlevleri çağrılır. İlk bağlama adayı genelde **Programlama** veya **Tercüme** (metin tabanlı, API hazır) olur; **Video** dosya yolu ve FFmpeg gerektirdiği için bir adım sonra.
3. **`.cursorrules`** ile uyum: Sunucuda motor başlatma sırası zaten kilitli; ana motordan “motor çağrısı” **bu sırayı bozmadan** sadece **iş akışı** olarak eklenir (import sırasını değiştirmeden).

Özet: **Yardımcı motorları ana motora bağlamak**, ana boru hattı tam açıldıktan ve bir iki pilot senaryo (ör. “şu metni çevir”, “şu kodu çalıştır”) netleştikten **hemen sonraki mühendislik turu** olarak planlanır; takvim olarak “önce ana güç, sonra orkestrasyon”.

## Bu oturumda netleşenler

- **Sunucu yeniden başlatma:** Rüzgar/Electron penceresini kapatmak **Python sunucusunu** (`ilim-assistant` içinde `desktop_server.py`) yenilemez. Kod veya ortam değişince eski işlemi durdurup sunucuyu yeniden başlat; tam yeniden başlatmada **Ollama + `desktop_server`** oturumunun da temiz kalktığından emin ol.
- **Sohbet belleği:** Bilgisayar/kapanış sonrası model bağlamı sıfırlanır; tam çözüm **bu dosya + anlamlı commit mesajları**.
- **Plan özeti (önceki oturumlardan):** Katmanlı akıl (hafıza + RAG + LLM); beş ara motor (Ses, Video, Okuma, Tercüme, Programlama) güçlenir, sonra Ana Motor’da orkestrasyon; `.cursorrules` motor sırasına uy.
- **Programlama Atölyesi:** Build rev `2026-06-15-ruzgar-programlama-pro-v4`. Offline gate **11/11 + 8/8 parity**. **Faz 85** hızlı yol (health+version+pytest, LLM yok); **yazım koruması** (boş/syntax/patch tek kapı). UI’da Faz85 kartı + tam ajan uyarısı. Basit görev örneği: `görev: smoke-live-test health endpointine version 2.0.0 ekle pytest geçir`. Tam ajan yalnızca karmaşık işlerde; `RUZGAR_FAZ85=0` ile zorlanır.
- **Video Atölyesi:** **v1–v4** tarafında temel işlevler kodlandı (kesim, dönüştürme, birleştirme, altyazı gömme, ses bağlama, zaman çizelgesi, altyazıyı Tercüme’ye gönderme). FFmpeg ortamı doğrulanmıştı.
- **Arayüz:** Kullanıcıya dönük metinler Türkçeleştirildi; çok dillilik sonra bağlanacak.
- **Doğrulama:** `ruzgar-desktop` içinde `npm run test:phase11` — kod kartı fenced ayrıştırma senkron kontrolü.

### 2026-05-11 / 12 — Rüzgar «zihin ayarı» ve Git

- **TDK ↔ Tarih çakışması:** `chat_core` içinde tarih niyeti varken genel RAG havuzundan **TDK kaynaklı** pasajlar birleşik bağlama alınmıyor. `rag_store._source_is_tarih_hafiza` yolu düzeltildi (`tarih_ve_kultur` + eski yazım uyumu). `source_is_tdk` / `source_is_tarih_hafiza` dışa açıldı.
- **Kelime / TDK sorgusu:** Kısa veya sözlük kalıbında (`nedir`, `anlamı`, ≤3 kelime ve kısa mesaj vb.) **`search_tdk_exact_lemma`** — yalnızca chunk içindeki **`##` başlıkları** ile tam eşleşme (900 karakterlik dilimler yüzünden tüm başlıklar taranıyor). Eşleşme yoksa vektörle yakın maddeye **zıplanmıyor** (Hayalet/Haya tipi karışma riski azaltıldı). Kapatmak: `RUZGAR_TDK_EXACT_LEMMA=0`.
- **Bilge üslubu:** `prompts.pick_system` → `ASSISTANT_SYSTEM + _bilge_voice_suffix()` (tok, samimi, bilge anlatım). Kapatmak: `RUZGAR_BILGE_VOICE=0`.
- **İndeks:** `python -m ilim_assistant.ingest_cli --incremental` çalıştırıldı. Kök ve `ilim-assistant/.gitignore` içinden **`ilim-assistant/.rag_index/`** çıkarıldı; indeks dosyaları repoda tutuluyor (yaklaşık 10k+ chunk; `embeddings.npy` + `chunks.jsonl` + manifest).
- **Mühür satırı:** `desktop_server` startup ve `gradio_chat` `__main__` sonunda konsola: *Rüzgar Kullanıma Hazır, Sistemi Yeniden Başlatabilirsiniz.* Kapatmak: `RUZGAR_PRINT_READY_SEAL=0`.
- **Tarih bilgi seti (repo):** `knowledge/TARIH_VE_KULTUR/` (incremental md + JSON), `tarih_incremental_protocol.py`, `tarih_kaynak_fetch.py`, `ingest_cli.py` güncellemeleri commit’lendi.
- **Push:** `origin/main` güncel (ör. `fdccbdb` ve önceki Rüzgar/indeks commit’i aynı push dalında).

**Yarın kaldığımız yer:** Kod ve indeks GitHub’da; yerelde çalıştırmadan önce `git pull` yeterli. Bilgi ekledikten sonra indeks tazelemek için yine `ilim-assistant` klasöründe `python -m ilim_assistant.ingest_cli --incremental` (kilit mesajı çıkarsa `--allow-other-knowledge`). İstersen bir sonraki turda: TDK tam yolunun tetikleyicilerini genişletme/daraltma, `bilge_modu` ile `bilge_heartbeat` entegrasyonu, veya aşağıdaki «Sıradaki adım» maddelerinden biri.

## Sıradaki adım (devam)

**Öncelik — programlama:** Faz85’i LLM’den önce çalıştır (`iter_fast_path_early` bağla) · E1 %70+ · isteğe bağlı karmaşık görevlerde Yol C (tam ajan optimizasyonu).

Diğer seçenekler: çeviri `.srt` / yumuşak altyazı · çeviri anahtarları · Ana Motor tek sohbet orkestrasyonu.

## Referans

Geçmiş Cursor oturum özetleri (yerel): `agent-transcripts` altında; örn. programlama / plan tartışması ile ilişkili kayıtlar `2ef431a9-a39f-4e81-90ce-896ec19d93f9`, plan özeti `b8ad8767-ad71-4e4d-8cf0-09b001298000`.

---

## Bekleyen UI — Yardım (? ) motor rehberi (2026-06-03, ertelendi)

Üst **?** penceresine motor başına madde madde rehber — **motorlar sağlam çalıştıktan sonra** (önce güçlendirme/test, sonra yazım).  
**Plan:** `ruzgar-desktop/docs/RUZGAR_YARDIM_MOTOR_PLANI.md`

---

**Not:** Yeni oturumda önce bu dosyayı okuyarak devam et; özellikle **Kuzey yıldızı** bölümü proje kararları için bağlayıcı vizyondur.
