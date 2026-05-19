# Created by Ümit & Gökçenur
"""
Rüzgar ana karar ağacı — İlim Hazinesi önceliği, sonra internet, akıllı filtre.

Mantık (Decision Tree v2 — Ana Motor planı ile):
  - gundelik / islem / hafiza: retrieval yok (doğrudan LLM + web planı)
  - bilgi: yerel indeks; arşiv atlanır; web kapatılmaz
  - bilim: arşiv önce (güçlü eşleşmede web kapalı)
  - dilbilgisi: yalnızca knowledge indeksi
  - varsayılan: arşiv → tam indeks (v1)

Durum metinleri masaüstü API akışında anlık olarak iletilir (desktop_server).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterator

from ilim_assistant.ana_motor_plan import looks_like_encyclopedic_fact_question

# --- Anlık durum (frontend / WebSocket) ---

STATUS_MEKTUBAT_SHELVES = "Şu an Mektubat rafları taranıyor…"
STATUS_ILIM_SCAN = "İlim Hazinesi külliyatları taranıyor (PDF/TXT)…"
STATUS_ARCHIVE_MATCH = "Arşivde eşleşme bulundu — alıntı zemini hazırlanıyor…"
STATUS_INTERNET_HADITH = "İnternette hadisler ve ilgili metinler araştırılıyor…"
STATUS_WEB_SCAN = "İnternette hızlı tarama yapılıyor (DuckDuckGo)…"
STATUS_FULL_INDEX = "Yerel indeks taranıyor (bilgi + arşiv birlikte)…"
STATUS_BILGI_INDEX = "Genel bilgi — yerel ilim indeksi taranıyor…"
STATUS_BILIM_FAST_INDEX = "Yerel indeks (hızlı tur) — ağır arşiv atlandı…"
STATUS_GEMINI_FIRST = "Gemini hızlı yanıt hazırlanıyor — yerel indeks ve web atlandı…"
STATUS_DILBILGISI_INDEX = "Dilbilgisi notları taranıyor…"
STATUS_SKIP_RETRIEVAL = "Kaynak taraması atlandı — doğrudan yanıt…"


def _bilim_gemini_index_first_enabled() -> bool:
    """Gemini açıkken ansiklopedik tarih sorusunda arşiv önceliğini atla (Faz 9 hız)."""
    if os.environ.get("RUZGAR_FAZ9_BILIM_FAST_INDEX", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    try:
        from ilim_assistant.llm_gemini import gemini_configured

        return gemini_configured()
    except Exception:
        return False


def _gemini_first_for_encyclopedic_enabled() -> bool:
    """Tek cevaplı genel bilgi/tarih sorularında RAG'i tamamen atla (Faz 9 hız)."""
    if os.environ.get("RUZGAR_FAZ9_GEMINI_FIRST_FOR_FACTS", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    try:
        from ilim_assistant.llm_gemini import gemini_configured

        return gemini_configured()
    except Exception:
        return False


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


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(getattr(question_plan, "primary", "") or "").strip().lower()
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return ""


def _plan_prefer_archive(question_plan: Any | None) -> bool:
    if question_plan is None:
        return False
    if hasattr(question_plan, "prefer_archive"):
        return bool(question_plan.prefer_archive)
    if isinstance(question_plan, dict):
        return bool(question_plan.get("prefer_archive"))
    return False


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
        "alıntları asgarî doğrudan metinle, **vakur ve edebî** bir üslupla (âlim/edip) sun.\n"
    )


def smart_filter_vision_directive() -> str:
    """Ümit & Gökçenur vizyonuna uygun sadeleştirme ve ölçülü dil."""
    return (
        "\n\n[TALİMAT — AKILLI FİLTRE — Ümit & Gökçenur]\n"
        "Bulduğun bilgiyi gereksiz tekrar, magazin dili ve polemik olmadan özetle; "
        "ölçülü, saygılı ve okura hürmet eden bir Türkçe ile sun. "
        "Şüphe veya çelişki varsa dürüstçe belirt.\n"
    )


def _empty_bundle() -> RetrievalBundle:
    return RetrievalBundle(
        hits=[],
        suppress_main_web_search=False,
        archive_was_primary=False,
        ilim_citation_tail="",
    )


def _yield_index_only(
    msg: str,
    rag_top_k: int,
    *,
    status_text: str,
    suppress_web: bool,
) -> Iterator[dict[str, Any]]:
    from ilim_assistant.rag_store import search as rag_search

    yield {"kind": "status", "phase": "full_index", "text": status_text}
    k = max(1, min(rag_top_k, 12))
    hits = rag_search(msg, top_k=k)
    tail = smart_filter_vision_directive()
    yield {
        "kind": "result",
        "bundle": RetrievalBundle(
            hits=hits,
            suppress_main_web_search=suppress_web,
            archive_was_primary=False,
            ilim_citation_tail=tail,
        ),
    }


def _yield_gemini_first() -> Iterator[dict[str, Any]]:
    yield {"kind": "status", "phase": "gemini_first", "text": STATUS_GEMINI_FIRST}
    yield {
        "kind": "result",
        "bundle": RetrievalBundle(
            hits=[],
            suppress_main_web_search=True,
            archive_was_primary=False,
            ilim_citation_tail=smart_filter_vision_directive(),
        ),
    }


def _yield_archive_first(
    msg: str,
    rag_top_k: int,
) -> Iterator[dict[str, Any]]:
    from ilim_assistant.rag_store import search as rag_search
    from ilim_assistant.rag_store import search_arsiv

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


def iter_archive_first_decision(
    msg: str,
    *,
    mode_norm: str,
    weather_q: bool,
    ilim_rag: bool,
    rag_top_k: int,
    question_plan: Any | None = None,
    search_text: str | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Karar ağacını uygular; her adımda durum sözlüğü yield eder, sonunda sonuç.

    Yield edilen sözlükler:
      - {"kind": "status", "phase": str, "text": str}
      - {"kind": "result", "bundle": RetrievalBundle}
    """
    from ilim_assistant.chat_core import _NO_RAG_MODES

    if mode_norm in _NO_RAG_MODES or weather_q or not ilim_rag:
        if mode_norm == "hafiza":
            yield {
                "kind": "status",
                "phase": "skip",
                "text": "Hafıza modu — yerel sözlük / sohbet (ağır indeks atlandı)…",
            }
        yield {"kind": "result", "bundle": _empty_bundle()}
        return

    q = (search_text or msg or "").strip() or msg
    primary = _plan_primary(question_plan)
    plan_on = os.environ.get("RUZGAR_ANA_MOTOR_PLAN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )

    if plan_on and primary:
        if primary in ("gundelik", "islem", "dosya", "hafiza", "hava"):
            yield {
                "kind": "status",
                "phase": "skip",
                "text": STATUS_SKIP_RETRIEVAL,
            }
            yield {"kind": "result", "bundle": _empty_bundle()}
            return

        if primary == "dilbilgisi":
            yield from _yield_index_only(
                q,
                rag_top_k,
                status_text=STATUS_DILBILGISI_INDEX,
                suppress_web=False,
            )
            return

        if primary == "bilgi":
            if _gemini_first_for_encyclopedic_enabled() and looks_like_encyclopedic_fact_question(q):
                yield from _yield_gemini_first()
                return
            yield from _yield_index_only(
                q,
                rag_top_k,
                status_text=STATUS_BILGI_INDEX,
                suppress_web=False,
            )
            return

        if primary == "bilim" or _plan_prefer_archive(question_plan):
            if (
                primary == "bilim"
                and (_gemini_first_for_encyclopedic_enabled() or _bilim_gemini_index_first_enabled())
                and looks_like_encyclopedic_fact_question(q)
            ):
                if _gemini_first_for_encyclopedic_enabled():
                    yield from _yield_gemini_first()
                else:
                    yield from _yield_index_only(
                        q,
                        rag_top_k,
                        status_text=STATUS_BILIM_FAST_INDEX,
                        suppress_web=False,
                    )
                return
            yield from _yield_archive_first(q, rag_top_k)
            return

    yield from _yield_archive_first(q, rag_top_k)


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
    question_plan: Any | None = None,
    search_text: str | None = None,
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
        question_plan=question_plan,
        search_text=search_text,
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
        bundle = _empty_bundle()
    return bundle, out_events
