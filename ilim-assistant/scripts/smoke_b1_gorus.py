# -*- coding: utf-8 -*-
"""B1 — görüş sorusu tanım kartına düşmesin."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ana_motor_plan import (  # noqa: E402
    looks_like_opinion_request,
    maybe_gundelik_instant_reply,
    maybe_opinion_instant_reply,
    plan_question,
)
from ilim_assistant.motorlar.ses_faz72 import (  # noqa: E402
    classify_ses_intent,
    maybe_instant_faz72,
)
from ilim_assistant.ruzgar_egitim import is_invalid_egitim_pair  # noqa: E402
from ilim_assistant.ruzgar_otomatik_ogrenme import (  # noqa: E402
    lookup_bilgi_kutuphane_hint,
    try_bilgi_kutuphane_instant_reply,
)


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    q_yz = "Yapay zeka hakkinda ne dusunuyorsun?"
    q_asistan = "Sence Ruzgar iyi bir asistan mi?"
    q_nedir = "Yapay zeka nedir?"

    failed += _ok(looks_like_opinion_request(q_yz), "YZ görüş → opinion")
    failed += _ok(looks_like_opinion_request(q_asistan), "asistan sence → opinion")
    failed += _ok(not looks_like_opinion_request(q_nedir), "nedir → opinion değil")

    p_yz = plan_question(q_yz, "genel", {})
    failed += _ok(p_yz.primary == "gundelik", f"YZ plan gundelik (got {p_yz.primary})")
    p_as = plan_question(q_asistan, "genel", {})
    failed += _ok(p_as.primary == "gundelik", f"asistan plan gundelik (got {p_as.primary})")
    p_n = plan_question(q_nedir, "genel", {})
    failed += _ok(p_n.primary == "bilgi", f"nedir plan bilgi (got {p_n.primary})")

    failed += _ok(
        lookup_bilgi_kutuphane_hint(q_yz) is None,
        "YZ görüş → kütüphane hint yok",
    )
    failed += _ok(
        try_bilgi_kutuphane_instant_reply(q_yz) is None,
        "YZ görüş → anlık kütüphane yok",
    )
    inst_n = try_bilgi_kutuphane_instant_reply(q_nedir)
    failed += _ok(
        inst_n is not None and "teknoloji" in (inst_n or "").lower(),
        "nedir → kütüphane tanım korunur",
    )

    poison = (
        "Yapay zeka hakkında ne düşünüyorum? Yapay zeka, insan zekasını taklit "
        "eden bir teknolojidir. Bilgisayarların ve makinelerin insan gibi öğrenme "
        "yeteneğini geliştirir."
    )
    failed += _ok(
        is_invalid_egitim_pair(q_yz, poison),
        "görüş→tanım egitim invalid",
    )

    ses = classify_ses_intent(q_asistan, mode_norm="ses")
    failed += _ok(
        ses.get("reason") != "set_profile",
        f"asistan soru → set_profile yok (got {ses.get('reason')})",
    )
    failed += _ok(
        maybe_instant_faz72(q_asistan) is None,
        "asistan soru → ses anlık profil yok",
    )
    switch = classify_ses_intent("asistan moduna geç", mode_norm="ses")
    failed += _ok(
        switch.get("reason") == "set_profile",
        "açık geçiş → set_profile korunur",
    )

    op_yz = maybe_opinion_instant_reply(q_yz) or ""
    failed += _ok(
        bool(op_yz) and "teknolojidir" not in op_yz.lower() and "tanımlanır" not in op_yz.lower(),
        "YZ görüş anlık → tanım değil",
    )
    g_yz = maybe_gundelik_instant_reply(q_yz, "genel", {}) or ""
    failed += _ok(
        "yararlı" in g_yz.lower() or "araç" in g_yz.lower() or "görüyorum" in g_yz.lower(),
        "YZ gundelik anlık görüş",
    )
    g_as = maybe_gundelik_instant_reply(q_asistan, "genel", {}) or ""
    failed += _ok(
        "asistan" in g_as.lower() and "profil" not in g_as.lower(),
        "asistan soru → görüş anlık (ses profil yok)",
    )
    failed += _ok(
        maybe_opinion_instant_reply(q_nedir) is None,
        "nedir → görüş anlık yok",
    )

    total = 17
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
