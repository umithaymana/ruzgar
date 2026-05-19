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
    Faz 10.4 — kullanıcı açıkça otonom hata ayıklama isterse (tek turda çok adım).

    Kapatmak: RUZGAR_CODE_DEBUG_AUTO=0
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
    )
    return any(k in low for k in keys)


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
    *,
    run_pytest: bool = True,
) -> tuple[ToolRunSummary, ExecReport | None]:
    """
    Faz 10.4 / 10.6 — LLM cevabındaki @@write bloklarını uygular; istenirse pytest ile doğrular.

    Dönüş: (özet, pytest raporu veya None).
    """
    summary, _ = run_tools_for_message((reply_body or "").strip(), workspace_root)
    pytest_rep: ExecReport | None = None
    tools = ProgramlamaAraclari(workspace_root)
    if run_pytest and tools.root is not None:
        pytest_rep = tools.run_dev_preset("pytest_run")
        summary.execs.append(pytest_rep)
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

    for rel in infer_rel_paths(message, tools.root):
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
) -> str:
    """Programlama modu LLM bağlamı: talimat + araç çıktıları (okuma/yazma/test).

    `run_presets=False` (varsayılan): tur hazırlığında pytest/ruff çalıştırma — ağır süreç
    yalnızca otonom debug döngüsünde (`apply_assistant_reply_tools`) yapılır.
    """
    from ilim_assistant.dinamit_gelisme import dinamit_heartbeat

    prompt = (message or "").strip()
    _, tools_block = run_tools_for_message(
        prompt, workspace_root, run_presets=run_presets
    )

    base = dinamit_heartbeat() + (
        f"[PROGRAMLAMA MOTORU — {MIMAR_IMZA}]\n"
        "Bu modda cevaplar teknik, doğru ve adım adım uygulanabilir olsun. "
        "Güvenli okuma/yazma (`local_tools`) ve onaylı test preset'leri "
        "(pytest_run, python_module_run, ruff_check) etkindir.\n"
        f"Kullanici mesaji: {prompt}\n"
    )
    if tools_block.strip():
        base = base.rstrip() + "\n\n" + tools_block.strip() + "\n"
    return base
