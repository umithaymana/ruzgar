def kelime_say(metin: str) -> int:
    if not metin or not isinstance(metin, str):
        return 0
    return len(metin.strip().split())
