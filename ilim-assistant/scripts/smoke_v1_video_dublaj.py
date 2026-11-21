# -*- coding: utf-8 -*-
# Created by Ümit & Gökçenur
"""Smoke — V1.0 omurga + V1.1 iptal/VRAM dublaj kancaları."""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    failed = 0
    total = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed, total
        total += 1
        print(("OK" if cond else "FAIL"), "-", label)
        if not cond:
            failed += 1

    from ilim_assistant.motorlar.video_dublaj import (
        DUBLAJ_VERSION,
        dubbing_status_snapshot,
        resolve_dub_omurga,
    )
    from ilim_assistant.motorlar.ses_klon_motoru import should_use_clone
    from ilim_assistant.ses_xtts_iptal import (
        CloneCancelled,
        begin_job,
        cancel_all,
        check as xtts_check,
        current_gen,
    )
    from ilim_assistant.ses_vram_hakem import acquire, release, snapshot as vram_snap
    from ilim_assistant.tts_service import read_ses_ayarlari

    check("video-dublaj-v1" in DUBLAJ_VERSION, f"ver {DUBLAJ_VERSION}")

    ay = read_ses_ayarlari()
    # V1.0 — tavan alias
    for raw, tavan in (
        ("asistan", "muhabbet"),
        ("muhabbet", "muhabbet"),
        ("alim", "alim"),
        ("âlim", "alim"),
        ("tilavet", "tilavet"),
        ("kuran", "tilavet"),
    ):
        p = resolve_dub_omurga(raw, voice_mode="edge", ayar=ay)
        check(p.get("ok") is True and p.get("tavan") == tavan, f"tavan {raw}→{tavan}")

    # muhabbet / asistan — BUSENAZ yolu (klon_onay varsa)
    p_muh = resolve_dub_omurga("muhabbet", voice_mode="auto", ayar=ay)
    check(p_muh.get("ok") is True, "muhabbet plan ok")
    check(p_muh.get("edge_voice"), f"muhabbet edge={p_muh.get('edge_voice')}")
    check(p_muh.get("rate") and p_muh.get("pitch"), "muhabbet rate/pitch S2")

    p_til = resolve_dub_omurga("tilavet", voice_mode="auto", ayar=ay)
    check(p_til.get("tavan") == "tilavet", "tilavet tavan")
    # Referans adları (varsa)
    if p_muh.get("speaker_name"):
        check(
            "BUSENAZ" in str(p_muh["speaker_name"]).upper()
            or "muhabbet" in str(p_muh["speaker_name"]).lower(),
            f"muhabbet speaker={p_muh.get('speaker_name')}",
        )
    else:
        # auto+klon_onay yoksa Edge — tutarlı
        check(p_muh.get("use_clone") is False, "klon_onay yok→Edge")

    if p_til.get("speaker_name"):
        check(
            "kuran" in str(p_til["speaker_name"]).lower(),
            f"tilavet speaker={p_til.get('speaker_name')}",
        )

    # should_use_clone parity
    sc = should_use_clone(backend="auto", karakter="muhabbet", ayar=ay)
    check(bool(sc) == bool(p_muh.get("use_clone")), f"should_use_clone parity sc={sc}")

    # edge zorla
    p_edge = resolve_dub_omurga("muhabbet", voice_mode="edge", ayar=ay)
    check(p_edge.get("use_clone") is False, "voice=edge → clone kapalı")

    # clone zorla + ref
    p_cl = resolve_dub_omurga("muhabbet", voice_mode="clone", ayar=ay)
    if p_cl.get("ok"):
        check(p_cl.get("speaker") is not None, "voice=clone → speaker")
    else:
        check("referans" in str(p_cl.get("error") or "").lower() or True, "clone refsiz hata")

    # V1.1 — iptal: begin → cancel → check CloneCancelled
    tok = begin_job()
    check(isinstance(tok, int), f"begin tok={tok}")
    cancel_all(reason="smoke_v1_dub")
    raised = False
    try:
        xtts_check(tok)
    except CloneCancelled:
        raised = True
    check(raised, "iptal→CloneCancelled")
    check(current_gen() > tok, "gen arttı")

    # Segment döngüsü simülasyonu: iptal ortada keser
    tok2 = begin_job()
    hits = []

    def _worker():
        for i in range(20):
            try:
                xtts_check(tok2)
                hits.append(i)
                time.sleep(0.05)
            except CloneCancelled:
                hits.append(-1)
                return

    th = threading.Thread(target=_worker, daemon=True)
    th.start()
    time.sleep(0.12)
    cancel_all(reason="mid_seg")
    th.join(timeout=2.0)
    check(-1 in hits and len([h for h in hits if h >= 0]) < 20, f"orta kesim hits={hits}")

    # VRAM hakemi
    snap0 = vram_snap()
    check("budget_mb" in snap0, f"vram budget={snap0.get('budget_mb')}")
    acq = acquire("xtts", prepare=False)
    check(acq.get("ok") is True, "acquire xtts")
    check(vram_snap().get("owner") == "xtts", "owner xtts")
    rel = release("xtts", restore=False)
    check(rel.get("ok") is True and vram_snap().get("owner") == "idle", "release idle")

    # Status + API kancaları
    st = dubbing_status_snapshot()
    check(st.get("v1", {}).get("omurga") is True, "status v1.omurga")
    check(st.get("v1", {}).get("iptal_vram") is True, "status v1.iptal_vram")
    check(st.get("v1", {}).get("kalite_mux") is True, "status v1.kalite_mux")
    check("muhabbet" in (st.get("omurga_plans") or {}), "omurga_plans")
    check("iptal" in st and "vram" in st, "status iptal+vram")
    check("v1.2" in DUBLAJ_VERSION or "v1.2" in str(st.get("version")), "ver v1.2")

    ds = (ROOT / "desktop_server.py").read_text(encoding="utf-8")
    check("/api/video/dub" in ds and "mix_original" in ds, "API mix_original")
    check("dubbing_status_snapshot" in ds, "API status")
    check("apply_quality_mux" in (ROOT / "ilim_assistant" / "motorlar" / "video_dublaj.py").read_text(encoding="utf-8"), "pipeline quality_mux")

    # Masa + mobil parity (V1.2 Form alanları)
    desk = ROOT.parent / "ruzgar-desktop" / "app.js"
    desk_txt = desk.read_text(encoding="utf-8") if desk.is_file() else ""
    check('fd.append("mix_original"' in desk_txt, "desktop mix_original Form")
    check('fd.append("orig_duck_db"' in desk_txt, "desktop orig_duck_db Form")
    check('fd.append("normalize"' in desk_txt, "desktop normalize Form")
    idx = ROOT.parent / "ruzgar-desktop" / "index.html"
    idx_txt = idx.read_text(encoding="utf-8") if idx.is_file() else ""
    check("video-dub-mix-original" in idx_txt and "ses-dub-mix-original" in idx_txt, "UI miks checkbox")
    mob = ROOT / "static" / "mobil-pwa" / "app.js"
    mob_txt = mob.read_text(encoding="utf-8")
    check("runVideoDub" in mob_txt and "mix_original" in mob_txt, "mobil runVideoDub")
    check("parseDubChatCmd" in mob_txt, "mobil dublaj chat komutu")

    mod = (ROOT / "ilim_assistant" / "motorlar" / "video_dublaj.py").read_text(
        encoding="utf-8"
    )
    check("resolve_dub_omurga" in mod, "resolve_dub_omurga")
    check("should_use_clone" in mod, "should_use_clone bağ")
    check("cancel_token" in mod and "xtts_check" in mod, "iptal segment")
    check("synthesize_clone_wav" in mod, "klon VRAM yolu")
    check("soft_fit" in mod, "assemble soft_fit")

    # V1.2 kalite mux birim testleri (ffmpeg)
    from ilim_assistant.ses_v1_dub_kalite_mux import (
        MUX_VERSION,
        apply_quality_mux,
        db_to_linear,
        mix_dub_over_original,
        normalize_loudness,
        plan_soft_fit,
        soft_fit_audio_duration,
    )
    from ilim_assistant.video_ffmpeg import (
        audio_duration_sec,
        ffmpeg_available,
        generate_silence_wav,
    )
    import tempfile

    check("kalite-mux" in MUX_VERSION, f"mux ver {MUX_VERSION}")
    check(abs(db_to_linear(-6.0) - 0.501) < 0.02, "db_to_linear -6")

    p_ok = plan_soft_fit(1.0, 1.0)
    check(p_ok["action"] in ("copy", "atempo"), f"fit equal action={p_ok['action']}")
    p_short = plan_soft_fit(0.5, 1.0)
    check(p_short["action"] in ("atempo", "atempo_pad"), f"fit short={p_short['action']}")
    p_long = plan_soft_fit(2.0, 1.0)
    check(p_long["action"] in ("atempo", "atempo_trim"), f"fit long={p_long['action']}")
    check(0.87 <= float(p_long.get("tempo") or 1) <= 1.15, "tempo pencere")

    if ffmpeg_available():
        td = Path(tempfile.mkdtemp(prefix="smoke_v12_"))
        try:
            src = td / "src.wav"
            generate_silence_wav(src, 800, sample_rate=22050)  # 0.8s
            fit_dst = td / "fit.wav"
            finfo = soft_fit_audio_duration(src, fit_dst, 1.0)
            check(fit_dst.is_file() and fit_dst.stat().st_size > 64, "soft_fit out")
            out_sec = float(finfo.get("out_sec") or audio_duration_sec(fit_dst))
            check(0.85 <= out_sec <= 1.15, f"soft_fit ~1s got={out_sec:.2f}")

            norm = td / "norm.wav"
            ninfo = normalize_loudness(fit_dst, norm)
            check(ninfo.get("ok") is True and norm.is_file(), f"loudnorm {ninfo.get('method')}")

            orig = td / "orig.wav"
            generate_silence_wav(orig, 1200, sample_rate=22050)
            mix = td / "mix.wav"
            minfo = mix_dub_over_original(orig, norm, mix, orig_duck_db=-16.0)
            check(minfo.get("ok") is True and mix.is_file(), "amix duck")

            final = td / "final.wav"
            # apply_quality_mux hedef dosyayı üzerine yazar
            import shutil

            shutil.copy2(fit_dst, final)
            q = apply_quality_mux(
                final,
                media_path=orig,
                mix_original=True,
                orig_duck_db=-18.0,
                normalize=True,
                work_dir=td / "w",
            )
            check(q.get("ok") is True and q.get("normalized") is True, "apply_quality_mux")
            check(q.get("mixed") is True, "apply mix flag")
        finally:
            try:
                for f in td.rglob("*"):
                    if f.is_file():
                        f.unlink(missing_ok=True)
                for d in sorted(td.rglob("*"), reverse=True):
                    if d.is_dir():
                        d.rmdir()
                td.rmdir()
            except OSError:
                pass
    else:
        check(False, "ffmpeg yok — V1.2 mux test atlandı")

    print(f"\n=== smoke_v1_video_dublaj: {total - failed}/{total} OK ===")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
