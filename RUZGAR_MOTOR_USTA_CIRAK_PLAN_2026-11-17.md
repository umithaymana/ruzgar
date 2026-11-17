# RÜZGAR — Motor güçlendirme · Usta / Çırak planı

**Tarih:** 2026-11-17  
**Mimar emri:** plana yaz + ilk sıradan başla; her yeşilden sonra diğerine geç  
**Model:** Ben = usta (Cursor ajanı) · Rüzgar programlama = çırak  
**Durum:** Dilim 0–7 mühür · **Dilim 8 Hızır** + erken tek yüz meta

---

## Öğrenme kuralı (çıraklık sayılır)

Her yeşil dilimde **en az bir ders** sisteme yazılır:
- niyet/kapı düzeltmesi, veya
- handoff şablonu, veya
- smoke case

Ders yazılmadan dilim yeşil sayılmaz. Seyretmek ≠ öğrenmek.  
Modül: `ilim_assistant/ruzgar_cirak_ders.py`

---

## Kilitler (dokunulmaz)

- Boot sırası (`.cursorrules`)
- Ana yüz kilidi (motor listesi / tutamaç / dört masa çerçevesi)
- Anayasa (evrensel dünya / hardcode yok)
- Serbest ajan / izinsiz silme yok

---

## Ritmi (her dilim)

1. Usta: dar hedef + (mümkünse) çırak `görev:`  
2. Çırak dener veya usta ölçer  
3. Kırılgan yerde usta müdahale  
4. Smoke (+ kısa canlı)  
5. Ders kaydı → plan işaretle → sonraki dilim  

---

## Dilimler

| # | Dilim | Çıkış | Durum |
|---|--------|--------|--------|
| **0** | Canlı bağ envanteri | Smoke tablo | **[x]** |
| **1** | Ses tek yüz | Smoke | **[x]** |
| **2** | Hafıza tek yüz | Smoke; hatırla çalmaz | **[x]** |
| **3** | Mimar tek yüz | İlim kaçmaz | **[x]** |
| **4** | Okuma netliği | `kismi_kasten` kart | **[x]** |
| **5** | Video bağ cilası | Faz E mutlu yol | **[x]** |
| **6** | Programlama çırak döngüsü | Ders sözleşmesi | **[x]** |
| **7** | Mühür | öz-bilgi ↔ tek yüz | **[x]** |
| **8** | Hızır tek yüz + erken orchestra meta | Panel handoff; pazar API yok | **[x]** 2026-11-17 |

### Bilinçli sonra / yok

- Gelişim → hub (ayrı onay)
- %90 serbest programlama
- Boot değiştirme
- Sahne/OSM yeni dilim
- 32B/70B

---

## Ders defteri

| Dilim | Ders (kısa) | Dosya / smoke |
|-------|-------------|----------------|
| **0** | Bağ ≠ güç: `tam_is_bagi` = hub+tek yüz | `smoke_motor_bag_envanter_d0.py` |
| **1** | Atölye öneki handoff; profil anlığı faz72’de kalsın | `ana_motor_faz_ses_tek_yuz.py` · `ana_motor_faz_ses_smoke.py` |
| **2** | Panel doldur ≠ kart yaz; `hatırla:` çalma | `ana_motor_faz_hafiza_tek_yuz.py` · `ana_motor_faz_hafiza_smoke.py` |
| **3** | İlim/nedir mimara düşmez | `ana_motor_faz_mimar_tek_yuz.py` · `ana_motor_faz_mimar_smoke.py` |
| **4** | Okuma yetim değil; `kismi_kasten` | `smoke_okuma_netlik_d4.py` · öz-bilgi kart |
| **5** | Video tek yüz + sohbet kaçmaz | `smoke_video_bag_cilasi_d5.py` |
| **6** | Yeşil = iş + ders; usta kırılgan listesi | `ruzgar_cirak_ders.py` · `smoke_cirak_ders_d6.py` |
| **7** | Kart ↔ faz bayrakları aynı gerçek | `smoke_motor_bag_muhur_d7.py` |
| **canlı** | `seste: Merhaba…` fast-lane/casual/hafıza ezmesin; UI cache bust | `chat_fast_lane` · `hafiza_dogal` · `tek_beyin` |
| **8** | Hızır panel handoff; pazar API bayrağı False; stream’de erken `tek_yuz_early` meta | `ana_motor_faz_hizir_tek_yuz.py` · smoke · `_async_iter_chat_events` |
| **9 çırak** | Supervised yazım + kök = `repo_root` (cwd değil); canlı `hello_cirak.py` | `try_cirak_supervised_write` · smoke_d6 |

**Sonraki (yarın):** çırak eksik giderme A–F → `RUZGAR_CIRAK_GELISIM_PLAN_2026-11-18.md`

---

## Canlı kullanım (Mimar)

Sunucu kodu için: `.\Ruzgar.ps1 -ForceRestart`  
Örnek cümleler:
- `seste: Merhaba Ümit abi`
- `hafızada: not satırı` (otomatik kayıt yok)
- `mimarda: logo taslağı`
- `şu videoyu indir https://…`
- `görev: …` (programlama)

Çırak görev şablonu: `görev: [cirak:smoke_yesil] …` (`ruzgar_cirak_ders.cirak_gorev_metni`)
