/* /r/* runs in the Worker first (wrangler.jsonc run_worker_first).
   A real page is served from assets. Anything else gets a redirect to the
   game for a puzzle number we have not built, or the generic card.
   _redirects cannot do this: a splat matches the fallback itself (workerd
   drops it as a loop) and redirects run before assets, so a catch-all would
   hide /r/001/–/r/112/. */
const R_CSP = "default-src 'self'; script-src 'self'; style-src 'none'; img-src 'self' data:; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'";

function securityHeaders(extra) {
  const headers = new Headers(extra || undefined);
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('Referrer-Policy', 'no-referrer');
  if (!headers.get('Content-Security-Policy')) headers.set('Content-Security-Policy', R_CSP);
  return headers;
}

function redirect(location) {
  const headers = securityHeaders();
  headers.set('Location', location);
  return new Response(null, { status: 302, headers });
}

function seal(response, status) {
  const headers = securityHeaders(response.headers);
  return new Response(response.body, { status: status == null ? response.status : status, headers });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const asset = await env.ASSETS.fetch(request);
    if (asset.status !== 404) return seal(asset);

    const path = url.pathname.replace(/\/+$/, '') || '/';
    const digits = path.match(/^\/r\/(\d+)$/);
    if (digits) {
      const n = parseInt(digits[1], 10);
      if (n >= 1) {
        const padded = String(n).padStart(3, '0');
        const canon = '/r/' + padded + '/';
        const canonRes = await env.ASSETS.fetch(new Request(new URL(canon, url.origin), { method: 'GET' }));
        if (canonRes.status !== 404) {
          if (url.pathname !== canon) return redirect(canon);
          return seal(canonRes);
        }
        return redirect('/?d=' + padded);
      }
    }

    const fallback = await env.ASSETS.fetch(new Request(new URL('/r/fallback/index.html', url.origin), { method: 'GET' }));
    if (fallback.status === 404) {
      const headers = securityHeaders({ 'content-type': 'text/html; charset=utf-8' });
      return new Response('<!doctype html><title>Riddle not found</title><p>That riddle link is not one we know.</p>', { status: 404, headers });
    }
    return seal(fallback, 200);
  },
};
