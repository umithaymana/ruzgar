# Created by Ümit & Gökçenur
"""Video modu icin yardimci motor. İlim ve İdrak: chat_core + ilim_ve_idrak."""


def build_motor_context(message: str) -> str:
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    return dinamit_heartbeat() + (
        "[VIDEO MOTORU]\n"
        "Bu modda cevaplari sahne, cekim ve kurgu adimlariyla planla. "
        "Mumkun oldugunda cekim listesi ve akis sirasi belirt.\n"
        f"Kullanici mesaji: {prompt}"
    )
