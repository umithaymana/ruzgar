# İlim Assistant — **RÜZGAR**

Varsayılan asistan adı **RÜZGAR**; hitap **Ümit abi**. Mesajda “Rüzgar” / “ruzgar” geçince ilk yanıt cümlesi sabit karşılamadır — metinler `ilim_assistant/persona.py` içinde değiştirilebilir.

Türkçe/Arapça dilbilgisi, edebiyat, tecvid notları ve benzeri bilgileri **Markdown** dosyalarında toplayıp; **gömme (embedding) + arama** ile modele bağlam olarak veren ve **Ollama** (yerel LLM) ile sohbet ettiren yapı.

**Telefon veya PC’de sesle “Rüzgar” demek** bu projenin tek başına parçası değildir: Android’de Google Asistan rutini / kısayol, iPhone’da Kısayollar, Windows’ta mikrofon + özel uygulama veya wake-word yazılımı gerekir; mikrofon metni Gradio kutusuna yazdırabilirsin.

## “Hepsini öğretmek” nasıl olur?

Modeli sıfırdan eğitmek şart değil. Pratik yol:

1. `knowledge/` altına konuya göre `.md` dosyaları ekle (özet, kendi notların, izinli içerik).
2. `python -m ilim_assistant.ingest_cli` ile indeks oluştur.
3. Sorularda ilgili parçalar otomatik bulunup LLM’e verilir (**RAG**).

## Sohbet ve gelişim (“kendini geliştirme”)

- Tam anlamıyla **otomatik sürekli öğrenme** yok (yanlış bilgiyi kalıcı yazma riski).
- **Son turu kaydet** ile sohbeti `knowledge/learned/` altına yazıp indeksi güncellersen, bir sonraki sorularda bu metinler **RAG ile tekrar kullanılır** — pratikte sen kontrollü şekilde sistemi güçlendirirsin.

## Web’den bilgi

- **DuckDuckGo** ile arama özeti; isteğe bağlı olarak ilk birkaç sonuç URL’sinden **sayfa metni** çekilir (`beautifulsoup4`).
- Varsayılan: `ENABLE_WEB_SEARCH=1`. Kapatmak için `ENABLE_WEB_SEARCH=0`.
- Siteler bot trafiğini engelleyebilir; içerik **doğrulanmamıştır**. Çok kaynaklı çelişkileri LLM’e not düşecek şekilde sistem istemi güncellendi.

## Kod yazma

- Kod modu sistem istemi **polyglot** tanımlıdır (istem dilinde çok sayıda dil ailesi); alt modelin gücü ve güncelliği yanıt kalitesini belirler.
- Arayüzde **Kod / yazılım modu**: ayrı sistem istemi + isteğe bağlı kod modeli.
- Yerelde güçlü sonuç için örnek: `ollama pull qwen2.5-coder:7b` ve ortamda `OLLAMA_CHAT_MODEL_CODING=qwen2.5-coder:7b`.
- Bulut API ile üst seviye mantık için `OPENAI_COMPAT_BASE` ve anahtarı kullanabilirsin (OpenAI uyumlu uç noktalar).

## Hız (gecikme)

- **Yerel indeks (RAG):** İndeks dosyaları artık **bellekte önbelleklenir**; her soruda tüm `chunks.jsonl` / `embeddings.npy` diskten okunmaz. İndeksi yenilediğinde (`ingest_cli`) önbellek dosya zamanına göre kendiliğinden yenilenir. Kapatmak için: `RAG_INDEX_CACHE=0`.
- **İlk cevap:** API ve Gradio açılırken **RAG ısıtması** (`warmup_index`) çalışır; gömme modeli ve indeks ilk mesajdan önce yüklenir.
- **Model:** Gecikmenin büyük kısmı **Ollama / yerel LLM** hızıdır. Projede **varsayılan** sohbet modeli **`llama3.2:3b`** (kod: `ilim_assistant/defaults.py`); daha güçlü alternatif: `ollama pull qwen2.5:7b` ve `OLLAMA_CHAT_MODEL=qwen2.5:7b`. Uzun yanıt süresi için `CHAT_MAX_TOKENS` düşürülebilir (varsayılan 720).
- **Web araması:** Açıkken ek gecikme vardır; hız için Gradio’da web kutusu kapalı / `fetch_pages=0` kullan.

## Gerçekçi beklenti

- **İstediğin her bilgi:** Pratikte arama + sayfa çekimi ile çok geniş kapsama yaklaşırsın; yine de ücretli duvarlar, CAPTCHA ve hukuki kısıtlar vardır.
- **Cursor’daki üst model kadar kod:** Aynı donanımda küçük yerel model **aynı kaliteyi garanti etmez**; kod için **coder modeli**, mümkünse **GPU** ve istenirse **API** gerekir.

## Onaylı PC işlemleri (Windows)

`gradio_chat.py` içinde **Onaylı işlemler (PC)** sekmesi: ön tanımlı komutlar (ör. `winget` ile Python, Windows Defender taraması, tehdit listesini salt okunur gösterme) yalnızca **önizleme + iki onay kutusu** ile çalışır. Rüzgar sohbetten tek başına komut çalıştıramaz.

- **Sistem klasörlerine yazma / sessiz silme yok**; tehdit silme için Windows **Güvenlik** uygulamasını kullan.
- **%100 virüs algılama** iddiası yok; asıl motor Defender tanımları + güncellemeler + sağduyu.

## Kurulum

```bash
pip install -r requirements.txt
ollama pull llama3.2:3b
python -m ilim_assistant.ingest_cli
python gradio_chat.py
```

Ollama varsayılan adres: `http://127.0.0.1:11434/v1` (OpenAI uyumlu). Sohbet modeli: ortam değişkeni `OLLAMA_CHAT_MODEL` (belirtilmezse **`llama3.2:3b`**). Daha yavaş ama genelde daha güçlü: `OLLAMA_CHAT_MODEL=qwen2.5:7b` (önce `ollama pull qwen2.5:7b`).

### Windows: hangi dosya neyi başlatır?

| Dosya (proje kökü) | Ne açılır |
|---------------------|-----------|
| **`Ruzgar_Hepsi.bat`** | Yerel API (**8777**) + **tarayıcı Gradio (7861)** + **Electron masaüstü** — ikisi bir arada |
| **`Ruzgar.bat`** | API + Electron (tarayıcı yok; daha az RAM) |
| **`Ruzgar_Baslat.bat`** | Yalnızca Gradio tarayıcı (**7861**) |

İkisini birden kullanırken **embedding modeli iki Python sürecinde yüklenebilir** (Gradio + API); RAM düşükse `Ruzgar.bat` ile yalnızca masaüstünü kullanın.

## Portlar

- İlim Assistant sohbet (Gradio): **7861** (varsayılan)
- Rüzgar masaüstü API (`desktop_server`): **8777**
- `ilim-voice` TTS arayüzü: **7860**
