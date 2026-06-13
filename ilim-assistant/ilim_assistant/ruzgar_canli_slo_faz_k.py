# Created by Ümit & Gökçenur
"""
Ana Motor — Faz K: ChatGPT canlı 10 soruluk SLO regresyon paketi (S1–S10).
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

CANLI_SLO_FAZ_K_VERSION = "canli-slo-faz-ac-v1-2026-06-13"

KESINTI_MARKERS = (
    "kesinti oldu",
    "[http 429]",
    "bulut kotası",
    "yanıt tamamlanamadı",
    '{"error"',
)


SLO_TURN_LABELS: dict[str, str] = {
    "S1": "Sohbet / oturum hafızası",
    "S2": "TDK / dilbilgisi",
    "S3": "Tarih / bilgi",
    "S4": "Bilim / medeniyet",
    "S5": "Canlı hava",
    "S6": "Çeviri",
    "S7": "Programlama",
    "S8": "Gündelik bilgi",
    "S9": "Hatırla komutu",
    "S10": "Tarih derin (Lale Devri)",
}

_ISSUE_HINTS: dict[str, str] = {
    "bos_yanit": "Yanıt boş — LLM zinciri veya API hatası; Ollama/Groq health kontrol edin.",
    "kisa": "Yanıt çok kısa — max token veya erken kesilme; RUZGAR_DOGAL_MAX_TOKENS artırın.",
    "yavas": "Yanıt yavaş — RAG ısınması, web tarama veya ağır model; ilk turdan sonra hızlanır.",
    "icerik_eslesmedi": "İçerik beklentiyle uyuşmadı — Web PRO, yerel RAG veya bilgi guard kontrol edin.",
    "yasak": "Kota/kesinti metni — yerel Ollama birincil olmalı (RUZGAR_FREE_BRAIN=1).",
    "exception": "Bağlantı/istisna — API veya /api/chat/full yolunu doğrulayın.",
}


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
        max_sec=float(os.environ.get("RUZGAR_SLO_S4_MAX_SEC", "90")),
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
        "label": SLO_TURN_LABELS.get(turn.id, turn.id),
    }


def build_weak_point_report(
    results: list[dict[str, Any]],
    *,
    passed: int,
    total: int,
    min_pass: int,
) -> dict[str, Any]:
    """Faz AC2 — SLO sonuçlarından okunabilir zayıf nokta raporu."""
    failed = [r for r in results if not r.get("ok")]
    weak: list[dict[str, Any]] = []
    recs: list[str] = []
    seen_rec: set[str] = set()

    for r in failed:
        issues = list(r.get("issues") or [])
        hints: list[str] = []
        for iss in issues:
            low_iss = str(iss).lower()
            if low_iss.startswith("exception"):
                hint = _ISSUE_HINTS["exception"]
            elif low_iss.startswith("yasak"):
                hint = _ISSUE_HINTS["yasak"]
            else:
                key = str(iss).split("(")[0].split(":")[0]
                hint = _ISSUE_HINTS.get(key, "")
            if hint and hint not in hints:
                hints.append(hint)
        for h in hints:
            if h not in seen_rec:
                seen_rec.add(h)
                recs.append(h)
        weak.append(
            {
                "id": r.get("id"),
                "label": r.get("label") or SLO_TURN_LABELS.get(str(r.get("id")), ""),
                "issues": issues,
                "elapsed_sec": r.get("elapsed_sec"),
                "reply_len": r.get("reply_len"),
                "preview": r.get("reply_preview"),
            }
        )

    slow = [
        r
        for r in results
        if r.get("ok") and any(str(x).startswith("yavas") for x in (r.get("issues") or []))
    ]
    score_pct = round(100.0 * passed / max(1, total), 1)
    summary_tr = (
        f"{passed}/{total} senaryo geçti (eşik ≥{min_pass}). "
        + (f"Zayıf: {len(weak)} tur." if weak else "Tüm turlar geçti.")
    )
    if not recs and weak:
        recs.append("Başarısız turları tek tek tekrar deneyin; health ve Ollama günlüğüne bakın.")
    if passed < min_pass:
        recs.insert(
            0,
            f"SLO eşiği tutmadı ({passed}/{min_pass}) — önce kırmızı turları düzeltin.",
        )

    return {
        "ok": passed >= min_pass,
        "summary_tr": summary_tr,
        "score_pct": score_pct,
        "passed": passed,
        "total": total,
        "min_pass": min_pass,
        "failed_count": len(weak),
        "weak_turns": weak,
        "slow_turns": [
            {
                "id": r.get("id"),
                "label": r.get("label"),
                "elapsed_sec": r.get("elapsed_sec"),
            }
            for r in slow
        ],
        "recommendations": recs[:8],
    }


def format_weak_point_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Ana Motor — SLO zayıf nokta raporu",
        "",
        report.get("summary_tr") or "",
        f"Skor: **{report.get('score_pct', 0)}%**",
        "",
    ]
    weak = report.get("weak_turns") or []
    if weak:
        lines.append("## Başarısız turlar")
        for w in weak:
            lines.append(
                f"- **{w.get('id')}** ({w.get('label')}): "
                f"{', '.join(w.get('issues') or [])} — {w.get('elapsed_sec')}s"
            )
        lines.append("")
    recs = report.get("recommendations") or []
    if recs:
        lines.append("## Öneriler")
        for r in recs:
            lines.append(f"- {r}")
    return "\n".join(lines)


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
                "label": SLO_TURN_LABELS.get(turn.id, turn.id),
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
    report = build_weak_point_report(
        results,
        passed=passed,
        total=len(CHATGPT_SLO_PACK),
        min_pass=need,
    )
    return {
        "ok": passed >= need,
        "version": CANLI_SLO_FAZ_K_VERSION,
        "passed": passed,
        "total": len(CHATGPT_SLO_PACK),
        "min_pass": need,
        "live": bool(live_base),
        "results": results,
        "weak_point_report": report,
    }


def slo_pack_status() -> dict[str, object]:
    job = get_slo_job_status()
    last = job.get("last_report")
    return {
        "enabled": slo_pack_enabled(),
        "version": CANLI_SLO_FAZ_K_VERSION,
        "turns": len(CHATGPT_SLO_PACK),
        "min_pass": min_pass_count(),
        "job_running": bool(job.get("running")),
        "last_score_pct": (last or {}).get("score_pct") if isinstance(last, dict) else None,
        "last_summary_tr": (last or {}).get("summary_tr") if isinstance(last, dict) else None,
    }


# --- Faz AC2: arka plan SLO + son rapor ---

_slo_lock = threading.Lock()
_slo_job: dict[str, Any] = {
    "running": False,
    "phase": "idle",
    "progress": "",
    "started_at": 0.0,
    "finished_at": 0.0,
    "last_pack": None,
    "last_report": None,
    "error": "",
}


def get_slo_job_status() -> dict[str, Any]:
    with _slo_lock:
        return {
            "running": bool(_slo_job.get("running")),
            "phase": _slo_job.get("phase"),
            "progress": _slo_job.get("progress"),
            "started_at": _slo_job.get("started_at"),
            "finished_at": _slo_job.get("finished_at"),
            "last_report": _slo_job.get("last_report"),
            "last_pack_ok": (_slo_job.get("last_pack") or {}).get("ok"),
            "error": _slo_job.get("error"),
            "version": CANLI_SLO_FAZ_K_VERSION,
        }


def _set_slo_job(**kwargs: Any) -> None:
    with _slo_lock:
        _slo_job.update(kwargs)


def _slo_worker(*, live_base: str | None, workspace_root: str | None) -> None:
    def _on(ev: dict[str, Any]) -> None:
        _set_slo_job(progress=f"{ev.get('id')} — {'OK' if ev.get('ok') else 'FAIL'}")

    try:
        out = run_slo_pack(
            live_base=live_base,
            workspace_root=workspace_root,
            on_result=_on,
        )
        report = out.get("weak_point_report") or {}
        _set_slo_job(
            running=False,
            phase="done",
            finished_at=time.time(),
            last_pack=out,
            last_report=report,
            progress=f"Tamam — {out.get('passed')}/{out.get('total')}",
            error="" if out.get("ok") else "slo_esik_alti",
        )
        print(
            f"[Rüzgar] SLO paketi bitti — {report.get('summary_tr', '')}",
            flush=True,
        )
        try:
            from ilim_assistant.ana_motor_faz_ad_slo_gece import persist_slo_report

            persist_slo_report(out, report)
        except Exception:
            pass
    except Exception as exc:
        _set_slo_job(
            running=False,
            phase="failed",
            finished_at=time.time(),
            error=str(exc)[:200],
            progress="Hata",
        )


def start_slo_pack_background(
    *,
    live_base: str | None = None,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    """Arka planda S1–S10 (5–15 dk sürebilir)."""
    if not slo_pack_enabled():
        return {"ok": False, "error": "disabled", "version": CANLI_SLO_FAZ_K_VERSION}
    with _slo_lock:
        if _slo_job.get("running"):
            return {
                "ok": True,
                "already_running": True,
                "job": get_slo_job_status(),
                "version": CANLI_SLO_FAZ_K_VERSION,
            }
    _set_slo_job(
        running=True,
        phase="running",
        progress="S1…",
        started_at=time.time(),
        finished_at=0.0,
        error="",
    )
    threading.Thread(
        target=_slo_worker,
        kwargs={"live_base": live_base, "workspace_root": workspace_root},
        daemon=True,
        name="slo-pack",
    ).start()
    return {
        "ok": True,
        "started": True,
        "live": bool(live_base),
        "turns": len(CHATGPT_SLO_PACK),
        "version": CANLI_SLO_FAZ_K_VERSION,
    }


def resolve_live_slo_base(explicit: str | None = None) -> str:
    if explicit and str(explicit).strip():
        return str(explicit).strip().rstrip("/")
    port = os.environ.get("RUZGAR_API_PORT", "8779").strip() or "8779"
    return f"http://127.0.0.1:{port}"
