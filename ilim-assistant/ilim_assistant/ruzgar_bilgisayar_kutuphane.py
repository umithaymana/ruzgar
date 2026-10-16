# -*- coding: utf-8 -*-
"""Rüzgar — bilgisayar mühendisliği anlık cevap (Faz 16).

Kaynak: knowledge/ortak_kaynak/alanlar/bilgisayar_muhendisligi/
Eğitim. Saldırı/exploit tarifi yok.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[1]
_DIR = _ROOT / "knowledge" / "ortak_kaynak" / "alanlar" / "bilgisayar_muhendisligi"
_KAV = _DIR / "kavramlar_bilgisayar.jsonl"

_CUES = (
    "bilgisayar muhendis",
    "bilgisayar mühendis",
    "sayisal mantik",
    "sayısal mantık",
    "dijital mantik",
    "dijital mantık",
    "mantik kapisi",
    "mantık kapısı",
    "islemci",
    "işlemci",
    "komut seti",
    "bellek hiyerars",
    "bellek hiyerarş",
    "onbellek",
    "önbellek",
    "veri yolu",
    "von neumann",
    "kesme",
    "cevre birimi",
    "çevre birimi",
    "saat darbesi",
    "kati hal",
    "katı hal",
    "sabit disk",
    "ayrik matematik",
    "ayrık matematik",
    "boolean cebir",
    "transistor",
    "transistör",
    "isletim cekirdegi",
    "işletim çekirdeği",
    "kernel",
    "sistem cagrisi",
    "sistem çağrısı",
    "proses",
    "sanal bellek",
    "sayfa tablosu",
    "dosya sistemi",
    "derleyici",
    "baglayici",
    "bağlayıcı",
    "ag yigini",
    "ağ yığını",
    "veri yapisi",
    "veri yapısı",
    "bagli liste",
    "bağlı liste",
    "cagri yigini",
    "çağrı yığını",
    "ikili arama",
    "hash tablosu",
    "birim testi",
    "hata ayiklama",
    "hata ayıklama",
    "surum kontrol",
    "sürüm kontrol",
    "yazilim tasarim",
    "yazılım tasarım",
    "html dili",
    "css dili",
    "javascript dili",
    "python dili",
    "statik site",
    "kucuk uygulama",
    "küçük uygulama",
    "site nasil kurulur",
    "site nasıl kurulur",
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def looks_like_bilgisayar_question(msg: str) -> bool:
    low = _fold(msg)
    return any(_fold(c) in low for c in _CUES)


@lru_cache(maxsize=1)
def _load_kavramlar() -> list[dict[str, Any]]:
    if not _KAV.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in _KAV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


_ENVANTER_CUES = (
    "kutuphanende hangi bilgi",
    "kutuphanende neler var",
    "kutuphanende ne var",
    "kutuphanendeki bilgi",
    "kutuphaneni listele",
    "kutuphaneni say",
    "kutuphane envanter",
    "bilgi kutuphaneni",
    "bilgi kutuphanende",
    "programlama kutuphanesi",
    "programlama raflari",
    "rafinda neler var",
    "rafinda hangi bilgi",
)


def wants_bilgisayar_envanter(msg: str) -> bool:
    """Kütüphane dökümü — model yok, dosyadan okunur."""
    low = _fold(msg)
    return any(cue in low for cue in _ENVANTER_CUES)


def _faz_key(faz: Any) -> tuple[int, str]:
    raw = str(faz or "").strip().lower()
    match = re.match(r"(\d+)(.*)", raw)
    if not match:
        return (999, raw)
    return (int(match.group(1)), match.group(2))


def _kaynak_matches_faz(kaynak: str, faz: Any) -> bool:
    low = _fold(kaynak)
    token = f"faz {faz}".strip().lower()
    start = 0
    while True:
        found = low.find(token, start)
        if found < 0:
            return False
        end = found + len(token)
        if end >= len(low) or not low[end].isalnum():
            return True
        start = found + 1


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _layer_manifests() -> list[dict[str, Any]]:
    root = _DIR / "katmanlar"
    rows: list[dict[str, Any]] = []
    if not root.is_dir():
        return rows
    for child in root.iterdir():
        manifest = child / "manifest.json"
        if not child.is_dir() or not manifest.is_file():
            continue
        data = _read_json(manifest)
        data.setdefault("katman_id", child.name)
        data.setdefault("baslik", child.name)
        data.setdefault("dosya_yolu", f"knowledge/ortak_kaynak/alanlar/bilgisayar_muhendisligi/katmanlar/{child.name}")
        rows.append(data)
    rows.sort(key=lambda row: (_faz_key(row.get("faz")), str(row.get("baslik") or "")))
    return rows


def format_bilgisayar_envanter() -> str:
    """Bilgisayar / programlama rafını sırayla döker. LLM çağırmaz."""
    catalog = _read_json(_DIR / "catalog.json")
    kavramlar = _load_kavramlar()
    layers = _layer_manifests()
    note_count = 0
    incremental = _DIR / "katmanlar"
    if incremental.is_dir():
        note_count = len(list(incremental.glob("*/incremental/*.md")))

    overview = [row for row in kavramlar if row.get("id") == "bilgisayar_muhendisligi"]
    rest = [row for row in kavramlar if row.get("id") != "bilgisayar_muhendisligi"]
    used: set[int] = set()
    grouped: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for layer in layers:
        hits: list[dict[str, Any]] = []
        for index, row in enumerate(rest):
            if index in used:
                continue
            if _kaynak_matches_faz(str(row.get("kaynak_notu") or ""), layer.get("faz")):
                hits.append(row)
                used.add(index)
        grouped.append((layer, hits))

    leftovers = [row for index, row in enumerate(rest) if index not in used]
    if leftovers:
        for layer, hits in grouped:
            if str(layer.get("katman_id") or "") == "donanim_cekirdek":
                hits[:0] = leftovers
                leftovers = []
                break
    if leftovers:
        grouped.append(
            (
                {
                    "baslik": "Katmansız kavramlar",
                    "faz": "",
                    "durum": "hazir",
                    "dosya_yolu": "knowledge/ortak_kaynak/alanlar/bilgisayar_muhendisligi/kavramlar_bilgisayar.jsonl",
                    "parca_sayisi": len(leftovers),
                },
                leftovers,
            )
        )

    lines = [
        "Ümit abi, bilgisayar ve programlama kütüphanesi — dosyadan okundu, model yok.",
        "",
        "Alan: Bilgisayar mühendisliği",
        f"Kavram: {len(kavramlar)}",
        f"Katman notu: {note_count}",
        "Kök: knowledge/ortak_kaynak/alanlar/bilgisayar_muhendisligi",
    ]
    politika = str(catalog.get("politika") or "").strip()
    if politika:
        lines.append(f"Politika: {politika}")
    if overview:
        title = str(overview[0].get("baslik") or "giriş").strip()
        lines.extend(["", f"Giriş: {title}"])
    if not grouped:
        lines.extend(["", "Raf boş: katman manifesti yok."])
        return "\n".join(lines).strip()

    for index, (layer, hits) in enumerate(grouped, start=1):
        title = str(layer.get("baslik") or layer.get("katman_id") or "katman").strip()
        faz = str(layer.get("faz") or "").strip()
        durum = str(layer.get("durum") or "bilinmiyor").strip()
        path = str(layer.get("dosya_yolu") or "").strip()
        pieces = layer.get("parca_sayisi")
        faz_bit = f" — faz {faz}" if faz else ""
        piece_bit = f" · {pieces} parça" if pieces not in (None, "") else ""
        lines.extend(
            [
                "",
                f"{index}. {title}{faz_bit} — {len(hits)} kavram{piece_bit} — {durum}",
                f"   {path}",
            ]
        )
        if not hits:
            lines.append("   (bu katmanda kavram kartı yok)")
            continue
        for concept_index, row in enumerate(hits, start=1):
            concept = str(row.get("baslik") or row.get("id") or "kavram").strip()
            lines.append(f"   {concept_index}. {concept}")
    return "\n".join(lines).strip()


def format_bilgisayar_reply(row: dict[str, Any]) -> str:
    title = (row.get("baslik") or row.get("id") or "bilgisayar").strip()
    body = (row.get("metin") or "").strip()
    note = (row.get("kaynak_notu") or "").strip()
    parts = [f"**{title}**", "", body]
    if note:
        parts.extend(["", f"_{note}_"])
    return "\n".join(parts).strip()


_CODE_TASK_BITS = (
    "@@",
    "pytest",
    "traceback",
    ".py",
    "refactor",
    "patch",
    "def ",
    "class ",
    "gorev:",
    "görev:",
)

_CONCEPT_ASK = (
    "nedir",
    "ne demek",
    "anlat",
    "acikla",
    "açıkla",
    "nasil",
    "nasıl",
    "farki",
    "farkı",
)


def programlama_kavram_notu(msg: str) -> str:
    """Programlama turu kavram sorusunda raf notu. Kod görevine karışmaz."""
    raw = (msg or "").strip()
    if not raw or len(raw) > 400:
        return ""
    low = _fold(raw)
    if any(bit in low for bit in _CODE_TASK_BITS):
        return ""
    if not any(p in low for p in _CONCEPT_ASK):
        return ""
    hit = try_bilgisayar_reply(raw)
    if not hit:
        return ""
    return (
        "[BİLGİSAYAR MÜHENDİSLİĞİ NOTU — dahili; kullanıcıya aynen okuma]\n"
        "Kavram notunu kendi cümlelerinle anlat. İstenirse kısa eğitim örneği yaz. "
        "Saldırı, exploit veya zararlı kod üretme.\n\n"
        + hit
    )


def try_bilgisayar_reply(msg: str) -> Optional[str]:
    if not (msg or "").strip():
        return None
    low = _fold(msg)
    is_cue = looks_like_bilgisayar_question(msg)
    ask = any(p in low for p in ("nedir", "ne demek", "anlat", "nasil", "nasıl"))
    if not is_cue and not ask:
        return None
    from ilim_assistant.ruzgar_kavram_match import match_kavram_row

    row = match_kavram_row(msg, _load_kavramlar(), min_score=55 if is_cue else 70)
    if row:
        return format_bilgisayar_reply(row)
    if is_cue and ask:
        for r in _load_kavramlar():
            if r.get("id") == "bilgisayar_muhendisligi":
                return format_bilgisayar_reply(r)
    return None
