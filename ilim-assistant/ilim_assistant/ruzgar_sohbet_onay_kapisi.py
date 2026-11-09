# Created by Ümit & Gökçenur
"""
Rüzgar Sohbet — ürün onay kapısı (plan 12 S1).

Sohbet ≠ iş. «Yap» deneni yap; onay yoksa yan etki yok.
Niyet: SOHBET | SORU | OGRET | IS | YASAK
Kapat: RUZGAR_SOHBET_ONAY=0
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

VERSION = "sohbet-onay-s1-v1-2026-11-09"
_PENDING_TTL_SEC = 900
_PENDING_NAME = "sohbet_onay_pending.json"
_AUDIT_NAME = "sohbet_onay_audit.jsonl"

_APPROVE_RE = re.compile(
    r"^\s*(?:yap|evet|onayla|tamam\s+yap|onayliyorum|onaylıyorum|olur|devam\s+et)\s*$",
    re.I,
)
_REJECT_RE = re.compile(
    r"^\s*(?:yapma|hayir|hayır|iptal|vazge[cç]|dur|istemiyorum)\s*$",
    re.I,
)

_YASAK_RE = re.compile(
    r"(?:"
    r"\b(?:dosya\s+sil|sil\s+dosya|rm\s+-rf|format\s+at|disk\s+sil)\b|"
    r"\b(?:git\s+push\s+--force|force\s+push)\b|"
    r"\b(?:kredi\s+kart|şifreler?i?\s+gönder|sifreleri?\s+gonder)\b"
    r")",
    re.I,
)

_IS_HINT_RE = re.compile(
    r"(?:"
    r"\b(?:kaydet|yaz\s+plana|plana\s+yaz|excel(?:e|\'ye)?\s+yaz|kurulum|yükle|yukle|"
    r"commit|push|sil|temizle|taşı|tasi|kopyala|pip\s+install|winget|"
    r"yeniden\s+başlat|yeniden\s+baslat|force\s*restart)\b|"
    r"^(?:yap\s*:|işlem\s+iste)"
    r")",
    re.I,
)

_OGRET_RE = re.compile(
    r"(?:"
    r"\b(?:öğret|ogret|şunu\s+öğren|sunu\s+ogren|hafızaya\s+yaz|hatırla\s*:)\b"
    r")",
    re.I,
)

_SORU_RE = re.compile(
    r"(?:"
    r"\?$|\b(?:nedir|kimdir|nasıl|nasil|neden|anlat|açıkla|acikla|kaç|kac|"
    r"ne\s+demek|hakkında|hakkinda)\b"
    r")",
    re.I,
)

_SOHBET_RE = re.compile(
    r"(?:"
    r"^(?:selam|merhaba|nasılsın|nasilsin)\b|"
    r"\b(?:nasıl\s+olur|nasil\s+olur|konuşalım|konusalim|ne\s+dersin|"
    r"fikir\s+ver|sence)\b"
    r")",
    re.I,
)

# Masa yazma eylemleri — onay ister. Okuma serbest.
_MASA_WRITE_PREFIXES = (
    "belge.yaz",
    "belge.ekle",
    "belge.yerine",
    "belge.tablo",
    "belge.temizle",
    "tablo.hucre",
    "tablo.sil",
    "tablo.temizle",
    "tablo.topla",
    "cizim.",
    "sunum.",
    "notlar.",
)
_MASA_READ_EYLEMS = {
    "belge.oku",
    "tablo.oku",
    "sunum.oku",
    "cizim.oku",
}


def enabled() -> bool:
    return os.environ.get("RUZGAR_SOHBET_ONAY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _store_dir() -> Path:
    # ilim-assistant/.ruzgar
    here = Path(__file__).resolve().parents[1]
    d = here / ".ruzgar"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pending_path() -> Path:
    return _store_dir() / _PENDING_NAME


def _audit_path() -> Path:
    return _store_dir() / _AUDIT_NAME


def audit(event: str, payload: dict[str, Any] | None = None) -> None:
    row = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "version": VERSION,
        **(payload or {}),
    }
    try:
        with _audit_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def load_pending() -> dict[str, Any] | None:
    p = _pending_path()
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if float(data.get("expires_at") or 0) < time.time():
        clear_pending()
        audit("pending_expired", {"kind": data.get("kind")})
        return None
    return data


def clear_pending() -> None:
    p = _pending_path()
    try:
        if p.is_file():
            p.unlink()
    except OSError:
        pass


def save_pending(op: dict[str, Any]) -> dict[str, Any]:
    now = time.time()
    payload = {
        **op,
        "created_at": now,
        "expires_at": now + _PENDING_TTL_SEC,
        "version": VERSION,
    }
    _pending_path().write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    audit("pending_saved", {"kind": op.get("kind"), "summary": op.get("summary")})
    return payload


def classify_intent(message: str) -> dict[str, Any]:
    raw = (message or "").strip()
    low = _fold(raw)
    if not raw:
        return {"intent": "SOHBET", "reason": "empty", "risk": "none"}
    if _APPROVE_RE.match(raw) or _REJECT_RE.match(raw):
        return {"intent": "SOHBET", "reason": "approve_reject_token", "risk": "none"}
    if _YASAK_RE.search(raw) or _YASAK_RE.search(low):
        return {"intent": "YASAK", "reason": "dangerous_pattern", "risk": "high"}
    if _OGRET_RE.search(raw) or _OGRET_RE.search(low):
        return {"intent": "OGRET", "reason": "teach_memory", "risk": "low"}
    if _IS_HINT_RE.search(raw) or _IS_HINT_RE.search(low):
        return {"intent": "IS", "reason": "side_effect_hint", "risk": "medium"}
    if _SOHBET_RE.search(raw) or _SOHBET_RE.search(low):
        return {"intent": "SOHBET", "reason": "chat_phrase", "risk": "none"}
    if _SORU_RE.search(raw) or _SORU_RE.search(low):
        return {"intent": "SORU", "reason": "question", "risk": "none"}
    return {"intent": "SORU", "reason": "default_ask", "risk": "none"}


def _masa_is_write(masa: dict[str, Any] | None) -> bool:
    if not isinstance(masa, dict) or masa.get("red"):
        return False
    if masa.get("bak"):
        return False
    eylemler: list[dict[str, Any]] = []
    if isinstance(masa.get("liste"), list):
        eylemler = [x for x in masa["liste"] if isinstance(x, dict)]
    elif masa.get("eylem"):
        eylemler = [masa]
    if not eylemler:
        # tek eylem dict olabilir
        if any(k.startswith("eylem") or k in {"metin", "baslik"} for k in masa):
            eylemler = [masa]
    for e in eylemler:
        ad = str(e.get("eylem") or "")
        if ad in _MASA_READ_EYLEMS:
            continue
        if any(ad.startswith(p) or ad == p.rstrip(".") for p in _MASA_WRITE_PREFIXES):
            return True
        if ad:
            return True
    return False


def _pending_prompt(summary: str) -> str:
    return (
        f"Bu bir iş isteği; sohbet tek başına uygulamam. "
        f"Özet: {summary}. "
        f"Uygulamamı onaylıyor musunuz? «yap» / «yapma»."
    )


def try_handle_sohbet_onay(
    message: str,
    *,
    masa_paket: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Erken kapı. Dönüş:
      None → normal sohbet devam
      dict → instant yanıt (reply, optional masa, orch meta)
    """
    if not enabled():
        return None

    raw = (message or "").strip()
    pending = load_pending()

    # Onay / red
    if pending and _APPROVE_RE.match(raw):
        kind = str(pending.get("kind") or "")
        masa = pending.get("masa") if isinstance(pending.get("masa"), dict) else None
        clear_pending()
        audit("approved", {"kind": kind, "summary": pending.get("summary")})
        if kind == "masa" and masa:
            return {
                "reply": "Onay alındı — masa işi uygulanıyor.",
                "masa": masa,
                "orch": {
                    "plan": {"primary": "sohbet_onay", "label_tr": "Onay kapısı · uygulandı"},
                    "sohbet_onay": {"version": VERSION, "status": "applied", "kind": kind},
                },
            }
        return {
            "reply": (
                "Onay kaydedildi. Bu iş türü henüz otomatik uygulanmıyor; "
                "Mimar emriyle ilgili motor/adımda yapılır."
            ),
            "masa": None,
            "orch": {
                "plan": {"primary": "sohbet_onay", "label_tr": "Onay kapısı · kaydedildi"},
                "sohbet_onay": {"version": VERSION, "status": "approved_no_auto", "kind": kind},
            },
        }

    if pending and _REJECT_RE.match(raw):
        kind = str(pending.get("kind") or "")
        clear_pending()
        audit("rejected", {"kind": kind, "summary": pending.get("summary")})
        return {
            "reply": "Tamam — uygulamadım, bekleyen iş iptal.",
            "masa": None,
            "orch": {
                "plan": {"primary": "sohbet_onay", "label_tr": "Onay kapısı · iptal"},
                "sohbet_onay": {"version": VERSION, "status": "rejected", "kind": kind},
            },
        }

    intent = classify_intent(raw)

    if intent["intent"] == "YASAK":
        audit("blocked_yasak", {"message": raw[:200]})
        return {
            "reply": (
                "Bunu yapamam — tehlikeli / yasak istek. "
                "Sohbet ≠ iş; böyle bir yan etki onaysız ve çoğu zaman hiç açılmaz."
            ),
            "masa": None,
            "orch": {
                "plan": {"primary": "sohbet_onay", "label_tr": "Onay kapısı · yasak"},
                "sohbet_onay": {"version": VERSION, "status": "blocked", "intent": intent},
            },
        }

    # Masa yazma → onay kuyruğu (okuma serbest)
    if masa_paket and masa_paket.get("masa") and not masa_paket.get("red"):
        masa = masa_paket["masa"]
        if _masa_is_write(masa if isinstance(masa, dict) else None):
            summary = "masa yazma/çizim/sunum/temizlik"
            eylem = ""
            if isinstance(masa, dict):
                eylem = str(masa.get("eylem") or "")
                if not eylem and isinstance(masa.get("liste"), list) and masa["liste"]:
                    eylem = str((masa["liste"][0] or {}).get("eylem") or "")
            if eylem:
                summary = f"masa · {eylem}"
            save_pending(
                {
                    "kind": "masa",
                    "summary": summary,
                    "masa": masa,
                    "source_message": raw[:500],
                    "intent": "IS",
                }
            )
            return {
                "reply": _pending_prompt(summary),
                "masa": None,  # uygulamadan önce masa yok
                "orch": {
                    "plan": {"primary": "sohbet_onay", "label_tr": "Onay kapısı · bekliyor"},
                    "sohbet_onay": {
                        "version": VERSION,
                        "status": "pending",
                        "kind": "masa",
                        "summary": summary,
                        "intent": intent,
                    },
                },
            }
        # okuma / bak — serbest
        return None

    # Genel IS ipucu (masa değil) — onay iste, otomatik uygulama yok
    if intent["intent"] == "IS":
        summary = raw[:160]
        save_pending(
            {
                "kind": "genel_is",
                "summary": summary,
                "source_message": raw[:500],
                "intent": "IS",
            }
        )
        return {
            "reply": _pending_prompt(summary),
            "masa": None,
            "orch": {
                "plan": {"primary": "sohbet_onay", "label_tr": "Onay kapısı · bekliyor"},
                "sohbet_onay": {
                    "version": VERSION,
                    "status": "pending",
                    "kind": "genel_is",
                    "summary": summary,
                    "intent": intent,
                },
            },
        }

    return None


def public_status() -> dict[str, Any]:
    pend = load_pending()
    return {
        "enabled": enabled(),
        "version": VERSION,
        "pending": bool(pend),
        "pending_summary": (pend or {}).get("summary"),
        "pending_kind": (pend or {}).get("kind"),
    }
