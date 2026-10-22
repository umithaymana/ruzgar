# -*- coding: utf-8 -*-
"""P1 smoke — supervised pattern kütüphanesi (version/health/import/dict/ping)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_SERVICE_NO_IMPORT = '''"""service — eksik greet import."""
from app.util import VERSION

def health_payload() -> dict[str, str]:
    return {"ok": "true", "service": "demo", "msg": greet("ruzgar")}
'''

_SERVICE_DICT = '''"""service — dict field adayı."""
from app.util import VERSION, greet

def health_payload() -> dict[str, str]:
    return {"ok": "true", "service": "demo", "msg": greet("ruzgar")}
'''

_MAIN_PING = '''"""main — ping yok."""
from fastapi import FastAPI
from app.service import health_payload

app = FastAPI()

@app.get("/health")
def health():
    return health_payload()
'''

_UTIL = '''VERSION = "2.0.0"

def greet(name: str) -> str:
    return f"selam {name}"
'''

_UTIL_BROKEN = '''VERSION = "1.0.0-broken"

def greet(name: str) -> str:
    return f"selam {name}"
'''

_SERVICE_VERSION = '''from app.util import VERSION, greet

def health_payload() -> dict[str, str]:
    return {"ok": "true", "service": "demo", "msg": greet("ruzgar")}
'''


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.motorlar.programlama_faz103_e2 import (
        e2_write_template_nudge,
        try_e2_supervised_write_boot,
    )
    from ilim_assistant.motorlar.programlama_supervised_patterns import (
        P1_PATTERNS_VERSION,
        list_pattern_ids,
        pattern_nudge_hints,
        try_supervised_pattern_library,
    )

    failed = 0
    ids = list_pattern_ids()
    failed += _ok(
        ids == ["e2_version", "health_fields", "import_fix", "dict_field", "ping_route"],
        f"pattern sırası {ids}",
    )
    failed += _ok("p1-v1" in P1_PATTERNS_VERSION, f"version {P1_PATTERNS_VERSION}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        scope = "projects/p1-demo"
        app = root / "projects" / "p1-demo" / "app"
        app.mkdir(parents=True)
        (app / "__init__.py").write_text("", encoding="utf-8")

        # 1) import_fix
        (app / "util.py").write_text(_UTIL, encoding="utf-8")
        (app / "service.py").write_text(_SERVICE_NO_IMPORT, encoding="utf-8")
        (app / "main.py").write_text(_MAIN_PING, encoding="utf-8")
        hit = try_supervised_pattern_library(
            root, scope, "eksik import düzelt greet", pattern_ids=["import_fix"]
        )
        txt = (app / "service.py").read_text(encoding="utf-8")
        failed += _ok(
            bool(hit.get("writes_ok")) and "greet" in txt and "from app.util import" in txt,
            f"import_fix detail={hit.get('detail')!r}",
        )

        # 2) dict_field
        (app / "service.py").write_text(_SERVICE_DICT, encoding="utf-8")
        hit = try_supervised_pattern_library(
            root, scope, "uptime alanı ekle", pattern_ids=["dict_field"]
        )
        txt = (app / "service.py").read_text(encoding="utf-8")
        failed += _ok(
            bool(hit.get("writes_ok")) and '"uptime"' in txt,
            f"dict_field detail={hit.get('detail')!r}",
        )

        # 3) ping_route
        (app / "main.py").write_text(_MAIN_PING, encoding="utf-8")
        hit = try_supervised_pattern_library(
            root, scope, "ping endpoint ekle", pattern_ids=["ping_route"]
        )
        txt = (app / "main.py").read_text(encoding="utf-8")
        failed += _ok(
            bool(hit.get("writes_ok")) and "/ping" in txt,
            f"ping_route detail={hit.get('detail')!r}",
        )

        # 4) e2_version via unified boot
        (app / "util.py").write_text(_UTIL_BROKEN, encoding="utf-8")
        (app / "service.py").write_text(_SERVICE_VERSION, encoding="utf-8")
        goal_v = (
            "app/util.py ve app/service.py duzelt. "
            'VERSION = "2.0.0" yaz; health_payload version ekle'
        )
        boot = try_e2_supervised_write_boot(root, scope, goal_v)
        util_txt = (app / "util.py").read_text(encoding="utf-8")
        failed += _ok(
            bool(boot.get("writes_ok")) and 'VERSION = "2.0.0"' in util_txt,
            f"unified e2_version source={boot.get('source')!r} detail={boot.get('detail')!r}",
        )

        # 5) nudge hints
        nudge = e2_write_template_nudge(scope, "uptime alanı ekle")
        hints = pattern_nudge_hints(scope, "ping endpoint ekle")
        failed += _ok("dict_field" in nudge or "uptime" in nudge.lower(), "nudge dict")
        failed += _ok("ping" in hints.lower(), "hint ping")

    # health regression (ayrı temp — sample main)
    with tempfile.TemporaryDirectory() as td2:
        root2 = Path(td2)
        proj = root2 / "projects" / "health"
        (proj / "app").mkdir(parents=True)
        (proj / "app" / "__init__.py").write_text("", encoding="utf-8")
        sample = (
            '"""FastAPI — health"""\n'
            "from fastapi import FastAPI\n"
            'app = FastAPI(title="health")\n\n'
            '@app.get("/health")\n'
            "def health() -> dict[str, str]:\n"
            '    return {"ok": "true", "service": "health", "version": "2.1.0"}\n'
        )
        (proj / "app" / "main.py").write_text(sample, encoding="utf-8")
        boot_h = try_e2_supervised_write_boot(
            root2, "projects/health", "health endpointine status alanı ekle pytest geçir"
        )
        main_txt = (proj / "app" / "main.py").read_text(encoding="utf-8")
        failed += _ok(
            bool(boot_h.get("writes_ok")) and '"status"' in main_txt,
            f"health regression source={boot_h.get('source')!r}",
        )

    total = 9
    passed = total - failed
    print(f"result: {passed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
