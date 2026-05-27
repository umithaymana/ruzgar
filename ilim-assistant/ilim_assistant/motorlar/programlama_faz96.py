# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 96 (P11): Otonom sistem analizi + güvenli onarım.

Tek komutla: self-scan, zayıflık, git, parity quick, sözdizimi → numaralı kuyruk.
Onarım: minimal patch, P2 risk, pytest doğrulama, post-verify.

Komutlar:
  «sistem analizi» · «tam analiz» — salt okuma rapor
  «hataları bul onar» · «kendini tara onar» — analiz + LLM onarım turu
  «onayla 1 2» (P11 kuyruğu) · «analiz onarımı başlat»
"""

from __future__ import annotations

import json
import os
import py_compile
import re
import subprocess
import time
from pathlib import Path
from typing import Any

FAZ96_VERSION = "programlama-faz96-v1-2026-05-27"
_REPORT_FILE = "system_analysis_last.json"

_FULL_CYCLE_RE = re.compile(
    r"(?:"
    r"hatalar[ıi]\s+bul\s+(?:ve\s+)?onar|"
    r"analiz\s+et\s+(?:ve\s+)?onar|"
    r"kendini\s+tara\s+(?:ve\s+)?onar|"
    r"otonom\s+onar|"
    r"tam\s+analiz\s+onar|"
    r"sistemi\s+tara\s+(?:ve\s+)?onar|"
    r"bul\s+ve\s+onar|"
    r"scan\s+and\s+fix|"
    r"fix\s+all\s+issues"
    r")",
    re.I,
)

_ANALYSIS_RE = re.compile(
    r"(?:"
    r"sistem\s+analizi|"
    r"otonom\s+analiz|"
    r"tam\s+analiz(?!\s+onar)|"
    r"system\s+analysis|"
    r"kendini\s+tara\s+analiz|"
    r"hatalar[ıi]\s+analiz|"
    r"sistemi\s+tara\s+analiz|"
    r"kod\s+tara\s+analiz"
    r")",
    re.I,
)

_REPAIR_START_RE = re.compile(
    r"(?:"
    r"analiz\s+on(?:ar|arım|arim)|"
    r"onar(?:ım[ıi]|im[iı])?\s+ba[sş]lat|"
    r"hatalar[ıi]\s+onar|"
    r"onarımı\s+ba[sş]lat|"
    r"onarm[iı]\s+ba[sş]lat"
    r")",
    re.I,
)

_P11_APPROVAL_RE = re.compile(r"\bonayla\s+(\d|[\w_])", re.I)

_last_analysis_state: dict[str, Any] | None = None
_force_p11_repair_turn: bool = False


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ96", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz96_enabled() -> bool:
    return _enabled()


def wants_full_autonomous_cycle(message: str) -> bool:
    return _enabled() and bool(_FULL_CYCLE_RE.search((message or "").strip()))


def wants_system_analysis(message: str) -> bool:
    if not _enabled():
        return False
    msg = (message or "").strip()
    if wants_full_autonomous_cycle(msg):
        return True
    return bool(_ANALYSIS_RE.search(msg))


def wants_autonomous_repair_start(message: str) -> bool:
    return _enabled() and bool(_REPAIR_START_RE.search((message or "").strip()))


def wants_p11_fix_approval(message: str) -> bool:
    if not _enabled():
        return False
    low = (message or "").lower()
    if not _P11_APPROVAL_RE.search(low):
        return False
    if any(
        k in low
        for k in (
            "onaylıyorum düzelt",
            "onayliyorum duzelt",
            "hepsini onayla düzelt",
            "hepsini onayla duzelt",
        )
    ):
        return False
    return get_last_analysis_state() is not None


def _max_fix_items() -> int:
    try:
        return max(1, min(12, int(os.environ.get("RUZGAR_P11_MAX_FIX_ITEMS", "6"))))
    except ValueError:
        return 6


def _report_path(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        d = root / ".ruzgar"
        d.mkdir(parents=True, exist_ok=True)
        return d / _REPORT_FILE
    except Exception:
        return None


def _persist_report(workspace_root: str | Path | None, report: dict[str, Any]) -> None:
    path = _report_path(workspace_root)
    if not path:
        return
    try:
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def _store_analysis_state(data: dict[str, Any]) -> None:
    global _last_analysis_state
    _last_analysis_state = {
        "data": data,
        "queue": list(data.get("repair_queue") or []),
        "numbered_queue": list(data.get("numbered_queue") or []),
        "at": time.time(),
        "version": FAZ96_VERSION,
    }


def get_last_analysis_state() -> dict[str, Any] | None:
    return _last_analysis_state


def clear_force_p11_repair_turn() -> None:
    global _force_p11_repair_turn
    _force_p11_repair_turn = False


def should_force_p11_repair_turn(message: str) -> bool:
    if _force_p11_repair_turn:
        return True
    return wants_autonomous_repair_start(message) or wants_full_autonomous_cycle(message)


def _gather_git_repo_summary(workspace_root: str | Path | None) -> dict[str, Any]:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return {"ok": False, "error": "workspace yok"}
        if not (root / ".git").exists():
            return {"ok": True, "is_repo": False, "has_changes": False, "preview": ""}
        r = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=8,
            encoding="utf-8",
            errors="replace",
        )
        preview = (r.stdout or "").strip()[:1200]
        return {
            "ok": r.returncode == 0,
            "is_repo": True,
            "has_changes": bool(preview),
            "changed_lines": len([x for x in preview.splitlines() if x.strip()]),
            "preview": preview,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}


def _syntax_spot_check(workspace_root: str | Path | None) -> list[dict[str, Any]]:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return []
    except Exception:
        return []

    rels: list[str] = [
        "ilim-assistant/desktop_server.py",
        "ilim-assistant/ilim_assistant/llm_brain.py",
        "ilim-assistant/ilim_assistant/motorlar/programlama_motoru.py",
    ]
    motor_dir = root / "ilim-assistant" / "ilim_assistant" / "motorlar"
    if motor_dir.is_dir():
        for fp in sorted(motor_dir.glob("programlama_faz9*.py")):
            rels.append(str(fp.relative_to(root)).replace("\\", "/"))

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rel in rels:
        if rel in seen:
            continue
        seen.add(rel)
        fp = root / rel.replace("/", os.sep)
        if not fp.is_file():
            continue
        try:
            py_compile.compile(str(fp), doraise=True)
            out.append({"path": rel, "ok": True, "detail": ""})
        except py_compile.PyCompileError as exc:
            out.append({"path": rel, "ok": False, "detail": str(exc)[:240]})
        except Exception as exc:
            out.append({"path": rel, "ok": False, "detail": str(exc)[:180]})
    return out


def _run_parity_quick(workspace_root: str | Path | None) -> dict[str, Any]:
    if os.environ.get("RUZGAR_P11_SKIP_PARITY", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return {"ok": True, "skipped": True, "reason": "RUZGAR_P11_SKIP_PARITY=1"}
    try:
        from ilim_assistant.motorlar.programlama_faz54 import run_parity_smoke_suite

        rep = run_parity_smoke_suite(workspace_root, mode="quick")
        checks = []
        for c in rep.checks or []:
            checks.append(
                {
                    "id": getattr(c, "id", None) or getattr(c, "label", "?"),
                    "label": getattr(c, "label", "?"),
                    "ok": bool(getattr(c, "ok", False)),
                    "detail": str(getattr(c, "detail", "") or "")[:200],
                }
            )
        return {
            "ok": bool(rep.ok),
            "passed": int(rep.passed or 0),
            "total": int(rep.total or 8),
            "elapsed_sec": round(float(rep.elapsed_sec or 0), 2),
            "checks": checks,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:180]}


def _severity_rank(sev: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(sev, 3)


def _queue_item(
    *,
    source: str,
    name: str,
    detail: str,
    hint: str,
    severity: str = "medium",
    fix_kind: str = "manual",
    auto_fixable: bool = False,
) -> dict[str, Any]:
    return {
        "source": source,
        "name": name,
        "detail": detail[:400],
        "hint": hint[:400],
        "severity": severity,
        "fix_kind": fix_kind,
        "auto_fixable": bool(auto_fixable),
    }


def build_repair_queue(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []

    for row in analysis.get("self_scan_failures") or []:
        name = str(row.get("name") or "?")
        if name == "gemini_configured":
            continue
        queue.append(
            _queue_item(
                source="self_scan",
                name=name,
                detail=str(row.get("detail") or ""),
                hint=str(row.get("hint") or "Ortam veya kod düzeltmesi gerekebilir."),
                severity="high" if name in ("workspace_root", "desktop_server_entry") else "medium",
                fix_kind="env" if name.endswith("_available") or "path" in name else "code",
                auto_fixable=name not in (
                    "python_on_path",
                    "pytest_available",
                    "git_available",
                    "disk_free_gb",
                    "gemini_configured",
                ),
            )
        )

    for chk in (analysis.get("parity") or {}).get("checks") or []:
        if chk.get("ok"):
            continue
        label = str(chk.get("label") or chk.get("id") or "parity_check")
        queue.append(
            _queue_item(
                source="parity",
                name=label,
                detail=str(chk.get("detail") or ""),
                hint="Parity kontrolünü geçecek minimal kod düzeltmesi yap; davranışı bozma.",
                severity="high",
                fix_kind="code",
                auto_fixable=True,
            )
        )

    for it in (analysis.get("weakness") or {}).get("items") or []:
        eid = str(it.get("id") or "?")
        if eid == "E6":
            fix_kind = "manual"
            auto = False
        elif eid == "E7":
            fix_kind = "restart"
            auto = False
        else:
            fix_kind = "code"
            auto = eid in ("E1", "E3")
        queue.append(
            _queue_item(
                source="weakness",
                name=f"weakness_{eid}",
                detail=str(it.get("msg") or ""),
                hint={
                    "E7": "API'yi yeniden başlat: Ruzgar.ps1 -ForceRestart",
                    "E6": "parity full çalıştır",
                }.get(eid, "KPI sinyalini gideren hedefli düzeltme."),
                severity=str(it.get("severity") or "medium"),
                fix_kind=fix_kind,
                auto_fixable=auto,
            )
        )

    if (analysis.get("build") or {}).get("mismatch"):
        queue.append(
            _queue_item(
                source="build",
                name="build_mismatch",
                detail=(
                    f"server={analysis['build'].get('server_rev')} "
                    f"expected={analysis['build'].get('expected_rev')}"
                ),
                hint=str(analysis["build"].get("restart_hint") or "Ruzgar.ps1 -ForceRestart"),
                severity="high",
                fix_kind="restart",
                auto_fixable=False,
            )
        )

    for row in analysis.get("syntax") or []:
        if row.get("ok"):
            continue
        rel = str(row.get("path") or "?")
        queue.append(
            _queue_item(
                source="syntax",
                name=f"syntax_{rel.replace('/', '_')}",
                detail=str(row.get("detail") or ""),
                hint=f"Sözdizimi hatasını düzelt: {rel}",
                severity="high",
                fix_kind="code",
                auto_fixable=True,
            )
        )

    queue.sort(key=lambda x: (_severity_rank(str(x.get("severity"))), str(x.get("name"))))
    return queue


def _number_queue(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numbered: list[dict[str, Any]] = []
    for idx, row in enumerate(queue, start=1):
        numbered.append({**row, "id": idx})
    return numbered


def run_autonomous_system_analysis(
    workspace_root: str | Path | None,
    *,
    include_parity: bool = True,
) -> dict[str, Any]:
    """P11 — birleşik sistem analizi (varsayılan salt okuma)."""
    t0 = time.perf_counter()
    report: dict[str, Any] = {
        "ok": True,
        "version": FAZ96_VERSION,
        "generated_at": time.time(),
        "workspace_root": str(workspace_root or ""),
        "sections": {},
        "score": 100,
    }

    self_failures: list[dict[str, Any]] = []
    try:
        from ilim_assistant.motorlar.programlama_faz2 import run_programlama_self_scan

        scan = run_programlama_self_scan(workspace_root)
        report["sections"]["self_scan"] = {
            "ok": bool(scan.get("ok")),
            "fail_count": len(scan.get("numbered_failures") or []),
        }
        self_failures = list(scan.get("numbered_failures") or [])
        report["self_scan_failures"] = self_failures
        if not scan.get("ok"):
            report["score"] -= min(30, 8 * len(self_failures))
    except Exception as exc:
        report["sections"]["self_scan"] = {"ok": False, "error": str(exc)[:120]}

    try:
        from ilim_assistant.motorlar.programlama_faz82 import build_weakness_report

        wr = build_weakness_report(workspace_root)
        report["weakness"] = wr
        report["sections"]["weakness"] = {
            "score": wr.get("score"),
            "grade": wr.get("grade"),
            "items": len(wr.get("items") or []),
        }
        report["score"] = min(report["score"], int(wr.get("score") or 100))
    except Exception as exc:
        report["sections"]["weakness"] = {"ok": False, "error": str(exc)[:120]}

    try:
        from ilim_assistant.motorlar.programlama_faz60 import (
            build_mismatch_info,
            expected_build_rev,
        )

        exp = expected_build_rev()
        mi = build_mismatch_info(exp)
        report["build"] = mi
        report["sections"]["build"] = {"mismatch": bool(mi.get("mismatch"))}
        if mi.get("mismatch"):
            report["score"] -= 15
    except Exception as exc:
        report["sections"]["build"] = {"ok": False, "error": str(exc)[:120]}

    git = _gather_git_repo_summary(workspace_root)
    report["git"] = git
    report["sections"]["git"] = {
        "has_changes": bool(git.get("has_changes")),
        "changed_lines": int(git.get("changed_lines") or 0),
    }

    syntax = _syntax_spot_check(workspace_root)
    report["syntax"] = syntax
    bad_syntax = [x for x in syntax if not x.get("ok")]
    report["sections"]["syntax"] = {"fail_count": len(bad_syntax)}
    report["score"] -= 12 * len(bad_syntax)

    parity: dict[str, Any] = {"skipped": True}
    if include_parity:
        parity = _run_parity_quick(workspace_root)
        report["parity"] = parity
        if parity.get("skipped"):
            report["sections"]["parity"] = {"skipped": True}
        else:
            failed = sum(1 for c in parity.get("checks") or [] if not c.get("ok"))
            report["sections"]["parity"] = {
                "passed": parity.get("passed"),
                "total": parity.get("total"),
                "failed": failed,
                "elapsed_sec": parity.get("elapsed_sec"),
            }
            report["score"] -= min(35, 5 * failed)
    else:
        report["parity"] = parity

    report["score"] = max(0, min(100, int(report["score"])))
    report["grade"] = (
        "A" if report["score"] >= 85 else "B" if report["score"] >= 70 else "C" if report["score"] >= 50 else "D"
    )

    queue = build_repair_queue(report)
    numbered = _number_queue(queue)
    report["repair_queue"] = queue
    report["numbered_queue"] = numbered
    report["fixable_count"] = sum(1 for x in queue if x.get("auto_fixable"))
    report["ok"] = len(queue) == 0
    report["elapsed_sec"] = round(time.perf_counter() - t0, 2)

    _store_analysis_state(report)
    _persist_report(workspace_root, report)
    return report


def format_system_analysis_report(report: dict[str, Any]) -> str:
    score = int(report.get("score") or 0)
    grade = report.get("grade") or "?"
    lines = [
        f"Ümit abi, **P11 otonom sistem analizi (Faz 96)** — skor **{score}/100 ({grade})**",
        f"Süre: {report.get('elapsed_sec', '?')}s · Düzeltilebilir madde: **{report.get('fixable_count', 0)}**",
        "",
    ]

    sections = report.get("sections") or {}
    if sections.get("self_scan"):
        ss = sections["self_scan"]
        if ss.get("ok"):
            lines.append("**Öz-denetim:** temiz")
        else:
            lines.append(f"**Öz-denetim:** {ss.get('fail_count', '?')} uyarı")
    if sections.get("weakness"):
        w = sections["weakness"]
        lines.append(f"**Zayıflık KPI:** {w.get('score', '?')}/100 ({w.get('grade', '?')})")
    if sections.get("build", {}).get("mismatch"):
        lines.append("**Build:** uyumsuz — API yeniden başlatılmalı")
    if sections.get("syntax", {}).get("fail_count"):
        lines.append(f"**Sözdizimi:** {sections['syntax']['fail_count']} dosya hatalı")
    if sections.get("parity") and not sections["parity"].get("skipped"):
        p = sections["parity"]
        lines.append(f"**Parity quick:** {p.get('passed', '?')}/{p.get('total', '?')}")

    git = report.get("git") or {}
    if git.get("has_changes"):
        lines.append(f"**Git:** {git.get('changed_lines', '?')} değişik satır (repo)")

    numbered = report.get("numbered_queue") or []
    lines.append("")
    if not numbered:
        lines.append("Kritik madde yok — sistem sağlıklı görünüyor.")
    else:
        lines.append("**Numaralı onarım kuyruğu:**")
        for row in numbered[:12]:
            fix = " [otomatik]" if row.get("auto_fixable") else " [manuel]"
            lines.append(
                f"{row.get('id')}. [{row.get('severity')}] {row.get('name')}{fix}"
                + (f" — {str(row.get('detail') or '')[:80]}" if row.get("detail") else "")
            )
        lines.append("")
        lines.append(
            "Onarım: `hataları bul onar` veya `onayla 1 2` · "
            "Salt rapor: `sistem analizi`"
        )

    lines.append(f"\n({FAZ96_VERSION})")
    technical = "\n".join(lines)
    try:
        from ilim_assistant.motorlar.programlama_faz97 import (
            choose_report,
            format_sade_system_analysis,
            sade_rapor_enabled,
        )

        if sade_rapor_enabled():
            return choose_report(technical, format_sade_system_analysis(report))
    except Exception:
        pass
    return technical


def parse_p11_approved_items(message: str, state: dict[str, Any] | None) -> list[str] | None:
    if not wants_p11_fix_approval(message):
        return None
    if not state:
        return []
    all_names = [str(n.get("name", "")) for n in state.get("numbered_queue") or []]
    if not all_names:
        return []
    low = (message or "").lower()
    if any(k in low for k in ("hepsini onayla", "tümünü onayla", "tumunu onayla")):
        return list(all_names)

    picked: list[str] = []
    for n in all_names:
        if n in low or n.replace("_", " ") in low:
            picked.append(n)

    nums = [int(x) for x in re.findall(r"\b(\d+)\b", message or "") if x.isdigit()]
    numbered = state.get("numbered_queue") or []
    for num in nums:
        for row in numbered:
            if row.get("id") == num:
                name = str(row.get("name", ""))
                if name and name not in picked:
                    picked.append(name)

    if picked:
        return picked
    return list(all_names)


def _build_repair_directive(items: list[dict[str, Any]]) -> str:
    lines = [
        "[P11 OTONOM ONARIM — Faz 96 — Ümit abi onaylı]",
        "KURALLAR (kesin):",
        "- Yalnızca aşağıdaki maddeleri düzelt; başka dosyaya/refaktöre girme.",
        "- Minimal @@write patch; hassas dosyalara (.env, hafiza, merkezi_bellek, *.db) yazma.",
        "- Mevcut çalışan davranışı bozma; gereksiz stil değişikliği yapma.",
        "- Her patch sonrası pytest_run ile doğrula.",
        "- Emin değilsen o maddeyi atla ve nedenini kısaca yaz.",
        "",
        "MADDELER:",
    ]
    for row in items:
        lines.append(
            f"- {row.get('name')} [{row.get('source')}]: "
            f"{row.get('hint') or row.get('detail') or 'düzelt'}"
        )
    lines.append("[/P11 OTONOM ONARIM]")
    return "\n".join(lines)


def prepare_autonomous_repair_turn(
    message: str,
    workspace_root: str | Path | None = None,
) -> dict[str, Any] | None:
    """
    P11 onarım turu hazırlığı.
    Dönüş: instant | augmented_message + force_debug
    """
    global _force_p11_repair_turn
    if not _enabled():
        return None

    msg = (message or "").strip()
    full_cycle = wants_full_autonomous_cycle(msg)
    repair_start = wants_autonomous_repair_start(msg)
    p11_approval = wants_p11_fix_approval(msg)

    if not (full_cycle or repair_start or p11_approval):
        return None

    state = get_last_analysis_state()
    if p11_approval and state and (time.time() - float(state.get("at") or 0)) < 900:
        analysis = dict(state.get("data") or {})
        if not analysis.get("numbered_queue"):
            analysis = run_autonomous_system_analysis(workspace_root, include_parity=True)
    else:
        analysis = run_autonomous_system_analysis(workspace_root, include_parity=True)

    numbered = list(analysis.get("numbered_queue") or [])
    if not numbered:
        return {
            "instant": (
                format_system_analysis_report(analysis)
                + "\n\nTemiz — otomatik onarım gerekmiyor."
            )
        }

    if full_cycle or repair_start or p11_approval:
        approved_names = parse_p11_approved_items(msg, {"numbered_queue": numbered})
        if approved_names is None and (full_cycle or repair_start):
            approved_names = [
                str(x.get("name"))
                for x in numbered
                if x.get("auto_fixable")
            ][: _max_fix_items()]

        if not approved_names:
            return {
                "instant": (
                    format_system_analysis_report(analysis)
                    + "\n\nOtomatik onarılabilir madde yok. "
                    "Manuel maddeler için ipuçları raporda."
                )
            }

        selected = [x for x in numbered if str(x.get("name")) in approved_names]
        code_items = [x for x in selected if x.get("auto_fixable") and x.get("fix_kind") == "code"]
        manual_items = [x for x in selected if not x.get("auto_fixable") or x.get("fix_kind") != "code"]

        if not code_items:
            hints = "\n".join(
                f"- {x.get('name')}: {x.get('hint')}" for x in manual_items[:8]
            )
            return {
                "instant": (
                    format_system_analysis_report(analysis)
                    + "\n\nSeçilen maddeler manuel/ortam:\n"
                    + hints
                )
            }

        try:
            from ilim_assistant.motorlar.programlama_faz92 import assess_risk, risk_confirmation_text

            probe = " ".join(str(x.get("hint") or "") for x in code_items)
            risk = assess_risk(probe)
            if risk.get("requires_confirmation"):
                return {"instant": risk_confirmation_text(risk)}
        except Exception:
            pass

        directive = _build_repair_directive(code_items[: _max_fix_items()])
        augmented = (
            msg
            + "\n\n"
            + directive
            + "\n\n"
            + format_system_analysis_report(analysis)[:2400]
        )
        _force_p11_repair_turn = True
        return {
            "augmented_message": augmented,
            "force_debug": True,
            "items": [x.get("name") for x in code_items],
            "analysis": analysis,
        }

    return None


def run_post_repair_verification(
    workspace_root: str | Path | None,
    *,
    before: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Onarım sonrası hızlı doğrulama — parity quick + self-scan özeti."""
    after = run_autonomous_system_analysis(
        workspace_root,
        include_parity=os.environ.get("RUZGAR_P11_SKIP_PARITY", "0").strip().lower()
        not in ("1", "true", "yes"),
    )
    before_score = int((before or {}).get("score") or 0)
    after_score = int(after.get("score") or 0)
    before_q = len((before or {}).get("repair_queue") or [])
    after_q = len(after.get("repair_queue") or [])
    improved = after_score > before_score or after_q < before_q
    return {
        "ok": after.get("ok"),
        "improved": improved,
        "before_score": before_score,
        "after_score": after_score,
        "before_issues": before_q,
        "after_issues": after_q,
        "after": after,
        "version": FAZ96_VERSION,
    }


def format_verification_report(verify: dict[str, Any]) -> str:
    b = int(verify.get("before_score") or 0)
    a = int(verify.get("after_score") or 0)
    bi = int(verify.get("before_issues") or 0)
    ai = int(verify.get("after_issues") or 0)
    mark = "iyileşti" if verify.get("improved") else "değişmedi"
    technical = (
        f"P11 doğrulama: skor {b}→{a}, madde {bi}→{ai} ({mark}). "
        f"Kalan otomatik madde: {sum(1 for x in (verify.get('after') or {}).get('repair_queue') or [] if x.get('auto_fixable'))}."
    )
    try:
        from ilim_assistant.motorlar.programlama_faz97 import (
            choose_report,
            format_sade_verification,
            sade_rapor_enabled,
        )

        if sade_rapor_enabled():
            return choose_report(technical, format_sade_verification(verify))
    except Exception:
        pass
    return technical


def maybe_instant_faz96(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    if not wants_system_analysis(message):
        return None
    if wants_full_autonomous_cycle(message) or wants_autonomous_repair_start(message):
        return None
    report = run_autonomous_system_analysis(workspace_root, include_parity=True)
    return format_system_analysis_report(report)


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz96"] = faz96_enabled()
    try:
        path = _report_path(None)
        if path and path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            out["p11_v106"] = {
                "enabled": faz96_enabled(),
                "last_score": data.get("score"),
                "last_grade": data.get("grade"),
                "last_issues": len(data.get("repair_queue") or []),
                "last_at": data.get("generated_at"),
            }
    except Exception:
        out["p11_v106"] = {"enabled": faz96_enabled()}
    return out


def faz96_directive() -> str:
    return (
        "[Faz 96 — P11 otonom sistem analizi]\n"
        "Komut: `sistem analizi` · `hataları bul onar` · `onayla 1 2`\n"
        f"Kapat: RUZGAR_FAZ96=0 · {FAZ96_VERSION}\n"
    )
