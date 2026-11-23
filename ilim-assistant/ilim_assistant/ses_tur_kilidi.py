"""Madde 2 (Sprint E+F) — Tur kilidi (turn_id) + ses telemetrisi.

Amaç
----
* **Tur kilidi (2.4):** istemci her sohbet turuna bir ``turn_id`` verir. Aynı kanalda
  (cihaz) yeni tur başlayınca veya kullanıcı kesince eski turun TTS parçaları
  sunucuda da reddedilir; eski ses yeni cevaba binmez.
* **Telemetri (2.6):** «ilk token» ile «kullanıcının duyduğu ilk ses» AYRI ölçülür.
  Yalnızca sayı/etiket tutulur — **metin, kullanıcı adı, token, cihaz kimliği YOK**.

Bellek-içi, sınırlı (LRU+TTL); disk yazmaz. ``RUZGAR_SES_TUR_KILIDI=0`` ile kilit kapanır
(telemetri açık kalır; ``RUZGAR_SES_TELEMETRI=0`` ile o da kapanır).
"""
from __future__ import annotations

import hashlib
import os
import re
import threading
import time
from collections import OrderedDict, deque
from typing import Any

VERSION = "ses-tur-kilidi-v1-2026-11-23"

_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-]{1,64}$")
_MAX_TURN = 512
_TTL_SEC = 900.0
_TEL_MAX = 400

_lock = threading.RLock()
_turns: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
_aktif: dict[str, str] = {}
_tel: "deque[dict[str, Any]]" = deque(maxlen=_TEL_MAX)
_sayac: dict[str, int] = {
    "tur_basladi": 0,
    "tur_iptal": 0,
    "tts_reddedildi": 0,
    "tts_izinli": 0,
}


def _env_on(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() not in ("0", "false", "no", "off")


def kilit_etkin() -> bool:
    return _env_on("RUZGAR_SES_TUR_KILIDI")


def telemetri_etkin() -> bool:
    return _env_on("RUZGAR_SES_TELEMETRI")


def temiz_id(x: Any) -> str:
    s = str(x or "").strip()
    return s if _ID_RE.match(s) else ""


def kanal_anahtari(device_id: Any = None, token: Any = None) -> str:
    """Cihaz kimliği / token'dan ham sızdırmayan kısa kanal anahtarı (``-`` = kimliksiz/PC)."""
    d = str(device_id or "").strip()
    t = str(token or "").strip()
    src = d or t
    if not src:
        return "pc"
    return "k" + hashlib.sha1(src.encode("utf-8", "ignore")).hexdigest()[:12]


def kanal_etiketi(device_id: Any = None, token: Any = None) -> str:
    """Telemetri etiketi: kimlik varsa ``mobil`` (PWA), yoksa ``pc``."""
    return "mobil" if (str(device_id or "").strip() or str(token or "").strip()) else "pc"


def _budama_locked(now: float) -> None:
    dead = [k for k, v in _turns.items() if now - float(v.get("t") or 0) > _TTL_SEC]
    for k in dead:
        _sil_locked(k)
    while len(_turns) > _MAX_TURN:
        k = next(iter(_turns))
        _sil_locked(k)


def _sil_locked(turn_id: str) -> None:
    rec = _turns.pop(turn_id, None)
    if rec:
        kn = rec.get("kanal")
        if kn and _aktif.get(kn) == turn_id:
            _aktif.pop(kn, None)


def _iptal_locked(turn_id: str, sebep: str) -> bool:
    rec = _turns.get(turn_id)
    if not rec or rec.get("iptal"):
        return False
    rec["iptal"] = True
    rec["sebep"] = str(sebep or "iptal")[:40]
    rec["t_iptal"] = time.time()
    _sayac["tur_iptal"] += 1
    return True


def begin(kanal: str, turn_id: Any, *, sebep_onceki: str = "yeni_tur") -> dict[str, Any]:
    """Yeni tur: aynı kanaldaki önceki tur iptal edilir (barge-in / eski ses susar)."""
    tid = temiz_id(turn_id)
    if not tid or not kilit_etkin():
        return {"ok": True, "turn_id": tid, "onceki_iptal": None, "kilit": False}
    kn = str(kanal or "pc")[:40]
    now = time.time()
    with _lock:
        _budama_locked(now)
        prev = _aktif.get(kn)
        iptal_prev = None
        if prev and prev != tid:
            if _iptal_locked(prev, sebep_onceki):
                iptal_prev = prev
        rec = _turns.get(tid)
        if rec is None:
            _turns[tid] = {"kanal": kn, "t": now, "iptal": False, "sebep": "", "bitti": False}
            _sayac["tur_basladi"] += 1
        else:
            rec["t"] = now
            _turns.move_to_end(tid)
        _aktif[kn] = tid
        _budama_locked(now)
    return {"ok": True, "turn_id": tid, "onceki_iptal": iptal_prev, "kilit": True}


def cancel(
    turn_id: Any = None, kanal: str | None = None, sebep: str = "barge"
) -> list[str]:
    """Belirli turu veya kanalın aktif turunu iptal et. İptal edilen kimlikleri döner."""
    out: list[str] = []
    if not kilit_etkin():
        return out
    tid = temiz_id(turn_id)
    with _lock:
        hedefler: list[str] = []
        if tid:
            hedefler.append(tid)
            if tid not in _turns:
                # Henüz görülmemiş tur iptali (yarış): önceden işaretle ki gelen TTS reddedilsin
                _turns[tid] = {
                    "kanal": str(kanal or "")[:40],
                    "t": time.time(),
                    "iptal": False,
                    "sebep": "",
                    "bitti": False,
                }
        elif kanal:
            a = _aktif.get(str(kanal)[:40])
            if a:
                hedefler.append(a)
        for h in hedefler:
            if _iptal_locked(h, sebep):
                out.append(h)
    return out


def bitir(turn_id: Any) -> None:
    """Sohbet akışı bitti (kaynak serbest bırakma işareti). İptal durumunu silmez."""
    tid = temiz_id(turn_id)
    if not tid:
        return
    with _lock:
        rec = _turns.get(tid)
        if rec:
            rec["bitti"] = True


def durum(turn_id: Any, kanal: str | None = None) -> str:
    """``ok`` | ``iptal`` | ``eski`` — TTS isteği bu tur adına hâlâ çalınabilir mi?"""
    tid = temiz_id(turn_id)
    if not tid or not kilit_etkin():
        return "ok"
    with _lock:
        rec = _turns.get(tid)
        if rec and rec.get("iptal"):
            return "iptal"
        kn = str(kanal or (rec or {}).get("kanal") or "")[:40]
        if kn:
            a = _aktif.get(kn)
            if a and a != tid:
                return "eski"
    return "ok"


def tts_izin(turn_id: Any, kanal: str | None = None) -> tuple[bool, str]:
    st = durum(turn_id, kanal)
    with _lock:
        if st == "ok":
            if temiz_id(turn_id):
                _sayac["tts_izinli"] += 1
        else:
            _sayac["tts_reddedildi"] += 1
    return st == "ok", st


# ---------------------------------------------------------------- telemetri


def _sayi(v: Any, lo: float = 0.0, hi: float = 600_000.0) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f or f < lo or f > hi:
        return None
    return round(f, 1)


def tel_kaydet(
    *,
    kanal: str = "pc",
    kaynak: str = "sunucu",
    ilk_token_ms: Any = None,
    ilk_ses_ms: Any = None,
    tts_ilk_bayt_ms: Any = None,
    ilk_ses_yolu: str | None = None,
    parca: Any = None,
    iptal: bool = False,
) -> dict[str, Any] | None:
    """Tek tur ölçümü. Yalnız sayı + kısa etiket; serbest metin kabul edilmez.

    * ``ilk_token_ms``: mesaj → ilk metin (kaynak ``sunucu`` veya ``istemci``)
    * ``ilk_ses_ms``: mesaj → kullanıcının DUYDUĞU ilk ses (yalnız istemci bilir)
    * ``tts_ilk_bayt_ms``: sunucuda TTS ilk ses baytı
    """
    if not telemetri_etkin():
        return None
    kn = re.sub(r"[^a-z0-9_]", "", str(kanal or "pc").lower())[:12] or "pc"
    ks = re.sub(r"[^a-z0-9_]", "", str(kaynak or "sunucu").lower())[:12] or "sunucu"
    yol = re.sub(r"[^a-z0-9_]", "", str(ilk_ses_yolu or "").lower())[:12] or None
    rec: dict[str, Any] = {
        "t": round(time.time(), 1),
        "kanal": kn,
        "kaynak": ks,
        "ilk_token_ms": _sayi(ilk_token_ms),
        "ilk_ses_ms": _sayi(ilk_ses_ms),
        "tts_ilk_bayt_ms": _sayi(tts_ilk_bayt_ms),
        "ilk_ses_yolu": yol,
        "parca": int(parca) if isinstance(parca, (int, float)) and 0 <= parca < 10_000 else None,
        "iptal": bool(iptal),
    }
    if (
        rec["ilk_token_ms"] is None
        and rec["ilk_ses_ms"] is None
        and rec["tts_ilk_bayt_ms"] is None
        and not rec["iptal"]
    ):
        return None
    with _lock:
        _tel.append(rec)
    return rec


def _yuzdelik(vals: list[float], p: float) -> float | None:
    if not vals:
        return None
    s = sorted(vals)
    i = min(len(s) - 1, max(0, int(round((len(s) - 1) * p))))
    return round(s[i], 1)


def _ozet_alan(rows: list[dict[str, Any]], alan: str) -> dict[str, Any]:
    vals = [float(r[alan]) for r in rows if r.get(alan) is not None]
    return {
        "n": len(vals),
        "p50": _yuzdelik(vals, 0.5),
        "p95": _yuzdelik(vals, 0.95),
        "son": vals[-1] if vals else None,
        "alti_1sn": (round(sum(1 for v in vals if v < 1000.0) / len(vals), 3) if vals else None),
    }


def _ozet_grup(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ilk_token_ms": {
            "sunucu": _ozet_alan([r for r in rows if r.get("kaynak") == "sunucu"], "ilk_token_ms"),
            "istemci": _ozet_alan([r for r in rows if r.get("kaynak") == "istemci"], "ilk_token_ms"),
        },
        "ilk_ses_ms": _ozet_alan(rows, "ilk_ses_ms"),
        "tts_ilk_bayt_ms": _ozet_alan(rows, "tts_ilk_bayt_ms"),
    }


def tel_ozet() -> dict[str, Any]:
    """Küçük özet — ``/api/health/full`` ve ``/api/ses/telemetri`` için."""
    with _lock:
        rows = list(_tel)
        sayac = dict(_sayac)
        aktif_tur = len(_aktif)
        kayitli = len(_turns)
    kanallar: dict[str, Any] = {}
    for kn in sorted({str(r.get("kanal") or "pc") for r in rows}):
        kanallar[kn] = _ozet_grup([r for r in rows if r.get("kanal") == kn])
    return {
        "version": VERSION,
        "kilit": kilit_etkin(),
        "telemetri": telemetri_etkin(),
        "kayit": len(rows),
        **_ozet_grup(rows),
        "kanallar": kanallar,
        "sayac": sayac,
        "aktif_tur": aktif_tur,
        "kayitli_tur": kayitli,
        "son": rows[-5:],
        "not": (
            "ilk_token_ms = mesaj→ilk metin (sunucu/istemci ayrı); "
            "ilk_ses_ms = mesaj→kullanıcının duyduğu ilk ses; "
            "tts_ilk_bayt_ms = sunucu TTS ilk ses baytı. Kişisel veri tutulmaz."
        ),
    }


def sifirla_test() -> None:
    """Yalnız testler için."""
    with _lock:
        _turns.clear()
        _aktif.clear()
        _tel.clear()
        for k in _sayac:
            _sayac[k] = 0
