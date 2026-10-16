# Created by Ümit & Gökçenur
"""Tarif defteri — modelsiz üretim.

Bilinen iş yerel şablondan dosyaya iner. Tarif yoksa dosya yazılmaz.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

TARIF_VERSION = "programlama-tarif-v1-2026-10-16"

_RECIPES: tuple[dict[str, Any], ...] = (
    {
        "id": "statik_site",
        "template": "static_site",
        "default_name": "ornek-site",
        "label": "basit site",
        "note": "Faz 20 statik site — Faz 6 static_site şablonu",
        "phrases": (
            "basit site yap",
            "statik site yap",
            "web sitesi yap",
            "bir site yap",
            "site yap",
        ),
    },
    {
        "id": "python_arac",
        "template": "cli_python",
        "default_name": "ornek-arac",
        "label": "küçük Python aracı",
        "note": "Faz 20 küçük uygulama — Faz 6 cli_python şablonu",
        "phrases": (
            "kucuk python araci yap",
            "python araci yap",
            "python cli yap",
            "komut satiri araci yap",
            "kucuk uygulama yap",
        ),
    },
)

_QUESTION = (
    "nedir",
    "nasil",
    "anlat",
    "acikla",
    "ne demek",
    "hangi bilgi",
    "kutuphane",
)

_MAKE = (" yap", " olustur", " hazirla")
_NOUNS = ("site", "uygulama", "arac", "program", "sayfa")


def _fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", text or "")
    raw = "".join(c for c in raw if not unicodedata.combining(c))
    raw = raw.replace("ı", "i").replace("İ", "I").lower()
    return re.sub(r"\s+", " ", raw).strip()


def _sorted_phrases() -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for recipe in _RECIPES:
        for phrase in recipe["phrases"]:
            rows.append((phrase, recipe))
    rows.sort(key=lambda item: len(item[0]), reverse=True)
    return rows


def match_tarif(message: str) -> tuple[dict[str, Any], str] | None:
    low = _fold(message)
    if not low or any(q in low for q in _QUESTION):
        return None
    for phrase, recipe in _sorted_phrases():
        if phrase in low:
            return recipe, phrase
    return None


def wants_tarif_miss(message: str) -> bool:
    """Üretim cümlesi ama rafta tarifi yok."""
    low = _fold(message)
    if not low or any(q in low for q in _QUESTION):
        return False
    if match_tarif(message):
        return False
    has_make = any(token in f" {low}" for token in _MAKE) or low.endswith(" yap")
    has_noun = any(noun in low for noun in _NOUNS)
    return has_make and has_noun


def wants_tarif(message: str) -> bool:
    return match_tarif(message) is not None or wants_tarif_miss(message)


def _project_name(message: str, default_name: str) -> str:
    raw = (message or "").strip()
    marked = re.search(r"(?:ad[ıi]|isim)\s*[:=]\s*([^\n]{1,48})", raw, re.I)
    if marked:
        return marked.group(1).strip().strip("\"'")
    if ":" in raw:
        tail = raw.split(":", 1)[1].strip().strip("\"'")
        if tail:
            return tail[:48]
    return default_name


def _verify_written(root: Path | None, written: list[str]) -> str:
    if root is None or not written:
        return "Doğrulama: yazılan dosya yok."
    notes: list[str] = []
    for rel in written:
        path = root / rel
        if not path.is_file():
            notes.append(f"{rel} yok")
            continue
        if path.suffix == ".py":
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
                notes.append(f"{rel} sözdizimi tamam")
            except SyntaxError as exc:
                notes.append(f"{rel} sözdizimi hatalı ({exc.msg})")
        elif path.name == "index.html":
            body = path.read_text(encoding="utf-8")
            notes.append("index.html var" if "<title" in body.lower() else "index.html başlıksız")
    return "Doğrulama: " + "; ".join(notes[:6])


def format_tarif_miss() -> str:
    lines = [
        "Ümit abi, bu işin tarifi rafta yok. Dosya yazmadım.",
        "",
        "Tarifler:",
        "1. basit site yap — statik site",
        "2. küçük Python aracı yap — komut satırı aracı",
        "",
        "Ad vermek için: basit site yap: vitrin",
        "Açık uç sırası tarifin yerine geçmez: önce yerel Ollama (kod, denge, hizli), gerekirse web.",
        f"({TARIF_VERSION})",
    ]
    return "\n".join(lines)


def run_tarif(
    message: str,
    workspace_root: str | Path | None = None,
) -> str:
    hit = match_tarif(message)
    if hit is None:
        return format_tarif_miss()
    recipe, _phrase = hit
    from ilim_assistant.motorlar.programlama_faz6 import run_scaffold
    from ilim_assistant.motorlar.programlama_motoru import repo_root

    name = _project_name(message, str(recipe["default_name"]))
    result = run_scaffold(str(recipe["template"]), name, workspace_root)
    if not result.get("ok"):
        err = result.get("error") or "yazılamadı"
        return (
            "Ümit abi, tarif durdu. Dosya uydurmadım.\n\n"
            f"{err}\n\n"
            f"Tarif: {recipe['label']}. ({TARIF_VERSION})"
        )
    written = [str(p) for p in (result.get("written") or [])]
    root = repo_root(workspace_root)
    lines = [
        f"Ümit abi, **{recipe['label']}** tarifi yerelden yazıldı. Model yok.",
        "",
        f"Not: {recipe['note']}",
        f"Proje: `{result.get('base_dir')}`",
        "",
        "Dosyalar:",
    ]
    for rel in written:
        lines.append(f"  · {rel}")
    lines.extend(["", _verify_written(root, written), f"({TARIF_VERSION})"])
    return "\n".join(lines)
