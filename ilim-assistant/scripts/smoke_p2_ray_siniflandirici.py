# -*- coding: utf-8 -*-
"""P2 smoke — niyet → ray sınıflayıcı."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CASES: list[tuple[str, str, str]] = [
    # goal, expected_ray, expected_path_hint
    ("yeni proje fastapi oluştur health ile", "scaffold", "faz85_fast"),
    ("sıfırdan site yap", "scaffold", "faz85_fast"),
    ("health endpointine version 2.0.0 ekle pytest geçir", "faz85_fast", "faz85_fast"),
    ("pytest geçir", "faz85_fast", "faz85_fast"),
    ("eksik import düzelt greet", "agent_boot", "agent"),
    ("uptime alanı ekle", "agent_boot", "agent"),
    ("ping endpoint ekle", "agent_boot", "agent"),
    ("app/util.py ve app/service.py düzelt VERSION", "agent_multi", "agent_multi"),
    ("şu projede app/main.py ve app/api.py refactor et", "agent_multi", "agent_multi"),
    ("projects/foo mega refactor 10+ dosya", "agent_mega", "agent_mega"),
    ("nasılsın bugün", "agent_boot", "agent"),
]


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.motorlar.programlama_ray_siniflandirici import (
        RAY_CLASSIFIER_VERSION,
        classify_programlama_ray,
        path_hint_for_goal,
    )
    from ilim_assistant.motorlar.programlama_yuzey_bridge import _path_hint_for_goal

    failed = 0
    failed += _ok("p2-v1" in RAY_CLASSIFIER_VERSION, f"version {RAY_CLASSIFIER_VERSION}")

    for goal, exp_ray, exp_hint in CASES:
        d = classify_programlama_ray(goal)
        ok_r = d.ray == exp_ray
        ok_h = d.path_hint == exp_hint
        failed += _ok(
            ok_r and ok_h,
            f"{goal[:48]!r} → ray={d.ray!r}(exp {exp_ray}) hint={d.path_hint!r}(exp {exp_hint}) reason={d.reason}",
        )
        # bridge uyumu
        br = _path_hint_for_goal(goal)
        failed += _ok(br == exp_hint, f"bridge hint {goal[:32]!r} → {br!r}")

    # path_hint_for_goal alias
    failed += _ok(
        path_hint_for_goal("ping endpoint ekle") == "agent",
        "alias path_hint_for_goal ping",
    )

    # scaffold use_faz85
    sc = classify_programlama_ray("web sitesi scaffold kur")
    failed += _ok(sc.use_faz85 and not sc.use_supervised_boot, "scaffold flags")

    mega = classify_programlama_ray("mega refactor 10+ dosya")
    failed += _ok(mega.use_supervised_boot and mega.ray == "agent_mega", "mega flags")

    total_checks = 1 + len(CASES) * 2 + 3
    passed = total_checks - failed
    print(f"result: {passed}/{total_checks} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
