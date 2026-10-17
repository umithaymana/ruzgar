/* Tuval gözü. Pikseli okur, dört renkten ve üç yerden söyler. Şekil uydurmaz. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ruzgarMasaGoz = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const KAGIT = [244, 240, 230];
  const RENK = [
    ["siyah", [26, 26, 28], "siyah"],
    ["mavi", [30, 77, 140], "mavi"],
    ["kirmizi", [140, 47, 47], "kırmızı"],
    ["yesil", [31, 107, 69], "yeşil"],
  ];

  function yakin(r, g, b, hedef) {
    const dr = r - hedef[0];
    const dg = g - hedef[1];
    const db = b - hedef[2];
    return dr * dr + dg * dg + db * db;
  }

  function cizimSoz(data, width, height) {
    const w = Number(width) || 0;
    const h = Number(height) || 0;
    if (!data || w < 2 || h < 2) return "Çizim boş.";
    const adim = 4;
    const bant = { ust: {}, orta: {}, alt: {} };
    let iz = 0;
    for (let y = 0; y < h; y += adim) {
      const yer = y < h / 3 ? "ust" : y < (2 * h) / 3 ? "orta" : "alt";
      for (let x = 0; x < w; x += adim) {
        const i = (y * w + x) * 4;
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        if (yakin(r, g, b, KAGIT) < 900) continue;
        let sec = RENK[0];
        let uzak = yakin(r, g, b, sec[1]);
        for (let n = 1; n < RENK.length; n++) {
          const olcu = yakin(r, g, b, RENK[n][1]);
          if (olcu < uzak) {
            uzak = olcu;
            sec = RENK[n];
          }
        }
        bant[yer][sec[2]] = (bant[yer][sec[2]] || 0) + 1;
        iz += 1;
      }
    }
    if (iz < 6) return "Çizim boş.";
    const yerAd = { ust: "Üstte", orta: "Ortada", alt: "Altta" };
    const satir = [];
    ["ust", "orta", "alt"].forEach(function (yer) {
      let ad = "";
      let sayi = 0;
      Object.keys(bant[yer]).forEach(function (anahtar) {
        if (bant[yer][anahtar] > sayi) {
          sayi = bant[yer][anahtar];
          ad = anahtar;
        }
      });
      if (sayi >= 3) satir.push(yerAd[yer] + " " + ad + " iz var.");
    });
    return satir.join(" ") || "Çizimde iz var.";
  }

  return { cizimSoz: cizimSoz };
});
