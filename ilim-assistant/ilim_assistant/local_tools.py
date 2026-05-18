"""Yerel araç bağlamı — model + gerçek dünya arasında köprü (tarih/saat, dosya özütü)."""

from __future__ import annotations

import os
import re
import shutil
import socket
from datetime import datetime, timezone
from pathlib import Path

from ilim_assistant.safety_policy import path_is_forbidden

_WORD_TAIL = re.compile(r"[.,;:!?）\]»\"'”]+$")


def _clean_rel_token(raw: str) -> str:
    s = raw.strip()
    s = _WORD_TAIL.sub("", s)
    return s.replace("\\", "/")


def extract_at_paths(message: str) -> list[str]:
    """Mesajdaki @@göreli/yol ifadeleri (yinelenenleri tekilleştir)."""
    seen: set[str] = set()
    out: list[str] = []
    for m in re.finditer(r"@@(\S+)", message or ""):
        t = _clean_rel_token(m.group(1))
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _now_block() -> str:
    tz_name = os.environ.get("LOCAL_TOOLS_TZ", "Europe/Istanbul")
    now: datetime
    try:
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo(tz_name))
    except Exception:
        try:
            now = datetime.now().astimezone()
        except Exception:
            now = datetime.now(timezone.utc)
    iso = now.isoformat(timespec="seconds")
    days_tr = (
        "Pazartesi",
        "Salı",
        "Çarşamba",
        "Perşembe",
        "Cuma",
        "Cumartesi",
        "Pazar",
    )
    try:
        day_note = days_tr[now.weekday()]
    except Exception:
        day_note = ""
    lines = [
        "=== Yerel araç: tarih/saat ===",
        f"Yetkili anlık zaman: {iso}",
    ]
    if day_note:
        lines.append(f"Yerel hafta günü: {day_note}")
    lines.append(f"Saat dilimi hedefi: {tz_name}")
    return "\n".join(lines) + "\n"


def _hostname_block() -> str:
    if os.environ.get("LOCAL_TOOLS_HOSTNAME", "0").strip() not in ("1", "true", "yes"):
        return ""
    try:
        return f"Makine adı (yerel ağ): {socket.gethostname()}\n"
    except OSError:
        return ""


def safe_read_file_under_root(root: Path, rel: str, max_chars: int) -> tuple[str, str | None]:
    """(içerik, hata); içerik boş ve hata dolu ise okuma başarısız."""
    root = root.resolve()
    rel_norm = rel.replace("\\", "/").lstrip("/")
    if ".." in Path(rel_norm).parts:
        return "", "`..` içeren yol güvenlik nedeniyle reddedildi."
    cand = (root / rel_norm).resolve()
    try:
        cand.relative_to(root)
    except ValueError:
        return "", "Yol çalışma kökünün dışına çıkıyor."
    if not cand.is_file():
        return "", "Dosya bulunamadı veya klasör."
    try:
        raw = cand.read_bytes()
    except OSError as e:
        return "", str(e)
    if len(raw) > 32 * 1024 * 1024:
        return "", "Dosya çok büyük (üst sınır aşıldı)."
    sample = raw[: 4096 if len(raw) > 4096 else len(raw)]
    if b"\x00" in sample:
        return "", "İkili / metin olmayan dosya."
    text = raw.decode("utf-8", errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[…metin uzun olduğu için kesildi…]"
    return text, None


_WRITE_MAX_BYTES = 32 * 1024 * 1024
_WRITE_TMP_SUFFIX = ".ruzgar_write_tmp"


def safe_write_file_under_root(root: Path, file_path: str, content: str) -> bool:
    """
    Proje kökü altına güvenli metin yazımı.

    - Path traversal (`..`) ve kök dışı yollar reddedilir.
    - ``safety_policy.path_is_forbidden`` birebir uygulanır.
    - Mevcut dosya yazılmadan önce yanına ``.bak`` yedeği alınır; hata olursa geri yüklenir.
    - Başarılı yazımda True, aksi halde False.
    """
    root = root.resolve()
    rel_norm = file_path.replace("\\", "/").lstrip("/")
    if not rel_norm:
        return False
    if ".." in Path(rel_norm).parts:
        return False

    cand = (root / rel_norm).resolve()
    try:
        cand.relative_to(root)
    except ValueError:
        return False

    if path_is_forbidden(cand):
        return False
    if cand.exists() and not cand.is_file():
        return False

    try:
        payload = content.encode("utf-8")
    except (UnicodeEncodeError, TypeError):
        return False
    if len(payload) > _WRITE_MAX_BYTES:
        return False

    backup_path = cand.with_name(cand.name + ".bak")
    had_prior = cand.is_file()
    if had_prior:
        try:
            shutil.copy2(cand, backup_path)
        except OSError:
            return False

    tmp_path = cand.with_name(cand.name + _WRITE_TMP_SUFFIX)
    try:
        cand.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_bytes(payload)
        os.replace(tmp_path, cand)
        return True
    except OSError:
        if tmp_path.is_file():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        if had_prior and backup_path.is_file():
            try:
                shutil.copy2(backup_path, cand)
            except OSError:
                pass
        return False


def build_local_tools_context(message: str, workspace_root: str | None) -> str:
    """
    LLM kullanıcı yüküne eklenecek blok.
    ENABLE_LOCAL_TOOLS=0 ile tamamen kapatılır.
    """
    if os.environ.get("ENABLE_LOCAL_TOOLS", "1").strip() in ("0", "false", "no"):
        return ""

    parts: list[str] = []

    if os.environ.get("LOCAL_TOOLS_DATETIME", "1").strip() not in ("0", "false", "no"):
        parts.append(_now_block())

    hn = _hostname_block()
    if hn.strip():
        parts.append("=== Yerel araç: ortam ===\n" + hn)

    root_hint = (workspace_root or os.environ.get("LOCAL_TOOLS_ROOT", "") or "").strip()
    if (
        root_hint
        and os.environ.get("LOCAL_TOOLS_FILE_SNIPPET", "1").strip()
        not in ("0", "false", "no")
    ):
        root = Path(root_hint)
        if root.is_dir():
            rels = extract_at_paths(message)
            max_one = max(500, int(os.environ.get("LOCAL_TOOLS_FILE_MAX_CHARS", "6000")))
            total_cap = max_one * 3
            try:
                total_cap = int(os.environ.get("LOCAL_TOOLS_FILES_TOTAL_MAX_CHARS", str(total_cap)))
            except ValueError:
                pass
            used = 0
            blocks: list[str] = []
            for rel in rels:
                if used >= total_cap:
                    blocks.append("[Toplam dosya kotası doldu — daha az @@ dosya veya kotayı artırın.]")
                    break
                budget = min(max_one, total_cap - used)
                if budget < 200:
                    break
                body, err = safe_read_file_under_root(root, rel, budget)
                if err:
                    blocks.append(f"[@@{rel}] Okunamadı: {err}")
                    continue
                chunk = f"[@@{rel} — çalışma kökünden okunan metin]\n{body}"
                used += len(chunk)
                blocks.append(chunk)
            if blocks:
                parts.append("=== Yerel araç: dosya özütleri ===\n" + "\n\n".join(blocks))

    if not parts:
        return ""

    tail = (
        "[TALİMAT — YEREL ARAÇ]\n"
        "Üstteki **Yerel araç** blokları gerçek sistem verisidir. "
        "Tarih/gün/saat sorularında bunları kullan; tahmini tarih uydurma. "
        "**@@ ile eklenen dosya** parçaları kullanıcının açıkça bağladığı metindir.\n"
    )
    return "\n\n".join(parts) + "\n\n" + tail

