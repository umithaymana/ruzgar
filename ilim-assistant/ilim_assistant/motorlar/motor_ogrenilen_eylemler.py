# Created by Ümit & Gökçenur
"""
Faz C — Öğrenilen motor eylemleri (onaylı hub delegasyonu).

Depo: ``{workspace}/.ruzgar/motor_ogrenilen_eylemler.json``

Öğretme (sohbet):
  ``eylem öğret: «tetik cümle» → video``
  ``komut öğret: tetik = programlama``

Yönetim:
  ``eylem listesi`` · ``eylem sil: «tetik»`` · ``eylem onayla: abc123``
"""

from __future__ import annotations

import json
import os
import re
import secrets
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.ana_motor_hub_faz76 import motor_label

FAZ_C_VERSION = "motor-ogrenilen-eylemler-v2-2026-06-07"
_STORE_NAME = "motor_ogrenilen_eylemler.json"
_MOTOR_TIPI = "Eylem"

_VALID_MOTORS = frozenset(
    {
        "programlama",
        "video",
        "hafiza",
        "tercume",
        "ses",
        "mimar",
        "okuma",
        "hizir",
    }
)

# Alt-intent: motor/spesifik iş (hub + masaüstü runner)
_VALID_SUB_INTENTS: dict[str, frozenset[str]] = {
    "video": frozenset(
        {
            "indir",
            "kes",
            "probe",
            "oynat",
            "kurgu",
            "transcode",
            "mux",
            "burn_sub",
            "concat",
            "list",
        }
    ),
    "programlama": frozenset({"pytest", "git", "briefing", "scan", "self_scan"}),
    "hafiza": frozenset({"durum", "gorev", "hatirla"}),
    "ses": frozenset({"stt", "profil", "oku", "ayar"}),
    "tercume": frozenset({"ara", "cevir", "indir"}),
    "mimar": frozenset({"foto", "sanat", "tasarim"}),
    "hizir": frozenset({"tara", "pazar"}),
}

_TEACH_RE = re.compile(
    r"^(?:eylem|komut)\s+(?:öğret|ogret)\s*[:：]\s*"
    r"(?:«([^»]+)»|\"([^\"]+)\"|'([^']+)'|(.+?))\s*"
    r"(?:→|->|=)\s*"
    r"(programlama|video|hafiza|tercume|ses|mimar|okuma|hizir)"
    r"(?:/([\w-]+))?\s*$",
    re.I,
)
_DELETE_RE = re.compile(
    r"^eylem\s+(?:sil|unut|kaldır|kaldir)\s*[:：]\s*"
    r"(?:«([^»]+)»|\"([^\"]+)\"|'([^']+)'|(.+)|id\s*[:：]?\s*([a-z0-9]{6,12}))\s*$",
    re.I,
)
_APPROVE_RE = re.compile(
    r"^eylem\s+(?:onayla|approve)\s*[:：]?\s*([a-z0-9]{6,12})\s*$",
    re.I,
)
_LIST_RE = re.compile(
    r"^(?:eylem|komut)\s+(?:listesi|list|yardım|yardim)\s*$|"
    r"^öğrenilen\s+(?:eylem|komut)|^eylem\s+paneli\s*$",
    re.I,
)

_INSTANCE: LearnedActionStore | None = None


def _enabled() -> bool:
    return os.environ.get("RUZGAR_MOTOR_EYLEM_OGREN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz_c_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _norm_key(text: str) -> str:
    t = _ascii_fold(text)
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _resolve_store_root(workspace_root: str | Path | None) -> Path:
    if workspace_root is not None and str(workspace_root).strip():
        return Path(str(workspace_root).strip()).resolve()
    pkg = Path(__file__).resolve().parents[1]
    ilim = pkg.parent
    env = (os.environ.get("RUZGAR_WORKSPACE_ROOT") or "").strip()
    if env:
        return Path(env).resolve()
    return ilim.resolve()


def _store_path(workspace_root: str | Path | None) -> Path:
    return _resolve_store_root(workspace_root) / ".ruzgar" / _STORE_NAME


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id() -> str:
    return secrets.token_hex(5)


def _fuzzy_min() -> float:
    try:
        return float(os.environ.get("RUZGAR_EYLEM_FUZZY_MIN", "0.82"))
    except ValueError:
        return 0.82


def validate_sub_intent(motor: str, sub_intent: str | None) -> str | None:
    mid = (motor or "").strip().lower()
    if mid == "okuma":
        mid = "mimar"
    sub = (sub_intent or "").strip().lower().replace("-", "_")
    if not sub:
        return None
    allowed = _VALID_SUB_INTENTS.get(mid)
    if not allowed or sub not in allowed:
        opts = ", ".join(sorted(allowed or ()))
        raise ValueError(
            f"Geçersiz alt-intent «{sub}» ({mid}). Geçerli: {opts or '(yok)'}"
        )
    return sub


def sub_intents_catalog() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for mid, subs in _VALID_SUB_INTENTS.items():
        out[mid] = sorted(subs)
    return {
        "ok": True,
        "version": FAZ_C_VERSION,
        "motors": out,
        "teach_format": "eylem öğret: «tetik» → video/kes",
    }


class LearnedActionStore:
    def __init__(self, workspace_root: str | Path | None = None) -> None:
        self._root = workspace_root
        self._path = _store_path(workspace_root)
        self._actions: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        path = self._path
        if not path.is_file():
            self._actions = []
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows = data.get("actions") if isinstance(data, dict) else None
            self._actions = [r for r in (rows or []) if isinstance(r, dict)]
        except (OSError, json.JSONDecodeError):
            self._actions = []

    def _save(self) -> None:
        path = self._path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": FAZ_C_VERSION,
            "updated_at": _now_iso(),
            "actions": self._actions,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def reload(self) -> None:
        self._load()

    def list_actions(self, *, approved_only: bool = True) -> list[dict[str, Any]]:
        rows = self._actions
        if approved_only:
            rows = [r for r in rows if r.get("approved") is not False]
        return list(reversed(rows))

    def add_action(
        self,
        trigger: str,
        motor: str,
        *,
        sub_intent: str | None = None,
        approved: bool | None = None,
        note: str = "",
    ) -> dict[str, Any]:
        trig = (trigger or "").strip()
        mid = (motor or "").strip().lower()
        if mid == "okuma":
            mid = "mimar"
        if not trig or len(trig) < 2:
            raise ValueError("Tetik cümle en az 2 karakter olmalı.")
        if mid not in _VALID_MOTORS:
            raise ValueError(f"Geçersiz motor: {mid}")
        sub = validate_sub_intent(mid, sub_intent)

        auto = os.environ.get("RUZGAR_EYLEM_AUTO_ONAY", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        )
        is_approved = auto if approved is None else bool(approved)

        for row in self._actions:
            if _norm_key(row.get("trigger", "")) == _norm_key(trig):
                row["motor"] = mid
                row["approved"] = is_approved
                row["updated_at"] = _now_iso()
                if sub:
                    row["sub_intent"] = sub
                elif "sub_intent" in row:
                    del row["sub_intent"]
                if note:
                    row["note"] = note
                self._save()
                return dict(row)

        row = {
            "id": _new_id(),
            "trigger": trig,
            "motor": mid,
            "intent": "hub_route",
            "approved": is_approved,
            "created_at": _now_iso(),
            "motor_tipi": _MOTOR_TIPI,
        }
        if sub:
            row["sub_intent"] = sub
        if note:
            row["note"] = note
        self._actions.append(row)
        self._save()

        try:
            from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

            meta = f"motor={mid}; id={row['id']}"
            if sub:
                meta += f"; sub={sub}"
            get_hafiza_motor().ekle_bilgi(
                f"eylem:{trig[:120]}",
                meta,
                motor_tipi=_MOTOR_TIPI,
            )
        except Exception:
            pass

        return row

    def delete_by_id(self, action_id: str) -> bool:
        aid = (action_id or "").strip().lower()
        if not aid:
            return False
        kept = [r for r in self._actions if str(r.get("id") or "").lower() != aid]
        if len(kept) == len(self._actions):
            return False
        self._actions = kept
        self._save()
        return True

    def delete_by_trigger_or_id(self, token: str) -> bool:
        tok = (token or "").strip()
        if not tok:
            return False
        tok_low = tok.lower()
        tok_norm = _norm_key(tok)
        kept: list[dict[str, Any]] = []
        removed = False
        for row in self._actions:
            rid = str(row.get("id") or "")
            trig = str(row.get("trigger") or "")
            if rid.lower() == tok_low or _norm_key(trig) == tok_norm:
                removed = True
                continue
            kept.append(row)
        if removed:
            self._actions = kept
            self._save()
        return removed

    def approve(self, action_id: str) -> dict[str, Any] | None:
        aid = (action_id or "").strip().lower()
        for row in self._actions:
            if str(row.get("id") or "").lower() == aid:
                row["approved"] = True
                row["approved_at"] = _now_iso()
                self._save()
                return dict(row)
        return None

    def match(self, message: str) -> dict[str, Any] | None:
        raw = (message or "").strip()
        if not raw:
            return None
        nq = _norm_key(raw)
        if not nq:
            return None

        best: dict[str, Any] | None = None
        best_score = 0.0

        for row in reversed(self._actions):
            if row.get("approved") is False:
                continue
            trig = str(row.get("trigger") or "").strip()
            if not trig:
                continue
            nt = _norm_key(trig)
            if not nt:
                continue
            if raw == trig or nq == nt:
                return {**dict(row), "eslesme": "tam", "skor": 1.0}
            if nq.startswith(nt) or nt.startswith(nq):
                sc = 0.95
                if sc > best_score:
                    best_score = sc
                    best = {**dict(row), "eslesme": "on ek", "skor": sc}
                continue
            ratio = SequenceMatcher(None, nq, nt).ratio()
            if ratio >= _fuzzy_min() and ratio > best_score:
                best_score = ratio
                best = {**dict(row), "eslesme": "fuzzy", "skor": ratio}

        return best


def get_learned_store(workspace_root: str | Path | None = None) -> LearnedActionStore:
    global _INSTANCE
    root_key = str(_resolve_store_root(workspace_root))
    if _INSTANCE is None or str(_resolve_store_root(getattr(_INSTANCE, "_root", None))) != root_key:
        _INSTANCE = LearnedActionStore(workspace_root=workspace_root)
    else:
        _INSTANCE.reload()
    return _INSTANCE


def reset_learned_store_singleton() -> None:
    global _INSTANCE
    _INSTANCE = None


def match_learned_action(
    message: str, workspace_root: str | Path | None = None
) -> dict[str, Any] | None:
    if not _enabled():
        return None
    return get_learned_store(workspace_root).match(message)


def parse_teach_action(message: str) -> tuple[str, str, str | None] | None:
    raw = (message or "").strip()
    m = _TEACH_RE.match(raw)
    if not m:
        return None
    trig = next(g for g in m.groups()[:4] if g)
    motor = (m.group(5) or "").strip().lower()
    sub_raw = (m.group(6) or "").strip() or None
    sub = validate_sub_intent(motor, sub_raw) if sub_raw else None
    return (trig.strip(), motor, sub)


def try_instant_learned_commands(
    message: str, workspace_root: str | Path | None = None
) -> str | None:
    """Eylem öğret / listele / sil — anında yanıt."""
    if not _enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None

    store = get_learned_store(workspace_root)

    parsed = parse_teach_action(raw)
    if parsed:
        trig, motor, sub = parsed
        try:
            row = store.add_action(trig, motor, sub_intent=sub)
        except ValueError as exc:
            return f"Ümit abi, kaydedemedim: {exc}"
        label = motor_label(row.get("motor") or motor)
        sub_txt = f"/{row.get('sub_intent')}" if row.get("sub_intent") else ""
        onay = "onaylı" if row.get("approved") else "onay bekliyor"
        if not row.get("approved"):
            return (
                f"Ümit abi, eylem kaydı oluşturdum (**{onay}**).\n"
                f"· Tetik: «{trig}»\n· Motor: **{label}{sub_txt}**\n· Kimlik: `{row.get('id')}`\n"
                f"Onaylamak için: `eylem onayla: {row.get('id')}`"
            )
        return (
            f"Tamam Ümit abi, öğrendim — «{trig}» deyince **{label}{sub_txt}** iş yaparım.\n"
            f"Kimlik: `{row.get('id')}` · ({FAZ_C_VERSION})"
        )

    am = _APPROVE_RE.match(raw)
    if am:
        row = store.approve(am.group(1))
        if not row:
            return "Ümit abi, bu kimlikte eylem bulamadım."
        return (
            f"Onaylandı: «{row.get('trigger')}» → **{motor_label(str(row.get('motor')))}** "
            f"(`{row.get('id')}`)"
        )

    dm = _DELETE_RE.match(raw)
    if dm:
        token = next((g for g in dm.groups() if g), "")
        if store.delete_by_trigger_or_id(token.strip()):
            return f"Ümit abi, eylem silindi: «{token.strip()}»"
        return "Silinecek eylem bulamadım."

    if _LIST_RE.search(_ascii_fold(raw)):
        if re.match(r"^eylem\s+paneli\s*$", _ascii_fold(raw)):
            return "__OPEN_EYLEM_PANEL__"
        rows = store.list_actions(approved_only=False)
        if not rows:
            return (
                "Ümit abi, henüz öğrenilmiş eylem yok.\n"
                "Örnek: `eylem öğret: «test indir» → video/indir` · `eylem paneli`"
            )
        lines = ["Ümit abi, **öğrenilen eylemler:**", ""]
        for row in rows[:20]:
            st = "✓" if row.get("approved") is not False else "⏳"
            sub = f"/{row.get('sub_intent')}" if row.get("sub_intent") else ""
            lines.append(
                f"{st} `{row.get('id')}` · «{row.get('trigger')}» → "
                f"**{motor_label(str(row.get('motor')))}{sub}**"
            )
        lines.extend(["", "Panel: **eylem paneli**", f"({FAZ_C_VERSION})"])
        return "\n".join(lines)

    return None


def learned_actions_snapshot(workspace_root: str | Path | None = None) -> dict[str, Any]:
    store = get_learned_store(workspace_root)
    rows = store.list_actions(approved_only=False)
    return {
        "ok": True,
        "version": FAZ_C_VERSION,
        "count": len(rows),
        "approved_count": sum(1 for r in rows if r.get("approved") is not False),
        "path": str(store._path),
        "actions": [
            {
                "id": r.get("id"),
                "trigger": r.get("trigger"),
                "motor": r.get("motor"),
                "sub_intent": r.get("sub_intent"),
                "approved": r.get("approved") is not False,
            }
            for r in rows[:40]
        ],
    }
