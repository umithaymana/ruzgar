# Created by Ümit & Gökçenur
"""
Ruzgar masaüst menü işlemleri — arşiv kopyası, dışa aktarım ve yapı taşları.
Kültür ve İlim Hazinesi vizyonu: Tasavvuf / Hadis / Klasik Türk Edebiyatı / Tarih-Kültür arşivleri.
Electron main süreci bu dosyayı alt süreç olarak çağırır.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
_ILIM_ASSISTANT = _WORKSPACE_ROOT / "ilim-assistant"
_ARSIV = _ILIM_ASSISTANT / "arsiv"
_KAYNAK_CONFIG = _ILIM_ASSISTANT / ".ruzgar_kaynak_onceligi.json"
_SYSTEM_PREFS = _ILIM_ASSISTANT / ".ruzgar_sistem_ayarlari.json"


def varsayilan_arsiv_hedef(relatif_alt: str = "Tasavvuf_Kulliyati") -> Path:
    """PDF/TXT kopyası için güvenli hedef klasör."""
    dst = (_ARSIV / relatif_alt).resolve()
    if not str(dst).startswith(str(_ARSIV.resolve())):
        raise ValueError("Gecersiz hedef")
    dst.mkdir(parents=True, exist_ok=True)
    return dst


def yeni_kaynak_kopyala(dosya_yollari: list[str], alt_klasor: str = "Tasavvuf_Kulliyati") -> list[str]:
    """Bilgisayardaki dosyaları ilim-assistant/arsiv/<alt_klasor> altına kopyalar."""
    hedef_dir = varsayilan_arsiv_hedef(alt_klasor)
    cikti: list[str] = []
    for src_raw in dosya_yollari:
        src = Path(src_raw).resolve()
        if not src.is_file():
            continue
        dst = hedef_dir / src.name
        shutil.copy2(src, dst)
        cikti.append(str(dst))
    return cikti


def disa_aktar(metin: str, dosya_yolu: str, bicim: str = "txt") -> str:
    """Metni dosyaya yaz; bicim txt veya basit pdf (fpdf2 varsa)."""
    path = Path(dosya_yolu)
    path.parent.mkdir(parents=True, exist_ok=True)
    bicim = bicim.lower().strip().lstrip(".")

    if bicim == "txt":
        path.write_text(metin, encoding="utf-8")
        return str(path)

    if bicim == "pdf":
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=14)
            pdf.add_page()
            pdf.set_font("Helvetica", "", 11)
            for raw in metin.replace("\r\n", "\n").split("\n"):
                satir = raw or " "
                # Helvetica icin ASCII disi tek karakter
                ascii_safe = "".join(ch if ord(ch) < 128 else "?" for ch in satir)
                pdf.multi_cell(0, 6, ascii_safe[:2000])
            pdf.output(str(path))
            return str(path)
        except Exception:
            yedek = path.with_suffix(".txt")
            yedek.write_text(metin, encoding="utf-8")
            return str(yedek)

    path.write_text(metin, encoding="utf-8")
    return str(path)


def bulut_yedekleme_hazirligi() -> dict:
    """Google Drive OAuth / API sonrasına hazırlık notları."""
    return {
        "durum": "hazırlanıyor",
        "oneri": (
            "google-api-python-client + OAuth istem deposu ile "
            "`ilim-assistant/arsiv` ve `.rag_index` yedeklenebilir."
        ),
    }


def bellek_temizle_yerelde() -> dict:
    """Sadece yan etki yok; UI Electron tarafında temizlenir."""
    return {"durum": "ui_temizleme_ipc"}


VARSAYILAN_KAYNAK = {
    "Tasavvuf_Kulliyati": True,
    "Hadis_Kulliyati": True,
    "Klasik_Turk_Edebiyati": True,
    "Tarih_ve_Kultur": True,
    "Kuran_i_Kerim": True,
    "Mektubat_i_Rabbani": True,
    "Mesnevi": True,
    "Fususul_Hikem": True,
    "rag_top_k": int(__import__("os").environ.get("RAG_TOP_K", "4")),
}


def kaynak_onceligi_kaydet(ayarlar: dict | None = None) -> Path:
    """Hangi klasörlerin RAG taramasında öncelikli olduğunu kaydeder (ileri uyum)."""
    data = {**VARSAYILAN_KAYNAK, **(ayarlar or {})}
    _KAYNAK_CONFIG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return _KAYNAK_CONFIG


def sistem_ayarlari_kaydet(
    *,
    metrics_poll_ms_cekirdek: int = 700,
    metrics_poll_ms_normal: int = 2500,
) -> Path:
    """GPU/CPU arayuz yoklaması için tercihler (ileride frontend okuyabilir)."""
    body = {
        "metrics_poll_ms_cekirdek": metrics_poll_ms_cekirdek,
        "metrics_poll_ms_normal": metrics_poll_ms_normal,
        "NOT": "Uzun vadede rag_store embed cihazi (CUDA/CPU) secimi eklenebilir.",
    }
    _SYSTEM_PREFS.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    return _SYSTEM_PREFS


def _cli_kopyala(argv: list[str]) -> None:
    if len(argv) < 2:
        print("usage: menu_islemleri.py kopyala <alt_klasor_relatif> <dosya>...", file=sys.stderr)
        sys.exit(2)
    alt = argv[0]
    paths = argv[1:]
    out = yeni_kaynak_kopyala(paths, alt_klasor=alt)
    payload: dict = {"kopyalanan": out}
    if out:
        payload["mesaj"] = "Mimar, yeni eser kütüphaneye eklendi"
    print(json.dumps(payload, ensure_ascii=False))


def _cli_disa_aktar(argv: list[str]) -> None:
    if len(argv) < 3:
        print("usage: menu_islemleri.py disa_aktar <stdin_utf8_txt> <cikti> <txt|pdf>", file=sys.stderr)
        sys.exit(2)
    girdi_yolu, cikti, bicim = argv[0], argv[1], argv[2]
    metin = Path(girdi_yolu).read_text(encoding="utf-8", errors="replace")
    sonuc = disa_aktar(metin, cikti, bicim)
    print(json.dumps({"yazildi": sonuc}, ensure_ascii=False))


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"uyari": "komut_yok"}, ensure_ascii=False))
        return
    cmd = sys.argv[1]
    tail = sys.argv[2:]
    if cmd == "kopyala":
        _cli_kopyala(tail)
    elif cmd == "disa_aktar":
        _cli_disa_aktar(tail)
    elif cmd == "bulut_yedek":
        print(json.dumps(bulut_yedekleme_hazirligi(), ensure_ascii=False))
    elif cmd == "bellek_placeholder":
        print(json.dumps(bellek_temizle_yerelde(), ensure_ascii=False))
    elif cmd == "kaynak_onceligi":
        if tail and tail[0].strip().startswith("{"):
            data = json.loads(tail[0])
        elif tail:
            cfg = Path(tail[0]).read_text(encoding="utf-8")
            data = json.loads(cfg) if cfg.strip() else {}
        else:
            data = {}
        p = kaynak_onceligi_kaydet(data)
        print(json.dumps({"konfig": str(p)}, ensure_ascii=False))
    elif cmd == "sistem_ayarlari":
        p = sistem_ayarlari_kaydet()
        print(json.dumps({"konfig": str(p)}, ensure_ascii=False))
    else:
        print(json.dumps({"hata": f"bilinmeyen_komut:{cmd}"}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
