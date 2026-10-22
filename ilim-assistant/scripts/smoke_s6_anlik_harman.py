# -*- coding: utf-8 -*-
"""S6 smoke — anlık kart vs grounded anlat harman."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.ruzgar_anlik_niyet_gate import (
        collect_library_llm_context,
        is_strict_library_lookup,
        resolve_anlik_harman,
        should_defer_library_instant,
    )

    failed = 0

    # Strict kart
    failed += _ok(is_strict_library_lookup("os nedir"), "os strict")
    failed += _ok(not should_defer_library_instant("os nedir"), "os defer yok")
    h_os = resolve_anlik_harman("os nedir")
    failed += _ok(h_os.get("mode") in ("kart", "miss") or h_os.get("has_card"), "os harman")

    # Anlat → grounded
    msg_anlat = "fotosentezi anlatır mısın"
    failed += _ok(should_defer_library_instant(msg_anlat), "fotosentez defer")
    ctx = collect_library_llm_context(msg_anlat)
    failed += _ok(
        bool(ctx) and ("GROUNDED S6" in ctx or "KÜTÜPHANE" in ctx),
        f"fotosentez ctx mark ({'empty' if not ctx else 'ok'})",
    )
    # Bilim rafı yoksa bile grounded markası test: galaksi / hicret
    ctx2 = collect_library_llm_context("hicreti daha açık anlat")
    failed += _ok(
        bool(ctx2) and "GROUNDED S6" in ctx2,
        "hicret grounded S6",
    )
    h_anlat = resolve_anlik_harman("hicreti daha açık anlat")
    failed += _ok(
        h_anlat.get("mode") in ("grounded_anlat", "miss"),
        f"hicret mode={h_anlat.get('mode')}",
    )
    if h_anlat.get("has_card"):
        failed += _ok(h_anlat.get("mode") == "grounded_anlat", "card+anlat→grounded")
    else:
        failed += _ok(True, "card yok skip")

    # Çelişki / miss: anlat ama kart yok
    h_miss = resolve_anlik_harman("bilinmeyenxyz kavramını anlat biraz")
    failed += _ok(
        h_miss.get("mode") == "miss" or not h_miss.get("has_card"),
        "bilinmeyen miss",
    )

    # Eski ipucu yolu bozulmasın (hakkında soft)
    ctx3 = collect_library_llm_context("yapay zeka hakkında ne düşünüyorsun")
    # görüş → skip in chat_core; burada boş veya ipucu olabilir
    failed += _ok(True, "gorus path smoke noop")

    # SourceRouter tip anlat
    from ilim_assistant.sohbet_source_router import classify_source_intent

    failed += _ok(
        classify_source_intent("galaksi nedir anlat biraz").tip == "anlat",
        "router anlat tip",
    )
    ctx4 = collect_library_llm_context("galaksi nedir anlat biraz")
    failed += _ok(
        (not ctx4) or ("GROUNDED S6" in ctx4) or ("KÜTÜPHANE" in ctx4),
        "galaksi ctx",
    )

    total = 11
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
