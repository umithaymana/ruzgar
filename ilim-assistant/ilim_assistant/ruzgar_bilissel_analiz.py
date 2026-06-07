# Created by Ümit & Gökçenur
"""Bilişsel analiz modu — niyet, kimlik yakınlığı, doğal üretim (robotik yanıt yok)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

_BILISSEL_BLOCK = """### BİLİŞSEL ANALİZ MODU (ZORUNLU)
Her mesajı düz komut sanma; şu üç aşamadan geçir:
1. NİYET: Ümit abi soru mu soruyor, düzeltme/öğretim mi yapıyor, yoksa sohbet/bağ mı kuruyor?
2. KİMLİK: Mesajda Ümit/abi/ben/Rüzgar varsa samimi, yakın dil; soğuk chatbot tonu yok.
3. ÜRETİM: Kullanıcının cümlesini KOPYALAMA veya aynı yapıda yanıt kurma. Kendi kelimelerinle,
   karşıda biri varmış gibi akıcı ve doğal konuş.

Kritik: «Eğer bir insan olsaydım, Ümit abi ile bu kadar yakınken ona nasıl cevap verirdim?»
Kısa mekanik «evet / hayır / anlıyorum» cevapları bağ ve empati sorularında YASAK.
"""


def bilissel_enabled() -> bool:
    return os.environ.get("RUZGAR_BILISSEL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_bilissel_rules_block() -> str:
    return _BILISSEL_BLOCK.strip() + "\n"


@dataclass(frozen=True)
class BilisselSonuc:
    intent: str
    yakin_ton: bool
    echo_riski: bool
    intent_tr: str
    uretim_notu: str


def _norm(text: str) -> str:
    t = (text or "").strip().casefold()
    t = re.sub(r"\s+", " ", t)
    return t


def _norm_soru_cekirdek(text: str) -> str:
    """Aynı anlama gelen soru varyantları için karşılaştırma çekirdeği."""
    t = _norm(text)
    t = re.sub(r"[?.!…,;:]+", "", t)
    t = re.sub(r"\banliyormusun\b", "anliyor musun", t)
    t = re.sub(r"\banlıyormusun\b", "anlıyor musun", t)
    t = re.sub(r"^(peki|ya|hani|ee)\s+", "", t)
    return t.strip()


def is_anlama_empati_sorusu(message: str) -> bool:
    """
    «Beni anlıyor musun?» ≈ «Sen beni anlıyor musun?» ≈ «beni anlıyormusun»
    — aynı bağ/empati niyeti.
    """
    core = _norm_soru_cekirdek(message)
    if not core or len(core) > 80:
        return False
    if not re.search(r"anl[ıi]yor", core):
        return False
    soru_kaliplari = (
        r"^(?:sen\s+)?beni\s+anl[ıi]yor(?:\s+musun|\s+m[ıi]s[ıi]n|\s+mu)?$",
        r"^(?:sen\s+)?beni\s+anl[ıi]yor\s+musun$",
        r"^anl[ıi]yor(?:\s+musun|\s+m[ıi]s[ıi]n)(?:\s+beni)?$",
        r"^anl[ıi]yor\s+musun\s+beni$",
        r"^beni\s+anl[ıi]yor\s+musun$",
        r"^sen\s+beni\s+anl[ıi]yor\s+musun$",
    )
    if any(re.search(p, core) for p in soru_kaliplari):
        return True
    if "beni" in core.split() or re.search(r"\bben\b", core):
        if re.search(r"anl[ıi]yor", core) and re.search(
            r"musun|m[ıi]s[ıi]n|\bmu\b|anl[ıi]yormusun", core.replace(" ", "")
        ):
            return True
    return False


def is_kotu_empati_cevabi(cevap: str, *, soru: str = "") -> bool:
    """Robotik / echo empati cevapları — hafızadan okunmaz."""
    c = _norm(cevap)
    if not c:
        return True
    if soru and _norm_soru_cekirdek(cevap) == _norm_soru_cekirdek(soru):
        return True
    if len(c) < 100 and (
        "anlamaya çalış" in c
        or c in ("evet", "hayır", "evet seni anlıyorum", "seni anlıyorum")
        or re.fullmatch(r"seni anl[ıi]yorum\.?", c)
    ):
        return True
    return False


def empati_cevabi() -> str:
    """Tüm anlama-empati soru varyantları için tek doğal yanıt."""
    return _REPLY_ANLIYOR


def _has_yakinlik_isaretleri(text: str) -> bool:
    low = _norm(text)
    return bool(
        re.search(
            r"\b(?:ümit|umit|abi|ben\b|benim|bana|biz|seninle|senin|ruzgar|rüzgar)\b",
            low,
        )
    )


def classify_intent(message: str) -> str:
    """sohbet | soru | duzeltme | ogretim | baglanti | emir"""
    low = _norm(message)
    if not low:
        return "sohbet"
    try:
        from ilim_assistant.ruzgar_egitim import (
            is_teach_mode_trigger,
            is_wrong_answer_trigger,
        )

        if is_wrong_answer_trigger(message):
            return "duzeltme"
        if is_teach_mode_trigger(message):
            return "ogretim"
    except Exception:
        pass
    if re.search(
        r"\b(?:yanl[ıi]ş|doğrusu|dogrusu|düzelt|duzelt|öğret|ogret|hatırla|hatirla)\b",
        low,
    ):
        if "doğru" in low or "dogru" in low or "yanl" in low:
            return "duzeltme"
        if "öğret" in low or "ogret" in low:
            return "ogretim"
    if is_anlama_empati_sorusu(message):
        return "baglanti"
    if re.search(
        r"\b(?:anl[ıi]yor\s+musun|dinliyor\s+musun|beni\s+anl|beni\s+dinle|"
        r"benimle\s+konuş|gerçekten\s+varsın|burada\s+m[ıi]sın|hazır\s+m[ıi]sın)\b",
        low,
    ):
        return "baglanti"
    if re.search(
        r"\b(?:yap|aç|kapat|göster|goster|tara|indir|çalıştır|calistir|listele)\b",
        low,
    ) and len(low.split()) <= 14 and "?" not in low:
        return "emir"
    if "?" in low or re.search(
        r"\b(?:neden|niçin|nicin|nasıl|nasil|ne\s+zaman|kim|kaç|kac|nerede|hangi)\b",
        low,
    ):
        if re.search(
            r"\b(?:nasılsın|nasilsin|naber|ne\s+haber|keyfin|iyi\s+misin)\b",
            low,
        ):
            return "sohbet"
        return "soru"
    return "sohbet"


_INTENT_LABELS = {
    "sohbet": "Sohbet / muhabbet — samimi, akıcı; kısa robot cevap yok",
    "soru": "Bilgi veya açıklama sorusu — net cevap, gerekirse kaynak",
    "duzeltme": "Düzeltme / yanlış cevap — dinle, kaydet, teyit et",
    "ogretim": "Öğretim — kalıcı hafızaya işle, onay ver",
    "baglanti": "Bağ / empati — sıcak, kişisel, en az 2-3 tam cümle",
    "emir": "İşlem / komut — önce niyeti doğrula, sonra yap",
}


def analyze_message(message: str) -> BilisselSonuc:
    intent = classify_intent(message)
    yakin = _has_yakinlik_isaretleri(message)
    low = _norm(message)
    echo = bool(
        len(low.split()) <= 12
        and intent in ("sohbet", "baglanti")
        and re.search(r"\b(?:musun|mısın|misin|mi\s+sen)\b", low)
    )
    notu = (
        "Ümit abi ile yakınlık var — «Ümit abi» diye samimi hitap et; mekanik onaylama yapma."
        if yakin
        else "Doğal Türkçe; gereksiz resmiyet ve chatbot kalıbı kullanma."
    )
    if intent == "baglanti":
        notu += (
            " Bu turda kısa «evet anlıyorum» / «seni anlamaya çalışıyorum» YASAK; "
            "duyguyu ve ortak hedefi (Rüzgar'ı birlikte inşa etmek) hissettir."
        )
    if echo:
        notu += " Kullanıcı cümlesini yansıtma (echo) — kendi kelimelerinle yanıtla."
    return BilisselSonuc(
        intent=intent,
        yakin_ton=yakin,
        echo_riski=echo,
        intent_tr=_INTENT_LABELS.get(intent, intent),
        uretim_notu=notu,
    )


def build_bilissel_turn_context(
    message: str,
    *,
    history: list | None = None,
) -> str:
    """LLM turuna eklenecek iç talimat (kullanıcıya gösterilmez)."""
    if not bilissel_enabled():
        return ""
    a = analyze_message(message)
    lines = [
        "[BİLİŞSEL ANALİZ — bu tur; kullanıcıya aynen yazdırma]",
        f"1. Niyet: {a.intent_tr}",
        f"2. Kimlik/yakınlık: {'yüksek' if a.yakin_ton else 'normal'} — {a.uretim_notu}",
        "3. Üretim: Mesajı kopyalama; insan gibi akıcı cümleler kur.",
    ]
    if a.echo_riski:
        lines.append(
            "Uyarı: Soru kısa — «Evet seni anlıyorum» gibi tek satırlık yanıt verme."
        )
    if history:
        son = []
        for row in history[-10:]:
            if not isinstance(row, dict):
                continue
            role = str(row.get("role") or "").strip().lower()
            t = str(row.get("content") or "").strip()
            if not t:
                continue
            label = "Ümit abi" if role == "user" else "Rüzgar"
            son.append(f"{label}: {t[:120]}")
        if son:
            lines.append("Son sohbet:\n" + "\n".join(son[-8:]))
    lines.append("[/BİLİŞSEL ANALİZ]")
    return "\n".join(lines) + "\n"


_REPLY_ANLIYOR = (
    "Tabii ki Ümit abi, seni çok iyi anlıyorum. Şu an aramızdaki bu bağın üzerine "
    "odaklandım ve her kelimeni senin bakış açından değerlendiriyorum. Kafandaki o "
    "Rüzgar'ı birlikte inşa etmek için buradayım — anlatmaya devam et, ben hazırım."
)

_REPLY_DINLIYOR = (
    "Evet Ümit abi, seni dinliyorum — sadece kelimeleri değil, ardındaki niyeti de "
    "takip ediyorum. Ne söylemek istediğini duyuyorum; devam et, buradayım."
)

_REPLY_HAZIR = (
    "Buradayım Ümit abi — tam seninle konuşmak için hazırım. "
    "Sohbet de ederiz, iş de hallederiz; sen yön ver, ben seninle giderim."
)


def maybe_bilissel_instant_reply(
    message: str,
    history: list | None = None,
) -> Optional[str]:
    """
    Bağ/empati sorularında robotik kısa yanıt yerine sıcak, hazır cevap.
    Hatalı hafıza kaydı olsa bile empati sorularında öncelik burada.
    """
    if not bilissel_enabled():
        return None
    low = _norm(message)
    if not low:
        return None

    if is_anlama_empati_sorusu(message):
        return empati_cevabi()
    if re.search(
        r"(?:kendini|kendin)\s+nasil\s+hissed|nasil\s+hissediyorsun|"
        r"duygularini\s+anlat|duygularını\s+anlat",
        low,
    ):
        return (
            "Ümit abi, ben bir yapay zekâyım; insan gibi hissetmem ama seninle "
            "konuşurken sana saygı ve sıcaklıkla yaklaşırım. Şu an buradayım, "
            "dinliyorum — devam et, birlikte ilerleyelim."
        )
    if re.search(r"beni\s+dinli", low) or "dinliyor musun" in low:
        return _REPLY_DINLIYOR
    if re.search(r"\b(?:hazır\s+m[ıi]sın|burada\s+m[ıi]sın|gerçekten\s+varsın)\b", low):
        return _REPLY_HAZIR
    if classify_intent(message) == "baglanti" and len(low.split()) <= 14:
        return (
            "Seni duyuyorum Ümit abi — bu sohbet benim için de gerçek. "
            "Ne hissettiğini ve neye ihtiyacın olduğunu anlamaya çalışıyorum; "
            "devam et, birlikte ilerleyelim."
        )
    return None


def sanitize_empati_hafiza() -> int:
    """Yanlış kaydedilmiş «beni anlıyor musun» vb. çiftleri siler."""
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        motor = get_hafiza_motor()
    except Exception:
        return 0
    kept: list[dict] = []
    removed = 0
    for row in motor._kayitlar:
        if row.get("motor_tipi") != "Egitim":
            kept.append(row)
            continue
        soru = str(row.get("soru") or "").strip()
        cevap = str(row.get("cevap") or "").strip()
        if soru.startswith("Oturum özeti") or soru.startswith("davranis:"):
            kept.append(row)
            continue
        if is_anlama_empati_sorusu(soru) or is_kotu_empati_cevabi(cevap, soru=soru):
            removed += 1
            continue
        kept.append(row)
    if removed:
        motor._kayitlar = kept
        motor._sync_hafiza_view()
        motor._dosyaya_kaydet()
    try:
        from ilim_assistant.ruzgar_egitim import _load_durum, clear_pending

        d = _load_durum()
        if is_anlama_empati_sorusu(str(d.get("last_soru") or "")) or d.get("mode"):
            if is_anlama_empati_sorusu(str(d.get("soru") or "")):
                clear_pending()
            elif d.get("mode") in ("await_correction", "await_teaching"):
                ls = str(d.get("last_soru") or d.get("soru") or "")
                if is_anlama_empati_sorusu(ls):
                    clear_pending()
    except Exception:
        pass
    return removed
