# -*- coding: utf-8 -*-
"""P5 smoke — scaffold ürün borusu (static / react / fastapi / cli)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CASES = [
    ("sıfırdan statik site yap adı: vitrin-p5", "static_site"),
    ("react vite panel oluştur adı: panel-p5", "react_vite"),
    ("yeni fastapi api oluştur adı: api-p5", "fastapi_api"),
    ("python cli aracı oluştur adı: cli-p5", "cli_python"),
]


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.motorlar.programlama_p5_scaffold_boru import (
        P5_VERSION,
        choose_product_template,
        run_product_scaffold_pipe,
        try_p5_fast_scaffold,
    )
    from ilim_assistant.motorlar.programlama_faz85 import try_fast_deterministic_task

    failed = 0
    failed += _ok("p5-scaffold" in P5_VERSION, f"version {P5_VERSION}")

    for goal, exp in CASES:
        got = choose_product_template(goal)
        failed += _ok(got == exp, f"choose {exp!r} ← {goal[:40]!r} got={got!r}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "projects").mkdir(parents=True)

        for goal, exp in CASES:
            slug = exp.replace("_", "-") + "-pipe"
            hit = run_product_scaffold_pipe(
                root, goal=goal, project_name=slug, template_id=exp
            )
            failed += _ok(
                bool(hit.get("writes_ok")) and hit.get("template_id") == exp,
                f"pipe {exp} writes={hit.get('writes_ok')} detail={hit.get('detail')!r}",
            )
            failed += _ok(
                bool(hit.get("verify_ok")),
                f"verify {exp} ok={hit.get('verify_ok')} detail={hit.get('detail')!r}",
            )

        # fast path handler
        hit2 = try_p5_fast_scaffold(
            root, "projects/ghost", "sıfırdan site yap adı: ghost-site"
        )
        failed += _ok(
            hit2 is not None and bool(hit2.get("writes_ok")),
            f"fast scaffold handler {hit2 and hit2.get('detail')}",
        )

        # faz85 birleşik (başka slug)
        fast = try_fast_deterministic_task(
            root,
            "projects/yeni-vitrin",
            "sıfırdan statik site yap",
            allow_agent_fallback=False,
        )
        failed += _ok(
            fast is not None and int(fast.get("writes_ok") or 0) > 0,
            f"faz85 fast site source={fast and fast.get('source')}",
        )

    # 1 ver + 4 choose + 4 pipe + 4 verify + 1 handler + 1 faz85 = 15
    total = 15
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
