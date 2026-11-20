# 2026-11-20 — onarim-faz2-selam-oturum

## 1) Emir
Mimar Ümit: ONARIM PLANI Faz 2 — history’li canonical_selam; SOHBET_ONCE selam+resume istisnası; test genişlet.

## 2) Sonuç
`has_prior_session=False` sabiti kalktı; fast_lane/plan history alır; SOHBET_ONCE altında saf selam anlık kalır; nasılsın LLM’e bırakılır.

## 3) Doğru
- Boş history → SELAM_STANDART («dün konuştuk» yok).
- Dolu history → SELAM_WITH_RESUME.
- Tek kapı = çift uzun resume metni yok (şikayet hariç).

## 4) Yanlış
- Eskiden SOHBET_ONCE=1 tüm gündelik anlığı öldürüyordu (resume dahil).
- history=None + False sabiti resume’u öldürüyordu.

## 5) Nerede
- Dal: `cursor/ruzgar-onarim-fazlari-9eeb`
- Commit: cb3aba4c1
- Dosyalar:
  - `chat_fast_lane.py`, `ana_motor_plan.py`, `ruzgar_sohbet_once.py`
  - `chat_core.py`, `desktop_server.py`
  - `tests/test_sohbet_tutarlilik.py`

## 6) Nasıl uygula
1. Selamda history’yi uçtan uca taşı.
2. SOHBET_ONCE istisnası yalnız `allow_selam_resume_instant`.
3. Saf selamda `try_session_resume_greeting` uzun metin basma.
4. Test: boş/dolu + SOHBET_ONCE=1.

## 7) Tuzaklar
- Disk tabanlı resume «dün» uydurabilir — client history öncelikli.
- `nasılsın` ile `selam` karıştırma.

## 8) Çözüm
canonical_selam(history=…) + allow_selam_resume_instant.

## 9) Bir daha yapma
`has_prior_session=False` sabitleme.

## 10) Anahtarlar
`selam`, `resume`, `sohbet-once`, `history`, `faz2`, `onarim`

## 11) Durum
`hazir`

---

## El rahatlatma

### Giriş kapısı
`ruzgar_sohbet_tek_kapi.canonical_selam_reply`

### Hazır komutlar
```bash
cd ilim-assistant && python3 -m pytest tests/test_sohbet_tutarlilik.py -q
```

### Dokunma
Faz 1 registry; RAG diversify.

### Beklenen çıktı
test_sohbet_tutarlilik yeşil; SOHBET_ONCE’ta selam anlık.

### Bilinen kırık
—

### İlk güvenli adım
`canonical_selam_reply("selam", history=None)` → STANDART

### Kapsam sınırı
Faz 2 — RAG/motor yok.

### Geri alma
commit revert.
