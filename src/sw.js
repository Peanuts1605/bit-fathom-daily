/* App shell cache. Network-first, then cache. Cache name bumped for the share-loop shell. */
const C='bf-riddle-share-v3';
const A=['./','./index.html','./manifest.json','./icon.svg'];
self.addEventListener('install',function(e){
  e.waitUntil(caches.open(C).then(function(c){return c.addAll(A)}));
  self.skipWaiting();
});
self.addEventListener('activate',function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){return k!==C}).map(function(k){return caches.delete(k)}));
  }));
  self.clients.claim();
});
self.addEventListener('fetch',function(e){
  if(e.request.method!=='GET') return;
  e.respondWith(
    fetch(e.request).then(function(r){
      var cp=r.clone();
      caches.open(C).then(function(c){c.put(e.request,cp)});
      return r;
    }).catch(function(){
      return caches.match(e.request,{ignoreSearch:true}).then(function(r){return r||caches.match('./index.html')});
    })
  );
});
