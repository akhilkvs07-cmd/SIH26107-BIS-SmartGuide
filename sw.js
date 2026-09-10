/* BIS SmartGuide legacy service-worker shutdown.
   This file intentionally unregisters the old worker without changing the page URL. */
self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil((async () => {
  try {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => caches.delete(k)));
  } catch (e) {}
  try { await self.registration.unregister(); } catch (e) {}
  try { await self.clients.claim(); } catch (e) {}
})()));
self.addEventListener('fetch', event => {
  event.respondWith(fetch(event.request));
});
