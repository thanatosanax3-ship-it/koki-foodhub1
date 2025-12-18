// Service Worker for Koki's Foodhub
// Bumped CACHE_NAME to force clients to update cached pages after deploy
const CACHE_NAME = "foodhub-cache-v3";
const urlsToCache = [
  "/",
  "/login/",
  "/static/styles.css",
  "/static/manifest.json"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
