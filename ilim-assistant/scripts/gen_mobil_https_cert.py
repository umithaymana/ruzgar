# Created by Ümit & Gökçenur
"""Mobil HTTPS köprüsü sertifikası.

1) Tercih: `tailscale cert <MagicDNS>` → Let's Encrypt (tarayıcı uyarısı yok)
2) Yedek: self-signed DNS+IP SAN (Gelişmiş/Devam bir kez)

Aşama D+sabit: MagicDNS hostname — LAN IP değişince sticky host kalır.
"""
from __future__ import annotations

import ipaddress
import json
import re
import socket
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

CERT_DIR = Path(__file__).resolve().parents[1] / ".ruzgar" / "certs"
STICKY = Path(__file__).resolve().parents[1] / ".ruzgar" / "mobil_sticky_host.json"
LE_CRT = CERT_DIR / "tailscale-le.crt"
LE_KEY = CERT_DIR / "tailscale-le.key"
SS_CRT = CERT_DIR / "ruzgar-mobil.crt"
SS_KEY = CERT_DIR / "ruzgar-mobil.key"
META = CERT_DIR / "cert_kind.json"


def _tailscale_magicdns() -> tuple[set[str], set[str]]:
    dns: set[str] = set()
    ips: set[str] = set()
    if STICKY.is_file():
        try:
            cur = json.loads(STICKY.read_text(encoding="utf-8"))
            h = str(cur.get("magicdns") or cur.get("host") or "").strip().lower().rstrip(".")
            if h:
                dns.add(h)
            tip = str(cur.get("ts_ip") or "").strip()
            if tip.startswith("100."):
                ips.add(tip)
        except Exception:
            pass
    try:
        out = subprocess.check_output(
            ["tailscale", "status", "--json"],
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=6,
        )
        data = json.loads(out)
        self_node = data.get("Self") or {}
        name = str(self_node.get("DNSName") or "").strip().rstrip(".").lower()
        if name:
            dns.add(name)
        for a in self_node.get("TailscaleIPs") or []:
            if str(a).startswith("100."):
                ips.add(str(a))
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["tailscale", "dns", "status"],
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=6,
        )
        m = re.search(r"reach this device at\s+([a-z0-9.-]+\.ts\.net)", out, re.I)
        if m:
            dns.add(m.group(1).strip().lower())
    except Exception:
        pass
    return dns, ips


def _write_meta(kind: str, host: str = "") -> None:
    try:
        CERT_DIR.mkdir(parents=True, exist_ok=True)
        META.write_text(
            json.dumps(
                {
                    "kind": kind,
                    "host": host,
                    "le_crt": str(LE_CRT.name),
                    "ss_crt": str(SS_CRT.name),
                    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def try_tailscale_le(hosts: set[str]) -> str | None:
    """Let’s Encrypt via Tailscale. Başarılıysa host adını döner."""
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    for host in sorted(h for h in hosts if h.endswith(".ts.net")):
        try:
            subprocess.check_call(
                [
                    "tailscale",
                    "cert",
                    "--cert-file",
                    str(LE_CRT),
                    "--key-file",
                    str(LE_KEY),
                    host,
                ],
                timeout=90,
            )
            if LE_CRT.is_file() and LE_KEY.is_file() and LE_CRT.stat().st_size > 100:
                _write_meta("tailscale_le", host)
                print("OK_LE", LE_CRT)
                print("HOST", host)
                return host
        except Exception as exc:
            print("WARN_LE", host, str(exc)[:160])
    return None


def write_self_signed(dns: set[str], ips: set[str], cn: str) -> None:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    san_list: list[x509.GeneralName] = [x509.DNSName(d) for d in sorted(dns)]
    san_list += [x509.IPAddress(ipaddress.ip_address(ip)) for ip in sorted(ips)]
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(key, hashes.SHA256())
    )
    SS_KEY.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    pem_cert = cert.public_bytes(serialization.Encoding.PEM)
    SS_CRT.write_bytes(pem_cert)
    (CERT_DIR / "ruzgar-mobil.cer").write_bytes(pem_cert)
    _write_meta("self_signed", cn)
    print("OK_SS", CERT_DIR)
    print("CN", cn)
    print("DNS", sorted(dns))
    print("IPS", sorted(ips))


def main() -> None:
    ips = {"127.0.0.1"}
    dns = {"localhost", "ruzgar-mobil.local"}
    try:
        dns.add(socket.gethostname().lower())
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip and not str(ip).startswith("127."):
                ips.add(str(ip))
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        rip = s.getsockname()[0]
        s.close()
        if rip and not str(rip).startswith("127."):
            ips.add(str(rip))
    except Exception:
        pass
    try:
        if sys.platform.startswith("win"):
            out = subprocess.check_output(
                ["ipconfig"], text=True, encoding="oem", errors="ignore", timeout=8
            )
            for m in re.finditer(r"IPv4[^:]*:\s*([0-9.]+)", out, re.I):
                ip = m.group(1).strip()
                if ip and not ip.startswith("127."):
                    ips.add(ip)
    except Exception:
        pass

    ts_dns, ts_ips = _tailscale_magicdns()
    dns |= ts_dns
    ips |= ts_ips

    le_host = try_tailscale_le(ts_dns)
    # Self-signed her zaman yedek (LE yoksa / IP ile açılış)
    cn = sorted(ts_dns)[0] if ts_dns else "ruzgar-mobil.local"
    write_self_signed(dns, ips, cn)
    if le_host:
        print("PREFER", "tailscale_le", f"https://{le_host}:8443/mobil/")
        print("STICKY", f"https://{le_host}:8443/mobil/")
    elif ts_dns:
        print("PREFER", "self_signed")
        print("STICKY", f"https://{sorted(ts_dns)[0]}:8443/mobil/")
        print("HINT", "İlk açılışta Gelişmiş → Devam (self-signed)")
    else:
        print("PREFER", "self_signed")
        print("HINT", "MagicDNS yok — Tailscale açık mı?")


if __name__ == "__main__":
    main()
