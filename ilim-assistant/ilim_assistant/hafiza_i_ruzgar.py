import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


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

    def __init__(self) -> None:
        # JSON dosyası proje ana dizininde tutulur.
        proje_koku = Path(__file__).resolve().parents[1]
        self._dosya_yolu = Path(
            os.path.join(str(proje_koku), self.GENEL_HAFIZA_DOSYASI_ADI)
        )
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
        """Öğretmez; sözlükte arar. `motor_tipi=None` ise tüm raflarda arar."""
        self._reload_if_disk_changed()
        t = (metin or "").strip()
        if not t:
            return None
        if "=" in t:
            return None
        mt = (motor_tipi or "").strip() or None
        adaylar = self._kayitlar
        if mt is not None:
            adaylar = [r for r in self._kayitlar if r.get("motor_tipi") == mt]
        for row in reversed(adaylar):
            if row.get("soru", "") == t:
                return row.get("cevap", "")
        nq = self._norm_eslesme(t)
        if not nq:
            return None
        for row in reversed(adaylar):
            k = row.get("soru", "")
            if self._norm_eslesme(k) == nq:
                return row.get("cevap", "")
        return None

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
        soru_k, _, cevap_k = parca.split("=", 1)
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


def get_hafiza_motor() -> HafizaIRuzgar:
    """Öğrenme dosyası için süreç içi tek örnek — masaüstü API ve ana sohbet aynı RAM/disk görür."""
    global _hafiza_singleton
    if _hafiza_singleton is None:
        _hafiza_singleton = HafizaIRuzgar()
    return _hafiza_singleton


def genel_hafiza_lookup(message: str, motor_tipi: str | None = None) -> Optional[str]:
    """Merkezi genel hafızadan yanıt bakar; `motor_tipi=None` ise tüm etiketler dahil."""
    return get_hafiza_motor().ogrenme_cevabi_bak(message, motor_tipi=motor_tipi)


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

