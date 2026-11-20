# Created by Ümit & Gökçenur
"""Gelisim modu icin yardimci motor.

DURUM (Faz 6 — P2 temizlik): **yan / boot dışı / import edilmiyor.**
Boot listesi: ses→video→okuma→mimar→tercüme→hafıza→programlama.
Bu dosya arşiv shim; yeni özellik buraya eklenmesin.

desktop_server ön yükleme / akış hızı: ruzgar_perf (Ümit & Gökçenur) ile uyumlu.
Ana İlim ve İdrak talimatları: chat_core.prepare_turn → ilim_ve_idrak.append_global_directive.
"""


def build_motor_context(message: str) -> str:
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    return dinamit_heartbeat() + (
        "[GELISIM MOTORU]\n"
        "Bu modda cevaplarini asama asama, acik ve gelistirilebilir sekilde ver. "
        "Gerektiginde kisa aksiyon maddeleri olustur.\n"
        f"Kullanici mesaji: {prompt}"
    )
