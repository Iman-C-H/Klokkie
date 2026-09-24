/* Klokkie service worker
   Bei jeder Änderung an index.html o. Ä. VERSION hochzählen,
   damit alle Geräte die neue Version laden. */
const VERSION = 'klokkie-v2';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon-64.png'
];
const FONT_CACHE = 'klokkie-fonts';
const META_CACHE = 'klokkie-meta';   // audio/index.json
// Audiodateien liegen in 'klokkie-audio-<version>' und werden von der Seite selbst verwaltet.

self.addEventListener('install', event => {
  event.waitUntil(caches.open(VERSION).then(c => c.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== VERSION && k !== FONT_CACHE && k !== META_CACHE && !k.startsWith('klokkie-audio-')).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Google Fonts: cache-first (Schrift bleibt auch offline erhalten)
  if (url.origin === 'https://fonts.googleapis.com' || url.origin === 'https://fonts.gstatic.com') {
    event.respondWith(
      caches.open(FONT_CACHE).then(async cache => {
        const hit = await cache.match(req);
        if (hit) return hit;
        const res = await fetch(req);
        if (res.ok || res.type === 'opaque') cache.put(req, res.clone());
        return res;
      })
    );
    return;
  }

  if (url.origin !== self.location.origin) return;

  // Liste der Audiodateien: network-first, damit neue Aufnahmen erkannt werden; offline aus dem Cache
  if (url.pathname.endsWith('/audio/index.json')) {
    event.respondWith(
      fetch(req).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(META_CACHE).then(c => c.put(req, copy)); }
        return res;
      }).catch(() => caches.match(req))
    );
    return;
  }

  // Seite selbst: network-first, damit Updates sofort ankommen; offline aus dem Cache
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).then(res => {
        const copy = res.clone();
        caches.open(VERSION).then(c => c.put('./index.html', copy));
        return res;
      }).catch(() => caches.match('./index.html'))
    );
    return;
  }

  // Alles andere (Icons, Manifest, MP3s): cache-first
  event.respondWith(caches.match(req).then(hit => hit || fetch(req)));
});
