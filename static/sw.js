const CACHE_NAME = 'agybot-mesh-v1';
const ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/app.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((k) => k !== CACHE_NAME && caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Network first, falling back to cache
  if (e.request.url.includes('/api/') || e.request.url.includes('/ws')) {
    return; // Don't cache dynamic API/WebSocket routes
  }
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
