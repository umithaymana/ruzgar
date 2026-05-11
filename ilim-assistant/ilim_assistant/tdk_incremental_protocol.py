"""
TDK — Kademeli Vektör İndeksleme (Incremental) protokolü.

Amaç:
- TDK verisini tek seferde değil, küçük paketler halinde `knowledge/tdk/incremental/` altına
  Markdown olarak yazmak ve her paketten sonra `build_index(incremental=True)` çalıştırmak.
- Protokol süresince genel `ingest_cli` ile tam bilgi indeksi yenilemeyi kilitlemek (karışmayı önlemek).

Kullanım (özet):
  python -m ilim_assistant.tdk_incremental_protocol init
  python -m ilim_assistant.tdk_incremental_protocol ingest --source path/to/tdk.txt --batch-size 400
  python -m ilim_assistant.tdk_incremental_protocol finalize

Kaynak dosya satır biçimi (UTF-8):
  - `kelime<TAB>anlam`
  - `kelime|anlam`
  - `kelime = anlam`
  Boş satırlar ve `#` ile başlayan satırlar yok sayılır.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ilim_assistant.rag_store import _KNOWLEDGE_ROOT, build_index

_STATE_PATH = Path(__file__).resolve().parent.parent / ".rag_index" / "tdk_protocol_state.json"
_TDK_INC_DIR = _KNOWLEDGE_ROOT / "tdk" / "incremental"
_COMPLETION_MSG = "TDK Hafızası Başarıyla Tamamlandı"


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
    return st.get("status") == "in_progress" and bool(st.get("exclusive_tdk", True))


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
    lemma = a.strip()
    gloss = b.strip()
    if not lemma:
        return None
    if not gloss:
        gloss = "(Tanım boş)"
    return lemma, gloss


def _entries_to_markdown(entries: list[tuple[str, str]], batch_index: int) -> str:
    head = (
        f"# TDK — kademeli paket\n\n"
        f"- Paket no: `{batch_index:05d}`\n"
        f"- Kayıt sayısı: **{len(entries)}**\n\n"
        "---\n\n"
    )
    parts = [head]
    for lemma, gloss in entries:
        parts.append(f"## {lemma}\n{gloss}\n\n")
    return "".join(parts)


def cmd_init() -> None:
    _TDK_INC_DIR.mkdir(parents=True, exist_ok=True)
    st = read_state()
    if st.get("status") == "in_progress":
        print(
            "Uyarı: zaten devam eden bir TDK protokolü kaydı var. "
            "Sıfırdan başlamak için önce `reset --yes`, sonra tekrar `init`."
        )
    write_state(
        {
            "phase": "tdk_only",
            "status": "in_progress",
            "exclusive_tdk": True,
            "started_at": _utc_now_iso(),
            "batches_written": 0,
            "file_line_offset": 0,
            "lines_ingested": 0,
            "source_path": None,
        }
    )
    print(f"OK: TDK protokolü başlatıldı (in_progress). Çıktı klasörü: {_TDK_INC_DIR}")


def cmd_ingest(source: Path, batch_size: int) -> None:
    st = read_state()
    if st.get("status") == "complete":
        raise SystemExit(
            "TDK protokolü tamamlanmış görünüyor. Yeni yükleme için önce: "
            "`python -m ilim_assistant.tdk_incremental_protocol reset --yes`"
        )
    if st.get("status") != "in_progress":
        raise SystemExit("Önce `init` çalıştırın.")

    src = Path(source)
    if not src.is_file():
        raise SystemExit(f"Kaynak bulunamadı: {src}")

    _TDK_INC_DIR.mkdir(parents=True, exist_ok=True)

    lines_ingested = int(st.get("lines_ingested") or 0)
    batches_written = int(st.get("batches_written") or 0)
    skip_lines = int(st.get("file_line_offset") or 0)

    st["source_path"] = str(src.resolve())
    st["last_ingest_at"] = _utc_now_iso()

    batch: list[tuple[str, str]] = []
    last_consumed = skip_lines

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
                n_words = len(batch)
                out_path = _TDK_INC_DIR / f"tdk_batch_{batches_written:05d}.md"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(_entries_to_markdown(batch, batches_written), encoding="utf-8")
                info = build_index(force=False, incremental=True)
                rel = f"tdk/incremental/{out_path.name}"
                print(
                    f"{n_words} kelime başarıyla vektör hafızasına eklendi "
                    f"(paket {batches_written:05d}, dosya: {rel}). İndeks: {info}"
                )
                batch.clear()
                st.update(
                    {
                        "file_line_offset": last_consumed,
                        "lines_ingested": lines_ingested,
                        "batches_written": batches_written,
                        "last_batch_relpath": rel.replace("\\", "/"),
                    }
                )
                write_state(st)

    if batch:
        batches_written += 1
        n_words = len(batch)
        out_path = _TDK_INC_DIR / f"tdk_batch_{batches_written:05d}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_entries_to_markdown(batch, batches_written), encoding="utf-8")
        info = build_index(force=False, incremental=True)
        rel = f"tdk/incremental/{out_path.name}"
        print(
            f"{n_words} kelime başarıyla vektör hafızasına eklendi "
            f"(paket {batches_written:05d}, dosya: {rel}). İndeks: {info}"
        )
        st.update(
            {
                "file_line_offset": last_consumed,
                "lines_ingested": lines_ingested,
                "batches_written": batches_written,
                "last_batch_relpath": rel.replace("\\", "/"),
            }
        )
        write_state(st)
    elif last_consumed > skip_lines:
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
    print(
        f"OK: ingest turu bitti. Kaynak satır imi: {int(st.get('file_line_offset') or 0)}, "
        f"indekslenen madde: {lines_ingested}, paket: {batches_written}. "
        f"Bitirmek için: finalize"
    )


def cmd_finalize() -> None:
    st = read_state()
    if st.get("status") != "in_progress":
        raise SystemExit("Önce init + ingest ile in_progress durumuna gelin.")
    if int(st.get("lines_ingested") or 0) <= 0:
        raise SystemExit("Henüz indekslenecek TDK maddesi yok (ingest çalıştırılmamış olabilir).")
    # Son tutarlılık: incremental bir tur daha (çoğunlukla no-op).
    info = build_index(force=False, incremental=True)
    st.update(
        {
            "status": "complete",
            "exclusive_tdk": False,
            "completed_at": _utc_now_iso(),
            "finalize_index": info,
        }
    )
    write_state(st)
    print(_COMPLETION_MSG)
    print(f"Detay: {json.dumps(info, ensure_ascii=False)}")


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
    inc = _KNOWLEDGE_ROOT / "tdk" / "incremental"
    if inc.is_dir():
        for p in sorted(inc.glob("tdk_batch_*.md")):
            try:
                p.unlink()
            except OSError:
                pass
    print("OK: protokol kaydı ve tdk/incremental/tdk_batch_*.md temizlendi.")
    if st:
        print("Not: vektör indeksi (.rag_index) duruyor; tam sıfırlamak için `ingest_cli --force` gerekir.")


def main() -> None:
    p = argparse.ArgumentParser(description="TDK — kademeli vektör indeksleme protokolü")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Protokolü başlat ve TDK çıktı klasörünü hazırla")
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
