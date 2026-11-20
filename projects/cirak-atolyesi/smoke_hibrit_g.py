# Created by Ümit & Gökçenur — Dilim G smoke
from pathlib import Path
import runpy
import sys

mod = Path(__file__).resolve().parent / 'hibrit_g_modul.py'
ns = runpy.run_path(str(mod))
code = ns['main']()
sys.exit(code)
