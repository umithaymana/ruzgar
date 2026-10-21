#!/usr/bin/env python3
"""Smoke — #4 E2 kararlılık: agent_ok KPI + çıplak VERSION patch kurtarma."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz103_e2 import (
        compute_e2_stats,
        format_e2_battery_report,
    )
    from ilim_assistant.motorlar.programlama_patch import (
        extract_patch_jobs,
        normalize_bare_e2_version_patches,
        apply_patch_jobs,
    )
    from ilim_assistant.motorlar.programlama_faz103_e2 import _setup_multi_file_broken

    fails: list[str] = []

    bare = (
        "util dosyasını değiştireceğim: `projects/demo/app/util.py`\n\n"
        "```search-replace\n"
        "<<<SEARCH\n"
        'VERSION = "1.0.0-broken"\n'
        "===\n"
        'VERSION = "2.0.0"\n'
        ">>>REPLACE\n"
        "```\n"
    )
    fixed = normalize_bare_e2_version_patches(bare)
    if "@@patch projects/demo/app/util.py" not in fixed:
        fails.append("bare normalize missing @@patch")
    jobs = extract_patch_jobs(bare)
    if not any(j[0].endswith("app/util.py") and "2.0.0" in j[2] for j in jobs):
        fails.append(f"extract missed bare version jobs={jobs!r}")

    with tempfile.TemporaryDirectory() as td:
        scope = "projects/e2-bare"
        ok_s, msg = _setup_multi_file_broken(td, scope)
        if not ok_s:
            fails.append(f"setup {msg}")
        else:
            body = (
                f"`{scope}/app/util.py`\n\n"
                "```search-replace\n"
                "<<<SEARCH\n"
                'VERSION = "1.0.0-broken"\n'
                "===\n"
                'VERSION = "2.0.0"\n'
                ">>>REPLACE\n"
                "```\n"
            )
            reps = apply_patch_jobs(body, td)
            util = Path(td) / "projects" / "e2-bare" / "app" / "util.py"
            txt = util.read_text(encoding="utf-8") if util.is_file() else ""
            if 'VERSION = "2.0.0"' not in txt:
                fails.append(f"disk bare apply failed {reps!r}")

    # KPI alanları (boş olsa da anahtarlar)
    st = compute_e2_stats(ROOT.parent, window_days=30)
    for key in (
        "agent_ok_rate",
        "agent_ok_count",
        "heal_share",
        "heal_fallback_count",
        "live_total",
    ):
        if key not in st:
            fails.append(f"stats missing {key}")

    fake_report = {
        "ok": True,
        "offline_battery": {
            "ok": True,
            "success_count": 5,
            "total": 5,
            "success_rate": 1.0,
            "target_rate": 0.9,
            "meets_target_90": True,
            "scenarios": [],
        },
        "e2_stats": st,
    }
    txt_rep = format_e2_battery_report(fake_report)
    if int(st.get("live_total") or 0) > 0 and "Canlı ajan" not in txt_rep:
        fails.append("report missing Canlı ajan line")

    if fails:
        for f in fails:
            print(f"FAIL {f}")
        return 1
    print(
        "PASS programlama_e2_kararlilik_smoke "
        f"agent_ok_rate={st.get('agent_ok_rate')} heal_share={st.get('heal_share')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
