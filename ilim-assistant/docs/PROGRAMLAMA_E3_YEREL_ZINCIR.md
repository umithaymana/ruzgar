# E3 — Yerel öncelik zinciri (Blok I81–I90)

**Faz 85 + 26 + 57** · Groq'suz / ollama-only uyumu

## Hedef (E3)

| Metrik | Varsayılan |
|--------|------------|
| Metin-only oranı | **≤ %1** (`RUZGAR_E3_TEXT_ONLY_TARGET=0.01`) |
| Yerel zincir başı | `kod` → `denge` → `hizli` (Ollama erişilebilirken) |
| Ollama-only | `RUZGAR_OLLAMA_ONLY=1` → Gemini/Groq kapalı |

Faz 57 parity hedefi ayrıca **≤ %3** (`RUZGAR_FAZ57_TEXT_ONLY_TARGET`) — workbench her ikisini gösterir.

## Ortam

| Değişken | Anlam |
|----------|--------|
| `RUZGAR_PROG_LOCAL_FIRST=1` | Programlama modunda yerel öncelik (varsayılan) |
| `RUZGAR_P9_STRICT_LOCAL_FIRST=1` | Yerel profiller önce, bulut kuyruk |
| `RUZGAR_OLLAMA_ONLY=1` | Yalnızca Ollama — bulut kapalı |
| `RUZGAR_DISABLE_GROQ=1` | Groq devre dışı |
| `RUZGAR_DISABLE_GEMINI=1` | Gemini devre dışı |

Zincir özelleştirme: `RUZGAR_PROG_BRAIN_CHAIN=kod,denge,hizli,groq,gemini`

## API

- `GET /api/programlama/local-workbench?workspace_root=…`

## UI

- Programlama atölye: **Yerel zincir (E3)** kartı — mod, zincir, metin-only %, kırsal mesaj

## Test

```powershell
cd ilim-assistant
python scripts/programlama_local_smoke.py
```

Offline bench (API gerekmez):

```powershell
cd "d:\CURSOR PROJELER\YAPAY ZEKA"
scripts\Ruzgar_Programlama_Bench.bat strict
```
