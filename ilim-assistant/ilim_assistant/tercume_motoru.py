# Created by Ümit & Gökçenur
"""Tercume modu icin yardimci motor. İlim ve İdrak: chat_core + ilim_ve_idrak."""


def build_motor_context(message: str) -> str:
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    return dinamit_heartbeat() + (
        "[TERCUME MOTORU]\n"
        "Bu modda cevirilerde anlam sadakatini koru, tonu dogal tut ve gerekiyorsa "
        "alternatif ceviri secenekleri ver.\n"
        f"Kullanici mesaji: {prompt}"
    )
