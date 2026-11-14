#!/usr/bin/env python3
"""Faz 5 — Blender ile basit kutu bina glTF üret (headless)."""
from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

OUT = Path(r"D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz\models")
OUT.mkdir(parents=True, exist_ok=True)
BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe")
SCRIPT = OUT / "_export_box.py"
GLTF = OUT / "ornek_bina.glb"


def main() -> None:
    if not BLENDER.is_file():
        print("FAIL: blender yok", BLENDER)
        raise SystemExit(1)
    SCRIPT.write_text(
        textwrap.dedent(
            """
            import bpy
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
            obj = bpy.context.active_object
            obj.scale = (6, 4, 3)
            bpy.ops.object.transform_apply(scale=True)
            bpy.ops.export_scene.gltf(filepath=r"%s", export_format="GLB")
            """
            % str(GLTF).replace("\\", "\\\\")
        ),
        encoding="utf-8",
    )
    r = subprocess.run(
        [str(BLENDER), "-b", "-P", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    ok = GLTF.is_file() and GLTF.stat().st_size > 100
    print(json.dumps({"ok": ok, "glb": str(GLTF), "code": r.returncode}, ensure_ascii=False))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
