import json

def json_ozet(veri: dict) -> str:
    """Verilen sözlüğü sıralı ve Türkçe karakter korumalı JSON stringe çevirir."""
    return json.dumps(veri, sort_keys=True, ensure_ascii=False)
