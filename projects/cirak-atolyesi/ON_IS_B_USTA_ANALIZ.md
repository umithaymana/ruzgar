# Usta analizi — 10 iş B

Yeşil **10/10** · çırak **10** · kurtarma **0** (nihai doğrulama sonrası)

## Eksikler ve düzeltmeler

1. **Async launch sessiz ölüm** (iş 4–5 ilk dalga): nested `python -c` + DEVNULL → ajan hiç başlamıyordu.  
   **Düzeltme:** `threading` ile doğrudan `/api/chat/full` + `ON_IS_B_LAUNCH.log` + idle re-kick.

2. **Çok-modül görevde `.py` yok** (iş 7–10 ilk dalga): mesajda `util.normalize` vardı, `util.py` yok → `cirak_missing_files` ateşlenmedi; ajan tur atıp dosya yazmadan kaldı.  
   **Düzeltme:** görev satırlarına açık `.py` yolları; `cirak_goal_required_paths` içine `mod.fn` ve `paket/cekirdek.py` çıkarımı (`programlama_faz34.py`).

3. **is-b scope**: `is_cirak_yazim_gorev` artık `/is-b` kabul ediyor.

## Tavan

Disk: `projects_mini_urun_ok` (merdiven sonu). Genel saha / boot / hub kapalı.

## Kanıt

- İlk tam koşu: 10/10 yeşil (5 kurtarma — launch + path).
- 7–10 yeniden: 4/4 `cirak_llm` 1. deneme.
- İş 4 yeniden (threading): `GREEN_CIRAK`.
