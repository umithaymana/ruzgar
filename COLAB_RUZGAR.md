# Rüzgar + Google Colab (PC'yi rahatlatma)

Laptop'ta «düşünüyor» takılıyorsa: ağır iş **Colab GPU/CPU**'da, PC'de sadece **Electron arayüzü** çalışır.

## 1) Colab'da motoru aç

1. [Google Colab](https://colab.research.google.com) → **Runtime → Change runtime type → GPU** (T4 yeterli).
2. `ruzgar_colab_motor.ipynb` dosyasını açın (proje kökünde).
3. Hücreleri **sırayla çalıştırın** (proje Drive'a yüklü veya GitHub'dan klonlanır).
4. **ngrok token**: https://dashboard.ngrok.com/get-started/your-authtoken
5. Son hücre **https://….ngrok-free.app** adresini yazdırır.

## 2) PC'de bağla

PowerShell:

```powershell
cd "D:\CURSOR PROJELER\YAPAY ZEKA"
.\scripts\Set-RuzgarColabUrl.ps1 -Url "https://XXXX.ngrok-free.app"
.\Ruzgar.ps1
```

`ruzgar_remote_api.txt` Colab adresini içerir; yerel API ve Ollama **başlatılmaz**.

## 3) Sadece bulut (Colab olmadan)

`ilim-assistant\RUZGAR_BRAIN.env` içinde Gemini + Groq anahtarları varsa ve `RUZGAR_DISABLE_LOCAL_OLLAMA=1` ise Rüzgar yerelde de yalnızca buluta gider (hafif mod).

```powershell
.\Ruzgar.ps1 -ForceRestart
```

## Sorun giderme

| Belirti | Çözüm |
|--------|--------|
| Sürekli düşünüyor | Colab hücresi çalışıyor mu? ngrok URL güncel mi? |
| 404 / bağlanamıyor | `Set-RuzgarColabUrl` — sonda `/api` **yok** |
| Gemini hata | `RUZGAR_BRAIN.env` → `GLOBAL_API_KEY` |
| Colab oturumu kapandı | Notebook'u yeniden çalıştır, yeni ngrok URL yaz |
