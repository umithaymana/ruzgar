def filtre_satirlar(satirlar, anahtar: str):
    """Satırlar içinde anahtar kelimeyi içerenleri yield eder."""
    for satir in satirlar:
        if anahtar in satir:
            yield satir
