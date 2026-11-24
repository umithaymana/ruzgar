# Created by Ümit & Gökçenur
"""K3 (din odaklı ilk dilim) — sorguyu kaynak diline taşı: TR/EN soru → Arapça terim/sorgu.

Mimari (Mimar):
  soru kullanıcının dilinde alınır → kavram/terim genişletme (VERİ sözlüğü) → kaynak dilinde (Arapça)
  arama (+ kelime tabanlı yeniden sıralama) → kanıt orijinalde → sentez kullanıcının dilinde;
  künye Arapça orijinale işaret eder (bkz. ``ruzgar_kunye``).

Dil bağımsız tasarım: sorgu dili (`kaynak_dil` = kullanıcının dili) ve kanıt dili (`hedef_dil`) ayrı alanlardır;
şimdilik TR/AR/EN. Sözlük ``data/terim_sozlugu/<alan>.json`` — konuya özel koşul KODDA YOK, yeni terim = yeni veri satırı.

Kapat: ``RUZGAR_K3_DIN_SORGU=0``. İnternet/bulut modele bağımlılık YOK (sözlük yerel veridir).
Sözlükte olmayan terimler için yerel Ollama ile TR→AR çeviri yedeği K3'ün sonraki diliminde (bu dilimde yok).
Boot sırasına dokunmaz; yalnız arama sırasında lazy yüklenir.
"""

from __future__ import annotations

import json
import os
import re
import threading
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

K3_VERSION = "k3-din-sorgu-v1-2026-11-24"

_PKG = Path(__file__).resolve().parent.parent
_SOZLUK_DIR = _PKG / "data" / "terim_sozlugu"

_lock = threading.Lock()
_cache: dict[str, Any] = {"alanlar": None}

_TR_MAP = str.maketrans({"İ": "i", "I": "i", "ı": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
                         "ö": "o", "Ö": "o", "ç": "c", "Ç": "c", "â": "a", "Â": "a", "î": "i", "Î": "i",
                         "û": "u", "Û": "u", "ê": "e", "ô": "o"})
_APOS = re.compile(r"[’‘`'ʿʾʼ´]")
_TASHKEEL = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
_AR_CH = re.compile(r"[\u0600-\u06FF]")

_TR_STOP = {"ve", "ile", "bir", "bu", "su", "o", "mi", "mu", "ne", "nasil", "nedir", "nelerdir", "midir", "hangi",
            "icin", "gibi", "de", "da", "ki", "ya", "ama", "olan", "olarak", "hakkinda", "kimdir", "neden"}
_EN_STOP = {"the", "a", "an", "of", "is", "are", "what", "how", "who", "why", "in", "on", "for", "and", "to", "does", "do"}


def k3_enabled() -> bool:
    return os.environ.get("RUZGAR_K3_DIN_SORGU", "1").strip().lower() not in ("0", "false", "no", "off")


# ---------------------------------------------------------------- normalizasyon
def fold_tr(s: str) -> str:
    t = unicodedata.normalize("NFKC", s or "").translate(_TR_MAP).lower()
    t = _APOS.sub("", t)
    t = t.replace("-", " ")
    return re.sub(r"[^a-z0-9\u0600-\u06ff\s]", " ", t)


def tokens_tr(s: str) -> list[str]:
    return [w for w in fold_tr(s).split() if w]


def ar_norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = _TASHKEEL.sub("", s)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ٱ", "ا"), ("ى", "ي"), ("ة", "ه"), ("ؤ", "و"), ("ئ", "ي")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def _ar_key(term: str) -> list[str]:
    """Arapça terim → anlamlı sözcük kökleri (başta belirli tanımlık atılır; kısa bağlaç/edatlar elenir).

    Parça, terimin TÜM sözcük köklerini (alt-dizgi olarak) taşıyorsa terim eşleşmiş sayılır; böylece
    bitişik ekler (ve-/bi-/li- önekleri) ve araya giren sözcükler eşleşmeyi bozmaz.
    """
    t = ar_norm(term)
    out = []
    for w in t.split():
        w2 = re.sub(r"^ال(?=.{3,})", "", w)
        if len(w2) >= 3:
            out.append(w2)
    return out


def dil_tespit(text: str) -> str:
    """Soru dili: ar | tr | en (kaba, bağımlılıksız). Çok dilli genişletme için ayrı alan."""
    s = text or ""
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return "tr"
    ar = sum(1 for c in letters if _AR_CH.match(c))
    if ar / len(letters) >= 0.35:
        return "ar"
    low = fold_tr(s).split()
    tr_hit = sum(1 for w in low if w in _TR_STOP)
    en_hit = sum(1 for w in low if w in _EN_STOP)
    if re.search(r"[ğüşıöçİĞÜŞÖÇâîû]", s):
        return "tr"
    if en_hit > tr_hit and en_hit >= 1:
        return "en"
    return "tr"


# ---------------------------------------------------------------- sözlük
@dataclass
class _Entry:
    id: str
    alan: str
    w: float
    forms: dict[str, list[list[str]]]   # dil -> [token listesi, ...] ("sözcük$" = yalnız tam eşleşme)
    ar: list[str]
    ar_keys: list[list[str]]
    en: list[str]
    baglam: list[str] = field(default_factory=list)  # bu kavram yalnız burada sayılan kavramlardan biri de eşleşirse geçerli


def _load_alan(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries: list[_Entry] = []
    for g in raw.get("girdiler", []):
        forms: dict[str, list[list[str]]] = {"tr": [], "en": []}
        for f in g.get("tr", []):
            tk = tokens_tr(f.replace("$", ""))
            if tk and f.strip().endswith("$"):
                tk[-1] = tk[-1] + "$"
            if tk:
                forms["tr"].append(tk)
        for f in g.get("en", []):
            tk = tokens_tr(f)
            if tk:
                forms["en"].append(tk)
        ar = [str(x).strip() for x in g.get("ar", []) if str(x).strip()]
        entries.append(_Entry(
            id=str(g.get("id")), alan=str(g.get("alan") or raw.get("alan") or ""),
            w=float(g.get("w", 1.0)), forms=forms, ar=ar,
            ar_keys=[k for k in (_ar_key(a) for a in ar) if k], en=list(g.get("en", [])),
            baglam=[str(x) for x in g.get("baglam", [])],
        ))
    return {"alan": raw.get("alan"), "surum": raw.get("surum"), "entries": entries,
            "alan_kategori": raw.get("alan_kategori", {}), "kaynak_dili": raw.get("kaynak_dili_varsayilan", "ar")}


def yukle_sozlukler(force: bool = False) -> list[dict[str, Any]]:
    with _lock:
        if _cache["alanlar"] is not None and not force:
            return _cache["alanlar"]
        out: list[dict[str, Any]] = []
        if _SOZLUK_DIR.is_dir():
            for p in sorted(_SOZLUK_DIR.glob("*.json")):
                try:
                    out.append(_load_alan(p))
                except Exception:
                    continue
        _cache["alanlar"] = out
        return out


# ---------------------------------------------------------------- eşleştirme
def _tok_eq(q: str, f: str, *, kisa_izin: bool = False) -> bool:
    """Katlanmış sorgu sözcüğü ↔ sözlük sözcüğü. Türkçe çekim eki için ön-ek eşleşmesi (en çok 5 harf ek)."""
    if f.endswith("$"):
        return q == f[:-1]
    if q == f:
        return True
    return len(f) >= (3 if kisa_izin else 4) and q.startswith(f) and (len(q) - len(f)) <= 7


def _find_span(qt: list[str], form: list[str]) -> tuple[int, int] | None:
    n, m = len(qt), len(form)
    if m == 0 or m > n:
        return None
    for i in range(0, n - m + 1):
        if all(_tok_eq(qt[i + j], form[j], kisa_izin=(m > 1 and j > 0)) for j in range(m)):
            return (i, i + m)
    return None


@dataclass
class K3Plan:
    aktif: bool
    kaynak_dil: str
    hedef_dil: str
    yontem: str                       # sozluk | ollama | yok
    kavramlar: list[dict[str, Any]] = field(default_factory=list)
    sorgular: dict[str, list[str]] = field(default_factory=dict)   # hedef dil -> sorgu listesi
    terimler: dict[str, list[tuple[str, float]]] = field(default_factory=dict)  # hedef dil -> (anahtar, ağırlık)
    kavram_anahtarlari: list[list[list[str]]] = field(default_factory=list)  # kavram -> terim -> sözcük kökleri (lexik)
    kelime_terimleri: list[str] = field(default_factory=list)  # ham metinde birebir (bayt) aranacak Arapça öbekler
    kategoriler: list[str] = field(default_factory=list)
    surum: str = K3_VERSION

    def ozet(self) -> dict[str, Any]:
        return {
            "surum": self.surum, "aktif": self.aktif, "kaynak_dil": self.kaynak_dil, "hedef_dil": self.hedef_dil,
            "yontem": self.yontem, "kavramlar": [k["id"] for k in self.kavramlar],
            "sorgular": self.sorgular.get(self.hedef_dil, [])[:5], "kategoriler": self.kategoriler[:6],
        }


def _aktif_mi(selected: list[tuple[_Entry, float, tuple[int, int]]]) -> bool:
    if not selected:
        return False
    ws = sorted((e.w for e, _s, _sp in selected), reverse=True)
    if ws[0] >= 1.0:          # w < 1.0 = genel/zayıf terim (kalp, dünya, tarih...): tek başına tetiklemez
        return True
    return len(ws) >= 2 and ws[0] + ws[1] >= 1.8


def plan_for_query(
    query: str,
    *,
    kaynak_dil: str | None = None,
    hedef_dil: str = "ar",
    max_kavram: int = 3,
) -> K3Plan | None:
    """Sorgudan K3 planı. Kapalıysa / sözlük eşleşmesi yoksa None.

    `query` Arapça ek (" | …") içerebilir; yalnız kullanıcı dilindeki kısım eşleştirilir.
    """
    if not k3_enabled():
        return None
    text = (query or "").split(" | ")[0]
    if not text.strip():
        return None
    src = kaynak_dil or dil_tespit(text)
    if src == hedef_dil:
        return None
    alanlar = yukle_sozlukler()
    if not alanlar:
        return None
    qt = [w for w in tokens_tr(text)]
    if not qt:
        return None
    matches: list[tuple[_Entry, float, tuple[int, int]]] = []
    for al in alanlar:
        for e in al["entries"]:
            best: tuple[float, tuple[int, int]] | None = None
            for form in e.forms.get(src if src in ("tr", "en") else "tr", []):
                sp = _find_span(qt, form)
                if sp is None:
                    continue
                sc = e.w * (1.0 + 0.25 * (len(form) - 1)) * (1.0 + 0.02 * sum(len(t) for t in form))
                if best is None or sc > best[0]:
                    best = (sc, sp)
            if best:
                matches.append((e, best[0], best[1]))
    if not matches:
        return None
    ids = {m[0].id for m in matches}
    matches = [m for m in matches if not m[0].baglam or any(b in ids for b in m[0].baglam)]
    if not matches:
        return None
    # örtüşme: uzun/özgül span kazanır; tamamen içinde kalan kısa kavram elenir
    matches.sort(key=lambda m: (-(m[2][1] - m[2][0]), -m[1]))
    selected: list[tuple[_Entry, float, tuple[int, int]]] = []
    for e, sc, sp in matches:
        contained = any(sp[0] >= s2[0] and sp[1] <= s2[1] and (sp != s2) for _e2, _sc2, s2 in selected)
        same = any(sp == s2 and e2.alan == e.alan for _e2, _sc2, s2 in selected for e2 in [_e2])
        if contained:
            continue
        if same and len(selected) >= 1 and sum(1 for _e, _s, s2 in selected if s2 == sp) >= 2:
            continue
        selected.append((e, sc, sp))
    selected.sort(key=lambda m: -m[1])
    selected = selected[: max(1, max_kavram + 1)]
    aktif = _aktif_mi(selected)
    kav = [{"id": e.id, "alan": e.alan, "w": e.w, "skor": round(sc, 2)} for e, sc, _sp in selected]
    top = selected[:max_kavram]
    # sorgular (hedef dil)
    sorgular: list[str] = []
    if hedef_dil == "ar":
        first_terms = [e.ar[0] for e, _s, _p in top if e.ar]
        if len(first_terms) >= 2:
            sorgular.append(" ".join(first_terms))
        for e, _s, _p in top:
            if e.ar:
                sorgular.append(e.ar[0])
                if len(e.ar) > 1 and e is top[0][0]:
                    sorgular.append(e.ar[1])
    elif hedef_dil == "en":
        for e, _s, _p in top:
            if e.en:
                sorgular.append(e.en[0])
    seen: set[str] = set()
    sorgular = [s for s in sorgular if not (s in seen or seen.add(s))][:5]
    terimler: list[tuple[str, float]] = []
    kavram_anahtarlari: list[list[str]] = []
    for e, sc, _p in selected:
        if hedef_dil == "ar":
            keys = [list(k) for k in e.ar_keys]
        else:
            keys = [fold_tr(x).split() for x in e.en if fold_tr(x).strip()]
        kavram_anahtarlari.append(keys)
        for k in keys:
            terimler.append((" ".join(k), float(e.w)))
    # kelime tabanlı (birebir öbek) arama terimleri: özgül (çok sözcüklü / uzun) Arapça öbekler
    kelime: list[str] = []
    if hedef_dil == "ar":
        for e, _sc, _p in selected[:max_kavram]:
            for a in e.ar:
                raw = _TASHKEEL.sub("", a).strip()
                n_words = len(raw.split())
                letters = len(raw.replace(" ", ""))
                if (n_words >= 2 and letters >= 7) or (letters >= 6 and e.w >= 1.3):
                    if raw not in kelime:
                        kelime.append(raw)
        kelime = kelime[:6]
    # kategori ipuçları (veri)
    cats: list[str] = []
    for al in alanlar:
        ak = al.get("alan_kategori", {})
        for e, _sc, _p in selected:
            for c in ak.get(e.alan, []):
                if c not in cats:
                    cats.append(c)
    return K3Plan(
        aktif=aktif, kaynak_dil=src, hedef_dil=hedef_dil, yontem="sozluk", kavramlar=kav,
        sorgular={hedef_dil: sorgular}, terimler={hedef_dil: terimler},
        kavram_anahtarlari=kavram_anahtarlari, kategoriler=cats, kelime_terimleri=kelime,
    )


# ---------------------------------------------------------------- kelime tabanlı (lexik) yeniden sıralama
def lex_skor(text: str, plan: K3Plan | None, *, hedef_dil: str = "ar") -> tuple[float, int]:
    """Parçada plan kavramlarının kaç tanesi geçiyor? (bonus, eşleşen kavram sayısı).

    Arapça: harekesiz/normalize metinde alt-dizgi (başta «ال» atılmış anahtar) araması; Latin: katlanmış metin.
    """
    if plan is None or not plan.aktif:
        return 0.0, 0
    if hedef_dil == "ar":
        blob = ar_norm(text or "")
    else:
        blob = fold_tr(text or "")
    hit = 0
    bonus = 0.0
    for keys, kav in zip(plan.kavram_anahtarlari, plan.kavramlar):
        if any(ws and all(w in blob for w in ws) for ws in keys):
            hit += 1
            bonus += 0.05 * float(kav.get("w", 1.0))
    if hit >= 2:
        bonus += 0.04 * (hit - 1)
    return min(0.30, bonus), hit


def blob_has_terms(text: str, plan: K3Plan | None) -> bool:
    return lex_skor(text, plan)[1] > 0


def kanit_alakali_mi(plan: K3Plan | None, hits: Sequence[Any]) -> bool:
    """Kanıt paketinde plan kavramlarından en az birini taşıyan parça var mı (usable kararı için)."""
    if plan is None or not plan.aktif:
        return True
    for h in hits or []:
        try:
            if lex_skor(str(h[0]), plan)[1] > 0:
                return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------------- sentez talimatı (kanıt dili ≠ cevap dili)
def _arapca_oran(text: str) -> float:
    letters = [c for c in text or "" if c.isalpha()]
    if len(letters) < 8:
        return 0.0
    return sum(1 for c in letters if _AR_CH.match(c)) / len(letters)


def kanit_dil_notu(blocks: Iterable[Any], *, want_source: bool = False, cevap_dili: str = "tr") -> str:
    """Kanıt blokları kaynak dilinde (Arapça) ise sentez talimatı: kullanıcının dilinde sade anlat, künyeyi koru.

    Boş döner: K3 kapalı / kanıt Arapça değil. Dil bağımsız: `cevap_dili` ileride genişletilir.
    """
    if not k3_enabled():
        return ""
    n_ar = 0
    n = 0
    for b in blocks or []:
        try:
            t = str(b[0])
        except Exception:
            continue
        n += 1
        if _arapca_oran(t) >= 0.4:
            n_ar += 1
    if n_ar == 0:
        return ""
    dil = {"tr": "Türkçe", "en": "İngilizce", "ar": "Arapça"}.get(cevap_dili, "Türkçe")
    lines = [
        "\n\n[TALİMAT — K3 — ARAPÇA KANIT → SENTEZ]\n",
        f"Kanıt parçalarının {n_ar} tanesi **Arapça orijinal eser metnidir**. Cevabı **{dil}**, sade ve herkesin anlayacağı "
        "biçimde yaz: Arapça metni yapıştırma, anlamını aktar (yalnız gerekirse tek bir terimi/ifadeyi Arapça yaz). "
        "Önce kısa net cevap, sonra gerekirse kısa ayrıntı.\n",
        "- Kanıt parçası soruyu karşılıyorsa **onu kullan**; alakasız parçayı yok say. Pasajdaki hükmü/iddiayı olduğundan "
        "güçlü veya zayıf gösterme.\n",
        "- Eser ve müellifi, bağlamdaki etikette görünen künyeyle an (Arapça eser adı — müellif); etikette olmayan eser, "
        "müellif, bölüm, cilt, sayfa, hadis/ayet numarası **uydurma**.\n",
        "- Birden çok eser varsa «… eserine göre …, … eserinde ise …» diye **ayrı eserlere** atıf yap (en çok 3).\n",
    ]
    if want_source:
        lines.append(
            "- Kullanıcı **kaynak istedi**: cevabın sonunda **Kaynak izi:** başlığı altında kullandığın her eseri "
            "«[K#] Arapça eser adı — müellif» biçiminde listele (yalnız bağlamdaki künyeler).\n"
        )
    return "".join(lines)
