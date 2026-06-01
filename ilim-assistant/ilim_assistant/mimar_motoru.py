"""
Mimar motoru — görsel atölye (Fotoğraf · Sanat · Tasarım).
Metin/ilim arşivi okuma_motoru + Tercüme Okuma sekmesindedir; bu modül yalnızca mimar-* arşivini hedefler.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ilim_assistant.ruzgar_perf import RUZGAR_PERF_MIMAR

_ROOT = Path(__file__).resolve().parents[1]
_ARSIV = _ROOT / "arsiv"


def _count_catalog_items(catalog_path: Path) -> int:
    if not catalog_path.is_file():
        return 0
    try:
        import json

        data = json.loads(catalog_path.read_text(encoding="utf-8"))
        items = data.get("items")
        return len(items) if isinstance(items, list) else 0
    except Exception:
        return 0


def _tasarim_project_count() -> int:
    d = _ARSIV / "mimar-tasarim"
    if not d.is_dir():
        return 0
    return sum(1 for p in d.glob("*.json") if not p.name.startswith("_"))


def _atolye_snapshot() -> dict[str, Any]:
    snap: dict[str, Any] = {"foto": 0, "sanat": 0, "tasarim": 0}
    try:
        from ilim_assistant.motorlar import mimar_fotograf, mimar_sanat, mimar_tasarim

        snap["foto"] = len((mimar_fotograf.list_photos() or {}).get("items") or [])
        snap["sanat"] = len((mimar_sanat.list_works() or {}).get("items") or [])
        snap["tasarim"] = len((mimar_tasarim.list_projects() or {}).get("items") or [])
    except Exception:
        snap["foto"] = _count_catalog_items(_ARSIV / "mimar-fotograf" / "_catalog.json")
        snap["sanat"] = _count_catalog_items(_ARSIV / "mimar-sanat" / "_catalog.json")
        snap["tasarim"] = _tasarim_project_count()
    return snap


def build_motor_context(message: str) -> str:
    """Mimar sohbet bağlamı — görsel atölye; Kur'an/Mektubat RAG burada yok."""
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    snap = _atolye_snapshot()
    atolye_hint = ""
    try:
        from ilim_assistant.motorlar.mimar_faz5 import parse_atolye_action

        act = parse_atolye_action(prompt)
        if act:
            atolye_hint = (
                f"Algılanan atölye niyeti: sekme={act.get('tab')}, "
                f"işlem={act.get('action')}, not={act.get('label_tr')}\n"
            )
    except Exception:
        pass

    return dinamit_heartbeat() + (
        f"[MİMAR MOTORU — Görsel atölye · {RUZGAR_PERF_MIMAR}]\n"
        "Bu motor yalnızca **Fotoğraf**, **Resim · Sanat** ve **Tasarım** tuvalidir.\n"
        "Arşiv kökleri (disk): `ilim-assistant/arsiv/mimar-fotograf`, "
        "`mimar-sanat`, `mimar-tasarim` — başka klasöre yazma.\n"
        f"Özet: fotoğraf={snap['foto']}, sanat eseri={snap['sanat']}, tasarım projesi={snap['tasarim']}.\n"
        "İlim metni, Kur'an, Mektubat, PDF derin okuma → **Tercüme motoru · Okuma sekmesi** "
        "(okuma_motoru); burada tekrarlama.\n"
        "Kullanıcı doğal dilde emir verebilir: «eseri tanı», «ev planı çiz», "
        "«fotoğraf restorasyon», «kopya çıkar poster» — UI atölye API ile yürür.\n"
        "Yanıt: kısa Türkçe, teknik jargonu sadeleştir; görsel iş için ilgili sekmeyi hatırlat.\n"
        f"{atolye_hint}"
        f"Kullanıcı mesajı: {prompt}"
    )
