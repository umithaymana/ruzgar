# -*- coding: utf-8 -*-
"""V1 smoke — STT/TTS ısınma kapısı (boot geciktirmez; dry_run)."""
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
    from ilim_assistant.ses_v1_isinma import (
        V1_VERSION,
        last_warmup_status,
        run_ses_v1_warmup,
        ses_v1_warmup_enabled,
    )

    failed = 0
    failed += _ok("v1-isinma" in V1_VERSION, f"ver {V1_VERSION}")
    failed += _ok(ses_v1_warmup_enabled(), "warmup varsayılan açık")

    dry = run_ses_v1_warmup(dry_run=True)
    failed += _ok(dry.get("dry_run") is True, "dry_run")
    failed += _ok(dry.get("version") == V1_VERSION, "dry version")
    failed += _ok(last_warmup_status().get("dry_run") is True, "last status")

    # desktop_server kancası — boot sırasını bozmadan warmup çağrısı var mı?
    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    failed += _ok("run_ses_v1_warmup" in ds, "desktop_server kanca")
    failed += _ok("_sync_startup_warmups" in ds, "warmup bloğu")
    # Kanca, _boot_motorlar_anaonce tanımından sonra gelmeli (metin sırası)
    i_boot = ds.find("def _boot_motorlar_anaonce")
    i_warm = ds.find("run_ses_v1_warmup")
    failed += _ok(i_boot > 0 and i_warm > i_boot, "kanca boot tanımından sonra")

    # Manifest: ana motor hâlâ ilk import
    failed += _ok(
        'importlib.import_module("ilim_assistant.main_engine")' in ds, "ana motor ilk"
    )

    total = 9
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
