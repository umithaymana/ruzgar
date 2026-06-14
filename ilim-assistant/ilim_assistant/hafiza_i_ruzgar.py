import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class HafizaIRuzgar:
    """
    Çok basit, katı kurallı bir öğrenme motoru.

    - Sadece `ruzgar_genel_hafiza.json` dosyasına bakar.
    - Açılışta dosyayı RAM'e yükler, sonrasında RAM'den cevap verir.
    - "[Soru] = [Cevap]" komutuyla kalıcı olarak öğrenir.
    """

    GENEL_HAFIZA_DOSYASI_ADI = "ruzgar_genel_hafiza.json"
    ESKI_DOSYA_ADLARI = ("hafiza_arsivi.json", "ogrenme_merkezi.json")
    VARSAYILAN_MOTOR_TIPI = "Hafıza"
    BILINMEYEN_YANIT = "Mimar, bunu henüz öğrenmedim, bana öğretir misin?"

    # Fuzzy eşik: 0.70 = %70 benzerlik. RUZGAR_FUZZY_MIN env değişkeniyle override edilebilir.
    FUZZY_VARSAYILAN_ESIK = 0.70

    # Token kapsama (sorgu kelimelerinin adayda bulunma oranı) → karakter benzerliği yetmediğinde
    # asıl kararı veren ikinci eksen. Tam kapsama %92 puan değerindedir; eşik %70'i geçer.
    TOKEN_KAPSAMA_AGIRLIK = 0.92
    # Token bazlı kelime karşılaştırmasında, iki kelimenin "aynı" sayılması için minimum
    # SequenceMatcher skoru (typo toleransı). Örn: "phyton" ↔ "python" = 0.92, eşik altı kalmaz.
    TOKEN_KELIME_BENZERLIK_ESIK = 0.85
    # Anlamsız kısa Türkçe ekler/edatlar — token kümesinden çıkarılır ki tek başlarına eşleşmesin.
    # Not: `_fuzzy_anahtar` Türkçe karakterleri ASCII'ye çevirdiği için liste de ASCII'dir.
    TOKEN_STOPWORDS = frozenset({
        "ne", "mi", "mu",
        "bir", "bu", "su", "o",
        "ve", "veya", "ama", "fakat", "icin",
        "de", "da", "ki", "ya", "ile",
        "den", "dan", "yi", "yu", "i", "u",
        "kimdir", "kimdi", "kimesne", "nedir",
    })

    # Baş/sondaki ayırıcı ve noktalama (Türkçe dahil)
    _STRIP_EDGE_PUNCT = re.compile(
        r'^[\s!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~¡§¨°´¿。“”‘’…、。￥]+|'
        r'[\s!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~¡§¨°´¿。“”‘’…、。￥]+$',
        re.UNICODE,
    )

    @classmethod
    def _norm_eslesme(cls, metin: str) -> str:
        """Fuzzy anahtar: büyük-küçük harf, ünlem/soru işareti, fazla boşluk, baş/son noktalama yok sayılır."""
        t = (metin or "").strip()
        if not t:
            return ""
        t = unicodedata.normalize("NFKC", t).casefold()
        for _ in range(16):
            nt = cls._STRIP_EDGE_PUNCT.sub("", t).strip()
            nt = re.sub(r"\s+", " ", nt).strip()
            if not nt:
                return ""
            if nt == t:
                break
            t = nt
        return t

    # Türkçe → ASCII benzeri tablo: yazım hatası toleransı için fuzzy karşılaştırmada kullanılır.
    _TR_HARITA = str.maketrans({
        "ı": "i", "İ": "i", "ş": "s", "Ş": "s",
        "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
        "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
    })
    _KIM_IDENTITY_SUFFIX = re.compile(
        r"\s+(?:kimdir|kimdi|kim|kimi|kimesne|nedir)\s*[\?.!…]*\s*$",
        re.I,
    )

    @classmethod
    def _strip_identity_question_suffix(cls, metin: str) -> str:
        t = (metin or "").strip()
        for _ in range(3):
            nt = cls._KIM_IDENTITY_SUFFIX.sub("", t).strip()
            if nt == t:
                break
            t = nt
        return re.sub(r"\s+", " ", t).strip()

    @classmethod
    def _fuzzy_anahtar(cls, metin: str) -> str:
        """Fuzzy karşılaştırma için ek sadeleştirme: TR karakterleri → ASCII, tüm noktalama silinir.

        Not: birebir/normal eşleşme için kullanılan `_norm_eslesme`'den ayrıdır;
        sadece Levenshtein/SequenceMatcher skorunu artırmak için kullanılır.
        """
        t = cls._norm_eslesme(metin)
        if not t:
            return ""
        t = t.translate(cls._TR_HARITA)
        # tüm noktalama ve özel karakter sil, sadece harf-rakam-boşluk bırak
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    @classmethod
    def _benzerlik(cls, a: str, b: str) -> float:
        """0.0–1.0 arası benzerlik skoru. SequenceMatcher (yerleşik, ek bağımlılık yok)."""
        if not a or not b:
            return 0.0
        if a == b:
            return 1.0
        return SequenceMatcher(None, a, b).ratio()

    @classmethod
    def _token_kumesi(cls, metin: str) -> frozenset:
        """Anlamlı kelime kümesi: TR→ASCII sadeleştirilmiş, stopword'siz, en az 2 karakterli.

        Kısa-uzun kıyaslamada "aynı kelimeler geçiyor mu?" sorusunu cevaplamak için kullanılır.
        """
        t = cls._fuzzy_anahtar(metin)
        if not t:
            return frozenset()
        return frozenset(
            w for w in t.split()
            if w and len(w) >= 2 and w not in cls.TOKEN_STOPWORDS
        )

    @classmethod
    def _token_kapsama(cls, sorgu_tok: frozenset, aday_tok: frozenset) -> float:
        """Sorgu kelimelerinin ne kadarı adayda bulunuyor? (typo toleranslı)

        - 0.0 → ortak hiç kelime yok
        - 1.0 → sorgudaki tüm kelimeler adayda mevcut (yazım hataları affedilir)
        Aday adayın kelime sayısı önemli değil; bakış açısı kullanıcının sorgusudur.
        """
        if not sorgu_tok or not aday_tok:
            return 0.0
        bulundu = 0
        for s in sorgu_tok:
            if s in aday_tok:
                bulundu += 1
                continue
            # Typo toleransı: aday kelimelerden biri ile yüksek benzerlik
            for a in aday_tok:
                if cls._benzerlik(s, a) >= cls.TOKEN_KELIME_BENZERLIK_ESIK:
                    bulundu += 1
                    break
        return bulundu / len(sorgu_tok)

    @classmethod
    def _fuzzy_esik(cls) -> float:
        """RUZGAR_FUZZY_MIN env değişkeni ile override; varsayılan 0.70."""
        raw = (os.environ.get("RUZGAR_FUZZY_MIN") or "").strip()
        if not raw:
            return cls.FUZZY_VARSAYILAN_ESIK
        try:
            v = float(raw)
        except ValueError:
            return cls.FUZZY_VARSAYILAN_ESIK
        if v <= 0:
            return cls.FUZZY_VARSAYILAN_ESIK
        if v > 1.0:
            v = v / 100.0
        return max(0.0, min(1.0, v))

    def __init__(self, dosya_yolu: Path | str | None = None) -> None:
        proje_koku = Path(__file__).resolve().parents[1]
        if dosya_yolu is not None:
            self._dosya_yolu = Path(dosya_yolu)
        else:
            try:
                from ilim_assistant.ruzgar_public_mode import genel_hafiza_path, current_user_id

                self._dosya_yolu = genel_hafiza_path(current_user_id())
            except Exception:
                self._dosya_yolu = proje_koku / self.GENEL_HAFIZA_DOSYASI_ADI
        self._eski_dosya_yollari = [
            Path(os.path.join(str(proje_koku), ad)) for ad in self.ESKI_DOSYA_ADLARI
        ]
        self._kayitlar: List[Dict[str, str]] = []
        self._hafiza: Dict[str, str] = {}
        self._ogrenme_disk_mtime_ns: int | None = None
        self._yukle_veya_olustur()

    def _disk_mtime_ns(self) -> int | None:
        try:
            st = self._dosya_yolu.stat()
            m = getattr(st, "st_mtime_ns", None)
            return m if isinstance(m, int) else int(float(st.st_mtime) * 1e9)
        except OSError:
            return None

    def _sync_disk_mtime_after_load(self) -> None:
        self._ogrenme_disk_mtime_ns = self._disk_mtime_ns()

    def _reload_if_disk_changed(self) -> None:
        """Tur başına tam dosya okuması yapmadan, yalnızca değiştiyse RAM'i tazeler."""
        self._ensure_store_ready()
        cur = self._disk_mtime_ns()
        if cur is None:
            return
        if self._ogrenme_disk_mtime_ns == cur:
            return
        self._yukle_veya_olustur()

    @staticmethod
    def _normalize_loaded_store(obj: object) -> List[Dict[str, str]]:
        """
        Diskten okunan veriyi güvenli şekilde kayıt listesine çevirir.

        Desteklenen eski/yeni yapılar:
        - {"kayitlar": [ ... ]}
        - {"sozluk": {"soru": "cevap", ...}}
        - {"soru": "cevap", ...}
        - [{"soru": "...", "cevap": "..."}, ...]
        """
        out: List[Dict[str, str]] = []
        if isinstance(obj, dict) and isinstance(obj.get("kayitlar"), list):
            obj = obj.get("kayitlar", [])
        if isinstance(obj, dict) and isinstance(obj.get("sozluk"), dict):
            obj = obj.get("sozluk", {})
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(k, str) and isinstance(v, str):
                    kk = k.strip()
                    vv = v.strip()
                    if kk and vv:
                        out.append(
                            {
                                "motor_tipi": HafizaIRuzgar.VARSAYILAN_MOTOR_TIPI,
                                "soru": kk,
                                "cevap": vv,
                            }
                        )
            return out
        if isinstance(obj, list):
            for row in obj:
                if not isinstance(row, dict):
                    continue
                s = str(row.get("soru", "")).strip()
                c = str(row.get("cevap", "")).strip()
                if s and c:
                    mt = str(
                        row.get("motor_tipi") or HafizaIRuzgar.VARSAYILAN_MOTOR_TIPI
                    ).strip()
                    rec = {"motor_tipi": mt or HafizaIRuzgar.VARSAYILAN_MOTOR_TIPI, "soru": s, "cevap": c}
                    ts = str(row.get("ts", "")).strip()
                    if ts:
                        rec["ts"] = ts
                    out.append(rec)
        return out

    def _sync_hafiza_view(self, motor_tipi: str = VARSAYILAN_MOTOR_TIPI) -> None:
        mt = (motor_tipi or self.VARSAYILAN_MOTOR_TIPI).strip() or self.VARSAYILAN_MOTOR_TIPI
        out: Dict[str, str] = {}
        for row in self._kayitlar:
            if row.get("motor_tipi") != mt:
                continue
            s = row.get("soru", "").strip()
            c = row.get("cevap", "").strip()
            if s and c:
                out[s] = c
        self._hafiza = out

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def _cevap_yer_tutucu_mu(cls, cevap: str) -> bool:
        """JSON satırı 'bilinmiyor' yer tutucusuysa anında yanıt veya fuzzy adayı olmasın."""
        if not (cevap or "").strip():
            return True
        c = unicodedata.normalize("NFKC", str(cevap).strip()).lower()
        if c == unicodedata.normalize("NFKC", cls.BILINMEYEN_YANIT).strip().lower():
            return True
        if "öğrenmedim" not in c and "ogrenmedim" not in c:
            try:
                from ilim_assistant.ruzgar_egitim import cevap_kullaniciya_okunmamali

                if cevap_kullaniciya_okunmamali(cevap):
                    return True
            except Exception:
                pass
            return False
        return "mimar" in c or "öğretir" in c or "ogretir" in c

    # ----------------- Dış API -----------------
    def cevap_ver(self, metin: str) -> str:
        """
        Dışarıdan çağrılan ana fonksiyon.

        - Eğer metin 'Soru = Cevap' biçimindeyse, öğrenme moduna geçer.
        - Aksi halde hazır hafızadan cevap döndürür.
        """
        self._reload_if_disk_changed()
        metin = metin.strip()

        if "=" in metin:
            return self._yeni_bilgi_isle(metin)

        # Tam anahtar eşleşmesi
        ans = self.ogrenme_cevabi_bak(metin, motor_tipi=self.VARSAYILAN_MOTOR_TIPI)
        if ans is not None:
            return ans

        # Esnek eşleşme (büyük/küçük harf, ünlem vb.)
        return self.BILINMEYEN_YANIT

    def ogrenme_cevabi_bak(self, metin: str, motor_tipi: str | None = None) -> Optional[str]:
        """Öğretmez; sözlükte arar. `motor_tipi=None` ise tüm raflarda arar.

        Arama sırası (hızlı → tolerant):
          1) Birebir tam eşleşme.
          2) Normalize eşleşme (lowercase + kenar noktalama temizliği).
          3) FUZZY: SequenceMatcher tabanlı benzerlik skoru; yazım hatası, eksik harf,
             Türkçe karakter farkı, fazladan kelime gibi hatalara dayanıklı.
             Eşik varsayılan %70 (RUZGAR_FUZZY_MIN ile değiştirilebilir).
        """
        detay = self.ogrenme_cevabi_bak_detayli(metin, motor_tipi=motor_tipi)
        return detay.get("cevap") if detay else None

    def ogrenme_cevabi_bak_detayli(
        self, metin: str, motor_tipi: str | None = None
    ) -> Optional[dict]:
        """Sözlük araması; eşleşme türü ve skor ile döner.

        Dönüş: ``{"cevap", "soru", "eslesme": "tam"|"norm"|"fuzzy", "skor": float}``
        """
        self._reload_if_disk_changed()
        t = (metin or "").strip()
        if not t or "=" in t:
            return None
        mt = (motor_tipi or "").strip() or None
        adaylar = self._kayitlar
        if mt is not None:
            adaylar = [r for r in self._kayitlar if r.get("motor_tipi") == mt]

        for row in reversed(adaylar):
            if row.get("soru", "") == t:
                ans = row.get("cevap", "")
                if self._cevap_yer_tutucu_mu(ans):
                    continue
                return {
                    "cevap": ans,
                    "soru": row.get("soru", ""),
                    "eslesme": "tam",
                    "skor": 1.0,
                }

        nq = self._norm_eslesme(t)
        if nq:
            for row in reversed(adaylar):
                k = row.get("soru", "")
                if self._fuzzy_aday_elenmeli_mi(t, k):
                    continue
                if self._norm_eslesme(k) == nq:
                    ans = row.get("cevap", "")
                    if self._cevap_yer_tutucu_mu(ans):
                        continue
                    return {
                        "cevap": ans,
                        "soru": k,
                        "eslesme": "norm",
                        "skor": 1.0,
                    }

        en_iyi = self._fuzzy_en_iyi_eslesme(t, adaylar)
        if en_iyi is not None:
            return {
                "cevap": en_iyi[0],
                "soru": en_iyi[1],
                "eslesme": "fuzzy",
                "skor": float(en_iyi[2]),
            }
        stripped = self._strip_identity_question_suffix(t)
        if stripped and stripped != t:
            nq2 = self._norm_eslesme(stripped)
            if nq2:
                for row in reversed(adaylar):
                    k = row.get("soru", "")
                    if self._fuzzy_aday_elenmeli_mi(t, k):
                        continue
                    if self._norm_eslesme(k) == nq2:
                        ans = row.get("cevap", "")
                        if self._cevap_yer_tutucu_mu(ans):
                            continue
                        return {
                            "cevap": ans,
                            "soru": k,
                            "eslesme": "norm",
                            "skor": 1.0,
                        }
            en_iyi = self._fuzzy_en_iyi_eslesme(stripped, adaylar)
            if en_iyi is not None:
                return {
                    "cevap": en_iyi[0],
                    "soru": en_iyi[1],
                    "eslesme": "fuzzy",
                    "skor": float(en_iyi[2]),
                }
        return None

    @classmethod
    def _fuzzy_kimdir_sorgu_adayda_tamam_mi(cls, sorgu: str, aday_soru: str) -> bool:
        """Kimdir sorusunda fuzzy: sorgudaki her anlamlı kelime adayda (typo toleranslı) bulunmalı.

        Örn. «emine haymana kimdir» yalnızca soyadı «haymana» ile «gökçe nur haymana» kaydına
        düşmesin — «emine» adayda yoksa eşleşme reddedilir.
        """
        sq = cls._norm_eslesme(sorgu)
        if not re.search(r"\b(kimdir|kimdi|kim)\b", sq):
            return True
        sorgu_tok = cls._token_kumesi(sorgu)
        if not sorgu_tok:
            return True
        aday_tok = cls._token_kumesi(aday_soru)
        if not aday_tok:
            return False
        for s in sorgu_tok:
            if s in aday_tok:
                continue
            if any(
                cls._benzerlik(s, a) >= cls.TOKEN_KELIME_BENZERLIK_ESIK for a in aday_tok
            ):
                continue
            return False
        return True

    @classmethod
    def _fuzzy_aday_elenmeli_mi(cls, sorgu: str, aday_soru: str) -> bool:
        """Oturum özeti / ham öğretim satırı — «kimdir» sorusunda aday olmasın."""
        aq = cls._norm_eslesme(aday_soru)
        if not aq:
            return True
        if aq.startswith("__ruzgar_") or aq.startswith("__"):
            return True
        if aq.startswith("kisisel not") or aq.startswith("oturum ozeti"):
            return True
        if "oturum ozeti" in aq or aq.startswith("dosya oturumu"):
            return True
        sq = cls._norm_eslesme(sorgu)
        if re.search(r"\b(kimdir|kimdi|kim)\b", sq) and len(aq) > len(sq) + 24:
            if "oturum" in aq or "konuşulan başlık" in aday_soru.lower():
                return True
        return False

    def _fuzzy_en_iyi_eslesme(
        self, sorgu: str, adaylar: List[Dict[str, str]]
    ) -> Optional[Tuple[str, str, float]]:
        """En yüksek benzerlik skoru veren (cevap, soru, skor) üçlüsünü döner.

        İki eksenli skor:
          - **Karakter benzerliği** (SequenceMatcher): yazım hatalarına dayanıklı.
          - **Token kapsama**: kullanıcının kelimelerinin hafıza sorusunda geçme oranı;
            kısa sorgu ↔ uzun hafıza eşleşmelerini yakalar (örn. `sen kimsin` ↔
            `sen kimsin ne iş yaparsın`).
        Final skor = max(karakter, token_kapsama * TOKEN_KAPSAMA_AGIRLIK).

        Skor `RUZGAR_FUZZY_MIN` (varsayılan 0.70) altındaysa None.
        Aynı skorda birden çok aday varsa daha yeni eklenen tercih edilir
        (kayıtlar listesi sondan başa taranır).
        """
        if not adaylar:
            return None
        anahtar = self._fuzzy_anahtar(sorgu)
        if not anahtar:
            return None
        sorgu_tok = self._token_kumesi(sorgu)
        esik = self._fuzzy_esik()
        en_iyi: Optional[Tuple[str, str, float]] = None
        for row in reversed(adaylar):
            k = row.get("soru", "")
            cv = row.get("cevap", "")
            if not k or not cv:
                continue
            if self._fuzzy_aday_elenmeli_mi(sorgu, k):
                continue
            if self._cevap_yer_tutucu_mu(cv):
                continue
            aday = self._fuzzy_anahtar(k)
            if not aday:
                continue
            char_skor = self._benzerlik(anahtar, aday)
            token_skor = 0.0
            if sorgu_tok:
                aday_tok = self._token_kumesi(k)
                token_skor = self._token_kapsama(sorgu_tok, aday_tok)
            final_skor = max(char_skor, token_skor * self.TOKEN_KAPSAMA_AGIRLIK)
            if final_skor < esik:
                continue
            if not self._fuzzy_kimdir_sorgu_adayda_tamam_mi(sorgu, k):
                continue
            if en_iyi is None or final_skor > en_iyi[2]:
                en_iyi = (cv, k, final_skor)
        return en_iyi

    def tum_bilgiler(self, motor_tipi: str = VARSAYILAN_MOTOR_TIPI) -> Dict[str, str]:
        """Belirtilen motor rafındaki öğrenme sözlüğünün güvenli kopyası."""
        self._reload_if_disk_changed()
        mt = (motor_tipi or self.VARSAYILAN_MOTOR_TIPI).strip() or self.VARSAYILAN_MOTOR_TIPI
        out: Dict[str, str] = {}
        for row in self._kayitlar:
            if row.get("motor_tipi") != mt:
                continue
            s = row.get("soru", "").strip()
            c = row.get("cevap", "").strip()
            if s and c:
                out[s] = c
        return out

    def ekle_bilgi(self, soru: str, cevap: str, motor_tipi: str = VARSAYILAN_MOTOR_TIPI) -> str:
        """Doğrudan soru/cevap ekleyip kalıcı kaydeder."""
        self._ensure_store_ready()
        return self._yeni_bilgi_isle(f"{soru} = {cevap}", motor_tipi=motor_tipi)

    def sil_bilgi(self, soru: str, motor_tipi: str = VARSAYILAN_MOTOR_TIPI) -> bool:
        """Soru anahtarını ve cevabı kalıcı olarak siler; yoksa False."""
        self._ensure_store_ready()
        anahtar = soru.strip()
        mt = (motor_tipi or self.VARSAYILAN_MOTOR_TIPI).strip() or self.VARSAYILAN_MOTOR_TIPI
        if not anahtar:
            return False
        once = len(self._kayitlar)
        self._kayitlar = [
            r
            for r in self._kayitlar
            if not (r.get("motor_tipi") == mt and r.get("soru") == anahtar)
        ]
        if len(self._kayitlar) == once:
            return False
        self._sync_hafiza_view()
        self._dosyaya_kaydet()
        return True

    def tumunu_degistir(self, yeni: Dict[str, str], motor_tipi: str = VARSAYILAN_MOTOR_TIPI) -> None:
        """Sözlüğü baştan yazar (analiz paneli tam kayıt). Boş sözlük tüm kayıtları siler."""
        self._ensure_store_ready()
        mt = (motor_tipi or self.VARSAYILAN_MOTOR_TIPI).strip() or self.VARSAYILAN_MOTOR_TIPI
        diger = [r for r in self._kayitlar if r.get("motor_tipi") != mt]
        temiz: Dict[str, str] = {}
        for k, v in (yeni or {}).items():
            kk = str(k).strip()
            if not kk:
                continue
            temiz[kk] = str(v).strip()
        self._kayitlar = diger + [
            {
                "motor_tipi": mt,
                "soru": k,
                "cevap": v,
                "ts": self._now_iso(),
            }
            for k, v in temiz.items()
            if k and v
        ]
        self._sync_hafiza_view()
        self._dosyaya_kaydet()

    def _coz_yeni_bilgi_parca(self, parca: str) -> Optional[Dict[str, str]]:
        """Tek bir 'soru = cevap' satırını soru/cevap olarak çözer."""
        parca = parca.strip()
        if not parca or "=" not in parca:
            return None
        parts = parca.split("=", 1)
        if len(parts) < 2:
            return None
        soru_k, cevap_k = parts[0], parts[1]
        s, c = soru_k.strip(), cevap_k.strip()
        if s and c:
            return {"soru": s, "cevap": c}
        return None

    def import_metin_blok(self, metin: str, motor_tipi: str = VARSAYILAN_MOTOR_TIPI) -> List[Dict[str, str]]:
        """
        Metni satır satır işler; yalnızca `soru = cevap` satırlarını içe aktarır.
        """
        self._ensure_store_ready()
        sonuc: List[Dict[str, str]] = []
        mt = (motor_tipi or self.VARSAYILAN_MOTOR_TIPI).strip() or self.VARSAYILAN_MOTOR_TIPI
        t = (metin or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not t:
            return sonuc

        for satir in t.split("\n"):
            satir = satir.strip()
            if not satir or satir.startswith("#"):
                continue
            row = self._coz_yeni_bilgi_parca(satir)
            if row:
                self._upsert_kayit(mt, row["soru"], row["cevap"])
                sonuc.append({"motor_tipi": mt, **row})
        if sonuc:
            self._sync_hafiza_view()
            self._dosyaya_kaydet()
        return sonuc

    def dosya_yolu(self) -> str:
        return str(self._dosya_yolu)

    def yeniden_yukle(self) -> int:
        """Diskten taze okuma — Rüzgar'ı kapat-aç etmeden RAM'i tazeler.

        JSON dosyası dışarıdan (editör veya başka bir araçla) değiştirildiğinde
        çağrılır. Geri dönüş: yüklenen kayıt sayısı (Mimar onay tanılaması için).
        """
        self._ogrenme_disk_mtime_ns = None
        self._yukle_veya_olustur()
        return len(self._hafiza)

    def dosya_yazilabilir_mi(self) -> bool:
        try:
            self._ensure_store_ready()
            return self._dosya_yolu.exists() and self._dosya_yolu.is_file()
        except Exception:
            return False

    # ----------------- İç detaylar -----------------
    def _yukle_veya_olustur(self) -> None:
        """
        Açılışta bir kez çalışır:
        - Dosya yoksa, içi boş bir JSON sözlüğü oluşturur.
        - Dosya varsa RAM'e yükler.
        """
        self._ensure_store_ready()

        try:
            icerik = self._dosya_yolu.read_text(encoding="utf-8")
            parsed = json.loads(icerik) if icerik.strip() else {}
            self._kayitlar = self._normalize_loaded_store(parsed)
            self._sync_hafiza_view()
        except Exception:
            # Herhangi bir bozulma durumunda güvenli tarafta kal:
            self._kayitlar = []
            self._hafiza = {}
        self._sync_disk_mtime_after_load()

    def _yeni_bilgi_isle(self, komut: str, motor_tipi: str = VARSAYILAN_MOTOR_TIPI) -> str:
        """
        '[Soru] = [Cevap]' formatındaki metni işler,
        hem dosyaya hem RAM'e ekler.
        """
        kalan = komut.strip()

        if "=" not in kalan:
            return "Mimar, yeni bilgiyi 'Soru = Cevap' formatında söylemelisin."

        soru_kisim, cevap_kisim = kalan.split("=", 1)
        soru = soru_kisim.strip()
        cevap = cevap_kisim.strip()

        if not soru or not cevap:
            return "Mimar, soru ve cevabı boş bırakma lütfen."
        mt = (motor_tipi or self.VARSAYILAN_MOTOR_TIPI).strip() or self.VARSAYILAN_MOTOR_TIPI
        self._upsert_kayit(mt, soru, cevap)
        self._sync_hafiza_view()

        # Diske kalıcı olarak yaz
        self._dosyaya_kaydet()

        return f"Mimar, '{soru}' bilgisini hafızama kazıdım."

    def _upsert_kayit(self, motor_tipi: str, soru: str, cevap: str) -> None:
        mt = (motor_tipi or self.VARSAYILAN_MOTOR_TIPI).strip() or self.VARSAYILAN_MOTOR_TIPI
        s = (soru or "").strip()
        c = (cevap or "").strip()
        if not s or not c:
            return
        yeni = []
        for row in self._kayitlar:
            if row.get("motor_tipi") == mt and row.get("soru") == s:
                continue
            yeni.append(row)
        yeni.append({"motor_tipi": mt, "soru": s, "cevap": c, "ts": self._now_iso()})
        self._kayitlar = yeni

    def _dosyaya_kaydet(self) -> None:
        """
        Mevcut RAM içeriğini JSON dosyasına yazar.
        """
        self._ensure_store_ready()
        self._dosya_yolu.write_text(
            json.dumps(self._kayitlar, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._sync_disk_mtime_after_load()

    def _ensure_store_ready(self) -> None:
        """
        Dosya yoksa oluşturur, proje köküne sabitler ve yazılabilirliği garanti etmeye çalışır.
        """
        try:
            self._dosya_yolu.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        if not self._dosya_yolu.exists():
            for eski in self._eski_dosya_yollari:
                if not eski.exists():
                    continue
                try:
                    self._dosya_yolu.write_text(
                        eski.read_text(encoding="utf-8", errors="ignore"),
                        encoding="utf-8",
                    )
                    break
                except Exception:
                    pass

        if not self._dosya_yolu.exists():
            # Otomatik dosya oluşturma (boş JSON)
            self._dosya_yolu.write_text("[]", encoding="utf-8")

        # Yazma yetkisi kontrolü / düzeltmesi
        try:
            os.chmod(self._dosya_yolu, 0o666)
        except Exception:
            # Windows/izin kısıtlarında chmod başarısız olabilir; kritik değil.
            pass


_hafiza_singleton: Optional[HafizaIRuzgar] = None
_hafiza_by_user: dict[str, HafizaIRuzgar] = {}


def get_hafiza_motor() -> HafizaIRuzgar:
    """Öğrenme dosyası için süreç içi örnek — halk modunda kullanıcı başına ayrı dosya."""
    global _hafiza_singleton
    try:
        from ilim_assistant.ruzgar_public_mode import current_user_id, is_public_mode

        if is_public_mode():
            uid = current_user_id()
            motor = _hafiza_by_user.get(uid)
            if motor is None:
                motor = HafizaIRuzgar()
                _hafiza_by_user[uid] = motor
            return motor
    except Exception:
        pass
    if _hafiza_singleton is None:
        _hafiza_singleton = HafizaIRuzgar()
    return _hafiza_singleton


def genel_hafiza_lookup(message: str, motor_tipi: str | None = None) -> Optional[str]:
    """Merkezi genel hafızadan yanıt bakar; `motor_tipi=None` ise tüm etiketler dahil."""
    return get_hafiza_motor().ogrenme_cevabi_bak(message, motor_tipi=motor_tipi)


def genel_hafiza_lookup_detayli(
    message: str, motor_tipi: str | None = None
) -> Optional[dict]:
    """Genel hafıza eşleşmesi + skor + eşleşme türü."""
    detay = get_hafiza_motor().ogrenme_cevabi_bak_detayli(message, motor_tipi=motor_tipi)
    if not detay:
        return None
    try:
        from ilim_assistant.ruzgar_tek_beyin_hafiza_seed import sanitize_gokcenur_hafiza_cevap

        cevap = sanitize_gokcenur_hafiza_cevap(
            str(detay.get("cevap") or ""),
            soru=str(detay.get("soru") or ""),
        )
        if cevap:
            detay = {**detay, "cevap": cevap}
    except Exception:
        pass
    return detay


def etkileşimli_mod() -> None:
    """
    Hızlı test için basit bir komut satırı arayüzü.
    Bu fonksiyonu üretim kodunda kullanmak zorunda değilsin.
    """
    motor = HafizaIRuzgar()
    print("Hafıza-i Rüzgar hazır. Çıkmak için Ctrl+C.")
    while True:
        try:
            soru = input("Sen: ").strip()
        except KeyboardInterrupt:
            print("\nGörüşürüz Mimar.")
            break

        yanit = motor.cevap_ver(soru)
        print(f"Rüzgar: {yanit}")


if __name__ == "__main__":
    etkileşimli_mod()

