# Created by Ümit & Gökçenur
"""Wake-on-LAN yardımcı (plan 11 §7). Magic packet gönderir; NIC BIOS/Windows açık olmalı."""

from __future__ import annotations

import os
import re
import socket
from typing import Any

VERSION = "wol-v1-2026-11-09"
_MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}([:\-]?)){5}[0-9A-Fa-f]{2}$")


def normalize_mac(mac: str) -> str:
    s = re.sub(r"[^0-9A-Fa-f]", "", mac or "")
    if len(s) != 12:
        raise ValueError("MAC 12 hex olmalı")
    return s.upper()


def build_magic_packet(mac: str) -> bytes:
    clean = normalize_mac(mac)
    mac_bytes = bytes.fromhex(clean)
    return b"\xff" * 6 + mac_bytes * 16


def send_wol(
    mac: str,
    *,
    broadcast: str | None = None,
    port: int = 9,
) -> dict[str, Any]:
    """
    Magic packet UDP broadcast.
    Varsayılan MAC: RUZGAR_WOL_MAC veya Ethernet F4-B5-20-74-6C-87 (bu PC ölçümü).
    """
    mac = (mac or os.environ.get("RUZGAR_WOL_MAC") or "").strip()
    if not mac:
        return {"ok": False, "error": "MAC yok — RUZGAR_WOL_MAC veya parametre"}
    try:
        pkt = build_magic_packet(mac)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    bcast = (broadcast or os.environ.get("RUZGAR_WOL_BCAST") or "255.255.255.255").strip()
    port = int(os.environ.get("RUZGAR_WOL_PORT", str(port)) or port)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(pkt, (bcast, port))
    except OSError as e:
        return {"ok": False, "error": f"gönderilemedi: {e}", "version": VERSION}
    return {
        "ok": True,
        "mac": normalize_mac(mac),
        "broadcast": bcast,
        "port": port,
        "version": VERSION,
        "note": "PC kapalıysa BIOS WoL + Windows «Hızlı başlangıç kapalı» önerilir.",
    }


def default_mac_hint() -> str:
    return (os.environ.get("RUZGAR_WOL_MAC") or "F4-B5-20-74-6C-87").strip()
