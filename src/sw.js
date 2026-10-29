/* App shell only. Old cache names are deleted on activate.
   Query strings share one cache entry. Shell files are never trimmed out. */
const C='bf-riddle-share-v5';
const MAX=8;
const SHELL=['./','./index.html','./manifest.json','./icon.svg'];
function shellRequest(url){
  var path=url.pathname;
  return path==='/' || path==='/index.html' || path==='/manifest.json' || path==='/icon.svg';
}
function cacheKey(request){
  var u=new URL(request.url);
  u.search='';
  u.hash='';
  return new Request(u.toString(), {method:'GET'});
}
function isPinned(request){
  var path=new URL(request.url).pathname;
  return path==='/' || path==='/index.html' || path==='/manifest.json' || path==='/icon.svg';
}
function trim(cache){
  return cache.keys().then(function(keys){
    var pinned=[], rest=[];
    keys.forEach(function(k){ (isPinned(k)?pinned:rest).push(k); });
    var room=Math.max(0, MAX-pinned.length);
    var extra=rest.length-room;
    if(extra<=0) return;
    return Promise.all(rest.slice(0, extra).map(function(k){return cache.delete(k)}));
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
      caches.open(C).then(function(c){return c.put(cacheKey(e.request), cp).then(function(){return trim(c)})});
      return r;
    }).catch(function(){
      return caches.match(cacheKey(e.request)).then(function(hit){return hit||caches.match('./index.html')});
    })
  );
});
