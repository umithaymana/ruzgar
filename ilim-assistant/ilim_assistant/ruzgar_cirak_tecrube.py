# Created by Ümit & Gökçenur
"""
Çırak teknik tecrübe defteri — yalnız doğrulanmış, kısa, öğretici kurallar.

F1: jsonl yaz/oku + dedup + limit
F2: yeşil çırak bitişinde dar şablon ders
F3: tur başı 3–5 ders enjeksiyonu

Kapat: RUZGAR_CIRAK_TECRUBE=0
Kişisel sohbet belleği burada YOK.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

CIRAK_TECRUBE_VERSION = "cirak-tecrube-v1-2026-11-18"
_FILE = "cirak_tecrube.jsonl"
_MAX_ACTIVE = 80
_MAX_INJECT = 5
_RULE_MAX = 160
_SKEL_MAX = 400
_ANTI_MAX = 120

# Kişisel / zehir anahtar — yazımda red
_POISON_RE = re.compile(
    r"\b(ailem|severim|akrab|dostum|karım|eşim|çocuğum|kimim|"
    r"hatırla\s+beni|kişisel\s+hayat)\b",
    re.I,
)

# Plan §5 tohumları (B dalgası doğrulanmış)
_SEED: tuple[dict[str, Any], ...] = (
    {
        "kind": "SPEC",
        "rule": "Görevde açık .py ve tests/test_*.py yolları yaz; util.normalize yetmez.",
        "skeleton": "görev: projects/x cirak — foo.py …; tests/test_foo.py …",
        "tags": ["spec", "path", "py"],
    },
    {
        "kind": "WRITE",
        "rule": "Çırak turunda önce @@write; salt grep/read ile bitmiş sayma.",
        "skeleton": "@@write projects/x/foo.py\n```python\ndef foo():\n    ...\n```",
        "tags": ["write", "gate"],
    },
    {
        "kind": "LAYOUT",
        "rule": "Üretim kodu scope kökünde; testler tests/ altında; paket ise __init__ export.",
        "skeleton": "x/foo.py + x/tests/test_foo.py · paket/__init__.py export",
        "tags": ["layout", "tests", "paket"],
    },
    {
        "kind": "API",
        "rule": "Hedefteki def adını uydurma; generator istenmişse yield kullan.",
        "skeleton": "def filtre_satirlar(...): yield ...",
        "tags": ["api", "def", "generator"],
    },
    {
        "kind": "TEST",
        "rule": "Yeşil = zorunlu dosyalar diskte + hedefli pytest (yanlış yoldaki yeşil sayılmaz).",
        "skeleton": "pytest -q tests/test_foo.py",
        "tags": ["test", "pytest"],
    },
    {
        "kind": "MULTI",
        "rule": "Çok-modülde util + iş dosyasını ayır; normalize tek yerde.",
        "skeleton": "util.py normalize · servis.py / app.py iş",
        "tags": ["multi", "util"],
    },
    {
        "kind": "ANTI",
        "rule": "Salt keşif turu veya idle ajan = yazım yok; görev bitmedi.",
        "anti": "grep-only / idle → yeşil sayma",
        "tags": ["anti", "idle", "write"],
    },
)


def tecrube_enabled() -> bool:
    return os.environ.get("RUZGAR_CIRAK_TECRUBE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _repo_root(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        return repo_root(workspace_root)
    except Exception:
        if workspace_root:
            return Path(workspace_root)
        return None


def _store_path(workspace_root: str | Path | None) -> Path | None:
    root = _repo_root(workspace_root)
    if root is None:
        return None
    return root / ".ruzgar" / _FILE


def _norm_rule(rule: str) -> str:
    return re.sub(r"\s+", " ", (rule or "").strip().lower())[:_RULE_MAX]


def _rule_key(kind: str, rule: str) -> str:
    raw = f"{(kind or '').upper()}|{_norm_rule(rule)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _is_poison(text: str) -> bool:
    return bool(_POISON_RE.search(text or ""))


def load_lessons(workspace_root: str | Path | None) -> list[dict[str, Any]]:
    path = _store_path(workspace_root)
    if path is None or not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict) and row.get("rule"):
                out.append(row)
    except OSError:
        return []
    return out


def _rewrite_all(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else "")
    path.write_text(body, encoding="utf-8")


def _trim(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(rows) <= _MAX_ACTIVE:
        return rows
    # yüksek hits + yeni kalsın
    ranked = sorted(
        rows,
        key=lambda r: (int(r.get("hits") or 1), float(r.get("created_ts") or 0)),
        reverse=True,
    )
    keep = ranked[:_MAX_ACTIVE]
    keep_ids = {r.get("id") for r in keep}
    return [r for r in rows if r.get("id") in keep_ids]


def upsert_lesson(
    workspace_root: str | Path | None,
    *,
    kind: str,
    rule: str,
    skeleton: str = "",
    anti: str | None = None,
    tags: list[str] | None = None,
    evidence: str = "green_cirak",
    scope_sample: str = "",
) -> dict[str, Any]:
    """Ders ekle veya aynı kuralda hits++. Zehir/şüpheli evidence red."""
    if not tecrube_enabled():
        return {"ok": False, "skipped": True, "reason": "disabled"}
    path = _store_path(workspace_root)
    if path is None:
        return {"ok": False, "error": "path"}
    kind_u = (kind or "SPEC").strip().upper()[:12]
    rule_s = (rule or "").strip()[:_RULE_MAX]
    if not rule_s:
        return {"ok": False, "error": "empty_rule"}
    if _is_poison(rule_s) or _is_poison(skeleton or "") or _is_poison(anti or ""):
        return {"ok": False, "rejected": "poison", "reason": "kisisel_veya_zehir"}
    # Pozitif kalıp yalnız kanıtlı yeşilden
    ev = (evidence or "").strip().lower()
    if kind_u != "ANTI" and kind_u != "GATE" and ev not in (
        "green_cirak",
        "seed_verified",
        "usta_gate",
    ):
        return {"ok": False, "rejected": "evidence", "reason": "pozitif_icin_kanit_yok"}
    if ev in ("red", "fail", "unknown", "hallucination"):
        return {"ok": False, "rejected": "evidence", "reason": "kirmizi_yasak"}

    rows = load_lessons(workspace_root)
    key = _rule_key(kind_u, rule_s)
    for row in rows:
        if row.get("key") == key or (
            str(row.get("kind") or "").upper() == kind_u
            and _norm_rule(str(row.get("rule") or "")) == _norm_rule(rule_s)
        ):
            row["hits"] = int(row.get("hits") or 1) + 1
            row["updated_ts"] = time.time()
            if scope_sample:
                row["scope_sample"] = (scope_sample or "")[:80]
            _rewrite_all(path, _trim(rows))
            return {"ok": True, "dedup": True, "id": row.get("id"), "hits": row["hits"]}

    lesson_id = f"ct-{time.strftime('%Y%m%d')}-{key[:6]}"
    entry = {
        "id": lesson_id,
        "key": key,
        "v": 1,
        "kind": kind_u,
        "rule": rule_s,
        "skeleton": (skeleton or "")[:_SKEL_MAX] or None,
        "anti": ((anti or "")[:_ANTI_MAX] or None),
        "tags": [str(t).lower()[:24] for t in (tags or [])][:8],
        "evidence": ev,
        "scope_sample": (scope_sample or "")[:80],
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "created_ts": time.time(),
        "hits": 1,
        "version": CIRAK_TECRUBE_VERSION,
    }
    rows.append(entry)
    _rewrite_all(path, _trim(rows))
    return {"ok": True, "dedup": False, "id": lesson_id, "hits": 1}


def ensure_seed_lessons(workspace_root: str | Path | None) -> dict[str, Any]:
    """İlk kurulumda plan tohumlarını bir kez yaz (dedup güvenli)."""
    if not tecrube_enabled():
        return {"ok": False, "skipped": True}
    n = 0
    for s in _SEED:
        r = upsert_lesson(
            workspace_root,
            kind=str(s["kind"]),
            rule=str(s["rule"]),
            skeleton=str(s.get("skeleton") or ""),
            anti=s.get("anti"),
            tags=list(s.get("tags") or []),
            evidence="seed_verified",
            scope_sample="projects/cirak-atolyesi",
        )
        if r.get("ok") and not r.get("dedup"):
            n += 1
    return {"ok": True, "seeded_new": n, "total": len(load_lessons(workspace_root))}


def _goal_tags(goal: str, scope_rel: str = "") -> set[str]:
    low = f"{goal or ''} {scope_rel or ''}".lower().replace("\\", "/")
    tags: set[str] = set()
    if ".py" in low or "tests/" in low:
        tags.update({"spec", "path", "py", "test"})
    if "tests/" in low or "pytest" in low or "test_" in low:
        tags.update({"test", "pytest", "layout"})
    if "util" in low or "servis" in low or "yardim" in low or "filtre" in low:
        tags.update({"multi", "util"})
    if "paket" in low or "__init__" in low:
        tags.update({"paket", "layout", "multi"})
    if "generator" in low or "yield" in low or "filtre_satir" in low:
        tags.update({"api", "generator", "def"})
    if "cirak" in low or "is-b" in low or "cirak-is" in low:
        tags.update({"write", "gate", "spec"})
    if not tags:
        tags.update({"write", "spec", "test"})
    return tags


def select_lessons_for_goal(
    workspace_root: str | Path | None,
    *,
    goal: str = "",
    scope_rel: str = "",
    limit: int = _MAX_INJECT,
) -> list[dict[str, Any]]:
    rows = load_lessons(workspace_root)
    if not rows:
        ensure_seed_lessons(workspace_root)
        rows = load_lessons(workspace_root)
    want = _goal_tags(goal, scope_rel)
    scored: list[tuple[int, dict[str, Any]]] = []
    for r in rows:
        rtags = {str(t).lower() for t in (r.get("tags") or [])}
        kind = str(r.get("kind") or "").lower()
        overlap = len(want & (rtags | {kind}))
        score = overlap * 10 + int(r.get("hits") or 1)
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    # çeşitlilik: aynı kind en fazla 2
    out: list[dict[str, Any]] = []
    kind_count: dict[str, int] = {}
    for _sc, r in scored:
        k = str(r.get("kind") or "?")
        if kind_count.get(k, 0) >= 2:
            continue
        out.append(r)
        kind_count[k] = kind_count.get(k, 0) + 1
        if len(out) >= max(1, min(limit, _MAX_INJECT)):
            break
    return out


def build_tecrube_inject_block(
    workspace_root: str | Path | None,
    *,
    goal: str = "",
    scope_rel: str = "",
) -> str:
    if not tecrube_enabled():
        return ""
    lessons = select_lessons_for_goal(
        workspace_root, goal=goal, scope_rel=scope_rel, limit=_MAX_INJECT
    )
    if not lessons:
        return ""
    lines = [
        f"[ÇIRAK TECRÜBE — yalnız uygula, uydurma · {CIRAK_TECRUBE_VERSION}]",
    ]
    for r in lessons:
        kind = r.get("kind") or "?"
        rule = r.get("rule") or ""
        lines.append(f"- [{kind}] {rule}")
        sk = r.get("skeleton")
        if sk:
            lines.append(f"  iskelet: {str(sk).replace(chr(10), ' / ')[:180]}")
        anti = r.get("anti")
        if anti:
            lines.append(f"  yasak: {anti}")
    return "\n".join(lines)[:2500]


def augment_turn_with_cirak_tecrube(
    turn_user: str,
    workspace_root: str | Path | None,
    *,
    goal: str = "",
    scope_rel: str = "",
) -> str:
    if not tecrube_enabled():
        return turn_user
    try:
        from ilim_assistant.motorlar.programlama_faz34 import is_cirak_yazim_gorev

        if not is_cirak_yazim_gorev(goal, scope_rel):
            return turn_user
    except Exception:
        low = f"{goal} {scope_rel}".lower()
        if "cirak" not in low and "is-b" not in low:
            return turn_user
    block = build_tecrube_inject_block(
        workspace_root, goal=goal, scope_rel=scope_rel
    )
    if not block:
        return turn_user
    return block.rstrip() + "\n\n" + (turn_user or "").lstrip()


def record_cirak_tecrube_from_outcome(
    workspace_root: str | Path | None,
    *,
    goal: str = "",
    scope_rel: str = "",
    success: bool,
    verify_ok: bool,
    writes_ok: int = 0,
    root_cause: str = "",
    usta_kurtarma: bool = False,
) -> dict[str, Any]:
    """
    F2: Yeşil çırak → pozitif dar şablon.
    Kurtarma/kırmızı → yalnız ANTI/GATE (pozitif yok).
    """
    if not tecrube_enabled():
        return {"ok": False, "skipped": True}
    try:
        from ilim_assistant.motorlar.programlama_faz34 import is_cirak_yazim_gorev

        if not is_cirak_yazim_gorev(goal, scope_rel):
            return {"ok": False, "skipped": True, "reason": "not_cirak"}
    except Exception:
        return {"ok": False, "skipped": True, "reason": "import"}

    ensure_seed_lessons(workspace_root)
    written: list[dict[str, Any]] = []
    scope = (scope_rel or "")[:80]
    tags = sorted(_goal_tags(goal, scope_rel))

    # Kırmızı / yazımsız → pozitif yasak; ANTI
    if not success or not verify_ok or int(writes_ok) <= 0:
        r = upsert_lesson(
            workspace_root,
            kind="ANTI",
            rule="Yazım veya verify yoksa görev bitmedi; salt keşif/idle yeşil sayılmaz.",
            anti="writes=0 veya verify kırmızı → bitmiş sayma",
            tags=["anti", "write", "gate"] + tags[:3],
            evidence="usta_gate",
            scope_sample=scope,
        )
        written.append(r)
        if root_cause and root_cause not in ("ok", "unknown_fail", ""):
            r2 = upsert_lesson(
                workspace_root,
                kind="GATE",
                rule=f"Tekrarlayan kök: {root_cause[:80]} — görevde path/def/test net yaz, sonra write+verify.",
                tags=["gate", root_cause[:24]] + tags[:2],
                evidence="usta_gate",
                scope_sample=scope,
            )
            written.append(r2)
        return {"ok": True, "positive": False, "written": written}

    if usta_kurtarma:
        # Pozitif reçete değil — ANTI/GATE
        r = upsert_lesson(
            workspace_root,
            kind="ANTI",
            rule="Usta kurtarma gerekti: görev satırında .py yolu ve def adını eksik bırakma.",
            anti="eksik SPEC → kurtarma",
            tags=["anti", "spec"] + tags[:3],
            evidence="usta_gate",
            scope_sample=scope,
        )
        written.append(r)
        return {"ok": True, "positive": False, "usta": True, "written": written}

    # Yeşil çırak — dar pozitif şablonlar (uydurma yok)
    g_low = (goal or "").lower().replace("\\", "/")
    specs = [
        (
            "SPEC",
            "Görevde açık .py ve tests/test_*.py yolları yaz; modül.metod yetmez.",
            "projects/x/foo.py · tests/test_foo.py",
            ["spec", "path"],
        ),
        (
            "WRITE",
            "Çırak yeşili: en az bir @@write + hedefli verify.",
            "@@write … sonra pytest -q tests/…",
            ["write", "test"],
        ),
        (
            "TEST",
            "Test dosyası tests/ altında olsun; kökteki test_*.py hedef sayılmaz.",
            "pytest -q tests/test_foo.py",
            ["test", "layout"],
        ),
    ]
    if "util" in g_low or g_low.count(".py") >= 2 or "servis" in g_low or "app.py" in g_low:
        specs.append(
            (
                "MULTI",
                "Çok-modül: yardımcıyı ayrı dosyada tut; iş modülü import etsin.",
                "util.py + app.py/servis.py",
                ["multi", "util"],
            )
        )
    if "paket/" in g_low or "paket." in g_low or "__init__" in g_low:
        specs.append(
            (
                "LAYOUT",
                "Paket işinde paket/cekirdek.py + paket/__init__.py export zorunlu.",
                "from paket import …",
                ["paket", "layout"],
            )
        )
    if "generator" in g_low or "yield" in g_low or "filtre_satir" in g_low:
        specs.append(
            (
                "API",
                "İstenen def adını ve generator davranışını olduğu gibi uygula.",
                "def …(): yield …",
                ["api", "generator"],
            )
        )

    for kind, rule, skel, tgs in specs:
        written.append(
            upsert_lesson(
                workspace_root,
                kind=kind,
                rule=rule,
                skeleton=skel,
                tags=tgs + tags[:2],
                evidence="green_cirak",
                scope_sample=scope,
            )
        )
    return {"ok": True, "positive": True, "written": written}


def write_tecrube_ozet_md(workspace_root: str | Path | None) -> dict[str, Any]:
    """İnsan okuması — en çok hits 20 kural."""
    root = _repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "root"}
    rows = load_lessons(workspace_root)
    rows = sorted(rows, key=lambda r: int(r.get("hits") or 1), reverse=True)[:20]
    lines = [
        "# Çırak tecrübe özeti",
        "",
        f"Sürüm: `{CIRAK_TECRUBE_VERSION}` · otomatik · kişisel bellek yok",
        "",
    ]
    for r in rows:
        lines.append(f"- **[{r.get('kind')}]** {r.get('rule')} _(hits={r.get('hits', 1)})_")
    path = root / "projects" / "cirak-atolyesi" / "CIRAK_TECRUBE_OZET.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "path": str(path), "n": len(rows)}
