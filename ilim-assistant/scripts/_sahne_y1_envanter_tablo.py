# -*- coding: utf-8 -*-
"""Sıra 18: tam envanter tablosu — meslek · lisans · yol · RAG-aday. RAG çalıştırmaz."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
RAF = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"
ENV = RAF / "SAHNE_Y1_ENVANTER_2026-11-13.json"
MES = RAF / "SAHNE_Y1_MESLEK_RAFLARI_RAPOR.json"
OUT_JSON = RAF / "SAHNE_Y1_ENVANTER_TABLO_2026-11-13.json"
OUT_DOCX = Path(r"C:\Users\hayma\Desktop\RÜZGAR") / "RUZGAR_SAHNE_ENVANTER_TABLO_2026-11-13.docx"

# Açık lisans varsayılanı (kaynak türüne göre)
LISANS = {
    "openstax": "CC BY (OpenStax)",
    "mdn": "CC BY-SA (MDN)",
    "w3c": "W3C Document License / açık TR",
    "wikipedia": "CC BY-SA",
    "maplibre": "BSD (MapLibre docs)",
    "ffmpeg": "LGPL/GPL (FFmpeg docs)",
    "khronos": "Khronos açık spesifikasyon",
    "osm": "ODbL (OSM) / wiki CC BY-SA",
    "homeassistant": "Apache-2.0 docs",
    "other_open": "Açık dokümantasyon / kamu",
}


def guess_lisans(url: str, baslik: str) -> str:
    u = (url or "").lower()
    b = (baslik or "").lower()
    if "openstax" in u:
        return LISANS["openstax"]
    if "mozilla.org" in u or "mdn" in b:
        return LISANS["mdn"]
    if "w3.org" in u:
        return LISANS["w3c"]
    if "wikipedia.org" in u:
        return LISANS["wikipedia"]
    if "maplibre" in u or "maplibre" in b:
        return LISANS["maplibre"]
    if "ffmpeg" in u or "ffmpeg" in b:
        return LISANS["ffmpeg"]
    if "khronos" in u or "gltf" in b:
        return LISANS["khronos"]
    if "openstreetmap" in u or "osm" in b:
        return LISANS["osm"]
    if "home-assistant" in u:
        return LISANS["homeassistant"]
    return LISANS["other_open"]


def row(meslek: str, paket: str, baslik: str, yol: str, url: str, parca: int, rag: str, durum: str) -> dict:
    return {
        "meslek": meslek,
        "paket": paket,
        "baslik": baslik,
        "yol": yol,
        "url": url,
        "parca": parca,
        "lisans": guess_lisans(url, baslik),
        "rag_aday": rag,
        "durum": durum,
    }


def main() -> int:
    rows: list[dict] = []
    env = json.loads(ENV.read_text(encoding="utf-8")) if ENV.exists() else {}
    for key, meta in (env.get("zaten_var") or {}).items():
        rows.append(
            row(
                "omurga/ortak",
                key,
                key,
                f"bilgisayar_eserleri + {meta.get('kaynak')}",
                "",
                0,
                "evet" if "openstax" in key or "harita" in key or "uzay" in key else "kismi",
                meta.get("durum") or "zaten_var",
            )
        )

    if MES.exists():
        mes = json.loads(MES.read_text(encoding="utf-8"))
        meslek_map = {
            "mimar_bina_3d": "mimar/muteahhit",
            "yonetmen_kurgu": "yonetmen/editor",
            "egitim_anatomi": "doktor/egitmen",
            "hukuk_dosya_masa": "avukat/noter",
            "muzik_partisyon": "muzisyen",
            "gazeteci_acik_veri": "gazeteci",
            "ciftci_saha": "ciftci/saha",
            "ogrenci_quiz": "ogrenci",
            "aile_cihaz": "aile",
            "muhendis_sim": "muhendis",
            "gezgin_rehber": "gezgin/tarihci",
        }
        for key, item in (mes.get("items") or {}).items():
            dal = item.get("dal") or ""
            yol = str(RAF / dal / "metin" / key)
            rows.append(
                row(
                    meslek_map.get(key, key),
                    key,
                    item.get("baslik") or key,
                    yol,
                    item.get("url") or "",
                    int(item.get("parca") or item.get("parca_sayisi") or 0),
                    "evet",
                    "kalin" if item.get("ok") else "eksik",
                )
            )

    # Yazılımcı / araştırmacı zaten var satırları
    rows.append(
        row(
            "yazilimci",
            "bilgisayar_eserleri_01_12 + ILERI_F",
            "Programlama kalın külliyat",
            str(RAF / "01_programlama"),
            "",
            7034,
            "kismi",
            "zaten_var",
        )
    )
    rows.append(
        row(
            "arastirmaci",
            "ilim+shamile+IR+tercume",
            "İlim/Şamile + IR + MT yakıtı",
            str(ROOT / "knowledge/ilim"),
            "",
            0,
            "kismi",
            "zaten_var_kismi",
        )
    )

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "plan_adim": 18,
        "n": len(rows),
        "rag_not": "Bu tabloda rag_aday işaretli; ingest YALNIZ sıra 33'te",
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(1.8)
        s.bottom_margin = Cm(1.8)
        s.left_margin = Cm(1.8)
        s.right_margin = Cm(1.8)
    doc.add_heading("RÜZGAR — SAHNE ENVANTER TABLOSU", 0)
    p = doc.add_paragraph()
    r = p.add_run("Tarih: 2026-11-13 · Plan sıra 18 · RAG henüz yok")
    r.font.size = Pt(11)
    table = doc.add_table(rows=1, cols=6)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, name in enumerate(["Meslek", "Paket", "Lisans", "Parça", "RAG-aday", "Durum"]):
        hdr[i].text = name
    for rowd in rows:
        cells = table.add_row().cells
        cells[0].text = rowd["meslek"]
        cells[1].text = rowd["paket"]
        cells[2].text = rowd["lisans"]
        cells[3].text = str(rowd["parca"])
        cells[4].text = rowd["rag_aday"]
        cells[5].text = rowd["durum"]
    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_DOCX)
    print("JSON", OUT_JSON)
    print("DOCX", OUT_DOCX, "rows", len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
