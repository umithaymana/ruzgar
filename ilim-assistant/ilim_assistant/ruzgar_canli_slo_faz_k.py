# Created by Ümit & Gökçenur
"""
Ana Motor — Faz K: ChatGPT canlı 10 soruluk SLO regresyon paketi (S1–S10).
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

CANLI_SLO_FAZ_K_VERSION = "canli-slo-faz-k-v1-2026-06-11"

KESINTI_MARKERS = (
    "kesinti oldu",
    "[http 429]",
    "bulut kotası",
    "yanıt tamamlanamadı",
    '{"error"',
)


@dataclass
class SloTurn:
    id: str
    message: str
    max_sec: float = 45.0
    min_chars: int = 12
    must_contain_any: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = KESINTI_MARKERS


CHATGPT_SLO_PACK: tuple[SloTurn, ...] = (
    SloTurn(
        "S1",
        "selam rüzgar bugün nasılsın? dün seninle hangi konuları konuşmuştuk bana söyler misin",
        max_sec=38.0,
        min_chars=18,
        must_contain_any=("ümit", "selam", "sohbet", "konu", "hatırl"),
    ),
    SloTurn(
        "S2",
        "merhaba kelimesinin TDK anlamı nedir?",
        max_sec=40.0,
        min_chars=15,
        must_contain_any=("merhaba", "selam", "tdk", "anlam"),
    ),
    SloTurn(
        "S3",
        "Osmanlı devletini kim kurdu?",
        max_sec=50.0,
        min_chars=20,
        must_contain_any=("osman", "fatih", "kur", "1299", "orhan"),
    ),
    SloTurn(
        "S4",
        "İslam medeniyetinde ilim geleneği hakkında ne söylersin?",
        max_sec=55.0,
        min_chars=35,
        must_contain_any=("ilim", "bilim", "medrese", "islam", "öğren"),
    ),
    SloTurn(
        "S5",
        "İstanbul hava durumu nasıl?",
        max_sec=25.0,
        min_chars=8,
        must_contain_any=("istanbul", "derece", "hava", "sıcak", "°"),
    ),
    SloTurn(
        "S6",
        "Merhaba dünya cümlesini ingilizceye çevir",
        max_sec=35.0,
        min_chars=8,
        must_contain_any=("hello", "world", "ingiliz", "çevir", "translate"),
    ),
    SloTurn(
        "S7",
        "Python'da [1,2,3] listesini ters çevir nasıl yapılır?",
        max_sec=45.0,
        min_chars=15,
        must_contain_any=("reverse", "ters", "[3", "slice", "::-1"),
    ),
    SloTurn(
        "S8",
        "Çay demlemek için ideal süre kaç dakikadır?",
        max_sec=45.0,
        min_chars=12,
        must_contain_any=("dakika", "çay", "deme", "dk"),
    ),
    SloTurn(
        "S9",
        "hatırla: smoke slo test sorusu = bu bir test cevabıdır",
        max_sec=20.0,
        min_chars=6,
        must_contain_any=("hatırl", "kayd", "tamam", "yazd"),
    ),
    SloTurn(
        "S10",
        "Lale Devri'nde hangi alanlarda gelişme oldu?",
        max_sec=55.0,
        min_chars=30,
        must_contain_any=("lale", "devr", "iii", "mustafa", "paşa", "sanat"),
    ),
)


def slo_pack_enabled() -> bool:
    return os.environ.get("RUZGAR_CANLI_SLO_FAZ_K", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def min_pass_count() -> int:
    try:
        return max(1, min(int(os.environ.get("RUZGAR_SLO_PACK_MIN_PASS", "8")), 10))
    except ValueError:
        return 8


def _fold(s: str) -> str:
    return (s or "").strip().lower()


def evaluate_reply(turn: SloTurn, reply: str, elapsed: float) -> dict[str, Any]:
    r = (reply or "").strip()
    low = _fold(r)
    issues: list[str] = []
    if not r:
        issues.append("bos_yanit")
    if len(r) < turn.min_chars:
        issues.append(f"kisa({len(r)}<{turn.min_chars})")
    if elapsed > turn.max_sec:
        issues.append(f"yavas({elapsed:.1f}s>{turn.max_sec}s)")
    for bad in turn.must_not_contain:
        if bad.lower() in low:
            issues.append(f"yasak:{bad[:24]}")
    if turn.must_contain_any and not any(x.lower() in low for x in turn.must_contain_any):
        issues.append("icerik_eslesmedi")
    return {
        "id": turn.id,
        "ok": not issues,
        "issues": issues,
        "elapsed_sec": round(elapsed, 2),
        "reply_len": len(r),
        "reply_preview": r[:120],
    }


def _collect_local_turn(
    message: str,
    history: list[dict[str, Any]],
    *,
    workspace_root: str | None,
) -> tuple[str, float]:
    from desktop_server import ChatRequest, iter_chat_turn_events

    t0 = time.monotonic()
    req = ChatRequest(
        message=message,
        history=list(history),
        mode="genel",
        coding_mode=False,
        use_web=False,
        fetch_pages=0,
        workspace_root=workspace_root,
    )
    reply = ""
    for ev in iter_chat_turn_events(req):
        if ev.get("type") == "token":
            reply += str(ev.get("text") or "")
        elif ev.get("type") == "done":
            reply = str(ev.get("full_reply") or reply)
    return reply.strip(), time.monotonic() - t0


def _collect_live_turn(
    base: str,
    message: str,
    history: list[dict[str, Any]],
    *,
    timeout: float,
) -> tuple[str, float, dict[str, Any]]:
    url = base.rstrip("/") + "/api/chat/full"
    body = json.dumps(
        {
            "message": message,
            "history": history,
            "mode": "genel",
            "coding_mode": False,
            "use_web": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    t0 = time.monotonic()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        cj = json.loads(r.read().decode("utf-8", errors="replace"))
    elapsed = time.monotonic() - t0
    if not cj.get("ok"):
        return "", elapsed, cj
    reply = str(cj.get("full_reply") or cj.get("reply") or "").strip()
    return reply, elapsed, cj


def run_slo_pack(
    *,
    live_base: str | None = None,
    workspace_root: str | None = None,
    on_result: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """S1–S10 ardışık tur; geçmiş birikir (uzun sohbet simülasyonu)."""
    if not slo_pack_enabled():
        return {"ok": True, "skipped": True, "reason": "disabled"}

    history: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    passed = 0

    for turn in CHATGPT_SLO_PACK:
        try:
            if live_base:
                reply, elapsed, _raw = _collect_live_turn(
                    live_base,
                    turn.message,
                    history,
                    timeout=max(turn.max_sec + 30.0, 60.0),
                )
            else:
                reply, elapsed = _collect_local_turn(
                    turn.message,
                    history,
                    workspace_root=workspace_root,
                )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            ev = {
                "id": turn.id,
                "ok": False,
                "issues": [f"exception:{str(exc)[:80]}"],
                "elapsed_sec": 0.0,
                "reply_len": 0,
                "reply_preview": "",
            }
            results.append(ev)
            if on_result:
                on_result(ev)
            continue

        ev = evaluate_reply(turn, reply, elapsed)
        results.append(ev)
        if on_result:
            on_result(ev)
        if ev.get("ok"):
            passed += 1
        if reply:
            history.append({"role": "user", "content": turn.message})
            history.append({"role": "assistant", "content": reply[:2000]})

    need = min_pass_count()
    return {
        "ok": passed >= need,
        "version": CANLI_SLO_FAZ_K_VERSION,
        "passed": passed,
        "total": len(CHATGPT_SLO_PACK),
        "min_pass": need,
        "live": bool(live_base),
        "results": results,
    }


def slo_pack_status() -> dict[str, object]:
    return {
        "enabled": slo_pack_enabled(),
        "version": CANLI_SLO_FAZ_K_VERSION,
        "turns": len(CHATGPT_SLO_PACK),
        "min_pass": min_pass_count(),
    }
