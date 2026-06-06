# Video motoru — smoke test checklist

Manuel test (Electron veya tarayıcı + `127.0.0.1:8779`). Her madde: ☐ → ✓

**Önkoşul:** FFmpeg PATH'te, yt-dlp kurulu, sunucu çalışıyor, Ctrl+Shift+R.

## Kabuk

| # | Test | ✓ |
|---|------|---|
| 1 | Video motoruna geç — sinema sahnesi, «Çalışma sayfası» yok | ☐ |
| 2 | Üstte 5 video düğmesi görünür | ☐ |
| 3 | Sol motor paneli « / » daralt/genişlet — layout bozulmaz | ☐ |
| 4 | `#video-engine-hint` FFmpeg + yt-dlp durumunu doğru yazar | ☐ |
| 5 | `?` yardım — Video motoru bölümü görünür | ☐ |

## Sinema sahnesi

| # | Test | ✓ |
|---|------|---|
| 6 | Dosya seç → oynatıcıda önizleme | ☐ |
| 7 | Medya bilgisi → teknik özet (Teknik özet paneli veya dock) | ☐ |
| 8 | Timeline: Başlangıç / Bitiş → Kesime yaz | ☐ |

## Dock panelleri

| # | Panel | ✓ |
|---|--------|---|
| 9 | URL indir — test URL veya son indirme | ☐ |
| 10 | Son indirmeler — tıkla → göreli yol dolar | ☐ |
| 11 | Kes — kısa kesim veya transcode | ☐ |
| 12 | Altyazı göm — (test dosyası varsa) | ☐ |
| 13 | Harici ses — (test dosyası varsa) | ☐ |
| 14 | Görsel kurgu — parça ekle; boş mesaj kaybolur | ☐ |
| 15 | Altyazı → Tercüme — tercüme motoruna geçer | ☐ |
| 16 | Dock kapat (× veya Escape) — sahne normale döner | ☐ |

## Probe (rel)

| # | Test | ✓ |
|---|------|---|
| 17 | Kes panelinde göreli yol yaz (indirilmiş video) → Medya bilgisi (dosya seçmeden) | ☐ |

## Sohbet (isteğe bağlı)

| # | Test | ✓ |
|---|------|---|
| 18 | YouTube URL + «panelde aç» → sinema `<video>` | ☐ |
| 19 | «video ara …» → panelde tıklanabilir liste | ☐ |
| 20 | «2 numarayı oynat» → indirmeden sinema | ☐ |
| 21 | Sinema URL çubuğu + **Aç** | ☐ |
| 22 | Sinema **İndir** → yerel dosya oynatıcıda | ☐ |
| 23 | Doğrudan `.mp4` link + oynat | ☐ |
| 24 | Electron **Web** düğmesi (BrowserView) | ☐ |

---

*SW-0…SW-5 smoke — `SINEMA_WEB_VIDEO_HUB_PLANI.md` ile eşleşir.*
