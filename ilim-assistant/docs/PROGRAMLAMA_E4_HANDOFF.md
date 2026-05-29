# E4 — Ana Motor ↔ Programlama handoff (Blok H79)

**Faz 59 + 79 + 76** · Handoff v4 workbench

## Hedef (E4)

| Metrik | Varsayılan |
|--------|------------|
| Son delege başarı oranı | **≥ %85** (`RUZGAR_E4_TARGET_RATE`) |
| Handoff paketi | `build_handoff_packet_v3` dolu |
| Manifest | `programlama.tag` sunucu ile UI eşleşir |

## Akış

1. **Genel mod** — hub kod/programlama niyeti seçer.
2. **Handoff v3** — kapsam, git özeti, son başarısız görevler, mega notu.
3. **Programlama** — ajan çalışır; Faz 59 footer: tur, yazım, **pytest** satırı.
4. **Dönüş** — kullanıcı genel moda geçer; son delege özeti API’den okunur.

## API

- `GET /api/programlama/handoff-workbench?workspace_root=…&message=…`
- `GET /api/ana-motor/delegation-summary`

## UI

- Programlama: **Handoff v4** kartı (özet, motor zinciri, pytest footer)
- Genel: orkestra köprüsü + delege butonları (mevcut)

## Test

```powershell
cd ilim-assistant
python scripts/programlama_handoff_smoke.py
```
