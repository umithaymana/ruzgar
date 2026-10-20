/* Masa düz cümleleri. Bilinen kalıp eylem döner; çözülemeyen iş masa değiştirmez. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ruzgarMasaSoz = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function bakMasa(raw) {
    const m = String(raw || "").match(/^(belgeye|tabloya|çizime|cizime|sunuma)\s+bak\s+ve\s+s[öo]yle$/i);
    if (!m) return "";
    const ad = m[1].toLowerCase();
    if (ad === "belgeye") return "belge";
    if (ad === "tabloya") return "tablo";
    if (ad === "sunuma") return "sunum";
    return "cizim";
  }

  function yerCiz(yer, tur, renk) {
    const yerAd = String(yer || "").toLowerCase();
    const sekil = String(tur || "").toLowerCase();
    let eylem = null;
    if (yerAd === "ortaya" && sekil === "kutu") eylem = { eylem: "cizim.kutu", x: 680, y: 430, w: 240, h: 140 };
    else if (yerAd === "ortaya" && sekil === "daire") eylem = { eylem: "cizim.daire", x: 800, y: 500, rx: 80, ry: 60 };
    else if (yerAd === "ortaya") eylem = { eylem: "cizim.cizgi", x1: 200, y1: 500, x2: 1400, y2: 500 };
    else if (yerAd === "üste" || yerAd === "uste") {
      if (sekil === "kutu") eylem = { eylem: "cizim.kutu", x: 80, y: 40, w: 240, h: 140 };
      else if (sekil === "daire") eylem = { eylem: "cizim.daire", x: 300, y: 120, rx: 80, ry: 60 };
      else eylem = { eylem: "cizim.cizgi", x1: 80, y1: 60, x2: 1520, y2: 60 };
    } else if (yerAd === "alta") {
      if (sekil === "kutu") eylem = { eylem: "cizim.kutu", x: 80, y: 780, w: 240, h: 140 };
      else if (sekil === "çizgi" || sekil === "cizgi") eylem = { eylem: "cizim.cizgi", x1: 80, y1: 920, x2: 1520, y2: 920 };
      else eylem = { eylem: "cizim.daire", x: 800, y: 860, rx: 80, ry: 60 };
    }
    if (!eylem) return null;
    if (renk) eylem.renk = renk;
    return eylem;
  }

  function parca(raw) {
    let m = raw.match(/^belgede\s+(.+?)\s+yerine\s+(.+?)\s+yaz$/i);
    if (m && m[1].trim() && m[2].trim()) return { eylem: "belge.yerine", eski: m[1].trim(), yeni: m[2].trim() };
    m = raw.match(/^belgeye\s+(\d{1,2})\s*[x×]\s*(\d{1,2})\s+tablo\s+ekle$/i);
    if (m) return { eylem: "belge.tablo", satir: Number(m[1]), sutun: Number(m[2]) };
    if (/^belgeye\s+tablo\s+ekle$/i.test(raw)) return { eylem: "belge.tablo", satir: 3, sutun: 3 };
    m = raw.match(/^belgeye\s+(.+?)\s+yaz$/i);
    if (m && m[1].trim()) return { eylem: "belge.yaz", metin: m[1].trim() };
    m = raw.match(/^belgeye\s+(.+?)\s+ekle$/i);
    if (m && m[1].trim()) return { eylem: "belge.ekle", metin: m[1].trim() };
    m = raw.match(/^(?:notlara|nota)\s+(.+?)\s+yaz$/i);
    if (m && m[1].trim()) return { eylem: "notlar.yaz", metin: m[1].trim() };
    m = raw.match(/^(?:notlara|nota)\s+(.+?)\s+ekle$/i);
    if (m && m[1].trim()) return { eylem: "notlar.ekle", metin: m[1].trim() };
    m = raw.match(/^(?:goreve|göreve|gorev|görev)\s+(.+?)\s+ekle$/i);
    if (m && m[1].trim()) return { eylem: "notlar.gorev", metin: m[1].trim() };
    m = raw.match(/^(?:tabloda\s+)?([A-La-l])(\d{1,2})\s+h[üu]cresini\s+sil$/i);
    if (m) return { eylem: "tablo.sil", hucre: (m[1] + m[2]).toUpperCase() };
    m = raw.match(/^([A-La-l])\s+s[üu]tununu\s+topla$/i);
    if (m) return { eylem: "tablo.topla", sutun: m[1].toUpperCase() };
    m = raw.match(/^(?:tabloda|tabloya)\s+([A-La-l])(\d{1,2})\s*(?:e|ye|hücresine|hucresine)?\s*(.+?)\s+yaz$/i);
    if (m && m[3].trim()) return { eylem: "tablo.hucre", hucre: (m[1] + m[2]).toUpperCase(), deger: m[3].trim() };
    if (/^(?:belgeyi temizle|belge temizle)$/i.test(raw)) return { eylem: "belge.temizle" };
    if (/^(?:tabloyu temizle|tablo temizle)$/i.test(raw)) return { eylem: "tablo.temizle" };
    if (/^(?:çizimi temizle|cizimi temizle|çizim temizle)$/i.test(raw)) return { eylem: "cizim.temizle" };
    if (/^(?:sunumu temizle|sunum temizle)$/i.test(raw)) return { eylem: "sunum.temizle" };
    m = raw.match(/^slayt[ıi]n\s+metnini\s+(.+?)\s+yap$/i);
    if (m && m[1].trim()) return { eylem: "sunum.metin", metin: m[1].trim() };
    m = raw.match(/^(?:çizime|cizime)\s+(ortaya|üste|uste|alta)\s+(?:(siyah|mavi|kırmızı|kirmizi|yeşil|yesil)\s+)?(kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)$/i);
    if (m) return yerCiz(m[1], m[3], m[2] || "");
    m = raw.match(/^(?:çizime|cizime)\s+(siyah|mavi|kırmızı|kirmizi|yeşil|yesil)\s+(kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)$/i);
    if (m) {
      const renk = m[1];
      const tur = m[2].toLowerCase();
      if (tur === "kutu") return { eylem: "cizim.kutu", x: 80, y: 80, w: 240, h: 140, renk: renk };
      if (tur === "daire") return { eylem: "cizim.daire", x: 300, y: 220, rx: 80, ry: 60, renk: renk };
      return { eylem: "cizim.cizgi", x1: 40, y1: 40, x2: 400, y2: 200, renk: renk };
    }
    m = raw.match(/^(?:çizime|cizime)\s+(kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)$/i);
    if (m) {
      const tur = m[1].toLowerCase();
      if (tur === "kutu") return { eylem: "cizim.kutu", x: 80, y: 80, w: 240, h: 140 };
      if (tur === "daire") return { eylem: "cizim.daire", x: 300, y: 220, rx: 80, ry: 60 };
      return { eylem: "cizim.cizgi", x1: 40, y1: 40, x2: 400, y2: 200 };
    }
    m = raw.match(/^slayt[ıi]n\s+ba[sş]l[ıi][gğ][ıi]n[ıi]\s+(.+?)\s+yap$/i);
    if (m && m[1].trim()) return { eylem: "sunum.baslik", baslik: m[1].trim() };
    m = raw.match(/^sunuma\s+slayt\s+ekle\s*[:\-]\s*(.+?)\s*\|\s*(.+)$/i);
    if (m && (m[1].trim() || m[2].trim())) return { eylem: "sunum.ekle", baslik: m[1].trim(), metin: m[2].trim() };
    m = raw.match(/^sunuma\s+(.+?)\s+slayt[ıi]\s+ekle\s*[:\-]\s*(.+)$/i);
    if (m && (m[1].trim() || m[2].trim())) return { eylem: "sunum.ekle", baslik: m[1].trim(), metin: m[2].trim() };
    if (/^belgede\s+ne\s+yaz[ıi]yor$/i.test(raw)) return { eylem: "belge.oku" };
    m = raw.match(/^tabloda\s+([A-La-l])(\d{1,2})\s+ne$/i);
    if (m) return { eylem: "tablo.oku", hucre: (m[1] + m[2]).toUpperCase() };
    if (/^slayt[ıi]n\s+ba[sş]l[ıi][gğ][ıi]\s+ne$/i.test(raw)) return { eylem: "sunum.oku" };
    if (/^(?:çizimde|cizimde)\s+ne\s+var$/i.test(raw)) return { eylem: "cizim.oku" };
    return null;
  }

  function coz(text) {
    let raw = String(text || "").replace(/\s+/g, " ").trim();
    raw = raw.replace(/[.!?…]+$/, "").trim();
    if (!raw || raw.length > 9000) return null;
    const bak = bakMasa(raw);
    if (bak) return { bak: bak };
    if (/^masay[ıi]\s+ba[sş]tan\s+tasarla$/i.test(raw)) return { red: true };
    const parcalar = raw.split(/\s*,\s*|\s+sonra\s+/).map(function (p) { return p.trim(); }).filter(Boolean);
    if (parcalar.length >= 2) {
      const liste = [];
      for (let i = 0; i < parcalar.length; i++) {
        if (bakMasa(parcalar[i])) return { red: true };
        const hit = parca(parcalar[i]);
        if (!hit) return liste.length ? { red: true } : null;
        liste.push(hit);
      }
      return { liste: liste };
    }
    return parca(raw);
  }

  function karisikAyir(text) {
    let raw = String(text || "").replace(/\s+/g, " ").trim();
    raw = raw.replace(/[.!?…]+$/, "").trim();
    const parcalar = raw.split(/\s*,\s*|\s+sonra\s+/).map(function (p) { return p.trim(); }).filter(Boolean);
    if (parcalar.length < 2) return null;
    const masa = [];
    const dosya = [];
    for (let i = 0; i < parcalar.length; i++) {
      if (/^(?:belgeye|belgede|belgeyi|tabloda|tabloya|tabloyu|çizime|cizime|çizimi|cizimi|sunuma|sunumu|slaytın|slaytin|notlara|nota|goreve|göreve|gorev|görev)\b/i.test(parcalar[i])) masa.push(parcalar[i]);
      else dosya.push(parcalar[i]);
    }
    if (!masa.length || !dosya.length) return null;
    return { masa: masa, dosya: dosya };
  }

  return { coz: coz, karisikAyir: karisikAyir };
});
