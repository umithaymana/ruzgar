"""Bilgi indeksini oluştur: python -m ilim_assistant.ingest_cli"""

from __future__ import annotations

import argparse

from ilim_assistant.rag_store import _KNOWLEDGE_ROOT, build_index


def main():
    p = argparse.ArgumentParser(description="İlim bilgi indeksi oluştur")
    p.add_argument("--force", action="store_true", help="Önbelleği yeniden oluştur")
    p.add_argument("--knowledge", default=str(_KNOWLEDGE_ROOT), type=str)
    args = p.parse_args()
    r = build_index(knowledge_root=args.knowledge, force=args.force)
    print(r)


if __name__ == "__main__":
    main()
