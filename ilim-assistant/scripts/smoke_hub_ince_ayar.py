# -*- coding: utf-8 -*-
"""Hub ince ayar — bilgi/görüş Ana Motor'da; gerçek video/mimar işi motorlarda."""
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
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import (
        is_video_workflow_request,
        resolve_hub_target,
    )

    stay = [
        "Ses nedir anlat biraz",
        "Profil fotoğrafı nedir",
        "Video nedir kısaca",
        "Yapay zeka hakkında ne düşünüyorsun?",
        "Fotosentezi anlatır mısın",
        "Galaksi nedir",
    ]
    for q in stay:
        mid, meta = resolve_hub_target(q, {})
        failed += _ok(mid == "genel", f"stay genel: {q[:36]} → {mid}/{meta.get('reason')}")
        failed += _ok(
            not is_video_workflow_request(q),
            f"video workflow yok: {q[:36]}",
        )

    go_video = [
        "şu videoyu indir",
        "videoyu kes 0:30-1:00",
        "ffmpeg ile dönüştür",
    ]
    for q in go_video:
        failed += _ok(
            is_video_workflow_request(q) or resolve_hub_target(q, {})[0] == "video",
            f"video işi: {q}",
        )

    mid_m, meta_m = resolve_hub_target("fotoğraf paneli aç", {})
    failed += _ok(
        mid_m == "mimar" or meta_m.get("reason") == "kabiliyet_registry",
        f"mimar panel: {mid_m}/{meta_m.get('reason')}",
    )

    from ilim_assistant.motorlar.ses_faz72 import classify_ses_intent

    ses = classify_ses_intent("asistan moduna geç", mode_norm="ses")
    failed += _ok(ses.get("reason") == "set_profile", "ses açık geçiş korunur")

    total = len(stay) * 2 + len(go_video) + 2
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
