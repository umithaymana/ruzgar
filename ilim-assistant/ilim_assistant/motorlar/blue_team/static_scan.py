# Created by Ümit & Gökçenur
"""
Statik analiz — PE/ELF başlık okuma + metin tabanlı imza (YARA-benzeri, savunma).

Kurallar yalnızca tespit içindir; zararlı yazılım üretmez / çalıştırmaz.
"""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path
from typing import Any

_SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def _max_severity(a: str, b: str) -> str:
    return a if _SEVERITY_RANK.get(a, 0) >= _SEVERITY_RANK.get(b, 0) else b


def parse_pe_header(data: bytes) -> dict[str, Any] | None:
    """MZ/PE başlığını salt okunur çözümle (saldırı yok)."""
    if len(data) < 64 or data[:2] != b"MZ":
        return None
    try:
        pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    except struct.error:
        return {"magic": "MZ", "pe_valid": False, "note": "e_lfanew okunamadı"}
    if pe_off < 0 or pe_off + 24 > len(data):
        return {"magic": "MZ", "pe_valid": False, "note": "PE offset sınır dışı"}
    if data[pe_off : pe_off + 4] != b"PE\x00\x00":
        return {"magic": "MZ", "pe_valid": False, "note": "PE imzası yok"}
    machine = struct.unpack_from("<H", data, pe_off + 4)[0]
    num_sections = struct.unpack_from("<H", data, pe_off + 6)[0]
    characteristics = struct.unpack_from("<H", data, pe_off + 22)[0]
    return {
        "magic": "MZ",
        "pe_valid": True,
        "machine": machine,
        "sections": num_sections,
        "characteristics": characteristics,
        "dll": bool(characteristics & 0x2000),
        "executable": bool(characteristics & 0x2),
    }


def parse_elf_header(data: bytes) -> dict[str, Any] | None:
    if len(data) < 16 or data[:4] != b"\x7fELF":
        return None
    return {
        "magic": "ELF",
        "class": data[4],  # 1=32, 2=64
        "endian": data[5],
        "osabi": data[7],
    }


class StaticSignatureScanner:
    """JSON kurallarıyla metin/bayt kalıbı tarayıcı (YARA-benzeri sade mantık)."""

    def __init__(self, rules_path: Path | str | None = None) -> None:
        self.rules: list[dict[str, Any]] = []
        if rules_path:
            self.load_rules(Path(rules_path))

    def load_rules(self, path: Path) -> None:
        if not path.is_file():
            self.rules = []
            return
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.rules = list(raw.get("rules") or [])

    def scan_path(self, path: Path | str, *, max_bytes: int = 2 * 1024 * 1024) -> dict[str, Any]:
        p = Path(path)
        out: dict[str, Any] = {
            "path": str(p),
            "suspicious": False,
            "severity": "clean",
            "matches": [],
            "headers": {},
        }
        if not p.is_file():
            out["error"] = "dosya yok"
            return out
        try:
            data = p.read_bytes()[:max_bytes]
        except OSError as exc:
            out["error"] = str(exc)
            return out

        pe = parse_pe_header(data[:4096])
        elf = parse_elf_header(data[:64])
        if pe:
            out["headers"]["pe"] = pe
        if elf:
            out["headers"]["elf"] = elf

        # Metin katmanı (UTF-8 hatalı baytları yok say)
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

        matches: list[dict[str, Any]] = []
        sev = "clean"
        for rule in self.rules:
            rid = str(rule.get("id") or "rule")
            severity = str(rule.get("severity") or "medium")
            desc = str(rule.get("description") or "")
            hit = False
            for pat in rule.get("strings") or []:
                s = str(pat)
                if not s:
                    continue
                if s.startswith("re:"):
                    try:
                        if re.search(s[3:], text, re.I | re.M):
                            hit = True
                            break
                    except re.error:
                        continue
                elif s.startswith("hex:"):
                    try:
                        hx = bytes.fromhex(s[4:].replace(" ", ""))
                        if hx and hx in data:
                            hit = True
                            break
                    except ValueError:
                        continue
                else:
                    if s.lower() in text.lower() or s.encode("utf-8", errors="ignore") in data:
                        hit = True
                        break
            if hit:
                matches.append({"id": rid, "severity": severity, "description": desc})
                sev = _max_severity(sev, severity) if sev != "clean" else severity

        # Başlık anomalileri (savunma ipucu)
        if pe and pe.get("pe_valid") and p.suffix.lower() in {
            ".txt",
            ".md",
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".html",
            ".htm",
            ".json",
            ".csv",
        }:
            matches.append(
                {
                    "id": "pe_in_document_ext",
                    "severity": "critical",
                    "description": "Belge uzantısında geçerli PE başlığı",
                }
            )
            sev = "critical"

        out["matches"] = matches
        out["suspicious"] = bool(matches)
        out["severity"] = sev if matches else "clean"
        return out


def scan_file_static(
    path: Path | str,
    rules_path: Path | str | None = None,
) -> dict[str, Any]:
    from . import default_rules_path

    scanner = StaticSignatureScanner(rules_path or default_rules_path())
    return scanner.scan_path(path)
