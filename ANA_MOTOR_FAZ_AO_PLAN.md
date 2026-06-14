# Ana Motor Faz AO — Sohbet devamı devralma

> **Mimar:** Ümit & Gökçenur · **2026-06-14**

## Amaç

Kısa devam cümlelerinde (**peki israil?**, **devam et**, **o konuda**) önceki turun **zaman + niyet** çerçevesini devralmak; güncel konuşma zincirini koparmamak.

## Uygulandı

| # | Modül | Özet |
|---|--------|------|
| AO1 | `ana_motor_idrak_zihin.py` | `_apply_thread_inheritance`, `thread_inherit_enabled` |
| AO2 | `ana_motor_plan.py` | `plan_question(..., history=, idrak_pre=)` |
| AO3 | `chat_core.py` | Plan + idrak aynı geçmişle |
| AO4 | `desktop_server.py` | SSE plan geçmişi |

## Ortam

```env
RUZGAR_IDRAK_ZIHIN=1
RUZGAR_IDRAK_THREAD_INHERIT=1
```

## Doğrulama

1. «iran şuan kimlerle savaşıyor»
2. «peki israil?» → hâlâ güncel olay + web

*Bismillah — Faz AO*
