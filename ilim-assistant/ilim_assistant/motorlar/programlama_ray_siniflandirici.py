"""
P2 — Niyet → ray sınıflayıcı (2026-10-23).

Greenfield → scaffold (Faz85/Faz6)
Dar health/version/pytest → faz85_fast
P1 pattern / dar patch → agent_boot (ajan + supervised)
Çok dosya → agent_multi
Mega → agent_mega

path_hint (UI/handoff uyumu):
  scaffold|faz85_fast → faz85_fast
  agent_boot → agent
  agent_multi → agent_multi
  agent_mega → agent_mega
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

RAY_CLASSIFIER_VERSION = "programlama-ray-p2-v1-2026-10-23"

RAY_SCAFFOLD = "scaffold"
RAY_FAZ85 = "faz85_fast"
RAY_AGENT_BOOT = "agent_boot"
RAY_AGENT_MULTI = "agent_multi"
RAY_AGENT_MEGA = "agent_mega"

_VALID_RAYS = (
    RAY_SCAFFOLD,
    RAY_FAZ85,
    RAY_AGENT_BOOT,
    RAY_AGENT_MULTI,
    RAY_AGENT_MEGA,
)

_SCAFFOLD_RE = re.compile(
    r"(?:yeni\s+proje|sifirdan|sıfırdan|api\s+yap|site\s+yap|uygulama\s+yap|"
    r"web\s*sitesi|fastapi\s+(?:olustur|oluştur|kur|scaffold)|"
    r"scaffold|iskelet\s+kur|proje\s+olustur|proje\s+oluştur)",
    re.I,
)

_SIMPLE_FAZ85_RE = re.compile(
    r"(?:health.*(?:version|status|ok|alan)|(?:version|status).*(?:health|endpoint)|"
    r"pytest\s*(?:gecir|geçir)|sadece\s*(?:dogrula|doğrula|verify))",
    re.I,
)

_BOOT_PATTERN_RE = re.compile(
    r"(?:\bimport\s*(?:duzelt|düzelt|fix|ekle)|eksik\s*import|ImportError|NameError|"
    r"(?:uptime|ready|env|build|revision|region)\s*(?:alan[ıi]?)?\s*(?:ekle|yaz|koy)|"
    r"(?:alan[ıi]?|field)\s*(?:ekle|yaz)|"
    r"/?ping|ping\s*(?:endpoint|route)|endpoint\s*ekle|route\s*ekle)",
    re.I,
)


@dataclass(frozen=True)
class RayDecision:
    ray: str
    path_hint: str
    reason: str
    use_faz85: bool
    use_supervised_boot: bool
    version: str = RAY_CLASSIFIER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _ascii_fold(text: str) -> str:
    try:
        from ilim_assistant.motorlar.programlama_faz85 import _ascii_fold as _af

        return _af(text or "")
    except Exception:
        return (text or "").lower()


def path_hint_for_ray(ray: str) -> str:
    if ray in (RAY_SCAFFOLD, RAY_FAZ85):
        return "faz85_fast"
    if ray == RAY_AGENT_MEGA:
        return "agent_mega"
    if ray == RAY_AGENT_MULTI:
        return "agent_multi"
    return "agent"


def classify_programlama_ray(goal: str, *, message: str = "") -> RayDecision:
    """Tek giriş: hedef (+ isteğe bağlı sohbet) → ray kararı."""
    raw = f"{message or ''} {goal or ''}".strip()
    if not raw:
        return RayDecision(
            ray=RAY_AGENT_BOOT,
            path_hint="agent",
            reason="bos_hedef",
            use_faz85=False,
            use_supervised_boot=True,
        )
    low = _ascii_fold(raw)

    # 1) Mega
    try:
        from ilim_assistant.motorlar.programlama_faz80 import wants_mega_refactor

        if wants_mega_refactor(raw):
            return RayDecision(
                ray=RAY_AGENT_MEGA,
                path_hint="agent_mega",
                reason="mega_refactor",
                use_faz85=False,
                use_supervised_boot=True,
            )
    except Exception:
        pass

    # 2) Çok dosya / multi
    try:
        from ilim_assistant.motorlar.programlama_faz56 import looks_like_multi_file_task

        if looks_like_multi_file_task(raw):
            return RayDecision(
                ray=RAY_AGENT_MULTI,
                path_hint="agent_multi",
                reason="multi_file",
                use_faz85=False,
                use_supervised_boot=True,
            )
    except Exception:
        pass
    try:
        from ilim_assistant.motorlar.programlama_faz85 import (
            _MULTI_PATH_RE,
            _AGENT_PATH_MARKERS,
        )

        if len(_MULTI_PATH_RE.findall(raw)) >= 2:
            return RayDecision(
                ray=RAY_AGENT_MULTI,
                path_hint="agent_multi",
                reason="two_plus_paths",
                use_faz85=False,
                use_supervised_boot=True,
            )
        # Ağır marker'lar (oauth, docker…) → multi/ajan; mega değilse multi
        heavy = (
            "refactor",
            "middleware",
            "oauth",
            "jwt",
            "database",
            "migrate",
            "docker",
            "kubernetes",
            "graphql",
            "websocket",
            "redis",
            "celery",
            "auth ekle",
        )
        if any(m in low for m in heavy):
            return RayDecision(
                ray=RAY_AGENT_MULTI,
                path_hint="agent_multi",
                reason="heavy_marker",
                use_faz85=False,
                use_supervised_boot=True,
            )
        # «N dosya» genel ajan işareti
        if any(
            m in low
            for m in _AGENT_PATH_MARKERS
            if m
            not in heavy
            and "dosya" in m
        ):
            return RayDecision(
                ray=RAY_AGENT_MULTI,
                path_hint="agent_multi",
                reason="dosya_marker",
                use_faz85=False,
                use_supervised_boot=True,
            )
    except Exception:
        pass

    # 3) Scaffold / greenfield
    if _SCAFFOLD_RE.search(low) or _SCAFFOLD_RE.search(raw):
        return RayDecision(
            ray=RAY_SCAFFOLD,
            path_hint="faz85_fast",
            reason="greenfield_scaffold",
            use_faz85=True,
            use_supervised_boot=False,
        )
    try:
        from ilim_assistant.motorlar.programlama_faz85 import _goal_wants_create

        if _goal_wants_create(raw):
            return RayDecision(
                ray=RAY_SCAFFOLD,
                path_hint="faz85_fast",
                reason="create_goal",
                use_faz85=True,
                use_supervised_boot=False,
            )
    except Exception:
        pass

    # 4) P1 supervised pattern niyetleri → agent_boot
    if _BOOT_PATTERN_RE.search(raw) or _BOOT_PATTERN_RE.search(low):
        return RayDecision(
            ray=RAY_AGENT_BOOT,
            path_hint="agent",
            reason="p1_pattern_intent",
            use_faz85=False,
            use_supervised_boot=True,
        )

    # 5) Basit Faz85
    if _SIMPLE_FAZ85_RE.search(low) or _SIMPLE_FAZ85_RE.search(raw):
        # Kısa pytest-only
        if "pytest" in low and len(low) < 80 and "health" not in low and "version" not in low:
            return RayDecision(
                ray=RAY_FAZ85,
                path_hint="faz85_fast",
                reason="pytest_short",
                use_faz85=True,
                use_supervised_boot=False,
            )
        if "health" in low or "version" in low or "status" in low:
            return RayDecision(
                ray=RAY_FAZ85,
                path_hint="faz85_fast",
                reason="health_or_version_fast",
                use_faz85=True,
                use_supervised_boot=False,
            )

    # Eski simple kural (yuzey_bridge uyumu)
    g = low
    simple = (
        ("health" in g and ("version" in g or "ok" in g or "duzelt" in g or "düzelt" in g))
        or ("pytest" in g and ("gecir" in g or "geçir" in g) and len(g) < 80)
        or ("yeni" in g and "api" in g and "health" in g)
    )
    if simple:
        return RayDecision(
            ray=RAY_FAZ85,
            path_hint="faz85_fast",
            reason="legacy_simple",
            use_faz85=True,
            use_supervised_boot=False,
        )

    # 6) Varsayılan — dar ajan + supervised
    return RayDecision(
        ray=RAY_AGENT_BOOT,
        path_hint="agent",
        reason="default_agent_boot",
        use_faz85=False,
        use_supervised_boot=True,
    )


def path_hint_for_goal(goal: str, *, message: str = "") -> str:
    """Yüzey köprüsü / 6c için tek satır path_hint."""
    return classify_programlama_ray(goal, message=message).path_hint
