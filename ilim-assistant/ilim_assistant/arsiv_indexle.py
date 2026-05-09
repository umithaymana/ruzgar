# Created by Ümit & Gökçenur
"""Dijital ilim arşivini klasör olarak hazırlar ve RAG indeksini günceller.

Külleştirilmiş kökler: Tasavvuf_Kulliyati, Hadis_Kulliyati, Klasik_Turk_Edebiyati,
Tarih_ve_Kultur — Ümit & Gökçenur Kültür ve İlim Hazinesi vizyonu.

Kullanım:
  python -m ilim_assistant.arsiv_indexle
  python -m ilim_assistant.arsiv_indexle --force --no-index  (yalnız klasörleri oluştur)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ilim_assistant.rag_store import build_index_from_roots

_ILIM_ROOT = Path(__file__).resolve().parents[1]
_ARSIV = _ILIM_ROOT / "arsiv"
_TASAVVUF = _ARSIV / "Tasavvuf_Kulliyati"
_HADIS = _ARSIV / "Hadis_Kulliyati"
_KLASIK = _ARSIV / "Klasik_Turk_Edebiyati"
_TARIH = _ARSIV / "Tarih_ve_Kultur"

_MASTER_README = _ARSIV / "README.md"

_ARCHIVE_README_NAME = "ARSIV_ANA_GIRIS.md"

_TAS_README = """---
title: Ümit & Gökçenur — Tasavvuf Külliyatı
---

# Tasavvuf_Kulliyati

Bu ana dizine **PDF** ve **TXT** (ve isteğe bağlı `.md`) eserleri ilgili alt klasörlere yerleştirin.
Üst düzey arşiv yapısı: `arsiv/README.md`.

```bash
python -m ilim_assistant.arsiv_indexle
```

## Alt klasörler

- **Kuran_i_Kerim** — Kur’an-ı Kerim metinleri
- **Mektubat_i_Rabbani** — İmam-ı Rabbani mektubları / ilgili metinler
- **Mesnevi** — Mevlânâ Mesnevî vb.
- **Fususul_Hikem** — İbn-i Arabî Füsûs vb.

İsteğe bağlı `index.jsonl` (satır bazlı JSON) ile hızlı kaynak ipuçları da ekleyebilirsiniz.
"""


def ensure_archive_layout() -> None:
    for name in (
        "Kuran_i_Kerim",
        "Mektubat_i_Rabbani",
        "Mesnevi",
        "Fususul_Hikem",
    ):
        (_TASAVVUF / name).mkdir(parents=True, exist_ok=True)
    p = _TASAVVUF / _ARCHIVE_README_NAME
    if not p.is_file():
        p.write_text(_TAS_README, encoding="utf-8")

    for kok, altlar in (
        (
            _HADIS,
            ("Kutub_i_Sitte", "Diger_Hadis_Kaynaklari"),
        ),
        (
            _KLASIK,
            ("Divan_ve_Siir", "Mesnevi_Serh", "Diger"),
        ),
        (
            _TARIH,
            ("Osmanli", "Islam_Tarihi", "Kultur_ve_Medeniyet"),
        ),
    ):
        kok.mkdir(parents=True, exist_ok=True)
        for a in altlar:
            (kok / a).mkdir(parents=True, exist_ok=True)

    if not _MASTER_README.is_file():
        _MASTER_README.write_text(
            "# Arşiv\n\nÜst düzey külliyat listesi bu depoda `arsiv/README.md` olarak tutulur.\n",
            encoding="utf-8",
        )


def main() -> None:
    p = argparse.ArgumentParser(description="İlim arşivi + RAG indeksi (Ümit & Gökçenur)")
    p.add_argument(
        "--force",
        action="store_true",
        help="Özet değişmese bile indeksi baştan oluştur",
    )
    p.add_argument(
        "--no-index",
        action="store_true",
        help="Yalnızca klasörleri ve başlık dosyalarını oluştur",
    )
    args = p.parse_args()

    ensure_archive_layout()
    if args.no_index:
        print(
            {
                "status": "layout_only",
                "arsiv": str(_ARSIV),
                "vizyon": "Kultur ve Ilim Hazinesi / dort kuliyat kokunden RAG",
            }
        )
        return

    r = build_index_from_roots(force=args.force)
    print(r)


if __name__ == "__main__":
    main()
