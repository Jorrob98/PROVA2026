const CACHE='jorrob-toolkit-v0.2.0';
const ASSETS=['./','./index.html','./assets/app.css','./assets/app.js','./manifest.webmanifest','./modules.json','./assets/icon.svg'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)));self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',event=>{if(event.request.method!=='GET')return;const req=event.request;event.respondWith(fetch(req).then(res=>{if(res&&res.ok&&new URL(req.url).origin===self.location.origin){const copy=res.clone();caches.open(CACHE).then(c=>c.put(req,copy));}return res;}).catch(()=>caches.match(req).then(r=>r||((req.mode==='navigate')?caches.match('./index.html'):Promise.resolve(undefined)))));});
