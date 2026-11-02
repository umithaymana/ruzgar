# -*- coding: utf-8 -*-
"""INDEX.xlsx doldur + Rüzgar beceri raporu (24 dal tamamlandıktan sonra)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook

DESK = Path(r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE İNDEKS\BİLGİSAYAR BİLİMLERİ")
RAF = Path(__file__).resolve().parents[1] / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"

SKILL_MAP = {
    1: "Programlama dillerinin temelleri (Python, JavaScript, Rust yönü), veri yapıları ve günlük yazılım pratiği.",
    2: "Algoritma tasarımı, karmaşıklık düşüncesi, graf/ağaç yapıları ve yarışma programlama omurgası.",
    3: "Yapay zekâ ve makine öğrenmesi kavramları, sinir ağları, pekiştirmeli öğrenme, arama/planlama.",
    4: "Veritabanı modelleme, SQL, işlem/eşzamanlılık ve depolama temelleri.",
    5: "Bilgisayar ağları, TCP/IP, protokoller; Beej ve HPBN çizgisinde ağ programlama.",
    6: "İşletim sistemleri: süreç, bellek, dosya sistemleri (OSTEP çizgisi).",
    7: "Siber güvenlik temeli, OWASP yaklaşımı ve güvenli kodlama alışkanlığı.",
    8: "Yazılım mimarisi, tasarım desenleri, açık kaynak mimari örnekleri (AOSA) ve ölçeklenebilirlik.",
    9: "DevOps düşüncesi, CI/CD kavramları, konteyner ve orkestrasyon doküman omurgası.",
    10: "Veri bilimi borusu, istatistik (Think Stats/Bayes) ve analiz temelleri.",
    11: "Bilgisayar bilimine giriş omurgası ve temel CS kavramları.",
    12: "Bilgisayar mühendisliği: donanım-yazılım köprüsü, NAND2Tetris yönü.",
    13: "Mühendislik matematiği: kalkülüs/lineer cebir açık kaynak yönü.",
    14: "Fizik temellerine açık ders kitabı yönü.",
    15: "Elektronik temelleri ve açık kaynak ders yönü.",
    16: "Robotik temelleri, kontrol ve ROS doküman yönü.",
    17: "Mekatronik sistem düşüncesi.",
    18: "Bilimsel araştırma yöntemi ve akademik çalışma disiplini.",
    19: "Psikoloji temelleri (açık kaynak / OCW yönü).",
    20: "Bilişsel bilimlere giriş.",
    21: "Dil bilimi ve NLP (Jurafsky SLP çizgisi).",
    22: "Felsefe klasik metinlere açık erişim yönü.",
    23: "Ekonomi temelleri (açık ders yönü).",
    24: "Oyun teorisi temelleri (açık ders notları yönü).",
}

DAL_NAMES = {
    23: "EKONOMİ",
    24: "OYUN TEORİSİ",
}
HEDEFLER = {23: 100, 24: 75}


def _collect_kats() -> dict[int, dict]:
    out: dict[int, dict] = {}
    for d in sorted(RAF.iterdir()):
        if not d.is_dir():
            continue
        k = d / "katalog.json"
        if not k.exists():
            continue
        data = json.loads(k.read_text(encoding="utf-8"))
        m = re.match(r"^(\d+)_", d.name)
        if m:
            out[int(m.group(1))] = data
    return out


def _collect_stats(kats: dict[int, dict]) -> dict[int, dict]:
    stats: dict[int, dict] = {}
    for p in sorted(DESK.glob("*_F_karar.xlsx")):
        m = re.match(r"\s*(\d+)", p.name)
        if not m:
            continue
        num = int(m.group(1))
        wb = load_workbook(p, read_only=True, data_only=True)
        ws = wb.active
        n = indir = muadil = ilave = 0
        ozet = kazanim = None
        for r in range(3, (ws.max_row or 0) + 1):
            a = ws.cell(r, 1).value
            if isinstance(a, str) and a.upper() in ("ÖZET", "OZET"):
                ozet = ws.cell(r, 2).value
                continue
            if isinstance(a, str) and "KAZANIM" in a.upper():
                kazanim = ws.cell(r, 2).value
                continue
            try:
                int(a)
            except Exception:
                continue
            n += 1
            f = str(ws.cell(r, 6).value or "")
            g = str(ws.cell(r, 7).value or "")
            if f == "indirebilirim":
                indir += 1
                if "ilave" in g.lower():
                    ilave += 1
            elif f == "indiremem":
                muadil += 1
        wb.close()
        kat = kats.get(num, {})
        stats[num] = {
            "n": n,
            "indir": indir,
            "muadil": muadil,
            "ilave": ilave,
            "sources": kat.get("sources") or kat.get("ok_sources"),
            "ok_sources": kat.get("ok_sources"),
            "skills": kat.get("skills") or [],
            "ozet": ozet,
            "kazanim": kazanim,
            "excel": p.name,
        }
    return stats


def main() -> int:
    kats = _collect_kats()
    stats = _collect_stats(kats)
    for num in sorted(stats):
        s = stats[num]
        print(
            f"{num:02d} n={s['n']} indir={s['indir']} muadil={s['muadil']} "
            f"ilave={s['ilave']} src={s['sources']} ok={s['ok_sources']}"
        )

    idx_path = DESK / "İNDEX.xlsx"
    wb = load_workbook(idx_path)
    ws = wb.active

    for r in range(3, ws.max_row + 1):
        try:
            num = int(ws.cell(r, 1).value)
        except Exception:
            continue
        s = stats.get(num)
        if not s:
            continue
        hedef = ws.cell(r, 3).value
        covered = s["indir"] + s["muadil"]
        ws.cell(r, 4).value = covered
        ws.cell(r, 5).value = (
            f"Tamam · liste {s['n']}/{hedef} · yasal kaynak {s['ok_sources'] or s['sources']} · "
            f"doğrudan {s['indir'] - s['ilave']} · muadil {s['muadil']} · ilave {s['ilave']}"
        )

    existing: set[int] = set()
    for r in range(3, ws.max_row + 1):
        try:
            existing.add(int(ws.cell(r, 1).value))
        except Exception:
            pass
    for num in (23, 24):
        if num in existing:
            continue
        r = ws.max_row + 1
        ws.cell(r, 1).value = num
        ws.cell(r, 2).value = DAL_NAMES[num]
        ws.cell(r, 3).value = HEDEFLER[num]
        s = stats.get(num, {})
        covered = (s.get("indir") or 0) + (s.get("muadil") or 0)
        ws.cell(r, 4).value = covered or None
        if s:
            ws.cell(r, 5).value = (
                f"Tamam · liste {s['n']} · yasal kaynak {s.get('ok_sources')}"
            )

    # Clear old footer markers if re-run
    for r in range(ws.max_row, 2, -1):
        a = ws.cell(r, 1).value
        if isinstance(a, str) and a.upper() in (
            "DURUM",
            "TARİH",
            "TARIH",
            "RÜZGAR TOPLAM KAZANIM RAPORU",
            "GENEL SONUÇ",
            "NO",
        ):
            for c in range(1, 6):
                ws.cell(r, c).value = None
        elif isinstance(a, int) and a >= 1 and a <= 24 and r > 30:
            for c in range(1, 6):
                ws.cell(r, c).value = None

    row = max(r for r in range(3, ws.max_row + 1) if ws.cell(r, 1).value not in (None, "")) + 2
    ws.cell(row, 1).value = "DURUM"
    ws.cell(row, 2).value = (
        "Yüklemeler tamamlandı — 24 dalın tamamı F/G analizi + yasal kaynak yerleştirme + özet satırlarıyla işlendi."
    )
    row += 1
    ws.cell(row, 1).value = "TARİH"
    ws.cell(row, 2).value = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    row += 2
    ws.cell(row, 1).value = "RÜZGAR TOPLAM KAZANIM RAPORU"
    row += 1
    ws.cell(row, 1).value = "No"
    ws.cell(row, 2).value = "Dal"
    ws.cell(row, 3).value = "Kazandığı beceriler (anlaşılır özet)"
    row += 1

    dal_by_num: dict[int, str] = {}
    for rr in range(3, 40):
        try:
            n = int(ws.cell(rr, 1).value)
        except Exception:
            continue
        dal_by_num[n] = str(ws.cell(rr, 2).value or f"Dal {n}")

    for num in range(1, 25):
        ws.cell(row, 1).value = num
        ws.cell(row, 2).value = dal_by_num.get(num, DAL_NAMES.get(num, f"Dal {num}"))
        ws.cell(row, 3).value = SKILL_MAP.get(num, "")
        row += 1

    row += 1
    ws.cell(row, 1).value = "GENEL SONUÇ"
    ws.cell(row, 2).value = (
        "Bu 24 Excel ile Rüzgar; programlama, algoritma, YZ, veri, ağ, işletim sistemi, güvenlik, mimari, "
        "DevOps, veri bilimi, CS/mühendislik, matematik-fizik-elektronik-robotik-mekatronik, araştırma, "
        "psikoloji, bilişsel bilim, dil bilimi, felsefe, ekonomi ve oyun teorisi alanlarında "
        "yasal açık kaynak omurgasına sahip oldu. Ticari/telifli eserler indirilmedi; muadilleri ve ilave "
        "ücretsiz eserlerle liste tamamlandı. Metinler knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/ altında."
    )

    try:
        wb.save(idx_path)
        print("INDEX saved", idx_path)
    except PermissionError:
        alt = idx_path.with_name("İNDEX_TAMAMLANDI.xlsx")
        wb.save(alt)
        print("INDEX saved alt", alt)

    md = [
        "# Bilgisayar Bilimleri kütüphane yükleme — tamamlandı",
        "",
        f"Tarih: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Dal özeti",
        "",
        "| No | Liste | Doğrudan | Muadil | İlave | Yasal kaynak |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for num in sorted(stats):
        s = stats[num]
        md.append(
            f"| {num} | {s['n']} | {s['indir'] - s['ilave']} | {s['muadil']} | "
            f"{s['ilave']} | {s['ok_sources'] or s['sources']} |"
        )
    md += ["", "## Rüzgar’ın kazandığı beceriler", ""]
    for num, text in SKILL_MAP.items():
        md.append(f"{num}. {text}")
    md += [
        "",
        "## Genel",
        "",
        "Yüklemeler tamamlandı. 24 dal F/G analizi, muadil, ilave, indirme, "
        "raf yerleştirme ve Excel özet satırlarıyla işlendi.",
    ]
    (RAF / "INDEX_TAMAMLANDI_RAPOR.md").write_text("\n".join(md), encoding="utf-8")
    (RAF / "index_tamam_rapor.json").write_text(
        json.dumps(
            {
                "stats": stats,
                "skills": SKILL_MAP,
                "utc": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("MD+JSON report written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
