# Created by Ümit & Gökçenur
"""
Mobil Yönetim — oturum + panel iskeleti (plan 11 / Ana sıra Adım 2).

Varsayılan: yerel dosya + token. Halka açılış / Tailscale ayrı kurulum.
Kapat: RUZGAR_MOBIL_OTURUM=0
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any

VERSION = "mobil-oturum-v2-2026-11-09"
_TTL_SEC = 60 * 60 * 24 * 30  # 30 gün — «bir kez giriş»
_STORE = "mobil_oturum_store.json"
_DEFAULT_MOTORS = {
    "sohbet": True,
    "ses": False,
    "video": False,
    "okuma": False,
    "mimar": False,
    "tercume": False,
    "programlama": False,
    "hafiza": False,
}
_CONCURRENT_YAZI = int(os.environ.get("RUZGAR_MOBIL_CONCURRENT_YAZI", "8") or "8")
_active_lock = threading.Lock()
_active_chats: dict[str, float] = {}


def enabled() -> bool:
    return os.environ.get("RUZGAR_MOBIL_OTURUM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def require_auth_for_remote() -> bool:
    """LAN/Tailscale dışı zorunlu kimlik — varsayılan açık."""
    return os.environ.get("RUZGAR_MOBIL_REQUIRE_AUTH", "1").strip().lower() not in (
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


def _load() -> dict[str, Any]:
    p = _path()
    if not p.is_file():
        return {
            "users": {},
            "sessions": {},
            "pending": {},
            "admins": [],
            "root_devices": [],
            "recovery": {},
            "version": VERSION,
        }
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "users": {},
            "sessions": {},
            "pending": {},
            "admins": [],
            "root_devices": [],
            "recovery": {},
            "version": VERSION,
        }
    if not isinstance(data, dict):
        return {
            "users": {},
            "sessions": {},
            "pending": {},
            "admins": [],
            "root_devices": [],
            "recovery": {},
            "version": VERSION,
        }
    for k, default in (
        ("users", {}),
        ("sessions", {}),
        ("pending", {}),
        ("admins", []),
        ("root_devices", []),
        ("recovery", {}),
    ):
        data.setdefault(k, default)
    return data


def _save(data: dict[str, Any]) -> None:
    data["version"] = VERSION
    data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = _path().with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, _path())


def _hash_pw(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def public_status() -> dict[str, Any]:
    data = _load()
    with _active_lock:
        active = sum(1 for t in _active_chats.values() if t > time.time() - 120)
    return {
        "enabled": enabled(),
        "version": VERSION,
        "users": len(data.get("users") or {}),
        "sessions": len(data.get("sessions") or {}),
        "pending": len(data.get("pending") or {}),
        "admins": len(data.get("admins") or []),
        "root_devices": len(data.get("root_devices") or []),
        "has_recovery": bool((data.get("recovery") or {}).get("code_hash")),
        "concurrent_yazi_limit": _CONCURRENT_YAZI,
        "concurrent_active": active,
        "note": "PWA /api/mobil/pwa · Tailscale kurulum ayrı · kök: Mimar PC + telefon.",
    }


def ensure_mimar_admin(kullanici: str = "mimar") -> dict[str, Any]:
    """İlk kurulum: yoksa mimar admin kullanıcı iskeleti (şifre sonra set)."""
    data = _load()
    kullanici = (kullanici or "mimar").strip().lower()
    if kullanici not in data["users"]:
        salt = secrets.token_hex(8)
        # Geçici; set_password veya recovery ile değişir
        pw = os.environ.get("RUZGAR_MIMAR_BOOT_PW", "ruzgar-mimar-degistir")
        data["users"][kullanici] = {
            "ad": "Ümit",
            "soyad": "Haymana",
            "telefon": "",
            "pw_hash": _hash_pw(pw, salt),
            "salt": salt,
            "motors": {**_DEFAULT_MOTORS, "sohbet": True, "hafiza": True, "mimar": True},
            "role": "mimar",
            "created_at": time.time(),
        }
    if kullanici not in data["admins"]:
        data["admins"].append(kullanici)
    data["users"][kullanici]["role"] = "mimar"
    _save(data)
    return {"ok": True, "kullanici": kullanici, "role": "mimar"}


def set_password(kullanici: str, yeni_sifre: str, *, actor: str | None = None) -> dict[str, Any]:
    if not enabled():
        return {"ok": False, "error": "mobil oturum kapalı"}
    kullanici = (kullanici or "").strip().lower()
    if len(yeni_sifre or "") < 4:
        return {"ok": False, "error": "şifre kısa"}
    data = _load()
    user = data["users"].get(kullanici)
    if not user:
        return {"ok": False, "error": "kullanıcı yok"}
    # Kök kural: başka admin mimar şifresini değiştiremez
    if user.get("role") == "mimar" and actor and actor != kullanici and actor != "mimar":
        return {"ok": False, "error": "kök: Mimar şifresine dokunulamaz"}
    salt = secrets.token_hex(8)
    user["pw_hash"] = _hash_pw(yeni_sifre, salt)
    user["salt"] = salt
    _save(data)
    return {"ok": True, "kullanici": kullanici}


def generate_recovery_code() -> dict[str, Any]:
    """PC'de bir kez gösterilir; hash saklanır."""
    code = secrets.token_urlsafe(12)
    salt = secrets.token_hex(8)
    data = _load()
    data["recovery"] = {
        "salt": salt,
        "code_hash": _hash_pw(code, salt),
        "created_at": time.time(),
    }
    _save(data)
    return {"ok": True, "recovery_code": code, "note": "Bu kodu güvenli yere yazın; bir daha gösterilmez."}


def use_recovery_code(code: str, yeni_sifre: str) -> dict[str, Any]:
    data = _load()
    rec = data.get("recovery") or {}
    if not rec.get("code_hash"):
        return {"ok": False, "error": "kurtarma yok"}
    if _hash_pw(code, str(rec.get("salt") or "")) != rec.get("code_hash"):
        return {"ok": False, "error": "kod yanlış"}
    ensure_mimar_admin()
    return set_password("mimar", yeni_sifre, actor="mimar")


def register_request(
    *,
    ad: str,
    soyad: str,
    telefon: str,
    kullanici: str,
    sifre: str,
) -> dict[str, Any]:
    """Onay yöntemi C: kısa kod + Mimar panelinden evet/hayır."""
    if not enabled():
        return {"ok": False, "error": "mobil oturum kapalı"}
    kullanici = (kullanici or "").strip().lower()
    if not kullanici or not sifre or len(sifre) < 4:
        return {"ok": False, "error": "kullanıcı/şifre eksik"}
    if kullanici in ("mimar", "admin", "root"):
        return {"ok": False, "error": "bu kullanıcı adı rezerve"}
    data = _load()
    if kullanici in (data.get("users") or {}):
        return {"ok": False, "error": "kullanıcı zaten var"}
    code = f"{secrets.randbelow(1000000):06d}"
    salt = secrets.token_hex(8)
    pid = secrets.token_hex(8)
    data["pending"][pid] = {
        "ad": (ad or "").strip(),
        "soyad": (soyad or "").strip(),
        "telefon": (telefon or "").strip(),
        "kullanici": kullanici,
        "pw_hash": _hash_pw(sifre, salt),
        "salt": salt,
        "code": code,
        "created_at": time.time(),
    }
    _save(data)
    return {"ok": True, "pending_id": pid, "code": code, "message": "Mimar panelinden onay bekleniyor"}


def approve_pending(pending_id: str, *, code: str, approve: bool, actor: str = "mimar") -> dict[str, Any]:
    if not enabled():
        return {"ok": False, "error": "mobil oturum kapalı"}
    data = _load()
    if actor and actor not in (data.get("admins") or []) and actor != "mimar":
        # henüz admin yoksa lokal PC onayı kabul
        if data.get("admins"):
            return {"ok": False, "error": "yalnız yönetici onaylar"}
    pend = (data.get("pending") or {}).get(pending_id)
    if not pend:
        return {"ok": False, "error": "bekleyen yok"}
    if str(pend.get("code")) != str(code).strip():
        return {"ok": False, "error": "kod uyuşmadı"}
    del data["pending"][pending_id]
    if not approve:
        _save(data)
        return {"ok": True, "status": "rejected"}
    kullanici = pend["kullanici"]
    data["users"][kullanici] = {
        "ad": pend.get("ad"),
        "soyad": pend.get("soyad"),
        "telefon": pend.get("telefon"),
        "pw_hash": pend.get("pw_hash"),
        "salt": pend.get("salt"),
        "motors": dict(_DEFAULT_MOTORS),
        "role": "user",
        "created_at": time.time(),
    }
    _save(data)
    return {"ok": True, "status": "approved", "kullanici": kullanici}


_DEVICE_KINDS = ("telefon", "tablet", "dizustu")


def login(
    kullanici: str,
    sifre: str,
    *,
    device_name: str = "",
    device_id: str = "",
    device_kind: str = "",
) -> dict[str, Any]:
    if not enabled():
        return {"ok": False, "error": "mobil oturum kapalı"}
    ensure_mimar_admin()
    kullanici = (kullanici or "").strip().lower()
    data = _load()
    user = (data.get("users") or {}).get(kullanici)
    if not user:
        return {"ok": False, "error": "kullanıcı yok / onaylanmamış"}
    if _hash_pw(sifre, str(user.get("salt") or "")) != user.get("pw_hash"):
        return {"ok": False, "error": "şifre yanlış"}
    kind = (device_kind or "").strip().lower().replace("ı", "i")
    if kind in ("dizüstü", "laptop", "pc"):
        kind = "dizustu"
    if kind not in _DEVICE_KINDS:
        # isimden tahmin
        dn = (device_name or "").lower()
        if "tablet" in dn:
            kind = "tablet"
        elif "dizustu" in dn or "dizüstü" in dn or "laptop" in dn:
            kind = "dizustu"
        else:
            kind = "telefon"
    name = (device_name or "").strip()[:80] or kind
    token = secrets.token_urlsafe(32)
    data["sessions"][token] = {
        "kullanici": kullanici,
        "device_name": name,
        "device_id": (device_id or "").strip()[:80],
        "device_kind": kind,
        "created_at": time.time(),
        "expires_at": time.time() + _TTL_SEC,
    }
    # Yönetici cihaz kaydı (telefon / tablet / dizüstü üçlüsü)
    role = user.get("role") or "user"
    if role in ("mimar", "admin") and device_id:
        roots = list(data.get("root_devices") or [])
        entry = {
            "device_id": device_id,
            "device_name": name,
            "device_kind": kind,
            "kullanici": kullanici,
            "updated_at": time.time(),
        }
        if role == "mimar":
            entry["root"] = True
        # Aynı türde tek slot (üçlü): eski kaydı güncelle
        replaced = False
        for i, r in enumerate(roots):
            if r.get("device_id") == device_id or (
                r.get("kullanici") == kullanici and r.get("device_kind") == kind
            ):
                roots[i] = {**r, **entry}
                replaced = True
                break
        if not replaced:
            roots.append(entry)
        data["root_devices"] = roots
    _save(data)
    return {
        "ok": True,
        "token": token,
        "expires_at": data["sessions"][token]["expires_at"],
        "kullanici": kullanici,
        "role": role,
        "motors": user.get("motors") or dict(_DEFAULT_MOTORS),
        "is_admin": kullanici in (data.get("admins") or []) or role == "mimar",
        "device_kind": kind,
    }


def logout(token: str) -> dict[str, Any]:
    data = _load()
    if token in (data.get("sessions") or {}):
        del data["sessions"][token]
        _save(data)
        return {"ok": True, "status": "logged_out"}
    return {"ok": True, "status": "already_gone"}


def kick_session(*, token_prefix: str = "", kullanici: str = "", actor: str = "mimar") -> dict[str, Any]:
    data = _load()
    if actor not in (data.get("admins") or []) and actor != "mimar":
        return {"ok": False, "error": "yetki yok"}
    removed = 0
    for tok, s in list((data.get("sessions") or {}).items()):
        hit = False
        if token_prefix and tok.startswith(token_prefix):
            hit = True
        if kullanici and s.get("kullanici") == kullanici.strip().lower():
            hit = True
        if hit:
            # Kök: mimar oturumunu başka admin düşüremez
            if s.get("kullanici") == "mimar" and actor != "mimar":
                continue
            del data["sessions"][tok]
            removed += 1
    _save(data)
    return {"ok": True, "removed": removed}


def validate_token(token: str) -> dict[str, Any] | None:
    if not token:
        return None
    data = _load()
    sess = (data.get("sessions") or {}).get(token)
    if not sess:
        return None
    if float(sess.get("expires_at") or 0) < time.time():
        del data["sessions"][token]
        _save(data)
        return None
    user = (data.get("users") or {}).get(sess.get("kullanici") or "")
    role = (user or {}).get("role") or "user"
    return {
        "kullanici": sess.get("kullanici"),
        "role": role,
        "motors": (user or {}).get("motors") or dict(_DEFAULT_MOTORS),
        "device_name": sess.get("device_name"),
        "device_id": sess.get("device_id"),
        "is_admin": sess.get("kullanici") in (data.get("admins") or []) or role == "mimar",
    }


def set_motor_acl(kullanici: str, motors: dict[str, bool], *, actor: str = "mimar") -> dict[str, Any]:
    data = _load()
    if actor not in (data.get("admins") or []) and actor != "mimar":
        return {"ok": False, "error": "yetki yok"}
    kullanici = (kullanici or "").strip().lower()
    user = data["users"].get(kullanici)
    if not user:
        return {"ok": False, "error": "kullanıcı yok"}
    if user.get("role") == "mimar" and actor != "mimar":
        return {"ok": False, "error": "kök: Mimar motorlarına dokunulamaz"}
    cur = dict(user.get("motors") or _DEFAULT_MOTORS)
    for k, v in (motors or {}).items():
        if k in _DEFAULT_MOTORS:
            cur[k] = bool(v)
    user["motors"] = cur
    _save(data)
    return {"ok": True, "kullanici": kullanici, "motors": cur}


def set_admin(kullanici: str, *, make: bool, actor: str = "mimar") -> dict[str, Any]:
    data = _load()
    if actor != "mimar":
        return {"ok": False, "error": "yalnız Mimar yönetici atar/düşürür"}
    kullanici = (kullanici or "").strip().lower()
    if kullanici == "mimar":
        return {"ok": False, "error": "Mimar düşürülemez"}
    if kullanici not in data["users"]:
        return {"ok": False, "error": "kullanıcı yok"}
    admins = list(data.get("admins") or [])
    if make:
        if kullanici not in admins:
            admins.append(kullanici)
        data["users"][kullanici]["role"] = "admin"
    else:
        admins = [a for a in admins if a != kullanici]
        data["users"][kullanici]["role"] = "user"
    data["admins"] = admins
    _save(data)
    return {"ok": True, "kullanici": kullanici, "admin": make}


def list_users() -> list[dict[str, Any]]:
    data = _load()
    out = []
    for k, u in (data.get("users") or {}).items():
        out.append(
            {
                "kullanici": k,
                "ad": u.get("ad"),
                "soyad": u.get("soyad"),
                "telefon": u.get("telefon"),
                "role": u.get("role"),
                "motors": u.get("motors"),
            }
        )
    return out


def list_pending() -> list[dict[str, Any]]:
    data = _load()
    out = []
    for pid, p in (data.get("pending") or {}).items():
        out.append(
            {
                "pending_id": pid,
                "ad": p.get("ad"),
                "soyad": p.get("soyad"),
                "telefon": p.get("telefon"),
                "kullanici": p.get("kullanici"),
                "code": p.get("code"),
                "created_at": p.get("created_at"),
            }
        )
    return out


def list_sessions() -> list[dict[str, Any]]:
    data = _load()
    out = []
    now = time.time()
    for tok, s in list((data.get("sessions") or {}).items()):
        if float(s.get("expires_at") or 0) < now:
            continue
        out.append(
            {
                "token_prefix": tok[:8],
                "kullanici": s.get("kullanici"),
                "device_name": s.get("device_name"),
                "device_id": s.get("device_id"),
                "device_kind": s.get("device_kind") or "",
                "expires_at": s.get("expires_at"),
            }
        )
    return out


def list_root_devices() -> list[dict[str, Any]]:
    data = _load()
    rows = list(data.get("root_devices") or [])
    # Üçlü vitrin: telefon / tablet / dizustu — boş slotlar da görünsün
    by_kind: dict[str, dict[str, Any]] = {}
    for r in rows:
        k = str(r.get("device_kind") or "").strip().lower() or "telefon"
        if k not in _DEVICE_KINDS:
            k = "telefon"
        by_kind[k] = r
    out: list[dict[str, Any]] = []
    for k in _DEVICE_KINDS:
        if k in by_kind:
            out.append({**by_kind[k], "slot": k, "filled": True})
        else:
            out.append({"slot": k, "device_kind": k, "filled": False})
    return out


def begin_chat_slot(token: str | None) -> dict[str, Any]:
    """Eşzamanlı yazı tavanı (plan 9.2)."""
    key = token or f"anon:{threading.get_ident()}"
    with _active_lock:
        now = time.time()
        dead = [k for k, t in _active_chats.items() if t < now - 180]
        for k in dead:
            _active_chats.pop(k, None)
        if len(_active_chats) >= _CONCURRENT_YAZI and key not in _active_chats:
            return {
                "ok": False,
                "error": "kuyruk",
                "message": f"Eşzamanlı yazı tavanı ({_CONCURRENT_YAZI}). Biraz sonra tekrar.",
            }
        _active_chats[key] = now
    return {"ok": True, "slot": key}


def end_chat_slot(slot: str | None) -> None:
    if not slot:
        return
    with _active_lock:
        _active_chats.pop(slot, None)


def motor_allowed(auth: dict[str, Any] | None, motor: str) -> bool:
    if auth is None:
        return True  # lokal PC sohbet (token yok)
    motors = auth.get("motors") or {}
    if motor == "genel" or motor == "sohbet":
        return bool(motors.get("sohbet", True))
    return bool(motors.get(motor, False))
