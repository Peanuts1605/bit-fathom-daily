/* App shell only. Old cache names are deleted on activate. Runtime cache stays capped. */
const C='bf-riddle-share-v4';
const MAX=8;
const SHELL=['./','./index.html','./manifest.json','./icon.svg'];
function shellRequest(url){
  var path=url.pathname;
  return path==='/' || /\/index\.html$/.test(path) || /\/manifest\.json$/.test(path) || /\/icon\.svg$/.test(path);
}
function trim(cache){
  return cache.keys().then(function(keys){
    var extra=keys.length-MAX;
    if(extra<=0) return;
    return Promise.all(keys.slice(0, extra).map(function(k){return cache.delete(k)}));
  });
}
self.addEventListener('install',function(e){
  e.waitUntil(caches.open(C).then(function(c){return c.addAll(SHELL)}));
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
  var url=new URL(e.request.url);
  if(url.origin!==self.location.origin || !shellRequest(url)) return;
  e.respondWith(
    fetch(e.request).then(function(r){
      var cp=r.clone();
      caches.open(C).then(function(c){return c.put(e.request, cp).then(function(){return trim(c)})});
      return r;
    }).catch(function(){
      return caches.match(e.request,{ignoreSearch:true}).then(function(hit){return hit||caches.match('./index.html')});
    })
  );
});
