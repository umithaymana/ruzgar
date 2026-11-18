/* Rüzgar PWA — HTML/ağ öncelikli; Yenile = güncelleme (skipWaiting + claim) */
const CACHE = "ruzgar-pwa-v20261118-onboard";
const ASSETS = [
  "./app.css?v=20261118-onboard",
  "./app.js?v=20261118-onboard",
  "./manifest.webmanifest?v=5",
  "./icon-192.png?v=5",
  "./icon-512.png?v=5",
  "./apple-touch-icon.png?v=5",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches
      .open(CACHE)
      .then((c) => c.addAll(ASSETS).catch(() => {}))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

/* Yeni SW indirgendiğinde hemen devral — Yenile yeterli olsun */
self.addEventListener("message", (e) => {
  if (e && e.data && e.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.includes("/api/")) return;

  // HTML her zaman ağdan — cihaz listesi güncel kalsın
  const isHtml =
    e.request.mode === "navigate" ||
    (e.request.headers.get("accept") || "").includes("text/html") ||
    url.pathname.endsWith("/") ||
    url.pathname.endsWith("/index.html") ||
    url.pathname.endsWith("/mobil");

  // app.js / app.css — ağ öncelikli (eski SW query ile kilitlenmesin)
  const isAppShell =
    /\/app\.js(?:\?|$)/.test(url.pathname + url.search) ||
    /\/app\.css(?:\?|$)/.test(url.pathname + url.search) ||
    url.pathname.endsWith("/app.js") ||
    url.pathname.endsWith("/app.css");

  if (isHtml || isAppShell) {
    e.respondWith(
      fetch(e.request)
        .then((res) => res)
        .catch(() => caches.match(e.request).then((hit) => hit || caches.match("./index.html"))),
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).catch(() => caches.match("./index.html"))),
  );
});
