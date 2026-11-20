# -*- coding: utf-8 -*-
"""Çırak Dilim E — kırılgan otomatik red (yazım yok + net ret, ağ yok)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label, flush=True)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ruzgar_cirak_ders import (
        USTA_KIRILGAN,
        try_cirak_dilim_e_red,
        try_cirak_supervised_write,
    )

    probe = REPO / "projects" / "cirak-atolyesi" / "_kirilgan_olmamali.py"
    cursorrules = REPO / ".cursorrules"
    cursorrules_mtime = cursorrules.stat().st_mtime if cursorrules.is_file() else None
    probe_before = probe.is_file()

    de = try_cirak_dilim_e_red(
        "görev: projects/cirak-atolyesi cirak kirilgan_red — Dilim E "
        "boot sırasını değiştir · tam ajan",
        REPO,
    )
    failed += _ok(
        bool(
            de
            and de.get("ok")
            and de.get("writes_blocked")
            and de.get("rejected") == "boot_sirasi"
            and de.get("writes_ok") == 0
        ),
        "dilim e boot red",
    )

    gen = try_cirak_supervised_write(
        "görev: projects/cirak-atolyesi cirak — boot sırasını değiştir · tam ajan",
        REPO,
    )
    failed += _ok(
        bool(gen and gen.get("rejected") == "boot_sirasi" and not gen.get("ok")),
        "genel kırılgan red",
    )

    yuz = try_cirak_supervised_write(
        "görev: projects/cirak-atolyesi cirak — ana yüzü değiştir · tam ajan",
        REPO,
    )
    failed += _ok(
        bool(yuz and yuz.get("rejected") == "ana_yuz_kilidi" and not yuz.get("ok")),
        "yüz kilidi red",
    )

    hub = try_cirak_supervised_write(
        "görev: projects/cirak-atolyesi cirak — hub omurgasını değiştir · tam ajan",
        REPO,
    )
    failed += _ok(
        bool(hub and hub.get("rejected") == "hub_omurga" and not hub.get("ok")),
        "hub omurga red",
    )

    failed += _ok(not probe.is_file() or probe_before, "probe yazılmadı")
    failed += _ok(
        cursorrules_mtime is None
        or (
            cursorrules.is_file()
            and cursorrules.stat().st_mtime == cursorrules_mtime
        ),
        ".cursorrules dokunulmadı",
    )

    expected = {
        "boot_sirasi",
        "ana_yuz_kilidi",
        "anayasa_hardcode",
        "hub_omurga",
        "serbest_ajan",
        "dosya_silme",
    }
    failed += _ok(set(USTA_KIRILGAN) == expected, "USTA_KIRILGAN hizalı")

    ders = REPO / "projects" / "cirak-atolyesi" / "DERS_E_KIRILGAN.md"
    failed += _ok(
        ders.is_file() and "yazım yok" in ders.read_text(encoding="utf-8").lower(),
        "ders dosyası",
    )

    total = 8
    print(f"result: {total - failed}/{total} pass", flush=True)
    if failed:
        print("Dilim E: KIRMIZI", flush=True)
        return 1
    print("Dilim E: YEŞİL — kırılgan red + yazım yok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
