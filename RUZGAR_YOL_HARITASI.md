# RÜZGAR — Yol haritası (KİLİTLİ)

**Kilit:** 2026-10-23 · Mimar onayı («bu planı sevdim, kilitle»)  
**Kaynak güvenli bölge:** 2026-10-22 · `0c919d60` · `origin/main`  
**Süre beklentisi:** birkaç gün (faz faz; atlama yok)  
**Aktif faz:** **S5** (S3✅ 2026-10-23 · S4 bekler Mimar `evet`)

Bu dosya çok günlük çalışmada **tek sıra kaynağıdır**. Sapma yasak. Güncelleme: dilim yeşil → burada işaretle + `PROJE_DURUMU.md` özet.

---

## Çalışma kuralı (her dilim)

1. Ölçüm (baseline / smoke)  
2. Yama (derin; yüzeysel cila yok)  
3. Smoke  
4. Canlı doğrulama  
5. Bu dosyada ✅ + gerekirse güvenli bölge notu  
6. **Sonraki dilime geç** — önceki yeşil olmadan atlama yok  

Faz bitmeden sonraki faza geçilmez. Commit/push yalnız Mimar emriyle.

---

## Sıra (bağlayıcı)

```
P  Programlama tavanı + 2 pilot ürün
↓
S  Sohbet muhakeme (anla → kaynak → harman → doğru konuş)
↓
V  Ses (STT güvenilir + TTS düşük gecikme)
↓
M  Diğer motorlar (Video → Tercüme → Okuma → Mimar)
```

**Yapılmaz (ayrı açık `evet` şart):** boot sırası değiştirmek · serbest kod exec · dosya silme · 32B/70B · telefon · Ümit cevap emrinde web sırasını niyet-koşulsuz bozmak (S4 diliminde ayrı onay).

**Tavan gerçeği (bu PC):** programlama ~%75–85 supervised; %90+/Cursor bu planda yok.

---

## Faz P — Programlama

| Dilim | İş | Çıkış | Durum |
|-------|-----|--------|--------|
| **P0** | Baseline: BOOT=0 / BOOT=1 KPI, görev pili | Sayısal başlangıç | ✅ 2026-10-23 · `docs/P0_BASELINE_2026-10-23.md` |
| **P1** | Supervised pattern kütüphanesi (VERSION/health ötesi sık niyetler) | Dar görev boot ↑ | ✅ 2026-10-23 · 5 pattern · smoke 9/9 |
| **P2** | Niyet → ray sınıflayıcı (scaffold / ajan+boot / mega) | Yanlış ray ↓ | ✅ 2026-10-23 · smoke 26/26 |
| **P3** | Dosya-dosya verify + heal→kök öğrenme | heal_r10 düşük; verify∧ok | ✅ 2026-10-23 · smoke 12/12 |
| **P4** | BOOT=0 yazım iyileştirme (dürüst KPI; şişirme yok) | boot0 agent_ok ↑ | ✅ 2026-10-23 · patch v1.4 · smoke 10/10 |
| **P5** | Scaffold ürün borusu (statik / react_vite / FastAPI) | Güvenli greenfield ray | ✅ 2026-10-23 · smoke 15/15 |
| **P6** | Pilot A: küçük CLI/araç uçtan uca | Çalışır + pytest | ✅ 2026-10-23 · `projects/pilot-a-selam-cli` · 4 pytest |
| **P7** | Pilot B: basit web sitesi uçtan uca | Açılır + smoke | ✅ 2026-10-23 · `projects/pilot-b-vitrin` · 11/11 |
| **P8** | Faz P mühür (KPI + 2 pilot) | P kapanır → S | ✅ 2026-10-23 · seal YEŞİL · `docs/P8_FAZ_P_MUHUR_2026-10-23.md` |

Kapılar açık: şablon · `@@patch` · `run_argv` verify · dar shell onay.  
Kapılar kapalı: serbest exec · silme · serbest dış yazma.

---

## Faz S — Sohbet muhakeme

| Dilim | İş | Çıkış | Durum |
|-------|-----|--------|--------|
| **S0** | Yalan/uydurma korpusu (20–30 örnek) | Ölçüm seti | ✅ 2026-10-23 · 28 case · smoke 8/8 |
| **S1** | Tek niyet kapısı (SourceRouter) | ≤1 sn struct karar | ✅ 2026-10-23 · 28/28 korpus · smoke 8/8 · `sohbet_source_router.py` |
| **S2** | Faz49 kısıt (sayı/güncelde kaynaksız LLM yok) | Fast-fact güvenli | ✅ 2026-10-23 · smoke 8/8 · `blocks_faz49_fast` |
| **S3** | Sayı/güncel hard-gate + geniş scrub | Kaynaksız rakam yok | ✅ 2026-10-23 · smoke 12/12 · `sohbet_sayi_hard_gate.py` |
| **S4** | Ümit emri web sırası niyet-koşullu | **Ayrı Mimar `evet`** | ⬜ |
| **S5** | Fuzzy + doğal sentez sıkı (bilir-gibi yalan ↓) | Yanlış kart özgüvensiz | ⬜ |
| **S6** | Anlık kart vs grounded anlat + harman | Çelişkide dürüst miss | ⬜ |
| **S7** | Canlı batarya + Faz S mühür | S kapanır → V | ⬜ |

Not: C/H yeşilleri semptom yaması sayılır; S borusu onları geçersiz kılmaz, aşar.

---

## Faz V — Ses

| Dilim | İş | Çıkış | Durum |
|-------|-----|--------|--------|
| **V0** | STT/TTS gecikme baseline (ms) | Ölçüm | ⬜ |
| **V1** | Isınma: Whisper `get_model` + TTS pool prime (boot 1–3’ü geciktirmeden, port sonrası) | Soğuk ilk tur yok | ⬜ |
| **V2** | STT doğruluk/hız (model, VAD, cihaz, ffmpeg yolu) | Duyuyor | ⬜ |
| **V3** | TTS ilk-byte (küçük chunk, workers, rate) | Gecikme ↓ | ⬜ |
| **V4** | Barge-in / mic↔TTS kilidi | Konuşunca kes + dinle | ⬜ |
| **V5** | Sesli tur uçtan uca + mühür | V kapanır → M | ⬜ |

---

## Faz M — Diğer motorlar

Sıra bağlayıcı: **M1 Video → M2 Tercüme → M3 Okuma → M4 Mimar**.  
Her motor: ölçüm → derin iş → uygulama denemesi → mühür. Önceki motor mühürsüz atlanmaz.

| Dilim | Motor | Durum |
|-------|--------|--------|
| **M1** | Video | ⬜ |
| **M2** | Tercüme | ⬜ |
| **M3** | Okuma | ⬜ |
| **M4** | Mimar | ⬜ |

---

## İlerleme özeti

| Faz | Durum |
|-----|--------|
| P | ✅ mühürlü (P0–P8) |
| S | 🔄 S0–S3✅ · **S4** Mimar `evet` · sırada **S5** |
| V | ⬜ S mühürüne bağlı |
| M | ⬜ V mühürüne bağlı |

**Son işaret:** 2026-10-23 — S3 yeşil (hard-gate) → S5 fuzzy/sentez (S4 ayrı `evet`).

---

## Temizlik (Mimar emri 2026-10-23)

**P + S + V + M hepsi mühürlenince** bu yol haritası kalabalık yapmasın diye silinebilir:

1. `RUZGAR_YOL_HARITASI.md` — sil  
2. `.cursor/rules/ruzgar-yol-haritasi-FROZEN.mdc` — sil  
3. `PROJE_DURUMU.md` içindeki «YOL HARİTASI» bloğu — kısa «P–M tamam · yol haritası kaldırıldı» notuna indir  

Özet başarılar ve KPI `PROJE_DURUMU.md` / git tarihinde kalır; ayrı plan dosyası tutulmaz.  
Erken silme yok — dört faz mühürsüzken bu dosya **durur**.
