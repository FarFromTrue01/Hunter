const C="hunter-cache-1";
const CORE=["./","index.html","manifest.webmanifest","icon-192.png","icon-512.png","icon-maskable.png"];
self.addEventListener("install",e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(CORE)).catch(()=>{}))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const r=e.request;if(r.method!=="GET") return;
  const u=new URL(r.url);
  if(u.origin===location.origin&&(r.mode==="navigate"||u.pathname.endsWith("/")||u.pathname.endsWith(".html"))){
    e.respondWith(fetch(r,{cache:"no-store"}).then(res=>{if(res.ok){const cp=res.clone();caches.open(C).then(c=>c.put("index.html",cp))}return res}).catch(()=>caches.match("index.html").then(m=>m||caches.match("./"))));
    return;
  }
  const cacheable=u.origin===location.origin||u.hostname==="fonts.googleapis.com"||u.hostname==="fonts.gstatic.com"||(u.hostname==="www.gstatic.com"&&u.pathname.startsWith("/firebasejs/"));
  if(!cacheable||u.pathname.endsWith(".mp3")) return;
  e.respondWith(caches.match(r).then(m=>m||fetch(r).then(res=>{if(res.ok||res.type==="opaque"){const cp=res.clone();caches.open(C).then(c=>c.put(r,cp))}return res})));
});
