# Created by Ümit & Gökçenur
"""
Motor A — Hafıza odaları (plan: oda / pin / hatırla).

Komutlar:
  oda aç: İlim
  oda: İlim
  odaya yaz: İlim | not metni
  odaya pin: İlim
  oda listesi
  oda kapat
Kapat: RUZGAR_HAFIZA_ODA=0
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

VERSION = "hafiza-oda-v1-2026-11-09"
_STORE = "hafiza_odalari.json"
_ACTIVE = "hafiza_oda_aktif.txt"


def enabled() -> bool:
    return os.environ.get("RUZGAR_HAFIZA_ODA", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _root() -> Path:
    d = Path(__file__).resolve().parents[1] / ".ruzgar"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _path() -> Path:
    return _root() / _STORE


def _active_path() -> Path:
    return _root() / _ACTIVE


def _load() -> dict[str, Any]:
    p = _path()
    if not p.is_file():
        return {"odalar": {}, "version": VERSION}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"odalar": {}, "version": VERSION}
    if not isinstance(data, dict):
        return {"odalar": {}, "version": VERSION}
    data.setdefault("odalar", {})
    return data


def _save(data: dict[str, Any]) -> None:
    data["version"] = VERSION
    data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = _path().with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, _path())


def _slug(name: str) -> str:
    t = re.sub(r"\s+", " ", (name or "").strip())
    return t[:80]


def get_active() -> str | None:
    p = _active_path()
    if not p.is_file():
        return None
    try:
        v = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return v or None


def set_active(name: str | None) -> None:
    p = _active_path()
    if not name:
        try:
            if p.is_file():
                p.unlink()
        except OSError:
            pass
        return
    p.write_text(name.strip() + "\n", encoding="utf-8")


def public_status() -> dict[str, Any]:
    data = _load()
    odalar = data.get("odalar") or {}
    return {
        "enabled": enabled(),
        "version": VERSION,
        "oda_sayisi": len(odalar),
        "aktif": get_active(),
        "odalar": sorted(odalar.keys()),
    }


def open_room(name: str) -> dict[str, Any]:
    name = _slug(name)
    if not name:
        return {"ok": False, "error": "oda adı boş"}
    data = _load()
    if name not in data["odalar"]:
        data["odalar"][name] = {
            "created_at": time.time(),
            "notes": [],
            "pins": [],
        }
        _save(data)
        created = True
    else:
        created = False
    set_active(name)
    return {"ok": True, "oda": name, "created": created, "aktif": True}


def list_rooms() -> list[dict[str, Any]]:
    data = _load()
    aktif = get_active()
    out = []
    for name, room in (data.get("odalar") or {}).items():
        out.append(
            {
                "oda": name,
                "notes": len(room.get("notes") or []),
                "pins": len(room.get("pins") or []),
                "aktif": name == aktif,
            }
        )
    return sorted(out, key=lambda x: x["oda"].casefold())


def write_note(name: str, text: str) -> dict[str, Any]:
    name = _slug(name)
    text = (text or "").strip()
    if not name or not text:
        return {"ok": False, "error": "oda veya not boş"}
    data = _load()
    if name not in data["odalar"]:
        data["odalar"][name] = {"created_at": time.time(), "notes": [], "pins": []}
    data["odalar"][name].setdefault("notes", []).append(
        {"ts": time.time(), "text": text[:4000]}
    )
    # en fazla 200 not
    data["odalar"][name]["notes"] = data["odalar"][name]["notes"][-200:]
    _save(data)
    set_active(name)
    # genel hafızaya da ince köprü
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        get_hafiza_motor().ekle_bilgi(
            f"Oda:{name}: {text[:80]}",
            text[:1500],
            motor_tipi="Hafıza",
        )
    except Exception:
        pass
    return {"ok": True, "oda": name, "notes": len(data["odalar"][name]["notes"])}


def pin_latest_to_room(name: str, text: str = "") -> dict[str, Any]:
    name = _slug(name)
    data = _load()
    if name not in data["odalar"]:
        data["odalar"][name] = {"created_at": time.time(), "notes": [], "pins": []}
    body = (text or "").strip()
    if not body:
        # son asistan cevabı kuvve'den
        try:
            from ilim_assistant.kuvve_hafiza import get_last_exchange_summary, list_sohbet

            _u, a = get_last_exchange_summary()
            if a and str(a).strip():
                body = str(a).strip()[:4000]
            if not body:
                for t in reversed(list_sohbet(limit=8) or []):
                    if (t.get("role") or "") == "assistant" and (t.get("content") or "").strip():
                        body = str(t.get("content") or "").strip()[:4000]
                        break
        except Exception:
            body = ""
    if not body:
        return {"ok": False, "error": "pinlenecek metin yok"}
    data["odalar"][name].setdefault("pins", []).append(
        {"ts": time.time(), "text": body}
    )
    data["odalar"][name]["pins"] = data["odalar"][name]["pins"][-100:]
    _save(data)
    set_active(name)
    return {"ok": True, "oda": name, "pins": len(data["odalar"][name]["pins"])}


def room_context(limit: int = 6) -> str:
    """Aktif oda not/pin özeti — sohbet bağlamı."""
    if not enabled():
        return ""
    aktif = get_active()
    if not aktif:
        return ""
    data = _load()
    room = (data.get("odalar") or {}).get(aktif) or {}
    notes = list(room.get("notes") or [])[-limit:]
    pins = list(room.get("pins") or [])[-3:]
    lines = [f"[Aktif hafıza odası: {aktif}]"]
    for n in notes:
        lines.append(f"· {str(n.get('text') or '')[:220]}")
    for p in pins:
        lines.append(f"★ {str(p.get('text') or '')[:220]}")
    return "\n".join(lines) if len(lines) > 1 else ""


def try_consume_oda_command(message: str) -> str | None:
    if not enabled():
        return None
    raw = (message or "").strip()
    if not raw or len(raw) > 2000:
        return None

    if re.match(r"(?is)^oda\s+listesi\s*$", raw):
        rooms = list_rooms()
        if not rooms:
            return "Henüz oda yok. `oda aç: İlim` ile başlayın."
        lines = ["Hafıza odaları:"]
        for r in rooms:
            star = " ★" if r.get("aktif") else ""
            lines.append(
                f"· {r['oda']}{star} — not {r['notes']} · pin {r['pins']}"
            )
        return "\n".join(lines)

    if re.match(r"(?is)^oda\s+kapat\s*$", raw):
        set_active(None)
        return "Aktif oda kapatıldı."

    m = re.match(r"(?is)^oda\s+a[cç]\s*[:\-–]?\s*(.+)$", raw)
    if m:
        r = open_room(m.group(1))
        if not r.get("ok"):
            return f"Oda açılamadı: {r.get('error')}"
        verb = "açıldı" if r.get("created") else "seçildi"
        return f"Oda {verb}: «{r['oda']}» (aktif)."

    m = re.match(r"(?is)^oda\s*[:\-–]\s*(.+)$", raw)
    if m:
        name = _slug(m.group(1))
        data = _load()
        if name not in (data.get("odalar") or {}):
            return open_room(name).get("oda") and f"Oda yoktu; oluşturup seçtim: «{name}»."
        set_active(name)
        return f"Aktif oda: «{name}»."

    m = re.match(r"(?is)^odaya\s+yaz\s*[:\-–]?\s*(.+?)\s*[|｜]\s*(.+)$", raw)
    if m:
        r = write_note(m.group(1), m.group(2))
        if not r.get("ok"):
            return f"Yazılamadı: {r.get('error')}"
        return f"«{r['oda']}» odasına yazıldı (toplam not: {r['notes']})."

    m = re.match(r"(?is)^odaya\s+pin\s*[:\-–]?\s*(.+)$", raw)
    if m:
        r = pin_latest_to_room(m.group(1))
        if not r.get("ok"):
            return f"Pinlenemedi: {r.get('error')}"
        return f"Son cevap «{r['oda']}» odasına pinlendi (pin: {r['pins']})."

    # aktif odaya kısa yaz: "odaya: metin"
    m = re.match(r"(?is)^odaya\s*[:\-–]\s*(.+)$", raw)
    if m:
        aktif = get_active()
        if not aktif:
            return "Aktif oda yok. Önce `oda aç: İsim`."
        r = write_note(aktif, m.group(1))
        if not r.get("ok"):
            return f"Yazılamadı: {r.get('error')}"
        return f"«{aktif}» odasına yazıldı."

    return None
