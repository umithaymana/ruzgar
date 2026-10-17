const assert = require("assert");
const { cizimSoz } = require("./ruzgar-masa-goz.js");

function kagit(w, h) {
  const data = new Uint8ClampedArray(w * h * 4);
  for (let i = 0; i < w * h; i++) {
    data[i * 4] = 244;
    data[i * 4 + 1] = 240;
    data[i * 4 + 2] = 230;
    data[i * 4 + 3] = 255;
  }
  return data;
}

function boya(data, w, x0, y0, x1, y1, renk) {
  for (let y = y0; y < y1; y++) {
    for (let x = x0; x < x1; x++) {
      const i = (y * w + x) * 4;
      data[i] = renk[0];
      data[i + 1] = renk[1];
      data[i + 2] = renk[2];
    }
  }
}

const bos = kagit(40, 30);
assert.strictEqual(cizimSoz(bos, 40, 30), "Çizim boş.");

const mavi = kagit(40, 30);
boya(mavi, 40, 0, 0, 40, 8, [30, 77, 140]);
const soz = cizimSoz(mavi, 40, 30);
assert.ok(soz.indexOf("Üstte mavi iz var.") >= 0, soz);
assert.ok(soz.indexOf("Altta") < 0, soz);

console.log("masa goz ok");
