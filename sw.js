/* LiftOff service worker — offline shell + safe updates.
   Strategy: network-first for the app page (updates always land when online,
   cached copy serves offline); cache-first for static assets (icons, manifest).
   Cache name is versioned; bump VERSION together with APP_VERSION at release. */
const VERSION = '3.12.0';
const CACHE = 'liftoff-v' + VERSION;
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return; // videos/thumbnails go straight to the network

  if (e.request.mode === 'navigate') {
    // network-first: fresh app when online, cached shell when not
    e.respondWith(
      fetch(e.request)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => { c.put('./', copy.clone()); c.put('./index.html', copy); });
          return res;
        })
        .catch(() => caches.match('./index.html').then(r => r || caches.match('./')))
    );
    return;
  }

  // static assets: cache-first, refresh in the background
  e.respondWith(
    caches.match(e.request).then(hit => {
      const refresh = fetch(e.request)
        .then(res => { if (res.ok) caches.open(CACHE).then(c => c.put(e.request, res.clone())); return res; })
        .catch(() => hit);
      return hit || refresh;
    })
  );
});

/* server-scheduled rest-timer push: iOS wakes us here even when the app is
   suspended or the phone is locked (and mirrors to a paired Apple Watch).
   Same tag as the in-app local notification, so they de-duplicate. */
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) { /* non-JSON payload */ }
  e.waitUntil(self.registration.showNotification(d.title || '⏱ Rest done!', {
    body: d.body || 'Back to it — your next set is ready 💥',
    tag: 'liftoff-rest', icon: 'icon-192.png', badge: 'icon-192.png', vibrate: [120, 60, 120],
  }));
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
    for (const c of cs) if ('focus' in c) return c.focus();
    return clients.openWindow('./');
  }));
});
