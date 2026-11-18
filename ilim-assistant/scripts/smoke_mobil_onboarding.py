# Created by Ümit & Gökçenur
"""Dar smoke — mobil onboarding sadeleştirme (2026-11-18).

Kontrol: erisim friend_guide / mimar_invite / cert_kind,
register→status poll, approve→login_ready, SW CACHE bump, LE cert dosyası.
Sunucu ayaktaysa HTTP; değilse saf dosya/modül.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IA = ROOT / "ilim-assistant"
PWA = IA / "static" / "mobil-pwa"
CERTS = IA / ".ruzgar" / "certs"
MARKER = "mobil-oturum-v3e-onboard-2026-11-18"
PORT = 8779


def _get(path: str, timeout: float = 4.0) -> dict:
    url = f"http://127.0.0.1:{PORT}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(path: str, body: dict, timeout: float = 6.0) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    failed = 0
    print("=== smoke_mobil_onboarding ===")

    # Dosya işaretleri
    oturum = (IA / "ilim_assistant" / "ruzgar_mobil_oturum.py").read_text(encoding="utf-8")
    if MARKER not in oturum:
        print("FAIL marker", MARKER)
        failed += 1
    else:
        print("OK marker", MARKER)

    sw = (PWA / "sw.js").read_text(encoding="utf-8")
    if "ruzgar-pwa-v20261118-onboard" not in sw or "SKIP_WAITING" not in sw:
        print("FAIL sw bump/skipWaiting")
        failed += 1
    else:
        print("OK sw network-first + skipWaiting")

    app_js = (PWA / "app.js").read_text(encoding="utf-8")
    for needle in ("startRegPoll", "paintPanelInvite", "paintFriendGuide", "SKIP_WAITING"):
        if needle not in app_js:
            print("FAIL app.js missing", needle)
            failed += 1
        else:
            print("OK app.js", needle)

    le = CERTS / "tailscale-le.crt"
    ss = CERTS / "ruzgar-mobil.crt"
    if le.is_file() and le.stat().st_size > 100:
        print("OK cert LE", le.name, le.stat().st_size)
    else:
        print("WARN cert LE yok — self-signed fallback beklenir")
    if ss.is_file():
        print("OK cert SS yedek var")

    proxy = (IA / "scripts" / "ruzgar_https_proxy.py").read_text(encoding="utf-8")
    if "tailscale-le" not in proxy or "_prefer_cert_paths" not in proxy:
        print("FAIL proxy LE prefer")
        failed += 1
    else:
        print("OK proxy LE prefer")

    # Modül birim
    sys.path.insert(0, str(IA))
    from ilim_assistant import ruzgar_mobil_oturum as mo

    if mo.VERSION != MARKER:
        print("FAIL version", mo.VERSION)
        failed += 1
    else:
        print("OK version import")

    # Canlı API (opsiyonel)
    live = False
    try:
        er = _get("/api/mobil/erisim")
        live = True
        if not er.get("friend_guide") or not er.get("mimar_invite"):
            print("FAIL erisim guide/invite", list(er.keys())[:12])
            failed += 1
        else:
            print("OK erisim friend_guide + mimar_invite")
            print("  sticky", (er.get("sticky_urls") or [None])[0])
            print("  cert_kind", er.get("cert_kind"))
            print("  invite", (er.get("mimar_invite") or {}).get("admin_users_url"))
        if er.get("cert_kind") not in ("tailscale_le", "self_signed", "none"):
            print("FAIL cert_kind", er.get("cert_kind"))
            failed += 1

        # register → waiting → approve → status approved (geçici kullanıcı)
        uname = f"smoke_ob_{__import__('time').time_ns() % 100000}"
        reg = _post(
            "/api/mobil/register",
            {
                "ad": "Smoke",
                "soyad": "Onboard",
                "telefon": "",
                "kullanici": uname,
                "sifre": "smoke1234",
            },
        )
        if not reg.get("ok") or not reg.get("pending_id"):
            print("FAIL register", reg)
            failed += 1
        else:
            pid = reg["pending_id"]
            code = reg["code"]
            st = _get(f"/api/mobil/register/status?pending_id={pid}")
            if st.get("status") != "waiting":
                print("FAIL status waiting", st)
                failed += 1
            else:
                print("OK status waiting")
            ap = _post(
                "/api/mobil/approve",
                {"pending_id": pid, "code": code, "approve": True},
            )
            if not ap.get("ok") or ap.get("status") != "approved":
                print("FAIL approve", ap)
                failed += 1
            else:
                print("OK approve login_ready", ap.get("login_ready"))
            st2 = _get(f"/api/mobil/register/status?pending_id={pid}")
            if st2.get("status") != "approved" or not st2.get("login_ready"):
                print("FAIL status approved", st2)
                failed += 1
            else:
                print("OK poll approved → girişe geç")
            login = _post(
                "/api/mobil/login",
                {
                    "kullanici": uname,
                    "sifre": "smoke1234",
                    "device_name": "smoke",
                    "device_kind": "telefon",
                },
            )
            if not login.get("ok") or not login.get("token"):
                print("FAIL login after approve", login)
                failed += 1
            else:
                print("OK soft login after approve")
    except urllib.error.URLError as e:
        print("WARN live API yok — dosya kontrolleri yeterli", str(e)[:120])
    except Exception as e:
        print("FAIL live", str(e)[:200])
        failed += 1

    if failed:
        print("SMOKE_FAIL mobil_onboarding", failed, "live" if live else "offline")
        return 1
    print("SMOKE_OK mobil_onboarding", "live" if live else "offline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
