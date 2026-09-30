const C="hunter-cache-2",META="hunter-meta";
const CORE=["./","index.html","manifest.webmanifest","logo-192.png","logo-512.png","logo-maskable.png","nf-icon.png","nf-badge.png"];
self.addEventListener("install",e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(CORE)).catch(()=>{}))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C&&k!==META).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
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

/* ---- bildirimler ---- */
async function jget(k){try{const c=await caches.open(META),r=await c.match(k);return r?await r.json():null}catch(e){return null}}
async function jput(k,o){try{const c=await caches.open(META);await c.put(k,new Response(JSON.stringify(o),{headers:{"content-type":"application/json"}}))}catch(e){}}
function opt(it,x){return Object.assign({body:it.b||"",tag:it.tag||it.id||"hunter",icon:"nf-icon.png",badge:"nf-badge.png",data:{go:it.go||"quests"},vibrate:[180,90,180],renotify:false},x||{})}
function stOpt(st){return {body:st.b,tag:"hunter-status",icon:"nf-icon.png",badge:"nf-badge.png",silent:true,renotify:false,data:{go:"quests"},actions:[{action:"quests",title:"Görevler"},{action:"gates",title:"Zindanlar"}]}}
async function markShown(id){const sh=(await jget("/__shown"))||{},now=Date.now();sh[id]=now;for(const k in sh) if(now-sh[k]>5*86400000) delete sh[k];await jput("/__shown",sh)}
async function tell(msg){const cl=await self.clients.matchAll({type:"window",includeUncontrolled:true});cl.forEach(c=>{try{c.postMessage(msg)}catch(e){}})}
self.addEventListener("push",e=>{
  e.waitUntil((async()=>{
    let it={};try{it=e.data?e.data.json():{}}catch(x){it={ti:"Hunter Sistemi",b:e.data?e.data.text():""}}
    const m=(await jget("/__notif"))||{},sh=(await jget("/__shown"))||{},id=it.id||"";
    const dup=id&&(sh[id]||(m.sent&&m.sent[id]));
    let shown=false;
    if(it.st&&m.stOn!==false){await self.registration.showNotification(it.st.ti,stOpt(it.st));shown=true}
    if(!it.so&&!dup){await self.registration.showNotification(it.ti||"Hunter Sistemi",opt(it));shown=true}
    if(!shown) await self.registration.showNotification(it.ti||"Hunter Sistemi",opt(it,{silent:true}));
    if(id){await markShown(id);await tell({nf:"push",id,at:Date.now()})}
  })());
});
self.addEventListener("periodicsync",e=>{
  if(e.tag!=="hunter-remind") return;
  e.waitUntil((async()=>{
    const m=await jget("/__notif");if(!m||!m.on) return;
    const sh=(await jget("/__shown"))||{},now=Date.now();
    const due=(m.plan||[]).filter(it=>!it.srv&&it.at<=now&&now-it.at<3*3600000&&!sh[it.id]&&!(m.sent||{})[it.id]);
    let st=null;
    for(const it of due.slice(-3)){
      if(it.st) st=it.st;
      if(!it.so) await self.registration.showNotification(it.ti,opt(it));
      await markShown(it.id);
    }
    if(st&&m.stOn) await self.registration.showNotification(st.ti,stOpt(st));
  })());
});
self.addEventListener("notificationclick",e=>{
  const n=e.notification,go=e.action||(n.data&&n.data.go)||"";
  if(n.tag!=="hunter-status") n.close();
  e.waitUntil((async()=>{
    const cl=await self.clients.matchAll({type:"window",includeUncontrolled:true});
    for(const c of cl){if("focus" in c){try{await c.focus()}catch(x){}c.postMessage({nf:"go",go});return}}
    await self.clients.openWindow(new URL("./"+(go?"?go="+go:""),self.registration.scope).href);
  })());
});
