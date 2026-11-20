# Created by Ümit & Gökçenur
"""Madde 6 — arsiv/ dürüst bağ: disk ince arama; ana indeks yutma yok."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, name: str) -> int:
    print(("OK" if cond else "FAIL") + " - " + name)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.rag_store import (
        arsiv_search_status,
        search_arsiv,
        search_arsiv_disk,
        _source_is_archive,
    )
    from ilim_assistant.main_engine import STATUS_ILIM_SCAN, STATUS_FULL_INDEX

    failed = 0
    st = arsiv_search_status()
    failed += _ok(st.get("vector_in_main_index", -1) == 0, "vector arsiv=0")
    failed += _ok(bool(st.get("disk_search_enabled")), "disk search on")
    failed += _ok(st.get("mode") == "disk_keyword", "mode disk_keyword")
    failed += _ok("ana RAG" in (st.get("hint") or "") or "indeksinde değil" in (st.get("hint") or ""), "honest hint")

    failed += _ok(_source_is_archive("arsiv/Hadis_Kulliyati/x.md"), "source flag")
    failed += _ok(not _source_is_archive("learned/x.md"), "not archive learned")

    failed += _ok("vektör" in STATUS_ILIM_SCAN.lower() or "disk" in STATUS_ILIM_SCAN.lower(), "status honest")
    failed += _ok("arşiv birlikte" not in STATUS_FULL_INDEX.lower(), "full index no lie")

    from ilim_assistant.rag_store import arsiv_disk_last_meta

    hits = search_arsiv_disk("mektubat", top_k=3)
    meta1 = arsiv_disk_last_meta()
    # klasörde mektubat varsa hit; yoksa boş da kabul (ortam)
    if hits:
        failed += _ok(all(_source_is_archive(h[1]) for h in hits), "disk hits arsiv path")
        failed += _ok(all(float(h[2]) >= 0.18 for h in hits), "disk score floor")
    else:
        # en azından fonksiyon çökmesin
        failed += _ok(isinstance(hits, list), "disk empty list ok")

    # İkinci çağrı — dosya listesi önbellek
    _ = search_arsiv_disk("mektubat", top_k=3)
    meta2 = arsiv_disk_last_meta()
    failed += _ok(bool(meta2.get("cache_hit")), "arsiv file list cache hit")
    failed += _ok("scanned" in meta1 and "cap" in meta1, "disk meta scanned/cap")

    # search_arsiv birleşik API
    h2 = search_arsiv("kuran", top_k=2)
    failed += _ok(isinstance(h2, list), "search_arsiv list")

    print("status_sample:", {k: st.get(k) for k in ("vector_in_main_index", "disk_md_approx", "mode", "arsiv_root")})
    print("disk_mektubat_hits:", len(hits), "kuran_hits:", len(h2), "cache:", meta2.get("cache_hit"))
    print("result:", "FAIL" if failed else "pass", f"({failed} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
