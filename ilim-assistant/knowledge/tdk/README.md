# TDK (yerel hafıza) — dosya formatı ve kademeli yükleme

Rüzgar’ın vektör araması (`rag_store`) `knowledge/` altındaki tüm `*.md` dosyalarıyla çalışır.

## 1) Bu klasöre ne koyacağız?
- TDK sözlük / tanımlar
- Dünya tarihi gibi “kademeli” veri parçaları

Her bilgi parçası bir `*.md` dosyası olacak şekilde eklenmeli.

## 2) MD dosyalarında önerilen biçim
Dosya başlığı (ilk `#` satırı) aramada “kaynak” olarak geçer:

```md
# {Madde / konu başlığı}

Kısa tanım / açıklama metni...

> Kaynak: TDK (veya ek bir iç not)
```

Önemli: aynı konuya dair kısa maddeleri birleştirip tek dev dosya yapmak yerine, **konuya göre parçalara ayır**.

## 3) Kademeli veri yükleme (incremental ingest)
BDİT: İlk defa veya model değiştiğinde tam indeks oluşturmak gerekir.

1. İlk kurulum:
   - `python -m ilim_assistant.ingest_cli --force`
2. Daha sonra yalnızca eklediğiniz/ değiştirdiğiniz md’leri gömmek için:
   - `python -m ilim_assistant.ingest_cli --incremental`

Bu sayede TDK’yi “adım adım” eklerken her seferinde tüm `knowledge/` tekrar gömülmez.

