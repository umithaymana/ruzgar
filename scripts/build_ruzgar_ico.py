"""PNG -> ICO (Windows kısayol). Pillow gerekir: py -3 -m pip install pillow"""
from __future__ import annotations

import sys
from pathlib import Path

def main() -> int:
    root = Path(__file__).resolve().parent.parent
    png = root / "ruzgar-desktop" / "assets" / "icon.png"
    ico = root / "ruzgar-desktop" / "assets" / "ruzgar.ico"
    if not png.is_file():
        print("icon.png yok:", png, file=sys.stderr)
        return 1
    try:
        from PIL import Image
    except ImportError:
        print("Pillow kur: py -3 -m pip install pillow", file=sys.stderr)
        return 1
    img = Image.open(png).convert("RGBA")
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico, format="ICO", sizes=ico_sizes)
    print("OK:", ico)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
