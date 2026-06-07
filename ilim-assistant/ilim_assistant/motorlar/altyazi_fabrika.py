# Created by Ümit & Gökçenur
"""
Faz S3 — Altyazı fabrikası.

SRT ayrıştırma/yazma, ASS şablonları (sinema / dini / minimal), hedef dile çeviri.
Çeviri: tercume_llm zinciri (Ollama → Groq → Gemini).
"""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ilim_assistant.stt_whisper import format_srt_timestamp

MIMAR = "Ümit & Gökçenur"
FABRIKA_VERSION = "altyazi-fabrika-s3-2026-06-06"

_LANG_LABEL: dict[str, str] = {
    "auto": "Otomatik",
    "tr": "Türkçe",
    "en": "İngilizce",
    "ar": "Arapça",
    "de": "Almanca",
    "fr": "Fransızca",
    "fa": "Farsça",
    "ru": "Rusça",
}

_SRT_TS = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)
_NUM_LINE = re.compile(r"^\s*(\d+)\s*$")
_TRANS_LINE = re.compile(r"^\s*(\d+)\.\s*(.+)\s*$")


class AltyaziSablonu(str, Enum):
    sinema = "sinema"
    dini = "dini"
    minimal = "minimal"


@dataclass(frozen=True)
class AltyaziCue:
    index: int
    start: float
    end: float
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "text": self.text,
        }


def _ts_parts(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def srt_timestamp_to_seconds(ts: str) -> float:
    m = _SRT_TS.search(ts)
    if not m:
        raise ValueError(f"Geçersiz SRT zaman damgası: {ts!r}")
    return _ts_parts(m.group(1), m.group(2), m.group(3), m.group(4))


def seconds_to_ass_time(seconds: float) -> str:
    cs = max(0, int(round(float(seconds) * 100)))
    h, rem = divmod(cs, 360_000)
    m, rem = divmod(rem, 6_000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def parse_srt(content: str) -> list[AltyaziCue]:
    """SRT metnini cue listesine çevirir."""
    raw = (content or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return []
    if raw.startswith("\ufeff"):
        raw = raw.lstrip("\ufeff")

    blocks = re.split(r"\n\s*\n", raw)
    cues: list[AltyaziCue] = []
    idx = 1
    for block in blocks:
        lines = [ln.rstrip() for ln in block.split("\n") if ln.strip()]
        if len(lines) < 2:
            continue
        pos = 0
        if _NUM_LINE.match(lines[0]):
            try:
                idx = int(lines[0].strip())
            except ValueError:
                idx = len(cues) + 1
            pos = 1
        if pos >= len(lines):
            continue
        timing = lines[pos]
        tm = _SRT_TS.search(timing)
        if not tm:
            continue
        start = _ts_parts(tm.group(1), tm.group(2), tm.group(3), tm.group(4))
        end = _ts_parts(tm.group(5), tm.group(6), tm.group(7), tm.group(8))
        body = "\n".join(lines[pos + 1 :]).strip()
        if not body:
            continue
        cues.append(AltyaziCue(index=idx, start=start, end=end, text=body))
        idx += 1
    return cues


def parse_srt_file(path: str | Path) -> list[AltyaziCue]:
    p = Path(path)
    return parse_srt(p.read_text(encoding="utf-8-sig"))


def cues_to_srt(cues: list[AltyaziCue]) -> str:
    lines: list[str] = []
    for i, cue in enumerate(cues, 1):
        num = cue.index if cue.index > 0 else i
        lines.append(str(num))
        lines.append(
            f"{format_srt_timestamp(cue.start)} --> {format_srt_timestamp(cue.end)}"
        )
        lines.append(cue.text.strip())
        lines.append("")
    return "\n".join(lines).strip() + ("\n" if lines else "")


def list_sablonlar() -> list[dict[str, str]]:
    return [
        {
            "id": AltyaziSablonu.sinema.value,
            "label": "Sinema",
            "desc": "Beyaz metin, kalın kontur — genel film/dizi",
        },
        {
            "id": AltyaziSablonu.dini.value,
            "label": "Dini / vakur",
            "desc": "Altın ton, geniş alt boşluk — ilim ve tilavet",
        },
        {
            "id": AltyaziSablonu.minimal.value,
            "label": "Minimal",
            "desc": "Küçük, yarı saydam — dikkat dağıtmayan",
        },
    ]


def _style_block(sablon: AltyaziSablonu) -> tuple[str, str]:
    """(style_name, V4+ Styles satırı)."""
    if sablon == AltyaziSablonu.dini:
        return (
            "RuzgarDini",
            "Style: RuzgarDini,Arial,44,&H00B8E6FF,&H000000FF,&H00303030,&H80000000,"
            "0,0,0,0,100,100,0,0,1,2,0,2,48,48,90,1",
        )
    if sablon == AltyaziSablonu.minimal:
        return (
            "RuzgarMini",
            "Style: RuzgarMini,Arial,34,&H99FFFFFF,&H000000FF,&H00000000,&H40000000,"
            "0,0,0,0,100,100,0,0,1,1,0,2,32,32,42,1",
        )
    return (
        "RuzgarSinema",
        "Style: RuzgarSinema,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,"
        "0,0,0,0,100,100,0,0,1,2,1,2,40,40,58,1",
    )


def cues_to_ass(
    cues: list[AltyaziCue],
    *,
    sablon: str | AltyaziSablonu = AltyaziSablonu.sinema,
    play_res_x: int = 1920,
    play_res_y: int = 1080,
    title: str = "RÜZGAR Altyazı",
) -> str:
    try:
        st = AltyaziSablonu(str(sablon).strip().lower())
    except ValueError:
        st = AltyaziSablonu.sinema
    style_name, style_line = _style_block(st)
    header = [
        "[Script Info]",
        f"Title: {title}",
        "ScriptType: v4.00+",
        f"PlayResX: {int(play_res_x)}",
        f"PlayResY: {int(play_res_y)}",
        "WrapStyle: 0",
        f"Original Script: {MIMAR}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        style_line,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    events: list[str] = []
    for cue in cues:
        text = cue.text.replace("\n", "\\N").strip()
        if not text:
            continue
        events.append(
            f"Dialogue: 0,{seconds_to_ass_time(cue.start)},{seconds_to_ass_time(cue.end)},"
            f"{style_name},,0,0,0,,{text}"
        )
    return "\n".join(header + events) + "\n"


def _subtitle_translate_batch(
    texts: list[str],
    *,
    src_lang: str,
    tgt_lang: str,
) -> list[str]:
    from ilim_assistant.motorlar.tercume_llm import translate_completion

    tgt_label = _LANG_LABEL.get(tgt_lang, tgt_lang)
    src_label = _LANG_LABEL.get(src_lang, src_lang) if src_lang != "auto" else "kaynak dil"
    numbered = "\n".join(f"{i + 1}. {t.replace(chr(10), ' ').strip()}" for i, t in enumerate(texts))
    system = (
        "Sen profesyonel altyazı çevirmenisin. "
        f"Görev: {src_label} altyazı satırlarını {tgt_label} hedef diline çevir.\n"
        "Kurallar:\n"
        "- Her satır ayrı altyazı; kısa ve doğal okunur uzunlukta\n"
        "- Satır sayısını ve numaraları aynen koru\n"
        "- Yalnızca numaralı çeviri satırları döndür; açıklama ekleme"
    )
    user = f"Hedef dil: {tgt_label}\n\n{numbered}"
    res = translate_completion(system, user, max_tokens=min(4000, 120 * len(texts) + 400))
    if not res.get("ok"):
        code = str(res.get("error_code") or "translate_failed")
        hint = str(res.get("hint_tr") or res.get("error") or "Çeviri başarısız")
        raise RuntimeError(f"{code}: {hint}")

    out_lines = [ln.strip() for ln in str(res.get("text") or "").splitlines() if ln.strip()]
    parsed: dict[int, str] = {}
    for ln in out_lines:
        m = _TRANS_LINE.match(ln)
        if m:
            parsed[int(m.group(1))] = m.group(2).strip()
    if len(parsed) >= len(texts):
        return [parsed.get(i + 1, texts[i]) for i in range(len(texts))]

    # Numarasız tek blok — satır satır böl
    if len(out_lines) == len(texts):
        return [ln.lstrip("0123456789.").strip() or texts[i] for i, ln in enumerate(out_lines)]

    # Yedek: tek tek
    singles: list[str] = []
    for t in texts:
        one = translate_completion(
            system,
            f"Hedef dil: {tgt_label}\n\nYalnızca şu altyazı satırını çevir:\n{t}",
            max_tokens=400,
        )
        if one.get("ok"):
            singles.append(str(one.get("text") or t).strip())
        else:
            singles.append(t)
    return singles


def translate_cues(
    cues: list[AltyaziCue],
    *,
    src_lang: str = "auto",
    tgt_lang: str = "tr",
    batch_size: int | None = None,
) -> list[AltyaziCue]:
    if not cues:
        return []
    bs = batch_size or max(4, int(os.environ.get("RUZGAR_SUB_TRANSLATE_BATCH", "10")))
    out: list[AltyaziCue] = []
    for start in range(0, len(cues), bs):
        batch = cues[start : start + bs]
        texts = [c.text for c in batch]
        translated = _subtitle_translate_batch(
            texts,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
        )
        for cue, txt in zip(batch, translated):
            out.append(
                AltyaziCue(
                    index=cue.index,
                    start=cue.start,
                    end=cue.end,
                    text=txt.strip() or cue.text,
                )
            )
    return out


def max_cues_limit() -> int:
    try:
        return max(20, int(os.environ.get("RUZGAR_SUB_MAX_CUES", "800")))
    except ValueError:
        return 800


def process_subtitle_file(
    sub_path: Path,
    *,
    tgt_lang: str | None = None,
    src_lang: str = "auto",
    sablon: str = AltyaziSablonu.sinema.value,
    output_format: str = "ass",
) -> tuple[str, list[AltyaziCue], str]:
    """
    SRT/VTT dosyasını okur; isteğe bağlı çevirir; SRT veya ASS metni döndürür.
    Dönüş: (içerik, cues, format)
    """
    suf = sub_path.suffix.lower()
    raw = sub_path.read_text(encoding="utf-8-sig")
    if suf == ".vtt":
        raw = _vtt_to_srtish(raw)
    cues = parse_srt(raw)
    if not cues:
        raise ValueError("Altyazı dosyasında okunabilir cue yok.")
    if len(cues) > max_cues_limit():
        raise ValueError(f"Çok fazla altyazı satırı (üst sınır {max_cues_limit()}).")

    if tgt_lang and tgt_lang.strip().lower() not in ("", "same", "none", src_lang.lower()):
        cues = translate_cues(cues, src_lang=src_lang, tgt_lang=tgt_lang.strip().lower()[:2])

    fmt = (output_format or "ass").strip().lower()
    if fmt == "srt":
        return cues_to_srt(cues), cues, "srt"
    return cues_to_ass(cues, sablon=sablon), cues, "ass"


def _vtt_to_srtish(vtt: str) -> str:
    """Basit WebVTT → SRT-benzeri metin (Zaman damgası dönüşümü)."""
    lines = vtt.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    idx = 1
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if "-->" in ln:
            timing = ln.replace(".", ",")
            i += 1
            body: list[str] = []
            while i < len(lines) and lines[i].strip() and "-->" not in lines[i]:
                body.append(lines[i].strip())
                i += 1
            if body:
                out.append(str(idx))
                out.append(timing)
                out.extend(body)
                out.append("")
                idx += 1
            continue
        i += 1
    return "\n".join(out)


def write_subtitle_export(
    content: str,
    *,
    export_dir: Path,
    stem: str,
    suffix: str,
) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w\-]+", "_", stem)[:48] or "sub"
    name = f"ruzgar_sub_{uuid.uuid4().hex[:10]}_{safe}{suffix}"
    out = export_dir / name
    out.write_text(content, encoding="utf-8")
    return out
