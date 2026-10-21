# -*- coding: utf-8 -*-
"""B3 — üniversite sayısı: kaynaksız 209 + webten bakarak meta kesilsin."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.ruzgar_egitim import is_invalid_egitim_pair  # noqa: E402
from ilim_assistant.ruzgar_otomatik_ogrenme import (  # noqa: E402
    lookup_bilgi_kutuphane_hint,
    should_check_bilgi_kutuphane_first,
    try_bilgi_kutuphane_instant_reply,
)
from ilim_assistant.ruzgar_web_arastirma_pro import (  # noqa: E402
    looks_like_live_web_needed,
    reason_web_question,
)
from ilim_assistant.text_encoding import (  # noqa: E402
    finalize_assistant_reply,
    strip_web_capability_noise,
)


def _ok(cond: bool, label: str) -> int:
    print(("OK" if cond else "FAIL"), "-", label)
    return 0 if cond else 1


def main() -> int:
    failed = 0
    q = "Turkiyede kac universite var?"
    poison = "Turkiyede 209 üniversite var. Webten bakarak bu bilgiye ulaştım."

    failed += _ok(looks_like_live_web_needed(q), "uni sayısı → live web")
    failed += _ok(
        not should_check_bilgi_kutuphane_first(q),
        "uni → kütüphane önce değil",
    )
    failed += _ok(
        try_bilgi_kutuphane_instant_reply(q) is None,
        "uni → zehirli anlık yok",
    )
    failed += _ok(
        lookup_bilgi_kutuphane_hint(q) is None,
        "uni → hint yok (invalid scrub)",
    )
    failed += _ok(is_invalid_egitim_pair(q, poison), "209+webten → invalid")

    stripped = strip_web_capability_noise(poison)
    failed += _ok(
        "webten" not in stripped.lower() and "ulaştım" not in stripped.lower(),
        "webten bakarak strip",
    )
    final = finalize_assistant_reply(poison)
    failed += _ok(
        "209" not in final and ("YÖK" in final or "yök" in final.lower() or "uydurmam" in final),
        "finalize → dürüst uni mesajı",
    )

    reasoned = reason_web_question(q)
    failed += _ok(
        "YÖK" in (reasoned.get("query") or "") or "yök" in (reasoned.get("query") or "").lower(),
        "arama sorgusu YÖK",
    )

    # Kaynaklı cevap korunur
    good = (
        "YÖK istatistiğine göre Türkiye'de yaklaşık 208 üniversite vardır "
        "(yok.gov.tr)."
    )
    failed += _ok(
        "208" in finalize_assistant_reply(good),
        "YÖK kaynaklı rakam korunur",
    )

    total = 10
    print(f"result: {total - failed}/{total} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
