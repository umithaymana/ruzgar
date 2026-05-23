# Created by Ümit & Gökçenur
"""Uzun öğretim metinlerinden niyet/kavrayış çıkarır; robotik şablon değil doğal yanıt."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Optional

_MOTOR = "Egitim"
_ANLAMA_PREFIX = "anlama:"
_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.I)


def _anlama_enabled() -> bool:
    if os.environ.get("RUZGAR_EGITIM_ANLAMA", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_EGITIM", "1").strip().lower() not in ("0", "false", "no")


def _llm_timeout() -> float:
    try:
        return float(os.environ.get("RUZGAR_EGITIM_LLM_SEC", "14"))
    except ValueError:
        return 14.0


def _looks_like_teaching_narrative(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 55:
        return False
    low = t.lower()
    cues = (
        "istiyorum",
        "anlasın",
        "anlamalı",
        "anlaması",
        "fark",
        "ama ",
        "şayet",
        "sayet",
        "hitap",
        "dersen",
        "cevap ver",
        "sohbet",
        "kanıs",
        "kanis",
        "öğret",
        "ogret",
    )
    return sum(1 for c in cues if c in low) >= 2


def _parse_json_blob(raw: str) -> Optional[dict[str, Any]]:
    t = (raw or "").strip()
    if not t:
        return None
    m = _JSON_FENCE.search(t)
    if m:
        t = m.group(1).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    start = t.find("{")
    end = t.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(t[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _llm_complete(system: str, user: str, *, max_tokens: int = 1800) -> str:
    """Yerel Ollama birincil; bulut yalnızca açıkça etkinse."""
    try:
        from ilim_assistant.llm_ollama import chat_completion

        out = (chat_completion(system, user) or "").strip()
        if out and not out.strip().startswith("["):
            return out
    except Exception:
        pass
    try:
        from ilim_assistant.config import groq_disabled, ollama_only_mode

        if not ollama_only_mode() and not groq_disabled():
            from ilim_assistant.llm_brain import chat_completion_groq

            out = chat_completion_groq(system, user)
            if out and not out.strip().startswith("["):
                return out.strip()
    except Exception:
        pass
    try:
        from ilim_assistant.config import gemini_disabled
        from ilim_assistant.gemini_quota_guard import gemini_cooldown_active
        from ilim_assistant.llm_gemini import chat_completion_gemini, gemini_configured

        if (
            not gemini_disabled()
            and gemini_configured()
            and not gemini_cooldown_active()
        ):
            out = chat_completion_gemini(system, user)
            if out and not out.strip().startswith("["):
                return out.strip()
    except Exception:
        pass
    return ""


def comprehend_teaching_text(
    metin: str,
    *,
    baglam_soru: str = "",
) -> dict[str, Any]:
    """
    Uzun öğretim metninden yapılandırılmış kurallar çıkarır.
    Dönüş: {"ok", "ozet", "kurallar": [...], "ham"}
    """
    metin = (metin or "").strip()
    if not metin:
        return {"ok": False, "ozet": "", "kurallar": [], "ham": ""}

    system = (
        "Sen Rüzgar'ın öğrenme analizcisisin. Ümit abi uzun ve doğal anlatımla öğretir; "
        "sen robotik «X dersen Y» kalıbına çevirme — niyet, bağlam farkı ve Rüzgar'ın "
        "kafasında oluşması gereken kavrayışı çıkar. Türkçe JSON üret."
    )
    user = f"""Bağlam (son kullanıcı mesajı): {(baglam_soru or '(yok)')[:400]}

Ümit abi'nin öğretim metni:
{metin[:3500]}

Yalnızca geçerli JSON (markdown kod çiti yok):
{{
  "ozet": "Ümit abi ne istedi — 1-3 cümle",
  "kurallar": [
    {{
      "id": "kisa_latin_id",
      "tetikleyiciler": ["kullanıcının söyleyeceği kısa ifadeler"],
      "kullanici_niyeti": "Ümit abi bu dediğinde ne kastediyor",
      "ruzgar_kavrayisi": "Rüzgar bunu duyunca ne anlamalı (duygu, bağlam)",
      "yanit_rehberi": "Nasıl cevap vermeli — doğal, kopyala-yapıştır değil",
      "ornek_yanit": "Ton için kısa örnek (birebir zorunlu değil)",
      "digerlerinden_ayir": "Diğer tetikleyicilerden farkı"
    }}
  ]
}}

Örnek ayrım: sadece «selam» ≠ «selam rüzgar» (isimle hitap = kişisel sohbet niyeti).
Her ayrı niyet ayrı kural olsun."""

    raw = _llm_complete(system, user, max_tokens=2000)
    parsed = _parse_json_blob(raw)
    if not parsed or not isinstance(parsed.get("kurallar"), list):
        return {"ok": False, "ozet": "", "kurallar": [], "ham": raw}

    kurallar: list[dict[str, Any]] = []
    for i, row in enumerate(parsed["kurallar"]):
        if not isinstance(row, dict):
            continue
        tid = str(row.get("id") or f"kural_{i+1}").strip()[:40]
        trigs = row.get("tetikleyiciler") or []
        if isinstance(trigs, str):
            trigs = [trigs]
        trigs = [str(x).strip() for x in trigs if str(x).strip()]
        if not trigs:
            continue
        kurallar.append(
            {
                "id": tid,
                "tetikleyiciler": trigs,
                "kullanici_niyeti": str(row.get("kullanici_niyeti") or "").strip(),
                "ruzgar_kavrayisi": str(row.get("ruzgar_kavrayisi") or "").strip(),
                "yanit_rehberi": str(row.get("yanit_rehberi") or "").strip(),
                "ornek_yanit": str(row.get("ornek_yanit") or "").strip(),
                "digerlerinden_ayir": str(row.get("digerlerinden_ayir") or "").strip(),
            }
        )

    ozet = str(parsed.get("ozet") or "").strip()
    return {"ok": bool(kurallar), "ozet": ozet, "kurallar": kurallar, "ham": raw}


def _rule_to_storage(rule: dict[str, Any], raw_teach: str = "") -> str:
    payload = {
        "tip": "anlama",
        "id": rule.get("id"),
        "tetikleyiciler": rule.get("tetikleyiciler") or [],
        "kullanici_niyeti": rule.get("kullanici_niyeti"),
        "ruzgar_kavrayisi": rule.get("ruzgar_kavrayisi"),
        "yanit_rehberi": rule.get("yanit_rehberi"),
        "ornek_yanit": rule.get("ornek_yanit"),
        "digerlerinden_ayir": rule.get("digerlerinden_ayir"),
        "ogretim_ozeti": (raw_teach or "")[:500],
        "ts": time.time(),
    }
    return json.dumps(payload, ensure_ascii=False)


def _parse_stored_rule(cevap: str) -> Optional[dict[str, Any]]:
    c = (cevap or "").strip()
    if not c.startswith("{"):
        return None
    try:
        obj = json.loads(c)
    except json.JSONDecodeError:
        return None
    if obj.get("tip") != "anlama":
        return None
    return obj


def save_understood_rules(
    kurallar: list[dict[str, Any]],
    *,
    raw_teach: str = "",
) -> int:
    """Her kuralı Egitim rafına JSON olarak yazar; her tetikleyici için de indeks."""
    if not kurallar:
        return 0
    from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

    motor = get_hafiza_motor()
    n = 0
    for rule in kurallar:
        blob = _rule_to_storage(rule, raw_teach)
        rid = str(rule.get("id") or "kural").strip()
        motor.ekle_bilgi(f"{_ANLAMA_PREFIX}{rid}", blob, motor_tipi=_MOTOR)
        n += 1
        for trig in rule.get("tetikleyiciler") or []:
            t = str(trig).strip()
            if t and len(t) < 120:
                motor.ekle_bilgi(t, blob, motor_tipi=_MOTOR)
                n += 1
    return n


def _trigger_matches(message: str, trigger: str) -> bool:
    from ilim_assistant.ruzgar_egitim import _trigger_matches as _tm

    return _tm(message, trigger)


def find_matching_rule(message: str) -> Optional[dict[str, Any]]:
    """Kullanıcı mesajına uyan anlama kuralını döner (en özel tetikleyici)."""
    msg = (message or "").strip()
    if not msg or len(msg) > 400:
        return None
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        motor = get_hafiza_motor()
    except Exception:
        return None

    best: tuple[int, int, dict[str, Any]] | None = None
    seen_ids: set[str] = set()

    for row in reversed(motor._kayitlar):
        if row.get("motor_tipi") != _MOTOR:
            continue
        cevap = str(row.get("cevap") or "")
        rule = _parse_stored_rule(cevap)
        if not rule:
            continue
        rid = str(rule.get("id") or "")
        if rid in seen_ids:
            continue
        trigs = rule.get("tetikleyiciler") or []
        for trig in trigs:
            if not _trigger_matches(msg, str(trig)):
                continue
            score = (len(str(trig).split()), len(str(trig)))
            if best is None or score > (best[0], best[1]):
                best = (score[0], score[1], rule)
                seen_ids.add(rid)
            break

    return best[2] if best else None


def synthesize_understood_reply(message: str, rule: dict[str, Any]) -> str:
    """Kavrayışa göre doğal Türkçe yanıt — örnek cümleyi kopyalamadan."""
    msg = (message or "").strip()
    ornek = str(rule.get("ornek_yanit") or "").strip()
    system = (
        "Sen Rüzgar'sın — Ümit abi'nin yerel yapay zeka arkadaşı. Kısa, sıcak, samimi Türkçe. "
        "Robot gibi tekrarlama; «nasıl yardımcı olabilirim» deme."
    )
    user = f"""Ümit abi şunu yazdı: «{msg}»

Öğretilmiş kavrayış (bunu içselleştir, aynen okuma):
- Niyet: {rule.get('kullanici_niyeti', '')}
- Senin anlaman gereken: {rule.get('ruzgar_kavrayisi', '')}
- Nasıl cevap: {rule.get('yanit_rehberi', '')}
- Diğer durumlardan fark: {rule.get('digerlerinden_ayir', '')}
- Ton örneği (kopyala değil, benzer his): {ornek or '(yok)'}

2–5 cümleyle doğal cevap ver. Yalnızca cevap metni."""

    t0 = time.monotonic()
    out = _llm_complete(system, user, max_tokens=380)
    if out and len(out) > 8 and (time.monotonic() - t0) < _llm_timeout() + 2:
        return out.strip()
    if ornek:
        return ornek
    rehber = str(rule.get("yanit_rehberi") or "").strip()
    return rehber[:300] if rehber else ""


def reply_from_understanding(message: str) -> Optional[str]:
    """Anlama kuralı varsa doğal sentez döner."""
    if not _anlama_enabled():
        return None
    try:
        from ilim_assistant.ruzgar_bilissel_analiz import is_anlama_empati_sorusu

        if is_anlama_empati_sorusu(message):
            return None
    except Exception:
        pass
    rule = find_matching_rule(message)
    if not rule:
        return None
    text = synthesize_understood_reply(message, rule)
    return text.strip() if text else None


def save_teaching_with_understanding(
    metin: str,
    *,
    baglam_soru: str = "",
) -> tuple[bool, str]:
    """
    Uzun metni analiz edip kaydeder.
    Dönüş: (başarılı mı, Ümit abi'ye gösterilecek onay metni)
    """
    if not _anlama_enabled():
        return False, ""
    comp = comprehend_teaching_text(metin, baglam_soru=baglam_soru)
    if not comp.get("ok"):
        return False, ""
    n = save_understood_rules(comp["kurallar"], raw_teach=metin)
    if n <= 0:
        return False, ""

    try:
        from ilim_assistant.ruzgar_umed_kurallari import SAVED_TEACH

        lines = [SAVED_TEACH]
    except Exception:
        lines = [
            "Tamam Ümit abi, bunu öğrendim ve hafızama kaydettim.",
        ]
    ozet = str(comp.get("ozet") or "").strip()
    if ozet:
        lines.append(f"Özet: {ozet}")
    for r in comp["kurallar"][:4]:
        tr = ", ".join((r.get("tetikleyiciler") or [])[:3])
        kav = str(r.get("ruzgar_kavrayisi") or "")[:120]
        if tr:
            lines.append(f"• «{tr}» → {kav}")
    return True, "\n".join(lines)
