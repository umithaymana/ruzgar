"""
Metni tema ve duyguya göre sahnelere böler (Ollama / OpenAI uyumlu API).

Gerçekçi beklenti: Bu çıktı 'yönetmen planı'dır. Sinema kalitesinde tam CGI/kısa film
üretmek için Runway/Sora/Kling gibi servisler veya ağır yerel modeller gerekir.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any


def plan_scenes(
    full_text: str,
    theme: str,
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """LLM'den yapılandırılmış sahne listesi JSON döner."""
    base = base_url or os.environ.get("OPENAI_COMPAT_BASE", "http://127.0.0.1:11434/v1")
    key = api_key if api_key is not None else os.environ.get("OPENAI_COMPAT_KEY", "ollama")
    m = model or os.environ.get("OLLAMA_CHAT_MODEL", "llama3.2")

    system = """Sen bir video yönetmeni ve editörüsün. Görevin: verilen metni sinematik sahnelere bölmek.
Her sahne için şunları üret (JSON dizi — yalnızca geçerli JSON, markdown yok):
- scene_id: sıra numarası (1…)
- narration: bu sahnede seslendirilecek metin (orijinal metinden uygun parça, gerekiyorsa kısalt)
- mood: duygusal ton (ör: huzur, heyecan, hüzün, umüt, saygı)
- visual_prompt: sessiz görsel üretimi için İngilizce veya Türkçe kısa sahne tasviri (arka plan, ışık, nesne)
- estimated_seconds: bu sahne için tahmini süre (30–120 arası makul)

Uzun metni mantıklı parçala; toplam sahne sayısı çok uzun metinde 15–40 arası olabilir.
Çıktı şekli kesin olarak: {"scenes": [ {...}, ... ]}"""

    user = f"Tema / bağlam: {theme}\n\nMetin:\n{full_text.strip()}"

    payload = {
        "model": m,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.4,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    raw = body["choices"][0]["message"]["content"].strip()

    json_str = _extract_json(raw)
    parsed = json.loads(json_str)
    if "scenes" not in parsed:
        raise ValueError("Model çıktısında 'scenes' yok.")
    return parsed


def _extract_json(text: str) -> str:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("JSON bulunamadı.")
    return m.group(0)


def save_plan(path: str, plan: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
