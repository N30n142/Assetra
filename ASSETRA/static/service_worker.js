// Minimal service worker -- just enough to make Assetra installable as an
// app on phones and laptops. It caches the visual shell (CSS/JS/icons) so
// the app opens instantly, while pages themselves always load fresh from
// the network (this is a live asset tracker, not something that should
// show stale data offline).

const SHELL_CACHE = "assetra-shell-v1";
const SHELL_FILES = [
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/img/favicon.svg",
  "/static/img/icon-192.png",
  "/static/img/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_FILES))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== SHELL_CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Only intervene for our own shell files -- everything else (pages, API
  // calls) goes straight to the network so data is always current.
  if (SHELL_FILES.includes(url.pathname)) {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
  }
});