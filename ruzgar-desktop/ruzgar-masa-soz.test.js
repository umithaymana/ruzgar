const assert = require("assert");
const { coz } = require("./ruzgar-masa-soz.js");

assert.deepStrictEqual(coz("belgeye selam mimar yaz"), { eylem: "belge.yaz", metin: "selam mimar" });
assert.deepStrictEqual(coz("belgeye bir satır daha ekle"), { eylem: "belge.ekle", metin: "bir satır daha" });
assert.strictEqual(coz("belgeye yaz: selam"), null);
assert.deepStrictEqual(coz("tabloda A1 e 10 yaz"), { eylem: "tablo.hucre", hucre: "A1", deger: "10" });
assert.strictEqual(coz("tablo A1 = 10"), null);
assert.deepStrictEqual(coz("çizime kutu çiz"), { eylem: "cizim.kutu", x: 80, y: 80, w: 240, h: 140 });
assert.deepStrictEqual(coz("çizime çizgi çiz").eylem, "cizim.cizgi");
assert.deepStrictEqual(coz("çizime daire çiz").eylem, "cizim.daire");
assert.deepStrictEqual(coz("sunuma Hoş geldin slaytı ekle: bugün deneme"), {
  eylem: "sunum.ekle",
  baslik: "Hoş geldin",
  metin: "bugün deneme",
});
assert.strictEqual(coz("menüyü lacivert yap"), null);
assert.strictEqual(coz("çizgi 40 40 400 200"), null);
console.log("masa soz ok");
