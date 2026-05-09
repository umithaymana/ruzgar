# Created by Ümit & Gökçenur
"""
Rüzgar ana karar ağacı — İlim Hazinesi önceliği, sonra internet, akıllı filtre.

Mantık (Decision Tree):
  1) Önce arşiv (Mektubat, Hadis külliyatı vb.): yalnızca arsiv/ indeks parçaları.
  2) Güven yetersizse tam yerel indeks + (isteğe bağlı) DuckDuckGo web araması.
  3) Ümit & Gökçenur vizyonu: vakur, âlim/edip üslubu için sistem ve kullanıcı ekleri.

Durum metinleri masaüstü API akışında anlık olarak iletilir (desktop_server).

Web: DuckDuckGo + sayfa gövdesi ``ilim_ve_idrak.active_reader_fetch_url`` (BeautifulSoup, isteğe bağlı Playwright).
PDF derin okuma ve özet: ``ilim_ve_idrak`` + ``chat_core.prepare_turn``.
Tavily/Google ayrı anahtar ileride eklenebilir.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterator

from ilim_assistant.merkezi_zihin_havuzu import no_rag_modes

# --- Anlık durum (frontend / WebSocket) ---

STATUS_MEKTUBAT_SHELVES = "Şu an Mektubat rafları taranıyor…"
STATUS_ILIM_SCAN = "İlim Hazinesi külliyatları taranıyor (PDF/TXT)…"
STATUS_ARCHIVE_MATCH = "Arşivde eşleşme bulundu — alıntı zemini hazırlanıyor…"
STATUS_INTERNET_HADITH = "İnternette hadisler ve ilgili metinler araştırılıyor…"
STATUS_WEB_SCAN = "İnternette hızlı tarama yapılıyor (DuckDuckGo)…"
STATUS_FULL_INDEX = "Yerel indeks taranıyor (bilgi + arşiv birlikte)…"


def _score_threshold() -> float:
    try:
        return float(os.environ.get("RUZGAR_ARCHIVE_SCORE_MIN", "0.22"))
    except ValueError:
        return 0.22


def archive_match_is_strong(hits: list[tuple[str, str, float]]) -> bool:
    """Arşiv sonuçları tek başına yeterli mi? (kosinüs benzerliği eşiği)."""
    if not hits:
        return False
    best = float(hits[0][2])
    return best >= _score_threshold()


@dataclass
class RetrievalBundle:
    """retrieve_for_turn çıktısı — prepare_turn bu yapı ile beslenir."""

    hits: list[tuple[str, str, float]]
    suppress_main_web_search: bool
    archive_was_primary: bool
    ilim_citation_tail: str


def ilim_hazinesi_citation_directive() -> str:
    """Arşiv öncelikli turda modele verilen alıntı talimatı."""
    return (
        "\n\n[TALİMAT — İLİM HAZİNESİ — Ümit & Gökçenur]\n"
        "Aşağıdaki bağlam **Kültür ve İlim Hazinesi** (arsiv külliyatı) kaynaklıdır. "
        "Yanıtta mümkünse **kaynak dosya veya külliyat adını** kısaca belirt; "
        "alıntıları asgarî doğrudan metinle, **vakur ve edebî** bir üslupla (âlim/edip) sun.\n"
    )


def smart_filter_vision_directive() -> str:
    """Ümit & Gökçenur vizyonuna uygun sadeleştirme ve ölçülü dil."""
    return (
        "\n\n[TALİMAT — AKILLI FİLTRE — Ümit & Gökçenur]\n"
        "Bulduğun bilgiyi gereksiz tekrar, magazin dili ve polemik olmadan özetle; "
        "ölçülü, saygılı ve okura hürmet eden bir Türkçe ile sun. "
        "Şüphe veya çelişki varsa dürüstçe belirt.\n"
    )


def iter_archive_first_decision(
    msg: str,
    *,
    mode_norm: str,
    weather_q: bool,
    ilim_rag: bool,
    rag_top_k: int,
) -> Iterator[dict[str, Any]]:
    """
    Karar ağacını uygular; her adımda durum sözlüğü yield eder, sonunda sonuç.

    Yield edilen sözlükler:
      - {"kind": "status", "phase": str, "text": str}
      - {"kind": "result", "bundle": RetrievalBundle}
    """
    from ilim_assistant.rag_store import search as rag_search
    from ilim_assistant.rag_store import search_arsiv

    _empty = RetrievalBundle(
        hits=[],
        suppress_main_web_search=False,
        archive_was_primary=False,
        ilim_citation_tail="",
    )

    if mode_norm in no_rag_modes() or weather_q or not ilim_rag:
        yield {"kind": "result", "bundle": _empty}
        return

    yield {"kind": "status", "phase": "archive", "text": STATUS_MEKTUBAT_SHELVES}
    yield {"kind": "status", "phase": "archive_detail", "text": STATUS_ILIM_SCAN}

    k_ar = max(1, min(rag_top_k, 12))
    ar_hits = search_arsiv(msg, top_k=k_ar)

    if archive_match_is_strong(ar_hits):
        yield {
            "kind": "status",
            "phase": "archive_hit",
            "text": STATUS_ARCHIVE_MATCH,
        }
        tail = ilim_hazinesi_citation_directive() + smart_filter_vision_directive()
        try:
            from ilim_assistant.motorlar.arsiv_ileri_motoru import enrich_archive_turn

            _ex = enrich_archive_turn(msg, ar_hits).strip()
            if _ex:
                tail = tail.rstrip() + "\n\n" + _ex
        except Exception:
            pass
        yield {
            "kind": "result",
            "bundle": RetrievalBundle(
                hits=ar_hits,
                suppress_main_web_search=True,
                archive_was_primary=True,
                ilim_citation_tail=tail,
            ),
        }
        return

    yield {"kind": "status", "phase": "web", "text": STATUS_INTERNET_HADITH}
    yield {"kind": "status", "phase": "web_engine", "text": STATUS_WEB_SCAN}
    yield {"kind": "status", "phase": "full_index", "text": STATUS_FULL_INDEX}

    hits = rag_search(msg, top_k=k_ar)
    tail = smart_filter_vision_directive()
    yield {
        "kind": "result",
        "bundle": RetrievalBundle(
            hits=hits,
            suppress_main_web_search=False,
            archive_was_primary=False,
            ilim_citation_tail=tail,
        ),
    }


def merge_ilim_tail(user_payload: str, tail: str) -> str:
    if not tail:
        return user_payload
    return user_payload.rstrip() + tail


def run_retrieval_with_status_events(
    msg: str,
    mode_norm: str,
    weather_q: bool,
    ilim_rag: bool,
    rag_top_k: int,
) -> tuple[RetrievalBundle, list[dict[str, Any]]]:
    """
    Masaüstü akışı: durum çerçeveleri + nihai RetrievalBundle (Ümit & Gökçenur).
    """
    out_events: list[dict[str, Any]] = []
    bundle: RetrievalBundle | None = None
    for ev in iter_archive_first_decision(
        msg,
        mode_norm=mode_norm,
        weather_q=weather_q,
        ilim_rag=ilim_rag,
        rag_top_k=rag_top_k,
    ):
        if ev.get("kind") == "status":
            out_events.append(
                {
                    "type": "status",
                    "phase": str(ev.get("phase") or "retrieval"),
                    "text": str(ev.get("text") or ""),
                }
            )
        elif ev.get("kind") == "result":
            bundle = ev["bundle"]
    if bundle is None:
        bundle = RetrievalBundle(
            hits=[],
            suppress_main_web_search=False,
            archive_was_primary=False,
            ilim_citation_tail="",
        )
    return bundle, out_events
