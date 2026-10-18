"""Sıra tahtası okunur, dosyası değişmez."""

from ilim_assistant.motorlar.programlama_motoru import is_code_agent_task_message
from ilim_assistant.ruzgar_sira_tahtasi import sira_tahtasi_yaniti


def test_sira_tahtasi_biteni_soyler_yazmaz(tmp_path):
    tahta = tmp_path / "RUZGAR_SIRA.md"
    tahta.write_text(
        "\n".join(
            [
                "| Sıra | İş | Durum | Son test |",
                "| --- | --- | --- | --- |",
                "| 39 | Dört masa sohbette | bitti | `test_masa` |",
                "| 40 | Orta işi söyle | bitti | `test_orta` |",
                "",
                "**Denenecek cümle:** `orta işi söyle`",
                "",
                "**Bilerek kapalı:** dosya silmek, üretilen kodu çalıştırmak.",
            ]
        ),
        encoding="utf-8",
    )
    once = tahta.read_bytes()
    yanit = sira_tahtasi_yaniti("sırada ne var", tahta)
    assert yanit
    assert "40" in yanit
    assert "Orta işi söyle" in yanit
    assert "Açık satır yok" in yanit
    assert "orta işi söyle" in yanit
    assert "dosya silmek" in yanit
    assert tahta.read_bytes() == once
    assert sira_tahtasi_yaniti("ne bitti", tahta)
    assert sira_tahtasi_yaniti("hava nasıl", tahta) is None
    assert is_code_agent_task_message("sıra tahtası", "programlama") is False
