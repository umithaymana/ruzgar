# -*- coding: utf-8 -*-
"""Smoke — tur bütçesi tek kaynak; ikinci begin sıfırlamaz; truncate→öğrenme red."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ruzgar_umed_cevap_emri import (
        begin_turn_budget,
        clear_turn_budget_state,
        ensure_turn_budget,
        get_turn_budget_sec,
        get_turn_deadline,
        is_answer_truncated,
        mark_answer_truncated,
        remaining_sec,
        resolve_active_budget_sec,
    )
    from ilim_assistant.ruzgar_tur_teshis_f0 import MISS_TIMEOUT, classify_miss
    from ilim_assistant.ruzgar_umed_kurallari import MISS_PHRASE
    from ilim_assistant.ruzgar_otomatik_ogrenme import auto_learn_from_turn

    clear_turn_budget_state()
    b1 = begin_turn_budget("Osmanlı nedir?", mode_norm="genel", force=True)
    d1 = get_turn_deadline()
    failed += _ok(b1 > 0 and get_turn_budget_sec() == b1, "begin budget saklandı")
    time.sleep(0.05)
    rem1 = remaining_sec()
    b2 = ensure_turn_budget("Osmanlı nedir?", mode_norm="genel")
    d2 = get_turn_deadline()
    rem2 = remaining_sec()
    failed += _ok(b2 == b1, "ensure aynı budget")
    failed += _ok(d2 == d1, "ensure deadline sıfırlamaz")
    failed += _ok(abs(rem2 - rem1) < 0.2, "ensure remaining korunur")
    failed += _ok(
        resolve_active_budget_sec("başka soru") == b1,
        "resolve_active ContextVar kullanır",
    )

    # classify orch.budget_sec öncelikli (boş mesaj 15 sn tuzağı yok)
    mc = classify_miss(
        reply=MISS_PHRASE,
        orch={"hits_count": 0, "budget_sec": b1},
        hits_count=0,
        elapsed_sec=float(b1) + 1.0,
        egitim_miss=True,
    )
    failed += _ok(mc == MISS_TIMEOUT, f"classify orch budget ({mc})")

    mark_answer_truncated(True)
    failed += _ok(is_answer_truncated(), "truncated bayrağı")
    meta = auto_learn_from_turn(
        "Osmanlı nedir?",
        "Yarım cevap örneği " * 20,
        plan_primary="bilgi",
    )
    failed += _ok(
        meta.get("saved") is False and meta.get("skipped") == "answer_truncated",
        "truncate öğrenme reddi",
    )

    clear_turn_budget_state()
    failed += _ok(get_turn_deadline() is None and not is_answer_truncated(), "clear state")

    # Masa full yanıt alanı
    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    failed += _ok('"masa": done_event.get("masa")' in ds, "chat/full masa alanı")
    failed += _ok("ensure_turn_budget" in (ROOT / "ilim_assistant" / "llm_brain.py").read_text(encoding="utf-8"), "llm ensure_turn_budget")
    failed += _ok("index_knowledge_files" in (ROOT / "ilim_assistant" / "tarih_incremental_protocol.py").read_text(encoding="utf-8"), "tarih upsert ince")
    failed += _ok("index_knowledge_files" in (ROOT / "ilim_assistant" / "tdk_incremental_protocol.py").read_text(encoding="utf-8"), "tdk upsert ince")
    failed += _ok("index_knowledge_files" in (ROOT / "ilim_assistant" / "nebula_kitap_hafiza.py").read_text(encoding="utf-8"), "nebula_kitap upsert ince")

    total = 14
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
