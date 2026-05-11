"""
tdk_kaynak.json (bilalozdemir/tr-word-list biçimi: [{"word","meanings"}, ...])
-> tdk_incremental_protocol ingest için UTF-8 TAB ayrımlı satırlar.

Kaynak: https://github.com/bilalozdemir/tr-word-list (CC BY-SA 4.0)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ilim_assistant.rag_store import _KNOWLEDGE_ROOT

_DEFAULT_IN = _KNOWLEDGE_ROOT / "tdk" / "tdk_kaynak.json"
_DEFAULT_OUT = _KNOWLEDGE_ROOT / "tdk" / "tdk_protocol_source.txt"


def _norm(s: str) -> str:
    return " ".join((s or "").replace("\t", " ").replace("\r", " ").split())


def convert(*, src: Path, dst: Path) -> int:
    raw = src.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise SystemExit("Beklenen biçim: kök JSON dizisi [{word, meanings}, ...]")
    lines: list[str] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        w = item.get("word") or item.get("kelime")
        if w is None:
            continue
        lemma = _norm(str(w))
        if not lemma:
            continue
        meanings = item.get("meanings") or []
        if isinstance(meanings, list) and meanings:
            gloss = " | ".join(_norm(str(m)) for m in meanings if m is not None and _norm(str(m)))
        else:
            gloss = "(Anlam listesi boş)"
        if not gloss:
            gloss = "(Anlam listesi boş)"
        lines.append(f"{lemma}\t{gloss}\n")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("".join(lines), encoding="utf-8")
    return len(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="tdk_kaynak.json -> TAB ingest kaynağı")
    p.add_argument("--input", type=str, default=str(_DEFAULT_IN))
    p.add_argument("--output", type=str, default=str(_DEFAULT_OUT))
    args = p.parse_args()
    src, dst = Path(args.input), Path(args.output)
    if not src.is_file():
        raise SystemExit(f"Girdi yok: {src}")
    n = convert(src=src, dst=dst)
    print(f"OK: {n} satır yazıldı -> {dst}")


if __name__ == "__main__":
    main()
