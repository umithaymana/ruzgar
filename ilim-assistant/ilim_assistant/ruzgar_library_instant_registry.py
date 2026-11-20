# -*- coding: utf-8 -*-
"""Tek anlık kütüphane registry — desktop_server çift bloğunu tek kapıya indirir.

Bilgi / karşılaştır / anlat niyetlerinde kart yok → RAG.
Saf gündelik (hava, döviz, kısa selam) bu registry'de değil.
Kapat (eski gevşek): RUZGAR_LIBRARY_INSTANT_REGISTRY=0 ile yine de fonksiyonlar çalışır;
  davranış politikası ruzgar_kutuphane_gorev + anlik_niyet_gate üzerinden gelir.
"""
from __future__ import annotations

import importlib
import re
import unicodedata
from typing import Any, Callable, Optional

# (modül, fonksiyon, orch anahtarı, plan primary, label_tr)
LIBRARY_INSTANT_ENTRIES: tuple[tuple[str, str, str, str, str], ...] = (
    ("ilim_assistant.ruzgar_akaid_kutuphane", "try_akaid_reply", "akaid_anlik", "ilim", "Akaid (anında)"),
    ("ilim_assistant.ruzgar_hadis_kutuphane", "try_hadis_reply", "hadis_anlik", "ilim", "Hadis (anında)"),
    ("ilim_assistant.ruzgar_siyer_kutuphane", "try_siyer_reply", "siyer_anlik", "ilim", "Siyer (anında)"),
    ("ilim_assistant.ruzgar_tasavvuf_kutuphane", "try_tasavvuf_reply", "tasavvuf_anlik", "ilim", "Tasavvuf (anında)"),
    ("ilim_assistant.ruzgar_felsefe_kutuphane", "try_felsefe_reply", "felsefe_anlik", "ilim", "Felsefe (anında)"),
    ("ilim_assistant.ruzgar_psikoloji_kutuphane", "try_psikoloji_reply", "psikoloji_anlik", "ilim", "Psikoloji (anında)"),
    ("ilim_assistant.ruzgar_edebiyat_kutuphane", "try_edebiyat_reply", "edebiyat_anlik", "ilim", "Edebiyat (anında)"),
    ("ilim_assistant.ruzgar_ek_raflar", "try_ek_raf_reply", "ek_raf_anlik", "bilgi", "İlim rafı (anında)"),
    ("ilim_assistant.ruzgar_bilim_kutuphane", "try_bilim_reply", "bilim_anlik", "bilgi", "Bilim (anında)"),
    ("ilim_assistant.ruzgar_cografya_kutuphane", "try_cografya_reply", "cografya_anlik", "bilgi", "Coğrafya (anında)"),
    ("ilim_assistant.ruzgar_bilgisayar_kutuphane", "try_bilgisayar_reply", "bilgisayar_anlik", "bilgi", "Bilgisayar mühendisliği (anında)"),
    ("ilim_assistant.ruzgar_teknoloji_kutuphane", "try_teknoloji_reply", "teknoloji_anlik", "bilgi", "Teknoloji (anında)"),
    ("ilim_assistant.ruzgar_usul_fikh_kutuphane", "try_usul_fikh_reply", "usul_fikh_anlik", "ilim", "Usûl-i fıkıh (anında)"),
    ("ilim_assistant.ruzgar_fikh_kutuphane", "try_fikh_reply", "fikh_anlik", "ilim", "Fıkıh (anında)"),
    ("ilim_assistant.ruzgar_kutuphane", "try_kutuphane_instant_reply", "kutuphane_raf_hit", "bilgi", "Rüzgar Kütüphanesi"),
    (
        "ilim_assistant.ruzgar_otomatik_ogrenme",
        "try_bilgi_kutuphane_instant_reply",
        "kutuphane_hit",
        "bilgi",
        "Bilgi kütüphanesi",
    ),
)


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("ı", "i").replace("İ", "i")
    return t.lower().strip()


def forces_library_rag(message: str) -> bool:
    """Bilgi/karşılaştır/anlat → anlık kart yasak, RAG zorunlu.

    Numaralı hadis/ayet (buhari 1) bu kapıdan geçmez.
    """
    raw = (message or "").strip()
    if not raw:
        return False
    # Numaralı matın / ayet — anlık kalsın
    if re.search(r"\b(?:hadis|ayet)\s*(?:no|numara|#)?\s*\d{1,5}\b", raw, re.I):
        return False
    if re.search(
        r"\b(?:buhari|buhârî|muslim|müslim|tirmizi|ebu\s*davud|nesai|ibn\s*mace)\b"
        r".{0,20}\b\d{1,5}\b",
        raw,
        re.I,
    ):
        return False
    low = _fold(raw)
    # Karşılaştırma / çok kaynak
    if any(
        k in low
        for k in (
            "karsilastir",
            "karşılaştır",
            "diger kaynak",
            "diğer kaynak",
            "rivayetler",
            "cok kaynak",
            "çok kaynak",
        )
    ):
        return True
    # Anlat / özet / açıkla — derin okuma
    if re.search(
        r"(?:\banlat(?:ır\s*mısın|irmisin)?\b|\baçıkla|\bacikla|"
        r"\bözet\b|\bozet\b|daha\s+uzun|detayl[ıi]|"
        r"hakk[ıi]nda|bilgi\s+ver)",
        raw,
        re.I,
    ) or re.search(
        r"(?:\banlat\b|\bacikla\b|\baçıkla\b|\bozet\b|\bözet\b|"
        r"hakkinda|bilgi\s+ver)",
        low,
    ):
        return True
    # Kavramsal «… nedir / ne demek» — tek raf kartı yerine indeks
    # (strict kısa lookup hariç: tek terim + nedir → anlık izin, örn. «python nedir»)
    try:
        from ilim_assistant.ruzgar_anlik_niyet_gate import is_strict_library_lookup

        if is_strict_library_lookup(raw):
            # «niyet hadisi nedir» strict'e düşebilir — ilim çok-kaynak istisnası
            if "niyet" in low and "hadis" in low:
                return True
            if any(k in low for k in ("tirmizi", "buhari", "muslim", "nesai")) and (
                "karsilastir" in low or "ile" in low
            ):
                return True
            return False
    except Exception:
        pass
    # Çok token'lı nedir/kimdir bilgi sorusu → RAG
    if re.search(r"\b(?:nedir|ne\s+demek|kimdir)\b", low):
        try:
            from ilim_assistant.ruzgar_kutuphane_gorev import _query_tokens

            if len(_query_tokens(raw)) >= 2:
                return True
        except Exception:
            if len(low.split()) >= 3:
                return True
    return False


def _load_try_fn(mod_path: str, fn_name: str) -> Optional[Callable[[str], Optional[str]]]:
    try:
        mod = importlib.import_module(mod_path)
        fn = getattr(mod, fn_name, None)
        return fn if callable(fn) else None
    except Exception:
        return None


def try_library_instant_from_registry(
    message: str,
    *,
    gate_fn: Optional[Callable[[str, Callable], Optional[str]]] = None,
) -> Optional[tuple[str, dict[str, Any]]]:
    """İlk eşleşen raf kartı + orch yaması. Yoksa None → RAG yolu.

    gate_fn(msg, try_fn) → reply|None; verilmezse doğrudan try_fn (test).
    """
    raw = (message or "").strip()
    if not raw:
        return None
    if forces_library_rag(raw):
        return None
    for mod_path, fn_name, orch_key, primary, label in LIBRARY_INSTANT_ENTRIES:
        fn = _load_try_fn(mod_path, fn_name)
        if fn is None:
            continue
        try:
            if gate_fn is not None:
                reply = gate_fn(raw, fn)
            else:
                reply = fn(raw)
        except Exception:
            reply = None
        if not (reply or "").strip():
            continue
        orch_patch: dict[str, Any] = {
            orch_key: True,
            "plan": {"primary": primary, "label_tr": label},
            "library_instant_registry": True,
            "library_instant_key": orch_key,
        }
        return (reply.strip(), orch_patch)
    return None
