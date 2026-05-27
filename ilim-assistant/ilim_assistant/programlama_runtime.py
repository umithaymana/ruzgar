from __future__ import annotations

"""
Basit ProgramlamaRuntime — Rüzgar programlama motorunu tek başına kullanmak için ince katman.

Amaç:
- Dış dünyaya küçük ve anlaşılır bir API vermek:
    - ProgramlamaRuntime(workspace_root).run_task(scope_rel, goal)
    - read_file / write_file / verify gibi temel yardımcılar
- Rüzgar'ın Ana Motor / hub / Electron bağımlılıklarını zorunlu kılmadan programlama motorunu çağırmak.

Notlar:
- Bu modül, mevcut programlama motoru mantığını değiştirmez; yalnızca üstüne ince bir katman ekler.
- İlk sürümde yalnızca temel araçları (okuma/yazma/verify) ve Faz 14 görev döngüsünü sarar.
"""

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from ilim_assistant.motorlar.programlama_motoru import (
    ExecReport,
    ProgramlamaAraclari,
    ReadReport,
    WriteReport,
    repo_root,
)
from ilim_assistant.motorlar.programlama_faz14 import (
    iter_code_agent_turn_events,
    run_project_verify,
)


@dataclass
class TaskResult:
    """Görev sonucu — dış dünya için sade özet."""

    ok: bool
    scope_rel: str
    goal: str
    writes_ok: int
    verify_ok: bool
    detail: str = ""
    elapsed_sec: float | None = None
    turns: int = 0


@dataclass
class _RuntimeReq:
    """Faz14 SSE döngüsü için minimum request şekli."""

    workspace_root: str
    programlama_active_file: str | None = None


class ProgramlamaRuntime:
    """
    Programlama motoru için bağımsız çalışma katmanı.

    Kullanım:
        rt = ProgramlamaRuntime("D:/projeler/benim-api")
        res = rt.run_task("projects/benim-api", "health endpointine version ekle ve pytest geçir")
    """

    def __init__(self, workspace_root: str | os.PathLike[str] | None = None) -> None:
        root = repo_root(Path(workspace_root) if workspace_root is not None else None)
        if root is None:
            raise RuntimeError(
                "ProgramlamaRuntime: proje kökü bulunamadı. "
                "workspace_root veya RUZGAR_EXEC_CWD / LOCAL_TOOLS_ROOT ayarlayın."
            )
        self._root: Path = root
        self._tools = ProgramlamaAraclari(self._root)

    @property
    def workspace_root(self) -> Path:
        return self._root

    # Temel araçlar

    def read_file(self, rel_path: str, max_chars: int = 6000) -> ReadReport:
        """Repo kökü altında güvenli okuma (local_tools kurallarına tabi)."""
        return self._tools.read(rel_path, max_chars=max_chars)

    def write_file(self, rel_path: str, content: str) -> WriteReport:
        """Repo kökü altında güvenli yazma (bak dosyası + yasak yollar korunur)."""
        return self._tools.write(rel_path, content)

    def run_verify(self, scope_rel: str, goal: str = "") -> ExecReport | None:
        """Verilen proje kapsamı için pytest/npm gibi doğrulama preset'lerini çalıştırır."""
        return run_project_verify(self._root, scope_rel, goal=goal)

    # Görev döngüsü (Faz 14 sarmalayıcı)

    def _iter_task_events(self, scope_rel: str, goal: str) -> Iterator[dict[str, Any]]:
        """Faz14 event akışını bağımsız runtime için minimal parametrelerle çalıştır."""
        msg = f"görev: {scope_rel} {goal}".strip()
        req = _RuntimeReq(workspace_root=str(self._root))
        return iter_code_agent_turn_events(
            message=msg,
            req=req,
            system="",
            user_payload=msg,
            model="gpt-4o-mini",
            prior=[],
            mode_norm="programlama",
            coding=True,
            turn_plan=None,
            hits=[],
            new_wake=False,
            orch={},
            delegated_from_genel=False,
        )

    def run_task(self, scope_rel: str, goal: str) -> TaskResult:
        """
        Faz 14 kod ajanını tek çağrıda çalıştır.

        scope_rel: örn. "projects/benim-api"
        goal: "health endpointine version ekle ve pytest geçir"
        """
        try:
            from ilim_assistant.motorlar.programlama_faz85 import try_fast_deterministic_task

            fast = try_fast_deterministic_task(self._root, scope_rel, goal)
            if fast is not None:
                return TaskResult(
                    ok=bool(fast.get("ok")),
                    scope_rel=scope_rel,
                    goal=goal,
                    writes_ok=int(fast.get("writes_ok") or 0),
                    verify_ok=bool(fast.get("verify_ok")),
                    detail=str(fast.get("detail") or ""),
                    elapsed_sec=0.0,
                    turns=0,
                )
        except Exception:
            pass
        events = self._iter_task_events(scope_rel, goal)
        writes_ok = 0
        verify_ok = False
        detail = ""
        elapsed: float | None = None
        turns = 0
        for ev in events:
            et = str(ev.get("type") or "")
            if et == "status":
                detail = str(ev.get("text") or detail)
            if et == "done":
                ca = dict(ev.get("code_agent") or {})
                turns = int(ca.get("turns") or 0)
                elapsed = float(ca.get("elapsed_sec") or 0.0)
                verify_ok = bool(ca.get("success"))
                full = str(ev.get("full_reply") or "")
                writes_ok = full.count("Yazılan:")
                detail = detail or str(ca)
            if et == "error":
                detail = str(ev.get("text") or "Görev hatası")
        ok = bool(verify_ok or writes_ok > 0)
        return TaskResult(
            ok=ok,
            scope_rel=scope_rel,
            goal=goal,
            writes_ok=writes_ok,
            verify_ok=verify_ok,
            detail=detail,
            elapsed_sec=elapsed,
            turns=turns,
        )


def _main() -> int:
    p = argparse.ArgumentParser(description="Programlama runtime (standalone başlangıç)")
    p.add_argument("--workspace", required=True, help="Çalışma kökü (örn. D:/projeler)")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("task", help="Görev çalıştır")
    t.add_argument("--scope", required=True, help="Görev kapsamı (örn. projects/benim-api)")
    t.add_argument("--goal", required=True, help="Görev hedefi")

    r = sub.add_parser("read", help="Dosya oku")
    r.add_argument("--path", required=True, help="Kök göreli dosya yolu")

    w = sub.add_parser("write", help="Dosya yaz")
    w.add_argument("--path", required=True, help="Kök göreli dosya yolu")
    w.add_argument("--content", required=True, help="Yazılacak metin")

    v = sub.add_parser("verify", help="Kapsam doğrula")
    v.add_argument("--scope", required=True, help="Kapsam (örn. projects/benim-api)")
    v.add_argument("--goal", default="", help="Opsiyonel hedef ipucu")

    a = p.parse_args()
    rt = ProgramlamaRuntime(a.workspace)

    if a.cmd == "task":
        out = rt.run_task(a.scope, a.goal)
        print(json.dumps(out.__dict__, ensure_ascii=False, indent=2))
        return 0 if out.ok else 1
    if a.cmd == "read":
        rep = rt.read_file(a.path)
        print(json.dumps(rep.__dict__, ensure_ascii=False, indent=2))
        return 0 if rep.ok else 1
    if a.cmd == "write":
        rep = rt.write_file(a.path, a.content)
        print(json.dumps(rep.__dict__, ensure_ascii=False, indent=2))
        return 0 if rep.ok else 1
    if a.cmd == "verify":
        rep = rt.run_verify(a.scope, goal=a.goal)
        if rep is None:
            print(json.dumps({"ok": False, "error": "verify atlandı"}, ensure_ascii=False))
            return 1
        print(json.dumps(rep.__dict__, ensure_ascii=False, indent=2))
        return 0 if rep.ok else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())

