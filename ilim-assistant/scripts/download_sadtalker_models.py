"""SadTalker model indirici — Windows yol/bosluk guvenli."""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

MODELS = [
    (
        "SadTalker_V0.0.2_256.safetensors",
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors",
        700_000_000,
    ),
    (
        "mapping_00109-model.pth.tar",
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar",
        150_000_000,
    ),
    (
        "mapping_00229-model.pth.tar",
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar",
        150_000_000,
    ),
]


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    if tmp.exists():
        tmp.unlink()
    print(f"Indiriliyor: {dest.name}")
    req = urllib.request.Request(url, headers={"User-Agent": "Ruzgar/1.0"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        chunk = 1024 * 1024
        with tmp.open("wb") as f:
            while True:
                block = resp.read(chunk)
                if not block:
                    break
                f.write(block)
                done += len(block)
                if total:
                    pct = done * 100 // total
                    if done % (10 * chunk) == 0 or done == total:
                        print(f"  {pct}% ({done // (1024*1024)} MB)")
    tmp.replace(dest)
    print(f"Tamam: {dest.name} ({dest.stat().st_size // (1024*1024)} MB)")


def main() -> int:
    ckpt = Path(sys.argv[1]).resolve()
    ckpt.mkdir(parents=True, exist_ok=True)
    for name, url, min_bytes in MODELS:
        dest = ckpt / name
        if dest.is_file() and dest.stat().st_size >= min_bytes:
            print(f"Atlandi (mevcut): {name}")
            continue
        if dest.is_file():
            dest.unlink()
        download(url, dest)
        if dest.stat().st_size < min_bytes:
            print(f"HATA: eksik dosya {name}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
