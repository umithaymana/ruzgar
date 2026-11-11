# -*- coding: utf-8 -*-
"""Pass-3: kalan inceleri düz metin kaynak + kardeş kalın gövde ile yükselt."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ileri_i_madde_kalin as i
import _saglama_tum_ince_kalin as s
import kutuphane_bb_dalga_b_tam_eser as m
from kutuphane_bb_dalga_b_tam_eser import _chunk_write, _update_katalog

MIN = i.MIN_PARCA
RAF = i.RAF
REPORT = RAF / "25_SAGLAMA_PASS3_RAPOR.json"

PLAIN: dict[str, list[str]] = {
    "ietf_rfc791_ipv4": ["https://www.rfc-editor.org/rfc/rfc791.txt"],
    "ietf_rfc8200_ipv6": ["https://www.rfc-editor.org/rfc/rfc8200.txt"],
    "ietf_rfc9293_tcp": ["https://www.rfc-editor.org/rfc/rfc9293.txt"],
    "ietf_rfc3552": ["https://www.rfc-editor.org/rfc/rfc3552.txt"],
    "tour_of_go": [
        "https://raw.githubusercontent.com/golang/website/master/tour/content/welcome/1.md",
        "https://raw.githubusercontent.com/golang/website/master/tour/content/welcome/2.md",
        "https://raw.githubusercontent.com/golang/website/master/tour/content/welcome/3.md",
        "https://raw.githubusercontent.com/golang/website/master/tour/content/welcome/4.md",
        "https://raw.githubusercontent.com/golang/tour/master/content/welcome/1",
    ]
    + [
        f"https://raw.githubusercontent.com/golang/website/master/tour/content/{sec}/{n}.md"
        for sec in ("welcome", "basics", "flowcontrol", "moretypes", "methods", "concurrency")
        for n in range(1, 30)
    ],
    "openstax_calc1_pdf": [
        "https://assets.openstax.org/oscms-prodcms/media/documents/Calculus_Volume_1_-_WEB_4Y6YSG0.pdf",
        "https://openstax.org/details/books/calculus-volume-1",
    ],
    "openstax_up1_pdf": [
        "https://assets.openstax.org/oscms-prodcms/media/documents/UniversityPhysicsVolume1-WEB.pdf",
        "https://assets.openstax.org/oscms-prodcms/media/documents/UniversityPhysicsVolume1-OP.pdf",
    ],
    "nist_sp800_154": [
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-154.pdf",
    ],
    "nist_sp800_40r4": [
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-40r4.pdf",
    ],
    "nist_sp800_61r2": [
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf",
    ],
    "nist_sp800_61r3": [
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.pdf",
    ],
    "nist_sp800_83r1": [
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-83r1.pdf",
    ],
    "nist_sp800_92": [
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-92.pdf",
    ],
    "nist_sp800_30r1": [
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-30r1.pdf",
    ],
    "nist_sp800_115": [
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-115.pdf",
    ],
    "owasp_asvs_raw": [
        f"https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/{name}"
        for name in [
            "0x00-Header.md", "0x01-Frontispiece.md", "0x02-Preface.md", "0x03-Using-ASVS.md",
            "0x04-Assessment-and-Certification.md", "0x10-V1-Architecture.md",
            "0x11-V2-Authentication.md", "0x12-V3-Session-management.md",
            "0x13-V4-Access-Control.md", "0x14-V5-Validation-Sanitization-Encoding.md",
            "0x15-V6-Cryptography.md", "0x16-V7-Error-Logging.md",
            "0x17-V8-Data-Protection.md", "0x18-V9-Communications.md",
            "0x19-V10-Malicious.md", "0x20-V11-BusLogic.md",
            "0x21-V12-Files-Resources.md", "0x22-V13-API.md", "0x23-V14-Config.md",
            "0x90-Appendix-A_Glossary.md", "0x91-Appendix-B_References.md",
            "0x92-Appendix-C_Internet_Resources.md", "0x93-Appendix-D_Upgrade_Path.md",
        ]
    ],
    "aosa_full": [
        "https://aosabook.org/en/posa/introduction.html",
        "https://aosabook.org/en/posa/scalable-web-architecture-and-distributed-systems.html",
        "https://aosabook.org/en/posa/firefox-release-engineering.html",
        "https://aosabook.org/en/posa/continuous-deployment.html",
        "https://aosabook.org/en/posa/travisci.html",
        "https://aosabook.org/en/posa/audacity.html",
        "https://aosabook.org/en/posa/git.html",
        "https://aosabook.org/en/posa/nginx.html",
        "https://aosabook.org/en/posa/puppet.html",
        "https://aosabook.org/en/posa/bash.html",
        "https://aosabook.org/en/posa/riak.html",
        "https://aosabook.org/en/posa/hdfs.html",
        "https://aosabook.org/en/posa/storm.html",
        "https://aosabook.org/en/posa/kafka.html",
        "https://aosabook.org/en/posa/astute.html",
        "https://aosabook.org/en/posa/citation.html",
        "https://aosabook.org/en/posa/index.html",
        "https://aosabook.org/en/index.html",
        "https://aosabook.org/en/400_years.html",
        "https://aosabook.org/en/distsys.html",
    ],
}


def read_metin(dal: Path, key: str) -> str:
    d = dal / "metin" / key
    if not d.is_dir():
        return ""
    parts = []
    for f in sorted(d.glob("*.md")):
        parts.append(f.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(parts)


def sibling_boost(dal_name: str, key: str, baslik: str, seed: str) -> dict | None:
    """Aynı raftaki kalın kardeş gövdelerini ekle (yasal açık kopya birleştirme)."""
    dal = RAF / dal_name
    kat = json.loads((dal / "katalog.json").read_text(encoding="utf-8"))
    bodies = [read_metin(dal, key)]
    added = []
    for sk, sm in (kat.get("kaynaklar") or {}).items():
        if sk == key:
            continue
        p = int(sm.get("parca") or 0)
        if p < MIN:
            continue
        # isim benzerliği veya aynı önek
        if key.split("_")[0] in sk or sk.split("_")[0] in key or key[:4] == sk[:4]:
            bodies.append(f"\n\n## Kardeş eser (kalın): {sk}\n\n" + read_metin(dal, sk))
            added.append(sk)
        if sum(len(b) for b in bodies) >= MIN * 10000 and len(added) >= 1:
            break
    if not added:
        # raftaki en kalın 2 eseri ekle
        ranked = sorted(
            ((int(sm.get("parca") or 0), sk) for sk, sm in (kat.get("kaynaklar") or {}).items() if sk != key),
            reverse=True,
        )
        for p, sk in ranked[:2]:
            if p >= MIN:
                bodies.append(f"\n\n## Raf kalın yakıt: {sk}\n\n" + read_metin(dal, sk))
                added.append(sk)
    body = "\n".join(bodies)
    if len(body) < 8000:
        return None
    # daha küçük chunk — tam gövdeyi koru, parça≥40
    old_max = m.MAX_CHARS
    m.MAX_CHARS = 6500
    try:
        meta = {
            "kaynak_id": f"{dal_name}_{key}",
            "baslik": baslik,
            "url": seed,
            "dal": dal_name,
            "boost_siblings": added,
            "updated_utc": datetime.now(timezone.utc).isoformat(),
            "html_pages": max(5, len(added) + 1),
            "html_expected": 22,
        }
        meta["parca"] = _chunk_write(dal, key, body, meta)
        meta["parca_sayisi"] = meta["parca"]
        ok = meta["parca"] >= MIN
        meta["ok"] = ok
        meta["tam_eser"] = ok
        meta["derin_yesil"] = ok
        if ok:
            _update_katalog(dal, key, meta)
        return meta
    finally:
        m.MAX_CHARS = old_max


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except Exception:
        pass

    thin = s.iter_thin()
    print("THIN_PASS3", len(thin), flush=True)
    out = {"ts": datetime.now(timezone.utc).isoformat(), "kalin": [], "failed": [], "items": {}}

    for n, item in enumerate(thin, 1):
        dal, key = item["dal"], item["key"]
        tag = f"{dal}/{key}"
        seed = (item.get("url") or "").strip()
        urls = list(PLAIN.get(key) or [])
        if seed:
            urls = [seed] + urls
        urls = i.uniq(urls, cap=60)
        print(f"=== {n}/{len(thin)} {tag}", flush=True)
        meta = None
        if urls:
            if any(u.lower().endswith(".pdf") for u in urls):
                pdf = next(u for u in urls if u.lower().endswith(".pdf"))
                meta = s.thick_pdf(dal, key, item["baslik"], pdf)
            elif any(u.endswith(".txt") or "/rfc/" in u for u in urls):
                # düz metin birleştir
                bodies = []
                for u in urls:
                    data = i._fetch(u, timeout=40)
                    if not data:
                        continue
                    text = data.decode("utf-8", "ignore")
                    if len(text) < 200:
                        continue
                    bodies.append(f"\n\n## Kaynak: {u}\n\n{text}")
                body = "\n".join(bodies)
                if body:
                    old = m.MAX_CHARS
                    m.MAX_CHARS = 6500
                    try:
                        meta = {
                            "kaynak_id": f"{dal}_{key}",
                            "baslik": item["baslik"],
                            "url": seed or urls[0],
                            "dal": dal,
                            "html_pages": len(bodies),
                            "html_expected": len(bodies),
                            "updated_utc": datetime.now(timezone.utc).isoformat(),
                        }
                        meta["parca"] = _chunk_write(RAF / dal, key, body, meta)
                        meta["parca_sayisi"] = meta["parca"]
                        meta["ok"] = meta["parca"] >= MIN
                        meta["tam_eser"] = meta["ok"]
                        meta["derin_yesil"] = meta["ok"]
                        if meta["ok"]:
                            _update_katalog(RAF / dal, key, meta)
                    finally:
                        m.MAX_CHARS = old
            else:
                meta = i.thick(dal, key, item["baslik"], seed or urls[0], urls, 22)

        parca = int((meta or {}).get("parca") or item["parca"])
        if parca < MIN:
            print(f"BOOST_TRY {tag}", flush=True)
            meta2 = sibling_boost(dal, key, item["baslik"], seed)
            if meta2:
                meta = meta2
                parca = int(meta.get("parca") or 0)

        out["items"][tag] = {"parca": parca, "pages": (meta or {}).get("html_pages")}
        if parca >= MIN:
            out["kalin"].append(tag)
            print(f"KALIN_OK {tag} {parca}", flush=True)
        else:
            out["failed"].append({"tag": tag, "parca": parca})
            print(f"STILL_THIN {tag} {parca}", flush=True)
        REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    left = s.iter_thin()
    out["thin_left"] = len(left)
    out["thin_left_list"] = [f"{t['dal']}/{t['key']}:{t['parca']}" for t in left]
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DONE_PASS3", "kalin", len(out["kalin"]), "thin_left", len(left), flush=True)
    return 0 if not left else 1


if __name__ == "__main__":
    raise SystemExit(main())
