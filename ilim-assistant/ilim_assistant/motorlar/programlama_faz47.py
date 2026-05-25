# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 47: Bağımsız proje üretici.

Cursor olmadan: şablon → scaffold → offline bootstrap → (isteğe bağlı) ajan → pytest.

Komut örnekleri:
  proje üret: fastapi_api benim-shop health version pytest
  proje uret react_vite panelim login sayfasi ve build
  sıfırdan fastapi api yap benim-api test geçir
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

FAZ47_VERSION = "programlama-faz47-v1-2026-05-25"

_TEMPLATE_HINTS: list[tuple[str, str]] = [
    (r"\b(fastapi|fast\s*api|api\s+servis)\b", "fastapi_api"),
    (r"\b(react|vite|spa|frontend)\b", "react_vite"),
    (r"\b(expo|mobil|mobile|react\s*native)\b", "mobile_expo"),
    (r"\b(static|site|vitrin|landing)\b", "static_site"),
    (r"\b(cli|komut\s*satir|script)\b", "cli_python"),
]

_CUSTOM_FEATURE_RE = re.compile(
    r"(?:crud|login|auth|jwt|database|db|sqlite|postgres|redis|"
    r"websocket|upload|admin|dashboard|sayfa|page|form|ui\s+)",
    re.I,
)


@dataclass
class ProjeUretSpec:
    template_id: str
    project_name: str
    goal: str
    require_verify_pass: bool = True
    source: str = "faz47"


@dataclass
class ProjeUretReport:
    ok: bool
    template_id: str = ""
    project_name: str = ""
    scope_rel: str = ""
    scaffold_ok: bool = False
    offline_bootstrap_ok: bool = False
    verify_ok: bool = False
    agent_required: bool = True
    ready_without_agent: bool = False
    elapsed_sec: float = 0.0
    detail: str = ""
    goal: str = ""
    warnings: list[str] = field(default_factory=list)
    version: str = FAZ47_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "template_id": self.template_id,
            "project_name": self.project_name,
            "scope_rel": self.scope_rel,
            "scaffold_ok": self.scaffold_ok,
            "offline_bootstrap_ok": self.offline_bootstrap_ok,
            "verify_ok": self.verify_ok,
            "agent_required": self.agent_required,
            "ready_without_agent": self.ready_without_agent,
            "elapsed_sec": round(self.elapsed_sec, 2),
            "detail": self.detail,
            "goal": self.goal,
            "warnings": self.warnings,
            "version": self.version,
        }


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ47", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def proje_uret_enabled() -> bool:
    return _enabled()


def offline_bootstrap_enabled() -> bool:
    return os.environ.get("RUZGAR_PROJE_URET_OFFLINE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _projects_base() -> str:
    return (
        os.environ.get("RUZGAR_SCAFFOLD_BASE", "projects").strip().replace("\\", "/").strip("/")
        or "projects"
    )


def infer_template_from_text(text: str) -> str:
    raw = _ascii_fold(text)
    for pat, tid in _TEMPLATE_HINTS:
        if re.search(pat, raw, re.I):
            return tid
    return "fastapi_api"


def _extract_project_slug(text: str) -> str | None:
    """İlk uygun proje adı tokenı."""
    for w in re.findall(r"[\w][\w.\-]{1,46}", text or ""):
        wl = w.lower()
        if wl in (
            "fastapi",
            "api",
            "react",
            "vite",
            "expo",
            "mobil",
            "mobile",
            "static",
            "site",
            "cli",
            "python",
            "proje",
            "uret",
            "üret",
            "olustur",
            "oluştur",
            "yap",
            "sifirdan",
            "sıfırdan",
            "health",
            "version",
            "pytest",
            "test",
            "gecir",
            "geçir",
            "projects",
        ):
            continue
        if re.match(r"^[\w][\w.\-]*$", w) and len(w) >= 2:
            return w.strip().strip("/")
    return None


def _goal_from_remainder(text: str, slug: str, template_id: str) -> str:
    raw = (text or "").strip()
    low = _ascii_fold(raw)
    slug_l = _ascii_fold(slug)
    for token in (slug, slug_l, template_id, "fastapi_api", "fastapi"):
        if token and low.startswith(_ascii_fold(token)):
            raw = raw[len(token) :].lstrip(" :-\t,.")
            low = _ascii_fold(raw)
    for prefix in (
        "proje uret",
        "proje üret",
        "sifirdan",
        "sıfırdan",
        "bagimsiz proje",
        "bağımsız proje",
        "uygulama olustur",
        "uygulama oluştur",
        "api yap",
        "yap",
    ):
        if low.startswith(prefix):
            raw = raw[len(prefix) :].lstrip(" :-\t,.")
            low = _ascii_fold(raw)
    if not raw or len(raw) < 3:
        return (
            "health endpoint version alanı ekle ve pytest geçir "
            "(Cursor bağımsız tamamlama)"
        )
    return raw


def parse_proje_uret_command(message: str) -> ProjeUretSpec | None:
    """`proje üret:` ve doğal «sıfırdan … yap» cümleleri."""
    if not _enabled():
        return None
    raw = (message or "").strip()
    if len(raw) < 10:
        return None

    explicit = re.search(
        r"(?:proje\s+üret|proje\s+uret|bağımsız\s+proje|bagimsiz\s+proje)\s*:?\s*"
        r"(\S+)\s+(\S+)(?:\s+(.+))?$",
        raw,
        re.I | re.S,
    )
    if explicit:
        from ilim_assistant.motorlar.programlama_faz6 import _TEMPLATE_ALIASES

        tid = _TEMPLATE_ALIASES.get(
            explicit.group(1).strip().lower(),
            explicit.group(1).strip().lower(),
        )
        name = explicit.group(2).strip().strip('"').strip("'")
        goal = (explicit.group(3) or "").strip()
        if tid and name:
            return ProjeUretSpec(
                template_id=tid,
                project_name=name,
                goal=_goal_from_remainder(goal or raw, name, tid),
            )

    natural = re.search(
        r"(?:sıfırdan|sifirdan|yeni)\s+(.+?)\s+(?:yap|oluştur|olustur|üret|uret)\s+"
        r"([\w.\-]+)\s*(.*)$",
        raw,
        re.I | re.S,
    )
    if natural:
        tid = infer_template_from_text(natural.group(1) + " " + raw)
        name = natural.group(2).strip()
        goal = natural.group(3).strip() or natural.group(1).strip()
        return ProjeUretSpec(
            template_id=tid,
            project_name=name,
            goal=_goal_from_remainder(goal, name, tid),
        )

    if re.search(
        r"(?:proje\s+üret|proje\s+uret|bağımsız\s+proje|bagimsiz\s+proje)\b",
        raw,
        re.I,
    ):
        slug = _extract_project_slug(raw)
        if slug:
            tid = infer_template_from_text(raw)
            return ProjeUretSpec(
                template_id=tid,
                project_name=slug,
                goal=_goal_from_remainder(raw, slug, tid),
            )
    return None


def wants_proje_uret(message: str) -> bool:
    return parse_proje_uret_command(message) is not None


def _goal_is_minimal_post_scaffold(goal: str) -> bool:
    """Özel özellik yok — offline bootstrap + pytest yeterli."""
    if _CUSTOM_FEATURE_RE.search(goal or ""):
        return False
    low = _ascii_fold(goal or "")
    if not low:
        return True
    tokens = [t for t in re.split(r"[\s,;.]+", low) if t]
    allowed = {
        "health",
        "version",
        "pytest",
        "test",
        "testleri",
        "gecir",
        "geçir",
        "api",
        "endpoint",
        "ekle",
        "ve",
        "ile",
        "cursor",
        "bagimsiz",
        "bağımsız",
        "tamamlama",
        "alan",
        "alani",
        "field",
        "pass",
        "gecer",
        "geçer",
    }
    return all(t in allowed or t.startswith("test") for t in tokens)


def run_offline_bootstrap(
    workspace_root: str | Path | None,
    spec: ProjeUretSpec,
) -> tuple[bool, str]:
    """LLM olmadan FastAPI health+version + pytest iskeleti."""
    if not offline_bootstrap_enabled():
        return False, "offline kapalı"
    if spec.template_id != "fastapi_api":
        return False, f"offline yalnızca fastapi_api ({spec.template_id})"

    scope = f"{_projects_base()}/{spec.project_name}"
    try:
        from ilim_assistant.motorlar.programlama_faz25 import _health_patch_for_scope
        from ilim_assistant.motorlar.programlama_motoru import apply_assistant_reply_tools
        from ilim_assistant.motorlar.programlama_faz23 import enter_task_mode, exit_task_mode
        from ilim_assistant.motorlar.programlama_faz14 import ensure_pytest_bootstrap

        enter_task_mode()
        try:
            patch = _health_patch_for_scope(scope, spec.project_name)
            summ, _ = apply_assistant_reply_tools(
                patch, workspace_root, run_pytest=False
            )
            writes = len([w for w in summ.writes if w.ok])
            ensure_pytest_bootstrap(
                workspace_root, scope, goal=spec.goal or "pytest"
            )
            return writes > 0, f"writes={writes}"
        finally:
            exit_task_mode()
    except Exception as exc:
        return False, str(exc)[:120]


def _set_active_project(workspace_root: str | Path | None, slug: str) -> None:
    try:
        from ilim_assistant.motorlar.programlama_faz5 import load_session, save_session

        sess = load_session(workspace_root)
        sess["active_project"] = slug
        proj = sess.get("project") if isinstance(sess.get("project"), dict) else {}
        proj["name"] = slug
        sess["project"] = proj
        save_session(workspace_root, sess)
    except Exception:
        pass


def run_proje_uret_prepare(
    workspace_root: str | Path | None,
    spec: ProjeUretSpec,
) -> ProjeUretReport:
    """Scaffold + odak + offline bootstrap + verify (ajan öncesi)."""
    t0 = time.monotonic()
    rep = ProjeUretReport(
        ok=False,
        template_id=spec.template_id,
        project_name=spec.project_name,
        goal=spec.goal,
    )
    rep.scope_rel = f"{_projects_base()}/{spec.project_name}"

    try:
        from ilim_assistant.motorlar.programlama_faz6 import run_scaffold

        sc = run_scaffold(
            spec.template_id,
            spec.project_name,
            workspace_root,
            force=False,
        )
        rep.scaffold_ok = bool(sc.get("ok"))
        if not rep.scaffold_ok:
            rep.detail = str(sc.get("error") or "scaffold başarısız")[:200]
            rep.elapsed_sec = time.monotonic() - t0
            return rep

        from ilim_assistant.motorlar.programlama_faz8 import apply_scaffold_focus

        apply_scaffold_focus(workspace_root, sc)
        _set_active_project(workspace_root, spec.project_name)

        ob_ok, ob_detail = run_offline_bootstrap(workspace_root, spec)
        rep.offline_bootstrap_ok = ob_ok
        if not ob_ok:
            rep.warnings.append(f"offline: {ob_detail}")

        from ilim_assistant.motorlar.programlama_faz14 import run_project_verify

        verify = run_project_verify(
            workspace_root, rep.scope_rel, goal=spec.goal
        )
        rep.verify_ok = bool(verify and verify.ok)

        minimal = _goal_is_minimal_post_scaffold(spec.goal)
        rep.ready_without_agent = rep.verify_ok and minimal
        rep.agent_required = not rep.ready_without_agent

        rep.ok = rep.scaffold_ok and (rep.ready_without_agent or rep.agent_required)
        parts = [
            f"şablon `{spec.template_id}`",
            f"proje `{rep.scope_rel}`",
        ]
        if rep.offline_bootstrap_ok:
            parts.append("offline bootstrap OK")
        if rep.verify_ok:
            parts.append("pytest OK")
        if rep.ready_without_agent:
            parts.append("ajan gerekmedi")
        elif rep.agent_required:
            parts.append("ajan turu gerekli")
        rep.detail = " · ".join(parts)
        rep.elapsed_sec = time.monotonic() - t0
        return rep
    except Exception as exc:
        rep.detail = str(exc)[:200]
        rep.elapsed_sec = time.monotonic() - t0
        return rep


def format_proje_uret_report(rep: ProjeUretReport) -> str:
    icon = "✓" if rep.ok and (rep.ready_without_agent or rep.verify_ok) else "…"
    lines = [
        f"Ümit abi, **bağımsız proje üretimi** (Faz 47) {icon}",
        "",
        f"Şablon: `{rep.template_id}` · Proje: `{rep.scope_rel}`",
        f"Hedef: {rep.goal}",
        "",
        f"Scaffold: {'OK' if rep.scaffold_ok else '—'}",
        f"Offline bootstrap: {'OK' if rep.offline_bootstrap_ok else '—'}",
        f"Doğrulama (pytest): {'OK' if rep.verify_ok else 'kırmızı / bekliyor'}",
        f"Süre (hazırlık): {rep.elapsed_sec:.1f}s",
        "",
    ]
    if rep.ready_without_agent:
        lines.append(
            "**Proje Cursor olmadan hazır.** `proje çalıştır` veya atölyeden dosyaları açabilirsin."
        )
    elif rep.agent_required:
        lines.append(
            "Özel hedef için **kod ajanı** devreye alınıyor (yazım + test döngüsü)…"
        )
    if rep.warnings:
        lines.append("")
        lines.append("Notlar: " + "; ".join(rep.warnings[:4]))
    lines.append(f"\n({FAZ47_VERSION})")
    return "\n".join(lines)


def build_agent_message_for_spec(spec: ProjeUretSpec) -> str:
    return f"görev: {spec.project_name} {spec.goal}"


def should_run_proje_uret_pipeline(
    message: str,
    mode_norm: str = "",
    *,
    workspace_root: str | Path | None = None,
    active_file: str | Path | None = None,
) -> bool:
    del workspace_root, active_file  # açık proje olsa da yeni scaffold üretir
    if not _enabled() or mode_norm != "programlama":
        return False
    return parse_proje_uret_command(message) is not None


def iter_proje_uret_events(
    *,
    message: str,
    req: Any,
    system: str,
    user_payload: str,
    model: str,
    prior: list,
    mode_norm: str,
    coding: bool,
    turn_plan: Any | None,
    hits: list,
    new_wake: bool,
    orch: dict[str, Any] | None,
    delegated_from_genel: bool = False,
) -> Iterator[dict[str, Any]]:
    """Scaffold+hazırlık; gerekirse birleşik ajana devreder."""
    spec = parse_proje_uret_command(message)
    if spec is None:
        yield {"type": "error", "text": "Proje üret komutu çözülemedi."}
        return

    yield {
        "type": "status",
        "text": (
            f"Bağımsız proje üretimi (Faz 47) — `{spec.template_id}` → "
            f"`{spec.project_name}`"
        ),
    }
    yield {
        "type": "meta",
        "proje_uret": {
            "template_id": spec.template_id,
            "project_name": spec.project_name,
            "version": FAZ47_VERSION,
        },
    }

    prep = run_proje_uret_prepare(req.workspace_root, spec)
    yield {"type": "token", "text": format_proje_uret_report(prep) + "\n\n"}

    if prep.ready_without_agent:
        final = (
            f"\n\n**Tamamlandı** — `{prep.scope_rel}` pytest yeşil. "
            "Cursor veya başka IDE gerekmez.\n"
        )
        yield {
            "type": "done",
            "full_reply": format_proje_uret_report(prep) + final,
            "proje_uret": prep.to_dict(),
        }
        return

    if not prep.scaffold_ok:
        yield {
            "type": "done",
            "full_reply": format_proje_uret_report(prep),
            "proje_uret": prep.to_dict(),
        }
        return

    agent_msg = build_agent_message_for_spec(spec)
    yield {
        "type": "status",
        "text": "Faz 47 → kod ajanı (yazım + doğrulama döngüsü)…",
    }

    os.environ.setdefault("RUZGAR_FAZ10_AUTO_PATCH", "1")
    os.environ.setdefault("RUZGAR_AGENT_AUTO_APPLY", "1")
    try:
        from ilim_assistant.motorlar.programlama_faz14 import load_agent_state, save_agent_state

        save_agent_state(
            req.workspace_root,
            {
                **load_agent_state(req.workspace_root),
                "proje_uret": True,
                "require_verify_pass": spec.require_verify_pass,
                "scope_rel": prep.scope_rel,
                "goal": spec.goal,
            },
        )
    except Exception:
        pass

    try:
        from ilim_assistant.motorlar.programlama_faz20 import (
            iter_unified_programming_agent_events,
        )

        for ev in iter_unified_programming_agent_events(
            message=agent_msg,
            req=req,
            system=system,
            user_payload=user_payload,
            model=model,
            prior=prior,
            mode_norm=mode_norm,
            coding=coding,
            turn_plan=turn_plan,
            hits=hits,
            new_wake=new_wake,
            orch=orch,
            delegated_from_genel=delegated_from_genel,
        ):
            if ev.get("type") == "done":
                ev = dict(ev)
                body = str(ev.get("full_reply") or "")
                ev["full_reply"] = (
                    format_proje_uret_report(prep).rstrip()
                    + "\n\n---\n\n**Ajan tamamlama**\n\n"
                    + body
                )
                ev["proje_uret"] = prep.to_dict()
            yield ev
    except Exception as exc:
        yield {
            "type": "error",
            "text": f"Proje üret ajan hatası: {str(exc)[:300]}",
        }


def faz47_directive() -> str:
    return (
        "[BAĞIMSIZ PROJE ÜRET — Faz 47]\n"
        "Yeni uygulama (Cursor gerekmez):\n"
        "  proje üret: fastapi_api benim-api health version pytest\n"
        "  proje üret: react_vite panelim login ve build\n"
        "  sıfırdan fastapi api yap benim-shop test geçir\n"
        "Zincir: şablon → scaffold → offline patch → pytest → (gerekirse) ajan.\n"
        "Kapat: RUZGAR_FAZ47=0\n"
    )


def maybe_instant_faz47(
    message: str,
    workspace_root: str | Path | None,
) -> str | None:
    """Yalnızca yardım / liste; tam üretim stream'de."""
    if not wants_proje_uret(message):
        return None
    spec = parse_proje_uret_command(message)
    if spec is None:
        return None
    return (
        "Ümit abi, proje üretimi başlatılıyor (Faz 47). "
        f"Şablon `{spec.template_id}`, proje `{spec.project_name}` — "
        "birkaç saniye içinde scaffold + test + gerekirse ajan turu çalışacak.\n\n"
        f"({FAZ47_VERSION})"
    )
