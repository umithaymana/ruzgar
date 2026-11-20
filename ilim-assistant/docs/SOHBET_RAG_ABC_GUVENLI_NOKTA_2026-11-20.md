# Sohbet / RAG — A→B→C güvenli nokta

**Tarih:** 2026-11-20  
**Mimar:** Ümit & Gökçenur  
**Amaç:** Omurga A (indeks/bütçe) + B (masa bağ) + C (kütüphane ince) kilit; burası güvenli nokta adayı.

---

## A — indeks + bütçe

| Madde | Durum | Not |
|-------|-------|-----|
| Nebula apply → `index_knowledge_files` | OK | Ana indeks upsert |
| tarih / TDK / nebula_kitap incremental | OK | `build_index` → `index_knowledge_files([rel])` |
| Tur `budget_sec` tek kaynak | OK | ContextVar + `orch.budget_sec` |
| `ensure_turn_budget` (çift begin yok) | OK | LLM deadline sıfırlamaz |
| Truncate → öğrenme reddi | OK | `answer_truncated` + `auto_learn` skip |
| wrap / classify aynı bütçe | OK | `resolve_active_budget_sec` |

## B — masa

| Madde | Durum | Not |
|-------|-------|-----|
| `/api/chat/full` → `masa` | OK | done_event.masa üst JSON |
| İstemci full → synthetic done.masa | OK | `app.js` `masa: j.masa` |
| Stream SSE done.masa | Önceden vardı | `ruzgarMasaSunucuUygula` |

## C — kütüphane

| Madde | Durum | Not |
|-------|-------|-----|
| Şamile usable Arapça | OK | skor tabanı 0.28 (env) |
| Arşiv disk mtime önbellek | OK | `arsiv_disk_last_meta.cache_hit` |
| Arşiv deadline erken kesme | OK | `remaining_sec < 0.35` |

---

## Smoke paketi (güvenli nokta)

```
python scripts/smoke_chat_full_finalize.py
python scripts/smoke_timeout_vs_miss.py
python scripts/smoke_turn_budget_single.py
python scripts/smoke_shamela_arabic_lex.py
python scripts/smoke_arsiv_disk_search.py
python scripts/smoke_baglam_zehir.py
python scripts/smoke_anlam_koruma.py
```

Hepsi yeşil → bu commit güvenli nokta.

---

## Canlı not

- Kod değişti: `Ruzgar.ps1 -ForceRestart` (port 8779).
- Yerel hafıza JSON / `.rag_index` git dışı (bilinçli).
- Boot motor sırası ve arayüz kilidi dokunulmadı.
