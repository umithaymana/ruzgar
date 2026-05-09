"""
Dinamit Geliştirme — otonom araştırma (5 paralel kaynak), duygu ipuçları, çekirdek damarı.
Ümit & Gökçenur — RÜZGAR ajan katmanı.
"""

from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Literal

_MIMAR = "Ümit & Gökçenur"
_LABEL = "[DİNAMİT GELİŞTİRME — Ümit & Gökçenur]"


def dinamit_heartbeat() -> str:
    """Tüm motorlara eklenecek tek satırlık bağ/bağlam ipucu (kısa)."""
    if os.environ.get("RUZGAR_DINAMIT", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return ""
    return (
        f"{_LABEL} Ajan katmanı etkin: otonom araştırma, duygu uyumu, görsel ve hatırlatıcılar "
        f"ile mimarın yanındayım.\n"
    )


def _enabled() -> bool:
    return os.environ.get("RUZGAR_DINAMIT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _format_rag_slice(hits: list[tuple[str, str, float]], title: str, n: int) -> str:
    lines = [title, ""]
    for i, (text, src, score) in enumerate(hits[:n], 1):
        t = (text or "").strip().replace("\r\n", "\n")
        if len(t) > 2400:
            t = t[:2400] + "…"
        lines.append(f"({i}) [{src}] skor~{score:.3f}\n{t}\n")
    return "\n".join(lines)


def _task_arsiv(msg: str, k: int) -> str:
    from ilim_assistant.rag_store import search_arsiv

    hits = search_arsiv(msg, top_k=k)
    return _format_rag_slice(
        hits,
        "=== Kaynak 1/5 — Yerel arşiv (külliyat / İlim Hazinesi) ===",
        k,
    )


def _task_full_index(msg: str, k: int) -> str:
    from ilim_assistant.rag_store import search

    hits = search(msg, top_k=k)
    return _format_rag_slice(
        hits,
        "=== Kaynak 2/5 — Tam yerel indeks (bilgi + arşiv) ===",
        k,
    )


def _task_web_packed(msg: str, fetch_n: int, label: str) -> str:
    from ilim_assistant.web_tools import build_web_context, strip_urls_for_search

    q = strip_urls_for_search(msg).strip()
    if not q:
        return f"{label}\n[Web: boş sorgu.]\n"
    try:
        return build_web_context(
            q,
            max_results=10,
            fetch_first_n_urls=fetch_n,
        )
    except Exception as e:
        return f"{label}\n[Web hata: {e}]\n"


def _task_web_variant(msg: str, suffix: str, fetch_n: int, label: str) -> str:
    from ilim_assistant.web_tools import build_web_context, strip_urls_for_search

    q = (strip_urls_for_search(msg) + " " + suffix).strip()
    if not q:
        return f"{label}\n[Web: boş sorgu.]\n"
    try:
        ctx = build_web_context(
            q,
            max_results=8,
            fetch_first_n_urls=fetch_n,
        )
        return f"{label}\n{ctx}"
    except Exception as e:
        return f"{label}\n[Web hata: {e}]\n"


def _task_url_only_fetch(msg: str) -> str:
    """DDG 5. organik sonuç — gövde (önceki web görevleri genelde ilk URL’leri alır)."""
    from duckduckgo_search import DDGS

    from ilim_assistant.web_tools import fetch_url_text, strip_urls_for_search

    q = strip_urls_for_search(msg).strip()
    if not q:
        return "=== Kaynak 5/5 — Ek web URL ===\n[Boş]\n"
    try:
        with DDGS() as ddgs:
            rows = list(ddgs.text(q, max_results=12))
    except Exception as e:
        return f"=== Kaynak 5/5 — Ek web URL ===\n{e}\n"
    idx = min(4, len(rows) - 1)
    if idx < 0 or not rows:
        return "=== Kaynak 5/5 — Ek web URL ===\n[Sonuç yok]\n"
    href = (rows[idx].get("href") or "").strip()
    if not href.startswith("http"):
        return "=== Kaynak 5/5 — Ek web URL ===\n[Geçersiz link]\n"
    txt, st = fetch_url_text(href)
    if txt:
        body = txt[:12000]
        if len(txt) > 12000:
            body += "…"
        return (
            f"=== Kaynak 5/5 — Ek web URL (DDG #{idx + 1}) ===\n{href}\n({st})\n\n{body}"
        )
    return f"=== Kaynak 5/5 — Ek web URL ===\n{href}\n[{st}]\n"


def run_autonomous_five_sources(user_message: str) -> str:
    """
    Web + yerel arşiv: 5 görev paralel — sonuçlar tek sentez bloğunda birleşir.
    """
    if not _enabled():
        return ""
    msg = (user_message or "").strip()
    if not msg:
        return ""
    try:
        k = max(3, min(int(os.environ.get("DINAMIT_RAG_K", "5")), 12))
    except ValueError:
        k = 5
    f1 = max(1, min(int(os.environ.get("DINAMIT_WEB_FETCH_A", "2")), 4))
    f2 = max(1, min(int(os.environ.get("DINAMIT_WEB_FETCH_B", "2")), 4))

    tasks: list[tuple[str, Any]] = [
        ("arsiv", lambda: _task_arsiv(msg, k)),
        ("full", lambda: _task_full_index(msg, k)),
        ("web_a", lambda: _task_web_packed(msg, f1, "=== Kaynak 3/5 — Web tarama A ===")),
        (
            "web_b",
            lambda: _task_web_variant(
                msg,
                "özet açıklama",
                f2,
                "=== Kaynak 4/5 — Web tarama B (varyasyon sorgusu) ===",
            ),
        ),
        ("url5", lambda: _task_url_only_fetch(msg)),
    ]

    chunks: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(fn): name for name, fn in tasks}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                chunks[name] = fut.result()
            except Exception as e:
                chunks[name] = f"[{name} hata: {e}]"

    order = ["arsiv", "full", "web_a", "web_b", "url5"]
    body = "\n\n".join(chunks.get(ky, "") for ky in order)
    return (
        "\n\n[DİNAMİT — OTONOM ARAŞTIRMA MODU — Ümit & Gökçenur]\n"
        "Aşağıda **5 paralel kaynaktan** (2× yerel gömme arama, 2× web tarayı, 1× ek URL gövdesi) "
        "gelir. Çelişkileri açıkça belirt; mümkünse tek paragrafta **sentezle**.\n\n"
        + body.strip()
        + "\n\n[/DİNAMİT]\n"
    )


EmotionKind = Literal["yorgun", "mutlu", "ciddi", "notr"]


_YORGUN_W = (
    "yorgun",
    "bitkin",
    "uykum",
    "uykum var",
    "halsiz",
    "yoruldum",
    "enerjim yok",
)
_MUTLU_W = (
    "mutluyum",
    "sevindim",
    "harika",
    "süper",
    "neşeliyim",
    "güzel",
    "teşekkür",
)
_CIDDI_W = (
    "ciddi",
    "önemli",
    "acil",
    "dikkat",
    "lütfen ciddi",
    "ciddiyet",
    "mesele",
)


def infer_emotion_from_text(text: str) -> EmotionKind:
    low = (text or "").lower()
    for w in _YORGUN_W:
        if w in low:
            return "yorgun"
    for w in _MUTLU_W:
        if w in low:
            return "mutlu"
    for w in _CIDDI_W:
        if w in low:
            return "ciddi"
    return "notr"


def infer_emotion_from_mic_energy(energy_01: float | None) -> EmotionKind | None:
    """
    energy_01: 0..1 ortalama seviye (Web Audio).
    Çok düşük → yorgun tahmini; çok yüksek → mutlu/neşeli tahmini — kaba sezgisel.
    """
    if energy_01 is None:
        return None
    try:
        e = float(energy_01)
    except (TypeError, ValueError):
        return None
    e = max(0.0, min(1.0, e))
    if e < 0.22:
        return "yorgun"
    if e > 0.72:
        return "mutlu"
    return None


def fuse_emotion(
    text: str,
    mic_energy_01: float | None,
) -> EmotionKind:
    """Metin öncelikli; enerji yalnızca 'notr'da kırılır."""
    t = infer_emotion_from_text(text)
    if t != "notr":
        return t
    m = infer_emotion_from_mic_energy(mic_energy_01)
    if m:
        return m
    return "notr"


def emotion_ses_adjustments(kind: EmotionKind) -> tuple[float, float, str]:
    """
    (hiz çarpanı çarpımı, huzur çarpanı çarpımı, edge pitch eki).
    Varsayılan 1.0 = değişmez.
    """
    if kind == "yorgun":
        return 0.92, 0.9, "-2Hz"
    if kind == "mutlu":
        return 1.05, 1.02, "+2Hz"
    if kind == "ciddi":
        return 0.94, 0.93, "-3Hz"
    return 1.0, 1.0, "+0Hz"


def merge_pitch(base_pitch: str, extra: str) -> str:
    """'+1Hz' + '-2Hz' gibi kaba birleştirme — Edge TTS için tek dize."""
    if not extra or extra == "+0Hz":
        return base_pitch
    bm = re.search(r"([+-]?\d+)\s*Hz", base_pitch or "", re.I)
    em = re.search(r"([+-]?\d+)\s*Hz", extra or "", re.I)
    if not bm:
        return extra
    if not em:
        return base_pitch
    try:
        total = int(bm.group(1)) + int(em.group(1))
    except ValueError:
        return base_pitch
    sign = "+" if total >= 0 else ""
    return f"{sign}{total}Hz"
