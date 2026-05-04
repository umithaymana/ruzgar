"""
Örnek kullanım:

  # 1) Metinden sahne planı (Ollama açık olmalı)
  python video_cli.py plan --text dosya.txt --theme "Kuran tilaveti sonrası tefsir" --out plan.json

  # 2) Her sahne için ses üretin (ör. ilim-voice / başka TTS) ve sesleri audio/001.wav … kaydedin
  # 3) Tek bir arka plan görseli veya sahne başına görsel
  python video_cli.py render --plan plan.json --audio-dir .\audio --image .\arka_plan.jpg --out film.mp4

Not: Uzun ve 'sinema kalitesi' tam yapay video için ticari API veya özel iş akışı gerekir;
bu araç plan + montaj temelidir.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ilim_video.ffmpeg_render import render_from_assets
from ilim_video.scene_planner import plan_scenes, save_plan


def main():
    p = argparse.ArgumentParser(description="İlim Video — sahne planı ve FFmpeg montaj")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="Metinden sahne planı JSON")
    p_plan.add_argument("--text", required=True, help="Metin dosyası yolu")
    p_plan.add_argument("--theme", required=True, help="Konu / tema")
    p_plan.add_argument("--out", default="video_plan.json")

    p_ren = sub.add_parser("render", help="plan.json + wav + görsel → mp4")
    p_ren.add_argument("--plan", required=True)
    p_ren.add_argument("--audio-dir", required=True, type=Path)
    p_ren.add_argument("--image", required=True, type=Path, help="Varsayılan arka plan görseli")
    p_ren.add_argument("--images-dir", type=Path, default=None, help="İsteğe bağlı sahne görselleri")
    p_ren.add_argument("--out", default="output.mp4")

    args = p.parse_args()

    if args.cmd == "plan":
        text = Path(args.text).read_text(encoding="utf-8")
        pl = plan_scenes(text, args.theme)
        save_plan(args.out, pl)
        print(f"Yazıldı: {args.out} ({len(pl.get('scenes', []))} sahne)")
        return

    if args.cmd == "render":
        out = render_from_assets(
            Path(args.plan),
            args.images_dir,
            Path(args.image),
            Path(args.audio_dir),
            Path(args.out),
        )
        print(f"Tamam: {out}")


if __name__ == "__main__":
    main()
