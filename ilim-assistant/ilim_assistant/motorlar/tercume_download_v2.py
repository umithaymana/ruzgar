# Created by Ümit & Gökçenur
"""Tercüme Faz 11 — indirme URL düzeltme ve anlaşılır hata mesajları."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote, urlparse

DOWNLOAD_V2_VERSION = "tercume-download-v2-faz11-2026-05-31"


def normalize_download_url(url: str) -> dict[str, Any]:
    """Archive.org details / eksik uzantı → doğrudan PDF indirme linki."""
    raw = (url or "").strip()
    if not raw:
        return {"ok": False, "url": "", "error": "url boş", "normalized": False}

    ul = raw.lower()
    parsed = urlparse(raw)
    path = unquote(parsed.path or "")

    if "archive.org/details/" in ul:
        m = re.search(r"/details/([^/?#]+)", path, re.I)
        if m:
            ident = m.group(1).strip()
            from ilim_assistant.motorlar.tercume_eser_arama import _archive_pdf_download_url

            dl = _archive_pdf_download_url(ident)
            if dl:
                return {
                    "ok": True,
                    "url": dl,
                    "original_url": raw,
                    "normalized": True,
                    "reason": "archive_details_to_pdf",
                    "archive_identifier": ident,
                }
            return {
                "ok": True,
                "url": raw,
                "original_url": raw,
                "normalized": False,
                "reason": "archive_details_no_pdf",
                "hint": "Archive kaydında PDF bulunamadı — tarayıcıdan manuel seçin.",
            }

    if "archive.org/download/" in ul:
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 3 and parts[0].lower() == "download":
            fname = parts[-1]
            if not fname.lower().endswith((".pdf", ".epub", ".djvu", ".txt", ".zip")):
                ident = parts[1]
                from ilim_assistant.motorlar.tercume_eser_arama import _archive_pdf_download_url

                dl = _archive_pdf_download_url(ident)
                if dl:
                    return {
                        "ok": True,
                        "url": dl,
                        "original_url": raw,
                        "normalized": True,
                        "reason": "archive_download_folder_to_pdf",
                        "archive_identifier": ident,
                    }

    return {"ok": True, "url": raw, "original_url": raw, "normalized": False}


def format_download_error(
    message: str,
    *,
    url: str = "",
    status_code: int | None = None,
) -> str:
    """HTTP / ağ hatalarını Ümit abi için sade Türkçe'ye çevir."""
    m = (message or "").strip()
    ml = m.lower()
    code = status_code
    if code is None:
        for pat in (r"\b403\b", r"\b404\b", r"\b429\b", r"\b500\b", r"\b502\b", r"\b503\b"):
            hit = re.search(pat, ml)
            if hit:
                code = int(hit.group(0))
                break

    if code == 403 or "403" in ml or "forbidden" in ml:
        return (
            "Erişim engellendi (403) — telif, bölge kısıtı veya oturum gerekebilir. "
            "Archive.org’da tarayıcıdan açıp alternatif format deneyin."
        )
    if code == 404 or "404" in ml or "not found" in ml:
        return "Dosya bulunamadı (404) — link eski veya kaldırılmış olabilir."
    if code == 429 or "429" in ml or "rate limit" in ml:
        return "Site çok istek aldı (429) — birkaç dakika bekleyip tekrar deneyin."
    if code in (500, 502, 503) or "502" in ml or "503" in ml or "bad gateway" in ml:
        return "Kaynak site geçici olarak yanıt vermiyor — daha sonra tekrar deneyin."
    if "timeout" in ml or "timed out" in ml:
        return "Bağlantı zaman aşımı — site yavaş veya kapalı; ağınızı kontrol edin."
    if "ssl" in ml or "certificate" in ml:
        return "Güvenli bağlantı hatası (SSL) — site sertifikası sorunlu olabilir."
    if "permission" in ml or "access denied" in ml:
        return "İndirme izni yok — telif veya üyelik gerekebilir."
    if "too large" in ml or "çok büyük" in ml:
        return m
    if "boş" in ml or "too short" in ml or "kısa" in ml:
        return "İndirilen dosya boş veya hatalı sayfa — URL doğrudan PDF değil olabilir."
    if "url boş" in ml:
        return "İndirilecek adres yok — arama skoru düşük veya sonuç boş."

    host = ""
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        pass
    if host and "archive.org" in host and "metadata" in ml:
        return "Archive.org metadata okunamadı — internet bağlantısını kontrol edin."

    return m[:240] if m else "Bilinmeyen indirme hatası."
