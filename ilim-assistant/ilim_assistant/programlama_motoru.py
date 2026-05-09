# Created by Ümit & Gökçenur
"""Programlama modu icin yardimci motor. İlim ve İdrak: chat_core + ilim_ve_idrak."""


def build_motor_context(message: str) -> str:
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    return dinamit_heartbeat() + (
        "[PROGRAMLAMA MOTORU]\n"
        "Bu modda cevaplar teknik, dogru ve adim adim uygulanabilir olsun. "
        "Gereksiz genisleme yapmadan istenen kod veya cozum uret.\n"
        f"Kullanici mesaji: {prompt}"
    )
