# Created by Ümit & Gökçenur
"""
Ana Motor — Faz 94: routing tutarlılığı KPI (offline ölçüm).

Hedef: doğal cümle → doğru motor / delege ≥ %90 (vizyon KPI).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

FAZ94_VERSION = "ana-motor-routing-kpi-faz94-v1"
KPI_TARGET_PCT = 90.0


@dataclass
class RoutingCase:
    label: str
    message: str
    mode_norm: str = "genel"
    motor_flags: dict[str, bool] = field(default_factory=dict)
    expect: Any = None
    checker: str = "intent"  # intent | delegate | hub | plan | natural


@dataclass
class RoutingKpiResult:
    version: str = FAZ94_VERSION
    total: int = 0
    passed: int = 0
    failed: list[str] = field(default_factory=list)
    pass_rate_pct: float = 0.0
    meets_target: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate_pct": round(self.pass_rate_pct, 1),
            "target_pct": KPI_TARGET_PCT,
            "meets_target": self.meets_target,
        }


def _routing_cases() -> list[RoutingCase]:
    return [
        RoutingCase(
            "intent_code",
            "bu dosyada pytest ekle ve geçir",
            expect="code",
            checker="intent",
        ),
        RoutingCase(
            "intent_ilim",
            "Osmanlı'da Lale Devri nedir açıkla",
            expect="ilim",
            checker="intent",
        ),
        RoutingCase(
            "intent_general",
            "bugün çok yoruldum biraz sohbet edelim",
            expect="general",
            checker="intent",
        ),
        RoutingCase(
            "delegate_prog",
            "ruzgar-desktop/index.html dosyasında buton ekle",
            expect=True,
            checker="delegate",
        ),
        RoutingCase(
            "delegate_no_casual",
            "selam nasılsın",
            expect=False,
            checker="delegate",
        ),
        RoutingCase(
            "hub_video",
            "bu videoyu indir https://www.youtube.com/watch?v=abc",
            motor_flags={"video": True},
            expect="video",
            checker="hub",
        ),
        RoutingCase(
            "hub_programlama",
            "pytest geçir projede",
            motor_flags={"programlama": True},
            expect="programlama",
            checker="hub",
        ),
        RoutingCase(
            "plan_gundelik",
            "selam nasılsın",
            expect="gundelik",
            checker="plan",
        ),
        RoutingCase(
            "plan_bilgi",
            "Python decorator nedir",
            expect="bilgi",
            checker="plan",
        ),
        RoutingCase(
            "natural_sohbet",
            "senin gibi cevap vermeli hadi başlayalım",
            expect=True,
            checker="natural",
        ),
        RoutingCase(
            "agent_loop_intent",
            "@@ilim-assistant/README.md dosyasına not ekle",
            expect=True,
            checker="agent_loop",
        ),
        RoutingCase(
            "agent_loop_no",
            "Kuran'da sabır ayeti nedir",
            expect=False,
            checker="agent_loop",
        ),
    ]


def _run_checker(case: RoutingCase) -> tuple[bool, str]:
    msg = case.message
    mode = case.mode_norm
    flags = case.motor_flags

    if case.checker == "intent":
        from ilim_assistant.ana_motor_faz59 import classify_turn_intent

        got = classify_turn_intent(msg, mode_norm=mode, motor_flags=flags).get("intent")
        ok = got == case.expect
        return ok, f"intent={got}"

    if case.checker == "delegate":
        from ilim_assistant.motorlar.programlama_faz10 import should_delegate_to_programlama

        got = should_delegate_to_programlama(msg, mode, motor_flags=flags)
        ok = bool(got) == bool(case.expect)
        return ok, f"delegate={got}"

    if case.checker == "hub":
        from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target

        tgt, _ = resolve_hub_target(msg, flags)
        ok = tgt == case.expect
        return ok, f"hub={tgt}"

    if case.checker == "plan":
        from ilim_assistant.ana_motor_plan import plan_question

        p = plan_question(msg, mode, flags)
        ok = p.primary == case.expect
        return ok, f"plan={p.primary}"

    if case.checker == "natural":
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import is_natural_conversation_turn

        got = is_natural_conversation_turn(msg, mode, None)
        ok = bool(got) == bool(case.expect)
        return ok, f"natural={got}"

    if case.checker == "agent_loop":
        from ilim_assistant.ana_motor_agent_loop import should_run_ana_motor_agent_loop
        from ilim_assistant.ana_motor_plan import plan_question

        plan = plan_question(msg, mode, flags)
        got = should_run_ana_motor_agent_loop(msg, mode, plan)
        ok = bool(got) == bool(case.expect)
        return ok, f"agent_loop={got}"

    return False, "unknown checker"


def collect_routing_kpi(
    *,
    cases: list[RoutingCase] | None = None,
    on_pass: Callable[[str], None] | None = None,
    on_fail: Callable[[str, str], None] | None = None,
) -> RoutingKpiResult:
    res = RoutingKpiResult()
    batch = cases or _routing_cases()
    res.total = len(batch)
    for case in batch:
        try:
            ok, detail = _run_checker(case)
        except Exception as exc:
            ok, detail = False, str(exc)[:120]
        if ok:
            res.passed += 1
            if on_pass:
                on_pass(f"{case.label} ({detail})")
        else:
            res.failed.append(f"{case.label}: beklenen {case.expect!r} — {detail}")
            if on_fail:
                on_fail(case.label, detail)
    if res.total:
        res.pass_rate_pct = 100.0 * res.passed / res.total
    res.meets_target = res.pass_rate_pct >= KPI_TARGET_PCT
    return res
