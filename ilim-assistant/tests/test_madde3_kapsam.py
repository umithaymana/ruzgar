"""Madde 3 — PC / mobil / kullanıcı izolasyonu (kapsam)."""

from __future__ import annotations

import asyncio
import json

import pytest

from ilim_assistant import ana_motor_sohbet_gecmis as gecmis
from ilim_assistant import ruzgar_kapsam as kapsam
from ilim_assistant import ruzgar_tek_beyin_ozet as ozet

SORU = "Osmanlı Devleti hangi yıl kuruldu ve kim kurdu"
CEVAP = (
    "Osmanlı Devleti, 1299 civarında Osman Bey tarafından Söğüt çevresinde kuruldu; "
    "daha sonra üç kıtaya yayılan bir imparatorluğa dönüştü."
)

TOKENS = {
    "tok-tel": {"kullanici": "ali", "device_id": "tel-1"},
    "tok-tab": {"kullanici": "ali", "device_id": "tab-1"},
    "tok-veli": {"kullanici": "veli", "device_id": "tel-1"},
    "tok-nodev": {"kullanici": "ali", "device_id": ""},
}


@pytest.fixture(autouse=True)
def _izole(tmp_path, monkeypatch):
    monkeypatch.setattr(gecmis, "_HISTORY_PATH", tmp_path / "hist.jsonl")
    monkeypatch.setattr(ozet, "_CACHE_PATH", tmp_path / "ozet.json")
    monkeypatch.delenv("RUZGAR_KAPSAM", raising=False)
    monkeypatch.delenv("RUZGAR_KAPSAM_LEGACY", raising=False)
    monkeypatch.delenv("RUZGAR_RUZGAR_PRESERVE", raising=False)

    import ilim_assistant.ruzgar_mobil_oturum as mo

    monkeypatch.setattr(mo, "validate_token", lambda t: TOKENS.get(t))
    # her test temiz bağlam
    kapsam._current.set(None)
    kapsam._pending.set(None)
    yield
    kapsam._current.set(None)
    kapsam._pending.set(None)


def _as(token: str | None, conv: str = "") -> kapsam.ChatScope:
    return kapsam.bind_scope(
        kapsam.resolve_scope(token, conversation_id=conv)
    )


# ── kimlik çözümü ─────────────────────────────────────────────────────────


def test_token_yok_pc():
    s = kapsam.resolve_scope(None)
    assert s.key == "pc" and s.is_pc


def test_gecerli_token_kullanici_ve_cihaz():
    a = kapsam.resolve_scope("tok-tel")
    b = kapsam.resolve_scope("tok-tab")
    c = kapsam.resolve_scope("tok-veli")
    assert a.key == "u:ali|d:tel-1"
    assert b.key == "u:ali|d:tab-1"
    # aynı cihaz kimliği ama farklı kullanıcı → farklı kapsam
    assert c.key == "u:veli|d:tel-1"
    assert len({a.key, b.key, c.key}) == 3
    assert not a.is_pc


def test_gecersiz_token_pc_olmaz():
    s = kapsam.resolve_scope("sahte-token")
    assert s.key.startswith("anon:") and not s.is_pc


def test_cihazsiz_token_oturuma_baglanir():
    s = kapsam.resolve_scope("tok-nodev")
    assert s.device.startswith("s") and s.key.startswith("u:ali|d:s")


def test_cihaz_ipucu_token_yoksa_pc_degil():
    s = kapsam.resolve_scope(None, device_hint="laptop-9")
    assert s.key == "d:laptop-9" and not s.is_pc


def test_zararli_kimlik_temizlenir():
    s = kapsam.resolve_scope(None, device_hint="../../etc|x y")
    assert "/" not in s.key and " " not in s.key and "|" not in s.key


def test_bind_req_ayni_istek_tekrar_cozmez(monkeypatch):
    calls = {"n": 0}
    orig = kapsam.resolve_scope

    def spy(*a, **k):
        calls["n"] += 1
        return orig(*a, **k)

    monkeypatch.setattr(kapsam, "resolve_scope", spy)

    class Req:
        session_token = "tok-tel"
        device_id = None
        conversation_id = "k1"
        ana_motor_session_id = None

    kapsam.bind_scope_for_request(Req())
    kapsam.bind_scope_for_request(Req())
    assert calls["n"] == 1
    assert kapsam.current_scope().key == "u:ali|d:tel-1"
    assert kapsam.current_scope().conversation == "k1"


# ── arşiv izolasyonu ─────────────────────────────────────────────────────


def test_arsiv_cihaz_izole_okuma():
    _as(None)  # PC
    gecmis.append_chat_turn(user_message="pc sorusu bir", assistant_message="pc cevabı bir uzun")
    _as("tok-tel")
    gecmis.append_chat_turn(user_message="telefon sorusu", assistant_message="telefon cevabı uzun")

    rows_tel = gecmis._load_entries(limit=50)
    assert [r["user"] for r in rows_tel] == ["telefon sorusu"]
    _as("tok-tab")
    assert gecmis._load_entries(limit=50) == []
    _as(None)
    assert [r["user"] for r in gecmis._load_entries(limit=50)] == ["pc sorusu bir"]


def test_satirlara_kapsam_yazilir():
    _as("tok-tel")
    gecmis.append_chat_turn(user_message="deneme sorusu", assistant_message="deneme cevabı uzun")
    row = json.loads(gecmis._HISTORY_PATH.read_text(encoding="utf-8").splitlines()[0])
    assert row["scope"] == "u:ali|d:tel-1"


@pytest.fixture()
def _yanki_acik(monkeypatch):
    # Yankı yolu varsayılanda kapalı (sohbet_tarz_chatgpt); env ile açılırsa da izole olmalı
    import ilim_assistant.prompts as prompts
    import ilim_assistant.ruzgar_anlik_niyet_gate as gate

    monkeypatch.setattr(prompts, "sohbet_tarz_chatgpt", lambda: False)
    monkeypatch.setattr(gate, "library_instant_would_match", lambda m: False)
    monkeypatch.setattr(gate, "should_defer_library_instant", lambda m: False)


def test_yanki_baska_cihazin_cevabini_vermez(_yanki_acik):
    _as(None)
    gecmis.append_chat_turn(user_message=SORU, assistant_message=CEVAP)
    # PC kendi cevabını yanki alabilir (ön koşul: yol gerçekten çalışıyor)
    assert gecmis.try_session_echo_reply(SORU) is not None
    for tok in ("tok-tel", "tok-tab", "tok-veli", "sahte-token"):
        _as(tok)
        assert gecmis.try_session_echo_reply(SORU) is None, tok


def test_yanki_mobilden_pc_ye_sizmaz(_yanki_acik):
    _as("tok-tel")
    gecmis.append_chat_turn(user_message=SORU, assistant_message=CEVAP)
    assert gecmis.try_session_echo_reply(SORU) is not None
    _as(None)
    assert gecmis.try_session_echo_reply(SORU) is None


def test_gecmis_arama_ve_son_turlar_izole():
    _as("tok-tel")
    gecmis.append_chat_turn(user_message="gizli telefon notu", assistant_message="telefon cevabı uzun")
    _as(None)
    assert gecmis.recent_chat_history(limit=20)["count"] == 0
    assert gecmis.search_chat_history("gizli telefon", limit=10).get("count", 0) == 0
    _as("tok-tel")
    assert gecmis.recent_chat_history(limit=20)["count"] == 1


def test_istatistik_yalniz_kendi_satirlari():
    _as(None)
    for i in range(3):
        gecmis.append_chat_turn(user_message=f"pc soru {i}", assistant_message="pc cevap uzun metin")
    _as("tok-tel")
    gecmis.append_chat_turn(user_message="tel soru", assistant_message="tel cevap uzun metin")
    assert gecmis.chat_history_stats()["stored_turns"] == 1
    _as(None)
    assert gecmis.chat_history_stats()["stored_turns"] == 3


def test_temizle_yalniz_kendi_kapsamini_siler():
    _as(None)
    gecmis.append_chat_turn(user_message="pc soru x", assistant_message="pc cevap uzun metin")
    _as("tok-tel")
    gecmis.append_chat_turn(user_message="tel soru x", assistant_message="tel cevap uzun metin")
    res = gecmis.clear_chat_history()
    assert res["ok"] and res["cleared"] == 1
    assert gecmis._load_entries(limit=10) == []
    _as(None)
    assert [r["user"] for r in gecmis._load_entries(limit=10)] == ["pc soru x"]


def test_eski_kapsamsiz_satirlar_varsayilan_yalniz_pc(monkeypatch):
    gecmis._HISTORY_PATH.write_text(
        json.dumps({"ts": 1, "mode": "genel", "user": "eski soru", "assistant": "eski cevap uzun"}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    _as(None)
    assert len(gecmis._load_entries(limit=10)) == 1
    _as("tok-tel")
    assert gecmis._load_entries(limit=10) == []
    monkeypatch.setenv("RUZGAR_KAPSAM_LEGACY", "all")
    assert len(gecmis._load_entries(limit=10)) == 1
    monkeypatch.setenv("RUZGAR_KAPSAM_LEGACY", "none")
    _as(None)
    assert gecmis._load_entries(limit=10) == []


def test_eski_satirlar_silinmez_baska_cihaz_temizleyince():
    gecmis._HISTORY_PATH.write_text(
        json.dumps({"ts": 1, "mode": "genel", "user": "eski", "assistant": "eski cevap uzun"}) + "\n",
        encoding="utf-8",
    )
    _as("tok-tel")
    gecmis.append_chat_turn(user_message="tel soru y", assistant_message="tel cevap uzun metin")
    gecmis.clear_chat_history()
    _as(None)
    assert [r["user"] for r in gecmis._load_entries(limit=10)] == ["eski"]


def test_kapsam_kapaliysa_eski_davranis(monkeypatch):
    monkeypatch.setenv("RUZGAR_KAPSAM", "0")
    _as("tok-tel")
    gecmis.append_chat_turn(user_message="kapali soru", assistant_message="kapali cevap uzun metin")
    row = json.loads(gecmis._HISTORY_PATH.read_text(encoding="utf-8").splitlines()[0])
    assert "scope" not in row
    _as(None)
    assert len(gecmis._load_entries(limit=10)) == 1


def test_kirpma_kapsam_basina_gurultulu_cihaz_digerini_silmez(monkeypatch):
    monkeypatch.setattr(gecmis, "_MAX_STORE", 10)
    monkeypatch.setattr(gecmis, "_TRIM_SLACK", 2)
    _as(None)
    gecmis.append_chat_turn(user_message="pc tek soru", assistant_message="pc cevap uzun metin")
    _as("tok-tel")
    for i in range(40):
        gecmis.append_chat_turn(user_message=f"gurultu {i}", assistant_message="gurultu cevap uzun")
    _as(None)
    assert [r["user"] for r in gecmis._load_entries(limit=50)] == ["pc tek soru"]
    _as("tok-tel")
    n = len(gecmis._load_entries(limit=100))
    assert 10 <= n <= 12


# ── özet önbelleği ───────────────────────────────────────────────────────


def _ozet(text: str) -> dict:
    return {"summary_text": text, "updated_at": 1.0, "turn_count": 9}


def test_ozet_onbellegi_kapsamli():
    _as("tok-tel")
    ozet._save_cache(_ozet("telefon özeti"))
    assert ozet.get_cached_summary()["summary_text"] == "telefon özeti"
    _as(None)
    assert ozet.get_cached_summary() is None
    ozet._save_cache(_ozet("pc özeti"))
    _as("tok-tel")
    assert ozet.get_cached_summary()["summary_text"] == "telefon özeti"
    _as("tok-tab")
    assert ozet.get_cached_summary() is None


def test_eski_duz_ozet_onbellegi_pc_ye_aittir():
    ozet._CACHE_PATH.write_text(
        json.dumps(_ozet("eski düz özet"), ensure_ascii=False), encoding="utf-8"
    )
    _as(None)
    assert ozet.get_cached_summary()["summary_text"] == "eski düz özet"
    _as("tok-tel")
    assert ozet.get_cached_summary() is None
    # yazınca eski PC özeti kaybolmaz
    ozet._save_cache(_ozet("tel yeni"))
    _as(None)
    assert ozet.get_cached_summary()["summary_text"] == "eski düz özet"


def test_ortak_hafizaya_yalniz_pc_yazar():
    _as("tok-tel")
    res = ozet._sync_to_oturum_ozet_hafiza({"summary_text": "x", "topics": []})
    assert res["stored"] is False and res["reason"] == "scope_non_pc"


# ── bağlam yayılımı / eşzamanlılık ───────────────────────────────────────


def test_kapsam_threadpool_a_yayilir():
    import anyio

    async def main():
        _as("tok-tel")
        return await anyio.to_thread.run_sync(lambda: kapsam.current_scope().key)

    assert asyncio.run(main()) == "u:ali|d:tel-1"


def test_eszamanli_istekler_birbirine_sizmaz():
    import anyio

    async def istek(tok, bekle):
        _as(tok)
        await asyncio.sleep(bekle)
        a = kapsam.current_scope().key
        b = await anyio.to_thread.run_sync(lambda: kapsam.current_scope().key)
        return a, b

    async def main():
        return await asyncio.gather(
            istek("tok-tel", 0.05),
            istek("tok-tab", 0.01),
            istek(None, 0.03),
            istek("tok-veli", 0.02),
        )

    out = asyncio.run(main())
    assert out == [
        ("u:ali|d:tel-1", "u:ali|d:tel-1"),
        ("u:ali|d:tab-1", "u:ali|d:tab-1"),
        ("pc", "pc"),
        ("u:veli|d:tel-1", "u:veli|d:tel-1"),
    ]


def test_asgi_ara_katman_bearer_tembel_cozer():
    seen: dict = {}

    async def app(scope, receive, send):
        seen["key"] = kapsam.current_scope().key

    mw = kapsam.KapsamASGIMiddleware(app)

    async def run(headers):
        await mw({"type": "http", "headers": headers}, None, None)

    async def main():
        # Gerçekte her istek ayrı görevdir (uvicorn): önceki Bearer sızmamalı
        await asyncio.create_task(run([(b"authorization", b"Bearer tok-tel")]))
        k1 = seen["key"]
        await asyncio.create_task(run([]))
        k2 = seen["key"]
        return k1, k2

    k1, k2 = asyncio.run(main())
    assert k1 == "u:ali|d:tel-1"
    assert k2 == "pc"


def test_asgi_gecersiz_bearer_pc_gormez():
    seen: dict = {}

    async def app(scope, receive, send):
        seen["key"] = kapsam.current_scope().key

    mw = kapsam.KapsamASGIMiddleware(app)
    asyncio.run(mw({"type": "http", "headers": [(b"authorization", b"Bearer yanlis")]}, None, None))
    assert seen["key"].startswith("anon:")
