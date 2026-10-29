/* /r/* is listed in run_worker_first, but a static-assets worker also runs for
   any path that does not match a file. Only ^/r/ gets the riddle card.
   A page-shaped miss outside /r/ is 404.html. A missing file stays a non-HTML 404.
   A _redirects splat cannot do this: it runs before assets and either loops
   or hides /r/001/–/r/112/. */
const R_CSP = "default-src 'self'; script-src 'self'; style-src 'none'; img-src 'self' data:; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'";
const NOT_FOUND_CSP = "default-src 'none'; style-src 'sha256-RaloRxbE3NDnQYHC6+wdtT2RjH5J0h8h8xjtys70374='; font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";
const R_PATH = /^\/r\/(\d{1,5})\/?$/;

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

function hasFileExtension(pathname) {
  return /\.[a-z0-9]+$/i.test(pathname);
}

function notFoundHeaders() {
  const headers = new Headers();
  headers.set('content-type', 'text/html; charset=utf-8');
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('Referrer-Policy', 'no-referrer');
  headers.set('Content-Security-Policy', NOT_FOUND_CSP);
  return headers;
}

async function brandedNotFound(env, origin) {
  const page = await env.ASSETS.fetch(new Request(new URL('/404.html', origin), { method: 'GET' }));
  if (page.status === 404) {
    return new Response('<!doctype html><title>Page not found</title><p>That page is not here.</p>', { status: 404, headers: notFoundHeaders() });
  }
  return new Response(page.body, { status: 404, headers: notFoundHeaders() });
}

async function notFound(env, url, asset) {
  const ctype = (asset.headers.get('content-type') || '').toLowerCase();
  if (hasFileExtension(url.pathname)) {
    if (ctype.includes('text/html')) return new Response(null, { status: 404, headers: securityHeaders() });
    return asset;
  }
  return brandedNotFound(env, url.origin);
}

async function genericCard(env, origin) {
  const fallback = await env.ASSETS.fetch(new Request(new URL('/r/fallback/index.html', origin), { method: 'GET' }));
  if (fallback.status === 404) {
    const headers = securityHeaders({ 'content-type': 'text/html; charset=utf-8' });
    return new Response('<!doctype html><title>Riddle not found</title><p>That riddle link is not one we know.</p>', { status: 404, headers });
  }
  return seal(fallback, 200);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const bare = url.pathname.replace(/\/+$/, '') || '/';
    if (bare === '/404' || bare === '/404.html') return brandedNotFound(env, url.origin);
    const asset = await env.ASSETS.fetch(request);
    if (asset.status !== 404) return seal(asset);

    if (!url.pathname.startsWith('/r/')) return notFound(env, url, asset);

    const digits = url.pathname.match(R_PATH);
    if (!digits) return genericCard(env, url.origin);

    const n = parseInt(digits[1], 10);
    if (!(n >= 1)) return genericCard(env, url.origin);

    const padded = String(n).padStart(3, '0');
    const canon = '/r/' + padded + '/';
    const canonRes = await env.ASSETS.fetch(new Request(new URL(canon, url.origin), { method: 'GET' }));
    if (canonRes.status !== 404) {
      if (url.pathname !== canon) return redirect(canon);
      return seal(canonRes);
    }
    return redirect('/?d=' + padded);
  },
};
