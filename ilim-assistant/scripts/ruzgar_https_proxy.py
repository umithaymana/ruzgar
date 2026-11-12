# Created by Ümit & Gökçenur
"""Mobil mikrofon için TLS köprüsü: https://0.0.0.0:8443 → http://127.0.0.1:8779

Telefonda http://100.x mikrofonu keser; bu proxy güvenli bağlam sağlar
(self-signed uyarıyı bir kez «Gelişmiş → devam» ile geçmek gerekir).
"""
from __future__ import annotations

import argparse
import asyncio
import ssl
from pathlib import Path

DEFAULT_CERT = Path(__file__).resolve().parents[1] / ".ruzgar" / "certs" / "ruzgar-mobil.crt"
DEFAULT_KEY = Path(__file__).resolve().parents[1] / ".ruzgar" / "certs" / "ruzgar-mobil.key"


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
    print(f"[https-proxy] listening {addrs} → http://{args.upstream_host}:{args.upstream_port}", flush=True)
    async with server:
        await server.serve_forever()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8443)
    p.add_argument("--upstream-host", default="127.0.0.1")
    p.add_argument("--upstream-port", type=int, default=8779)
    p.add_argument("--cert", default=str(DEFAULT_CERT))
    p.add_argument("--key", default=str(DEFAULT_KEY))
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
