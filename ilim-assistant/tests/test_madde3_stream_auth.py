"""Madde 3.6 — SSE/WS kimlik kapısı (stream_auth_gate) birim testleri."""

from __future__ import annotations

import pytest

from ilim_assistant import ruzgar_kapsam as kapsam
import ilim_assistant.ruzgar_mobil_oturum as mo

AUTHS = {
    "tok-ok": {"kullanici": "ali", "device_id": "tel-1", "motors": {"sohbet": True}, "ns": "u:ali"},
    "tok-acl": {"kullanici": "veli", "device_id": "tel-2", "motors": {"sohbet": False}, "ns": "u:veli"},
}


@pytest.fixture(autouse=True)
def _izole(monkeypatch):
    monkeypatch.delenv("RUZGAR_STREAM_AUTH", raising=False)
    monkeypatch.delenv("RUZGAR_STREAM_SLOT", raising=False)
    monkeypatch.setattr(mo, "validate_token", lambda t: AUTHS.get(t))
    monkeypatch.setattr(mo, "_active_chats", {})
    monkeypatch.setattr(mo, "_CONCURRENT_YAZI", 2)
    yield


def test_token_yok_masaustu_aynen_gecer():
    for t in (None, "", "   "):
        g = kapsam.stream_auth_gate(t)
        assert g == {"ok": True, "auth": None, "slot": None}
    assert mo._active_chats == {}  # kuyruğa hiç dokunmaz


def test_gecersiz_token_acik_hata():
    g = kapsam.stream_auth_gate("sahte")
    assert g["ok"] is False and g["code"] == "oturum_gecersiz"
    # /api/chat/full ile aynı mesaj
    assert g["error"] == "Oturum geçersiz veya süresi dolmuş. PWA'dan tekrar giriş."
    assert mo._active_chats == {}


def test_acl_kapali_motor_reddedilir():
    g = kapsam.stream_auth_gate("tok-acl")
    assert g["ok"] is False and g["code"] == "motor_acl"
    assert "ACL" in g["error"]
    assert mo._active_chats == {}


def test_gecerli_token_yuva_alir_ve_birakir():
    g = kapsam.stream_auth_gate("tok-ok")
    assert g["ok"] and g["auth"]["kullanici"] == "ali" and g["slot"]
    assert len(mo._active_chats) == 1
    kapsam.stream_auth_release(g)
    assert mo._active_chats == {}
    # idempotent
    kapsam.stream_auth_release(g)
    kapsam.stream_auth_release(None)


def test_kuyruk_tavani_acik_hata_ve_yuva_sizmaz(monkeypatch):
    # tavan 2: iki farklı oturum yuvası dolu → üçüncü reddedilir
    AUTHS["tok-b"] = {"kullanici": "b", "device_id": "x", "motors": {"sohbet": True}, "ns": "u:b"}
    AUTHS["tok-c"] = {"kullanici": "c", "device_id": "y", "motors": {"sohbet": True}, "ns": "u:c"}
    try:
        a = kapsam.stream_auth_gate("tok-ok")
        b = kapsam.stream_auth_gate("tok-b")
        c = kapsam.stream_auth_gate("tok-c")
        assert a["ok"] and b["ok"]
        assert c["ok"] is False and c["code"] == "kuyruk" and c.get("queue")
        kapsam.stream_auth_release(a)
        assert kapsam.stream_auth_gate("tok-c")["ok"]
    finally:
        AUTHS.pop("tok-b", None)
        AUTHS.pop("tok-c", None)


def test_slot_kapali_kuyruk_uygulanmaz(monkeypatch):
    monkeypatch.setenv("RUZGAR_STREAM_SLOT", "0")
    g = kapsam.stream_auth_gate("tok-ok")
    assert g["ok"] and g["slot"] is None and mo._active_chats == {}


def test_auth_kapali_eski_davranis(monkeypatch):
    monkeypatch.setenv("RUZGAR_STREAM_AUTH", "0")
    for t in ("sahte", "tok-acl", "tok-ok"):
        g = kapsam.stream_auth_gate(t)
        assert g == {"ok": True, "auth": None, "slot": None}
    assert mo._active_chats == {}


def test_hata_olaylari_error_ve_done():
    g = kapsam.stream_auth_gate("sahte")
    evs = kapsam.stream_auth_error_events(g, "  merhaba ")
    assert [e["type"] for e in evs] == ["error", "done"]
    assert evs[0]["text"] == g["error"] and evs[0]["auth_error"] is True
    assert evs[1]["full_reply"] == g["error"] and evs[1]["user_message"] == "merhaba"
    assert evs[1]["stream_error"] is True


def test_kapsam_ile_tutarli_gecerli_token_kapsami():
    # kapı geçen token'ın kapsamı da u:<kullanici>|d:<cihaz> olmalı (tutarlılık)
    s = kapsam.resolve_scope("tok-ok")
    assert s.key == "u:ali|d:tel-1" and s.authed
