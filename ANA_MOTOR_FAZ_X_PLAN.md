# Ana Motor — Faz X Planı (2026-06-10)

> **Hedef:** Ajan 2.0 — daha uzun tur, patch doğrulama, çok dosya onay kartı.

## Faz X — uygulandı

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| X1 | Ajan 2.0 yapılandırma | `ana_motor_ajan20.py` | Varsayılan 5 tur (üst 8) |
| X2 | Patch doğrulama | `ana_motor_ajan20.py` | `py_compile` + isteğe pytest |
| X3 | Çok dosya staging | `ana_motor_ajan20.py` + `agent_loop` | 2+ dosya → onay kartı |

### Entegrasyon

- `ana_motor_agent_loop.py` → `process_agent_loop_patches`
- `GET /api/ana-motor/agent-loop/status`

### Ortam

```env
RUZGAR_ANA_AGENT_V2=1
RUZGAR_ANA_AGENT_MAX_TURNS=5
RUZGAR_ANA_AGENT_VERIFY=1
RUZGAR_ANA_AGENT_STAGE_MULTI=1
RUZGAR_ANA_AGENT_VERIFY_PYTEST=0
```

### Başarı ölçütü

1. Dosya işlemi → en fazla 5 tur (v2)
2. `.py` patch → py_compile doğrulama
3. 2 dosya patch → staging (onay kartı)

## Sıradaki (Faz Y — öneri)

- Bilgi kalite 2.0 (opsiyonel LLM reflection)
- Sohbet içi kaynak + güven rozeti

*Bismillah — Ümit & Gökçenur*
