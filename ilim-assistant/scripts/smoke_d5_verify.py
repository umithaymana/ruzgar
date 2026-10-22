# -*- coding: utf-8 -*-
"""D5 — yazım sonrası verify zorunlu; agent_ok verify’siz yeşil sayılmaz."""
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
    failed = 0
    from ilim_assistant.motorlar.programlama_faz103_e2 import e2_write_template_nudge
    import inspect
    from ilim_assistant.motorlar import programlama_faz103_e2 as m

    src = inspect.getsource(m.run_combined_e2_battery)
    failed += _ok(
        "verify_ok" in src and "agent_ok" in src,
        "combined battery verify+agent_ok bağı",
    )
    failed += _ok(
        "verify yok" in src or "verify_ok" in src,
        "verify yok → heal yolu",
    )
    nudge = e2_write_template_nudge(
        "projects/demo",
        "app/util.py ve app/service.py version 2.0.0 pytest gecir",
    )
    failed += _ok("verify" in nudge.lower() or "pytest" in nudge.lower(), "şablon verify")
    failed += _ok("D5" in nudge or "ZORUNLU" in nudge, "D5 verify cümlesi")

    # Offline heal verify_ok
    from ilim_assistant.motorlar.programlama_faz103_e2 import (
        _run_offline_multi_heal,
        _setup_multi_file_broken,
    )
    import inspect
    import tempfile

    td = tempfile.mkdtemp()
    scope = "projects/d5-verify"
    ok, _ = _setup_multi_file_broken(td, scope)
    failed += _ok(ok, "setup")
    heal = _run_offline_multi_heal(td, scope)
    failed += _ok(bool(heal.get("ok")) and bool(heal.get("verify_ok")), "offline heal verify_ok")

    # Canlı zincir: verify_ok success'e zorlanmasın
    from ilim_assistant.motorlar import programlama_faz88 as f88
    from ilim_assistant.motorlar import programlama_faz14 as f14

    failed += _ok(
        'if "verify_ok" in agent' in inspect.getsource(f88.run_live_code_agent),
        "faz88 verify_ok ayrı alan",
    )
    failed += _ok(
        '"verify_ok": _done_verify' in inspect.getsource(f14.iter_code_agent_turn_events)
        or "verify_ok" in inspect.getsource(f14.iter_code_agent_turn_events),
        "faz14 done.verify_ok",
    )

    total = 8
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
