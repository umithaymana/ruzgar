# Mimar + Tercüme atölye birleşimi (UI kabuğu)

**Onay (Ümit abi):**
- Tercüme ve Mimar **ayrı bağımsız motorlar**
- Ses, Video, Programlama **ayrı kalır**
- **Okuma** sekmesi **yalnız Tercüme** motorunda
- Mimar iş sekmeleri (3): **İçerik · Resim·Sanat · Tasarım** (+ yan sohbet her sekmede)

---

## Faz 1 — Tercüme: Okuma sekmesi ✅
- `page-okuma` içeriği → `tercume-okuma-panel`
- Sekme: Sohbet | Çalışma | Eser ara | **Okuma**
- «Kaynak panele» → çeviri kaynağına aktarır

## Faz 2 — Bilim → Mimar (isim + kabuk) ✅
- Sidebar / üst bar: **MIMAR MOTORU**
- `data-mode="mimar"` (`okuma` / `bilim` alias → mimar)
- Tercüme v2 ile aynı kabuk: sohbet + sekmeler + çalışma alanı
- `app.js` + `mimar-atolye.js` + `mimar-atolye.css`

## Faz 3 — Mimar sekmeleri ✅
- **İçerik:** metin / ilim notu + sohbete aktar / özet iste
- **Resim · Sanat:** görsel seç + not alanı
- **Tasarım:** metin tabanlı plan/şema (eski ad: Kroki)
- Her üç sekmede **yan sohbet + geniş çalışma** (Sohbet sekmesi kaldırıldı)

## Tercüme Okuma — yan sohbet ✅
- Okuma sekmesinde «Yardım (katla)» gizlenir; **sohbet solda**, arşiv okuma sağda

## Faz 4 — Temizlik ✅ (kısmi, 2026-06-01)
- `mimar_atolye_smoke.py` + `Ruzgar_Mimar_Smoke.bat` — Faz 4 API/modül smoke
- ROK: `okuma_faz73` → `mimar` alias (`classify_mimar_intent`, `rok_smoke` + `programlama_smoke`)
- 4S-4 UI: trace / poster / pencil seçici
- Kalan: görsel atölye backend’ini `okuma_faz73` sohbet/arsiv katmanından tam ayırma (ileride)

---

## Test
- Tercüme → Okuma: arşiv listesi, dosya aç, metni kaynak panele aktar
- Mimar → her sekme açılır, sohbet yan panel (Sohbet sekmesi)
- Motorlar birbirini bozmaz
