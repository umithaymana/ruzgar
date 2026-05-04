"""NLLB ile metin çevirisi (çevrimiçi model indirme — ilk çalıştırmada)."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Hız/hafıza dengesi: distilled-600M hafif; kalite için NLLB_DISTILLED_SIZE=1.3B veya tam modeller
_DEFAULT_MODEL = os.environ.get(
    "NLLB_MODEL",
    "facebook/nllb-200-distilled-600M",
)


@lru_cache(maxsize=1)
def _load(model_name: str):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()
    return tokenizer, model, device


def translate_text(
    text: str,
    src_nllb: str,
    tgt_nllb: str,
    model_name: Optional[str] = None,
    max_length: int = 1024,
) -> str:
    """
    NLLB ile çeviri. Dini/edebi metinlerde hata olabilir; kritik yayın için insan gözden geçirmesi önerilir.
    """
    if not text.strip():
        return ""
    name = model_name or _DEFAULT_MODEL
    tokenizer, model, device = _load(name)

    tokenizer.src_lang = src_nllb
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    forced_bos_token_id = tokenizer.lang_code_to_id[tgt_nllb]

    with torch.no_grad():
        out = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=max_length,
            num_beams=5,
            early_stopping=True,
        )

    return tokenizer.batch_decode(out, skip_special_tokens=True)[0]
