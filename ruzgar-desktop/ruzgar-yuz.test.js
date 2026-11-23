/* node ruzgar-yuz.test.js — masaüstü yüzün saf yardımcıları (DOM yok) */
"use strict";
const assert = require("assert");
const Y = require("./ruzgar-yuz.js");

let n = 0;
function t(ad, fn) {
  fn();
  n++;
  console.log("ok -", ad);
}

t("dalga yolu: kayar döngü için geniş ve düzgün", () => {
  const d = Y.dalgaYolu(800, 24);
  assert.ok(d.startsWith("M0 12 Q50 0 100 12"));
  assert.ok(d.endsWith("T800 12"));
  assert.strictEqual((d.match(/T/g) || []).length, 7);
  assert.ok(Y.dalgaYolu(0, 0).startsWith("M0 "));
});

t("yüz tercihi: URL > kayıt, varsayılan AÇIK", () => {
  assert.strictEqual(Y.yuzTercihi("", null), "1");
  assert.strictEqual(Y.yuzTercihi("", "0"), "0");
  assert.strictEqual(Y.yuzTercihi("?yuz=1", "0"), "1");
  assert.strictEqual(Y.yuzTercihi("?v=1&yuz=0", "1"), "0");
  assert.strictEqual(Y.yuzTercihi("?yuz=2", "0"), "0");
});

t("durum önceliği: dinle > konuş > düşün > hazır", () => {
  assert.strictEqual(Y.durumHesapla({}), "hazir");
  assert.strictEqual(Y.durumHesapla(), "hazir");
  assert.strictEqual(Y.durumHesapla({ mesgul: true }), "dusun");
  assert.strictEqual(Y.durumHesapla({ mesgul: true, konusuyor: true }), "konus");
  assert.strictEqual(Y.durumHesapla({ konusuyor: true, dinliyor: true }), "dinle");
  assert.strictEqual(Y.durumHesapla({ duraklatik: true }), "konus");
});

t("durum metni", () => {
  assert.strictEqual(Y.durumNormal("bilinmez"), "hazir");
  assert.strictEqual(Y.durumMetni("hazir"), "");
  assert.strictEqual(Y.durumMetni("dinle"), "Dinliyor");
  assert.strictEqual(Y.durumMetni("dusun"), "Düşünüyor");
  assert.ok(Y.durumMetni("konus").startsWith("Konuşuyor"));
  assert.ok(Y.durumMetni("konus", true).startsWith("Duraklatıldı"));
});

t("renkler: 6 seçenek, geçerli hex, masaüstü varsayılanı altın", () => {
  assert.strictEqual(Y.RENKLER.length, 6);
  Y.RENKLER.forEach((r) => assert.ok(Y.renkGecerli(r.hex), r.id));
  assert.strictEqual(Y.renkBul("altin").hex, "#d4af37");
  assert.strictEqual(Y.renkBul("yok").id, "altin");
  assert.strictEqual(Y.renkGecerli("red; x"), false);
});

console.log("\n" + n + " test geçti");
