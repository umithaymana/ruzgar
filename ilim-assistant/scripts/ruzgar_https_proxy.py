# Created by Ümit & Gökçenur
"""Mobil mikrofon için TLS köprüsü: https://0.0.0.0:8443 → http://127.0.0.1:8779

Telefonda http://100.x mikrofonu keser; bu proxy güvenli bağlam sağlar.
Tercih: Tailscale Let's Encrypt (uyarı yok). Yedek: self-signed
(«Gelişmiş → devam» bir kez).
"""
from __future__ import annotations

import argparse
import asyncio
import ssl
from pathlib import Path

_CERT_DIR = Path(__file__).resolve().parents[1] / ".ruzgar" / "certs"
_LE_CERT = _CERT_DIR / "tailscale-le.crt"
_LE_KEY = _CERT_DIR / "tailscale-le.key"
_SS_CERT = _CERT_DIR / "ruzgar-mobil.crt"
_SS_KEY = _CERT_DIR / "ruzgar-mobil.key"


def _prefer_cert_paths() -> tuple[Path, Path, str]:
    if _LE_CERT.is_file() and _LE_KEY.is_file():
        return _LE_CERT, _LE_KEY, "tailscale_le"
    return _SS_CERT, _SS_KEY, "self_signed"


_pref_c, _pref_k, _pref_kind = _prefer_cert_paths()
DEFAULT_CERT = _pref_c
DEFAULT_KEY = _pref_k
DEFAULT_CERT_KIND = _pref_kind


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError, OSError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def _handle(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    upstream_host: str,
    upstream_port: int,
) -> None:
    try:
        up_reader, up_writer = await asyncio.open_connection(upstream_host, upstream_port)
    except OSError as e:
        client_writer.close()
        try:
            await client_writer.wait_closed()
        except Exception:
            pass
        print(f"[https-proxy] upstream fail: {e}", flush=True)
        return
    await asyncio.gather(
        _pipe(client_reader, up_writer),
        _pipe(up_reader, client_writer),
    )


async def main_async(args: argparse.Namespace) -> None:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(args.cert, args.key)
    server = await asyncio.start_server(
        lambda r, w: _handle(r, w, args.upstream_host, args.upstream_port),
        host=args.host,
        port=args.port,
        ssl=ctx,
    )
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets or [])
    kind = getattr(args, "cert_kind", DEFAULT_CERT_KIND)
    print(
        f"[https-proxy] listening {addrs} → http://{args.upstream_host}:{args.upstream_port}"
        f" cert={kind} file={args.cert}",
        flush=True,
    )
    async with server:
        await server.serve_forever()


def main() -> None:
    pref_c, pref_k, pref_kind = _prefer_cert_paths()
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8443)
    p.add_argument("--upstream-host", default="127.0.0.1")
    p.add_argument("--upstream-port", type=int, default=8779)
    p.add_argument("--cert", default=str(pref_c))
    p.add_argument("--key", default=str(pref_k))
    args = p.parse_args()
    # Argüman self-signed verse bile LE varsa ve arg default SS ise LE'ye kay (çağıran açık path verdiyse koru)
    args.cert_kind = pref_kind
    if Path(args.cert).resolve() == _SS_CERT.resolve() and pref_kind == "tailscale_le":
        args.cert = str(pref_c)
        args.key = str(pref_k)
        args.cert_kind = "tailscale_le"
    elif "tailscale-le" in str(args.cert).replace("\\", "/").lower():
        args.cert_kind = "tailscale_le"
    elif "ruzgar-mobil" in str(args.cert).replace("\\", "/").lower():
        args.cert_kind = "self_signed"
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
