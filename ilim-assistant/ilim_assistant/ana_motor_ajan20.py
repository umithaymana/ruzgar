# Created by Ümit & Gökçenur
"""Ana Motor Faz X — Ajan 2.0 (çok tur + patch doğrulama + çok dosya staging)."""

from __future__ import annotations

import os
import py_compile
from pathlib import Path
from typing import Any

FAZ_X_VERSION = "ana-motor-ajan20-x1-2026-06-10"

_SENSITIVE_FRAGMENTS = (
    ".env",
    "hafiza",
    "ruzgar_genel_hafiza",
    ".db",
    "sağlık",
    "saglik",
    "credentials",
    "secret",
)


def agent_v2_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_AGENT_V2", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def agent_verify_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_AGENT_VERIFY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def agent_stage_multi_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_AGENT_STAGE_MULTI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def effective_max_agent_turns() -> int:
    """Faz X: varsayılan 5 tur, üst sınır 8 (v2 açıkken)."""
    if not agent_v2_enabled():
        try:
            return max(1, min(int(os.environ.get("RUZGAR_ANA_AGENT_MAX_TURNS", "3")), 6))
        except ValueError:
            return 3
    try:
        raw = int(os.environ.get("RUZGAR_ANA_AGENT_MAX_TURNS", "5"))
    except ValueError:
        raw = 5
    return max(1, min(raw, 8))


def _repo_root(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        return repo_root(workspace_root)
    except Exception:
        raw = (workspace_root or os.environ.get("LOCAL_TOOLS_ROOT", "") or "").strip()
        if raw:
            p = Path(raw)
            return p.resolve() if p.is_dir() else None
    return None


def should_stage_agent_patches(paths: list[str]) -> bool:
    """Çok dosya veya hassas yol → onay kartı (otomatik yazım yok)."""
    if not agent_v2_enabled() or not agent_stage_multi_enabled():
        return False
    clean = [str(p or "").replace("\\", "/").lower() for p in paths if p]
    if not clean:
        return False
    if len(clean) >= 2:
        return True
    for p in clean:
        if any(frag in p for frag in _SENSITIVE_FRAGMENTS):
            return True
    return False


def run_agent_v2_verify(
    applied_paths: list[str],
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
) -> dict[str, Any]:
    """Hafif doğrulama: py_compile + isteğe bağlı pytest."""
    if not agent_verify_enabled():
        return {"ok": True, "skipped": True, "reason": "agent_verify_disabled"}

    root = _repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace_root yok"}

    steps: list[dict[str, Any]] = []
    py_paths = [p for p in applied_paths if str(p).lower().endswith(".py")]
    compile_ok = True
    for rel in py_paths[:12]:
        full = root / str(rel).replace("/", os.sep)
        if not full.is_file():
            steps.append({"step": "py_compile", "path": rel, "ok": False, "error": "dosya yok"})
            compile_ok = False
            continue
        try:
            py_compile.compile(str(full), doraise=True)
            steps.append({"step": "py_compile", "path": rel, "ok": True})
        except py_compile.PyCompileError as exc:
            compile_ok = False
            steps.append(
                {
                    "step": "py_compile",
                    "path": rel,
                    "ok": False,
                    "error": str(exc)[:400],
                }
            )

    run_pytest = os.environ.get("RUZGAR_ANA_AGENT_VERIFY_PYTEST", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if not run_pytest:
        for rel in applied_paths:
            low = str(rel).replace("\\", "/").lower()
            if "/tests/" in low or low.startswith("tests/") or "test_" in low:
                run_pytest = True
                break

    pytest_verify: dict[str, Any] = {}
    if run_pytest and compile_ok:
        try:
            from ilim_assistant.motorlar.programlama_faz10 import run_project_verify

            scope = scope_rel or (applied_paths[0] if applied_paths else "")
            if scope:
                pytest_verify = run_project_verify(workspace_root, scope)
                steps.append(
                    {
                        "step": "pytest_scope",
                        "scope": scope,
                        "ok": bool(pytest_verify.get("ok", True)),
                        "exit_code": (
                            (pytest_verify.get("steps") or [{}])[0].get("exit_code")
                            if pytest_verify.get("steps")
                            else None
                        ),
                    }
                )
        except Exception as exc:
            pytest_verify = {"ok": False, "error": str(exc)[:200]}
            compile_ok = False

    ok = compile_ok and (not pytest_verify or pytest_verify.get("ok", True))
    report_lines = ["Ümit abi, **Ajan 2.0 doğrulama**:", ""]
    for st in steps:
        mark = "✓" if st.get("ok") else "✗"
        detail = st.get("path") or st.get("scope") or st.get("step")
        err = st.get("error")
        report_lines.append(f"{mark} {st.get('step')}: {detail}" + (f" — {err}" if err else ""))
    if pytest_verify.get("report"):
        report_lines.extend(["", str(pytest_verify["report"])[:2000]])

    return {
        "ok": ok,
        "steps": steps,
        "pytest": pytest_verify,
        "report": "\n".join(report_lines),
        "version": FAZ_X_VERSION,
    }


def merge_verify_into_patch_meta(patch_meta: dict[str, Any], v2_verify: dict[str, Any]) -> dict[str, Any]:
    if not v2_verify or v2_verify.get("skipped"):
        return patch_meta
    out = dict(patch_meta)
    out["verify_v2"] = v2_verify
    base = dict(out.get("verify") or {})
    combined_ok = bool(base.get("ok", True)) and bool(v2_verify.get("ok", True))
    reports = [str(base.get("report") or "").strip(), str(v2_verify.get("report") or "").strip()]
    merged_report = "\n\n".join(r for r in reports if r)
    out["verify"] = {**base, "ok": combined_ok, "report": merged_report}
    if not combined_ok and not out.get("errors"):
        out["errors"] = ["Ajan 2.0 doğrulama başarısız."]
    footer = str(out.get("footer") or "")
    if v2_verify.get("report") and str(v2_verify["report"]) not in footer:
        out["footer"] = footer + "\n\n" + str(v2_verify["report"])[:2000]
    return out


def process_agent_loop_patches(
    reply_body: str,
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    message: str = "",
) -> dict[str, Any]:
    """Ajan döngüsü tur sonu — staging + yazım + Faz X doğrulama."""
    try:
        from ilim_assistant.motorlar.programlama_faz10 import extract_write_jobs

        jobs = extract_write_jobs(reply_body)
    except Exception:
        jobs = []

    paths = [j[0] for j in jobs] if jobs else []

    if should_stage_agent_patches(paths):
        try:
            from ilim_assistant.ana_motor_patch_bridge import process_turn_patches

            staged = process_turn_patches(
                reply_body,
                workspace_root,
                scope_rel=scope_rel,
                delegated_from_genel=True,
                message=message,
            )
            if staged.get("action") == "staged":
                staged["agent_v2_staged"] = True
                return staged
        except Exception:
            pass

    try:
        from ilim_assistant.motorlar.programlama_faz10 import process_assistant_reply_patches

        meta = process_assistant_reply_patches(
            reply_body,
            workspace_root,
            scope_rel=scope_rel,
        )
    except Exception as exc:
        return {"action": "error", "errors": [str(exc)[:200]]}

    applied = list(meta.get("applied") or [])
    if applied and agent_verify_enabled():
        v2 = run_agent_v2_verify(applied, workspace_root, scope_rel=scope_rel)
        meta = merge_verify_into_patch_meta(meta, v2)
    meta["agent_v2"] = agent_v2_enabled()
    return meta


def get_agent_loop_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": FAZ_X_VERSION,
        "agent_v2": agent_v2_enabled(),
        "agent_verify": agent_verify_enabled(),
        "agent_stage_multi": agent_stage_multi_enabled(),
        "max_turns": effective_max_agent_turns(),
        "legacy_max_cap": 6,
        "v2_max_cap": 8,
    }


def faz_x_agent_directive_extra() -> str:
    if not agent_v2_enabled():
        return ""
    return (
        "[ANA MOTOR AJAN 2.0 — Faz X]\n"
        f"En fazla {effective_max_agent_turns()} tur; patch sonrası py_compile doğrulama.\n"
        "Çok dosya veya hassas yol → onay kartı (otomatik yazım yok).\n"
        "Doğrulama kırmızıysa yalnızca düzeltme patch'i üret.\n"
    )
