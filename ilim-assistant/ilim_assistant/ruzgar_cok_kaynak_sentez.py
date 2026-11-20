# -*- coding: utf-8 -*-
"""Rüzgar — genel amaçlı çok kaynaklı okuma / özet / sentez.

Dar alan kalıplarına (yalnız doğum/vefat/anne-baba vb.) kilitlenmeden:
- İndeks hit'lerini eser/kitap bazında çeşitlendir (3–5 kaynak)
- Sentez ve kaynak atıfı için bağlam paketle
- Doğal karşılaştırma önerisi üret

Kapat: RUZGAR_COK_KAYNAK=0
"""
from __future__ import annotations

import os
import re
from pathlib import PurePosixPath
from typing import Any, Sequence

COK_KAYNAK_VERSION = "cok-kaynak-sentez-v1-2026-11-20"

_BOOK_HINT = re.compile(
    r"(?:buhari|buhârî|bukhari|muslim|müslim|tirmizi|tirmizî|tirmidhi|"
    r"nesai|nesâî|nasai|ebu\s*davud|ibn\s*mace|ibn\s*majah|"
    r"ibn\s*his[hş]am|vakidi|vâkıdî|taberi|taberî|serahsi|"
    r"gazali|gazzali|mevlana|risale|mektubat)",
    re.I,
)


def cok_kaynak_enabled() -> bool:
    return os.environ.get("RUZGAR_COK_KAYNAK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _source_book_key(src: str) -> str:
    """Hit kaynağını eser/kitap anahtarına indirger (raf bağımsız)."""
    s = (src or "").replace("\\", "/").strip()
    if not s:
        return "unknown"
    low = s.lower()
    # Bilinen hadis eserleri
    for name in (
        "buhari",
        "muslim",
        "tirmizi",
        "nesai",
        "ebu_davud",
        "ibn_mace",
        "kutub_i_sitte",
    ):
        if name in low:
            return name
    parts = [p for p in PurePosixPath(low).parts if p and p not in (".", "..")]
    # knowledge/.../eser_adi/... → son anlamlı 2–3 parça
    if len(parts) >= 2:
        return "/".join(parts[-3:-1]) if len(parts) >= 3 else "/".join(parts[-2:])
    return parts[-1] if parts else low[:80]


def diversify_hits_by_book(
    hits: Sequence[tuple[str, str, float]] | None,
    *,
    max_books: int = 5,
    per_book: int = 2,
    max_total: int = 10,
) -> list[tuple[str, str, float]]:
    """Farklı eserlerden dengeli hit seç — tek rafa/tek alana sıkışmayı kır."""
    if not cok_kaynak_enabled() or not hits:
        return list(hits or [])
    try:
        max_books = max(2, min(int(os.environ.get("RUZGAR_COK_KAYNAK_MAX_BOOKS", str(max_books))), 8))
    except ValueError:
        max_books = 5
    try:
        per_book = max(1, min(int(os.environ.get("RUZGAR_COK_KAYNAK_PER_BOOK", str(per_book))), 4))
    except ValueError:
        per_book = 2
    try:
        max_total = max(3, min(int(os.environ.get("RUZGAR_COK_KAYNAK_MAX_TOTAL", str(max_total))), 16))
    except ValueError:
        max_total = 10

    ordered = sorted(
        ((str(t), str(s), float(sc)) for t, s, sc in hits),
        key=lambda h: h[2],
        reverse=True,
    )
    by_book: dict[str, list[tuple[str, str, float]]] = {}
    book_order: list[str] = []
    for h in ordered:
        key = _source_book_key(h[1])
        if key not in by_book:
            by_book[key] = []
            book_order.append(key)
        if len(by_book[key]) < per_book:
            by_book[key].append(h)

    picked: list[tuple[str, str, float]] = []
    # Round-robin kitaplar arası
    for _ in range(per_book):
        for key in book_order[:max_books]:
            bucket = by_book.get(key) or []
            if bucket:
                picked.append(bucket.pop(0))
                if len(picked) >= max_total:
                    return picked
    # Kalan yüksek skorlu (çeşitlilik sonrası)
    seen = {(p[1], p[0][:160]) for p in picked}
    for h in ordered:
        key = (h[1], h[0][:160])
        if key in seen:
            continue
        picked.append(h)
        seen.add(key)
        if len(picked) >= max_total:
            break
    return picked


def count_distinct_books(hits: Sequence[tuple[str, str, float]] | None) -> int:
    keys = {_source_book_key(s) for _t, s, _sc in (hits or []) if s}
    return len(keys)


def pack_multi_source_context(
    hits: Sequence[tuple[str, str, float]] | None,
    *,
    max_books: int = 5,
    max_chars: int = 7000,
) -> str:
    """LLM bağlamı: 3–5 eserden pasaj + kaynak etiketi."""
    if not cok_kaynak_enabled():
        return ""
    diversified = diversify_hits_by_book(hits, max_books=max_books, max_total=max_books * 2)
    if not diversified:
        return ""
    lines = [
        "=== ÇOK KAYNAKLI KÜTÜPHANE PASAJLARI (genel sentez; dar alan kilidi yok) ===",
        "Aşağıdaki parçalar farklı eser/raflardan gelir. Kullanıcının sorusuna göre "
        "hepsini oku, tutarlı bir özet/sentez yaz; yalnız doğum/vefat/anne-baba gibi "
        "tek bir alanı çekip cevabı oraya sıkıştırma. Her önemli iddiada kaynağı belirt.",
        "",
    ]
    budget = max_chars
    used_books: set[str] = set()
    idx = 0
    for text, src, score in diversified:
        book = _source_book_key(src)
        if len(used_books) >= max_books and book not in used_books:
            continue
        body = " ".join((text or "").split())
        if len(body) < 40:
            continue
        if len(body) > 1100:
            body = body[:1100] + "…"
        idx += 1
        used_books.add(book)
        chunk = f"[K{idx}] eser≈{book} · skor~{score:.2f} · yol={src}\n{body}\n"
        if len(chunk) > budget:
            break
        lines.append(chunk)
        budget -= len(chunk)
    if idx < 1:
        return ""
    lines.append("=== /ÇOK KAYNAKLI PASAJLAR ===")
    return "\n".join(lines).strip()


def comparison_offer_line(message: str, hits: Sequence[tuple[str, str, float]] | None) -> str:
    """Doğal karşılaştırma önerisi — sabit şablon değil, bağlama göre."""
    if not cok_kaynak_enabled():
        return ""
    n_books = count_distinct_books(hits)
    low = (message or "").lower()
    if any(k in low for k in ("hadis", "buhari", "buhârî", "tirmizi", "müslim", "muslim", "rivayet")):
        return (
            "İstersen diğer kaynaklardaki rivayet ve şerhlerle de karşılaştırabilirim."
        )
    if n_books >= 2 or any(
        k in low for k in ("karşılaştır", "karsilastir", "farkı", "farki", "görüş", "gorus")
    ):
        return (
            "İstersen diğer eserlerdeki anlatım ve görüşlerle de karşılaştırabilirim."
        )
    if n_books >= 1:
        return (
            "İstersen kütüphanedeki diğer ilgili eserlerden de okuyup sentezi genişletebilirim."
        )
    return ""


def library_rag_top_k_boost(base: int, message: str) -> int:
    """Kütüphane bilgi sorularında 3–5+ pasaj için top_k yükselt."""
    if not cok_kaynak_enabled():
        return base
    try:
        from ilim_assistant.ruzgar_kutuphane_gorev import (
            is_kutuphane_bilgi_soru,
            kutuphane_enabled_hard,
        )

        if not (kutuphane_enabled_hard() and is_kutuphane_bilgi_soru(message or "")):
            return base
    except Exception:
        return base
    try:
        target = int(os.environ.get("RUZGAR_COK_KAYNAK_RAG_TOP_K", "6"))
    except ValueError:
        target = 6
    return max(base, min(target, 12))


def multi_source_grounding_addon(
    *,
    source_count: int,
    distinct_books: int,
    want_source: bool,
    message: str = "",
) -> str:
    """grounding_directive'e eklenen genel sentez kuralları."""
    if not cok_kaynak_enabled() or source_count <= 0:
        return ""
    offer = comparison_offer_line(message, None)
    # hits yokken genel teklif
    if not offer:
        offer = (
            "İstersen diğer kaynaklardaki rivayet, şerh veya anlatımlarla da "
            "karşılaştırabilirim."
        )
    lines = [
        "\n[TALİMAT — ÇOK KAYNAKLI SENTEZ — GENEL]\n",
        f"Bağlamda yaklaşık **{source_count}** parça / **{distinct_books or '?'}** eser izi var.\n",
        "- Dar alan kilidi YASAK: cevabı yalnız doğum tarihi, vefat, anne/baba, tek sayı "
        "veya tek kart alanına sıkıştırma. Kullanıcının sorduğu derinlikte oku ve özetle.\n",
        "- Mümkünse **3–5 farklı eser/kitaptan** gelen bilgiyi birleştir; tutarlı sentez yaz.\n",
        "- Hangi bilginin hangi kaynaktan geldiğini doğal cümleyle belirt "
        "(«Buhârî'de …», «İbn Hişâm anlatımında …»).\n",
        "- Çelişki varsa uydurma; «kaynaklar farklı söylüyor» de.\n",
        f"- Yanıtın sonunda (uygunsa) doğal bir teklif ekle: «{offer}»\n",
        "- Pasaj yokmuş gibi genel model uydurması yapma.\n",
    ]
    if want_source:
        lines.append(
            "- Kullanıcı kaynak istedi: eser/yol; mümkünse bölüm/no/sayfa "
            "(yalnızca bağlamdaysa).\n"
        )
    return "".join(lines)


def should_force_library_synthesis(
    *,
    hits: Sequence[tuple[str, str, float]] | None,
    mode_norm: str,
    message: str = "",
) -> bool:
    """Web olmasa bile yerel ≥3 çeşit hit → sentez turu."""
    if not cok_kaynak_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim", "okuma", "ilim", "hafiza"):
        return False
    n = len(hits or [])
    books = count_distinct_books(hits)
    if n >= 3 or books >= 2:
        return True
    try:
        from ilim_assistant.ruzgar_kutuphane_gorev import (
            is_kutuphane_bilgi_soru,
            kutuphane_enabled_hard,
        )

        if kutuphane_enabled_hard() and is_kutuphane_bilgi_soru(message) and n >= 2:
            return True
    except Exception:
        pass
    return False


def cok_kaynak_status() -> dict[str, Any]:
    return {
        "enabled": cok_kaynak_enabled(),
        "version": COK_KAYNAK_VERSION,
    }
