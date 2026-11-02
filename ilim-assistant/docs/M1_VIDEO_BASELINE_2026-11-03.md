# M1 — Video motor baseline + mühür — 2026-11-03

`ses-m1-video-baseline-v1-2026-11-03`

## Ölçüm (bu PC)

| Motor | Durum |
|-------|--------|
| FFmpeg | ✓ |
| ffprobe | ✓ |
| yt-dlp | ✓ |

| Boru | ms (örnek) |
|------|------------|
| gen 2s test mp4 → probe | — |
| trim (re-encode) | ~100–300 |
| concat iki parça | ~50–200 |

## Derin yama

**Hub Faz E:** Video modundayken her mesaj `motor_action=atolye` açıyordu (selam/hava dahil).  
Artık yalnız `is_video_workflow_request` / indirme niyeti atölyeyi tetikler.

## Smoke

`scripts/smoke_m1_video.py` · hub ince ayar 17/17 ile uyumlu.

## Sonraki

**M2 Tercüme** (Video mühüründen sonra).
