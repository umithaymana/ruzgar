# Created by Ümit & Gökçenur
"""Madde 5 — bağlam/zehir kod kapısı (silme yok)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(cond: bool, name: str) -> int:
    print(("OK" if cond else "FAIL") + " - " + name)
    return 0 if cond else 1


def main() -> int:
    from ilim_assistant.kullanici_baglami import (
        _detect_user_intro,
        is_plausible_person_name,
        list_suspect_profiles,
        heal_active_user_if_poisoned,
        ingest_message,
        build_context_block,
    )
    from ilim_assistant.ruzgar_metin_sadakati import is_auto_learn_poison
    from ilim_assistant.hafiza_i_ruzgar import list_suspect_hafiza_entries

    failed = 0
    failed += _ok(is_plausible_person_name("Ümit abi"), "plausible umit")
    failed += _ok(is_plausible_person_name("Ayşe"), "plausible ayse")
    failed += _ok(not is_plausible_person_name("Sana Bir Şey Soracağım"), "reject sentence")
    failed += _ok(not is_plausible_person_name("Geldim Nasılsın Rüzgar"), "reject selam")
    failed += _ok(not is_plausible_person_name("Kimim"), "reject kimim")
    failed += _ok(_detect_user_intro("benim adım Mehmet") == "Mehmet", "intro adim")
    failed += _ok(_detect_user_intro("ben sana bir şey soracağım") == "", "no bare ben")
    failed += _ok(_detect_user_intro("Ben geldim nasılsın") == "", "no ben geldim")
    failed += _ok(is_auto_learn_poison("Para deliği küçük bir deliktir."), "poison para")
    failed += _ok(
        is_auto_learn_poison("Ümit abi, süre yetmedi; cevap yarım kaldı."),
        "poison timeout",
    )
    failed += _ok(not is_auto_learn_poison("Lale Devri 1718–1730 arasıdır."), "clean ok")

    with tempfile.TemporaryDirectory() as td:
        bag = Path(td) / "bag.json"
        bag.write_text(
            json.dumps(
                {
                    "active_user": "sana_bir_sey_soracagim",
                    "profiles": {
                        "sana_bir_sey_soracagim": {
                            "display_name": "Sana Bir Şey Soracağım",
                            "aliases": [],
                            "relations": [],
                            "topic_notes": [],
                        },
                        "umit_abi": {
                            "display_name": "Ümit abi",
                            "aliases": ["Ümit abi"],
                            "relations": [],
                            "topic_notes": [],
                        },
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        with mock.patch(
            "ilim_assistant.kullanici_baglami._path", return_value=bag
        ):
            suspects = list_suspect_profiles()
            failed += _ok(any(s["slug"] == "sana_bir_sey_soracagim" for s in suspects), "suspect listed")
            data = json.loads(bag.read_text(encoding="utf-8"))
            failed += _ok(heal_active_user_if_poisoned(data), "heal changes")
            failed += _ok(data.get("active_user") == "umit_abi", "heal active umit")
            # Sahte profiller silinmedi
            failed += _ok("sana_bir_sey_soracagim" in data["profiles"], "no delete yet")
            ingest_message("ben sana bir şey soracağım")
            data2 = json.loads(bag.read_text(encoding="utf-8"))
            failed += _ok(data2.get("active_user") == "umit_abi", "ingest keeps umit")
            block = build_context_block()
            failed += _ok("Ümit abi" in block, "context umit")
            failed += _ok("Soracağım" not in block, "context no poison name")

    # Canlı dosya — yalnız rapor (silme yok)
    live_suspects = list_suspect_profiles()
    hafiza_sus = list_suspect_hafiza_entries(limit=20)
    print(f"live_suspect_profiles={len(live_suspects)}")
    print(f"live_suspect_hafiza={len(hafiza_sus)}")
    if live_suspects:
        print("sample_profiles:", [s["display_name"] for s in live_suspects[:8]])
    if hafiza_sus:
        print("sample_hafiza:", [s["soru"] for s in hafiza_sus[:5]])

    print("result:", "FAIL" if failed else "pass", f"({failed} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
