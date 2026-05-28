# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 98 (P12): Ümit abi onay kapısı — yerel işlem.

Kural: Onay olmadan bilgisayara müdahale YOK.
Akış: önizleme → «tamam yap» / «yapma» → (onaylıysa) uygula → sonuç raporu.

Desteklenen işlemler (izinli yollar):
  copy, move, mkdir, shell (projects/ veya izinli kök), pip_install, winget (dar liste)

Komutlar:
  «şu dosyayı şuraya taşı» · «işlem iste: …» · «tamam yap» · «yapma» · «işlem liste»
Kapat: RUZGAR_FAZ98=0
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root
from ilim_assistant.safety_policy import path_is_forbidden, validate_custom_winget_line

FAZ98_VERSION = "programlama-faz98-v1-2026-05-27"
_PENDING_FILE = "umit_onay_pending.json"
_LOG_FILE = "umit_onay_log.jsonl"
_PENDING_TTL_SEC = 900

_APPROVE_RE = re.compile(
    r"^\s*(?:tamam\s+yap|tamam|onayla|evet|yap|devam\s+et|onayliyorum|onaylıyorum|olur|tamamdir|tamamdır)\s*$",
    re.I,
)
_REJECT_RE = re.compile(
    r"^\s*(?:yapma|iptal|vazge[cç]|hayir|hayır|dur|istemiyorum|vazgectim|vazgeçtim)\s*$",
    re.I,
)
_LIST_RE = re.compile(r"^\s*(?:işlem|islem)\s+liste\s*$", re.I)
_HISTORY_RE = re.compile(r"^\s*(?:işlem|islem)\s+geçmiş(?:i)?(?:\s+.+)?\s*$", re.I)
_CANCEL_RE = re.compile(r"^\s*(?:işlem|islem)\s+iptal\s*$", re.I)
_EXPLICIT_ISTEK_RE = re.compile(
    r"^\s*(?:işlem|islem)\s+iste(?:k|ğ)?\s*:\s*(.+)$",
    re.I | re.S,
)
_SHELL_ISTEK_RE = re.compile(
    r"^\s*(?:shell|ozgur-shell|özgür\s*shell)\s+istek\s*:\s*(.+)$",
    re.I | re.S,
)
_SHELL_ONAY_RE = re.compile(
    r"^\s*(?:shell|ozgur-shell|özgür\s*shell)\s+onay\s*:\s*(.+)$",
    re.I | re.S,
)
_SHELL_ONAYLA_RE = re.compile(r"^\s*shell\s+onayla(?:\s*:\s*[a-f0-9]{6,12})?\s*$", re.I)
_SHELL_IPTAL_RE = re.compile(r"^\s*shell\s+iptal\s*$", re.I)
_SHELL_LISTE_RE = re.compile(r"^\s*shell\s+liste\s*$", re.I)

_MOVE_RE = re.compile(
    r"(?:"
    r"(.+?)\s+(?:dosyasini|dosyasını|dosyayı|dosyayi|logu|klasörünü|klasorunu)\s+(.+?)\s+(?:taşı|tasi|suraya\s+taşı|şuraya\s+taşı)|"
    r"(?:taşı|tasi|move)\s+(.+?)\s+(?:->|→|şuraya|suraya|içine|icine|to)\s+(.+)|"
    r"(.+?)\s+(?:yolunu|klasörüne|klasorune)\s+(.+?)\s+(?:taşı|tasi)"
    r")",
    re.I | re.S,
)
_COPY_RE = re.compile(
    r"(?:"
    r"(.+?)\s+(?:kopyala|copy)\s+(?:şuraya|suraya|to|->|→)\s+(.+)|"
    r"(?:kopyala|copy)\s+(.+?)\s+(?:->|→|şuraya|suraya|to)\s+(.+)"
    r")",
    re.I | re.S,
)
_PIP_RE = re.compile(
    r"(?:pip\s+install|kur(?:ulum)?|yükle|yukle)\s+([a-zA-Z0-9_\-\.]+)",
    re.I,
)
_SHELL_NATURAL_RE = re.compile(
    r"(?:çalıştır|calistir|çalistir|koş|kos)\s*[:：]?\s*(.+)$",
    re.I | re.S,
)

_HOME_REL = ("Desktop", "Masaüstü", "Downloads", "İndirilenler", "Indirilenler", "Documents", "Belgeler")


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ98", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz98_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _clean_path_phrase(raw: str) -> str:
    s = (raw or "").strip().strip('"').strip("'")
    if not s:
        return ""
    # Natural-language fillers around file paths.
    s = re.sub(r"^\s*(?:dosya(?:s[ıi])?|klas[oö]r(?:[üu])?)\s+", "", s, flags=re.I)
    s = re.sub(r"\s+(?:dosya(?:s[ıi])?|klas[oö]r(?:[üu])?)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s+(?:i[cç]ine|i[cç]eris?ine|alt[ıi]na|yoluna)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s+(?:şuraya|suraya)\s*$", "", s, flags=re.I)
    s = re.sub(r"^(?:deki|daki)\s+", "", s, flags=re.I)
    return s.strip()


def _rewrite_natural_root(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return s
    # Common Turkish location phrases -> canonical folder names under home.
    root_patterns = (
        (r"^\s*masa(?:üstü|ustu)(?:ndeki|deki)?\s+", "Desktop"),
        (r"^\s*desktop(?:taki|teki|deki)?\s+", "Desktop"),
        (r"^\s*indirilenler\s+klas[oö]r(?:ü|u)ndeki\s+", "Downloads"),
        (r"^\s*indirilenler(?:deki)?\s+", "Downloads"),
        (r"^\s*downloads(?:taki|teki|deki)?\s+", "Downloads"),
        (r"^\s*belgeler(?:deki)?\s+", "Documents"),
        (r"^\s*belgelerdeki\s+", "Documents"),
        (r"^\s*documents(?:taki|teki|deki)?\s+", "Documents"),
    )
    for pat, target in root_patterns:
        m = re.match(pat, s, flags=re.I)
        if m:
            rest = s[m.end():].lstrip("/\\ ")
            return str((Path.home() / target / rest).resolve()) if rest else str((Path.home() / target).resolve())
    return s


def _pending_path(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    d = root / ".ruzgar"
    try:
        d.mkdir(parents=True, exist_ok=True)
        return d / _PENDING_FILE
    except OSError:
        return None


def _token_for(op: dict[str, Any]) -> str:
    raw = json.dumps(
        {
            "kind": op.get("kind"),
            "src": op.get("src"),
            "dst": op.get("dst"),
            "command": op.get("command"),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]


def load_pending(workspace_root: str | Path | None) -> dict[str, Any] | None:
    path = _pending_path(workspace_root)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if float(data.get("expires_at") or 0) < time.time():
        clear_pending(workspace_root)
        return None
    return data


def save_pending(workspace_root: str | Path | None, op: dict[str, Any]) -> dict[str, Any]:
    path = _pending_path(workspace_root)
    if path is None:
        return {"ok": False, "error": "workspace kökü yok"}
    now = time.time()
    payload = {
        **op,
        "token": _token_for(op),
        "created_at": now,
        "expires_at": now + _PENDING_TTL_SEC,
        "version": FAZ98_VERSION,
    }
    store = {"operation": op, **{k: v for k, v in payload.items() if k != "operation"}}
    try:
        path.write_text(
            json.dumps(store, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"ok": True, **store}
    except OSError as exc:
        return {"ok": False, "error": str(exc)[:120]}


def clear_pending(workspace_root: str | Path | None) -> bool:
    path = _pending_path(workspace_root)
    if path is None:
        return False
    try:
        path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _log_path(workspace_root: str | Path | None) -> Path | None:
    root = repo_root(workspace_root)
    if root is None:
        return None
    d = root / ".ruzgar"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return d / _LOG_FILE


def append_audit_log(
    workspace_root: str | Path | None,
    *,
    event: str,
    op: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
) -> None:
    path = _log_path(workspace_root)
    if path is None:
        return
    row = {
        "ts": round(time.time(), 3),
        "event": event,
        "version": FAZ98_VERSION,
    }
    if op:
        row["op"] = {
            "kind": op.get("kind"),
            "label": op.get("label"),
            "src": op.get("src_abs") or op.get("src"),
            "dst": op.get("dst_abs") or op.get("dst"),
            "command": op.get("command"),
            "package": op.get("package"),
        }
    if result:
        row["result"] = {
            "ok": result.get("ok"),
            "summary": str(result.get("summary") or "")[:240],
            "error": str(result.get("error") or "")[:240],
        }
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        return


def _parse_history_query(raw: str) -> tuple[int, str]:
    low = _ascii_fold(raw)
    nums = re.findall(r"\b(\d{1,2})\b", raw)
    limit = int(nums[0]) if nums else 8
    limit = max(1, min(20, limit))
    mode = "all"
    if "sadece fail" in low or "yalniz fail" in low or "yalnız fail" in low:
        mode = "fail"
    elif "sadece ok" in low or "yalniz ok" in low or "yalnız ok" in low:
        mode = "ok"
    return limit, mode


def format_history_report(
    workspace_root: str | Path | None,
    *,
    limit: int = 8,
    mode: str = "all",
) -> str:
    path = _log_path(workspace_root)
    if path is None or not path.is_file():
        return f"Ümit abi, henüz işlem geçmişi yok.\n({FAZ98_VERSION})"
    try:
        rows = [x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    except OSError:
        return f"Ümit abi, işlem geçmişi okunamadı.\n({FAZ98_VERSION})"
    lines = ["Ümit abi, son onaylı işlem geçmişi:", ""]
    shown = 0
    for raw in reversed(rows):
        if shown >= max(1, min(20, limit)):
            break
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        op = row.get("op") or {}
        res = row.get("result") or {}
        kind = op.get("label") or op.get("kind") or "işlem"
        evt = row.get("event") or "event"
        is_ok = bool(res.get("ok"))
        if mode == "fail" and is_ok:
            continue
        if mode == "ok" and not is_ok:
            continue
        mark = "OK" if res.get("ok") else ("PREVIEW" if evt == "preview_created" else "FAIL")
        tail = str(res.get("summary") or res.get("error") or evt)[:100]
        lines.append(f"- {mark} {kind}: {tail}")
        shown += 1
    if shown == 0:
        return f"Ümit abi, geçmişte okunur kayıt yok.\n({FAZ98_VERSION})"
    lines.append(f"\n({FAZ98_VERSION})")
    return "\n".join(lines)


def _extra_allow_roots() -> list[Path]:
    raw = os.environ.get("RUZGAR_FAZ98_EXTRA_PATHS", "").strip()
    out: list[Path] = []
    for part in raw.split(";"):
        p = part.strip()
        if p:
            try:
                out.append(Path(p).expanduser().resolve())
            except OSError:
                continue
    return out


def _standard_allow_roots(workspace_root: str | Path | None) -> list[Path]:
    roots: list[Path] = []
    wr = repo_root(workspace_root)
    if wr is not None:
        roots.append(wr.resolve())
    home = Path.home()
    for name in _HOME_REL:
        cand = home / name
        if cand.is_dir():
            roots.append(cand.resolve())
    roots.extend(_extra_allow_roots())
    uniq: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        key = str(r).lower()
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


def resolve_allowed_path(
    raw: str,
    workspace_root: str | Path | None,
    *,
    must_exist: bool = False,
) -> tuple[Path | None, str]:
    text = _rewrite_natural_root(_clean_path_phrase(raw))
    if not text:
        return None, "boş yol"
    if ".." in Path(text.replace("\\", "/")).parts:
        return None, "üst dizine çıkış (..) yasak"

    p = Path(text).expanduser()
    if not p.is_absolute():
        wr = repo_root(workspace_root)
        if wr is None:
            return None, "göreli yol için proje kökü gerekli"
        p = (wr / text.replace("\\", "/").lstrip("/")).resolve()
    else:
        p = p.resolve()

    if path_is_forbidden(p):
        return None, "sistem yolu — izin yok"

    allowed = False
    for root in _standard_allow_roots(workspace_root):
        try:
            p.relative_to(root)
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        return None, "yol izinli alanın dışında (repo, Masaüstü, İndirilenler, Belgeler)"

    if must_exist and not p.exists():
        return None, f"bulunamadı: {p}"
    return p, ""


def _validate_write_target(p: Path) -> tuple[bool, str]:
    try:
        from ilim_assistant.motorlar.programlama_faz3 import programlama_write_allowed

        wr = repo_root(None)
        if wr is not None:
            try:
                rel = str(p.resolve().relative_to(wr.resolve())).replace("\\", "/")
                ok, reason = programlama_write_allowed(wr, rel)
                if not ok:
                    return False, reason
            except ValueError:
                pass
    except Exception:
        pass
    return True, ""


def _preview_copy_move(kind: str, src: Path, dst: Path) -> dict[str, Any]:
    risks: list[str] = []
    success = f"Dosya `{dst}` konumunda olur."
    if kind == "move":
        success = f"Kaynak silinir; dosya `{dst}` altında kalır."
    if not src.is_file() and not src.is_dir():
        return {
            "ok": False,
            "error": f"kaynak yok: {src}",
            "risks": ["Kaynak bulunamadı — işlem başarısız olur."],
        }
    if dst.exists():
        risks.append("Hedefte aynı isim var — üzerine yazılabilir veya hata döner.")
    parent = dst.parent
    if not parent.is_dir():
        risks.append("Hedef klasör yok — oluşturulmayı denerim (onay sonrası).")
    ok_w, reason = _validate_write_target(dst)
    if not ok_w:
        return {"ok": False, "error": reason, "risks": [reason]}
    size = src.stat().st_size if src.is_file() else 0
    return {
        "ok": True,
        "success": success,
        "risks": risks or ["Düşük risk — yalnızca belirttiğin dosya/klasör."],
        "detail": f"Boyut ~{size // 1024} KB" if size else "Klasör veya boş dosya",
    }


def _preview_shell(command: str, cwd: Path | None) -> dict[str, Any]:
    try:
        from ilim_assistant.motorlar.programlama_faz67 import validate_shell_command

        ok, err = validate_shell_command(command)
        if not ok:
            return {"ok": False, "error": err, "risks": [err]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120], "risks": []}
    return {
        "ok": True,
        "success": "Komut çalışır; çıktı terminal özetinde döner.",
        "risks": [
            "Yanlış komut proje dosyalarını etkileyebilir — emin değilsen yapma de.",
        ],
        "detail": f"Çalışma dizini: {cwd or '?'}",
    }


def _preview_pip(package: str) -> dict[str, Any]:
    pkg = re.sub(r"[^a-zA-Z0-9_\-\.]", "", package or "")
    if not pkg:
        return {"ok": False, "error": "geçersiz paket adı", "risks": []}
    return {
        "ok": True,
        "success": f"`{pkg}` Python ortamına kurulur (pip).",
        "risks": ["İnternet ve pip gerekir; sürüm çakışması olabilir."],
        "detail": f"python -m pip install {pkg}",
    }


def build_operation(
    kind: str,
    workspace_root: str | Path | None,
    *,
    src: str | None = None,
    dst: str | None = None,
    command: str | None = None,
    scope_rel: str | None = None,
    package: str | None = None,
) -> dict[str, Any]:
    op: dict[str, Any] = {
        "kind": kind,
        "label": kind,
        "src": src,
        "dst": dst,
        "command": command,
        "scope_rel": scope_rel,
        "package": package,
    }
    preview: dict[str, Any]

    if kind in ("copy", "move"):
        sp, err_s = resolve_allowed_path(str(src or ""), workspace_root, must_exist=True)
        dp, err_d = resolve_allowed_path(str(dst or ""), workspace_root, must_exist=False)
        if sp is None:
            return {"ok": False, "error": err_s}
        if dp is None:
            return {"ok": False, "error": err_d}
        op["src_abs"] = str(sp)
        op["dst_abs"] = str(dp)
        preview = _preview_copy_move(kind, sp, dp)
    elif kind == "mkdir":
        dp, err_d = resolve_allowed_path(str(dst or src or ""), workspace_root, must_exist=False)
        if dp is None:
            return {"ok": False, "error": err_d}
        op["dst_abs"] = str(dp)
        preview = {
            "ok": True,
            "success": f"Klasör oluşur: {dp}",
            "risks": ["Zaten varsa sorun çıkmaz (atlanır)."],
            "detail": "",
        }
    elif kind == "shell":
        cmd = (command or "").strip()
        cwd = None
        scope = (scope_rel or "").strip().replace("\\", "/")
        if scope.startswith("projects/"):
            try:
                from ilim_assistant.motorlar.programlama_faz15 import _scope_cwd

                cwd = _scope_cwd(workspace_root, scope)
            except Exception:
                cwd = None
        if cwd is None:
            wr = repo_root(workspace_root)
            cwd = wr
        preview = _preview_shell(cmd, cwd)
        op["cwd"] = str(cwd) if cwd else ""
    elif kind == "pip_install":
        preview = _preview_pip(str(package or ""))
        op["package"] = re.sub(r"[^a-zA-Z0-9_\-\.]", "", str(package or ""))
    elif kind == "winget":
        line = (command or "").strip()
        ok, err = validate_custom_winget_line(line)
        if not ok:
            return {"ok": False, "error": err, "risks": [err]}
        preview = {
            "ok": True,
            "success": "Winget kurulumu başlatılır (yalnızca onaylı Python paketi).",
            "risks": ["Sistem genelinde kurulum — emin değilsen yapma."],
            "detail": line,
        }
    else:
        return {"ok": False, "error": f"bilinmeyen işlem: {kind}"}

    if not preview.get("ok"):
        return {"ok": False, "error": preview.get("error", "?"), "risks": preview.get("risks") or []}

    op["preview"] = preview
    op["label"] = {
        "copy": "Dosya kopyalama",
        "move": "Dosya taşıma",
        "mkdir": "Klasör oluşturma",
        "shell": "Terminal komutu",
        "pip_install": "Python paket kurulumu",
        "winget": "Winget kurulumu",
    }.get(kind, kind)
    return {"ok": True, "operation": op}


def format_preview_report(pending: dict[str, Any]) -> str:
    op = pending.get("operation") or pending
    preview = op.get("preview") or {}
    kind = op.get("kind") or "?"
    lines = [
        "Ümit abi, **şu işlemi yapmak istiyorum — henüz yapmadım.**",
        "",
        f"**Ne:** {op.get('label') or kind}",
    ]
    if op.get("src_abs") or op.get("src"):
        lines.append(f"**Kaynak:** `{op.get('src_abs') or op.get('src')}`")
    if op.get("dst_abs") or op.get("dst"):
        lines.append(f"**Hedef:** `{op.get('dst_abs') or op.get('dst')}`")
    if op.get("command"):
        lines.append(f"**Komut:** `{op.get('command')}`")
    if op.get("package"):
        lines.append(f"**Paket:** `{op.get('package')}`")
    if op.get("scope_rel"):
        lines.append(f"**Kapsam:** `{op.get('scope_rel')}`")
    if preview.get("detail"):
        lines.append(f"**Ayrıntı:** {preview['detail']}")
    lines.extend(
        [
            "",
            f"**Beklenen sonuç (iyi senaryo):** {preview.get('success', '?')}",
            "",
            "**Olası sorunlar:**",
        ]
    )
    for r in preview.get("risks") or ["Bilinmeyen risk — emin değilsen yapma."]:
        lines.append(f"- {r}")
    token = pending.get("token") or "?"
    lines.extend(
        [
            "",
            "Sonuç sende:",
            "- Sorun yoksa: **`tamam yap`** veya **`tamam`**",
            "- İstemiyorsan: **`yapma`** veya **`iptal`**",
            f"- Jeton: `{token}` (15 dk geçerli)",
            "",
            f"({FAZ98_VERSION})",
        ]
    )
    return "\n".join(lines)


def format_result_report(result: dict[str, Any]) -> str:
    if result.get("cancelled"):
        return f"Ümit abi, işlem iptal edildi — bilgisayarına dokunmadım.\n({FAZ98_VERSION})"
    if not result.get("ok"):
        return (
            f"Ümit abi, işlemi denedim ama **olmadı**: {result.get('error', '?')}\n"
            f"Çıktı: {(result.get('output') or '')[:800]}\n({FAZ98_VERSION})"
        )
    lines = [
        "Ümit abi, **onayladığın işlemi yaptım.**",
        "",
        f"**Ne yaptım:** {result.get('label', '?')}",
        f"**Sonuç:** {result.get('summary', 'Tamamlandı.')}",
    ]
    if result.get("output"):
        lines.extend(["", "**Çıktı (özet):**", "```", str(result["output"])[:2000], "```"])
    lines.append(f"\n({FAZ98_VERSION})")
    return "\n".join(lines)


def execute_operation(
    workspace_root: str | Path | None,
    op: dict[str, Any],
) -> dict[str, Any]:
    kind = str(op.get("kind") or "")
    label = str(op.get("label") or kind)

    if kind in ("copy", "move"):
        src = Path(str(op.get("src_abs") or ""))
        dst = Path(str(op.get("dst_abs") or ""))
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if kind == "copy":
                if src.is_dir():
                    if dst.exists():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            else:
                shutil.move(str(src), str(dst))
            return {
                "ok": True,
                "label": label,
                "summary": f"{'Kopyalandı' if kind == 'copy' else 'Taşındı'} → `{dst}`",
            }
        except OSError as exc:
            return {"ok": False, "label": label, "error": str(exc)[:200]}

    if kind == "mkdir":
        dst = Path(str(op.get("dst_abs") or ""))
        try:
            dst.mkdir(parents=True, exist_ok=True)
            return {"ok": True, "label": label, "summary": f"Klasör hazır: `{dst}`"}
        except OSError as exc:
            return {"ok": False, "label": label, "error": str(exc)[:200]}

    if kind == "shell":
        scope = str(op.get("scope_rel") or "projects/")
        if not scope.startswith("projects/"):
            wr = repo_root(workspace_root)
            scope = "projects/"
            _ = wr
        try:
            from ilim_assistant.motorlar.programlama_faz67 import run_free_shell

            rep = run_free_shell(
                workspace_root,
                scope,
                str(op.get("command") or ""),
            )
            if rep.get("pending"):
                return {
                    "ok": False,
                    "label": label,
                    "error": "Shell Faz 67 bekliyor — işlem iste: shell … kullan",
                }
            ok = rep.get("exit_code") == 0
            out = (rep.get("output") or rep.get("error") or "")[:4000]
            return {
                "ok": ok,
                "label": label,
                "summary": "Komut bitti." if ok else "Komut hata kodu döndü.",
                "output": out,
                "error": "" if ok else out[:200],
            }
        except Exception as exc:
            return {"ok": False, "label": label, "error": str(exc)[:200]}

    if kind == "pip_install":
        import sys

        pkg = str(op.get("package") or "")
        try:
            from ilim_assistant.approved_executor import run_argv

            code, out, err = run_argv(
                [sys.executable, "-m", "pip", "install", pkg],
                timeout_sec=180,
                cwd=str(repo_root(workspace_root) or "."),
            )
            combined = (out or err or "")[:4000]
            return {
                "ok": code == 0,
                "label": label,
                "summary": f"`{pkg}` kuruldu." if code == 0 else "pip başarısız.",
                "output": combined,
                "error": "" if code == 0 else combined[:200],
            }
        except Exception as exc:
            return {"ok": False, "label": label, "error": str(exc)[:200]}

    if kind == "winget":
        line = str(op.get("command") or "")
        try:
            from ilim_assistant.approved_executor import run_argv

            code, out, err = run_argv(
                line.split(),
                timeout_sec=300,
                cwd=str(repo_root(workspace_root) or "."),
            )
            combined = (out or err or "")[:4000]
            return {
                "ok": code == 0,
                "label": label,
                "summary": "Winget tamam." if code == 0 else "Winget başarısız.",
                "output": combined,
                "error": "" if code == 0 else combined[:200],
            }
        except Exception as exc:
            return {"ok": False, "label": label, "error": str(exc)[:200]}

    return {"ok": False, "error": "desteklenmeyen işlem"}


def _parse_explicit_istek(body: str, workspace_root: str | Path | None) -> dict[str, Any] | None:
    text = body.strip()
    low = _ascii_fold(text)
    if low.startswith("copy "):
        parts = text[5:].split("->", 1)
        if len(parts) == 2:
            return build_operation("copy", workspace_root, src=parts[0].strip(), dst=parts[1].strip())
    if low.startswith("move "):
        parts = text[5:].split("->", 1)
        if len(parts) == 2:
            return build_operation("move", workspace_root, src=parts[0].strip(), dst=parts[1].strip())
    if low.startswith("mkdir "):
        return build_operation("mkdir", workspace_root, dst=text[6:].strip())
    if low.startswith("shell "):
        rest = text[6:].strip()
        scope = "projects/"
        cmd = rest
        if rest.lower().startswith("projects/"):
            sp = rest.split(None, 1)
            scope = sp[0]
            cmd = sp[1] if len(sp) > 1 else "dir"
        return build_operation(
            "shell",
            workspace_root,
            command=cmd,
            scope_rel=scope,
        )
    if low.startswith("pip "):
        return build_operation("pip_install", workspace_root, package=text[4:].strip())
    if low.startswith("winget "):
        return build_operation("winget", workspace_root, command=text.strip())
    return None


def _extract_shell_scope_and_command(raw_cmd: str) -> tuple[str, str]:
    text = (raw_cmd or "").strip()
    if not text:
        return "projects/", ""
    m = re.match(r"^\s*(projects/[^\s]+)\s+(.+)$", text, flags=re.I | re.S)
    if m:
        scope = m.group(1).rstrip("/") + "/"
        cmd = m.group(2).strip()
        return scope, cmd
    return "projects/", text


def parse_natural_operation(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    raw = (message or "").strip()
    if not raw:
        return None

    m = _EXPLICIT_ISTEK_RE.match(raw)
    if m:
        return _parse_explicit_istek(m.group(1), workspace_root)
    m_shell_istek = _SHELL_ISTEK_RE.match(raw) or _SHELL_ONAY_RE.match(raw)
    if m_shell_istek:
        scope, cmd = _extract_shell_scope_and_command(m_shell_istek.group(1))
        return build_operation(
            "shell",
            workspace_root,
            command=cmd,
            scope_rel=scope,
        )

    low = _ascii_fold(raw)
    if any(x in low for x in ("sil ", " delete", "rm -rf", "format c:")):
        return {
            "ok": False,
            "error": "Silme / disk formatı Faz 98 ile kapalı — güvenlik.",
            "risks": [],
        }

    cm = _COPY_RE.search(raw)
    if cm:
        g = [x for x in cm.groups() if x]
        if len(g) >= 2:
            return build_operation("copy", workspace_root, src=g[0].strip(), dst=g[-1].strip())

    mm = _MOVE_RE.search(raw)
    if mm:
        g = [x for x in mm.groups() if x]
        if len(g) >= 2:
            return build_operation("move", workspace_root, src=g[0].strip(), dst=g[-1].strip())

    pm = _PIP_RE.search(raw)
    if pm and any(x in low for x in ("kur", "yukle", "yükle", "pip", "paket")):
        return build_operation("pip_install", workspace_root, package=pm.group(1))

    if low.startswith("winget install"):
        return build_operation("winget", workspace_root, command=raw)

    sm = _SHELL_NATURAL_RE.search(raw)
    if sm:
        scope_m = re.search(r"(projects/[\w\-./]+)", raw, re.I)
        scope = scope_m.group(1) if scope_m else "projects/"
        return build_operation(
            "shell",
            workspace_root,
            command=sm.group(1).strip(),
            scope_rel=scope.rstrip("/") + "/" if not scope.endswith("/") else scope,
        )

    return None


def wants_umit_gate(message: str) -> bool:
    if not _enabled():
        return False
    raw = (message or "").strip()
    if not raw:
        return False
    if (
        _APPROVE_RE.match(raw)
        or _REJECT_RE.match(raw)
        or _LIST_RE.match(raw)
        or _HISTORY_RE.match(raw)
        or _CANCEL_RE.match(raw)
        or _EXPLICIT_ISTEK_RE.match(raw)
        or _SHELL_ISTEK_RE.match(raw)
        or _SHELL_ONAY_RE.match(raw)
        or _SHELL_ONAYLA_RE.match(raw)
        or _SHELL_IPTAL_RE.match(raw)
        or _SHELL_LISTE_RE.match(raw)
    ):
        return True
    low = _ascii_fold(raw)
    if any(
        k in low
        for k in (
            "islem iste",
            "işlem iste",
            "tamam yap",
            "dosyayi",
            "dosyayı",
            "suraya tasi",
            "şuraya taşı",
            "kopyala",
            "masaustune",
            "masaüstüne",
        )
    ):
        return True
    if _MOVE_RE.search(raw) or _COPY_RE.search(raw) or _PIP_RE.search(raw):
        return True
    if low.startswith("winget install"):
        return True
    if _SHELL_NATURAL_RE.search(raw):
        return True
    return False


def maybe_instant_faz98(
    message: str,
    workspace_root: str | Path | None = None,
) -> str | None:
    if not _enabled():
        return None

    raw = (message or "").strip()
    if _SHELL_ONAYLA_RE.match(raw):
        raw = "tamam yap"
    elif _SHELL_IPTAL_RE.match(raw):
        raw = "yapma"
    elif _SHELL_LISTE_RE.match(raw):
        raw = "işlem liste"
    pending = load_pending(workspace_root)

    if _REJECT_RE.match(raw) or _CANCEL_RE.match(raw):
        if pending:
            op = pending.get("operation") or pending
            clear_pending(workspace_root)
            append_audit_log(workspace_root, event="cancelled", op=op, result={"ok": True, "summary": "cancelled"})
            return format_result_report({"ok": True, "cancelled": True})
        return "Ümit abi, bekleyen onaylı işlem yok.\n" + f"({FAZ98_VERSION})"

    if _LIST_RE.match(raw):
        if not pending:
            return (
                "Ümit abi, bekleyen işlem yok. Dosya taşı/kopyala/kur için isteğini yaz; "
                "önce önizleme gösteririm.\n"
                f"({FAZ98_VERSION})"
            )
        return format_preview_report(pending)

    if _HISTORY_RE.match(raw):
        limit, mode = _parse_history_query(raw)
        return format_history_report(workspace_root, limit=limit, mode=mode)

    if _APPROVE_RE.match(raw):
        if not pending:
            return (
                "Ümit abi, onaylayacak bekleyen işlem yok. Önce ne yapmamı istediğini yaz.\n"
                f"({FAZ98_VERSION})"
            )
        op = pending.get("operation") or pending
        clear_pending(workspace_root)
        result = execute_operation(workspace_root, op)
        append_audit_log(workspace_root, event="approved_executed", op=op, result=result)
        return format_result_report(result)

    built = parse_natural_operation(raw, workspace_root)
    if built is None:
        return None
    if not built.get("ok"):
        err = built.get("error", "?")
        risks = "\n".join(f"- {r}" for r in built.get("risks") or [])
        return (
            f"Ümit abi, bu isteği şimdilik güvenle hazırlayamadım: {err}\n{risks}\n({FAZ98_VERSION})"
        )

    op = built["operation"]
    saved = save_pending(workspace_root, op)
    if not saved.get("ok"):
        return f"Ümit abi, işlem kuyruğa alınamadı: {saved.get('error')}\n({FAZ98_VERSION})"
    append_audit_log(workspace_root, event="preview_created", op=op, result={"ok": True, "summary": "preview"})
    return format_preview_report(saved)


def faz98_directive() -> str:
    return (
        "[ÜMİT ONAY KAPISI — Faz 98]\n"
        "Dosya taşı/kopyala, pip, projects/ shell: önce önizleme — «tamam yap» ile uygula.\n"
        "Vazgeç: «yapma» · Liste: «işlem liste»\n"
        "İzinli: repo, Masaüstü, İndirilenler, Belgeler (+ RUZGAR_FAZ98_EXTRA_PATHS)\n"
        "Onaysız müdahale YOK. Kapat: RUZGAR_FAZ98=0\n"
    )


def run_command_battery(
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    """
    Faz 98 komut-anlama ölçümü (P12).
    Skor, parse_natural_operation + wants_umit_gate üzerinden hesaplanır.
    """
    root = repo_root(workspace_root)
    batt_rel = "projects/_faz98_battery"
    if root is not None:
        try:
            batt_dir = (root / batt_rel).resolve()
            batt_dir.mkdir(parents=True, exist_ok=True)
            (batt_dir / "a.txt").write_text("a", encoding="utf-8")
            (batt_dir / "m.txt").write_text("m", encoding="utf-8")
        except OSError:
            pass
    try:
        dls = Path.home() / "Downloads"
        dls.mkdir(parents=True, exist_ok=True)
        (dls / "data.csv").write_text("id,val\n1,2\n", encoding="utf-8")
    except OSError:
        pass

    cases: list[dict[str, Any]] = [
        {"text": "işlem iste: mkdir projects/demo-a", "kind": "mkdir", "gate": True},
        {
            "text": f"islem iste: copy {batt_rel}/a.txt -> {batt_rel}/b.txt",
            "kind": "copy",
            "gate": True,
        },
        {
            "text": f"işlem iste: move {batt_rel}/m.txt -> {batt_rel}/moved.txt",
            "kind": "move",
            "gate": True,
        },
        {"text": "işlem iste: pip pytest", "kind": "pip_install", "gate": True},
        {"text": f"shell istek: {batt_rel}/ dir", "kind": "shell", "gate": True},
        {"text": f"shell onay: {batt_rel}/ dir", "kind": "shell", "gate": True},
        {
            "text": f"Masaüstündeki rapor.txt dosyasını {batt_rel}/rapor.txt şuraya taşı",
            "kind": "move",
            "gate": True,
        },
        {
            "text": f"İndirilenler klasöründeki data.csv dosyasını {batt_rel}/data.csv şuraya taşı",
            "kind": "move",
            "gate": True,
        },
        {"text": f"{batt_rel}/a.txt dosyasını {batt_rel}/x.txt şuraya taşı", "kind": "move", "gate": True},
        {"text": f"kopyala {batt_rel}/a.txt -> {batt_rel}/copy-a.txt", "kind": "copy", "gate": True},
        {"text": "tamam yap", "kind": None, "gate": True},
        {"text": "tamamdır", "kind": None, "gate": True},
        {"text": "olur", "kind": None, "gate": True},
        {"text": "yapma", "kind": None, "gate": True},
        {"text": "vazgeçtim", "kind": None, "gate": True},
        {"text": "işlem liste", "kind": None, "gate": True},
        {"text": "işlem geçmişi 20", "kind": None, "gate": True},
        {"text": "işlem geçmişi sadece fail", "kind": None, "gate": True},
        {"text": "merhaba abi", "kind": None, "gate": False},
        {"text": "hava nasıl bugün", "kind": None, "gate": False},
        {"text": "kodu açıkla", "kind": None, "gate": False},
        {"text": "şarkı açar mısın", "kind": None, "gate": False},
    ]
    checks: list[dict[str, Any]] = []
    ok_count = 0

    for c in cases:
        text = str(c.get("text") or "")
        expect_gate = bool(c.get("gate"))
        expect_kind = c.get("kind")
        got_gate = wants_umit_gate(text)
        got = parse_natural_operation(text, workspace_root)
        got_kind = (
            str(((got or {}).get("operation") or {}).get("kind") or "")
            if isinstance(got, dict) and got.get("ok")
            else None
        )
        kind_ok = (expect_kind is None) or (got_kind == expect_kind)
        gate_ok = got_gate == expect_gate
        ok = gate_ok and kind_ok
        if ok:
            ok_count += 1
        checks.append(
            {
                "text": text,
                "ok": ok,
                "gate_ok": gate_ok,
                "kind_ok": kind_ok,
                "expected_gate": expect_gate,
                "got_gate": got_gate,
                "expected_kind": expect_kind,
                "got_kind": got_kind,
            }
        )

    total = len(cases)
    score = int(round((ok_count / max(1, total)) * 100))
    return {
        "ok": ok_count == total,
        "score": score,
        "passed": ok_count,
        "total": total,
        "checks": checks,
        "version": FAZ98_VERSION,
    }


def evaluate_command_dataset(
    dataset: list[dict[str, Any]],
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    """
    Faz 98 için dış veri seti değerlendirici.
    Girdi satırı örneği: {"text":"...", "gate":True, "kind":"move"}
    """
    checks: list[dict[str, Any]] = []
    ok_count = 0
    for row in dataset:
        text = str(row.get("text") or "")
        expect_gate = bool(row.get("gate"))
        expect_kind = row.get("kind")
        tags = row.get("tags") or []
        got_gate = wants_umit_gate(text)
        got = parse_natural_operation(text, workspace_root)
        got_kind = (
            str(((got or {}).get("operation") or {}).get("kind") or "")
            if isinstance(got, dict) and got.get("ok")
            else None
        )
        gate_ok = got_gate == expect_gate
        kind_ok = (expect_kind is None) or (got_kind == expect_kind)
        ok = gate_ok and kind_ok
        if ok:
            ok_count += 1
        checks.append(
            {
                "text": text,
                "ok": ok,
                "tags": tags,
                "gate_ok": gate_ok,
                "kind_ok": kind_ok,
                "expected_gate": expect_gate,
                "got_gate": got_gate,
                "expected_kind": expect_kind,
                "got_kind": got_kind,
            }
        )
    total = len(dataset)
    score = int(round((ok_count / max(1, total)) * 100))
    by_tag: dict[str, dict[str, int]] = {}
    for c in checks:
        tag_list = c.get("tags") or []
        if not tag_list:
            tag_list = ["genel"]
        for tg in tag_list:
            st = by_tag.setdefault(str(tg), {"total": 0, "passed": 0})
            st["total"] += 1
            if c.get("ok"):
                st["passed"] += 1
    return {
        "ok": ok_count == total,
        "score": score,
        "passed": ok_count,
        "total": total,
        "checks": checks,
        "by_tag": by_tag,
        "version": FAZ98_VERSION,
    }
