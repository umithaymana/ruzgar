# -*- coding: utf-8 -*-
"""P2 doğal sohbet — use_web=false iken web/güven gürültüsü."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("RUZGAR_DOGAL_SOHBET", "1")


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    from ilim_assistant.ana_motor_kaynak import citation_directive_for_turn
    from ilim_assistant.ruzgar_dogal_sohbet_faz91 import (
        is_natural_conversation_turn,
        payload_indicates_web_used,
        should_suppress_trust_noise,
    )

    failed += _ok(
        should_suppress_trust_noise(
            "hicreti daha açık anlat",
            "genel",
            None,
            use_web=False,
            web_present=False,
            source_count=0,
        ),
        "anlat → suppress trust noise",
    )
    failed += _ok(
        should_suppress_trust_noise(
            "selam nasılsın",
            "genel",
            None,
            use_web=False,
            web_present=False,
            source_count=0,
        )
        or is_natural_conversation_turn("selam nasılsın", "genel", None),
        "sohbet → soft path",
    )
    failed += _ok(
        should_suppress_trust_noise(
            "rastgele konu",
            "genel",
            None,
            use_web=False,
            web_present=False,
            source_count=0,
        ),
        "use_web=false + kaynaksız → suppress",
    )
    failed += _ok(
        (not should_suppress_trust_noise(
            "osmanli nedir",
            "genel",
            None,
            use_web=False,
            web_present=False,
            source_count=3,
        ))
        and (not is_natural_conversation_turn("osmanli nedir", "genel", None)),
        "yerel kaynak varken bilgi turu suppress zorlanmaz",
    )

    soft = citation_directive_for_turn(
        source_count=0, archive_primary=False, web_present=False, soft_natural=True
    )
    failed += _ok(
        "Güven: düşük" not in soft and "doğal sohbet" in soft.lower(),
        "soft citation → Güven düşük yok",
    )
    hard = citation_directive_for_turn(
        source_count=0, archive_primary=False, web_present=False, soft_natural=False
    )
    failed += _ok("Güven: düşük" in hard, "hard citation → Güven düşük var")

    failed += _ok(
        not payload_indicates_web_used("sadece yerel RAG metni [K1]"),
        "payload web yok",
    )
    failed += _ok(
        payload_indicates_web_used(
            "=== Web araması (DuckDuckGo — doğrulanmamış) ===\nsnippet"
        ),
        "payload web var",
    )

    # prepare_turn: use_web=False iken web bloğu eklenmesin
    from ilim_assistant.chat_core import prepare_turn

    prep = prepare_turn(
        "galaksi nedir",
        [],
        False,
        0,
        False,
        False,
        mode="genel",
        read_message_links=False,
    )
    if prep is None:
        failed += _ok(False, "prepare_turn None")
    else:
        _msg, _hits, user_payload, _sys, _model, _direct = prep
        failed += _ok(
            not payload_indicates_web_used(user_payload or ""),
            "use_web=false → prepare_turn web yok",
        )
        failed += _ok(
            "Güven: düşük" not in (user_payload or "")
            or "doğal sohbet" in (user_payload or "").lower(),
            "use_web=false kaynaksız → zorunlu Güven düşük talimatı yok/soft",
        )

    total = 10
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
