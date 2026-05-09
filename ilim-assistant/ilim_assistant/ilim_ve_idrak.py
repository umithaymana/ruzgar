# Created by Ümit & Gökçenur
"""
İlim ve İdrak — Aktif Okuyucu: web sayfasına gir, PDF’i derinlemesine oku, özü özetle.

- Web: BeautifulSoup ile metin; isteğe bağlı Playwright (RUZGAR_PLAYWRIGHT=1).
- PDF: pypdf; boşsa isteğe bağlı OCR (pytesseract + pdf2image — ayrı kurulum).
- Özet: âlim/edip üslubuna uygun kısa talimatlar (model + hafif çıkarma).
"""

from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path
from typing import Tuple

_PKG_ROOT = Path(__file__).resolve().parent.parent

# Büyük kütüphane / yavaş ayna sayfaları: okuma 300 sn (Read timeout). Bağlantı ayrı kısa tutulur.
_WEB_FETCH_CONNECT = float(os.environ.get("WEB_FETCH_CONNECT_TIMEOUT", "15"))
_WEB_FETCH_READ = float(
    os.environ.get(
        "WEB_FETCH_READ_TIMEOUT",
        os.environ.get("WEB_FETCH_TIMEOUT", "300"),
    )
)
_MAX_FETCH_CHARS = int(os.environ.get("WEB_FETCH_MAX_CHARS", "18000"))
_USER_AGENT = os.environ.get(
    "WEB_USER_AGENT",
    "Mozilla/5.0 (compatible; Ruzgar-AktifOkuyucu/1.0; +Ümit&Gökçenur)",
)

# Motorlara eklenecek kısa hatırlatıcı (tüm build_motor_context sonları)
ILIM_IDRAK_MOTOR_FOOTER = (
    "\n\n[Aktif Okuyucu — Ümit & Gökçenur — İlim ve İdrak]\n"
    "Kaynak adıyla yetinme; bağlama veya URL’ye girilmiş metnin özünü okuyup vakur bir üslupla aktar.\n"
)

_GLOBAL_USER_APPENDIX = (
    "\n\n[TALİMAT — İLİM VE İDRAK — Ümit & Gökçenur]\n"
    "**Aktif Okuyucu:** Web veya arşivde bulduğun bilgiyi yalnızca link veya kaynak adı olarak verme; "
    "aşağıdaki **okunmuş metin** üzerinden yanıtla. Uzun metinleri **3–4 cümlede**, ana fikri bozmadan, "
    "âlim veya edip edasıyla özetleyebilirsin (sesli yanıtta özellikle kısa tut).\n"
)

# Yerel dosya / kütüphane: açma süresi (sohbet ve RAG indeks PDF çıkarma) — env ile okuyun


def _acil_okuma_model_append() -> str:
    sec = int(float(os.environ.get("RUZGAR_ACIL_OKUMA_SEC", "10")))
    return (
        f"\n\n[TALİMAT — Acil Okuma — Ümit & Gökçenur]\n"
        f"Bir arşiv veya kütüphane dosyasını **{sec} saniye** içinde tam olarak açıp metin çıkaramazsan, "
        "**tüm külliyatı veya diski uç uca taramayı bırak**; kullanıcıya doğrudan ve net şekilde şunu söyle: "
        "**«Dosyayı buldum ama açamıyorum.»** Sebep için kısaca (zaman aşımı, çok büyük dosya, "
        "şifreli/bozuk PDF) ekle; varsayım ve uydurma metin verme.\n"
    )


def enabled() -> bool:
    return os.environ.get("RUZGAR_ILIM_IDRAK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def append_global_directive(user_payload: str) -> str:
    if not enabled():
        return user_payload
    out = user_payload.rstrip() + _GLOBAL_USER_APPENDIX
    if os.environ.get("RUZGAR_ACIL_OKUMA_PROMPT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        out = out.rstrip() + _acil_okuma_model_append()
    return out


def extractive_summary_tr(text: str, max_sentences: int = 4, max_chars: int = 3600) -> str:
    """Çok uzun ham metni TTS / bağlam için kısalt (çıkarma özet)."""
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    parts = re.split(r"(?<=[.!?…])\s+", t)
    out: list[str] = []
    n = 0
    for p in parts:
        p = p.strip()
        if not p:
            continue
        out.append(p)
        n += 1
        if n >= max_sentences:
            break
        if sum(len(x) for x in out) >= max_chars:
            break
    s = " ".join(out).strip()
    if len(s) > max_chars:
        s = s[: max_chars - 1].rstrip() + "…"
    return s or t[:max_chars]


def resolve_pdf_path_from_rag_source(source: str) -> Path | None:
    """RAG kaynak yolu (ör. arsiv/Hadis_Kulliyati/x.pdf) → mutlak dosya."""
    s = (source or "").replace("\\", "/").strip()
    if not s.lower().endswith(".pdf"):
        return None
    p = (_PKG_ROOT / s).resolve()
    try:
        p.relative_to(_PKG_ROOT.resolve())
    except ValueError:
        return None
    if p.is_file():
        return p
    return None


def read_pdf_text_basic(path: Path, *, max_pages: int | None = None) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(str(path))
        parts: list[str] = []
        for i, page in enumerate(reader.pages):
            if max_pages is not None and i >= max_pages:
                break
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n".join(parts).strip()
    except Exception:
        return ""


def extract_pdf_plain_with_deadline(
    path: Path,
    *,
    deadline_sec: float,
    max_pages: int | None = None,
) -> tuple[str, bool]:
    """
    PDF metin çıkarma — ayrı iş parçacığında süre sınırı.
    Dönüş: (metin, zaman_aşımı_oldu_mu). Zaman aşımında metin \"\".
    """
    if deadline_sec <= 0:
        return read_pdf_text_basic(path, max_pages=max_pages), False

    def _job() -> str:
        return read_pdf_text_basic(path, max_pages=max_pages)

    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_job)
        try:
            return (fut.result(timeout=deadline_sec).strip(), False)
        except FuturesTimeout:
            return ("", True)
        except Exception:
            return ("", False)


def read_pdf_ocr_fallback(path: Path, max_pages: int = 3) -> str:
    """Taranmış PDF — isteğe bağlı. pdf2image + pytesseract kurulu olmalı."""
    if os.environ.get("RUZGAR_PDF_OCR", "0").strip() not in ("1", "true", "yes"):
        return ""
    try:
        import pytesseract  # type: ignore
        from pdf2image import convert_from_path  # type: ignore
    except ImportError:
        return ""
    try:
        images = convert_from_path(str(path), first_page=1, last_page=max_pages)
        bits: list[str] = []
        for img in images:
            bits.append(pytesseract.image_to_string(img, lang="tur+osd") or "")
        return "\n".join(bits).strip()
    except Exception:
        return ""


def acil_okuma_failure_block(source_key: str) -> str:
    """Kullanıcı ve modele görünen net sistem mesajı (path var, açılamadı)."""
    return (
        f"=== Acil Okuma — {source_key} ===\n"
        "Dosyayı buldum ama açamıyorum ( zaman aşımı veya dosya çok büyük / okunamayan PDF ). "
        "Lütfen daha küçük bir bölüm veya başka bir kopya dene.\n"
    )


def pdf_deep_read(source_key: str, max_chars: int = 6000) -> str:
    """Arşiv PDF tek kaynağı — metin çıkar + süz + kısalt (Acil Okuma süresi ile sınırlı)."""
    path = resolve_pdf_path_from_rag_source(source_key)
    if not path:
        return ""
    try:
        chat_max_pages = int(os.environ.get("RUZGAR_PDF_CHAT_MAX_PAGES", "64"))
    except ValueError:
        chat_max_pages = 64
    max_pages_cap = chat_max_pages if chat_max_pages > 0 else None
    deadline = float(os.environ.get("RUZGAR_ACIL_OKUMA_SEC", "10"))
    raw, timed_out = extract_pdf_plain_with_deadline(
        path, deadline_sec=deadline, max_pages=max_pages_cap
    )
    if timed_out:
        return acil_okuma_failure_block(source_key)
    if len(raw.strip()) < 80:
        ocr_deadline = max(3.0, min(float(deadline), 12.0))

        def _ocr() -> str:
            return read_pdf_ocr_fallback(path)

        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(_ocr)
            try:
                raw = (fut.result(timeout=ocr_deadline) or "").strip()
            except FuturesTimeout:
                return acil_okuma_failure_block(source_key)
    raw = raw.strip()
    if not raw:
        return acil_okuma_failure_block(source_key)
    return extractive_summary_tr(raw, max_sentences=12, max_chars=max_chars)


def build_pdf_hazine_enrichment(
    hits: list[tuple[str, str, float]],
    *,
    budget_chars: int = 14000,
) -> str:
    """RAG isabetlerindeki PDF dosyaları için derin metin (İlim Hazinesi)."""
    seen: set[str] = set()
    chunks: list[str] = []
    used = 0
    for _t, src, _sc in hits:
        if not src.lower().endswith(".pdf") or src in seen:
            continue
        seen.add(src)
        body = pdf_deep_read(src, max_chars=min(8000, budget_chars - used))
        if not body:
            continue
        block = f"=== PDF derin okuma (Ümit & Gökçenur) — {src} ===\n{body}"
        chunks.append(block)
        used += len(block)
        if used >= budget_chars:
            break
    if not chunks:
        return ""
    return "\n\n".join(chunks)


def _fetch_static_html(url: str, max_chars: int) -> Tuple[str, str]:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as e:
        return "", f"eksik paket: {e}"
    try:
        r = requests.get(
            url,
            stream=True,
            timeout=(_WEB_FETCH_CONNECT, _WEB_FETCH_READ),
            headers={"User-Agent": _USER_AGENT, "Accept-Language": "tr,en;q=0.9"},
        )
        r.raise_for_status()
        ct = (r.headers.get("Content-Type") or "").lower()
        if "charset=" not in ct:
            r.encoding = "utf-8"
        if "application/pdf" in ct or url.lower().endswith(".pdf"):
            return "", "pdf-doğrudan"
        if "text/html" not in ct and "application/xhtml" not in ct:
            return "", f"HTML değil: {ct[:80]}"

        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
        if len(body) > max_chars:
            body = body[:max_chars] + "\n\n[… kesildi — Aktif Okuyucu …]"
        return body, "ok"
    except Exception as e:
        return "", str(e)


def _fetch_playwright(url: str, max_chars: int) -> Tuple[str, str]:
    if os.environ.get("RUZGAR_PLAYWRIGHT", "0").strip() not in ("1", "true", "yes"):
        return "", "playwright-kapalı"
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "", "playwright-yok"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(
                url,
                wait_until="networkidle",
                timeout=int(_WEB_FETCH_READ * 1000),
            )
            text = page.inner_text("body")
            browser.close()
        t = (text or "").strip()
        if len(t) > max_chars:
            t = t[:max_chars] + "\n\n[… kesildi — Playwright …]"
        return t, "ok-playwright"
    except Exception as e:
        return "", f"playwright:{e}"


def active_reader_fetch_url(url: str, max_chars: int | None = None) -> Tuple[str, str]:
    """
    Aktif Okuyucu: önce statik HTML, kısa/boşsa isteğe bağlı Playwright.
    Dönüş: (metin, durum_kısası)
    """
    mc = max_chars if max_chars is not None else _MAX_FETCH_CHARS
    text, st = _fetch_static_html(url, mc)
    if st == "ok" and len(text) >= 400:
        return text, st
    pw, st2 = _fetch_playwright(url, mc)
    if pw and len(pw) >= 200:
        return pw, st2
    if text:
        return text, st
    return pw, st2 or st


def expose_extractive_for_web_body(text: str) -> str:
    """Web gövdesi çok uzunsa model öncesi hafif kısaltma."""
    if len(text) <= 9000:
        return text
    return extractive_summary_tr(text, max_sentences=10, max_chars=8500)
