# Created by Ümit & Gökçenur
"""
Programlama motoru — güvenli dosya okuma/yazma ve onaylı test/lint preset'leri.

Omurgalar:
  - ``local_tools.safe_read_file_under_root`` / ``safe_write_file_under_root``
  - ``approved_executor.run_preset`` (pytest_run, python_module_run, ruff_check)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ilim_assistant.approved_executor import run_preset
from ilim_assistant.local_tools import (
    safe_read_file_under_root,
    safe_write_file_under_root,
)

MIMAR_IMZA = "Ümit & Gökçenur"
PROJE_ADI = "RÜZGAR Programlama Motoru"

DevPresetKey = Literal["pytest_run", "python_module_run", "ruff_check"]
ALLOWED_DEV_PRESETS: frozenset[str] = frozenset(
    {"pytest_run", "python_module_run", "ruff_check"}
)

_WRITE_FENCE_RE = re.compile(
    r"@@write\s+(\S+)\s*\r?\n```(?:[\w+-]+)?\s*\r?\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class ReadReport:
    path: str
    content: str
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class WriteReport:
    path: str
    ok: bool
    detail: str = ""


@dataclass
class ExecReport:
    preset: str
    exit_code: int
    output: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


@dataclass
class ToolRunSummary:
    reads: list[ReadReport] = field(default_factory=list)
    writes: list[WriteReport] = field(default_factory=list)
    execs: list[ExecReport] = field(default_factory=list)

    @property
    def any_error(self) -> bool:
        if any(not r.ok for r in self.reads):
            return True
        if any(not w.ok for w in self.writes):
            return True
        if any(not e.ok for e in self.execs):
            return True
        return False


def repo_root(workspace_root: str | Path | None = None) -> Path | None:
    """Proje kökü: argüman → RUZGAR_EXEC_CWD → LOCAL_TOOLS_ROOT → ilim-assistant üstü."""
    raw = (
        str(workspace_root).strip()
        if workspace_root is not None
        else ""
    )
    if not raw:
        raw = (
            os.environ.get("RUZGAR_EXEC_CWD", "").strip()
            or os.environ.get("LOCAL_TOOLS_ROOT", "").strip()
        )
    if raw:
        p = Path(raw)
        if p.is_dir():
            return p.resolve()
    try:
        from ilim_assistant.ruzgar_hafiza_koprusu import ilim_assistant_root

        parent = ilim_assistant_root().parent
        if parent.is_dir():
            return parent.resolve()
    except Exception:
        pass
    return None


def infer_rel_paths(message: str, root: Path) -> list[str]:
    """@@ yolları ve mesajdaki göreli dosya adları."""
    from ilim_assistant.ana_motor_agent import infer_workspace_rel_paths

    return infer_workspace_rel_paths(message, root)


def _max_read_chars() -> int:
    try:
        return max(500, int(os.environ.get("LOCAL_TOOLS_FILE_MAX_CHARS", "6000")))
    except ValueError:
        return 6000


def _extract_write_jobs(message: str) -> list[tuple[str, str]]:
    """``@@write yol`` + hemen ardından fenced kod bloğu."""
    jobs: list[tuple[str, str]] = []
    for m in _WRITE_FENCE_RE.finditer(message or ""):
        rel = m.group(1).strip().replace("\\", "/").lstrip("/")
        body = m.group(2)
        if rel and body is not None:
            jobs.append((rel, body.rstrip("\n") + "\n"))
    return jobs


def _wants_pytest(message: str) -> bool:
    low = (message or "").lower()
    return any(
        x in low
        for x in (
            "pytest",
            "test et",
            "testleri çalıştır",
            "testleri calistir",
            "unit test",
            "traceback",
        )
    )


def _wants_lint(message: str) -> bool:
    low = (message or "").lower()
    return any(
        x in low
        for x in (
            "ruff",
            "flake8",
            "lint",
            "static analiz",
            "linter",
            "kod kalitesi",
        )
    )


def _wants_smoke_module(message: str) -> bool:
    low = (message or "").lower()
    return any(
        x in low
        for x in (
            "python -m",
            "smoke test",
            "modül çalıştır",
            "modul calistir",
        )
    )


def _wants_full_verify(message: str) -> bool:
    low = (message or "").lower()
    return any(
        x in low
        for x in (
            "tam doğrula",
            "tam dogrula",
            "hepsini test",
            "lint ve test",
            "test ve lint",
        )
    )


def wants_autonomous_code_debug(message: str) -> bool:
    """
    Faz 10.4 / Programlama Faz 1 — otonom hata ayıklama (çok adımlı LLM + pytest).

    Kapatmak: RUZGAR_CODE_DEBUG_AUTO=0
    Traceback metni: RUZGAR_CODE_DEBUG_ON_TRACEBACK=1 (varsayılan açık)
    """
    if os.environ.get("RUZGAR_CODE_DEBUG_AUTO", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    low = (message or "").lower()
    keys = (
        "otomatik debug",
        "otomatik hata ayıklama",
        "otomatik hata ayiklama",
        "debug döngüsü",
        "debug dongusu",
        "traceback'i düzelt",
        "tracebacki düzelt",
        "kendin düzelt",
        "pytest döngüsü",
        "pytest dongusu",
        "hata ayıkla",
        "hata ayikla",
        "hatayı düzelt",
        "hatayi duzelt",
        "kodu düzelt",
        "kodu duzelt",
        "testi geçir",
        "testi gecir",
        "pytest ile düzelt",
        "patch yaz ve test",
    )
    if any(k in low for k in keys):
        return True
    if os.environ.get("RUZGAR_CODE_DEBUG_ON_TRACEBACK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        if "traceback" in low and (
            "file \"" in low
            or 'file "' in (message or "")
            or "line " in low
            or "modulenotfounderror" in low
            or "assertionerror" in low
        ):
            return True
    return False


_SKIP_REPO_DIRS = frozenset(
    {
        ".git",
        ".cursor",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "hafiza",
        "knowledge",
        "dist",
        "build",
        ".pytest_cache",
        "video_indirilen",
    }
)

_REPO_TOP_DIRS = ("ilim-assistant", "ruzgar-desktop", "scripts")


def build_repo_map(
    workspace_root: str | Path | None = None,
    *,
    max_lines: int = 58,
) -> str:
    """Programlama modu için kısa proje haritası (LLM halüsinasyonunu azaltır)."""
    root = repo_root(workspace_root)
    if root is None:
        return ""
    lines: list[str] = [f"Kök dizin: {root}"]
    for top in _REPO_TOP_DIRS:
        if len(lines) >= max_lines:
            break
        tp = root / top
        if not tp.exists():
            continue
        if tp.is_file():
            lines.append(f"- {top}")
            continue
        lines.append(f"- {top}/")
        try:
            kids = sorted(tp.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            continue
        shown = 0
        for child in kids:
            if shown >= 14 or len(lines) >= max_lines:
                lines.append("  …")
                break
            name = child.name
            if name in _SKIP_REPO_DIRS or name.startswith("."):
                continue
            tag = "/" if child.is_dir() else ""
            lines.append(f"  · {name}{tag}")
            shown += 1
    lines.append(
        "Giriş: ilim-assistant/desktop_server.py, ilim-assistant/ilim_assistant/chat_core.py, "
        "ruzgar-desktop/app.js"
    )
    return "\n".join(lines)


def _bilge_programlama_directive() -> str:
    return (
        "[BİLGE PROGRAMLAMA — Ümit & Gökçenur]\n"
        "Akış: (1) kısa plan (2–4 madde) → (2) ilgili dosyaları oku → "
        "(3) `@@write yol` + kod bloğu ile patch → (4) pytest/ruff çıktısını yorumla.\n"
        "Uydurma dosya yolu yazma; üstteki haritada olmayan yolu önce sor veya @@ ile oku.\n"
        "Traceback varsa satır numarasına göre düzelt; başarısız testte assertion'ı hedefle.\n"
        "Kullanıcı istemedikçe kapsamı büyütme; her turda yalnızca gerekli değişiklik.\n"
    )


def is_code_agent_task_message(message: str, mode_norm: str = "programlama") -> bool:
    """görev: / gorev: — otonom ajan; Faz 7 anında rehber atlansın."""
    if mode_norm != "programlama":
        return False
    try:
        from ilim_assistant.motorlar.programlama_faz19 import normalize_agent_message
        from ilim_assistant.motorlar.programlama_faz14 import parse_code_agent_task

        return parse_code_agent_task(
            normalize_agent_message(message, mode_norm=mode_norm)
        ) is not None
    except Exception:
        return False


def is_programlama_reserved_command(message: str) -> bool:
    """Eğitim hafızası / genel sohbet bu komutları yutmasın."""
    if is_code_agent_task_message(message):
        return False
    try:
        from ilim_assistant.motorlar.programlama_faz4 import wants_security_scan

        if wants_security_scan(message):
            return True
    except Exception:
        pass
    if wants_self_scan(message):
        return True
    try:
        from ilim_assistant.motorlar.programlama_faz96 import (
            wants_autonomous_repair_start,
            wants_full_autonomous_cycle,
            wants_p11_fix_approval,
            wants_system_analysis,
        )

        if (
            wants_system_analysis(message)
            or wants_full_autonomous_cycle(message)
            or wants_autonomous_repair_start(message)
            or wants_p11_fix_approval(message)
        ):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz2 import wants_briefing

        if wants_briefing(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz2 import wants_scan_fix_approval

        if wants_scan_fix_approval(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz5 import (
            wants_project_clear,
            wants_project_summary,
            patch_project_from_message,
        )

        if (
            wants_project_summary(message)
            or wants_project_clear(message)
            or patch_project_from_message(message)
        ):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz6 import (
            parse_scaffold_command,
            wants_template_list,
        )

        if wants_template_list(message) or parse_scaffold_command(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz47 import wants_proje_uret

        if wants_proje_uret(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz7 import wants_file_help, wants_project_run

        if wants_file_help(message) or wants_project_run(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz8 import (
            wants_api_serve,
            wants_api_stop,
            wants_project_tree_focus,
        )

        if wants_api_serve(message) or wants_api_stop(message) or wants_project_tree_focus(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz10 import (
            wants_patch_apply,
            wants_patch_cancel,
            wants_patch_preview,
            wants_project_verify_cmd,
            wants_workspace_index,
        )

        if (
            wants_patch_preview(message)
            or wants_patch_apply(message)
            or wants_patch_cancel(message)
            or wants_workspace_index(message)
            or wants_project_verify_cmd(message)
        ):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz28 import (
            wants_git_branch_create,
            wants_git_branch_list,
        )

        if wants_git_branch_list(message) or wants_git_branch_create(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz29 import (
            wants_project_list,
            wants_project_switch,
        )

        if wants_project_list(message) or wants_project_switch(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz31 import (
            wants_pr_create,
            wants_pr_push,
            wants_pr_status,
        )

        if wants_pr_status(message) or wants_pr_push(message) or wants_pr_create(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz32 import (
            wants_task_save_pipeline,
            wants_workflow_summary,
        )

        if wants_workflow_summary(message) or wants_task_save_pipeline(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz101_report_read import (
            wants_clarification,
            wants_report_read,
        )

        if wants_report_read(message) or wants_clarification(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz63 import wants_live_kpi

        if wants_live_kpi(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz86 import wants_live_task_battery

        if wants_live_task_battery(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz65 import wants_best_of_n_agent

        if wants_best_of_n_agent(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz64 import wants_best_of_n

        if wants_best_of_n(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz22 import wants_symbol_command

        if wants_symbol_command(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz42 import (
            wants_find_references,
            wants_import_graph,
            wants_rename_symbol,
        )

        if (
            wants_find_references(message)
            or wants_rename_symbol(message)
            or wants_import_graph(message)
        ):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz13 import (
            wants_find_command,
            wants_project_scan_instant,
        )

        if wants_find_command(message) or wants_project_scan_instant(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz14 import (
            wants_code_agent_status,
            wants_code_agent_stop,
        )

        if wants_code_agent_stop(message) or wants_code_agent_status(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz19 import parse_task_aliases

        if parse_task_aliases(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz44 import (
            parse_at_refs,
            wants_context_map,
        )

        if wants_context_map(message) or parse_at_refs(message):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz43 import wants_terminal_v3

        if wants_terminal_v3(message):
            return True
    except Exception:
        try:
            from ilim_assistant.motorlar.programlama_faz15 import wants_terminal_command

            if wants_terminal_command(message):
                return True
        except Exception:
            pass
    try:
        from ilim_assistant.motorlar.programlama_faz16 import (
            wants_patch_accept,
            wants_patch_list,
            wants_patch_reject,
            wants_patch_rollback,
        )

        if (
            wants_patch_accept(message)
            or wants_patch_reject(message)
            or wants_patch_rollback(message)
            or wants_patch_list(message)
        ):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz17 import (
            wants_commit_apply,
            wants_commit_cancel,
            wants_commit_suggest,
            wants_git_diff,
            wants_git_status,
        )

        if (
            wants_git_status(message)
            or wants_git_diff(message)
            or wants_commit_suggest(message)
            or wants_commit_apply(message)
            or wants_commit_cancel(message)
        ):
            return True
    except Exception:
        pass
    low8 = (message or "").lower()
    if "api durum" in low8 or "sunucu durum" in low8:
        return True
    try:
        from ilim_assistant.ruzgar_owner_lock import is_owner_phrase

        if is_owner_phrase(message):
            return True
    except Exception:
        pass
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "otomatik debug",
            "pytest döngüsü",
            "pytest dongusu",
            "kendin düzelt",
        )
    )


def wants_self_scan(message: str) -> bool:
    low = (message or "").lower()
    return any(
        k in low
        for k in (
            "kendini tara",
            "kendini kontrol",
            "öz kontrol",
            "oz kontrol",
            "self-test",
            "self test",
            "selftest",
            "öz-denetim",
            "oz-denetim",
        )
    )


def format_self_scan_report(
    workspace_root: str | Path | None = None,
) -> str:
    """Faz 2 — genişletilmiş öz-denetim; onay bekler."""
    from ilim_assistant.motorlar.programlama_faz2 import format_self_scan_report as _faz2_report

    return _faz2_report(workspace_root)


def unpack_programlama_instant(
    result: str | dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any]]:
    """Anında yanıt: düz metin veya {text, focus_rel, ...} (Faz 8)."""
    if result is None:
        return None, {}
    if isinstance(result, dict):
        text = str(result.get("text") or "").strip() or None
        meta = {k: v for k, v in result.items() if k != "text"}
        return text, meta
    s = str(result).strip()
    return (s or None), {}


def maybe_programlama_instant_reply(
    message: str,
    mode_norm: str,
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
    editor_snippet: str | None = None,
) -> str | dict[str, Any] | None:
    """Programlama motoruna özel anında yanıtlar (LLM turu atlanır)."""
    if mode_norm != "programlama":
        return None
    try:
        from ilim_assistant.motorlar.programlama_faz10 import extract_user_intent_message
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        user_only = extract_user_intent_message(message)
        if looks_like_casual_social_chat(user_only or message):
            return None
    except Exception:
        pass
    parts: list[str] = []
    focus_meta: dict[str, Any] = {}
    try:
        from ilim_assistant.ruzgar_owner_lock import maybe_owner_instant_reply

        owner = maybe_owner_instant_reply(message, mode_norm)
        if owner:
            parts.append(owner)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz101_report_read import (
            maybe_instant_report_read,
        )

        rep101 = maybe_instant_report_read(message, workspace_root)
        if rep101:
            parts.append(rep101)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz2 import (
            build_startup_briefing,
            wants_briefing,
        )

        if wants_briefing(message):
            parts.append(build_startup_briefing(workspace_root).get("text", ""))
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz4 import (
            format_security_scan_report,
            wants_security_scan,
        )

        if wants_security_scan(message):
            parts.append(format_security_scan_report(workspace_root))
    except Exception:
        pass
    _skip_self_for_p11 = False
    try:
        from ilim_assistant.motorlar.programlama_faz96 import (
            maybe_instant_faz96,
            wants_system_analysis,
        )

        faz96_hit = maybe_instant_faz96(message, workspace_root)
        if faz96_hit:
            parts.append(faz96_hit)
        _skip_self_for_p11 = wants_system_analysis(message)
    except Exception:
        pass
    if wants_self_scan(message) and not _skip_self_for_p11:
        try:
            from ilim_assistant.ruzgar_egitim import clear_pending

            clear_pending()
        except Exception:
            pass
        parts.append(format_self_scan_report(workspace_root))
    try:
        from ilim_assistant.motorlar.programlama_faz5 import (
            format_project_summary_report,
            wants_project_clear,
            wants_project_summary,
            clear_session,
            maybe_apply_message_project_patch,
        )

        if wants_project_clear(message):
            clear_session(workspace_root)
            parts.append(
                "Proje oturum bağlamı temizlendi (.ruzgar/programlama_oturum.json)."
            )
        elif wants_project_summary(message):
            parts.append(format_project_summary_report(workspace_root))
            try:
                from ilim_assistant.motorlar.programlama_faz13 import (
                    build_project_summary_block,
                    format_scan_report,
                    resolve_scope_rel,
                    scan_project_files,
                )

                scope = resolve_scope_rel(
                    workspace_root, active_file=active_file, message=message
                )
                if scope:
                    scan = scan_project_files(workspace_root, scope)
                    if scan.get("ok"):
                        parts.append(format_scan_report(scan))
                    block = build_project_summary_block(
                        workspace_root, scope_rel=scope
                    ).strip()
                    if block:
                        parts.append(f"```\n{block}\n```")
            except Exception:
                pass
        elif maybe_apply_message_project_patch(message, workspace_root):
            parts.append(format_project_summary_report(workspace_root))
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz6 import (
            format_template_list_report,
            parse_scaffold_command,
            run_scaffold,
            wants_template_list,
        )

        if wants_template_list(message):
            parts.append(format_template_list_report())
        else:
            sc = parse_scaffold_command(message)
            if sc:
                tid, pname = sc
                result = run_scaffold(tid, pname, workspace_root)
                from ilim_assistant.motorlar.programlama_faz8 import (
                    apply_scaffold_focus,
                    enrich_scaffold_report,
                )

                fm = apply_scaffold_focus(workspace_root, result) if result.get("ok") else {}
                parts.append(enrich_scaffold_report(result, fm))
                if fm.get("focus_rel"):
                    focus_meta = fm
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz7 import (
            format_explain_run_report,
            format_run_report,
            resolve_target_rel,
            run_project_profile,
            wants_project_run,
        )

        if is_code_agent_task_message(message):
            pass
        elif wants_project_run(message):
            rel = resolve_target_rel(
                message,
                active_file=active_file,
                workspace_root=workspace_root,
            )
            if rel:
                parts.append(
                    format_run_report(
                        run_project_profile(workspace_root, rel, smoke_only=False)
                    )
                )
            else:
                parts.append(
                    "Ümit abi, `proje çalıştır` için atölyede bir dosya aç "
                    "veya `projects/...` yolunu yaz."
                )
        else:
            guide = format_explain_run_report(
                message,
                workspace_root,
                active_file=active_file,
            )
            if guide:
                parts.append(guide)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz17 import maybe_instant_faz17

        faz17_hit = maybe_instant_faz17(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz17_hit:
            parts.append(faz17_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz16 import maybe_instant_faz16

        faz16_hit = maybe_instant_faz16(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz16_hit:
            parts.append(faz16_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz44 import maybe_instant_faz44

        faz44_hit = maybe_instant_faz44(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz44_hit:
            parts.append(faz44_hit)
    except Exception:
        pass
    try:
        os.environ["RUZGAR_LAST_PROG_MSG"] = (message or "")[:4000]
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz78 import maybe_instant_faz78

        faz78_hit = maybe_instant_faz78(message)
        if faz78_hit:
            parts.append(faz78_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz82 import maybe_instant_faz82

        faz82_hit = maybe_instant_faz82(message, workspace_root)
        if faz82_hit:
            parts.append(faz82_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz91 import maybe_instant_faz91

        faz91_hit = maybe_instant_faz91(message, workspace_root)
        if faz91_hit:
            parts.append(faz91_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz89 import maybe_instant_faz89

        faz89_hit = maybe_instant_faz89(message, workspace_root)
        if faz89_hit:
            parts.append(faz89_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz88 import maybe_instant_faz88

        faz88_hit = maybe_instant_faz88(message, workspace_root)
        if faz88_hit:
            parts.append(faz88_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz86 import maybe_instant_faz86

        faz86_hit = maybe_instant_faz86(message, workspace_root)
        if faz86_hit:
            parts.append(faz86_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz83 import maybe_instant_faz83

        faz83_hit = maybe_instant_faz83(message, workspace_root)
        if faz83_hit:
            parts.append(faz83_hit)
    except Exception:
        pass
    _faz98_claimed = False
    try:
        from ilim_assistant.motorlar.programlama_faz98 import (
            maybe_instant_faz98,
            wants_umit_gate,
        )

        _faz98_claimed = wants_umit_gate(message)
        faz98_hit = maybe_instant_faz98(message, workspace_root)
        if faz98_hit:
            parts.append(faz98_hit)
    except Exception:
        pass
    if not _faz98_claimed:
        try:
            from ilim_assistant.motorlar.programlama_faz67 import maybe_instant_faz67

            faz67_hit = maybe_instant_faz67(
                message,
                workspace_root,
                active_file=active_file,
            )
            if faz67_hit:
                parts.append(faz67_hit)
        except Exception:
            pass
    try:
        from ilim_assistant.motorlar.programlama_faz43 import maybe_instant_faz43

        faz43_hit = maybe_instant_faz43(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz43_hit:
            parts.append(faz43_hit)
    except Exception:
        try:
            from ilim_assistant.motorlar.programlama_faz15 import maybe_instant_faz15

            faz15_hit = maybe_instant_faz15(
                message,
                workspace_root,
                active_file=active_file,
            )
            if faz15_hit:
                parts.append(faz15_hit)
        except Exception:
            pass
    try:
        from ilim_assistant.motorlar.programlama_faz63 import maybe_instant_faz63

        faz63_hit = maybe_instant_faz63(message, workspace_root)
        if faz63_hit:
            parts.append(faz63_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz66 import maybe_instant_faz66

        faz66_hit = maybe_instant_faz66(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz66_hit:
            parts.append(faz66_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz65 import maybe_instant_faz65

        faz65_hit = maybe_instant_faz65(message, workspace_root)
        if faz65_hit:
            parts.append(faz65_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz64 import maybe_instant_faz64

        faz64_hit = maybe_instant_faz64(message, workspace_root)
        if faz64_hit:
            parts.append(faz64_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz14 import maybe_instant_faz14

        faz14_hit = maybe_instant_faz14(message, workspace_root)
        if faz14_hit:
            parts.append(faz14_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz28 import maybe_instant_faz28

        faz28_hit = maybe_instant_faz28(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz28_hit:
            parts.append(faz28_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz37 import maybe_instant_faz37

        faz37_hit = maybe_instant_faz37(message, workspace_root)
        if faz37_hit:
            parts.append(faz37_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz36 import maybe_instant_faz36

        faz36_hit = maybe_instant_faz36(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz36_hit:
            parts.append(faz36_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz42 import maybe_instant_faz42

        faz42_hit = maybe_instant_faz42(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz42_hit:
            parts.append(faz42_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz34 import maybe_instant_faz34

        faz34_hit = maybe_instant_faz34(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz34_hit:
            parts.append(faz34_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz32 import maybe_instant_faz32

        faz32_hit = maybe_instant_faz32(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz32_hit:
            parts.append(faz32_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz31 import maybe_instant_faz31

        faz31_hit = maybe_instant_faz31(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz31_hit:
            parts.append(faz31_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz29 import maybe_instant_faz29

        faz29_hit = maybe_instant_faz29(message, workspace_root)
        if faz29_hit:
            if isinstance(faz29_hit, dict):
                t29 = str(faz29_hit.get("text") or "").strip()
                if t29:
                    parts.append(t29)
                for key in ("focus_rel", "project_rel", "expand_tree"):
                    if faz29_hit.get(key):
                        focus_meta[key] = faz29_hit[key]
            else:
                parts.append(str(faz29_hit))
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz22 import maybe_instant_faz22

        faz22_hit = maybe_instant_faz22(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz22_hit:
            parts.append(faz22_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz13 import maybe_instant_faz13

        faz13_hit = maybe_instant_faz13(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz13_hit:
            parts.append(faz13_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz10 import maybe_instant_faz10

        faz10_hit = maybe_instant_faz10(
            message,
            workspace_root,
            active_file=active_file,
        )
        if faz10_hit:
            parts.append(faz10_hit)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz8 import maybe_instant_api_command

        api_hit = maybe_instant_api_command(
            message,
            workspace_root,
            active_file=active_file,
        )
        if api_hit:
            api_text = str(api_hit.get("text") or "").strip()
            if api_text:
                parts.append(api_text)
            for key in ("focus_rel", "project_rel", "expand_tree"):
                if api_hit.get(key):
                    focus_meta[key] = api_hit[key]
    except Exception:
        pass
    _ = editor_snippet
    if parts:
        text = "\n\n".join(p for p in parts if p.strip())
        if focus_meta.get("focus_rel") or focus_meta.get("project_rel"):
            return {"text": text, **focus_meta}
        return text
    return None


def code_debug_max_retries() -> int:
    """Başarısız pytest sonrası en fazla kaç ek LLM turu (varsayılan 2, tavan 5)."""
    try:
        v = int(os.environ.get("RUZGAR_CODE_DEBUG_LOOPS", "2"))
    except ValueError:
        v = 2
    return max(0, min(v, 5))


def apply_assistant_reply_tools(
    reply_body: str,
    workspace_root: str | Path | None = None,
    legacy_workspace: str | Path | None = None,
    *,
    run_pytest: bool = True,
) -> tuple[ToolRunSummary, ExecReport | None]:
    """
    Faz 10.4 / 10.6 — LLM cevabındaki @@write bloklarını uygular; istenirse pytest ile doğrular.

    Geriye uyum: eski hatalı çağrı ``(round_body, round_body, workspace)`` — üçüncü argüman kök.

    Dönüş: (özet, pytest raporu veya None).
    """
    root = workspace_root
    if legacy_workspace is not None:
        root = legacy_workspace
    elif root is not None and str(root) == str(reply_body or "").strip():
        root = None
    summary, _ = run_tools_for_message((reply_body or "").strip(), root)
    pytest_rep: ExecReport | None = None
    tools = ProgramlamaAraclari(root)
    if run_pytest and tools.root is not None:
        pytest_rep = tools.run_dev_preset("pytest_run")
        summary.execs.append(pytest_rep)
    try:
        from ilim_assistant.motorlar.programlama_faz5 import record_tool_summary

        write_paths = [w.path for w in summary.writes if w.ok and w.path]
        record_tool_summary(
            root,
            writes=write_paths,
            pytest_ok=pytest_rep.ok if pytest_rep else None,
            pytest_exit=pytest_rep.exit_code if pytest_rep else None,
        )
    except Exception:
        pass
    return summary, pytest_rep


class ProgramlamaAraclari:
    """Programlama motoru araç seti — okuma, yazma, onaylı exec."""

    def __init__(self, workspace_root: str | Path | None = None) -> None:
        self._root = repo_root(workspace_root)

    @property
    def root(self) -> Path | None:
        return self._root

    def read(self, rel_path: str, max_chars: int | None = None) -> ReadReport:
        if self._root is None:
            return ReadReport(
                path=rel_path,
                content="",
                error="Proje kökü bulunamadı (LOCAL_TOOLS_ROOT / RUZGAR_EXEC_CWD).",
            )
        cap = max_chars if max_chars is not None else _max_read_chars()
        body, err = safe_read_file_under_root(self._root, rel_path, cap)
        return ReadReport(path=rel_path, content=body, error=err)

    def write(self, rel_path: str, content: str) -> WriteReport:
        if self._root is None:
            return WriteReport(
                path=rel_path,
                ok=False,
                detail="Proje kökü bulunamadı.",
            )
        try:
            from ilim_assistant.motorlar.programlama_faz3 import programlama_write_allowed
            from ilim_assistant.motorlar.programlama_faz4 import validate_write_content

            try:
                from ilim_assistant.motorlar.programlama_faz78 import augment_write_policy

                allowed, reason = augment_write_policy(
                    self._root, rel_path, os.environ.get("RUZGAR_LAST_PROG_MSG", "")
                )
            except Exception:
                allowed, reason = programlama_write_allowed(self._root, rel_path)
            if not allowed:
                detail = reason
                try:
                    from ilim_assistant.motorlar.programlama_faz102_e1_live import (
                        format_scope_early_rejection,
                    )

                    if "Faz 78" in (reason or "") or "kapsam" in (reason or "").lower():
                        detail = format_scope_early_rejection(reason)[:800]
                except Exception:
                    pass
                return WriteReport(path=rel_path, ok=False, detail=detail)
            ok_content, creason = validate_write_content(content)
            if not ok_content:
                return WriteReport(path=rel_path, ok=False, detail=creason)
        except Exception:
            pass
        ok = safe_write_file_under_root(self._root, rel_path, content)
        if ok:
            return WriteReport(path=rel_path, ok=True, detail="Yazıldı (.bak yedek alındı).")
        return WriteReport(path=rel_path, ok=False, detail="Yazma reddedildi veya hata.")

    def run_dev_preset(self, preset: DevPresetKey | str) -> ExecReport:
        key = str(preset).strip()
        if key not in ALLOWED_DEV_PRESETS:
            return ExecReport(
                preset=key,
                exit_code=-1,
                output=f"İzin verilmeyen preset: {key}. İzinli: {', '.join(sorted(ALLOWED_DEV_PRESETS))}",
            )
        code, out = run_preset(key)
        return ExecReport(preset=key, exit_code=code, output=out)

    def verify_pipeline(self, *, lint: bool = True, pytest: bool = True, smoke: bool = False) -> list[ExecReport]:
        reports: list[ExecReport] = []
        if lint:
            reports.append(self.run_dev_preset("ruff_check"))
        if smoke:
            reports.append(self.run_dev_preset("python_module_run"))
        if pytest:
            reports.append(self.run_dev_preset("pytest_run"))
        return reports


def run_tools_for_message(
    message: str,
    workspace_root: str | Path | None = None,
    *,
    run_presets: bool = True,
) -> tuple[ToolRunSummary, str]:
    """
    Mesaja göre okuma / @@write / test-lint preset'lerini çalıştırır.
    Dönüş: (özet, LLM bağlam bloğu).
    """
    tools = ProgramlamaAraclari(workspace_root)
    summary = ToolRunSummary()
    blocks: list[str] = []

    if tools.root is None:
        return summary, (
            "[PROGRAMLAMA MOTORU — araçlar]\n"
            "Proje kökü yok; okuma/yazma/test atlandı. "
            "Electron workspace_root veya LOCAL_TOOLS_ROOT ayarlayın.\n"
        )

    read_paths: list[str] = list(infer_rel_paths(message, tools.root))
    try:
        from ilim_assistant.motorlar.programlama_faz10 import expand_message_paths

        for rel in expand_message_paths(message, workspace_root):
            if rel not in read_paths:
                read_paths.append(rel)
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz13 import expand_find_paths

        for rel in expand_find_paths(message, workspace_root):
            if rel not in read_paths:
                read_paths.append(rel)
    except Exception:
        pass
    for rel in read_paths:
        rep = tools.read(rel)
        summary.reads.append(rep)
        if rep.ok:
            blocks.append(f"=== Okuma: {rel} ===\n{rep.content}")
        else:
            blocks.append(f"=== Okuma: {rel} ===\n[HATA] {rep.error}")

    for rel, body in _extract_write_jobs(message):
        wrep = tools.write(rel, body)
        summary.writes.append(wrep)
        if wrep.ok:
            blocks.append(f"=== Yazma: {rel} ===\n{wrep.detail}")
            reread = tools.read(rel)
            summary.reads.append(reread)
            if reread.ok:
                blocks.append(f"=== Yazma sonrası doğrulama okuması: {rel} ===\n{reread.content[:2000]}")
        else:
            blocks.append(f"=== Yazma: {rel} ===\n[HATA] {wrep.detail}")

    if run_presets:
        if _wants_full_verify(message):
            summary.execs.extend(tools.verify_pipeline(lint=True, pytest=True, smoke=False))
        else:
            if _wants_lint(message):
                summary.execs.append(tools.run_dev_preset("ruff_check"))
            if _wants_pytest(message):
                summary.execs.append(tools.run_dev_preset("pytest_run"))
            if _wants_smoke_module(message):
                summary.execs.append(tools.run_dev_preset("python_module_run"))

    try:
        from ilim_assistant.motorlar.programlama_faz15 import (
            parse_terminal_preset,
            run_terminal_preset,
        )

        pid = parse_terminal_preset(message)
        if pid:
            tres = run_terminal_preset(workspace_root, pid, message=message)
            if tres.get("error") and not tres.get("output"):
                blocks.append(f"=== Terminal [{pid}] ===\n[HATA] {tres.get('error')}")
            else:
                code = int(tres.get("exit_code") or 1)
                status = "OK" if code == 0 else "HATA"
                scope = tres.get("scope_rel") or "?"
                blocks.append(
                    f"=== Terminal [{tres.get('label') or pid}] @ {scope} "
                    f"[{status} exit={code}] ===\n{str(tres.get('output') or '')}"
                )
    except Exception:
        pass

    for ex in summary.execs:
        status = "OK" if ex.ok else "HATA"
        blocks.append(
            f"=== Çalıştırma: {ex.preset} [{status} exit={ex.exit_code}] ===\n{ex.output}"
        )

    if not blocks:
        return summary, ""

    directive = (
        "\n[TALİMAT — PROGRAMLAMA ARAÇLARI — Ümit & Gökçenur]\n"
        "Üstteki okuma/yazma/terminal çıktıları gerçek sistem verisidir. "
        "Traceback veya lint satırlarını yorumla; gerekirse patch öner. "
        "Dosya yazımı `@@write yol` + kod bloğu ile veya API `write_file` ile yapılır; "
        "her yazımda `.bak` yedeği alınır.\n"
    )
    body = "\n\n".join(blocks)
    return summary, f"[PROGRAMLAMA MOTORU — araç çıktısı]\n{body}{directive}"


def read_file(
    rel_path: str,
    workspace_root: str | Path | None = None,
    max_chars: int | None = None,
) -> ReadReport:
    return ProgramlamaAraclari(workspace_root).read(rel_path, max_chars)


def write_file(
    rel_path: str,
    content: str,
    workspace_root: str | Path | None = None,
) -> WriteReport:
    return ProgramlamaAraclari(workspace_root).write(rel_path, content)


def run_dev_preset(
    preset: DevPresetKey,
    workspace_root: str | Path | None = None,
) -> ExecReport:
    return ProgramlamaAraclari(workspace_root).run_dev_preset(preset)


def build_motor_context(
    message: str,
    *,
    workspace_root: str | Path | None = None,
    run_presets: bool = False,
    active_file: str | None = None,
    editor_snippet: str | None = None,
) -> str:
    """Programlama modu LLM bağlamı: talimat + araç çıktıları (okuma/yazma/test).

    `run_presets=False` (varsayılan): tur hazırlığında pytest/ruff çalıştırma — ağır süreç
    yalnızca otonom debug döngüsünde (`apply_assistant_reply_tools`) yapılır.
    """
    try:
        from ilim_assistant.motorlar.programlama_faz21 import (
            build_light_programming_context,
            light_context_enabled,
        )

        if light_context_enabled():
            return build_light_programming_context(
                message,
                workspace_root=workspace_root,
                active_file=active_file,
                editor_snippet=editor_snippet,
                include_tools=True,
            )
    except Exception:
        pass

    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    _, tools_block = run_tools_for_message(
        prompt, workspace_root, run_presets=run_presets
    )

    base = dinamit_heartbeat() + _bilge_programlama_directive()
    try:
        from ilim_assistant.motorlar.programlama_faz2 import compact_self_knowledge

        base += "\n" + compact_self_knowledge() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz4 import write_guard_directive

        base += write_guard_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz5 import (
            format_session_context_block,
            usta_coding_directive,
        )

        base += usta_coding_directive() + "\n"
        sess_block = format_session_context_block(workspace_root).strip()
        if sess_block:
            base += sess_block + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz6 import scaffold_directive

        base += scaffold_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz7 import run_directive

        base += run_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz8 import focus_directive

        base += focus_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz11 import orchestra_directive

        base += orchestra_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz10 import (
            build_workspace_index,
            faz10_directive,
            resolve_scope_rel,
        )

        base += faz10_directive() + "\n"
        scope = resolve_scope_rel(workspace_root)
        idx = build_workspace_index(workspace_root, scope_rel=scope).strip()
        if idx:
            base += f"\n[WORKSPACE İNDEKS — Faz 10]\n{idx}\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz13 import (
            build_project_summary_block,
            faz13_directive,
            resolve_scope_rel as resolve_scope_faz13,
        )

        base += faz13_directive() + "\n"
        scope13 = resolve_scope_faz13(workspace_root, message=prompt)
        summary13 = build_project_summary_block(
            workspace_root, scope_rel=scope13
        ).strip()
        if summary13:
            base += f"\n{summary13}\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz14 import faz14_directive

        base += faz14_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz15 import faz15_directive

        base += faz15_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz16 import faz16_directive

        base += faz16_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz17 import faz17_directive

        base += faz17_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz18 import faz18_directive

        base += faz18_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz19 import faz19_directive

        base += faz19_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz20 import faz20_tool_directive

        base += faz20_tool_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz22 import faz22_directive

        base += faz22_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz23 import faz23_directive

        base += faz23_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz24 import faz24_directive

        base += faz24_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz25 import faz25_directive

        base += faz25_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz26 import faz26_directive

        base += faz26_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz27 import faz27_directive

        base += faz27_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz28 import faz28_directive

        base += faz28_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz29 import faz29_directive

        base += faz29_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz30 import faz30_directive

        base += faz30_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz31 import faz31_directive

        base += faz31_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz32 import faz32_directive

        base += faz32_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz33 import faz33_directive

        base += faz33_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz34 import faz34_directive

        base += faz34_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz35 import faz35_directive

        base += faz35_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz36 import faz36_directive

        base += faz36_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz37 import faz37_directive

        base += faz37_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz38 import faz38_directive

        base += faz38_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz39 import faz39_directive

        base += faz39_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz40 import faz40_directive

        base += faz40_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz41 import faz41_directive

        base += faz41_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz42 import faz42_directive

        base += faz42_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz43 import faz43_directive

        base += faz43_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz44 import faz44_directive

        base += faz44_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz45 import faz45_directive

        base += faz45_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz46 import faz46_directive

        base += faz46_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz47 import faz47_directive

        base += faz47_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz50 import faz50_directive

        base += faz50_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz51 import faz51_directive

        base += faz51_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz52 import faz52_directive

        base += faz52_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz53 import faz53_directive

        base += faz53_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz54 import faz54_directive

        base += faz54_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz55 import faz55_directive

        base += faz55_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz56 import faz56_directive

        base += faz56_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz57 import faz57_directive

        base += faz57_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz58 import faz58_directive

        base += faz58_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz60 import faz60_directive

        base += faz60_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz61 import faz61_directive

        base += faz61_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz62 import faz62_directive

        base += faz62_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz63 import faz63_directive

        base += faz63_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz64 import faz64_directive

        base += faz64_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz65 import faz65_directive

        base += faz65_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz66 import faz66_directive

        base += faz66_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz67 import faz67_directive

        base += faz67_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz98 import faz98_directive

        base += faz98_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz68 import faz68_directive

        base += faz68_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz69 import faz69_directive

        base += faz69_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz70 import faz70_directive

        base += faz70_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz78 import (
            core_scope_directive,
            faz78_directive,
        )

        base += faz78_directive() + "\n"
        cs = core_scope_directive(prompt)
        if cs:
            base += cs + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz79 import (
            faz79_directive,
            format_handoff_context_block,
        )

        base += faz79_directive() + "\n"
        h79 = format_handoff_context_block(
            prompt, workspace_root, active_file=active_file
        )
        if h79:
            base += f"\n[HANDOFF v3]\n{h79}\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz84 import faz84_directive

        base += faz84_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz80 import (
            faz80_directive,
            mega_refactor_directive,
        )

        base += faz80_directive() + "\n"
        mr = mega_refactor_directive(prompt)
        if mr:
            base += mr + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz81 import faz81_directive

        base += faz81_directive() + "\n"
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz48 import faz48_directive

        base += faz48_directive() + "\n"
    except Exception:
        pass
    try:
        if os.environ.get("RUZGAR_PROG_REPO_MAP", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        ):
            rmap = build_repo_map(workspace_root).strip()
            if rmap:
                base += f"\n[PROJE HARİTASI]\n{rmap}\n"
    except Exception:
        pass
    base += (
        f"\n[PROGRAMLAMA MOTORU — {MIMAR_IMZA}]\n"
        "Bu modda cevaplar teknik, doğru ve adım adım uygulanabilir olsun. "
        "Güvenli okuma/yazma (`local_tools`) ve onaylı test preset'leri "
        "(pytest_run, python_module_run, ruff_check) etkindir.\n"
        f"Kullanici mesaji: {prompt}\n"
    )
    if wants_autonomous_code_debug(prompt):
        base += (
            "\n[OTONOM DEBUG]\n"
            "Kullanıcı otonom düzeltme istedi; cevabında @@write ile patch ver, "
            "sunucu pytest döngüsünü çalıştıracak.\n"
        )
    if tools_block.strip():
        base = base.rstrip() + "\n\n" + tools_block.strip() + "\n"
    return base
