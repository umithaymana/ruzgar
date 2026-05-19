"""Sohbet modu / durum satırı kontrolü (in-process, LLM tamamlanmadan kesilir)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop_server import ChatRequest, iter_chat_turn_events


def probe(name: str, body: dict) -> None:
    req = ChatRequest(**body)
    statuses: list[str] = []
    route = None
    tokens = 0
    for ev in iter_chat_turn_events(req):
        if ev.get("type") == "meta" and ev.get("chat_route"):
            route = ev["chat_route"]
        if ev.get("type") == "status":
            t = str(ev.get("text") or "").strip()
            if t:
                statuses.append(t)
            if body.get("coding_mode") and len(statuses) >= 4:
                break
            if "gemini_first" in str(ev.get("phase") or "") or "Gemini hızlı" in t:
                break
        elif ev.get("type") == "token":
            tokens += 1
            break
        elif ev.get("type") == "error":
            print(f"--- {name} ERROR: {ev.get('text')}")
            return
    bad = [s for s in statuses if "bilgi + arşiv" in s or "Mektubat" in s]
    print(f"--- {name} route={route} statuses={len(statuses)} tokens={tokens} bad={len(bad)} ---")
    for s in statuses[:12]:
        print(f"  {s}")
    if bad:
        print("  !! heavy index:", bad[0][:100])


def main() -> int:
    cases = [
        (
            "coding_genel",
            {
                "message": "selam",
                "history": [],
                "use_web": True,
                "coding_mode": True,
                "mode": "genel",
                "read_message_links": False,
            },
        ),
        (
            "mode_programlama",
            {
                "message": "selam",
                "history": [],
                "use_web": False,
                "coding_mode": True,
                "mode": "programlama",
                "read_message_links": False,
            },
        ),
        (
            "encyclopedic",
            {
                "message": "ilk osmanlı padişahı kimdir",
                "history": [],
                "use_web": True,
                "coding_mode": False,
                "mode": "genel",
                "read_message_links": False,
            },
        ),
    ]
    for name, body in cases:
        probe(name, body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
