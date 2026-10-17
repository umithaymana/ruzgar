/* Masa düz cümleleri. Bilinen kalıp eylem döner; çözülemeyen iş masa değiştirmez. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ruzgarMasaSoz = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function parca(raw) {
    let m = raw.match(/^belgeye\s+(.+?)\s+yaz$/i);
    if (m && m[1].trim()) return { eylem: "belge.yaz", metin: m[1].trim() };
    m = raw.match(/^belgeye\s+(.+?)\s+ekle$/i);
    if (m && m[1].trim()) return { eylem: "belge.ekle", metin: m[1].trim() };
    m = raw.match(/^(?:tabloda|tabloya)\s+([A-La-l])(\d{1,2})\s*(?:e|ye|hücresine|hucresine)?\s*(.+?)\s+yaz$/i);
    if (m && m[3].trim()) return { eylem: "tablo.hucre", hucre: (m[1] + m[2]).toUpperCase(), deger: m[3].trim() };
    m = raw.match(/^(?:çizime|cizime)\s+(kutu|çizgi|cizgi|daire)\s+(?:çiz|ciz)$/i);
    if (m) {
      const tur = m[1].toLowerCase();
      if (tur === "kutu") return { eylem: "cizim.kutu", x: 80, y: 80, w: 240, h: 140 };
      if (tur === "daire") return { eylem: "cizim.daire", x: 300, y: 220, rx: 80, ry: 60 };
      return { eylem: "cizim.cizgi", x1: 40, y1: 40, x2: 400, y2: 200 };
    }
    m = raw.match(/^sunuma\s+slayt\s+ekle\s*[:\-]\s*(.+?)\s*\|\s*(.+)$/i);
    if (m && (m[1].trim() || m[2].trim())) return { eylem: "sunum.ekle", baslik: m[1].trim(), metin: m[2].trim() };
    m = raw.match(/^sunuma\s+(.+?)\s+slayt[ıi]\s+ekle\s*[:\-]\s*(.+)$/i);
    if (m && (m[1].trim() || m[2].trim())) return { eylem: "sunum.ekle", baslik: m[1].trim(), metin: m[2].trim() };
    return null;
  }

  function coz(text) {
    const raw = String(text || "").replace(/\s+/g, " ").trim();
    if (!raw || raw.length > 9000) return null;
    const tek = parca(raw);
    if (tek) return tek;
    if (/^masay[ıi]\s+ba[sş]tan\s+tasarla$/i.test(raw)) return { red: true };
    const parcalar = raw.split(/\s*,\s*|\s+sonra\s+/).map(function (p) { return p.trim(); }).filter(Boolean);
    if (parcalar.length < 2) return null;
    const liste = [];
    for (let i = 0; i < parcalar.length; i++) {
      const hit = parca(parcalar[i]);
      if (!hit) return liste.length ? { red: true } : null;
      liste.push(hit);
    }
    return { liste: liste };
  }

  return { coz: coz };
});
