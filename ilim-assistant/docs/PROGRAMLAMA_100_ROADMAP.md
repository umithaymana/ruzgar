# Programlama Motoru 100/100 Yol Haritasi

Bu plan iki ana hedefe odaklanir:
- Komut anlama seviyesi: 86 -> 100
- Bagimsiz proje tamamlama seviyesi: 68 -> 100

## Adim 1 - Release Gate (tamamlandi)
- `scripts/programlama_upgrade_runner.py` eklendi.
- Faz 98 komut degerlendirmesi + Faz 99 iki ardisk kosu birlikte olculuyor.
- `--strict` modunda sure ve tutarlilik sarti zorunlu.

## Adim 2 - Komut Altin Veri Seti (Blok D — 2026-05-29)
- `scripts/programlama_command_goldens.json` — **50** ifade (explicit, natural, shell, approval, winget, noise).
- `prepare_command_golden_fixtures()` — bench öncesi test dosyaları (battery + masaüstü/indirilenler).
- Faz 98: `şuraya kopyala` doğal dil kalıbı; `evaluate_command_dataset()` + `--strict` gate ≥95.
- **Aylık revizyon (D40):** Her ay başı başarısız `checks` satırlarını altın sete ekle veya Faz 98 regex güncelle; `Ruzgar_Programlama_Bench.bat strict` ile doğrula.

## Adim 3 - Gorev Merdiveni (Blok E — 2026-05-29)
- `scripts/programlama_task_ladder.json` — **S1–S5** (small → full).
- S4: parity quick 8/8 · S5: komut + Faz99 x2 + parity + git commit.
- `independence_level` = min(komut, otonomi, parity); strict gate ≥95.

## Adim 4 - Onay Guvenlik Standardi (isliyor, sertlestirme acik)
- Faz 98 onay kapisi aktif.
- Sonraki artirim: risk sinifina gore zorunlu aciklama sablonu.

## Adim 5 - Tekrar Eden Hata Azaltma (siradaki adim)
- Runner ciktilarindan "basarisiz kontrol -> kok neden etiketi" uret.
- Ayni kok neden tekrarinda kural onerisi kaydi ac.

## Adim 6 - SLA ve KPI (siradaki adim)
- Upgrade raporunu haftalik KPI'ya bagla.
- Hedef: komut >=95, bagimsiz >=95, tutarlilik = true.

## Calistirma
- Sadece upgrade gate:
  - `python scripts/programlama_upgrade_runner.py --strict`
- Smoke ile beraber:
  - `python scripts/programlama_smoke.py --upgrade`
- Windows kisa yol (kök):
  - `scripts\Ruzgar_Programlama_Bench.bat` — normal gate
  - `scripts\Ruzgar_Programlama_Bench.bat strict` — **CI / release oncesi zorunlu** (`--strict`: sure + tutarlilik + esik)

**CI notu:** PR veya Blok D/E merge oncesi `--strict` gecmeli; gunluk gelistirmede strictsiz bench yeterli.
