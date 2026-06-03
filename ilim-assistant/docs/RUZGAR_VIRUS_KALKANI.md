# Rüzgar Virüs Kalkanı

Rüzgar'ın **kendi** çok katmanlı antivirüs motoru (`ruzgar_antivirus.py`). Windows Defender varsayılan olarak **kullanılmaz**; yedek için `RUZGAR_AV_DEFENDER_BACKUP=1`.

## Katmanlar

| Katman | Açıklama |
|--------|----------|
| URL itibar | `data/ruzgar_url_blocklist.json` |
| Uzantı politikası | Tehlikeli uzantı, çift uzantı, Unicode homograf |
| Sihirli bayt | Sahte PDF/ZIP/görsel |
| Gömülü PE | MZ/ELF + PE başlık doğrulama |
| Entropi | Şifreli/paketli içerik şüphesi |
| Arşiv | Zip bomba, iç içe `.exe`, makro izleri |
| İçerik | PDF JavaScript, HTML script, HTA, Office makro |
| İmza | `ruzgar_threat_signatures.json` + EICAR |
| Regex | `ruzgar_threat_rules.json` |
| Kara liste | `ruzgar_threat_hashes.json` |
| Clam yedek | `RUZGAR_AV_CLAM_SUPPORT=1` |

## İndirme akışı

1. Karantinaya indir  
2. **deep** tarama (quick: `scan_mode=quick`)  
3. Temiz → sesli onay → kullanıcı «tamam indirebilirsin»  
4. **Commit öncesi yeniden deep tarama**  
5. Hedef klasöre taşı  

Tehdit → **nötralize** (`threats_neutralized/`, 64KB güvenli silme, log).

## Veri dosyaları (genişletilebilir)

- `ilim-assistant/data/ruzgar_threat_signatures.json`
- `ilim-assistant/data/ruzgar_threat_rules.json`
- `ilim-assistant/data/ruzgar_threat_hashes.json`
- `ilim-assistant/data/ruzgar_trusted_hashes.json`
- `ilim-assistant/data/ruzgar_url_blocklist.json`

## API

- `GET /api/ruzgar/virus-guard/capabilities`
- `POST /api/ruzgar/virus-guard/preflight` — `scan_mode=deep|quick`
- `POST /api/ruzgar/virus-guard/commit`
- `POST /api/ruzgar/virus-guard/reject`
- `POST /api/ruzgar/virus-guard/scan-file`
- `GET /api/ruzgar/virus-guard/threat-log`

## Ortam

```env
RUZGAR_VIRUS_GUARD=1
RUZGAR_AV_DEFENDER_BACKUP=0
RUZGAR_AV_CLAM_SUPPORT=0
RUZGAR_AV_FAIL_FAST=1
RUZGAR_VIRUS_GUARD_MAX_MB=2048
```
