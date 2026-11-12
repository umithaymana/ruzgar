/* Rüzgar PWA — HTML/ağ öncelikli (eski cache yüzünden PC seçeneği kaybolmasın) */
const CACHE = "ruzgar-pwa-v18";
const ASSETS = [
  "./app.css?v=16",
  "./app.js?v=18",
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

  if (isHtml) {
    e.respondWith(
      fetch(e.request)
        .then((res) => res)
        .catch(() => caches.match("./index.html")),
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).catch(() => caches.match("./index.html"))),
  );
});
