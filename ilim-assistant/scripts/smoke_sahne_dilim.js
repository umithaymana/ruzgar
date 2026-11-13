#!/usr/bin/env node
/**
 * Sahne dilim smoke — dosya sözleşmesi + stream mantığı (DOM yok).
 * Çıkış 0 = yeşil.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const jsPath = path.join(root, "ruzgar-desktop", "ruzgar-masa.js");
const cssPath = path.join(root, "ruzgar-desktop", "ruzgar-masa.css");

function fail(msg) {
  console.error("FAIL:", msg);
  process.exit(1);
}

function ok(msg) {
  console.log("OK:", msg);
}

const js = fs.readFileSync(jsPath, "utf8");
const css = fs.readFileSync(cssPath, "utf8");

const needJs = [
  "ensureSahneExtras",
  "ruzgar-sahne-durum",
  "ruzgar-sahne-dalga",
  "is-speaking-text",
  "sameStream",
  "schedulePaintSpeech",
  "ruzgar-sahne-yazi",
  "scrollTop",
  "preventScroll",
  "isSahneDusunuyor",
  "ruzgar-sahne-dusun",
  "is-thinking-sahne",
  "bubble.user",
  "aria-live",
  "data-sahne-mode",
  "visibilitychange",
  "640",
  "Durum: ",
  'role", "status"',
  "mobil sahne→sohbet",
  "Rüzgar sahne",
  "aria-busy",
  'data-sahne-mode", "hazir"',
  "Rüzgar sahne · ",
  "aria-atomic",
  "onSahneResume",
  "pageshow",
  'lang", "tr"',
  '"online"',
  "sahneLastSoz = SAHNE_PLACEHOLDER",
  "SAHNE_PLACEHOLDER",
  "Durum: hazir",
  "sahneYaziTimer",
  ".inert",
  "ruzgar-sahne-mini",
  "ruzgar-sahne-soft",
  "data-sahne-layout",
  '"full"',
  '"mini"',
  "applySahneOrgan",
];
for (const k of needJs) {
  if (!js.includes(k)) fail("masa.js eksik: " + k);
}
ok("masa.js işaretler");

const needCss = [
  ".ruzgar-sahne-durum",
  ".ruzgar-sahne-dalga",
  "ruzgar-sahne-live",
  "ruzgar-sahne-dinle",
  "ruzgar-sahne-yazi",
  "@keyframes ruzgar-dalga",
  "is-speaking-text",
  "#ruzgar-sahne-masa:hover",
  "body.ruzgar-sahne-on:not(.ruzgar-sahne-live)",
  "ruzgar-sahne-dusun",
  "ruzgar-nefes-dusun",
  "is-dusun",
  "ruzgar-sahne-dinle .ruzgar-sahne-face .ruzgar-face-ring",
  "prefers-reduced-motion",
  "safe-area-inset",
  "--sahne-gold",
  "user-select: none",
  "touch-callout",
  "user-select: text",
  "scrollbar-width: thin",
  "overscroll-behavior: contain",
  "touch-action: manipulation",
  "ruzgar-sahne-yazi .ruzgar-sahne-face .ruzgar-face-ring",
  "color-scheme: dark",
  "ruzgar-sahne-dusun) .ruzgar-sahne-wind",
  "--sahne-fade",
  "--sahne-fade-slow",
  "ruzgar-sahne-mini #ruzgar-sahne",
  "ruzgar-sahne-soft",
];
for (const k of needCss) {
  if (!css.includes(k)) fail("masa.css eksik: " + k);
}
ok("masa.css işaretler");

/* Stream mantığı birimi: prefix büyümesi fresh sayılmaz */
function classify(prev, shown) {
  const sameStream =
    !!shown &&
    !!prev &&
    prev !== "Yaz. Cevabı ben buradan söyleyeyim." &&
    shown.length >= prev.length &&
    shown.indexOf(prev.replace(/…$/, "")) === 0;
  const fresh = shown !== prev && !sameStream;
  return { fresh, sameStream };
}

const t1 = classify("Merhaba", "Merhaba dünya");
if (!t1.sameStream || t1.fresh) fail("stream büyümesi sameStream olmalı");
const t2 = classify("Merhaba", "Selam");
if (t2.sameStream || !t2.fresh) fail("yeni metin fresh olmalı");
const t3 = classify("", "İlk");
if (t3.sameStream) fail("boş prev stream değil");
ok("stream sınıflandırma");

/* Locked yüzey dosyalarına sahne dilimi yazılmadı — masa only sözleşmesi */
const locked = ["ruzgar-sade.css", "ruzgar-split.js", "ruzgar-ui-prebody.js"];
for (const f of locked) {
  const p = path.join(root, "ruzgar-desktop", f);
  if (!fs.existsSync(p)) continue;
  const body = fs.readFileSync(p, "utf8");
  if (body.includes("ruzgar-sahne-dalga") || body.includes("ensureSahneExtras")) {
    fail("kilitli dosyaya sızmış: " + f);
  }
}
ok("yüz kilidi sızıntı yok");

console.log("SMOKE_SAHNE_DILIM=PASS");
process.exit(0);
