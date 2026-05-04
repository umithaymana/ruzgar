# RÜZGAR — GitHub ve bulut dağıtımı

Bu depo masaüstü (Electron `ruzgar-desktop`), yerel API (`ilim-assistant/desktop_server.py`) ve bağlı modülleri içerir. **Tam yığının tek bir sunucuya taşınması** (PyTorch + RAG + Whisper + sürekli Ollama/LLM) bellek ve mimari olarak ağırdır; pratik yaklaşım aşağıdaki gibidir.

## Ne nereye gider?

| Parça | GitHub | Vercel | Railway vb. |
|--------|--------|--------|--------------|
| Kaynak kod | Evet | — | — |
| `desktop_server.py` API | — | Önerilmez | **Uygun** (Docker) |
| Electron masaüstü | Releases ile ikili yayınlanabilir | — | — |

**Vercel:** Sunucu süreleri, dosya sistemi ve sohbet SSE akışı + büyük PyTorch görüntüleri ile **tam `desktop_server` barındırmak** için uygun değildir. Vercelde yalnızca statik site veya ince sunucusuz işlevler tutulur.

**Railway / Render / Fly.io:** `ilim-assistant/Dockerfile` ile HTTP API çalıştırılabilir.

**LLM (Ollama):** Konteynerin içinde Ollama + büyük model çalıştırmak ikinci bir hizmet veya çok daha büyük makine gerektirir. Genelde **`OPENAI_COMPAT_BASE`** ile dışarıdaki bir Ollama/OpenAI uyumlu uç nokta (ör. kendi GPU sunucunuz, Groq/OpenAI uyumlu API) kullanılır.

---

## Adım adım — GitHub

1. **Git yüklü olsun** ([git-scm.com](https://git-scm.com/)).
2. Proje klasöründe `.gitignore` zaten dolu tutulması için kök dizinde bulunuyor (`node_modules`, `.venv`, `google_api_key.txt` vb. repoya gitmez).
3. **İlk yükleme (örnek):**
   ```bash
   cd "PROJE_KÖKÜ"
   git init
   git add .
   git commit -m "İlk commit: RÜZGAR"
   ```
4. GitHub’da yeni bir **boş depo** oluşturun (README eklemeden).
5. Uzak adresi ekleyin ve itin:
   ```bash
   git remote add origin https://github.com/KULLANICI/ruzgar.git
   git branch -M main
   git push -u origin main
   ```
6. **Güvenlik:** Anahtar, `.env`, `ruzgar-desktop/google_api_key.txt` asla push etmeyin.

---

## Adım adım — Railway ile API (`desktop_server`)

1. [railway.app](https://railway.app) hesabı; GitHub depoyu bağlayın.
2. **Yeni proje → Deploy from GitHub** → ilgili depoyu seçin.
3. **Servis ayarları → Root Directory:** `ilim-assistant` olarak ayarlayın (Railway Dockerfile’ı bu klasörde arar veya Dockerfile yolunu buna göre verin).
4. **Dockerfile kullanım:** `ilim-assistant/Dockerfile` ile build edilir.
5. **Değişkenler (Variables)** örnekleri:
   | Değişken | Açıklama |
   |----------|-----------|
   | `PORT` | Railway genelde otomatik verir; elle gerekmez. |
   | `OPENAI_COMPAT_BASE` | LLM adresi; örn. `https://ollama.sunucum.com/v1` veya OpenAI uyumlu URL. |
   | `OPENAI_COMPAT_KEY` | Gerekliyse API anahtarı; Ollama için çoğu kurulumda `ollama`. |
   | `OLLAMA_CHAT_MODEL` | Kullanılacak model adı. |
   | `RUZGAR_STT` | Bellek sıkışırsa `0` yazarak yerel Whisper STT’yi kapatın. |
6. **Sağlık kontrolü:** Dağıtılan URL için `GET /api/health` ve `GET /docs` (FastAPI Swagger) açılabilir olmalı.
7. **Bellek:** `sentence-transformers` + `torch` + ilk istek için model + isteğe bağlı Whisper ağır olabilir. Railway planda RAM yükseltmeyi veya `RUZGAR_STT=0` denemeyini düşünün.

---

## Masaüstü uygulamasını buluttaki API’ye bağlama

`ruzgar-desktop/app.js` içinde API adresi önceliği şöyledir:

1. Adres çubuğundaki parametre: `?api=https://sizin-api.railway.app`
2. Tarayıcı `localStorage` anahtarı: `ruzgarApi`
3. Varsayılan: `http://127.0.0.1:8777`

Örnek: yerel paketlenmiş `index.html` veya geliştirme için  
`file:///.../index.html?api=https://....`

Kalıcı yapmak için geliştirici konsolunda:

`localStorage.setItem('ruzgarApi', 'https://sizin-api.railway.app')`

---

## Docker’ı yerel deneme

PowerShell (`ilim-assistant` üst klasöründen):

```powershell
docker build -f ilim-assistant/Dockerfile -t ruzgar-api ilim-assistant
docker run --rm -p 8777:8777 ^
  -e OPENAI_COMPAT_BASE=http://host.docker.internal:11434/v1 ^
  -e OPENAI_COMPAT_KEY=ollama ^
  ruzgar-api
```

(`host.docker.internal` Windows/Mac’te yaygın; Linux’ta farklı olabilir.)

---

## Dosya özeti

- `ilim-assistant/requirements-api.txt` — Docker / bulutta API için bağımlılıklar (Gradio yok).
- `ilim-assistant/Dockerfile` — API imgesi (`ffmpeg`, Whisper uyumu).
- `ilim-assistant/.dockerignore` — imaj boyutunu ve gereksiz dosyayı azaltır.
- `ilim-assistant/railway.json` — Railway’de Dockerfile build ipucu.
- `requirements.txt` (ilim içinde tam geliştirme) için mevcut `ilim-assistant/requirements.txt` kullanılmaya devam eder.

Sorularınız için bir sorun bildirimi veya dahili dokümantasyon genişletebilirsiniz.
