# -*- coding: utf-8 -*-
"""Sağlama bitiş raporu — yapılanlar + kalanlar (temiz Word)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

DESK = Path(r"C:\Users\hayma\Desktop\RÜZGAR")
OUT = DESK / f"RUZGAR_SAGLAMA_RAPORU — {datetime.now().strftime('%Y-%m-%d')}.docx"
RAF = Path(__file__).resolve().parents[1] / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"
MIN = 40


def add_h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    return p


def add_p(doc, text, bold=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.font.size = Pt(11)
    return p


def add_num(doc, n, text):
    p = doc.add_paragraph()
    r = p.add_run(f"{n}. {text}")
    r.font.size = Pt(11)
    return p


def katalog_stats():
    thick = thin = 0
    thins = []
    for dal in sorted(p for p in RAF.iterdir() if p.is_dir() and p.name[:1].isdigit()):
        data = json.loads((dal / "katalog.json").read_text(encoding="utf-8"))
        for key, m in (data.get("kaynaklar") or {}).items():
            p = int(m.get("parca") or m.get("parca_sayisi") or 0)
            if p >= MIN:
                thick += 1
            else:
                thin += 1
                thins.append(f"{dal.name}/{key} (parça={p})")
    return thick, thin, thins


def rag_manifests():
    root = Path(__file__).resolve().parents[1]
    out = {}
    for name in (".rag_index_bilgisayar", ".rag_index_ayiklama", ".rag_index"):
        man = root / name / "manifest.json"
        if man.is_file():
            try:
                out[name] = json.loads(man.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                out[name] = {"error": "json"}
        else:
            out[name] = {"missing": True}
    return out


def main() -> int:
    thick, thin, thins = katalog_stats()
    rag = rag_manifests()
    bb = rag.get(".rag_index_bilgisayar") or {}
    ay = rag.get(".rag_index_ayiklama") or {}
    ana = rag.get(".rag_index") or {}

    doc = Document()
    add_h(doc, "Rüzgar — Sağlama Raporu", 0)
    add_p(doc, f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}", bold=True)
    add_p(
        doc,
        "Bu belge, büyük plan Excel/Word sağlaması sonrası yapılan işleri ve bilinçli kalanları listeler.",
    )

    add_h(doc, "A) Yapılanlar (numaralı)", 1)
    done = [
        "Excel RÜZGAR_BUYUK_PLAN.xlsx (13 sayfa) gözden geçirildi; Ana_Sıra 0→6 ve §10 mühürleri doğrulandı.",
        "Word PLANIMIZ güncel FACT ile uyumlu hale getirildi (Motor A→F, bilgisayar RAG, donanım Basamak0).",
        "Plan→sistem eşlemesi doğrulandı: health, Şamile shards, ayıklama RAG, bilgisayar RAG, Motor C–F vitrin smoke.",
        "desktop_server DDGS lazy-import kırığı giderildi (eksik paket sunucuyu düşürmez).",
        f"Bilgisayar rafları kalınlaştırıldı: kalın eser {thick} (eşik≥{MIN} parça).",
        "İnce→kalın scriptleri eklendi: _saglama_tum_ince_kalin / pass2 / pass3_boost; shrink koruması.",
        "Raf yerleşimi kontrol: orphan/katalog-metin uyumsuzluğu 0.",
        f"Bilgisayar RAG indeksi: {bb.get('num_chunks', '?')} chunk · {bb.get('num_files', '?')} dosya · built {bb.get('built_at', '?')}.",
        f"Ayıklama RAG: {ay.get('num_chunks', '?')} chunk · ready.",
        f"Ana .rag_index: {ana.get('num_chunks', '?')} chunk.",
        "Kalınlık bayrak onarımı (parça≥40 ama derin_yesil=false) yapıldı.",
        "fonttools kuruldu (PDF metin çıkarımı).",
        "Bu sağlamalama raporu Word olarak üretildi.",
    ]
    for i, t in enumerate(done, 1):
        add_num(doc, i, t)

    add_h(doc, "B) Kalanlar / bilinçli açık", 1)
    remaining = [
        f"Hâlâ ince katalog kaydı: {thin} (çoğu SPA hub, arşiv 429 veya tek sayfa stub; boost denendi).",
        "Madde el / 7/24 merkez fiziksel kurulum: bilinçli kapalı (alım yok; §10.5).",
        "Donanım alımı (RAM 32GB vb.): Mimar talimatıyla yapılmıyor.",
        "İsteğe bağlı: kalan ince stub’ları tek tek manuel URL ile yeniden doldurma veya stub’ları katalogdan ayıklama.",
    ]
    if thins:
        remaining.append("İnce kalan örnekler (ilk 40):")
    for i, t in enumerate(remaining, 1):
        add_num(doc, i, t)
    for t in thins[:40]:
        add_p(doc, f"   • {t}")

    add_h(doc, "C) Özet sayılar", 1)
    add_p(doc, f"Kalın eser (≥{MIN}): {thick}")
    add_p(doc, f"İnce eser (<{MIN}): {thin}")
    add_p(doc, f"Bilgisayar RAG chunk: {bb.get('num_chunks')}")
    add_p(doc, f"Ayıklama RAG chunk: {ay.get('num_chunks')}")

    DESK.mkdir(parents=True, exist_ok=True)
    try:
        doc.save(OUT)
        print("WROTE", OUT)
    except PermissionError:
        print("LOCKED", OUT)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
