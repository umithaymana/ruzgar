# Created by Ümit & Gökçenur
"""Tercüme Faz 9 — kapı kontrol (OCR, beyin, arşiv, isteğe dosya)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

PREFLIGHT_VERSION = "tercume-preflight-v9-faz9-2026-05-31"


def _check(label: str, ok: bool, *, detail: str = "", required: bool = True) -> dict[str, Any]:
    return {
        "id": label.lower().replace(" ", "_"),
        "label": label,
        "ok": bool(ok),
        "detail": detail,
        "required": required,
    }


def _brain_ok() -> tuple[bool, str]:
    try:
        from ilim_assistant.motorlar.tercume_llm import translation_brain_status

        st = translation_brain_status()
        if st.get("ready"):
            chain = st.get("chain") or []
            detail = " + ".join(chain) if chain else "hazır"
            if st.get("ollama_only"):
                detail = f"Ollama-only · {st.get('ollama_model') or detail}"
            return True, detail
        if st.get("ollama_only"):
            return False, "Ollama gerekli (RUZGAR_OLLAMA_ONLY=1) — ollama serve + model"
        return False, "GEMINI_API_KEY, GROQ_API_KEY veya Ollama gerekli"
    except Exception:
        pass
    gem = bool((os.environ.get("GEMINI_API_KEY") or os.environ.get("GLOBAL_API_KEY") or "").strip())
    groq = bool((os.environ.get("GROQ_API_KEY") or "").strip())
    ollama = False
    try:
        from ilim_assistant.llm_ollama import ollama_reachable

        ollama = bool(ollama_reachable())
    except Exception:
        pass
    if gem or groq or ollama:
        parts = []
        if gem:
            parts.append("Gemini")
        if groq:
            parts.append("Groq")
        if ollama:
            parts.append("Ollama")
        return True, " + ".join(parts)
    return False, "GEMINI_API_KEY, GROQ_API_KEY veya Ollama gerekli"


def _internet_ok(timeout: float = 4.0) -> tuple[bool, str]:
    try:
        req = Request("https://duckduckgo.com/", headers={"User-Agent": "RuzgarTercume/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.status < 500, f"HTTP {resp.status}"
    except Exception as exc:
        return False, str(exc)[:120]


def _resolve_rel(rel: str) -> Path | None:
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        return None
    try:
        from ilim_assistant.motorlar.tercume_read_pipeline import resolve_book_path

        target, _ = resolve_book_path(raw)
        return target if target.is_file() else None
    except Exception:
        return None


def run_tercume_preflight(
    *,
    rel: str = "",
    need_internet: bool = False,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    try:
        from ilim_assistant.motorlar.tercume_ocr_runtime import ocr_runtime_status

        ocr = ocr_runtime_status()
        checks.append(
            _check(
                "OCR (Tesseract)",
                bool(ocr.get("available")),
                detail=str(ocr.get("hint") or "")[:200],
                required=False,
            )
        )
    except Exception as exc:
        checks.append(_check("OCR (Tesseract)", False, detail=str(exc)[:120], required=False))

    brain_ok, brain_detail = _brain_ok()
    checks.append(_check("Çeviri beyni", brain_ok, detail=brain_detail, required=True))

    arsiv_ok = False
    arsiv_detail = ""
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(None)
        if root:
            arsiv = Path(root) / "ilim-assistant" / "arsiv"
            arsiv_ok = arsiv.is_dir()
            n = sum(1 for _ in arsiv.rglob("*") if _.is_file()) if arsiv_ok else 0
            arsiv_detail = f"{arsiv} · ~{n} dosya" if arsiv_ok else "ilim-assistant/arsiv yok"
    except Exception as exc:
        arsiv_detail = str(exc)[:80]
    checks.append(_check("Yerel arşiv", arsiv_ok, detail=arsiv_detail, required=False))

    pdf_ocr = os.environ.get("RUZGAR_TERCUME_PDF_OCR", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    pdf2_ok = False
    try:
        import pdf2image  # noqa: F401

        pdf2_ok = True
    except ImportError:
        pass
    checks.append(
        _check(
            "Taranmış PDF OCR",
            pdf_ocr and pdf2_ok,
            detail=(
                "pdf2image + RUZGAR_TERCUME_PDF_OCR=1 aktif"
                if pdf_ocr and pdf2_ok
                else "Kapalı veya pdf2image yok (pip install pdf2image poppler)"
            ),
            required=False,
        )
    )

    if need_internet:
        net_ok, net_detail = _internet_ok()
        checks.append(_check("Internet aramasi", net_ok, detail=net_detail, required=True))

    target = _resolve_rel(rel)
    if rel.strip():
        checks.append(
            _check(
                "Seçili dosya",
                target is not None,
                detail=str(target) if target else f"Bulunamadı: {rel}",
                required=False,
            )
        )
        if target is not None:
            ext = target.suffix.lower()
            if ext in {".mobi", ".azw", ".azw3", ".kfx"}:
                try:
                    from ilim_assistant.motorlar.tercume_ebook_read import calibre_available

                    cal_ok = calibre_available()
                    checks.append(
                        _check(
                            "Calibre (MOBI/AZW)",
                            cal_ok,
                            detail=(
                                "ebook-convert hazır"
                                if cal_ok
                                else "Calibre kurun — MOBI/Kindle için gerekli"
                            ),
                            required=False,
                        )
                    )
                except Exception:
                    pass
            elif ext in {".djvu", ".djv"}:
                try:
                    from ilim_assistant.motorlar.tercume_ebook_read import djvu_available

                    checks.append(
                        _check(
                            "DjVu (djvutxt)",
                            djvu_available(),
                            detail="djvutxt hazır" if djvu_available() else "DjVuLibre kurun",
                            required=False,
                        )
                    )
                except Exception:
                    pass

    required_fail = [c for c in checks if c.get("required") and not c.get("ok")]
    ready = len(required_fail) == 0
    hints: list[str] = []
    if not brain_ok:
        try:
            from ilim_assistant.config import ollama_only_mode

            if ollama_only_mode():
                hints.append("RUZGAR_OLLAMA_ONLY=1: yalnız Ollama — `ollama serve` ve model pull.")
            else:
                hints.append("Çeviri için Gemini/Groq anahtarı veya yerel Ollama açın.")
        except Exception:
            hints.append("Çeviri için Gemini/Groq anahtarı veya yerel Ollama açın.")
    if need_internet and not any(c.get("id") == "internet_aramasi" and c.get("ok") for c in checks):
        hints.append("Arama/indirme için internet gerekli.")
    ocr_row = next((c for c in checks if c.get("id") == "ocr_(tesseract)"), None)
    if ocr_row and not ocr_row.get("ok"):
        hints.append("Taranmış sayfa için Tesseract kurun (Arapça/Türkçe paketleri).")

    return {
        "ok": ready,
        "ready": ready,
        "version": PREFLIGHT_VERSION,
        "checks": checks,
        "hints": hints,
        "rel": (rel or "").strip(),
    }
