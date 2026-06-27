/* Offline-first service worker. Cache-first for app shell, network-first for
   data (so a fresh snapshot wins when online, last snapshot serves offline). */
const CACHE = "edu-delta-v3";
const SHELL = [
  "./index.html", "./insights.html",
  "./assets/styles.css", "./assets/app.js", "./assets/insights.js",
  "./assets/echarts.min.js", "./assets/world.json", "./assets/icon.svg",
  "./manifest.webmanifest",
  "./data/manifest.json",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) =>
    Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = e.request.url;
  const isData = url.includes("/data/");
  if (isData) {
    e.respondWith(
      fetch(e.request).then((r) => {
        const copy = r.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return r;
      }).catch(() => caches.match(e.request))
    );
  } else {
    e.respondWith(caches.match(e.request).then((c) => c || fetch(e.request)));
  }
});
