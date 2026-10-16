import base64,json,sys
def gen(name,files,out):
  F={k:[base64.b64encode(open(p,'rb').read()).decode(),t] for k,(p,t) in files.items()}
  w="const F="+json.dumps(F)+r""";const D=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
export default{async fetch(req){const u=new URL(req.url);let p=u.pathname.slice(1)||'index.html';if(p==='favicon.ico')p='favicon.svg';const f=F[p];if(!f)return new Response('Not found',{status:404});
return new Response(D(f[0]),{headers:{'content-type':f[1],'x-content-type-options':'nosniff','referrer-policy':'no-referrer','x-robots-tag':'noindex','content-security-policy':"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",'cache-control':'public, max-age=60','strict-transport-security':'max-age=31536000; includeSubDomains'}})}};"""
  code="async () => {\nconst scriptName=%s;const script=%s;\n"%(json.dumps(name),json.dumps(w))+r"""let ex=null;try{ex=await cloudflare.request({method:"GET",path:`/accounts/${accountId}/workers/scripts/${scriptName}/settings`})}catch(e){if(!String(e).includes("10007"))throw e}if(!(ex&&ex.success))return {abort:"missing: refusing to create a new worker"};
const b="----F"+Date.now();const body=["--"+b,'Content-Disposition: form-data; name="metadata"',"Content-Type: application/json","",JSON.stringify({main_module:"worker.mjs",compatibility_date:"2026-10-15",bindings:[]}),"--"+b,'Content-Disposition: form-data; name="worker.mjs"; filename="worker.mjs"',"Content-Type: application/javascript+module","",script,"--"+b+"--"].join("\r\n");
const put=await cloudflare.request({method:"PUT",path:`/accounts/${accountId}/workers/scripts/${scriptName}`,body,contentType:`multipart/form-data; boundary=${b}`,rawBody:true});
const sub=await cloudflare.request({method:"POST",path:`/accounts/${accountId}/workers/scripts/${scriptName}/subdomain`,body:{enabled:true}});
return {put:put.success,pe:put.errors,sub:sub.success,se:sub.errors};}"""
  open(out,'w').write(code)
H='text/html; charset=utf-8'
gen('bit-fathom-daily-preview',{'index.html':('/workspace/proto-bot/bit-fathom-daily/index.html',H),'favicon.svg':('/workspace/bf-review/fav.svg','image/svg+xml')},'/workspace/bf-review/deploy-app.js')
import os
fs={'index.html':('site/index.html',H),'favicon.svg':('fav.svg','image/svg+xml')}
for f in os.listdir('img'): fs['img/'+f]=('img/'+f,'image/jpeg')
gen('bit-fathom-review',fs,'/workspace/bf-review/deploy-review.js')
