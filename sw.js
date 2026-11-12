// Service worker for the hosted web version: caches the whole game so it opens offline.
// Bump CACHE_VERSION whenever any of these files change, so players get the update.
const CACHE_VERSION = 'solitaire-pro-v5';

const PRECACHE = [
  './',
  'index.html',
  'styles.css',
  'manifest.json',
  'solitaire.ico',
  'icons/icon-180.png',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'src/audio/sound.js',
  'src/engine/card.js',
  'src/engine/deck.js',
  'src/engine/hints.js',
  'src/engine/leaderboard.js',
  'src/engine/solitaire.js',
  'src/engine/solver.js',
  'src/engine/stats.js',
  'src/ui/app.js',
  'src/ui/cards-svg.js',
  'src/ui/drag-controller.js',
  'src/ui/haptics.js',
  'src/ui/i18n.js',
  'src/ui/renderer.js',
  'src/ui/victory-canvas.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_VERSION).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

// Cache first, then the network (and keep a copy of anything new from this site)
self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin) return;

  event.respondWith(
    caches.match(request, { ignoreSearch: true }).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(request, copy));
        }
        return response;
      });
    })
  );
});
