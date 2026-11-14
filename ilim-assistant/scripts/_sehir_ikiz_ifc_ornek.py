#!/usr/bin/env python3
"""Faz 6 — IfcOpenShell duman: örnek IFC oku veya minimal oluştur."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(r"D:\ÜMİT\14-) PROGRAMLAR\RuzgarSehirIkiz\models")
OUT.mkdir(parents=True, exist_ok=True)
IFC_PATH = OUT / "ornek_bina.ifc"


def main() -> None:
    try:
        import ifcopenshell
        import ifcopenshell.api
    except Exception as ex:
        print(json.dumps({"ok": False, "error": f"ifcopenshell yok: {ex}"}))
        raise SystemExit(1)

    # Minimal IFC4 project
    f = ifcopenshell.file(schema="IFC4")
    project = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcProject", name="RuzgarPilot")
    ifcopenshell.api.run("unit.assign_unit", f)
    context = ifcopenshell.api.run("context.add_context", f, context_type="Model")
    body = ifcopenshell.api.run(
        "context.add_context",
        f,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=context,
    )
    site = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcSite", name="PilotSite")
    building = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcBuilding", name="PilotBina")
    ifcopenshell.api.run("aggregate.assign_object", f, relating_object=project, products=[site])
    ifcopenshell.api.run("aggregate.assign_object", f, relating_object=site, products=[building])
    # basit blok temsil
    matrix = None
    try:
        import numpy as np
        from ifcopenshell.util.placement import a2p

        matrix = a2p(np.array([0.0, 0.0, 0.0]), np.array([0, 0, 1.0]), np.array([1.0, 0, 0]))
    except Exception:
        pass
    if matrix is not None:
        ifcopenshell.api.run("geometry.add_slab_representation", f, context=body, depth=0.2)
    f.write(str(IFC_PATH))
    # yeniden aç duman
    g = ifcopenshell.open(str(IFC_PATH))
    print(
        json.dumps(
            {
                "ok": True,
                "path": str(IFC_PATH),
                "schema": g.schema,
                "by_type_building": len(list(g.by_type("IfcBuilding"))),
                "version": getattr(ifcopenshell, "version", "?"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
