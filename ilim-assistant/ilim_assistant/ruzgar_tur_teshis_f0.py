# Created by Ümit & Gökçenur
"""
F0 — Tur teşhis kartı (ölçüm; kör yama yok).

Miss sınıfları, son tur halkası, warmup ılık/soğuk özeti.
Kullanıcıya spam yok; log + /api/tur-teshis.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from typing import Any

FAZ_F0_VERSION = "tur-teshis-f0-v1-2026-11-17"

# Miss sınıfları (F0.2) — «öğret» tek torba olmasın
MISS_NO_HITS = "no_hits"
MISS_FILTERED = "filtered"
MISS_TIMEOUT = "timeout"
MISS_WEAK_LLM = "weak_llm"
MISS_BUDGET = "budget"
MISS_SAYI_GATE = "sayi_hard_gate"
MISS_KUTUPHANE = "kutuphane_usable"
MISS_UNKNOWN = "unknown"

_MISS_CLASSES = frozenset(
    {
        MISS_NO_HITS,
        MISS_FILTERED,
        MISS_TIMEOUT,
        MISS_WEAK_LLM,
        MISS_BUDGET,
        MISS_SAYI_GATE,
        MISS_KUTUPHANE,
        MISS_UNKNOWN,
    }
)

_lock = threading.Lock()
_recent: deque[dict[str, Any]] = deque(maxlen=40)
_last_shamela_cats: list[str] = []
_warmup: dict[str, Any] = {
    "rag": False,
    "ollama": False,
    "whisper_tts": False,
    "boot_bg_done": False,
    "rag_at": None,
    "ollama_at": None,
    "whisper_tts_at": None,
    "boot_bg_at": None,
}
_ollama_probe_cache: dict[str, Any] = {"ts": 0.0, "ok": False, "models": [], "warn": None}


def _enabled() -> bool:
    return os.environ.get("RUZGAR_TUR_TESHIS_F0", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def note_shamela_cats(cats: list[str] | tuple[str, ...] | None) -> None:
    global _last_shamela_cats
    if not cats:
        return
    with _lock:
        _last_shamela_cats = [str(c).strip() for c in cats if str(c).strip()][:8]


def get_last_shamela_cats() -> list[str]:
    with _lock:
        return list(_last_shamela_cats)


def mark_warmup(part: str, ok: bool = True) -> None:
    key = (part or "").strip().lower()
    if key not in ("rag", "ollama", "whisper_tts", "boot_bg_done"):
        return
    with _lock:
        _warmup[key] = bool(ok)
        at_key = {
            "rag": "rag_at",
            "ollama": "ollama_at",
            "whisper_tts": "whisper_tts_at",
            "boot_bg_done": "boot_bg_at",
        }.get(key)
        if at_key:
            _warmup[at_key] = time.time() if ok else None


def warmup_snapshot(*, booting: bool | None = None) -> dict[str, Any]:
    """F0.3 / F1.4 — ılık / soğuk + Ollama model uyarısı."""
    with _lock:
        w = dict(_warmup)
        cats = list(_last_shamela_cats)
    rag = bool(w.get("rag"))
    ollama = bool(w.get("ollama"))
    ses = bool(w.get("whisper_tts"))
    boot_done = bool(w.get("boot_bg_done"))
    ollama_models: list[str] = []
    ollama_ok = False
    ollama_warn = None
    try:
        now = time.time()
        if now - float(_ollama_probe_cache.get("ts") or 0) > 30.0:
            from ilim_assistant.llm_ollama import ollama_list_model_names, ollama_reachable

            ok = bool(ollama_reachable(timeout_sec=1.2))
            models: list[str] = []
            warn = None
            if ok:
                models = list(ollama_list_model_names(timeout_sec=1.5) or [])[:12]
                if not models:
                    warn = "Ollama açık ama model listesi boş"
            else:
                warn = "Ollama ulaşılmıyor"
            with _lock:
                _ollama_probe_cache.update(
                    {"ts": now, "ok": ok, "models": models, "warn": warn}
                )
        with _lock:
            ollama_ok = bool(_ollama_probe_cache.get("ok"))
            ollama_models = list(_ollama_probe_cache.get("models") or [])
            ollama_warn = _ollama_probe_cache.get("warn")
        if ollama_ok and ollama_models and not ollama:
            ollama = True
    except Exception:
        ollama_warn = "Ollama sağlık kontrolü atlandı"
    if booting is True:
        state = "isiniyor"
    elif rag and boot_done and ollama_ok:
        state = "ilik"
    elif rag or ollama or ollama_ok:
        state = "kismi"
    else:
        state = "soguk"
    return {
        "ok": True,
        "version": FAZ_F0_VERSION,
        "state": state,  # ilik | kismi | soguk | isiniyor
        "ilik": state == "ilik",
        "rag": rag,
        "ollama": ollama,
        "ollama_reachable": ollama_ok,
        "ollama_models": ollama_models,
        "ollama_warn": ollama_warn,
        "whisper_tts": ses,
        "boot_bg_done": boot_done,
        "rag_at": w.get("rag_at"),
        "ollama_at": w.get("ollama_at"),
        "whisper_tts_at": w.get("whisper_tts_at"),
        "boot_bg_at": w.get("boot_bg_at"),
        "last_shamela_cats": cats,
        "label_tr": {
            "ilik": "Ilık — RAG/boot/Ollama hazır",
            "kismi": "Kısmi — bazı parçalar hazır",
            "soguk": "Soğuk — ilk tur yavaş olabilir",
            "isiniyor": "Isınıyor — arka plan warmup",
        }.get(state, state),
    }


def classify_miss(
    *,
    reply: str = "",
    orch: dict[str, Any] | None = None,
    hits_count: int | None = None,
    elapsed_sec: float | None = None,
    egitim_miss: bool = False,
    budget_sec: float | None = None,
) -> str | None:
    """Cevap miss/öğret ise sınıf; değilse None."""
    o = orch if isinstance(orch, dict) else {}
    preset = str(o.get("miss_class") or "").strip()
    if preset in _MISS_CLASSES:
        return preset
    from ilim_assistant.ruzgar_umed_kurallari import MISS_PHRASE, TIMEOUT_PHRASE

    t = (reply or "").strip()
    is_timeout_phrase = bool(TIMEOUT_PHRASE and (TIMEOUT_PHRASE in t or t == TIMEOUT_PHRASE))
    is_miss = (
        bool(egitim_miss)
        or (MISS_PHRASE in t)
        or t == MISS_PHRASE
        or is_timeout_phrase
    )
    if not is_miss:
        low = t.lower()
        if "bulamadım" in low and ("öğret" in low or "ogret" in low):
            is_miss = True
        if "süre yetmedi" in low or "sure yetmedi" in low:
            is_miss = True
            is_timeout_phrase = True
    if not is_miss:
        return None

    if is_timeout_phrase:
        return MISS_TIMEOUT
    if o.get("sayi_hard_gate"):
        return MISS_SAYI_GATE
    if o.get("kutuphane_usable") is False or o.get("miss_class") == MISS_KUTUPHANE:
        return MISS_KUTUPHANE

    hc = hits_count
    if hc is None:
        try:
            hc = int(o.get("hits_count"))
        except Exception:
            hc = None
    raw_n = o.get("hits_raw_count")
    try:
        raw_n_i = int(raw_n) if raw_n is not None else None
    except Exception:
        raw_n_i = None

    if hc == 0 and raw_n_i is not None and raw_n_i > 0:
        return MISS_FILTERED
    if hc == 0 or (hc is None and o.get("thin_pipe")):
        if hc == 0:
            return MISS_NO_HITS

    el = float(elapsed_sec) if elapsed_sec is not None else None
    bud = budget_sec
    if bud is None:
        try:
            from ilim_assistant.ruzgar_umed_cevap_emri import turn_budget_sec

            bud = float(turn_budget_sec(""))
        except Exception:
            bud = 15.0
    if el is not None and el >= float(bud) * 0.92:
        return MISS_TIMEOUT if el >= float(bud) else MISS_BUDGET

    low = t.lower()
    if "ollama" in low or "gemini kota" in low or "yanıt yok" in low:
        return MISS_WEAK_LLM
    if egitim_miss and el is not None and el >= float(bud) * 0.8:
        return MISS_TIMEOUT
    if egitim_miss:
        return MISS_WEAK_LLM
    return MISS_UNKNOWN


def build_tur_kart(
    *,
    user_message: str = "",
    reply: str = "",
    orch: dict[str, Any] | None = None,
    hits: list | None = None,
    elapsed_sec: float | None = None,
    provider: str | None = None,
    egitim_miss: bool = False,
    mode: str = "genel",
) -> dict[str, Any]:
    o = dict(orch) if isinstance(orch, dict) else {}
    hits_list = list(hits or [])
    hits_count = len(hits_list)
    if "hits_count" in o:
        try:
            hits_count = int(o["hits_count"])
        except Exception:
            pass
    top_scores: list[float] = []
    for h in hits_list[:5]:
        try:
            if isinstance(h, (list, tuple)) and len(h) >= 3:
                top_scores.append(round(float(h[2]), 4))
        except Exception:
            continue
    thin = bool(o.get("thin_pipe"))
    usable = o.get("kutuphane_usable")
    if usable is None and o.get("miss_class") == MISS_KUTUPHANE:
        usable = False
    cats = o.get("shamela_cats")
    if not cats:
        cats = get_last_shamela_cats()
    miss_class = classify_miss(
        reply=reply,
        orch=o,
        hits_count=hits_count,
        elapsed_sec=elapsed_sec,
        egitim_miss=egitim_miss,
    )
    prov = (provider or o.get("provider") or o.get("llm_provider") or "").strip() or None
    if not prov:
        try:
            from ilim_assistant.ruzgar_provider_rozet import last_brain_profile

            prov = last_brain_profile() or None
        except Exception:
            prov = None
    rozet = (o.get("provider_rozet") or "").strip() or None
    if not rozet:
        try:
            from ilim_assistant.ruzgar_provider_rozet import provider_rozet_label

            rozet = provider_rozet_label(
                prov or "",
                raftan=bool(o.get("kutuphane_extractive") or o.get("ilim_no_cloud_invent")),
                extractive=bool(o.get("kutuphane_extractive")),
            )
        except Exception:
            rozet = None
    plan = o.get("plan") if isinstance(o.get("plan"), dict) else {}
    card = {
        "version": FAZ_F0_VERSION,
        "ts": time.time(),
        "mode": (mode or "genel").strip() or "genel",
        "user_preview": (user_message or "").strip()[:160],
        "hits_count": hits_count,
        "hits_raw_count": o.get("hits_raw_count"),
        "top_scores": top_scores,
        "usable": usable,
        "thin_pipe": thin,
        "shamela_cats": list(cats or [])[:8],
        "elapsed_sec": round(float(elapsed_sec), 3) if elapsed_sec is not None else None,
        "provider": prov,
        "provider_rozet": rozet,
        "miss_class": miss_class,
        "egitim_miss": bool(egitim_miss),
        "hub_target": o.get("hub_target"),
        "plan_primary": plan.get("primary") if isinstance(plan, dict) else None,
        "sayi_hard_gate": bool(o.get("sayi_hard_gate")),
        "warmup": warmup_snapshot().get("state"),
        "ilim_no_cloud_invent": bool(o.get("ilim_no_cloud_invent")),
    }
    return card


def record_tur_kart(card: dict[str, Any]) -> dict[str, Any]:
    if not _enabled():
        return card
    with _lock:
        _recent.appendleft(dict(card))
    try:
        import logging

        logging.getLogger("ruzgar.tur_teshis").info(
            "F0 tur: hits=%s usable=%s thin=%s miss=%s prov=%s rozet=%s el=%s cats=%s",
            card.get("hits_count"),
            card.get("usable"),
            card.get("thin_pipe"),
            card.get("miss_class"),
            card.get("provider"),
            card.get("provider_rozet"),
            card.get("elapsed_sec"),
            card.get("shamela_cats"),
        )
    except Exception:
        pass
    return card


def recent_cards(limit: int = 10) -> list[dict[str, Any]]:
    n = max(1, min(40, int(limit or 10)))
    with _lock:
        return [dict(x) for x in list(_recent)[:n]]


def attach_teshis_to_done(
    done: dict[str, Any],
    *,
    hits: list | None = None,
    mode: str = "genel",
) -> dict[str, Any]:
    """done olayına tur_teshis ekler ve halkaya yazar."""
    if not _enabled() or not isinstance(done, dict):
        return done
    orch = done.get("orchestra") if isinstance(done.get("orchestra"), dict) else {}
    card = build_tur_kart(
        user_message=str(done.get("user_message") or ""),
        reply=str(done.get("full_reply") or ""),
        orch=orch,
        hits=hits,
        elapsed_sec=done.get("elapsed_sec"),
        provider=done.get("provider") or done.get("llm_provider"),
        egitim_miss=bool(done.get("egitim_miss")),
        mode=mode,
    )
    record_tur_kart(card)
    out = dict(done)
    out["tur_teshis"] = card
    if card.get("miss_class") and isinstance(orch, dict):
        orch = dict(orch)
        orch["miss_class"] = card["miss_class"]
        out["orchestra"] = orch
    return out


def note_rag_retrieval(
    orchestration_out: dict[str, Any] | None,
    *,
    hits: list | None = None,
    hits_raw_count: int | None = None,
    usable: bool | None = None,
    miss_class: str | None = None,
) -> None:
    if orchestration_out is None or not isinstance(orchestration_out, dict):
        return
    hl = list(hits or [])
    orchestration_out["hits_count"] = len(hl)
    if hits_raw_count is not None:
        orchestration_out["hits_raw_count"] = int(hits_raw_count)
    cats = get_last_shamela_cats()
    if cats:
        orchestration_out["shamela_cats"] = cats
    if usable is not None:
        orchestration_out["kutuphane_usable"] = bool(usable)
    if miss_class and miss_class in _MISS_CLASSES:
        orchestration_out["miss_class"] = miss_class
