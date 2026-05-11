"""Bilgi indeksini oluştur: python -m ilim_assistant.ingest_cli"""

from __future__ import annotations

import argparse

from ilim_assistant.rag_store import _KNOWLEDGE_ROOT, build_index
from ilim_assistant.tdk_incremental_protocol import protocol_lock_active


def main():
    p = argparse.ArgumentParser(description="İlim bilgi indeksi oluştur")
    p.add_argument("--force", action="store_true", help="Önbelleği yeniden oluştur")
    p.add_argument(
        "--incremental",
        action="store_true",
        help="Sadece değişen/eklenen md dosyalarının chunk'larını yeniden gömmeye çalış (kademeli yükleme).",
    )
    p.add_argument(
        "--allow-other-knowledge",
        action="store_true",
        help="TDK kademeli protokolü (exclusive) aktifken bile genel indekslemeye izin ver.",
    )
    p.add_argument("--knowledge", default=str(_KNOWLEDGE_ROOT), type=str)
    args = p.parse_args()
    if protocol_lock_active() and not args.allow_other_knowledge:
        raise SystemExit(
            "TDK kademeli yükleme kilidi aktif (tdk_incremental_protocol in_progress). "
            "Genel indekslemeyi ertelemek veya zorunluysa: "
            "`python -m ilim_assistant.ingest_cli ... --allow-other-knowledge`"
        )
    r = build_index(
        knowledge_root=args.knowledge,
        force=args.force,
        incremental=bool(args.incremental),
    )
    print(r)


if __name__ == "__main__":
    main()
