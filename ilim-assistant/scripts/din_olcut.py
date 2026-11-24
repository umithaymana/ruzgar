"""D1 — Din ölçütleri (genel çözüm; soruya/esere özel kural YOK).

Koşucu (`altin_set_kos.py`) bu modülü kullanır:
  (a) kaynak verme   : cevapta eser/müellif/bölüm künyesi var mı (doğrulanmış atıf)
  (b) çoklu eser     : cevapta anılan FARKLI eser sayısı (kanıt paketiyle eşleşen)
  (c) uydurma denetimi: cevapta anılan eser/müellif adı kanıt paketindeki (retrieved) künyelerde yoksa şüphe
  (d) sadelik        : ajan puanı (ayrı dosya, `*.sade.json`)

Yöntem (sezgisel, belgeli sınırlar):
- Atıf adayı = «Kaynak izi/Kaynak:» bölümü satırları + eser sözcüğüne bitişik özel ad öbekleri
  (`X adlı eser`, `X'in Y'si`, `... eserinde/kitabında/tefsirinde`) + tırnak/kalın içinde ad + Arapça yazılı ad öbekleri.
- Doğrulama = adayın anlamlı sözcüklerinden en az biri kanıt künyelerinin (eser adı, müellif, kimlik, yol) sözcükleriyle
  (bulanık eşleşme) veya sorunun kendi sözcükleriyle örtüşüyor.
- Şüphe = aday hiçbir künye/soru sözcüğüyle örtüşmüyor (kanıt yokken atıf yapılması dahil).
Sınırlar: yalnız yazılı atıfları görür; model eser anmadan bilgi verirse bu ölçüt onu yakalamaz.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

_TR = str.maketrans({"İ": "i", "I": "i", "ı": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
                     "ö": "o", "Ö": "o", "ç": "c", "Ç": "c", "â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u",
                     "Û": "u", "’": "'", "‘": "'", "`": "'"})
_TASHKEEL = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
_AR_RUN = re.compile(r"[\u0600-\u06FF][\u0600-\u06FF\s]*[\u0600-\u06FF]|[\u0600-\u06FF]{3,}")

# Atıf anlamı taşımayan, her cevapta geçebilen sözcükler (özel ad değil)
_GENEL = {
    "allah", "kuran", "kur'an", "peygamber", "hz", "hazreti", "muhammed", "resulullah", "islam", "musluman", "mekke",
    "medine", "kabe", "umit", "ruzgar", "kaynak", "kaynaklar", "izi", "eser", "kitap", "kitab", "tefsir", "serh",
    "imam", "hadis", "sunnet", "sahabe", "rivayet", "bolum", "baslik", "cilt", "sayfa", "bilgi", "yaklasik", "ornek",
    "turkce", "arapca", "orijinal", "yazar", "muellif", "mualllif", "aynen", "adli", "isimli", "ilim", "alim",
    "ulema", "klasik", "birlikte", "gore", "gibi", "icin", "ancak", "fakat", "ayrica", "yani", "ayet", "sure",
}
_STOP_TOK = _GENEL | {"nin", "nun", "nın", "nün", "in", "un", "ın", "ün", "de", "da", "den", "dan", "ve", "ile", "bir",
                      "bu", "su", "o", "el", "er", "es", "en", "ed", "ez", "ibn", "ebu", "bin", "ben"}

_KAYNAK_BASLIK = re.compile(
    r"(?im)^\s*(?:\*\*)?\s*(?:kaynak\s*izi|kaynaklar|kaynak|künye|kunye|kaynakça)\s*(?:\*\*)?\s*"
    r"(?:[:：]\s*(?:\*\*)?\s*(.*?)|\s*)$"
)
_CUE = r"(?:eser\w*|kitab\w*|kitap\w*|tefsir\w*|şerh\w*|serh\w*|risâle\w*|risale\w*|müsned\w*|musned\w*|sünen\w*|sunen\w*|sahîh\w*|sahih\w*|mecmû\w*|mecmu\w*|ansiklopedi\w*)"
_CAP = r"[A-ZÇĞİÖŞÜÂÎÛ][\w’'\-âîûçğıöşü]*"
_RE_ADLI = re.compile(rf"((?:{_CAP}\s+){{1,4}})(?:adlı\s+|isimli\s+)?{_CUE}")
_RE_GEN = re.compile(rf"({_CAP}(?:\s+{_CAP}){{0,3}})['’](?:n[iıuü]n|[iıuü]n)\s+({_CAP}(?:\s+{_CAP}){{0,3}})")
_RE_ESERDE = re.compile(rf"((?:{_CAP}\s+){{1,4}})(?:{_CUE}\s+)?(?:eserinde|kitabında|tefsirinde|şerhinde|risalesinde|Sahîh'inde|Sahih'inde|Müsned'inde|Sünen'inde)")
_RE_QUOTE = re.compile(r"[«“\"]([^»”\"\n]{3,80})[»”\"]|\*\*([^*\n]{3,80})\*\*")


def fold(s: str) -> str:
    t = unicodedata.normalize("NFKC", s or "").translate(_TR).lower()
    return t


def ar_norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = _TASHKEEL.sub("", s)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ٱ", "ا"), ("ى", "ي"), ("ة", "ه"), ("ؤ", "و"), ("ئ", "ي")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def _tok_clean(t: str) -> str:
    t = fold(t).split("'")[0]
    t = re.sub(r"[^a-z0-9\u0600-\u06ff\-]", "", t)
    t = re.sub(r"^(?:el|er|es|en|ed|ez|et|ul|ur)-", "", t)
    return t.strip("-")


def _tokens(s: str) -> list[str]:
    out = []
    for raw in re.split(r"[\s/\-–—,;:()\[\]·|.]+", s or ""):
        t = _tok_clean(raw) if not re.search(r"[\u0600-\u06ff]", raw) else ar_norm(raw)
        if len(t) >= 3 and t not in _STOP_TOK:
            out.append(t)
    return out


def _ar_tokens(s: str) -> list[str]:
    out = []
    for run in _AR_RUN.findall(s or ""):
        for w in ar_norm(run).split():
            w2 = re.sub(r"^(?:ال|وال|بال|لل|و)(?=.{3,})", "", w)
            if len(w2) >= 3:
                out.append(w2)
    return out


def kunye_token_seti(kunyeler: list[dict]) -> dict[str, set[str]]:
    """eser_id -> token kümesi (Türkçe + Arapça)."""
    out: dict[str, set[str]] = {}
    for i, k in enumerate(kunyeler or []):
        key = str(k.get("eser_id") or k.get("yol_adi") or k.get("yol") or f"k{i}")
        toks: set[str] = set()
        for f in ("eser_tr", "yazar", "eser_id", "yol_adi"):
            toks.update(_tokens(str(k.get(f) or "")))
        for f in ("eser_ar", "yazar_ar"):
            toks.update(_ar_tokens(str(k.get(f) or "")))
        out.setdefault(key, set()).update(toks)
    return out


_AR2LAT = {"ب": "b", "ت": "t", "ث": "s", "ج": "c", "ح": "h", "خ": "h", "د": "d", "ذ": "z", "ر": "r", "ز": "z",
           "س": "s", "ش": "s", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "غ": "g", "ف": "f", "ق": "k", "ك": "k",
           "ل": "l", "م": "m", "ن": "n", "ه": "h"}


def _skel_ar(w: str) -> str:
    """Arapça sözcük → ünsüz iskeleti (Latin yazılışla kaba karşılaştırma için)."""
    w = re.sub(r"^(?:ال|وال|بال|لل)(?=.{3,})", "", ar_norm(w))
    return "".join(_AR2LAT.get(c, "") for c in w)


def _skel_lat(w: str) -> str:
    w = fold(w).split("'")[0]
    for a, b in (("sh", "s"), ("th", "s"), ("dh", "z"), ("kh", "h"), ("gh", "g"), ("q", "k"), ("j", "c"),
                 ("w", ""), ("x", "ks"), ("ç", "c"), ("ş", "s")):
        w = w.replace(a, b)
    w = re.sub(r"^(?:el|al|er|es|en|ed|ez|et)-?", "", w)
    w = re.sub(r"[^a-z]", "", w)
    w = re.sub(r"[aeiouy]", "", w)
    return re.sub(r"(.)\1+", r"\1", w)


def _skel_match(t: str, pool: set[str]) -> bool:
    """Latin yazılmış ad ↔ Arapça künye sözcüğü (ünsüz iskeleti)."""
    if re.search(r"[\u0600-\u06ff]", t):
        return False
    a = _skel_lat(t)
    if len(a) < 3:
        return False
    for p in pool:
        if not re.search(r"[\u0600-\u06ff]", p):
            continue
        b = _skel_ar(p)
        if len(b) >= 3 and SequenceMatcher(None, a, b).ratio() >= 0.8:
            return True
    return False


def _tok_match(t: str, pool: set[str]) -> bool:
    if t in pool:
        return True
    if len(t) < 5:
        return False
    if _skel_match(t, pool):
        return True
    for p in pool:
        if abs(len(p) - len(t)) <= 2 and SequenceMatcher(None, t, p).ratio() >= 0.82:
            return True
        if len(p) >= 6 and len(t) >= 6 and (p in t or t in p):
            return True
    return False


def _strip_md(s: str) -> str:
    s = re.sub(r"\[K\d+\]", " ", s)
    s = s.replace("**", "").replace("__", "")
    return s


def atif_adaylari(cevap: str) -> list[str]:
    """Cevaptan eser/müellif atıf adayı metinleri (sezgisel)."""
    txt = cevap or ""
    adaylar: list[str] = []
    # 1) «Kaynak izi:» bölümü
    lines = txt.splitlines()
    in_k = False
    for ln in lines:
        m = _KAYNAK_BASLIK.match(ln)
        if m:
            in_k = True
            tail = (m.group(1) or "").strip() if m.lastindex else ""
            if tail:
                adaylar.append(_strip_md(tail))
            continue
        if in_k:
            if not ln.strip():
                continue
            if re.match(r"^\s*(?:[-•*]|\d+[.)]|\[K\d+\])", ln):
                adaylar.append(_strip_md(re.sub(r"^\s*(?:[-•*]|\d+[.)])\s*", "", ln)))
            else:
                in_k = False
    plain = _strip_md(txt)
    for rx in (_RE_ADLI, _RE_ESERDE):
        for m in rx.finditer(plain):
            adaylar.append(m.group(1).strip())
    for m in _RE_GEN.finditer(plain):
        # «X'in Y'si»: yalnız Y bir eser sözcüğüyle/büyük harfle başlıyorsa anlamlı; ikisini de aday yap
        adaylar.append(f"{m.group(1)} {m.group(2)}".strip())
    for m in _RE_QUOTE.finditer(txt):
        g = (m.group(1) or m.group(2) or "").strip()
        if g and len(g.split()) <= 8 and not re.search(r"\b(?:hadis|ayet|dua)\b", fold(g)):
            # yalnız bir eser/kaynak cümlesi içindeyse (aynı satırda cue veya Arapça künye)
            line = next((ln for ln in lines if g in ln), "")
            if re.search(_CUE, line, re.I):
                adaylar.append(g)
    # yol/şablon cümleleri atıf değildir (ham yol listesi, «kütüphanemdeki eserlerden okudum» şablonu)
    adaylar = [a for a in adaylar if not re.search(r"knowledge/|\.md\b|kütüphanem|kutuphanem", a, re.I)]
    # tekrar sil
    out, seen = [], set()
    for a in adaylar:
        key = fold(a)[:80]
        if key and key not in seen:
            seen.add(key)
            out.append(a)
    return out[:20]


def kaynak_denetim(cevap: str, kunyeler: list[dict], soru: str = "") -> dict:
    """Atıfları kanıt künyeleriyle karşılaştırır.

    Dönüş: {atif_sayisi, dogrulanan:[...], supheli:[...], eserler:[eser_id,...], kunye_var, eser_sayisi}
    """
    adaylar = atif_adaylari(cevap)
    havuz = kunye_token_seti(kunyeler)
    soru_tok = set(_tokens(soru)) | set(_ar_tokens(soru))
    tum: set[str] = set()
    for v in havuz.values():
        tum |= v
    dogru, supheli, eserler = [], [], []
    for a in adaylar:
        toks = [t for t in _tokens(a)] + _ar_tokens(a)
        toks = [t for t in toks if t not in _STOP_TOK]
        if not toks:
            continue
        # soru sözcükleri atıf değil, konu adıdır
        sig = [t for t in toks if not _tok_match(t, soru_tok)] if soru_tok else toks
        if not sig:
            continue
        eslesen = [k for k, v in havuz.items() if any(_tok_match(t, v) for t in sig)]
        if eslesen:
            dogru.append(a)
            for k in eslesen:
                if k not in eserler:
                    eserler.append(k)
        else:
            supheli.append(a)
    return {
        "atif_sayisi": len(dogru) + len(supheli),
        "dogrulanan": dogru,
        "supheli": supheli,
        "eserler": eserler,
        "kunye_var": bool(dogru),
        "eser_sayisi": len(eserler),
    }
