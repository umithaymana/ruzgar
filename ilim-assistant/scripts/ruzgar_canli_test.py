# Created by Ümit — Rüzgar canlı tur testi (in-process)
"""Bir dizi soruyu iter_chat_turn_events ile dener; tam yanıt + meta yazar."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ilim_assistant.env_bootstrap import ensure_ruzgar_env

ensure_ruzgar_env()

from desktop_server import ChatRequest, iter_chat_turn_events  # noqa: E402


SORULAR = [
    "selam",
    "osman bey kimdir",
    "orhan bey kimdir",
    "Osmanlı İmparatorluğu ne zaman kuruldu",
    "uzay nedir",
]


def run_one(message: str) -> dict:
    req = ChatRequest(
        message=message,
        history=[],
        use_web=True,
        coding_mode=False,
        mode="genel",
        read_message_links=False,
    )
    t0 = time.perf_counter()
    statuses: list[str] = []
    meta: dict = {}
    reply = ""
    flags: dict = {}
    for ev in iter_chat_turn_events(req):
        et = ev.get("type")
        if et == "status":
            statuses.append(str(ev.get("text") or ""))
        elif et == "meta":
            for k in ("umed_cevap_emri", "brain", "plan", "chat_route"):
                if k in ev:
                    meta[k] = ev[k]
        elif et == "token":
            reply += str(ev.get("text") or "")
        elif et == "done":
            reply = str(ev.get("full_reply") or reply)
            flags = {
                k: ev.get(k)
                for k in (
                    "egitim_instant",
                    "egitim_miss",
                    "instant_gundelik",
                    "tarih_fast",
                    "casual_fast",
                )
                if ev.get(k)
            }
    elapsed = time.perf_counter() - t0
    return {
        "soru": message,
        "sure_sn": round(elapsed, 2),
        "cevap": reply.strip()[:1200],
        "durumlar": statuses[:8],
        "bayraklar": flags,
        "meta_ozet": {
            "brain": (meta.get("brain") or {}).get("chain")
            if isinstance(meta.get("brain"), dict)
            else None,
            "umed": meta.get("umed_cevap_emri"),
            "plan_primary": (meta.get("plan") or {}).get("primary")
            if isinstance(meta.get("plan"), dict)
            else None,
        },
    }


def main() -> int:
    out = []
    for s in SORULAR:
        print(f"\n=== {s!r} ===", flush=True)
        r = run_one(s)
        out.append(r)
        print(f"sure: {r['sure_sn']}s")
        print(f"bayraklar: {r['bayraklar']}")
        print(f"cevap: {r['cevap'][:500]}")
    Path(__file__).with_name("ruzgar_canli_test_sonuc.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
