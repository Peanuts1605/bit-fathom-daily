#!/usr/bin/env python3
""" /r/ routes against wrangler dev --local (workerd), not a Python redirect emulation.

Real pages 001 and 112 are assets. Later puzzle numbers redirect to /?d=NNN.
Malformed /r/ paths return the generic card. Every other miss is a real 404.
CSP and nosniff stay on the riddle responses.
"""
import base64, hashlib, http.client, os, re, shutil, socket, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WRANGLER = ROOT / 'node_modules' / '.bin' / 'wrangler'
CANON = 'https://bit-fathom-daily-next.gigantic-stranger.workers.dev'
fail = 0


def check(name, cond, detail=''):
    global fail
    fail += 0 if cond else 1
    print(('PASS ' if cond else 'FAIL ') + name + (f' ({detail})' if detail else ''))


def free_port():
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def fetch(port, path):
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=20)
    conn.request('GET', path)
    res = conn.getresponse()
    raw = res.read()
    headers = {k.lower(): v for k, v in res.getheaders()}
    conn.close()
    return res.status, headers, raw


def text(raw):
    return raw.decode('utf-8', 'replace')


def location_is(headers, expected):
    return headers.get('location', '') == expected


def png_card(raw, headers):
    ctype = headers.get('content-type', '').split(';')[0].strip().lower()
    if ctype != 'image/png' or not raw.startswith(b'\x89PNG\r\n\x1a\n') or len(raw) < 24:
        return False
    width = int.from_bytes(raw[16:20], 'big')
    height = int.from_bytes(raw[20:24], 'big')
    return width == 1200 and height == 630


def header_ok(headers):
    csp = headers.get('content-security-policy', '')
    return (
        'unsafe-inline' not in csp
        and "frame-ancestors 'none'" in csp
        and headers.get('x-content-type-options') == 'nosniff'
        and headers.get('referrer-policy') == 'no-referrer'
    )


def main():
    if not WRANGLER.is_file():
        raise SystemExit('FAIL wrangler is not installed (npm ci)')
    if not (ROOT / 'publish' / 'r' / '001' / 'index.html').is_file():
        raise SystemExit('FAIL publish/ is missing (run build.py)')
    if (ROOT / 'publish' / '_redirects').exists():
        raise SystemExit('FAIL publish/_redirects must not exist (workerd rejects the /r/* splat)')
    port = free_port()
    persist = Path('/tmp/bf-wrangler-persist')
    if persist.exists():
        shutil.rmtree(persist)
    log_path = Path('/tmp/bf-wrangler-dev.log')
    log = open(log_path, 'w')
    env = os.environ.copy()
    env['CI'] = '1'
    env['WRANGLER_SEND_METRICS'] = 'false'
    proc = subprocess.Popen(
        [str(WRANGLER), 'dev', '--local', '--port', str(port), '--ip', '127.0.0.1',
         '--persist-to', str(persist), '--config', 'wrangler.jsonc'],
        cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    try:
        ready = False
        for _ in range(90):
            if proc.poll() is not None:
                break
            try:
                status, _, _ = fetch(port, '/')
                if status in (200, 304):
                    ready = True
                    break
            except OSError:
                time.sleep(0.5)
                continue
            time.sleep(0.5)
        log.flush()
        startup = log_path.read_text(errors='replace')
        check('wrangler dev ready', ready, startup[-400:].replace('\n', ' | '))
        check('no infinite-loop redirect', 'Infinite loop' not in startup, 'see /tmp/bf-wrangler-dev.log')
        if not ready:
            print('RESULT FAIL')
            raise SystemExit(1)

        status, headers, raw = fetch(port, '/r/001/')
        body = text(raw)
        check('r/001 asset', status == 200 and f'{CANON}/r/001/' in body and 'Play riddle #001' in body, f'{status}')
        check('r/001 security headers', header_ok(headers), headers.get('content-security-policy', '')[:120])

        status, headers, raw = fetch(port, '/r/112/')
        body = text(raw)
        check('r/112 asset', status == 200 and f'{CANON}/r/112/' in body and 'Play riddle #112' in body, f'{status}')
        check('r/112 security headers', header_ok(headers))

        status, headers, raw = fetch(port, '/r/029')
        loc = headers.get('location', '')
        check('r/029 adds the trailing slash', status == 307 and location_is(headers, '/r/029/'), f'{status} {loc}')

        status, headers, raw = fetch(port, '/r/113/')
        loc = headers.get('location', '')
        check('r/113 redirects past the last page', status == 302 and location_is(headers, '/?d=113'), f'{status} {loc}')
        check('r/113 security headers', header_ok(headers))

        status, headers, _ = fetch(port, '/r/999')
        loc = headers.get('location', '')
        check('r/999 redirects', status == 302 and location_is(headers, '/?d=999'), f'{status} {loc}')
        check('r/999 security headers', header_ok(headers))

        status, headers, raw = fetch(port, '/r/abc')
        body = text(raw)
        check('r/abc generic card', status == 200 and 'today.png' in body and 'A new science riddle is waiting' in body, f'{status}')
        check('r/abc security headers', header_ok(headers))

        status, headers, raw = fetch(port, '/r/000')
        body = text(raw)
        check('r/000 generic card', status == 200 and 'today.png' in body and 'A new science riddle is waiting' in body, f'{status}')
        check('r/000 security headers', header_ok(headers))

        status, headers, _ = fetch(port, '/r/0029')
        loc = headers.get('location', '')
        check('r/0029 canonical page', status == 302 and location_is(headers, '/r/029/'), f'{status} {loc}')
        check('r/0029 security headers', header_ok(headers))

        huge = '/r/' + ('9' * 30)
        status, headers, raw = fetch(port, huge)
        body = text(raw)
        check('30 nines stay on the generic card', status == 200 and 'location' not in headers and 'A new science riddle is waiting' in body, f'{status} {headers.get("location", "")}')

        longer = '/r/' + ('9' * 400)
        status, headers, raw = fetch(port, longer)
        body = text(raw)
        check('400 digits stay on the generic card', status == 200 and 'location' not in headers and 'A new science riddle is waiting' in body and 'Infinity' not in body, f'{status} {headers.get("location", "")}')

        status, headers, raw = fetch(port, '/nope')
        check('missing path is a 404', status == 404 and 'A new science riddle is waiting' not in text(raw), f'{status} {headers.get("content-type")}')
        page_html = (ROOT / 'publish' / '404.html').read_text()
        style = re.search(r'<style>(.*?)</style>', page_html, re.S)
        style_hash = 'sha256-' + base64.b64encode(hashlib.sha256(style.group(1).encode('utf-8')).digest()).decode('ascii')
        csp = headers.get('content-security-policy', '')
        check(
            '404 page csp',
            "default-src 'none'" in csp
            and f"style-src '{style_hash}'" in csp
            and "font-src 'self'" in csp
            and "base-uri 'none'" in csp
            and "form-action 'none'" in csp
            and "frame-ancestors 'none'" in csp
            and 'unsafe-inline' not in csp,
            csp[:200],
        )

        status, headers, raw = fetch(port, '/404')
        check('/404 is status 404', status == 404 and 'Page not found' in text(raw), f'{status} {headers.get("location", "")}')

        status, headers, raw = fetch(port, '/og/999.png')
        ctype = headers.get('content-type', '')
        check('missing og is a 404', status == 404 and 'text/html' not in ctype.lower() and 'A new science riddle is waiting' not in text(raw), f'{status} {ctype}')

        status, headers, raw = fetch(port, '/R/029/')
        check('uppercase /R/ is a 404', status == 404 and 'A new science riddle is waiting' not in text(raw), f'{status}')

        status, headers, raw = fetch(port, '/og/001.png')
        check('og merge /og/001.png', status == 200 and png_card(raw, headers), f'{status} {headers.get("content-type")} {len(raw)}')
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
    print('RESULT', 'PASS' if fail == 0 else f'FAIL ({fail})')
    raise SystemExit(1 if fail else 0)


if __name__ == '__main__':
    main()
