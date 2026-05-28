# Programlama Motoru 100/100 Yol Haritasi

Bu plan iki ana hedefe odaklanir:
- Komut anlama seviyesi: 86 -> 100
- Bagimsiz proje tamamlama seviyesi: 68 -> 100

## Adim 1 - Release Gate (tamamlandi)
- `scripts/programlama_upgrade_runner.py` eklendi.
- Faz 98 komut degerlendirmesi + Faz 99 iki ardisk kosu birlikte olculuyor.
- `--strict` modunda sure ve tutarlilik sarti zorunlu.

## Adim 2 - Komut Altin Veri Seti (tamamlandi, genisletilecek)
- `scripts/programlama_command_goldens.json` eklendi.
- Ilk paket 30 farkli ifade iceriyor (explicit, natural, shell, approval, noise).
- Faz 98'e `evaluate_command_dataset()` eklendi.

## Adim 3 - Gorev Merdiveni (tamamlandi, senaryo artacak)
- `scripts/programlama_task_ladder.json` eklendi.
- Kucuk/orta/uretim seviyesi gecis kosullari tanimlandi.
- Runner raporunda her seviye ayrica geciyor.

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
