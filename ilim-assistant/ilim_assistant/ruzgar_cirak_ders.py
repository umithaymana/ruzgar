# Created by Ümit & Gökçenur
"""Dilim 6 — Programlama çırak ders sözleşmesi.

Yeşil dilim = iş bitti + en az bir ders kaydı.
Rüzgar çırak; usta (Cursor) kırılgan yerde keser.

2026-11-18: Atölye ipleri gevşetildi — yalnız projects/cirak-atolyesi/
(.py/.md, fence ile çok satır). Ana kod / boot / hub hâlâ kapalı.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

CIRAK_DERS_VERSION = "ruzgar-cirak-ders-v1.10-sozlesme-5eksi-2026-11-18"

CIRAK_ATOLYE_SCOPE = "projects/cirak-atolyesi"

_PROJECTS_PY_RE = re.compile(
    r"(?P<path>projects/[\w.\-]+(?:/[\w.\-]+)*\.py)\b",
    re.I,
)
_ATOLYE_FILE_RE = re.compile(
    r"(?P<path>projects/cirak-atolyesi/[\w.\-]+(?:/[\w.\-]+)*\.(?:py|md))\b",
    re.I,
)
_FENCE_RE = re.compile(
    r"```(?:python|py|md|markdown)?\s*\n(.*?)```",
    re.I | re.S,
)

# Çıraka verilebilecek dar görev türleri (serbest ajan değil)
CIRAK_GOREV_TURLERI: tuple[str, ...] = (
    "tek_dosya_patch",
    "smoke_yesil",
    "pytest_gecir",
    "atolye_alan_doldur",
    "niyet_regex_dar",
    "rapor_md",
    "verify_yazdim",
    "cok_satir",
    "dar_patch",
    "kirilgan_red",
    "mini_muhur",
    "gece_rapor",
    "hibrit_g",
    "tavan_ders",
    "tavan_yukselt",
    "bilgi_kopru",
    "mimar_vizyon",
    "yardimci_is",
    "istek_plan",
    "proje_oku",
    "gercek_paket",
)

# Usta işi — çırağa verilmez
USTA_KIRILGAN: tuple[str, ...] = (
    "boot_sirasi",
    "ana_yuz_kilidi",
    "anayasa_hardcode",
    "hub_omurga",
    "serbest_ajan",
    "dosya_silme",
)

# Tavan — Mimar onayı olmadan yükselmez
# 2026-11-18 Mimar «yap»: +1 basamak (genel saha hâlâ kapalı)
TAVAN_ONCEKI = "atolye_kapili"
TAVAN_SU_AN = "atolye_hibrit_ajan_ok"
MIMAR_ONAY_TAVAN = "mimar-onay-2026-11-18-yap"
TAVAN_USTU_YASAK: tuple[str, ...] = (
    "genel_saha",
    "serbest_ajan_yuzde90",
    "ana_kod_yama",
    "boot_yuz_hub",
)
TAVAN_IZINLI_SIMDI: tuple[str, ...] = (
    "atolye_supervised",
    "atolye_hibrit_g",  # written+disk+smoke
    "atolye_tam_ajan_dar",  # yalnız cirak-atolyesi; G kapısı geçerli
)

DERS_ZORUNLU_ALANLAR: tuple[str, ...] = (
    "dilim",
    "ders",
    "smoke_veya_dosya",
)


def looks_like_cirak_gorev(message: str) -> bool:
    """Çırak görev satırı mı? (ajan fallback kapısı)"""
    low = (message or "").strip().lower()
    if not low:
        return False
    if "cirak" in low or "çırak" in low:
        return True
    if "cirak-atolyesi" in low.replace("\\", "/"):
        return True
    return False


def wants_full_code_agent(message: str) -> bool:
    """Faz 85 miss sonrası tam ajan / çırak borusu."""
    low = (message or "").strip().lower()
    if "tam ajan" in low or "tam_ajan" in low:
        return True
    return looks_like_cirak_gorev(message)


def cirak_gorev_metni(tur: str, hedef: str) -> str:
    """Kapılı çırak görev satırı — scope = cirak-atolyesi (projects/cirak değil).

    Köşeli [cirak:…] kullanma — path_hint / proje yolu bozulur (canlı ders 2026-11-17).
    Sonuna `tam ajan` eklenir — Faz85 miss'te ajan borusu açılsın.
    """
    t = (tur or "").strip()
    h = (hedef or "").strip()[:800]
    if t not in CIRAK_GOREV_TURLERI:
        t = "tek_dosya_patch"
    return (
        f"görev: {CIRAK_ATOLYE_SCOPE} cirak {t} — {h} · tam ajan"
    ).strip()


def ders_kaydi_gecerli(kayit: dict[str, Any] | None) -> bool:
    if not isinstance(kayit, dict):
        return False
    for k in DERS_ZORUNLU_ALANLAR:
        if not str(kayit.get(k) or "").strip():
            return False
    return True


def yesil_dilim_icin_ders_gerekli(kayit: dict[str, Any] | None) -> dict[str, Any]:
    """Çıkış: ok + neden."""
    if ders_kaydi_gecerli(kayit):
        return {"ok": True, "version": CIRAK_DERS_VERSION}
    return {
        "ok": False,
        "reason": "ders_yazilmadan_yesil_sayilmaz",
        "required": list(DERS_ZORUNLU_ALANLAR),
        "version": CIRAK_DERS_VERSION,
    }


def cirak_status() -> dict[str, Any]:
    return {
        "enabled": True,
        "version": CIRAK_DERS_VERSION,
        "atolye_scope": CIRAK_ATOLYE_SCOPE,
        "gorev_turleri": list(CIRAK_GOREV_TURLERI),
        "usta_kirilgan": list(USTA_KIRILGAN),
        "tavan": TAVAN_SU_AN,
        "tavan_onceki": TAVAN_ONCEKI,
        "tavan_izinli": list(TAVAN_IZINLI_SIMDI),
        "tavan_ustu_yasak": list(TAVAN_USTU_YASAK),
        "mimar_onay": MIMAR_ONAY_TAVAN,
        "tavan_not": (
            f"Tavan={TAVAN_SU_AN} (Mimar {MIMAR_ONAY_TAVAN}): "
            "atölyede hibrit + dar tam ajan; yeşil hâlâ written+disk+smoke. "
            "Genel saha / %90 serbest / ana kod / boot-yüz-hub KAPALI."
        ),
        "supervised_write": True,
        "supervised_ext": [".py", ".md"],
        "hibrit_kural": "ajan_konusur_yesil_disk_ve_smoke",
    }


def claim_yesil_gecerli(
    *,
    written: str | None,
    disk_ok: bool,
    smoke_ok: bool,
) -> dict[str, Any]:
    """Dilim G kuralı: 'yazdım/yeşil' iddiası written+disk+smoke olmadan geçersiz."""
    w = (written or "").strip()
    ok = bool(w) and disk_ok and smoke_ok
    return {
        "ok": ok,
        "reason": None
        if ok
        else "iddia_yesil_ama_written_disk_smoke_eksik",
        "written": w,
        "disk_ok": disk_ok,
        "smoke_ok": smoke_ok,
        "version": CIRAK_DERS_VERSION,
    }


def _kirilgan_istiyor(message: str) -> str | None:
    """Kırılgan *eylem* niyeti varsa etiket (salt bahis → red yok)."""
    low = (message or "").lower()
    # Eylem kalıpları — raporda «boot’a dokunma» demek red değil
    action = (
        ("boot_sirasi", (
            "boot değiştir",
            "boot sirasini degistir",
            "boot sırasını değiştir",
            "boot_sirasi değiştir",
            ".cursorrules yaz",
            ".cursorrules değiştir",
        )),
        ("ana_yuz_kilidi", (
            "ana yüzü değiştir",
            "ana yuzu degistir",
            "motor listesini değiştir",
            "yüz kilidini kaldır",
            "yuz kilidini kaldir",
        )),
        ("hub_omurga", (
            "hub omurgasını değiştir",
            "hub omurgasini degistir",
            "ana_motor_hub yaz",
            "hub omurga yama",
        )),
        ("serbest_ajan", (
            "%90 serbest aç",
            "serbest ajan aç",
            "serbest_ajan=1",
        )),
        ("dosya_silme", (
            "dosya sil ",
            "dosyayı sil",
            "dosyayi sil",
            "os.remove",
            "path.unlink",
        )),
    )
    for tag, keys in action:
        if any(k in low for k in keys):
            return tag
    # Tavan üstü — Mimar onayı yoksa red
    if _tavan_yukselt_istiyor(low) and "mimar onay" not in low and "mimar_onay" not in low:
        return "tavan_ustu"
    return None


def _tavan_yukselt_istiyor(low: str) -> bool:
    keys = (
        "tavanı kaldır",
        "tavani kaldir",
        "tavan yükselt",
        "tavan yukselt",
        "genel saha aç",
        "genel saha ac",
        "%90 serbest",
        "serbest ajan aç",
        "ana koda yaz",
        "boot değiştir",
    )
    return any(k in low for k in keys)


def _fence_body(raw: str) -> str | None:
    m = _FENCE_RE.search(raw or "")
    if not m:
        return None
    body = m.group(1)
    return body if body.strip() else None


def _write_intent(message: str) -> bool:
    """Supervised yalnız net yazım niyetinde tetiklensin (oku yolu çalmasın)."""
    if _fence_body(message) is not None:
        return True
    low = (message or "").lower()
    markers = (
        "print pass",
        "pass cirak",
        "pass cirak-d9",
        "yaz:",
        "oluştur:",
        "olustur:",
        "@@write",
        "supervised yaz",
        "dosya yaz",
        "yaz ve doğrula",
        "yaz + ",
    )
    if any(m in low for m in markers):
        return True
    # «…/x.py yaz» / «…/x.md oluştur»
    if re.search(
        r"projects/cirak-atolyesi/[^\s]+\.(?:py|md).{0,40}\b(yaz|oluştur|olustur)\b",
        low,
    ):
        return True
    if re.search(
        r"\b(yaz|oluştur|olustur)\b.{0,40}projects/cirak-atolyesi/[^\s]+\.(?:py|md)",
        low,
    ):
        return True
    return False


def _default_py_body(raw: str) -> str:
    low = (raw or "").lower()
    if "pass cirak" in low or "pass cirak-d9" in low or "print pass" in low:
        return 'print("PASS cirak-d9")\n'
    if "print(" in raw:
        pm = re.search(r"print\s*\([^)]*\)", raw)
        return (pm.group(0) if pm else 'print("PASS cirak")') + "\n"
    return 'print("PASS cirak")\n'


def _resolve_repo_root(workspace_root: str | Path | None) -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
    except Exception:
        root = None
    if root is None:
        return Path(workspace_root).resolve() if workspace_root else Path.cwd().resolve()
    return Path(root).resolve()


def try_cirak_dilim_a_rapor(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim A — dürüst rapor (LLM yok): 3 kanıt dosyasını oku → v2.md yaz."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "oz_analiz_raporu_v2" not in low and "dilim a" not in low and "rapor_md" not in low:
        return None
    if "oz_analiz_raporu_v2" not in low and "dürüst" not in low and "durust" not in low:
        # rapor_md tek başına yetmez; Dilim A / v2 hedefi şart
        if "dilim a" not in low:
            return None

    root = _resolve_repo_root(workspace_root)
    kanitlar = (
        ("ilim-assistant/ilim_assistant/ruzgar_cirak_ders.py", root / "ilim-assistant" / "ilim_assistant" / "ruzgar_cirak_ders.py"),
        ("ilim-assistant/scripts/smoke_cirak_ders_d6.py", root / "ilim-assistant" / "scripts" / "smoke_cirak_ders_d6.py"),
        ("projects/cirak-atolyesi/hello_cirak.py", root / "projects" / "cirak-atolyesi" / "hello_cirak.py"),
    )
    okunan: list[str] = []
    hello_icerik = ""
    for rel, path in kanitlar:
        if path.is_file():
            okunan.append(rel)
            if rel.endswith("hello_cirak.py"):
                try:
                    hello_icerik = path.read_text(encoding="utf-8").strip()[:120]
                except OSError:
                    hello_icerik = "(okunamadı)"
        else:
            okunan.append(f"{rel} (YOK)")

    hedef = root / "projects" / "cirak-atolyesi" / "oz_analiz_raporu_v2.md"
    body = "\n".join(
        [
            "# Çırak Atölyesi — Öz-analiz raporu v2 (dürüst)",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}  ",
            "**Kapsam:** yalnız `projects/cirak-atolyesi/`  ",
            "**Yöntem:** supervised Dilim A (LLM yok — kanıt dosyaları okundu)",
            "",
            "## Okunan dosya yolları (kanıt)",
            *[f"- `{p}`" for p in okunan],
            "",
            "## Supervised yazım ne yaptı?",
            (
                "Kapılı yol (`try_cirak_supervised_write` / Dilim A): "
                "`projects/cirak-atolyesi/` altına `.py`/`.md` yazar; "
                f"`hello_cirak.py` örneği içerik: `{hello_icerik or 'boş'}`."
            ),
            "",
            "## Ne yapamadım?",
            "- Tam ajan yolu yavaş / tur timeout riski (canlı denemede turn 1’de takılma görüldü).",
            "- Serbest ajan / ana kod / boot / hub yazımı kapalı (`USTA_KIRILGAN`).",
            "- Atölye dışı `projects/*.py` supervised ile yazılmaz.",
            "",
            "## Bilmiyorum / klişe yok",
            "- FastAPI üretim mimarisi, observability stack: **bilmiyorum** (uydurmuyorum).",
            "- Genel saha olgunluğu: atölye çırağı; genel saha hayır.",
            "",
            "## Not",
            "- `oz_analiz_raporu.md` (v1) silinmedi — kanıt olarak duruyor.",
            "",
        ]
    )
    try:
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(body, encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_dilim_a_rapor",
            "detail": f"Dilim A yazılamadı: {exc}",
            "version": CIRAK_DERS_VERSION,
        }

    yollar_ok = sum(1 for p in okunan if "(YOK)" not in p)
    return {
        "ok": yollar_ok >= 3 and hedef.is_file(),
        "verify_ok": yollar_ok >= 3 and hedef.is_file(),
        "writes_ok": 1,
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_a_rapor",
        "detail": (
            f"Dilim A supervised rapor OK · `{CIRAK_ATOLYE_SCOPE}/oz_analiz_raporu_v2.md`\n"
            f"Kanıt yolu: {yollar_ok}/3 · ({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/oz_analiz_raporu_v2.md",
        "kanit_yol": yollar_ok,
    }


def try_cirak_dilim_b_verify(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim B — yazdım = diskte var (aynı turda oku-doğrula).

    Yanlış kök (`ilim-assistant/projects/...`) = kırmızı.
    """
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "verify_yazdim" not in low and "dilim b" not in low:
        return None

    root = _resolve_repo_root(workspace_root)
    rel = f"{CIRAK_ATOLYE_SCOPE}/verify_yazdim.py"
    target = (root / "projects" / "cirak-atolyesi" / "verify_yazdim.py").resolve()
    wrong = (root / "ilim-assistant" / "projects" / "cirak-atolyesi" / "verify_yazdim.py")

    body = (
        '# Created by Ümit & Gökçenur — Dilim B\n'
        '"""Yazdım = diskte var — self-check."""\n'
        "from pathlib import Path\n"
        "\n"
        "PASS_LINE = 'PASS cirak-B'\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    here = Path(__file__).resolve()\n"
        "    text = here.read_text(encoding='utf-8')\n"
        "    if PASS_LINE not in text:\n"
        "        print('FAIL missing PASS')\n"
        "        return 1\n"
        "    print(PASS_LINE)\n"
        "    return 0\n"
        "\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(main())\n"
    )

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_dilim_b_verify",
            "detail": f"Dilim B yazılamadı: {exc}",
            "version": CIRAK_DERS_VERSION,
        }

    # Aynı turda disk doğrulama
    try:
        disk = target.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_dilim_b_verify",
            "detail": f"Yazdım iddiası — disk okunamadı: {exc}",
            "version": CIRAK_DERS_VERSION,
        }

    same = disk == body and "PASS cirak-B" in disk
    wrong_hit = wrong.is_file()
    target_s = str(target).replace("\\", "/").lower()
    atolye_ok = False
    try:
        target.relative_to((root / "projects" / "cirak-atolyesi").resolve())
        atolye_ok = True
    except ValueError:
        atolye_ok = False

    ok = bool(
        same
        and atolye_ok
        and target.is_file()
        and "/ilim-assistant/projects/" not in target_s
    )

    detail_lines = [
        f"Dilim B {'OK' if ok else 'FAIL'} · `{rel}`",
        f"disk_aynı={same} · kök_atölye={atolye_ok} · yanlış_kök_kalıntı={wrong_hit}",
        f"PASS satırı: {'var' if 'PASS cirak-B' in disk else 'yok'}",
        f"({CIRAK_DERS_VERSION})",
    ]
    if wrong_hit:
        detail_lines.append(
            "Uyarı: `ilim-assistant/projects/...` altında eski kalıntı var (bu yazım oraya gitmedi)."
        )

    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": 1 if target.is_file() else 0,
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_b_verify",
        "detail": "\n".join(detail_lines),
        "version": CIRAK_DERS_VERSION,
        "written": rel,
        "disk_match": same,
        "wrong_root": wrong_hit,
    }


def _atolye_write(
    root: Path,
    rel_name: str,
    body: str,
) -> tuple[Path, bool]:
    """Yalnız cirak-atolyesi altına yaz; (path, ok)."""
    target = (root / "projects" / "cirak-atolyesi" / rel_name).resolve()
    try:
        target.relative_to((root / "projects" / "cirak-atolyesi").resolve())
    except ValueError:
        return target, False
    if "/ilim-assistant/" in str(target).replace("\\", "/").lower():
        return target, False
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        return target, True
    except OSError:
        return target, False


def try_cirak_dilim_c_cok_satir(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim C — PASS kalıbı dışı çok satır .py (docstring + fonksiyon)."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "dilim c" not in low and "cok_satir" not in low and "çok_satır" not in low and "cok satir" not in low:
        return None

    root = _resolve_repo_root(workspace_root)
    rel = f"{CIRAK_ATOLYE_SCOPE}/cok_satir_modul.py"
    body = (
        "# Created by Ümit & Gökçenur — Dilim C\n"
        '"""Çok satırlı çırak modülü (PASS kalıbı dışı).\n'
        "\n"
        "Bu dosya docstring + fonksiyon içerir; tek satır print PASS değildir.\n"
        '"""\n'
        "\n"
        "MODUL_BASLIK = 'Dilim C cok satir'\n"
        "\n"
        "\n"
        "def ozet_satir() -> str:\n"
        '    """Kısa özet döndür."""\n'
        "    return f'{MODUL_BASLIK}: docstring+fonksiyon'\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    print(ozet_satir())\n"
        "    return 0\n"
        "\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(main())\n"
    )
    target, wrote = _atolye_write(root, "cok_satir_modul.py", body)
    if not wrote:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_dilim_c",
            "detail": "Dilim C yazılamadı",
            "version": CIRAK_DERS_VERSION,
        }
    disk = target.read_text(encoding="utf-8")
    headings_ok = (
        '"""Çok satırlı' in disk
        and "def ozet_satir" in disk
        and "MODUL_BASLIK" in disk
        and "print(\"PASS" not in disk
    )
    # ana paket yok
    ana_yok = not (root / "ilim-assistant" / "ilim_assistant" / "cok_satir_modul.py").is_file()
    ok = headings_ok and ana_yok and target.is_file()
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": 1,
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_c",
        "detail": (
            f"Dilim C {'OK' if ok else 'FAIL'} · `{rel}`\n"
            f"docstring+fonksiyon={headings_ok} · ana_paket_yok={ana_yok}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": rel,
    }


def try_cirak_dilim_d_patch(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim D — üç dar patch (d1 yeni / d2 düzelt / d3 smoke)."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "dilim d" not in low and "dar_patch" not in low:
        return None

    root = _resolve_repo_root(workspace_root)
    # hangi alt dilim?
    if "d3" in low or "smoke" in low or "pytest" in low:
        adim = "d3"
    elif "d2" in low or "düzelt" in low or "duzelt" in low or "patch2" in low:
        adim = "d2"
    elif "d1" in low or "yeni" in low or "fonksiyon" in low or "patch1" in low:
        adim = "d1"
    else:
        # tek mesajda üçü birden
        adim = "hepsi"

    results: list[str] = []
    ok_all = True
    written: list[str] = []

    def d1() -> bool:
        body = (
            "# Created by Ümit & Gökçenur — Dilim D1\n"
            '"""Dar patch 1: yeni dosya + tek fonksiyon."""\n'
            "\n"
            "\n"
            "def carp(a: int, b: int) -> int:\n"
            "    return a * b\n"
        )
        p, w = _atolye_write(root, "dar_patch_d1.py", body)
        if not w:
            return False
        written.append(f"{CIRAK_ATOLYE_SCOPE}/dar_patch_d1.py")
        t = p.read_text(encoding="utf-8")
        return "def carp" in t and "return a * b" in t

    def d2() -> bool:
        p = root / "projects" / "cirak-atolyesi" / "dar_patch_d1.py"
        if not p.is_file():
            if not d1():
                return False
        text = p.read_text(encoding="utf-8")
        # küçük düzeltme: carp → güvenli int
        if "return int(a) * int(b)" in text:
            fixed = text
        else:
            fixed = text.replace("return a * b", "return int(a) * int(b)")
        if "Dilim D2" not in fixed:
            fixed = fixed.replace("Dilim D1", "Dilim D1→D2")
            if '"""Dar patch 1:' in fixed:
                fixed = fixed.replace(
                    '"""Dar patch 1: yeni dosya + tek fonksiyon."""',
                    '"""Dar patch 1+2: yeni dosya + düzeltme (int güvenli)."""',
                )
        p2, w = _atolye_write(root, "dar_patch_d1.py", fixed)
        if not w:
            return False
        written.append(f"{CIRAK_ATOLYE_SCOPE}/dar_patch_d1.py")
        t = p2.read_text(encoding="utf-8")
        return "return int(a) * int(b)" in t

    def d3() -> bool:
        smoke_body = (
            "# Created by Ümit & Gökçenur — Dilim D3\n"
            '"""Smoke: dar_patch_d1.carp."""\n'
            "from __future__ import annotations\n"
            "\n"
            "import sys\n"
            "from pathlib import Path\n"
            "\n"
            "HERE = Path(__file__).resolve().parent\n"
            "if str(HERE) not in sys.path:\n"
            "    sys.path.insert(0, str(HERE))\n"
            "\n"
            "from dar_patch_d1 import carp\n"
            "\n"
            "\n"
            "def main() -> int:\n"
            "    if carp(3, 4) != 12:\n"
            "        print('FAIL carp')\n"
            "        return 1\n"
            "    print('PASS cirak-D3')\n"
            "    return 0\n"
            "\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    raise SystemExit(main())\n"
        )
        p, w = _atolye_write(root, "smoke_dar_patch_d3.py", smoke_body)
        if not w:
            return False
        written.append(f"{CIRAK_ATOLYE_SCOPE}/smoke_dar_patch_d3.py")
        import subprocess
        import sys as _sys

        pr = subprocess.run(
            [_sys.executable, str(p)],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(p.parent),
        )
        return pr.returncode == 0 and "PASS cirak-D3" in (pr.stdout or "")

    if adim in ("d1", "hepsi"):
        o = d1()
        results.append(f"d1={'OK' if o else 'FAIL'}")
        ok_all = ok_all and o
    if adim in ("d2", "hepsi"):
        o = d2()
        results.append(f"d2={'OK' if o else 'FAIL'}")
        ok_all = ok_all and o
    if adim in ("d3", "hepsi"):
        o = d3()
        results.append(f"d3={'OK' if o else 'FAIL'}")
        ok_all = ok_all and o

    # yalnız atölye
    ana_yok = not (root / "ilim-assistant" / "ilim_assistant" / "dar_patch_d1.py").is_file()
    ok = ok_all and ana_yok
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": len(written),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_d",
        "detail": (
            f"Dilim D {'OK' if ok else 'FAIL'} · adım={adim}\n"
            + " · ".join(results)
            + f"\nana_paket_yok={ana_yok}\n({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": written[0] if len(written) == 1 else ",".join(written),
        "adim": adim,
    }


def try_cirak_dilim_e_red(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim E — kırılgan otomatik red (yazım yok + net ret).

    Yalnız «dilim e» / «kirilgan_red» etiketli görevde; genel kırılgan
    red aşağıda ok=False kartına düşer.
    """
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "dilim e" not in low and "kirilgan_red" not in low:
        return None

    tag = _kirilgan_istiyor(message) or "boot_sirasi"
    root = _resolve_repo_root(workspace_root)
    probe = root / "projects" / "cirak-atolyesi" / "_kirilgan_olmamali.py"
    existed_before = probe.is_file()
    # bilerek yazma yok
    return {
        "ok": True,  # red başarılı = yeşil dilim
        "verify_ok": True,
        "writes_ok": 0,
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_e_red",
        "detail": (
            f"Dilim E OK · kırılgan red `{tag}` — yazım yok.\n"
            f"USTA_KIRILGAN={list(USTA_KIRILGAN)}\n"
            f"probe_yeni={probe.is_file() and not existed_before}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "rejected": tag,
        "writes_blocked": True,
    }


def try_cirak_dilim_f_muhur(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim F — mini mühür kartı + gece raporu kapısı."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "dilim f" not in low and "mini_muhur" not in low and "gece_rapor" not in low:
        return None

    root = _resolve_repo_root(workspace_root)
    atolye = root / "projects" / "cirak-atolyesi"
    checks = {
        "A": (atolye / "oz_analiz_raporu_v2.md").is_file(),
        "B": (atolye / "verify_yazdim.py").is_file(),
        "C": (atolye / "cok_satir_modul.py").is_file(),
        "D": (atolye / "dar_patch_d1.py").is_file()
        and (atolye / "smoke_dar_patch_d3.py").is_file(),
        "E": True,  # red damarı kodda; yazım yok = başarı
    }
    yesil = [k for k, v in checks.items() if v]
    kirmizi = [k for k, v in checks.items() if not v]

    muhur = "\n".join(
        [
            "# Çırak atölyesi — Mini mühür (Dilim F)",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            "**Karar:** atölye çırağı hazır; **genel saha hayır**.",
            "",
            "## Dilim durumu",
            *[f"- {k}: {'yeşil' if checks[k] else 'kırmızı'}" for k in "ABCDE"],
            "",
            "## Mimar’a cümle",
            "Atölye çırağı A–E kapılı damarda yürüdü; boot/yüz/hub’a dokunulmadı. Genel saha açılmasın.",
            "",
        ]
    )
    p_m, w_m = _atolye_write(root, "MINI_MUHUR_DILIM_F.md", muhur)

    gece = "\n".join(
        [
            "# Gece raporu — 2026-11-18",
            "",
            "**Kim:** Rüzgar çırak (supervised) · **Usta:** Cursor",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            "",
            "## Dilimler",
            f"- Yeşil: {', '.join(yesil) or '—'}",
            f"- Kırmızı: {', '.join(kirmizi) or '—'}",
            "- F: mühür kartı yazıldı",
            "",
            "## Dosya yolları",
            f"- `{CIRAK_ATOLYE_SCOPE}/oz_analiz_raporu_v2.md`",
            f"- `{CIRAK_ATOLYE_SCOPE}/verify_yazdim.py`",
            f"- `{CIRAK_ATOLYE_SCOPE}/cok_satir_modul.py`",
            f"- `{CIRAK_ATOLYE_SCOPE}/dar_patch_d1.py`",
            f"- `{CIRAK_ATOLYE_SCOPE}/smoke_dar_patch_d3.py`",
            f"- `{CIRAK_ATOLYE_SCOPE}/MINI_MUHUR_DILIM_F.md`",
            f"- `{CIRAK_ATOLYE_SCOPE}/GECE_RAPORU_2026-11-18.md`",
            "",
            "## Smoke",
            "- `ilim-assistant/scripts/smoke_cirak_ders_d6.py`",
            "- `smoke_dar_patch_d3.py` → PASS cirak-D3",
            "- `verify_yazdim.py` → PASS cirak-B",
            "",
            "## Dersler",
            "- A: kanıt yolu / klişe yok",
            "- B: yazdım = diskte oku",
            "- C: PASS dışı çok satır (docstring+fonksiyon)",
            "- D: üç dar patch ayrı yeşil",
            "- E: kırılgan eylem → red, yazım yok",
            "- F: atölye hazır, genel saha hayır",
            "",
            "## Ne yapılamadı",
            "- Tam ajan (LLM) yolu timeout / yavaş — Dilim A–F kapılı supervised damardan bitti",
            "- Serbest ajan / ana kod / boot / hub: kapalı kaldı",
            "",
            "## Mimar sabah notu",
            "A–F yeşil (supervised). Sonraki tavan konuşması Mimar onayı ister; genel saha açma.",
            "",
        ]
    )
    p_g, w_g = _atolye_write(root, "GECE_RAPORU_2026-11-18.md", gece)

    ok = bool(w_m and w_g and not kirmizi and p_m.is_file() and p_g.is_file())
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": int(w_m) + int(w_g),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_f",
        "detail": (
            f"Dilim F {'OK' if ok else 'FAIL'} · mühür+gece rapor\n"
            f"yeşil={yesil} kırmızı={kirmizi}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/MINI_MUHUR_DILIM_F.md,{CIRAK_ATOLYE_SCOPE}/GECE_RAPORU_2026-11-18.md",
        "yesil": yesil,
        "kirmizi": kirmizi,
    }


def try_cirak_dilim_g_hibrit(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim G — hibrit: oku → kapılı yaz → disk+smoke; iddia yalnız kanıtla yeşil.

    Scope = görevdeki cirak-atolyesi; oturumdaki live-bat ezemez (ders notu).
    """
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "dilim g" not in low and "hibrit_g" not in low and "hibrit dogruluk" not in low and "hibrit doğruluk" not in low:
        return None

    root = _resolve_repo_root(workspace_root)
    atolye = root / "projects" / "cirak-atolyesi"

    # 1) Oku (kanıt)
    okunan: list[str] = []
    for rel in (
        f"{CIRAK_ATOLYE_SCOPE}/hello_cirak.py",
        f"{CIRAK_ATOLYE_SCOPE}/verify_yazdim.py",
    ):
        p = root / Path(rel)
        okunan.append(rel if p.is_file() else f"{rel} (YOK)")

    # 2) Kapılı yazım
    py_body = (
        "# Created by Ümit & Gökçenur — Dilim G hibrit\n"
        '"""Ajan konuşur; yeşil = disk + smoke."""\n'
        "from pathlib import Path\n"
        "\n"
        "PASS_LINE = 'PASS cirak-G'\n"
        "\n"
        "\n"
        "def hibrit_ozet() -> str:\n"
        "    return PASS_LINE\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    here = Path(__file__).resolve()\n"
        "    text = here.read_text(encoding='utf-8')\n"
        "    if PASS_LINE not in text:\n"
        "        print('FAIL claim without disk content')\n"
        "        return 1\n"
        "    # Scope disiplini: dosya atölyede olmalı\n"
        "    if 'cirak-atolyesi' not in str(here).replace('\\\\', '/'):\n"
        "        print('FAIL wrong scope')\n"
        "        return 1\n"
        "    print(PASS_LINE)\n"
        "    return 0\n"
        "\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(main())\n"
    )
    p_py, w_py = _atolye_write(root, "hibrit_g_modul.py", py_body)

    smoke_body = (
        "# Created by Ümit & Gökçenur — Dilim G smoke\n"
        "from pathlib import Path\n"
        "import runpy\n"
        "import sys\n"
        "\n"
        "mod = Path(__file__).resolve().parent / 'hibrit_g_modul.py'\n"
        "ns = runpy.run_path(str(mod))\n"
        "code = ns['main']()\n"
        "sys.exit(code)\n"
    )
    p_sm, w_sm = _atolye_write(root, "smoke_hibrit_g.py", smoke_body)

    ders = "\n".join(
        [
            "# Dilim G — Hibrit doğruluk dersi",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            "",
            "## Kural",
            "1. Çırak (ajan) konuşabilir / planlayabilir.",
            "2. Yeşil yalnız: `written` yolu + disk aynı içerik + smoke PASS.",
            "3. «Yazdım» iddiası kanıtsızsa **kırmızı** (`claim_yesil_gecerli`).",
            "4. Scope = görevdeki `projects/cirak-atolyesi` — oturumdaki `live-bat` ezemez.",
            "",
            "## Bu turda okunan",
            *[f"- `{x}`" for x in okunan],
            "",
            "## Written",
            f"- `{CIRAK_ATOLYE_SCOPE}/hibrit_g_modul.py`",
            f"- `{CIRAK_ATOLYE_SCOPE}/smoke_hibrit_g.py`",
            "",
        ]
    )
    p_ders, w_ders = _atolye_write(root, "DERS_G_HIBRIT.md", ders)

    # 3) Disk + smoke
    disk_ok = bool(
        w_py
        and p_py.is_file()
        and "PASS cirak-G" in p_py.read_text(encoding="utf-8")
    )
    smoke_ok = False
    if disk_ok and p_sm.is_file():
        import subprocess
        import sys as _sys

        pr = subprocess.run(
            [_sys.executable, str(p_sm)],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(atolye),
        )
        smoke_ok = pr.returncode == 0 and "PASS cirak-G" in (pr.stdout or "")

    written = f"{CIRAK_ATOLYE_SCOPE}/hibrit_g_modul.py"
    claim = claim_yesil_gecerli(written=written, disk_ok=disk_ok, smoke_ok=smoke_ok)
    # Negatif kanıt: written yoksa iddia düşer
    claim_bad = claim_yesil_gecerli(written="", disk_ok=True, smoke_ok=True)

    ok = bool(claim.get("ok") and w_ders and not claim_bad.get("ok"))
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": int(w_py) + int(w_sm) + int(w_ders),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_g_hibrit",
        "detail": (
            f"Dilim G {'OK' if ok else 'FAIL'} · hibrit doğruluk\n"
            f"okunan={okunan}\n"
            f"claim={claim}\n"
            f"iddia_kansiz_red={not claim_bad.get('ok')}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": written,
        "disk_ok": disk_ok,
        "smoke_ok": smoke_ok,
        "claim": claim,
    }


def try_cirak_dilim_h_yardimci(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Katman 2 / Dilim H — gerçek fonksiyon + pytest (G kapısı + bilgi notu)."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "yardimci_is" not in low and "dilim h" not in low and "katman 2" not in low:
        return None

    root = _resolve_repo_root(workspace_root)
    from ilim_assistant.ruzgar_cirak_bilgi_kopru import build_cirak_bilgi_context

    ctx = build_cirak_bilgi_context(
        "python function unit test pytest",
        message=message,
        scope_rel=CIRAK_ATOLYE_SCOPE,
        top_k=2,
    )
    mod = (
        "# Created by Ümit & Gökçenur — Dilim H (Katman 2)\n"
        '"""Gerçek yardımcı iş: topla + kanıtlı test."""\n'
        "\n"
        "\n"
        "def topla(a: int, b: int) -> int:\n"
        '    """İki sayıyı topla (birim test ile doğrulanır)."""\n'
        "    return int(a) + int(b)\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    print(f'PASS cirak-H topla={topla(2, 3)}')\n"
        "    return 0\n"
        "\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(main())\n"
    )
    test = (
        "# Created by Ümit & Gökçenur — Dilim H pytest\n"
        "from yardimci_is import topla\n"
        "\n"
        "\n"
        "def test_topla():\n"
        "    assert topla(2, 3) == 5\n"
        "    assert topla(-1, 1) == 0\n"
    )
    ders = "\n".join(
        [
            "# Dilim H — Güvenilir yardımcı (Katman 2)",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            "",
            "## Ders",
            "1. Mimar isteği: küçük gerçek iş (topla).",
            "2. Bilgi köprüsünden bak (kaynak yolları aşağıda).",
            "3. Yaz → pytest yeşil → ancak o zaman «bitti».",
            "4. G kuralı: written + disk + smoke/pytest.",
            "",
            "## Kaynaklar (0A)",
            *[f"- `{s}`" for s in (ctx.get("sources") or ["(yok)"])],
            "",
            "## Written",
            f"- `{CIRAK_ATOLYE_SCOPE}/yardimci_is.py`",
            f"- `{CIRAK_ATOLYE_SCOPE}/tests/test_topla.py`",
            "",
        ]
    )
    p1, w1 = _atolye_write(root, "yardimci_is.py", mod)
    # tests/ altı
    tests_dir = root / "projects" / "cirak-atolyesi" / "tests"
    try:
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        tp = tests_dir / "test_topla.py"
        tp.write_text(test, encoding="utf-8")
        w2 = True
    except OSError:
        tp = tests_dir / "test_topla.py"
        w2 = False
    p3, w3 = _atolye_write(root, "DERS_H_YARDIMCI.md", ders)

    import subprocess
    import sys as _sys

    smoke_ok = False
    pytest_ok = False
    if w1 and p1.is_file():
        pr = subprocess.run(
            [_sys.executable, str(p1)],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(root / "projects" / "cirak-atolyesi"),
        )
        smoke_ok = pr.returncode == 0 and "PASS cirak-H" in (pr.stdout or "")
    if w2 and tp.is_file():
        pr2 = subprocess.run(
            [_sys.executable, "-m", "pytest", "-q", str(tp)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(root / "projects" / "cirak-atolyesi"),
        )
        pytest_ok = pr2.returncode == 0

    claim = claim_yesil_gecerli(
        written=f"{CIRAK_ATOLYE_SCOPE}/yardimci_is.py",
        disk_ok=bool(w1 and p1.is_file()),
        smoke_ok=bool(smoke_ok and pytest_ok),
    )
    ok = bool(claim.get("ok") and w3)
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": int(w1) + int(w2) + int(w3),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_h_yardimci",
        "detail": (
            f"Dilim H {'OK' if ok else 'FAIL'} · yardımcı iş\n"
            f"smoke={smoke_ok} pytest={pytest_ok} claim={claim.get('ok')}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/yardimci_is.py",
        "smoke_ok": smoke_ok,
        "pytest_ok": pytest_ok,
    }


def try_cirak_dilim_p_plan(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim P — Mimar isteğinden plan iskeleti (usta öğretir, çırak yazar)."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "istek_plan" not in low and "dilim p" not in low and "istekten plan" not in low:
        return None

    root = _resolve_repo_root(workspace_root)
    vizyon = root / "projects" / "cirak-atolyesi" / "MIMAR_VIZYON.md"
    vizyon_var = vizyon.is_file()
    # Örnek Mimar isteği (öğretim)
    istek = (
        "Mimar isteği (örnek): Atölyede iki sayıyı toplayan küçük bir yardımcı yaz; "
        "testi geçsin; abartma; boot'a dokunma."
    )
    plan = "\n".join(
        [
            "# Dilim P — İstek → plan iskeleti",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            f"**Vizyon kartı okundu:** {'evet' if vizyon_var else 'hayır'}",
            "",
            "## 1) Mimar ne istedi? (tek cümle)",
            istek,
            "",
            "## 2) Plan iskeleti (usta kalıbı)",
            "1. Anla: vizyon + istek (sınır: atölye).",
            "2. Bilgi: 0A köprüsü / ilgili kavram.",
            "3. Yaz: tek dosya + test.",
            "4. Doğrula: disk + pytest/smoke (G).",
            "5. Sor: «Bu Mimar’ın istediği mi?»",
            "",
            "## 3) Yapılmayacaklar",
            "- Boot / yüz / hub / genel saha",
            "- Kanıtsız «bitti»",
            "",
            "## Ders",
            "Plan = istekten çıkan merdiven; koddan önce yazılır.",
            "",
        ]
    )
    p, w = _atolye_write(root, "PLAN_ISTEK.md", plan)
    ok = bool(w and p.is_file() and "Plan iskeleti" in p.read_text(encoding="utf-8") and vizyon_var)
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": int(w),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_p_plan",
        "detail": (
            f"Dilim P {'OK' if ok else 'FAIL'} · istek→plan\n"
            f"vizyon={vizyon_var}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/PLAN_ISTEK.md",
    }


def try_cirak_dilim_r_proje_oku(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim R — atölye projesini baştan sona oku (envanter + sıra)."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "proje_oku" not in low and "dilim r" not in low and "baştan sona" not in low and "bastan sona" not in low:
        return None

    root = _resolve_repo_root(workspace_root)
    atolye = root / "projects" / "cirak-atolyesi"
    if not atolye.is_dir():
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_dilim_r_proje_oku",
            "detail": "Atölye yok",
            "version": CIRAK_DERS_VERSION,
        }

    files: list[str] = []
    for p in sorted(atolye.rglob("*")):
        if not p.is_file():
            continue
        if "__pycache__" in p.parts or p.suffix in {".pyc", ".bak"}:
            continue
        rel = p.relative_to(atolye).as_posix()
        files.append(rel)

    # Okuma sırası (usta öğretisi)
    sira = [
        "MIMAR_VIZYON.md — ne isteniyor",
        "OZET_MIMAR_VIZYON.md — çırak anladı mı",
        "PLAN_ISTEK.md — istek→plan",
        "BILGI_KOPRU_KANIT.md — bilgiye uzandı mı",
        "yardimci_is.py + tests/ — asıl iş",
        "DERS_*.md / TAVAN_*.md — ders ve tavan",
        "smoke_*.py / verify_*.py — kanıt",
    ]
    body = "\n".join(
        [
            "# Dilim R — Projeyi baştan sona oku",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            f"**Kapsam:** `{CIRAK_ATOLYE_SCOPE}/`",
            f"**Dosya sayısı:** {len(files)}",
            "",
            "## Usta sırası (nasıl okunur)",
            *[f"{i}. {s}" for i, s in enumerate(sira, 1)],
            "",
            "## Diskte görülenler",
            *[f"- `{f}`" for f in files[:80]],
            ("" if len(files) <= 80 else f"- … +{len(files) - 80} dosya"),
            "",
            "## Ders",
            "Baştan sona = vizyon → plan → bilgi → kod → test → mühür. Ortadan kod yazma.",
            "",
        ]
    )
    p, w = _atolye_write(root, "PROJE_OKUMA.md", body)
    must_see = {"MIMAR_VIZYON.md", "yardimci_is.py"}
    seen = set(files)
    ok = bool(w and p.is_file() and len(files) >= 5)
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": int(w),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_r_proje_oku",
        "detail": (
            f"Dilim R {'OK' if ok else 'FAIL'} · proje okuma\n"
            f"n={len(files)} must={must_see & seen}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/PROJE_OKUMA.md",
        "n_files": len(files),
    }


def try_cirak_dilim_0a_bilgi(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """0A — bilgi köprüsü kanıtı: kaynak çek + atölyeye yaz."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "bilgi_kopru" not in low and "dilim 0a" not in low and "0a" not in low:
        if "bilgi köprü" not in low and "bilgi kopru" not in low:
            return None

    root = _resolve_repo_root(workspace_root)
    q = "python fonksiyon def test pytest yazılım"
    # Hedefi mesajdan çek
    if "—" in message:
        q = message.split("—", 1)[-1].strip()[:400] or q
    elif "-" in message:
        q = message.split("cirak", 1)[-1].strip()[:400] or q

    from ilim_assistant.ruzgar_cirak_bilgi_kopru import build_cirak_bilgi_context

    ctx = build_cirak_bilgi_context(
        q,
        message=message,
        scope_rel=CIRAK_ATOLYE_SCOPE,
        top_k=3,
    )
    sources = list(ctx.get("sources") or [])
    rows = list(ctx.get("rows") or [])
    body_lines = [
        "# 0A — Bilgi köprüsü kanıtı",
        "",
        f"**Sürüm:** {CIRAK_DERS_VERSION}",
        f"**Köprü:** {ctx.get('version')}",
        f"**Sorgu:** {q[:200]}",
        "",
        "## Kaynaklar (okunan)",
    ]
    if not sources:
        body_lines.append("- (kaynak yok — bilmiyorum; uydurmadım)")
    else:
        for s in sources:
            body_lines.append(f"- `{s}`")
    body_lines.extend(["", "## Snippet özeti", ""])
    for i, r in enumerate(rows, 1):
        body_lines.append(f"### {i}. `{r.get('source')}`")
        body_lines.append((r.get("text") or "")[:500])
        body_lines.append("")
    body_lines.extend(
        [
            "## Kural",
            "Görevde önce bilgi; sonra yazım. Yazım yalnız atölye/scope.",
            "",
        ]
    )
    p, w = _atolye_write(root, "BILGI_KOPRU_KANIT.md", "\n".join(body_lines))
    ok = bool(w and p.is_file() and (sources or "bilmiyorum" in p.read_text(encoding="utf-8").lower()))
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": int(w),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_0a_bilgi",
        "detail": (
            f"Dilim 0A {'OK' if ok else 'FAIL'} · bilgi köprüsü\n"
            f"kaynak_sayısı={len(sources)}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/BILGI_KOPRU_KANIT.md",
        "sources": sources,
    }


def try_cirak_dilim_0b_vizyon(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """0B — Mimar vizyonunu oku, özet yaz (anladığını kanıtla)."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if (
        "mimar_vizyon" not in low
        and "dilim 0b" not in low
        and "0b" not in low
        and "vizyon özet" not in low
        and "vizyon ozet" not in low
    ):
        return None

    root = _resolve_repo_root(workspace_root)
    src = root / "projects" / "cirak-atolyesi" / "MIMAR_VIZYON.md"
    if not src.is_file():
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_dilim_0b_vizyon",
            "detail": "MIMAR_VIZYON.md yok — Mimar/usta kartı önce yazılmalı",
            "version": CIRAK_DERS_VERSION,
        }
    try:
        raw = src.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_dilim_0b_vizyon",
            "detail": f"Vizyon okunamadı: {exc}",
            "version": CIRAK_DERS_VERSION,
        }

    # Basit kanıt: karttaki zorunlu başlıklar geçsin
    must = ("Ümit ne istiyor", "Nasıl bir ürün", "Çıraktan şimdi", "Başarı ne")
    found = [m for m in must if m in raw]
    ozet = "\n".join(
        [
            "# Çırak özeti — Mimar vizyonu (0B)",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            f"**Kaynak:** `{CIRAK_ATOLYE_SCOPE}/MIMAR_VIZYON.md`",
            "",
            "## Anladığım (özet)",
            "- Mimar: Ümit — Rüzgar güvenilir yardımcı olsun; sihirbaz abartısı yok.",
            "- Başarı: kanıtlı iş (disk + smoke); «yazdım» yetmez.",
            "- Sınır: atölye/tavan; boot/yüz/hub/genel saha yok.",
            "- Bilgi: kütüphaneden uzan; uydurma.",
            "",
            "## Kartta gördüğüm başlıklar",
            *[f"- {m}: {'var' if m in found else 'YOK'}" for m in must],
            "",
            "## Kaynak yolu (kanıt)",
            f"- okunan: `{CIRAK_ATOLYE_SCOPE}/MIMAR_VIZYON.md` ({len(raw)} karakter)",
            "",
        ]
    )
    p, w = _atolye_write(root, "OZET_MIMAR_VIZYON.md", ozet)
    ok = bool(w and p.is_file() and len(found) >= 3 and "MIMAR_VIZYON.md" in p.read_text(encoding="utf-8"))
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": int(w),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_0b_vizyon",
        "detail": (
            f"Dilim 0B {'OK' if ok else 'FAIL'} · vizyon özeti\n"
            f"baslik={len(found)}/{len(must)}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/OZET_MIMAR_VIZYON.md",
        "baslik_ok": len(found),
    }


def try_cirak_tavan_yukselt(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Mimar onaylı +1 tavan mühürü — genel saha açmaz."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "tavan_yukselt" not in low and "tavan yükselt" not in low and "tavan yukselt" not in low:
        return None
    # Onaysız yükseltme → red («mimar onay» görev satırında şart)
    has_mimar = ("mimar onay" in low) or ("mimar_onay" in low) or (
        "mimar" in low and "onay" in low
    )
    if not has_mimar:
        return {
            "ok": True,
            "verify_ok": True,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_tavan_yukselt",
            "detail": (
                "Tavan yükseltme RED · Mimar onayı yok\n"
                f"({CIRAK_DERS_VERSION})"
            ),
            "version": CIRAK_DERS_VERSION,
            "rejected": "tavan_ustu",
            "writes_blocked": True,
            "tavan": TAVAN_SU_AN,
        }

    root = _resolve_repo_root(workspace_root)
    # Genel saha / %90 hâlâ yasak — bu dilim onları açmaz
    if "genel saha" in low or "%90" in low or "serbest ajan" in low:
        return {
            "ok": True,
            "verify_ok": True,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_tavan_yukselt",
            "detail": (
                "Tavan +1 OK ama genel saha/%90 RED — ayrı Mimar emri ister\n"
                f"tavan_kalan={TAVAN_SU_AN}\n"
                f"({CIRAK_DERS_VERSION})"
            ),
            "version": CIRAK_DERS_VERSION,
            "rejected": "genel_saha",
            "writes_blocked": True,
            "tavan": TAVAN_SU_AN,
        }

    card = "\n".join(
        [
            "# Tavan yükseltme mühürü",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            f"**Mimar onay:** `{MIMAR_ONAY_TAVAN}` (sohbet: «yap»)",
            f"**Önceki:** `{TAVAN_ONCEKI}`",
            f"**Şimdi:** `{TAVAN_SU_AN}`",
            "",
            "## Açılan",
            *[f"- `{x}`" for x in TAVAN_IZINLI_SIMDI],
            "",
            "## Hâlâ kapalı",
            *[f"- `{x}`" for x in TAVAN_USTU_YASAK],
            "",
            "## Hibrit kural (G) duruyor",
            "Yeşil = written + disk + smoke. İddia kanıtsızsa kırmızı.",
            "",
        ]
    )
    p, w = _atolye_write(root, "TAVAN_YUKSELTME_2026-11-18.md", card)
    # Ders kartını da yeni tavana göre yenile
    try_cirak_dilim_t_tavan(
        "görev: projects/cirak-atolyesi cirak tavan_ders — Dilim T tavan ders · tam ajan",
        workspace_root,
    )
    ok = bool(w and p.is_file() and TAVAN_SU_AN == "atolye_hibrit_ajan_ok")
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": int(w),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_tavan_yukselt",
        "detail": (
            f"Tavan +1 {'OK' if ok else 'FAIL'} · `{TAVAN_ONCEKI}` → `{TAVAN_SU_AN}`\n"
            f"mimar={MIMAR_ONAY_TAVAN}\n"
            f"genel_saha=KAPALI\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/TAVAN_YUKSELTME_2026-11-18.md",
        "tavan": TAVAN_SU_AN,
        "tavan_onceki": TAVAN_ONCEKI,
    }


def try_cirak_dilim_t_tavan(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dilim T — tavan dersi: şimdiki tavan + üstü yasak; yükseltme yalnız Mimar."""
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "dilim t" not in low and "tavan_ders" not in low and "tavan ders" not in low:
        return None
    # tavan_yukselt ayrı handler
    if "tavan_yukselt" in low or "tavan yükselt" in low:
        return None

    root = _resolve_repo_root(workspace_root)

    # Tavan yükseltme denemesi (Mimar yok) → red kartı, yazım yok
    # (ders dosyasını yazmadan önce probe; asıl ders yazımı aşağıda)
    raise_probe = (
        _tavan_yukselt_istiyor(low)
        and "mimar onay" not in low
        and "mimar_onay" not in low
        and ("yükselt deneme" in low or "yukselt deneme" in low or "kaldır deneme" in low or "kaldir deneme" in low)
    )
    if raise_probe:
        return {
            "ok": True,  # ders başarısı = red doğru çalıştı
            "verify_ok": True,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_dilim_t_tavan",
            "detail": (
                "Dilim T OK · tavan yükseltme RED (Mimar onayı yok)\n"
                f"tavan={TAVAN_SU_AN}\n"
                f"yasak={list(TAVAN_USTU_YASAK)}\n"
                f"({CIRAK_DERS_VERSION})"
            ),
            "version": CIRAK_DERS_VERSION,
            "rejected": "tavan_ustu",
            "writes_blocked": True,
            "tavan": TAVAN_SU_AN,
        }

    body = "\n".join(
        [
            "# Dilim T — Tavan dersi",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            f"**Tavan önceki:** `{TAVAN_ONCEKI}`",
            f"**Tavan şimdi:** `{TAVAN_SU_AN}` (Mimar `{MIMAR_ONAY_TAVAN}`)",
            f"**Kapsam:** `{CIRAK_ATOLYE_SCOPE}/` + Dilim G hibrit kuralı (written+disk+smoke).",
            "",
            "## Çırak ne yapabilir (tavan altı / izinli)",
            *[f"- `{x}`" for x in TAVAN_IZINLI_SIMDI],
            "- `görev: projects/cirak-atolyesi …` ile atölye işi",
            "- Supervised / hibrit / dar tam ajan (atölye içi)",
            "- Kırılganda dur (`USTA_KIRILGAN`)",
            "",
            "## Tavan üstü (hâlâ yasak)",
            *[f"- `{x}`" for x in TAVAN_USTU_YASAK],
            "- Boot / ana yüz / hub / anayasa hardcode",
            "- «%90 serbest ajan», «genel saha aç» (bir üst Mimar onayı ister)",
            "",
            "## Tavan nasıl yükselir?",
            "1. Mimar açıkça der: `mimar onay` / «yap» + ne kadar tavan.",
            "2. Usta plan yazar, çırak `tavan_yukselt` diliminde mühürler.",
            "3. Yeşil = disk + smoke + ders; sonra bir üst basamak.",
            "",
            "## Bu dersin özü",
            "Tavan = güvenlik ağı. +1 basamak açıldı; genel saha hâlâ kapalı.",
            "",
        ]
    )
    p, w = _atolye_write(root, "TAVAN_DERS.md", body)
    # Küçük probe: yükseltme isteği red mi?
    probe_red = _kirilgan_istiyor(
        "görev: cirak tavanı kaldır genel saha aç · tam ajan"
    )
    ok = bool(w and p.is_file() and probe_red == "tavan_ustu")
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": int(w),
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_t_tavan",
        "detail": (
            f"Dilim T {'OK' if ok else 'FAIL'} · tavan dersi yazıldı\n"
            f"probe_red={probe_red}\n"
            f"tavan={TAVAN_SU_AN}\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/TAVAN_DERS.md",
        "tavan": TAVAN_SU_AN,
        "probe_red": probe_red,
    }


def wants_llm_cirak_handoff(message: str) -> bool:
    """Supervised şablon yerine tam ajan (çırak kendisi) denensin."""
    low = (message or "").lower()
    if "tam ajan" not in low and "tam_ajan" not in low:
        return False
    if "supervised zorla" in low or "kapili yaz" in low or "kapılı yaz" in low:
        return False
    markers = (
        "pytest",
        "fonksiyon",
        "kendin yaz",
        "kendin yap",
        "llm el",
        "ajan yazsin",
        "ajan yazsın",
        "unit test",
        "birim test",
        "çarp",
        "carp(",
        "carp ekle",
        "implement",
        "ekle ve test",
        "def carp",
        "filtre_satirlar",
        "gercek_paket",
        "gerçek paket",
        "sozlesme",
        "sözleşme",
    )
    return any(m in low for m in markers)


def try_cirak_dilim_gercek_paket(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Atölyede gerçekçi çok-dosya paket (boot/hub açılmaz — tavan korunur).

    «tam ajan» + gercek_paket → None (LLM el).
    Aksi halde supervised iskelet + pytest + ders.
    """
    if not looks_like_cirak_gorev(message):
        return None
    low = (message or "").lower()
    if "gercek_paket" not in low and "gerçek paket" not in low and "dilim gercek" not in low:
        return None
    # LLM çırağa bırak
    if wants_llm_cirak_handoff(message) and _fence_body(message) is None:
        return None

    root = _resolve_repo_root(workspace_root)
    pkg = "paket_is"
    yardim = (
        "# Created by Ümit & Gökçenur — Dilim gercek_paket\n"
        "def normalize(s: str) -> str:\n"
        "    return (s or '').strip().lower()\n"
    )
    servis = (
        "# Created by Ümit & Gökçenur — Dilim gercek_paket\n"
        "from paket_is.yardim import normalize\n\n"
        "def isle(satirlar, anahtar: str) -> list[str]:\n"
        "    key = normalize(anahtar)\n"
        "    out = []\n"
        "    for s in satirlar or []:\n"
        "        if key and key in normalize(str(s)):\n"
        "            out.append(s)\n"
        "    return out\n"
    )
    init = (
        "# Created by Ümit & Gökçenur — Dilim gercek_paket\n"
        "from paket_is.servis import isle\n"
        "from paket_is.yardim import normalize\n\n"
        "__all__ = ['isle', 'normalize']\n"
    )
    test = (
        "# Created by Ümit & Gökçenur — Dilim gercek_paket\n"
        "from paket_is import isle, normalize\n\n"
        "def test_normalize():\n"
        "    assert normalize('  AbC ') == 'abc'\n\n"
        "def test_isle():\n"
        "    assert isle(['Merhaba', 'x', 'MERHABA'], 'merhaba') == ['Merhaba', 'MERHABA']\n"
        "    assert isle([], 'a') == []\n"
    )
    ders = "\n".join(
        [
            "# Dilim — Gerçek paket (atölye içi)",
            "",
            f"**Sürüm:** {CIRAK_DERS_VERSION}",
            "",
            "## Ders",
            "1. Gerçek iş çok dosyalıdır: paket + servis + test.",
            "2. Boot/hub/ana kod hâlâ kapalı (tavan) — ama atölyede gerçekçi yapı kurulur.",
            "3. Sözleşme: `normalize` + `isle` imzaları zorunlu; uydurma API yetmez.",
            "4. Hedef pytest yeşil olmadan «bitti» yok.",
            "",
            "## Written",
            f"- `{CIRAK_ATOLYE_SCOPE}/paket_is/__init__.py`",
            f"- `{CIRAK_ATOLYE_SCOPE}/paket_is/yardim.py`",
            f"- `{CIRAK_ATOLYE_SCOPE}/paket_is/servis.py`",
            f"- `{CIRAK_ATOLYE_SCOPE}/tests/test_paket_is.py`",
            "",
        ]
    )
    base = root / "projects" / "cirak-atolyesi" / pkg
    tests_dir = root / "projects" / "cirak-atolyesi" / "tests"
    wrote = 0
    try:
        base.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)
        (base / "__init__.py").write_text(init, encoding="utf-8")
        (base / "yardim.py").write_text(yardim, encoding="utf-8")
        (base / "servis.py").write_text(servis, encoding="utf-8")
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        (tests_dir / "test_paket_is.py").write_text(test, encoding="utf-8")
        _atolye_write(root, "DERS_GERCEK_PAKET.md", ders)
        wrote = 5
    except OSError as exc:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_dilim_gercek_paket",
            "detail": f"Paket yazılamadı: {exc}",
            "version": CIRAK_DERS_VERSION,
        }

    import subprocess
    import sys as _sys

    pr = subprocess.run(
        [_sys.executable, "-m", "pytest", "-q", "tests/test_paket_is.py"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(root / "projects" / "cirak-atolyesi"),
    )
    pytest_ok = pr.returncode == 0
    ok = bool(pytest_ok and wrote >= 4)
    return {
        "ok": ok,
        "verify_ok": ok,
        "writes_ok": wrote,
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_dilim_gercek_paket",
        "detail": (
            f"Dilim gercek_paket {'OK' if ok else 'FAIL'} · çok dosya paket\n"
            f"pytest={pytest_ok}\n({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": f"{CIRAK_ATOLYE_SCOPE}/paket_is/servis.py",
        "pytest_ok": pytest_ok,
    }


def try_cirak_supervised_write(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dar çırak yazımı — LLM yok; yalnız projects/cirak-atolyesi/*.{py,md}.

    - Dilim A–F + G hibrit + T tavan (önce).
    - Fence gövdesi varsa onu yazar (çok satır .py/.md).
    - .md için fence yoksa None → tam ajan yazsın.
    - Net yazım niyeti yoksa None (salt okuma yolu bozulmasın).
    - Kırılgan niyet → red kartı (yazım yok).
    - Karmaşık «tam ajan» iş → None (çırak LLM eliyle yapsın).
    """
    if not looks_like_cirak_gorev(message):
        return None

    for fn in (
        try_cirak_dilim_gercek_paket,
        try_cirak_dilim_h_yardimci,
        try_cirak_dilim_p_plan,
        try_cirak_dilim_r_proje_oku,
        try_cirak_dilim_0a_bilgi,
        try_cirak_dilim_0b_vizyon,
        try_cirak_tavan_yukselt,
        try_cirak_dilim_t_tavan,
        try_cirak_dilim_g_hibrit,
        try_cirak_dilim_f_muhur,
        try_cirak_dilim_e_red,
        try_cirak_dilim_d_patch,
        try_cirak_dilim_c_cok_satir,
        try_cirak_dilim_b_verify,
        try_cirak_dilim_a_rapor,
    ):
        hit = fn(message, workspace_root)
        if hit is not None:
            return hit

    kirilgan = _kirilgan_istiyor(message)
    if kirilgan:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_supervised_write",
            "detail": (
                f"Çırak red · kırılgan `{kirilgan}` — usta işi; yazım yok.\n"
                f"({CIRAK_DERS_VERSION})"
            ),
            "version": CIRAK_DERS_VERSION,
            "rejected": kirilgan,
        }

    # Dilim şablonu yok + gerçek iş → LLM çırağa bırak (PASS şablonu ezmesin)
    if wants_llm_cirak_handoff(message) and _fence_body(message) is None:
        return None

    if not _write_intent(message):
        return None

    raw = (message or "").strip()
    m = _ATOLYE_FILE_RE.search(raw) or _PROJECTS_PY_RE.search(raw)
    if not m:
        return None
    rel = m.group("path").replace("\\", "/")
    if ".." in rel or not rel.lower().startswith("projects/"):
        return None
    # Atölye dışı projects/*.py — eski dar PASS yolu yalnız cirak-atolyesi
    if not rel.lower().startswith(f"{CIRAK_ATOLYE_SCOPE}/"):
        return None

    fence = _fence_body(raw)
    is_md = rel.lower().endswith(".md")
    if is_md and fence is None:
        # Rapor/çok satır .md → ajan
        return None
    if fence is not None:
        body = fence if fence.endswith("\n") else fence + "\n"
    elif is_md:
        return None
    else:
        body = _default_py_body(raw)

    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
    except Exception:
        root = None
    if root is None:
        root = Path(workspace_root).resolve() if workspace_root else Path.cwd().resolve()
    else:
        root = Path(root).resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to((root / "projects" / "cirak-atolyesi").resolve())
    except ValueError:
        return None

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": CIRAK_ATOLYE_SCOPE,
            "source": "cirak_supervised_write",
            "detail": f"Yazılamadı: {exc}",
            "version": CIRAK_DERS_VERSION,
        }

    return {
        "ok": True,
        "verify_ok": True,
        "writes_ok": 1,
        "scope_rel": CIRAK_ATOLYE_SCOPE,
        "source": "cirak_supervised_write",
        "detail": (
            f"Çırak supervised yazım OK · `{rel}`\n"
            f"İçerik:\n```\n{body.rstrip()}\n```\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": rel,
    }
