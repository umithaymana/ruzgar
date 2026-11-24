# Created by Ümit & Gökçenur
"""Ana Motor — numaralı kaynak blokları ve zorunlu atıf talimatı (Faz 9.2 + ortak kaynak)."""

from __future__ import annotations

import os
from typing import Any


def _chunk_max_chars() -> int:
    try:
        return max(400, int(os.environ.get("RUZGAR_KAYNAK_CHUNK_MAX", "2400")))
    except ValueError:
        return 2400


def _enrich_src_label(src: str) -> str:
    """Eser künyesi (manifest) → ortak kayıt bibliyografisi → path. Hata yutulur.

    K3: kaynak klasöründe manifest.json varsa etiket «Arapça eser adı — müellif (Türkçe ad) [kimlik · kategori]» olur;
    kanıt orijinal eserde kalır, künye Arapça orijinale işaret eder. Kapat: RUZGAR_KUNYE=0.
    """
    try:
        from ilim_assistant.ruzgar_kunye import kunye_etiketi

        _k = kunye_etiketi(src)
        if _k:
            return _k
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_ortak_kaynak import enrich_source_label, ortak_kaynak_enabled

        if ortak_kaynak_enabled():
            return enrich_source_label(src) or src
    except Exception:
        pass
    return src


def format_context_blocks(
    hits: list[tuple[str, str, float]],
    *,
    archive_primary: bool = False,
) -> list[tuple[str, str]]:
    """RAG parçalarını [K1]… numaralı bağlam bloklarına çevirir."""
    if not hits:
        return []
    max_c = _chunk_max_chars()
    out: list[tuple[str, str]] = []
    for i, (text, src, score) in enumerate(hits, start=1):
        body = (text or "").strip()
        if len(body) > max_c:
            body = body[: max_c - 24].rstrip() + "\n… [metin kısaltıldı]"
        display = _enrich_src_label(src)
        label = f"[K{i}] {display}"
        if archive_primary:
            label = f"[K{i} — İlim Hazinesi] {display}"
        meta = f"(benzerlik: {float(score):.2f})"
        out.append((f"{label} {meta}\n{body}", src))
    return out


def kaynak_izi_footer(
    hits: list[tuple[str, str, float]] | None,
    *,
    max_items: int = 5,
) -> str:
    """1.C — yanıt sonu için kısa kaynak izi (path → okunur etiket)."""
    if not hits:
        return ""
    lines = ["", "—", "**Kaynak izi:**"]
    seen: set[str] = set()
    n = 0
    for _text, src, score in hits:
        label = _enrich_src_label(src)
        key = label.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        n += 1
        lines.append(f"- [K{n}] {label} (benzerlik {float(score):.2f})")
        if n >= max_items:
            break
    if n == 0:
        return ""
    return "\n".join(lines)


def _source_key(src: str) -> str:
    """Aynı eser farklı chunk → tek anahtar; klasör+dosya ile kardeş eser ayrılır."""
    s = (src or "").strip().replace("\\", "/").lower()
    if not s:
        return ""
    parts = [p for p in s.split("/") if p]
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    return parts[-1] if parts else s


def distinct_source_count(hits: list[tuple[str, str, float]] | None) -> int:
    """F2.3 — benzersiz eser/yol sayısı."""
    seen: set[str] = set()
    for h in hits or []:
        try:
            key = _source_key(str(h[1] or ""))
        except Exception:
            continue
        if key:
            seen.add(key)
    return len(seen)


def cok_eser_sentez_directive(
    *,
    source_count: int,
    distinct_sources: int,
) -> str:
    """F2.3 — 3+ pasaj / çok eser: kaynaklı kısa sentez talimatı."""
    if source_count < 2 or distinct_sources < 2:
        return ""
    n = min(5, max(2, distinct_sources))
    return (
        "\n\n[TALİMAT — F2.3 ÇOK ESER SENTEZ]\n"
        f"Bağlamda **{source_count}** parça, yaklaşık **{distinct_sources}** ayrı eser/yol var.\n"
        f"- Cevabı **{min(3, n)}–{n}** farklı [K#] pasajına dayandır; tek parçadan ezberleme.\n"
        "- 4–8 cümlede **kaynaklı kısa özet**: ortak nokta + varsa ayrım.\n"
        "- Her önemli iddiada [K1]/[K2]… kullan; bağlamda yoksa uydurma.\n"
        "- Sonunda **Kaynak izi:** ile kullandığın [K#] eserlerini listele.\n"
        "- Madde bombardımanı yok; sohbet dilinde sentez.\n"
    )


def citation_directive_for_turn(
    *,
    source_count: int,
    archive_primary: bool,
    web_present: bool,
    soft_natural: bool = False,
    distinct_sources: int = 0,
) -> str:
    """Modele zorunlu kaynak / güven talimatı."""
    no_fabricate = (
        "- Kaynakta **olmayan** sayfa, cilt, bölüm, alıntı, eser veya yazar **uydurma**. "
        "Yalnızca bağlamda veya kayıtta görünen bilgileri yaz. "
        "Kesin kaynak yoksa: «Bu bilgi mevcut kütüphanedeki kaynaklarda doğrulanamadı.»\n"
        "- Web bilgisini kalıcı kütüphane kaydı gibi gösterme; web varsa URL/site ayrı belirt.\n"
    )
    if soft_natural:
        # Faz 91 P2 — doğal sohbet: zorunlu «Güven: düşük» / web gürültüsü yok
        if source_count <= 0 and not web_present:
            return (
                "\n\n[TALİMAT — KAYNAK — doğal sohbet]\n"
                "Bu tur sohbet/anlatım; zorunlu güven satırı veya web damgası yazma. "
                "Uydurma tarih/alıntı yok; bilmiyorsan kısaca dürüstçe söyle.\n"
            )
        lines = [
            "\n\n[TALİMAT — KAYNAK — doğal sohbet]\n",
            f"Bağlamda **{source_count}** yerel parça",
        ]
        if web_present:
            lines.append(" ve web metni")
        lines.append(
            " var. Önce bunlara dayan; mümkünse [K1] kullan. "
            "Zorunlu **Güven:** satırı veya «web taraması» notu yazma; "
            "sohbet akışını bozma.\n"
        )
        lines.append(no_fabricate)
        if distinct_sources >= 2:
            lines.append(
                cok_eser_sentez_directive(
                    source_count=source_count, distinct_sources=distinct_sources
                )
            )
        return "".join(lines)
    if source_count <= 0 and not web_present:
        return (
            "\n\n[TALİMAT — KAYNAK — Ana Motor]\n"
            "Bu turda **yerel indeks veya web metni** bağlama eklenmedi. "
            "Yanıtını genel model bilginle ver; **uydurma tarih, isim veya alıntı yazma**. "
            "Emin değilsen kısaca «bu konuda yerel kaynağım yok, genel bilgiyle…» de. "
            "Kesin kaynak bilgisi uydurma. "
            "Son satırda: **Güven: düşük** (genel bilgi).\n"
        )
    lines = [
        "\n\n[TALİMAT — KAYNAK — Ana Motor — Ümit & Gökçenur]\n",
        f"Bağlamda **{source_count}** numaralı yerel parça",
    ]
    if web_present:
        lines.append(" ve **web araması** metni")
    lines.append(" var.\n")
    lines.append(
        "- Cevabını **önce bu kaynaklara** dayandır; mümkünse cümle sonunda **[K1]** gibi referans kullan.\n"
        "- Cevabın sonunda **Kaynak izi:** başlığı altında [K1]… etiketlerini eser/yol ile listele "
        "(yazar, eser adı; cilt/bölüm/sayfa **yalnızca bağlamda varsa**).\n"
    )
    if archive_primary:
        lines.append(
            "- İlim Hazinesi (arşiv) önceliklidir; külliyat veya dosya adını kısaca belirt.\n"
        )
    if web_present:
        lines.append("- Web bilgisinde site adı veya URL kısaca geçsin.\n")
    lines.append(no_fabricate)
    lines.append(
        "- Kaynaklar çelişirse ikisini de söyle; tek doğru uydurma.\n"
        "- Yanıtın **son satırı** şu biçimde bitsin: **Güven: yüksek|orta|düşük** — (kısa gerekçe).\n"
    )
    if distinct_sources >= 2:
        lines.append(
            cok_eser_sentez_directive(
                source_count=source_count, distinct_sources=distinct_sources
            )
        )
    return "".join(lines)
