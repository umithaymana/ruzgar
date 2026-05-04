"""
Rüzgar / onaylı işlemler için sınırlar.

- Gerçek antivirüs: Windows Defender + güncel tanımlar; özel bir bot %100 “her virüsü” garanti edemez.
- Sistem klasörlerine yazma / dosya silme bu modülde YOK; silme için kullanıcı Windows Güvenliği’ni kullanmalı.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# Dosya işlemleri (ileride eklenecekse) bu önekler kesinlikle dokunulmaz
FORBIDDEN_PATH_PREFIXES = tuple(
    os.path.normpath(p).lower()
    for p in (
        os.environ.get("SystemRoot", r"C:\Windows") + r"\System32",
        os.environ.get("SystemRoot", r"C:\Windows") + r"\SysWOW64",
        os.environ.get("SystemRoot", r"C:\Windows") + r"\WinSxS",
        r"C:\Windows\System32",
        r"C:\Windows\SysWOW64",
    )
)


def path_is_forbidden(target: str | Path) -> bool:
    try:
        norm = os.path.normpath(str(target)).lower()
    except Exception:
        return True
    return any(norm.startswith(pref) for pref in FORBIDDEN_PATH_PREFIXES)


# Özel metin komutu: yalnızca winget kurulum (Python paket kimliği) — enjeksiyon riskini azaltır
_WINGET_PYTHON_ONLY = re.compile(
    r"^\s*winget\s+install\s+Python\.Python\.3\.\d+\s+"
    r"(?:--accept-package-agreements\s+)?(?:--accept-source-agreements\s*)?$",
    re.IGNORECASE,
)


def validate_custom_winget_line(line: str) -> tuple[bool, str]:
    s = line.strip()
    if not s:
        return False, "Boş komut."
    if _WINGET_PYTHON_ONLY.match(s):
        return True, ""
    return False, "Yalnızca şu biçim izinli: winget install Python.Python.3.xx [--accept-package-agreements] [--accept-source-agreements]"


DISCLAIMER_TR = (
    "Bu araçlar bilgisayarı otomatik ‘tam yetkiyle’ yönetmez. "
    "Tüm çalıştırmalar önizleme + senin onayın ile yapılır. "
    "Virüs için asıl koruma Windows Güvenliği ve güncel tanımlardır; "
    "şüpheli dosyayı silme kararı sende olmalıdır."
)
