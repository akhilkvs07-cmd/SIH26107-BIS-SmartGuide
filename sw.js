/* BIS SmartGuide legacy service-worker shutdown. */
self.addEventListener('install',event=>event.waitUntil(self.skipWaiting()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  try{
    const keys=await caches.keys();
    await Promise.all(keys.map(k=>caches.delete(k)));
  }catch(e){}
  try{await self.registration.unregister()}catch(e){}
  try{
    const clients=await self.clients.matchAll({type:'window'});
    clients.forEach(c=>c.navigate(c.url+'#sw-disabled').catch(()=>{}));
  }catch(e){}
  await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
  event.respondWith(fetch(event.request));
});
