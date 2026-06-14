# Ana Motor Faz AN — İdrak Zihin

> **Mimar:** Ümit & Gökçenur · **2026-06-14**

## Amaç

Cursor tarzı akıcı sohbet için **tur başı anlama**:

- **Zaman:** geçmiş / şimdi / gelecek / zamansız  
- **Niyet:** güncel olay, kişisel, arşiv, sohbet, bilgi  
- **Kaynak politikası:** «şimdi» sorularında web zorunlu; arşiv/hafıza hijack yasak  

## Uygulanan modüller

| # | Modül | Özet |
|---|--------|------|
| AN1 | `ana_motor_idrak_zihin.py` | `analyze_turn`, `TurnIdrak`, kaynak kapıları |
| AN2 | `ana_motor_plan.py` | Erken plan + tek beyin / arşiv blok |
| AN3 | `chat_core.py` | Tur idrak, arşiv skip, LLM talimatı |
| AN4 | `ruzgar_tek_beyin.py` | Hafıza/chat_history blok (güncel olay) |
| AN5 | `ruzgar_tek_beyin_analiz.py` | Niyet sınıflandırma köprüsü |
| AN6 | `desktop_server.py` | Health `idrak_zihin_faz_an` |
| AN7 | `scripts/ana_motor_smoke.py` | İran / Emine / arşiv regression |

## Ortam

```env
RUZGAR_IDRAK_ZIHIN=1
```

Kapatma: `RUZGAR_IDRAK_ZIHIN=0`

## Build

`2026-06-14-ruzgar-idrak-zihin-faz-an`

## Doğrulama

```bash
cd ilim-assistant
python scripts/ana_motor_smoke.py
Ruzgar_TemizBaslat.bat
```

Canlı örnekler:
- `iran şuan kimlerle savaşıyor` → bilgi + web (eski arşiv değil)
- `emine haymana kimdir` → kişisel hafıza
- `daha önce ne konuşmuştuk` → arşiv geri çağırma

*Bismillah — Faz AN*
