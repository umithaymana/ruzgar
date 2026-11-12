#!/usr/bin/env node
/** Çift hat: PC smoke_sahne_dilim + mobil smoke_mobil_sahne. İkisi de PASS şart. */
"use strict";
const { spawnSync } = require("child_process");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const py =
  process.env.RUZGAR_PYTHON ||
  "D:\\ÜMİT\\14-) PROGRAMLAR\\venvs\\ruzgar\\Scripts\\python.exe";

function run(cmd, args, label) {
  console.log("---", label, "---");
  const r = spawnSync(cmd, args, { cwd: root, encoding: "utf8", shell: false });
  if (r.stdout) process.stdout.write(r.stdout);
  if (r.stderr) process.stderr.write(r.stderr);
  if (r.status !== 0) {
    console.error("CIFT_FAIL:", label, "exit", r.status);
    process.exit(r.status || 1);
  }
}

run(process.execPath, ["--check", path.join(root, "ruzgar-desktop", "ruzgar-masa.js")], "pc-syntax");
run(process.execPath, [path.join(__dirname, "smoke_sahne_dilim.js")], "pc-sahne");
run(py, [path.join(__dirname, "smoke_mobil_sahne.py")], "mobil-sahne");

/* Parite sözleşmesi: her iki hatta aynı durum sözlüğü */
const fs = require("fs");
const modes = ["hazir", "yazi", "dinle", "dusun", "konus"];
const mobilJs = fs.readFileSync(path.join(root, "ilim-assistant", "static", "mobil-pwa", "app.js"), "utf8");
const pcJs = fs.readFileSync(path.join(root, "ruzgar-desktop", "ruzgar-masa.js"), "utf8");
for (const m of modes) {
  if (!mobilJs.includes(m === "hazir" ? "Hazır" : m === "yazi" ? "Yazıyorsun" : m === "dinle" ? "Dinliyor" : m === "dusun" ? "Düşünüyor" : "Konuşuyor")) {
    console.error("CIFT_FAIL: mobil durum etiketi eksik", m);
    process.exit(1);
  }
  if (!pcJs.includes(m === "hazir" ? "Hazır" : m === "yazi" ? "Yazıyorsun" : m === "dinle" ? "Dinliyor" : m === "dusun" ? "Düşünüyor" : "Konuşuyor")) {
    console.error("CIFT_FAIL: pc durum etiketi eksik", m);
    process.exit(1);
  }
}
console.log("OK: durum sözlüğü 5/5 çift");

const pcCss = fs.readFileSync(path.join(root, "ruzgar-desktop", "ruzgar-masa.css"), "utf8");
const mobilCss = fs.readFileSync(
  path.join(root, "ilim-assistant", "static", "mobil-pwa", "app.css"),
  "utf8"
);
for (const [label, blob] of [
  ["pc", pcCss + pcJs],
  ["mobil", mobilCss + mobilJs],
]) {
  for (const need of [
    "data-sahne-mode",
    "prefers-reduced-motion",
    "safe-area-inset",
    "--sahne-gold",
  ]) {
    if (!blob.includes(need)) {
      console.error("CIFT_FAIL: parity core eksik", label, need);
      process.exit(1);
    }
  }
}
console.log("OK: PARITY_CORE çift");

function countDalga(htmlOrJs, pattern) {
  const m = htmlOrJs.match(pattern);
  return m ? m.length : 0;
}
const mobilHtml = fs.readFileSync(
  path.join(root, "ilim-assistant", "static", "mobil-pwa", "index.html"),
  "utf8"
);
const mobilDalga = (mobilHtml.match(/id="sahneDalga"[\s\S]*?<\/div>/) || [""])[0];
const mobilSpans = (mobilDalga.match(/<span>/g) || []).length;
if (mobilSpans !== 5) {
  console.error("CIFT_FAIL: mobil dalga span", mobilSpans);
  process.exit(1);
}
if (!pcJs.includes("for (let i = 0; i < 5; i++)")) {
  console.error("CIFT_FAIL: pc dalga 5 bar yok");
  process.exit(1);
}
console.log("OK: dalga 5/5 çift");

const placeholder = "Yaz. Cevabı ben buradan söyleyeyim.";
if (!mobilHtml.includes(placeholder) || !pcJs.includes(placeholder)) {
  console.error("CIFT_FAIL: boş sahne sözü hizasız");
  process.exit(1);
}
console.log("OK: boş söz placeholder çift");

if (!pcJs.includes("aria-busy") || !mobilJs.includes("aria-busy")) {
  console.error("CIFT_FAIL: aria-busy eksik");
  process.exit(1);
}
if (!mobilCss.includes(".sahne-dalga.is-dinle") || !mobilCss.includes(".sahne-dalga.is-dusun")) {
  console.error("CIFT_FAIL: mobil dalga display hiza (is-dinle/is-dusun)");
  process.exit(1);
}
if (!pcCss.includes(".ruzgar-sahne-dalga.is-dinle") || !pcCss.includes(".ruzgar-sahne-dalga.is-dusun")) {
  console.error("CIFT_FAIL: pc dalga display hiza");
  process.exit(1);
}
console.log("OK: aria-busy + dalga display çift");

if (!mobilJs.includes("is-thinking-sahne") || !pcJs.includes("is-thinking-sahne")) {
  console.error("CIFT_FAIL: is-thinking-sahne çift eksik");
  process.exit(1);
}
if (!mobilCss.includes("user-select: text") || !pcCss.includes("user-select: text")) {
  console.error("CIFT_FAIL: soz user-select text çift eksik");
  process.exit(1);
}
console.log("OK: thinking-face + soz select çift");

if (!mobilCss.includes(".sahne-stage.is-yazi .sahne-soz") || !pcCss.includes("ruzgar-sahne-yazi .ruzgar-sahne-soz")) {
  console.error("CIFT_FAIL: yazi soz border çift eksik");
  process.exit(1);
}
if (!pcJs.includes('data-sahne-mode", "hazir"') || !pcJs.includes('aria-busy", "false"')) {
  console.error("CIFT_FAIL: pc sahne-off hazir/aria-busy reset");
  process.exit(1);
}
console.log("OK: yazi border + off-reset çift");

if (!mobilJs.includes("sameStream") || !pcJs.includes("sameStream")) {
  console.error("CIFT_FAIL: sameStream çift eksik");
  process.exit(1);
}
if (!mobilJs.includes('aria-busy", "false"') || !mobilJs.includes('data-sahne-mode", "hazir"')) {
  console.error("CIFT_FAIL: mobil gate-off reset");
  process.exit(1);
}
console.log("OK: sameStream + gate-off reset çift");

if (!mobilJs.includes("Rüzgar sahne · ") || !pcJs.includes("Rüzgar sahne · ")) {
  console.error("CIFT_FAIL: stage title hiza");
  process.exit(1);
}
if (!mobilCss.includes("scrollbar-width: thin") || !pcCss.includes("scrollbar-width: thin")) {
  console.error("CIFT_FAIL: soz scrollbar-width thin");
  process.exit(1);
}
console.log("OK: stage title + scrollbar çift");

if (!mobilJs.includes("aria-atomic") || !pcJs.includes("aria-atomic")) {
  console.error("CIFT_FAIL: aria-atomic çift");
  process.exit(1);
}
if (!mobilCss.includes("overscroll-behavior: contain") || !pcCss.includes("overscroll-behavior: contain")) {
  console.error("CIFT_FAIL: overscroll-behavior contain");
  process.exit(1);
}
console.log("OK: aria-atomic + overscroll çift");

if (!mobilCss.includes("touch-action: manipulation") || !pcCss.includes("touch-action: manipulation")) {
  console.error("CIFT_FAIL: touch-action manipulation");
  process.exit(1);
}
if (!mobilCss.includes(".sahne-stage.is-yazi .sahne-face-ring") || !pcCss.includes("ruzgar-sahne-yazi .ruzgar-sahne-face .ruzgar-face-ring")) {
  console.error("CIFT_FAIL: yazi face-ring");
  process.exit(1);
}
console.log("OK: touch-action + yazi ring çift");

/* sameStream birim — PC smoke_sahne_dilim ile aynı sözleşme (mobil de uygular) */
function classify(prev, shown) {
  const ph = "Yaz. Cevabı ben buradan söyleyeyim.";
  const sameStream =
    !!shown &&
    !!prev &&
    prev !== ph &&
    shown.length >= prev.length &&
    shown.indexOf(prev.replace(/…$/, "")) === 0;
  const fresh = shown !== prev && !sameStream;
  return { fresh, sameStream };
}
const u1 = classify("Merhaba", "Merhaba dünya");
if (!u1.sameStream || u1.fresh) {
  console.error("CIFT_FAIL: stream büyümesi sameStream");
  process.exit(1);
}
const u2 = classify("Merhaba", "Selam");
if (u2.sameStream || !u2.fresh) {
  console.error("CIFT_FAIL: yeni metin fresh");
  process.exit(1);
}
console.log("OK: sameStream birim çift");

const safeNeedles = ["safe-area-inset-top", "safe-area-inset-bottom", "safe-area-inset-left", "safe-area-inset-right"];
for (const [label, blob] of [
  ["pc", pcCss],
  ["mobil", mobilCss],
]) {
  for (const n of safeNeedles) {
    if (!blob.includes(n)) {
      console.error("CIFT_FAIL: safe-area eksik", label, n);
      process.exit(1);
    }
  }
}
console.log("OK: safe-area 4 kenar çift");

if (!mobilCss.includes("color-scheme: dark") || !pcCss.includes("color-scheme: dark")) {
  console.error("CIFT_FAIL: color-scheme dark");
  process.exit(1);
}
if (!pcCss.includes("ruzgar-sahne-dusun) .ruzgar-sahne-wind") || !mobilCss.includes(":not(.is-dusun) .sahne-wind")) {
  console.error("CIFT_FAIL: idle wind dusun hariç");
  process.exit(1);
}
console.log("OK: color-scheme + idle-wind dusun çift");

if (!mobilJs.includes("onSahneResume") || !pcJs.includes("onSahneResume")) {
  console.error("CIFT_FAIL: onSahneResume");
  process.exit(1);
}
if (!mobilJs.includes("pageshow") || !pcJs.includes("pageshow")) {
  console.error("CIFT_FAIL: pageshow bfcache");
  process.exit(1);
}
console.log("OK: pageshow resume çift");

if (!mobilJs.includes('lang", "tr"') || !pcJs.includes('lang", "tr"')) {
  console.error("CIFT_FAIL: lang=tr sahne metin");
  process.exit(1);
}
console.log("OK: lang=tr çift");

if (!mobilJs.includes('addEventListener("online"') || !pcJs.includes('addEventListener("online"')) {
  console.error("CIFT_FAIL: online resume");
  process.exit(1);
}
if (!pcJs.includes("sahneLastSoz = SAHNE_PLACEHOLDER")) {
  console.error("CIFT_FAIL: pc off placeholder reset");
  process.exit(1);
}
console.log("OK: online + off-placeholder çift");

/* mobil gate-off da placeholder + sınıf temizliği (PC syncSahne off ile hiza) */
if (!mobilJs.includes("sozOff.textContent = SAHNE_PLACEHOLDER")) {
  console.error("CIFT_FAIL: mobil gate-off placeholder");
  process.exit(1);
}
if (!mobilJs.includes("faceOff.classList.remove") || !mobilJs.includes("dalgaOff.classList.remove")) {
  console.error("CIFT_FAIL: mobil gate-off face/dalga temiz");
  process.exit(1);
}
console.log("OK: mobil gate-off full reset");

if (!mobilJs.includes("Durum: hazir") || !pcJs.includes("Durum: hazir")) {
  console.error("CIFT_FAIL: off durum title hazir");
  process.exit(1);
}
console.log("OK: off durum title çift");

if (!mobilJs.includes("sahneYaziTimer") || !mobilJs.includes(", 60)")) {
  console.error("CIFT_FAIL: mobil yazi debounce 60");
  process.exit(1);
}
if (!pcJs.includes("setTimeout(paintSpeech, 60)") || !pcJs.includes("sahneYaziTimer")) {
  console.error("CIFT_FAIL: pc 60ms nabız hiza");
  process.exit(1);
}
console.log("OK: 60ms nabız çift");

if (!mobilJs.includes("SAHNE_PLACEHOLDER") || !pcJs.includes("SAHNE_PLACEHOLDER")) {
  console.error("CIFT_FAIL: SAHNE_PLACEHOLDER sabit");
  process.exit(1);
}
console.log("OK: SAHNE_PLACEHOLDER sabit çift");

if (!mobilCss.includes("--sahne-fade") || !pcCss.includes("--sahne-fade")) {
  console.error("CIFT_FAIL: --sahne-fade token");
  process.exit(1);
}
if (!mobilCss.includes("--sahne-fade-slow") || !pcCss.includes("--sahne-fade-slow")) {
  console.error("CIFT_FAIL: --sahne-fade-slow token");
  process.exit(1);
}
console.log("OK: sahne-fade token çift");

if (!mobilCss.includes("--sahne-fade: 0s") || !pcCss.includes("--sahne-fade: 0s")) {
  console.error("CIFT_FAIL: reduced-motion fade 0s");
  process.exit(1);
}
console.log("OK: reduced-motion fade 0 çift");

if (!mobilJs.includes(".inert") || !pcJs.includes(".inert")) {
  console.error("CIFT_FAIL: inert kapalı sahne");
  process.exit(1);
}
console.log("OK: inert kapalı sahne çift");

if (!mobilCss.includes("var(--sahne-fade") || !pcCss.includes("var(--sahne-fade")) {
  console.error("CIFT_FAIL: fade token kullanımı");
  process.exit(1);
}
console.log("OK: fade token kullanım çift");
console.log("SMOKE_SAHNE_CIFT=PASS");
process.exit(0);
