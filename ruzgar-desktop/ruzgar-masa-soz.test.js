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

const kabul = "belgeye selam yaz, tabloda A1 e 10 yaz, çizime kutu çiz, sunuma Hoş geldin slaytı ekle: bugün";
const liste = coz(kabul);
assert.deepStrictEqual(liste.liste.map(function (adim) { return adim.eylem; }), [
  "belge.yaz",
  "tablo.hucre",
  "cizim.kutu",
  "sunum.ekle",
]);
assert.strictEqual(liste.liste[0].metin, "selam");
assert.strictEqual(liste.liste[1].hucre, "A1");
assert.strictEqual(liste.liste[1].deger, "10");
assert.strictEqual(liste.liste[3].baslik, "Hoş geldin");
assert.strictEqual(liste.liste[3].metin, "bugün");
assert.deepStrictEqual(coz("belgeye bak ve söyle"), { bak: "belge" });
assert.deepStrictEqual(coz("çizime bak ve söyle"), { bak: "cizim" });
assert.deepStrictEqual(coz("belgede selam yerine merhaba yaz"), {
  eylem: "belge.yerine",
  eski: "selam",
  yeni: "merhaba",
});
assert.deepStrictEqual(coz("A1 hücresini sil"), { eylem: "tablo.sil", hucre: "A1" });
assert.deepStrictEqual(coz("A sütununu topla"), { eylem: "tablo.topla", sutun: "A" });
assert.strictEqual(coz("çizime mavi kutu çiz").renk, "mavi");
assert.deepStrictEqual(coz("slaytın başlığını Hoş geldin yap"), { eylem: "sunum.baslik", baslik: "Hoş geldin" });
assert.deepStrictEqual(coz("belgeye bak ve söyle, belgeye selam yaz"), { red: true });
assert.deepStrictEqual(coz("masayı baştan tasarla"), { red: true });
assert.deepStrictEqual(coz("belgeye selam yaz, şunu uydur"), { red: true });
console.log("masa soz ok");
