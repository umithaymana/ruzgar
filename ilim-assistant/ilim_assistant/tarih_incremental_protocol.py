"""
Tarih Hafızası — Kademeli Vektör İndeksleme (TDK protokolüyle aynı mantık).

Hedef içerik (özet): Türk Tarih Kurumu (TTK) türevi metinler, Osmanlı tarihi,
Büyük Türk Tarihi vb. — hepsi `knowledge/TARIH_VE_KULTUR/` altında toplanır.

Çıktı:
- Paketler: `knowledge/TARIH_VE_KULTUR/incremental/tarih_batch_#####.md`
- Durum: `.rag_index/tarih_protocol_state.json`

Kullanım:
  python -m ilim_assistant.tarih_incremental_protocol init
  python -m ilim_assistant.tarih_incremental_protocol ingest --source path/to/tarih.txt --batch-size 400
  python -m ilim_assistant.tarih_incremental_protocol ingest --source knowledge/TARIH_VE_KULTUR/tarih_kaynak.json --batch-size 500
  python -m ilim_assistant.tarih_incremental_protocol finalize

Kaynak:
  - `.json`: `entries` dizisi veya Digital Ottomans `objects` / TimelineJS `events` kökü.
  - Metin: satır başına `başlık<TAB>metin` (veya `|`, `=`).

Kaynak satır biçimi (UTF-8, TDK protokolüyle uyumlu):
  - `başlık<TAB>metin`
  - `başlık|metin`
  - `başlık = metin`
  Boş satırlar ve `#` ile başlayan satırlar yok sayılır.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ilim_assistant.rag_store import _KNOWLEDGE_ROOT, build_index
from ilim_assistant.tarih_kaynak_fetch import load_tarih_entries_for_ingest

_STATE_PATH = Path(__file__).resolve().parent.parent / ".rag_index" / "tarih_protocol_state.json"
_TARIH_INC_DIR = _KNOWLEDGE_ROOT / "TARIH_VE_KULTUR" / "incremental"
_COMPLETION_MSG = "Tarih Hafızası Başarıyla Tamamlandı"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_state() -> dict[str, Any]:
    if not _STATE_PATH.is_file():
        return {}
    try:
        return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_state(data: dict[str, Any]) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def protocol_lock_active() -> bool:
    st = read_state()
    return st.get("status") == "in_progress" and bool(st.get("exclusive_tarih", True))


def _parse_line(line: str) -> tuple[str, str] | None:
    s = (line or "").strip()
    if not s or s.startswith("#"):
        return None
    if "\t" in s:
        a, b = s.split("\t", 1)
    elif "|" in s:
        a, b = s.split("|", 1)
    elif "=" in s:
        a, b = s.split("=", 1)
    else:
        return None
    title = a.strip()
    body = b.strip()
    if not title:
        return None
    if not body:
        body = "(Metin boş)"
    return title, body


def _tarih_batch_report(n_items: int, batches_written: int, rel: str, info: dict) -> None:
    print(
        "Tarih bilgisi başarıyla hafızaya eklendi "
        f"({n_items} kayıt, paket {batches_written:05d}, dosya: {rel}). İndeks: {info}"
    )


def _entries_to_markdown(entries: list[tuple[str, str]], batch_index: int) -> str:
    head = (
        f"# Tarih ve kültür — kademeli paket\n\n"
        f"- Paket no: `{batch_index:05d}`\n"
        f"- Kayıt sayısı: **{len(entries)}**\n\n"
        "---\n\n"
    )
    parts = [head]
    for title, body in entries:
        parts.append(f"## {title}\n{body}\n\n")
    return "".join(parts)


def cmd_init() -> None:
    _TARIH_INC_DIR.mkdir(parents=True, exist_ok=True)
    st = read_state()
    if st.get("status") == "in_progress":
        print(
            "Uyarı: zaten devam eden bir Tarih protokolü kaydı var. "
            "Sıfırdan başlamak için önce `reset --yes`, sonra tekrar `init`."
        )
    write_state(
        {
            "phase": "tarih_ve_kultur",
            "status": "in_progress",
            "exclusive_tarih": True,
            "started_at": _utc_now_iso(),
            "batches_written": 0,
            "file_line_offset": 0,
            "lines_ingested": 0,
            "source_path": None,
        }
    )
    print(f"OK: Tarih protokolü başlatıldı (in_progress). Çıktı klasörü: {_TARIH_INC_DIR}")


def _flush_tarih_batch(
    batch: list[tuple[str, str]],
    *,
    batches_written: int,
    st: dict[str, Any],
    lines_ingested: int,
    last_cursor: int,
) -> tuple[int, int, dict[str, Any]]:
    out_path = _TARIH_INC_DIR / f"tarih_batch_{batches_written:05d}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_entries_to_markdown(batch, batches_written), encoding="utf-8")
    info = build_index(force=False, incremental=True)
    rel = f"TARIH_VE_KULTUR/incremental/{out_path.name}"
    n_items = len(batch)
    _tarih_batch_report(n_items, batches_written, rel, info)
    st.update(
        {
            "file_line_offset": last_cursor,
            "lines_ingested": lines_ingested,
            "batches_written": batches_written,
            "last_batch_relpath": rel.replace("\\", "/"),
        }
    )
    write_state(st)
    return batches_written, lines_ingested, st


def cmd_ingest(source: Path, batch_size: int) -> None:
    st = read_state()
    if st.get("status") == "complete":
        raise SystemExit(
            "Tarih protokolü tamamlanmış görünüyor. Yeni yükleme için önce: "
            "`python -m ilim_assistant.tarih_incremental_protocol reset --yes`"
        )
    if st.get("status") != "in_progress":
        raise SystemExit("Önce `init` çalıştırın.")

    src = Path(source)
    if not src.is_file():
        raise SystemExit(f"Kaynak bulunamadı: {src}")

    _TARIH_INC_DIR.mkdir(parents=True, exist_ok=True)

    lines_ingested = int(st.get("lines_ingested") or 0)
    batches_written = int(st.get("batches_written") or 0)
    skip_lines = int(st.get("file_line_offset") or 0)

    st["source_path"] = str(src.resolve())
    st["last_ingest_at"] = _utc_now_iso()

    batch: list[tuple[str, str]] = []
    last_consumed = skip_lines
    json_mode = src.suffix.lower() == ".json"

    if json_mode:
        records = load_tarih_entries_for_ingest(src)
        total = len(records)
        if total == 0:
            raise SystemExit("JSON kaynakta indekslenecek kayıt yok.")
        prev_src = st.get("source_path")
        if prev_src and str(prev_src) != str(src.resolve()) and skip_lines > 0:
            print(
                "Uyarı: Kaynak dosya değişmiş görünüyor; yine de file_line_offset ile devam ediliyor. "
                "Sıfırdan başlamak için reset --yes önerilir."
            )
        for idx in range(skip_lines, total):
            ent = records[idx]
            last_consumed = idx + 1
            batch.append(ent)
            lines_ingested += 1
            if len(batch) >= max(1, batch_size):
                batches_written += 1
                batches_written, lines_ingested, st = _flush_tarih_batch(
                    batch,
                    batches_written=batches_written,
                    st=st,
                    lines_ingested=lines_ingested,
                    last_cursor=last_consumed,
                )
                batch.clear()
        if batch:
            batches_written += 1
            batches_written, lines_ingested, st = _flush_tarih_batch(
                batch,
                batches_written=batches_written,
                st=st,
                lines_ingested=lines_ingested,
                last_cursor=last_consumed,
            )
            batch.clear()
    else:
        with src.open(encoding="utf-8", errors="replace") as f:
            for lineno, raw in enumerate(f, start=1):
                if lineno <= skip_lines:
                    continue
                last_consumed = lineno
                ent = _parse_line(raw)
                if ent is None:
                    continue
                batch.append(ent)
                lines_ingested += 1
                if len(batch) >= max(1, batch_size):
                    batches_written += 1
                    batches_written, lines_ingested, st = _flush_tarih_batch(
                        batch,
                        batches_written=batches_written,
                        st=st,
                        lines_ingested=lines_ingested,
                        last_cursor=last_consumed,
                    )
                    batch.clear()

        if batch:
            batches_written += 1
            batches_written, lines_ingested, st = _flush_tarih_batch(
                batch,
                batches_written=batches_written,
                st=st,
                lines_ingested=lines_ingested,
                last_cursor=last_consumed,
            )
            batch.clear()
        elif last_consumed > skip_lines and not json_mode:
            st["file_line_offset"] = last_consumed
            write_state(st)

    st.update(
        {
            "lines_ingested": lines_ingested,
            "batches_written": batches_written,
            "last_ingest_at": _utc_now_iso(),
        }
    )
    write_state(st)
    cursor_label = "kayıt imi" if json_mode else "satır imi"
    print(
        f"OK: ingest turu bitti. Kaynak {cursor_label}: {int(st.get('file_line_offset') or 0)}, "
        f"indekslenen madde: {lines_ingested}, paket: {batches_written}. "
        f"Bitirmek için: finalize"
    )


def cmd_finalize() -> None:
    st = read_state()
    if st.get("status") != "in_progress":
        raise SystemExit("Önce init + ingest ile in_progress durumuna gelin.")
    if int(st.get("lines_ingested") or 0) <= 0:
        raise SystemExit("Henüz indekslenecek tarih maddesi yok (ingest çalıştırılmamış olabilir).")
    info = build_index(force=False, incremental=True)
    st.update(
        {
            "status": "complete",
            "exclusive_tarih": False,
            "completed_at": _utc_now_iso(),
            "finalize_index": info,
        }
    )
    write_state(st)
    print(_COMPLETION_MSG)
    print(f"Detay: {json.dumps(info, ensure_ascii=False)}")
    n_done = int(st.get("lines_ingested") or 0)
    if n_done > 0:
        xbin = n_done / 1000.0
        xs = f"{xbin:.2f}".replace(".", ",").rstrip("0").rstrip(",")
        if xs == "":
            xs = "0"
        print(f"Toplam {xs} bin tarihsel veri başarıyla işlendi.")


def cmd_status() -> None:
    st = read_state()
    if not st:
        print("Kayıt yok (henüz init çalışmamış olabilir).")
        return
    print(json.dumps(st, ensure_ascii=False, indent=2))


def cmd_reset(*, yes: bool) -> None:
    if not yes:
        raise SystemExit("Onay için `--yes` verin (incremental md ve protokol kaydı silinir).")
    st = read_state()
    if _STATE_PATH.is_file():
        try:
            _STATE_PATH.unlink()
        except OSError:
            pass
    inc = _KNOWLEDGE_ROOT / "TARIH_VE_KULTUR" / "incremental"
    if inc.is_dir():
        for p in sorted(inc.glob("tarih_batch_*.md")):
            try:
                p.unlink()
            except OSError:
                pass
    print("OK: protokol kaydı ve TARIH_VE_KULTUR/incremental/tarih_batch_*.md temizlendi.")
    if st:
        print("Not: vektör indeksi (.rag_index) duruyor; tam sıfırlamak için `ingest_cli --force` gerekir.")


def main() -> None:
    p = argparse.ArgumentParser(description="Tarih Hafızası — kademeli vektör indeksleme protokolü")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Protokolü başlat ve çıktı klasörünü hazırla")
    p_init.set_defaults(func=lambda _: cmd_init())

    p_ing = sub.add_parser("ingest", help="Kaynak dosyayı paketleyerek yaz ve incremental indeksle")
    p_ing.add_argument("--source", required=True, type=str)
    p_ing.add_argument("--batch-size", type=int, default=400)
    p_ing.set_defaults(func=lambda a: cmd_ingest(Path(a.source), int(a.batch_size)))

    p_fin = sub.add_parser("finalize", help="Protokolü tamamla ve raporu yazdır")
    p_fin.set_defaults(func=lambda _: cmd_finalize())

    p_st = sub.add_parser("status", help="Protokol durumunu göster")
    p_st.set_defaults(func=lambda _: cmd_status())

    p_rs = sub.add_parser("reset", help="Protokol kaydını ve incremental paket md'lerini sil")
    p_rs.add_argument("--yes", action="store_true")
    p_rs.set_defaults(func=lambda a: cmd_reset(yes=bool(a.yes)))

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
