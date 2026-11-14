# Created by Ümit & Gökçenur
"""Mobil HTTPS köprüsü için self-signed sertifika (DNS + IP SAN)."""
from __future__ import annotations

import ipaddress
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

CERT_DIR = Path(__file__).resolve().parents[1] / ".ruzgar" / "certs"


def main() -> None:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
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
    for extra in ("192.168.1.105", "100.119.194.31"):
        ips.add(extra)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "ruzgar-mobil.local")]
    )
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

    (CERT_DIR / "ruzgar-mobil.key").write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    pem_cert = cert.public_bytes(serialization.Encoding.PEM)
    (CERT_DIR / "ruzgar-mobil.crt").write_bytes(pem_cert)
    (CERT_DIR / "ruzgar-mobil.cer").write_bytes(pem_cert)
    print("OK", CERT_DIR)
    print("DNS", sorted(dns))
    print("IPS", sorted(ips))


if __name__ == "__main__":
    main()
