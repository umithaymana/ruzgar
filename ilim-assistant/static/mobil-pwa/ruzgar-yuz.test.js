/* node ruzgar-yuz.test.js — saf yardımcılar (DOM yok) */
"use strict";
const assert = require("assert");
const Y = require("./ruzgar-yuz.js");

let n = 0;
function t(ad, fn) {
  fn();
  n++;
  console.log("ok -", ad);
}

t("selam saatleri", () => {
  assert.strictEqual(Y.selamMetni(5), "Günaydın");
  assert.strictEqual(Y.selamMetni(10), "Günaydın");
  assert.strictEqual(Y.selamMetni(11), "İyi günler");
  assert.strictEqual(Y.selamMetni(16), "İyi günler");
  assert.strictEqual(Y.selamMetni(17), "İyi akşamlar");
  assert.strictEqual(Y.selamMetni(21), "İyi akşamlar");
  assert.strictEqual(Y.selamMetni(22), "İyi geceler");
  assert.strictEqual(Y.selamMetni(3), "İyi geceler");
  assert.strictEqual(Y.selamMetni("x"), "İyi günler");
});

t("dalga yolu: kayar döngü için geniş ve düzgün", () => {
  const d = Y.dalgaYolu(800, 24);
  assert.ok(d.startsWith("M0 12 Q50 0 100 12"));
  assert.ok(d.endsWith("T800 12"));
  assert.strictEqual((d.match(/T/g) || []).length, 7);
  assert.ok(Y.dalgaYolu(0, 0).startsWith("M0 "));
});

t("yüz tercihi: URL > kayıt, varsayılan kapalı", () => {
  assert.strictEqual(Y.yuzTercihi("", null), "0");
  assert.strictEqual(Y.yuzTercihi("", "1"), "1");
  assert.strictEqual(Y.yuzTercihi("?yuz=1", "0"), "1");
  assert.strictEqual(Y.yuzTercihi("?v=1&yuz=0", "1"), "0");
  assert.strictEqual(Y.yuzTercihi("?yuz=2", "1"), "1");
});

t("durum metni", () => {
  assert.strictEqual(Y.durumNormal("bilinmez"), "hazir");
  assert.strictEqual(Y.durumMetni("hazir"), "");
  assert.strictEqual(Y.durumMetni("dinle"), "Dinliyor");
  assert.strictEqual(Y.durumMetni("dusun"), "Düşünüyor");
  assert.ok(Y.durumMetni("konus").startsWith("Konuşuyor"));
});

t("renkler: 6 seçenek, geçerli hex, bilinmeyen → ilk", () => {
  assert.strictEqual(Y.RENKLER.length, 6);
  Y.RENKLER.forEach((r) => assert.ok(Y.renkGecerli(r.hex), r.id));
  assert.strictEqual(Y.renkBul("altin").hex, "#d4af37");
  assert.strictEqual(Y.renkBul("yok").id, "gok");
  assert.strictEqual(Y.renkGecerli("red; x"), false);
});

t("kullanıcı adı güzelleştirme (güvenli)", () => {
  assert.strictEqual(Y.kullaniciAdiGuzel("mimar"), "Mimar");
  assert.strictEqual(Y.kullaniciAdiGuzel("ümit"), "Ümit");
  assert.strictEqual(Y.kullaniciAdiGuzel("<b>x</b>"), "");
  assert.strictEqual(Y.kullaniciAdiGuzel(""), "");
});

console.log("\n" + n + " test geçti");
