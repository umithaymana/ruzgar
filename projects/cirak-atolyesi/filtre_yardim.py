# Created by Ümit & Gökçenur — gece T5 (spec uyumu)
def normalize(s: str) -> str:
    """Metni budayıp küçük harfe çevirir."""
    return (s or "").strip().lower()
