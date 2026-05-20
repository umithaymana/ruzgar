# Created by Ümit & Gökçenur
"""Ana Motor — numaralı kaynak blokları ve zorunlu atıf talimatı (Faz 9.2)."""

from __future__ import annotations

import os
from typing import Any


def _chunk_max_chars() -> int:
    try:
        return max(400, int(os.environ.get("RUZGAR_KAYNAK_CHUNK_MAX", "2400")))
    except ValueError:
        return 2400


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
        label = f"[K{i}] {src}"
        if archive_primary:
            label = f"[K{i} — İlim Hazinesi] {src}"
        meta = f"(benzerlik: {float(score):.2f})"
        out.append((f"{label} {meta}\n{body}", src))
    return out


def citation_directive_for_turn(
    *,
    source_count: int,
    archive_primary: bool,
    web_present: bool,
) -> str:
    """Modele zorunlu kaynak / güven talimatı."""
    if source_count <= 0 and not web_present:
        return (
            "\n\n[TALİMAT — KAYNAK — Ana Motor]\n"
            "Bu turda **yerel indeks veya web metni** bağlama eklenmedi. "
            "Yanıtını genel model bilginle ver; **uydurma tarih, isim veya alıntı yazma**. "
            "Emin değilsen kısaca «bu konuda yerel kaynağım yok, genel bilgiyle…» de. "
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
    )
    if archive_primary:
        lines.append(
            "- İlim Hazinesi (arşiv) önceliklidir; külliyat veya dosya adını kısaca belirt.\n"
        )
    if web_present:
        lines.append("- Web bilgisinde site adı veya URL kısaca geçsin.\n")
    lines.append(
        "- Kaynaklar çelişirse ikisini de söyle; tek doğru uydurma.\n"
        "- Yanıtın **son satırı** şu biçimde bitsin: **Güven: yüksek|orta|düşük** — (kısa gerekçe).\n"
    )
    return "".join(lines)
