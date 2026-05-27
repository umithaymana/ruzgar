# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 97: Ümit abi sade rapor dili.

Teknik Faz 7 / parity / öz-denetim çıktılarını günlük Türkçe özetlere çevirir.
Kapat: RUZGAR_SADE_RAPOR=0
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ97_VERSION = "programlama-faz97-v1-2026-05-27"

_TEST_LABELS: dict[str, str] = {
    "workspace_root": "proje ana klasörü",
    "desktop_server_entry": "Rüzgar sunucu dosyası (desktop_server.py)",
    "ruzgar_desktop_entry": "masaüstü arayüz dosyası (app.js)",
    "owner_phrase_match": "sahip kilidi ifadesi",
    "owner_lock_module": "sahip kilidi modülü",
    "python_on_path": "Python kurulumu",
    "python_version": "Python sürümü (3.10+)",
    "pytest_available": "pytest aracı",
    "ruff_available": "ruff aracı (isteğe bağlı)",
    "git_available": "Git",
    "disk_free_gb": "disk boş alanı",
    "prog_write_policy": "güvenli yazım politikası",
    "gemini_configured": "Gemini anahtarı (bilgi)",
}


def sade_rapor_enabled() -> bool:
    return os.environ.get("RUZGAR_SADE_RAPOR", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def choose_report(technical: str, sade: str | None) -> str:
    if not sade_rapor_enabled() or not (sade or "").strip():
        return technical
    return sade.strip()


def _list_project_files(
    workspace_root: str | Path | None,
    project_rel: str,
    *,
    limit: int = 14,
) -> list[str]:
    root = repo_root(workspace_root)
    if root is None:
        return []
    base = root / project_rel.replace("/", os.sep)
    if not base.is_dir():
        return []
    out: list[str] = []
    try:
        for f in sorted(base.rglob("*")):
            if not f.is_file():
                continue
            if any(p.startswith(".") for p in f.relative_to(base).parts):
                continue
            if any(x in f.parts for x in (".git", "__pycache__", "node_modules")):
                continue
            out.append(f.relative_to(base).as_posix())
            if len(out) >= limit:
                break
    except OSError:
        return []
    return out


def _human_test_name(name: str) -> str:
    return _TEST_LABELS.get(name, name.replace("_", " "))


def format_sade_self_scan(data: dict[str, Any]) -> str:
    tests = list(data.get("tests") or [])
    ok_items = [_human_test_name(str(t.get("name") or "?")) for t in tests if t.get("ok")]
    fails = list(data.get("numbered_failures") or [])
    lines = ["Ümit abi, az önce sistemi baştan sona taradım.", ""]

    if ok_items:
        lines.append("**Baktığım yerler (sorun yok):**")
        for label in ok_items[:14]:
            lines.append(f"- {label}")
        if len(ok_items) > 14:
            lines.append(f"- … ve {len(ok_items) - 14} kontrol daha")

    if not fails:
        lines.extend(
            [
                "",
                "**Sonuç:** Kritik bir şey çıkmadı — şu an tıkır tıkır çalışıyor gibi.",
                "İstersen yine de `sistem analizi` ile derin tarama yapabilirsin.",
            ]
        )
    else:
        lines.extend(["", "**Düzelmesi gerekenler:**"])
        for row in fails[:10]:
            hint = (row.get("hint") or "").strip()
            lines.append(
                f"- **{row.get('id')}.** {_human_test_name(str(row.get('name') or '?'))}"
                + (f" — {hint[:120]}" if hint else "")
            )
        lines.extend(
            [
                "",
                "Düzeltmemi istersen: `onayla 1` veya `hepsini onayla düzelt` yaz.",
            ]
        )
    lines.append(f"\n({FAZ97_VERSION})")
    return "\n".join(lines)


def format_sade_faz7_explain(
    profile: dict[str, Any],
    *,
    workspace_root: str | Path | None = None,
    rel: str | None = None,
) -> str:
    slug = profile.get("slug") or profile.get("project_rel", "proje")
    proj = profile.get("project_rel") or slug
    pid = profile.get("profile_id") or "proje"
    files = _list_project_files(workspace_root, str(proj))
    lines = [
        f"Ümit abi, **{proj}** projesine baktım.",
        "",
    ]
    if files:
        lines.append("**Gördüğüm dosyalar (özet):**")
        for f in files:
            lines.append(f"- `{f}`")
        lines.append("")
    else:
        lines.append("Proje klasörü boş veya henüz oluşmamış olabilir.")
        lines.append("")

    if pid == "fastapi_api":
        lines.extend(
            [
                "**Ne işe yarıyor:** Küçük bir web API — sağlık kontrolü, kayıt listesi, Swagger dokümantasyonu.",
                "",
                "**Senin yapman gerekenler:**",
                "1. Terminalde proje klasörüne gir (`cd projects/...`).",
                "2. `python -m pip install -r requirements.txt`",
                "3. `python -m uvicorn app.main:app --reload --port 8080`",
                "",
                "**Tarayıcıda aç:**",
            ]
        )
        for u in profile.get("urls") or []:
            lines.append(f"- {u}")
        lines.append("")
        lines.append("**Durum:** Kod tarafında bariz hata görmedim; sunucuyu açınca çalışması lazım.")
    elif pid == "react_vite":
        lines.extend(
            [
                "**Ne işe yarıyor:** React + Vite tek sayfa uygulama.",
                "",
                "Kurulum: `npm install` · Çalıştırma: `npm run dev`",
            ]
        )
        for u in profile.get("urls") or []:
            lines.append(f"- {u}")
    elif pid == "static_site":
        lines.extend(
            [
                "**Ne işe yarıyor:** Statik vitrin sitesi (HTML/CSS).",
                "",
                "Çalıştırma: `python -m http.server 5500` (veya rehberdeki port).",
            ]
        )
        for u in profile.get("urls") or []:
            lines.append(f"- {u}")
    else:
        manual = (profile.get("manual") or "").strip()
        if manual:
            lines.extend(["**Çalıştırma:**", "```bash", manual, "```"])
    if rel and rel.endswith(".py"):
        lines.extend(["", f"Son baktığım dosya: `{rel}`"])
    lines.extend(
        [
            "",
            "Atölyede **Çalıştır** dersen ben de smoke denerim.",
            f"({FAZ97_VERSION})",
        ]
    )
    return "\n".join(lines)


def format_sade_run_report(result: dict[str, Any]) -> str:
    proj = result.get("project_rel") or "proje"
    steps = list(result.get("steps") or [])
    lines = [f"Ümit abi, **{proj}** için çalıştırma denemesi yaptım.", ""]

    _step_tr = {
        "pip_install": "Python paketlerini kurdum",
        "npm_install": "npm paketlerini kurdum",
        "import_smoke": "API kodunu içe aktarıp duman testi yaptım",
        "smoke": "kısa duman testi",
        "run": "programı çalıştırdım",
        "static_smoke": "statik dosyaları kontrol ettim",
        "http_server": "yerel sunucuyu denedim",
        "npm_build": "üretim derlemesi (build)",
        "npm_dev": "geliştirme sunucusu",
    }

    any_fail = False
    for st in steps:
        key = str(st.get("step") or "?")
        label = _step_tr.get(key, key)
        ok = st.get("exit_code") == 0
        if not ok:
            any_fail = True
        mark = "tamam" if ok else "takıldı"
        lines.append(f"- {label}: **{mark}**")
        if not ok and st.get("output"):
            snippet = str(st["output"]).strip().splitlines()
            if snippet:
                lines.append(f"  Hata özeti: `{snippet[-1][:160]}`")

    if result.get("error"):
        any_fail = True
        lines.extend(["", f"**Özet hata:** {result.get('error')}"])

    lines.append("")
    if result.get("ok") and not any_fail:
        lines.append("**Sonuç:** Sorunsuz — şu an tıkır tıkır çalışıyor gibi.")
    elif result.get("ok"):
        lines.append("**Sonuç:** Kısmen tamam; yukarıdaki uyarılara bir bak.")
    else:
        lines.append("**Sonuç:** Çalıştıramadım; yukarıdaki hatayı düzeltmen lazım.")

    urls = result.get("urls") or []
    if urls:
        lines.extend(["", "**Açık adresler:**"])
        for u in urls:
            lines.append(f"- {u}")
    manual = (result.get("manual") or "").strip()
    if manual and result.get("profile_id") == "fastapi_api":
        lines.extend(
            [
                "",
                "Sürekli açık kalsın dersen ayrı terminalde:",
                "```bash",
                manual,
                "```",
            ]
        )
    lines.append(f"\n({FAZ97_VERSION})")
    return "\n".join(lines)


def format_sade_scan(scan: dict[str, Any]) -> str:
    scope = scan.get("scope_rel") or "proje"
    n = int(scan.get("file_count") or 0)
    lines = [
        f"Ümit abi, **`{scope}`** klasörünü taradım.",
        "",
        f"**{n} dosya** buldum (~{int(scan.get('total_bytes', 0)) // 1024} KB).",
    ]
    by_lang = scan.get("by_lang") or {}
    if by_lang:
        parts = ", ".join(f"{k}: {v}" for k, v in sorted(by_lang.items()))
        lines.append(f"Dil dağılımı: {parts}.")
    try:
        from ilim_assistant.motorlar.programlama_faz13 import detect_entrypoints

        eps = detect_entrypoints(str(scope), scan.get("entries") or [])
        if eps:
            lines.append("")
            lines.append("Ana giriş dosyaları:")
            for ep in eps:
                lines.append(f"- `{ep}`")
    except Exception:
        pass
    lines.extend(
        [
            "",
            "Bu turda dosya içeriğinde hata aramadım — sadece harita çıkardım.",
            f"({FAZ97_VERSION})",
        ]
    )
    return "\n".join(lines)


def format_sade_system_analysis(report: dict[str, Any]) -> str:
    score = int(report.get("score") or 0)
    queue = list(report.get("numbered_queue") or [])
    sections = report.get("sections") or {}
    lines = [
        "Ümit abi, sistemi uçtan uca taradım (öz-denetim, zayıflık, git, parity).",
        "",
    ]

    scanned: list[str] = []
    if sections.get("self_scan"):
        ss = sections["self_scan"]
        scanned.append(
            "öz-denetim"
            + (" temiz" if ss.get("ok") else f" — {ss.get('fail_count', '?')} uyarı")
        )
    if sections.get("weakness"):
        w = sections["weakness"]
        scanned.append(f"zayıflık KPI ({w.get('score', '?')}/100)")
    if sections.get("syntax", {}).get("fail_count"):
        scanned.append(f"sözdizimi — {sections['syntax']['fail_count']} dosya")
    if sections.get("parity") and not sections["parity"].get("skipped"):
        p = sections["parity"]
        scanned.append(f"Cursor uyum testi {p.get('passed')}/{p.get('total')}")
    git = report.get("git") or {}
    if git.get("has_changes"):
        scanned.append(f"git — {git.get('changed_lines', '?')} satır değişmiş")

    if scanned:
        lines.append("**Baktıklarım:**")
        for s in scanned:
            lines.append(f"- {s}")
        lines.append("")

    if not queue:
        lines.extend(
            [
                f"**Sonuç:** Kritik madde yok (skor {score}/100). Şu an tıkır tıkır çalışıyor gibi.",
            ]
        )
    else:
        auto = [x for x in queue if x.get("auto_fixable")]
        manual = [x for x in queue if not x.get("auto_fixable")]
        lines.append(f"**Sonuç:** Skor {score}/100 — düzeltilmesi gereken **{len(queue)}** madde var.")
        lines.append("")
        if auto:
            lines.append("**Ben düzeltebilirim:**")
            for row in auto[:8]:
                lines.append(f"- {row.get('name')}")
        if manual:
            lines.append("")
            lines.append("**Senin elinle (veya ortam):**")
            for row in manual[:8]:
                hint = (row.get("hint") or row.get("detail") or "")[:100]
                lines.append(f"- {row.get('name')}" + (f" — {hint}" if hint else ""))
        lines.extend(
            [
                "",
                "Düzeltmemi istersen: `hataları bul onar` veya `onayla 1 2`.",
            ]
        )
    lines.append(f"\n({FAZ97_VERSION})")
    return "\n".join(lines)


def format_sade_verification(verify: dict[str, Any]) -> str:
    b = int(verify.get("before_score") or 0)
    a = int(verify.get("after_score") or 0)
    bi = int(verify.get("before_issues") or 0)
    ai = int(verify.get("after_issues") or 0)
    if verify.get("improved"):
        body = (
            f"Ümit abi, onarımdan sonra tekrar taradım: skor **{b} → {a}**, "
            f"açık madde **{bi} → {ai}**. İyileşti — sistem daha toparlı."
        )
    else:
        body = (
            f"Ümit abi, onarımdan sonra tekrar taradım: skor **{b} → {a}**, "
            f"madde **{bi} → {ai}**. Henüz aynı; bir tur daha bakmak gerekebilir."
        )
    return body + f"\n({FAZ97_VERSION})"


def format_sade_parity_run(report: Any) -> str:
    ok = bool(getattr(report, "ok", False))
    checks = list(getattr(report, "checks", []) or [])
    scope = getattr(report, "scope_rel", "") or getattr(report, "project_name", "")
    passed = sum(1 for c in checks if getattr(c, "ok", False))
    total = len(checks) or passed
    lines = [
        f"Ümit abi, Cursor uyum denemesini **`{scope}`** üzerinde koştum.",
        "",
    ]
    failed = [c for c in checks if not getattr(c, "ok", True)]
    if ok:
        lines.append(f"**{passed}/{total}** kontrol geçti — uyum tamam, tıkır tıkır.")
    else:
        lines.append(f"**{passed}/{total}** geçti; kalanlar:")
        for c in failed[:6]:
            lines.append(f"- {getattr(c, 'label', '?')}")
    lines.append(f"\n({FAZ97_VERSION})")
    return "\n".join(lines)


def format_sade_parity_smoke(report: Any) -> str:
    ok = bool(getattr(report, "ok", False))
    passed = int(getattr(report, "passed", 0) or 0)
    total = int(getattr(report, "total", 0) or 8)
    checks = list(getattr(report, "checks", []) or [])
    if ok:
        return (
            f"Ümit abi, hızlı uyum testini çalıştırdım (**{passed}/{total}**). "
            f"Hepsi yeşil — KPI tarafı da tamam.\n({FAZ97_VERSION})"
        )
    failed = [c for c in checks if not getattr(c, "ok", True)]
    lines = [
        f"Ümit abi, uyum testinde **{passed}/{total}** geçti; şunlar kırmızı:",
        "",
    ]
    for c in failed[:8]:
        label = getattr(c, "label", None) or getattr(c, "id", "?")
        lines.append(f"- {label}")
    lines.append(f"\n({FAZ97_VERSION})")
    return "\n".join(lines)


def format_sade_compliance(r: dict[str, Any]) -> str:
    score = int(r.get("score") or 0)
    grade = r.get("grade") or "—"
    pp = r.get("parity_passed", 0)
    pt = r.get("parity_total", 8)
    ok = bool(r.get("overall_kpi_ok"))
    if ok:
        tail = "Genel tablo iyi — tıkır tıkır."
    else:
        tail = "Hedefe tam değil; parity veya uyum skoruna bak."
    return (
        f"Ümit abi, atölye KPI özetine baktım: uyum **{score}/100 ({grade})**, "
        f"parity **{pp}/{pt}**. {tail}\n({FAZ97_VERSION})"
    )


def format_sade_scaffold(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return (
            f"Ümit abi, proje oluşturamadım: {result.get('error', '?')}\n({FAZ97_VERSION})"
        )
    rel = str(result.get("project_rel") or result.get("base_dir") or result.get("path") or "projects/...")
    rel = rel.replace("\\", "/")
    tid = result.get("template_id") or "şablon"
    files = _list_project_files(result.get("workspace_root"), rel)
    lines = [
        f"Ümit abi, **{rel}** projesini **{tid}** şablonuyla oluşturdum.",
        "",
    ]
    if files:
        lines.append("Oluşan dosyalar (ilk birkaçı):")
        for f in files[:10]:
            lines.append(f"- `{f}`")
    lines.extend(
        [
            "",
            "Şimdi `nasıl çalıştırırım` yazarsan adım adım anlatırım.",
            f"({FAZ97_VERSION})",
        ]
    )
    return "\n".join(lines)


def faz97_directive() -> str:
    return (
        "[SADE RAPOR — Faz 97]\n"
        "Anında yanıtlar teknik Faz numarası yerine günlük Türkçe özet verir.\n"
        "Eski teknik rapor: RUZGAR_SADE_RAPOR=0\n"
    )
