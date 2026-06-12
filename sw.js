// Service Worker Silka — consultation hors-ligne
var CACHE = 'silka-v4';
var CORE = ['/', '/index.html', '/manifest.json', '/icon-192.png', '/icon-512.png'];

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE).then(function(c) { return c.addAll(CORE); }).then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.filter(function(k){ return k !== CACHE; }).map(function(k){ return caches.delete(k); }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(e) {
  var url = new URL(e.request.url);
  // HTML : network-first (toujours la dernière version si en ligne, cache sinon)
  if (e.request.mode === 'navigate' || url.pathname === '/' || url.pathname.endsWith('.html')) {
    e.respondWith(
      fetch(e.request).then(function(resp) {
        var copy = resp.clone();
        caches.open(CACHE).then(function(c) { c.put(e.request, copy); });
        return resp;
      }).catch(function() {
        return caches.match(e.request).then(function(r){ return r || caches.match('/'); });
      })
    );
    return;
  }
  // Reste (fonts, CDN, images) : cache-first
  e.respondWith(
    caches.match(e.request).then(function(cached) {
      return cached || fetch(e.request).then(function(resp) {
        if (resp.ok && (url.origin === location.origin || url.hostname.indexOf('gstatic') >= 0 || url.hostname.indexOf('googleapis') >= 0 || url.hostname.indexOf('cdnjs') >= 0)) {
          var copy = resp.clone();
          caches.open(CACHE).then(function(c) { c.put(e.request, copy); });
        }
        return resp;
      });
    })
  );
});
