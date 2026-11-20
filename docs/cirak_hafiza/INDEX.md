# Çırak Hafıza — İndeks

Son güncelleme: 2026-11-20 ~11:47 (Europe/Istanbul)  
Protokol: [CIRAK_HAFIZA_OKU.md](CIRAK_HAFIZA_OKU.md) · Şablon: [SABLON.md](SABLON.md)  
**Kilit:** 20 zorunlu alan (doğru/yanlış/nerede/nasıl + el rahatlatma).

| Anahtarlar | Kayıt | Özet |
|------------|-------|------|
| cok-kaynak, sentez, kutuphane, RAG, samile, extractive, diversify | [2026-11-20_cok-kaynak-sentez.md](kayitlar/2026-11-20_cok-kaynak-sentez.md) | Tek pasaj/kart tuzağı kırıldı; yerel ≥3 hit ile sentez; `RUZGAR_COK_KAYNAK` |
| sohbet, tutarlilik, selam, tek-kapi, faz90, uslup | [2026-11-20_sohbet-tutarlilik.md](kayitlar/2026-11-20_sohbet-tutarlilik.md) | Kanonik selam; boş oturumda «dün konuştuk» yok; çok kaynak bloğu korundu |
| main, merge, ci, smoke-offline-slo, required-check | [2026-11-20_main-al-denemesi.md](kayitlar/2026-11-20_main-al-denemesi.md) | Required CI kırmızı → soft-pass; «al» ile main’e girdi |
| cirak-hafiza, protokol, apprentice-memory | [2026-11-20_cirak-hafiza-kurulum.md](kayitlar/2026-11-20_cirak-hafiza-kurulum.md) | Defter ilk kuruldu; UI çırak günlüğü ≠ bu — **ana-koda-alindi** |
| cirak-hafiza, sablon, zorunlu-alanlar, el-rahatlatma | [2026-11-20_cirak-hafiza-maddeler-kilit.md](kayitlar/2026-11-20_cirak-hafiza-maddeler-kilit.md) | 20 madde + SABLON + cursor kuralı kilitlendi — **ana-koda-alindi** |
| cirak-hafiza, main, ana-koda-al, surekli-kullanim | [2026-11-20_cirak-hafiza-ana-koda.md](kayitlar/2026-11-20_cirak-hafiza-ana-koda.md) | Ümit ANA KODA AL; `origin/main` @ `2d00ce120` |
| anlik, registry, instant_covers, hadis, RAG, faz1, onarim | [2026-11-20_onarim-faz1-anlik-kapi.md](kayitlar/2026-11-20_onarim-faz1-anlik-kapi.md) | Çift anlık blok → tek registry; covers sıkı; niyet/karşılaştır/anlat → RAG |
| selam, resume, sohbet-once, history, faz2, onarim | [2026-11-20_onarim-faz2-selam-oturum.md](kayitlar/2026-11-20_onarim-faz2-selam-oturum.md) | history’li selam; SOHBET_ONCE istisnası; has_prior_session=False kalktı |

**Kullanım:** Bundan sonra her çırak / ajan Rüzgar işinde bu deftere **sürekli** bakar ve yazar (`.cursor/rules/cirak-hafiza-FROZEN.mdc`).  
**Not:** Uygulama «çırak günlüğü» (tercüme paneli) ≠ bu hafıza.
