# Çırak — Bilgi · Kas · Tecrübe (Mimar raporu)

**Tarih:** 2026-11-18  
**Soru:** Kütüphane yeterli mi / uzanabiliyor mu? Programlar var mı / eksik mi?

---

## 1) Bilgi (kütüphane)

### Rafta ne var? — **BOL**
- Genel kütüphane: `ilim-assistant/knowledge/kutuphane/` (+ sohbet `kütüphane ara`)
- Bilgisayar eserleri: `knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/` (~76k dosya; `01_programlama` … meslek rafları)
- Kavram kartları: `…/bilgisayar_muhendisligi/` (anlık cevap modülü)
- İlim / diğer raflar: `knowledge/ilim`, `ortak_kaynak`, vb.

**Sonuç:** Yol yürümek için **kaynak kıt değil**. Kitaplık dolu.

### Çırak uzanıyor mu? — **görevde KISMI / fiilen HAYIR**

Disk + bilgisayar RAG sidecar **kalın** (~593k chunk). Ama:

| Yol | Uzanır mı? | Ne zaman |
|-----|------------|----------|
| Sohbet «kütüphane / bilgisayar kavram» | **Evet** | `ruzgar_kutuphane` / `ruzgar_bilgisayar_kutuphane` |
| Programlama **görev** turu RAG | **Hayır** | `chat_core._NO_RAG_MODES` içinde `programlama`; Faz21 ağır RAG atlar; çırak fallback `hits=[]` |
| Code agent grep | **Pratikte kütüphane yok** | `search_in_project` yalnız `projects/…` |
| Code agent `read` | **Teorik KISMI** | Kök altı `knowledge/…` okunabilir; prompt/otomatik enjekte yok |
| Supervised çırak (A–G) | **Hayır** | Şablon yazım; kütüphane yok |

**Düz cümle:** Kitaplık dolu; sohbette uzanır. **Görev/çırak borusu bilerek RAG’siz** — “kitaptan öğrenerek kodla” henüz bağlı değil. Sonraki köprü (onayla): göreve dar `read`/bilgisayar-RAG snippet, yazım hâlâ yalnız atölye.

---

## 2) Kas (donanım + program)

### Donanım
Disk boş alan yeterli (~TB ölçeği). Kas tarafı “bilgisayar yetmiyor” değil.

### Programlar (bugün ölçüldü + derin envanter)

| Program | Durum |
|---------|--------|
| Python 3.12 + venv (`venvs\ruzgar`) | Var — `Ruzgar.ps1` ile |
| pytest | Var (PATH/venv); `requirements.txt`’te pin zayıf |
| Git | Var |
| Node / npm / Electron | Var |
| Ollama + Groq/Gemini wiring | Var (`.env` / `RUZGAR_BRAIN.env`) |
| ffmpeg / ripgrep | Var |
| ruff / mypy / Docker / gh | **Yok** veya zayıf (isteğe bağlı) |
| Yerel `ilim-assistant\.venv` | Yok — dış venv kullanılıyor |
| Çırak `pytest_gecir` → birleşik verify | Zayıf — çoğunlukla PASS-print smoke |

**Düz cümle:** Temel kas **var** (yaz, test, git, masaüstü, beyin). Eksik “program yokluğu”ndan çok: **gerçek pytest döngüsünün çırağa bağlanması**, ruff/docker isteğe bağlı. Katman 2 için Python+pytest+git yeter; sıradaki iş kanıtlı fonksiyon+test.

---

## 3) Tecrübe
Senin + ustanın yanında yol yürümek = asıl öğretmen.  
Şu an tecrübe birikimi: atölye A–G + tavan (supervised). LLM ajan tecrübesi hâlâ **zayıf** (timeout / yanlış scope geçmişi).

---

## Net cevap (iki soru)

1. **Kaynak yeterli mi?** Evet (PY4E vb. eserler + RAG kalın).  
   **Uzanıp kullanıyor mu?** Sohbette evet; **görevde fiilen hayır** (programlama no-RAG + grep `projects/` sınırı).

2. **Program eksik mi?** Kritik eksik yok (Python/pytest/git/node/ollama).  
   İsteğe bağlı eksik: **Docker**, **ruff**.  
   Asıl açık: program yokluğu değil; **kütüphaneyi göreve bağlama** + **ajanın kanıtlı yeşil alışkanlığı**.

---

## Önerilen sonraki iş (Mimar kritik sırası)

1. **0A Bilgi köprüsü** — görevde dar kütüphane/read (programlama no-RAG istisnası); yazım hâlâ atölye.  
2. **0B Mimar’ı anla** — `MIMAR_VIZYON.md` (taslak atölyede; Mimar düzeltir) + anlama smoke.  
3. Sonra Katman 2: kaynaklı + kanıtlı küçük fonksiyon/test.  
4. Yol boyunca usta öğretir: istek→plan, projeyi baştan sona okuma.
