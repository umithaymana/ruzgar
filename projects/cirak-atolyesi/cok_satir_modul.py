# Created by Ümit & Gökçenur — Dilim C
"""Çok satırlı çırak modülü (PASS kalıbı dışı).

Bu dosya docstring + fonksiyon içerir; tek satır print PASS değildir.
"""

MODUL_BASLIK = 'Dilim C cok satir'


def ozet_satir() -> str:
    """Kısa özet döndür."""
    return f'{MODUL_BASLIK}: docstring+fonksiyon'


def main() -> int:
    print(ozet_satir())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
