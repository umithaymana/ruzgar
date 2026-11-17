# Created by Ümit & Gökçenur
"""Dilim 0 — Motor bağ envanteri: hub / tek yüz / anlık / boot / yetim.

Çıkış: her motor için bag_sinifi + kanıt. 0 hata = yeşil.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from ilim_assistant.ana_motor_faz6c_tek_yuz import (
        enrich_orchestra_faz6c,
        faz6c_enabled,
    )
    from ilim_assistant.ana_motor_faz_e_tek_yuz import (
        enrich_orchestra_faz_e,
        faz_e_enabled,
    )
    from ilim_assistant.ana_motor_faz_ses_tek_yuz import (
        enrich_orchestra_faz_ses,
        faz_ses_enabled,
    )
    from ilim_assistant.ana_motor_faz_hafiza_tek_yuz import (
        enrich_orchestra_faz_hafiza,
        faz_hafiza_enabled,
    )
    from ilim_assistant.ana_motor_faz_mimar_tek_yuz import (
        enrich_orchestra_faz_mimar,
        faz_mimar_enabled,
    )
    from ilim_assistant.ana_motor_faz_hizir_tek_yuz import (
        enrich_orchestra_faz_hizir,
        faz_hizir_enabled,
    )
    from ilim_assistant.motorlar.ana_motor_hub_faz76 import resolve_hub_target
    from ilim_assistant.motorlar.ruzgar_cekirdegi import (
        ARA_MOTOR_BOOT_ORDER,
        HUB_DISI_YARDIMCILAR,
        HUB_MOTOR_IDS,
        cekirdek_envanter,
    )
    from ilim_assistant.ruzgar_oz_bilgi import MOTOR_KARTLARI, motor_kartlari
    from ilim_assistant.ruzgar_orkestrasyon_faz_c import build_genel_orchestra_preview

    fails = 0
    rows: list[dict] = []

    env = cekirdek_envanter()
    hub = set(env.get("hub_motors") or [])
    boot = list(env.get("ara_motor_boot_order") or [])
    assert boot == list(ARA_MOTOR_BOOT_ORDER), boot
    assert list(HUB_MOTOR_IDS) == list(hub) or set(HUB_MOTOR_IDS) == hub

    # Tek yüz kanıtları
    orch6, patch6 = build_genel_orchestra_preview(
        "görev: smoke-live-test health endpointine version ekle"
    )
    ua6 = (orch6.get("ui_action") or {}) if isinstance(orch6, dict) else {}
    tek_yuz_programlama = (
        faz6c_enabled()
        and (
            ua6.get("motor") == "programlama"
            or patch6.get("faz6c")
            or enrich_orchestra_faz6c({}, "görev: x.py pytest geçir").get("faz6c")
        )
    )

    orch_e, patch_e = build_genel_orchestra_preview(
        "şu videoyu indir https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    ua_e = (orch_e.get("ui_action") or {}) if isinstance(orch_e, dict) else {}
    tek_yuz_video = faz_e_enabled() and (
        ua_e.get("motor") == "video" or patch_e.get("faz_e")
    )
    orch_t = enrich_orchestra_faz_e(
        {}, "altyazilar/ornek.srt dosyasını İngilizceye çevir"
    )
    tek_yuz_tercume = faz_e_enabled() and (orch_t.get("ui_action") or {}).get(
        "motor"
    ) == "tercume"
    orch_s = enrich_orchestra_faz_ses({}, "seste: Dilim0 ses kanıt metni")
    tek_yuz_ses = faz_ses_enabled() and (orch_s.get("ui_action") or {}).get(
        "motor"
    ) == "ses"
    orch_h = enrich_orchestra_faz_hafiza({}, "hafızada: Dilim0 hafıza kanıt")
    tek_yuz_hafiza = faz_hafiza_enabled() and (orch_h.get("ui_action") or {}).get(
        "motor"
    ) == "hafiza"
    orch_m = enrich_orchestra_faz_mimar({}, "mimarda: Dilim0 mimar kanıt")
    tek_yuz_mimar = faz_mimar_enabled() and (orch_m.get("ui_action") or {}).get(
        "motor"
    ) == "mimar"
    orch_hz = enrich_orchestra_faz_hizir({}, "hizirda: Dilim0 hizir kanıt")
    tek_yuz_hizir = faz_hizir_enabled() and (orch_hz.get("ui_action") or {}).get(
        "motor"
    ) == "hizir"

    # Hub niyet örnekleri
    hub_hits = {
        "programlama": resolve_hub_target("pytest geçir")[0],
        "video": resolve_hub_target("şu youtube videosunu indir")[0],
        "ses": resolve_hub_target("alim moduna geç")[0],
        "hafiza": resolve_hub_target("bunu hatırla: dilim0 test")[0],
        "mimar": resolve_hub_target("fotoğraf paneli aç")[0],
        "tercume": resolve_hub_target("tercüme paneline geç")[0],
        "hizir": resolve_hub_target("pazar yerini tara")[0],
        "genel_ilim": resolve_hub_target("fotosentez nedir")[0],
    }

    print("=== Dilim 0 motor bağ envanteri ===")
    print(f"cekirdek={env.get('version')} faz6c={faz6c_enabled()} faz_e={faz_e_enabled()}")
    print(f"hub={list(HUB_MOTOR_IDS)}")
    print(f"boot={boot}")
    print()

    catalog2 = [
        {
            "id": "ana",
            "hub": True,
            "boot": "ilk",
            "tek_yuz": False,
            "hub_ornek": True,
            "note": "omurga",
        },
        {
            "id": "ses",
            "hub": "ses" in hub,
            "boot": "ses" in boot,
            "tek_yuz": bool(tek_yuz_ses),
            "hub_ornek": hub_hits["ses"] in ("ses", "genel"),
            "note": "faz72 anlık + dilim1 tek yüz",
        },
        {
            "id": "video",
            "hub": "video" in hub,
            "boot": "video" in boot,
            "tek_yuz": bool(tek_yuz_video),
            "hub_ornek": hub_hits["video"] in ("video", "genel"),
            "note": "Faz E",
        },
        {
            "id": "okuma",
            "hub": False,
            "boot": "okuma" in boot,
            "tek_yuz": False,
            "hub_ornek": hub_hits["genel_ilim"] == "genel",
            "note": "kasten kısmi (ilim→genel)",
        },
        {
            "id": "mimar",
            "hub": "mimar" in hub,
            "boot": "mimar" in boot,
            "tek_yuz": bool(tek_yuz_mimar),
            "hub_ornek": hub_hits["mimar"] in ("mimar", "genel"),
            "note": "dilim3 tek yüz; ilim kaçmaz",
        },
        {
            "id": "tercume",
            "hub": "tercume" in hub,
            "boot": "tercume" in boot,
            "tek_yuz": bool(tek_yuz_tercume),
            "hub_ornek": True,
            "note": "Faz E",
        },
        {
            "id": "hafiza",
            "hub": "hafiza" in hub,
            "boot": "hafiza" in boot,
            "tek_yuz": bool(tek_yuz_hafiza),
            "hub_ornek": hub_hits["hafiza"] in ("hafiza", "genel"),
            "note": "dilim2 tek yüz; hatırla çalmaz",
        },
        {
            "id": "programlama",
            "hub": "programlama" in hub,
            "boot": "programlama" in boot,
            "tek_yuz": bool(tek_yuz_programlama),
            "hub_ornek": hub_hits["programlama"] in ("programlama", "genel"),
            "note": "6c",
        },
        {
            "id": "hizir",
            "hub": "hizir" in hub,
            "boot": False,
            "tek_yuz": bool(tek_yuz_hizir),
            "hub_ornek": hub_hits["hizir"] in ("hizir", "genel"),
            "note": "dilim8 tek yüz; pazar API yok",
        },
        {
            "id": "gelisim",
            "hub": False,
            "boot": False,
            "tek_yuz": False,
            "hub_ornek": None,
            "note": "yetim/hub_disi",
        },
    ]

    for r in catalog2:
        mid = r["id"]
        if mid == "ana":
            bag = "omurga"
        elif mid == "okuma":
            bag = "kismi_kasten"
        elif mid == "gelisim":
            bag = "yetim_hub_disi"
        elif r["hub"] and r["tek_yuz"]:
            bag = "tam_is_bagi"
        elif r["hub"]:
            bag = "hub_bagli_tek_yuz_yok"
        elif r["boot"]:
            bag = "boot_var_hub_yok"
        else:
            bag = "yetim"
        r["bag"] = bag
        rows.append(r)
        print(
            f"  {mid:12} bag={bag:24} hub={r['hub']!s:5} boot={r['boot']!s:5} "
            f"tek_yuz={r['tek_yuz']!s:5}  # {r['note']}"
        )

    # Sert iddialar (envanter tutarlılığı)
    by_id = {r["id"]: r for r in rows}
    if not by_id["programlama"]["tek_yuz"]:
        print("FAIL programlama tek yüz (6c) beklenirdi")
        fails += 1
    if not by_id["video"]["tek_yuz"]:
        print("FAIL video tek yüz (Faz E) beklenirdi")
        fails += 1
    if not by_id["tercume"]["tek_yuz"]:
        print("FAIL tercume tek yüz (Faz E) beklenirdi")
        fails += 1
    if not by_id["ses"]["tek_yuz"]:
        print("FAIL ses tek yüz (dilim1) beklenirdi")
        fails += 1
    if not by_id["hafiza"]["tek_yuz"]:
        print("FAIL hafiza tek yüz (dilim2) beklenirdi")
        fails += 1
    if not by_id["mimar"]["tek_yuz"]:
        print("FAIL mimar tek yüz (dilim3) beklenirdi")
        fails += 1
    if not by_id["hizir"]["tek_yuz"]:
        print("FAIL hizir tek yüz (dilim8) beklenirdi")
        fails += 1
    if by_id["okuma"]["bag"] != "kismi_kasten":
        print("FAIL okuma kismi_kasten olmalı")
        fails += 1
    if by_id["gelisim"]["bag"] != "yetim_hub_disi":
        print("FAIL gelisim yetim_hub_disi olmalı")
        fails += 1
    if hub_hits["genel_ilim"] != "genel":
        print("FAIL ilim sorusu genel'de kalmalı", hub_hits["genel_ilim"])
        fails += 1

    # Öz-bilgi kartları hub bayrağı ile çelişmesin (okuma hub:false)
    kartlar = {m["id"]: m for m in MOTOR_KARTLARI}
    if kartlar.get("okuma", {}).get("hub") is not False:
        print("FAIL oz-bilgi okuma.hub False olmalı")
        fails += 1
    live = motor_kartlari()
    if not any(x.get("id") == "ses" for x in live):
        print("FAIL motor_kartlari ses yok")
        fails += 1

    # Sonraki dilim ipucu
    eksik_tek_yuz = [r["id"] for r in rows if r["bag"] == "hub_bagli_tek_yuz_yok"]
    print()
    print("sonraki_aday_tek_yuz:", ",".join(eksik_tek_yuz) or "(yok)")
    print(f"hub_ornek_hits={hub_hits}")

    if fails:
        print(f"FAIL smoke_motor_bag_envanter_d0 fails={fails}")
        return 1
    print("PASS smoke_motor_bag_envanter_d0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
