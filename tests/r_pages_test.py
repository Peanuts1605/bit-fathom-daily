#!/usr/bin/env python3
"""Every scheduled /r/NNN/ through 2027-01-31 exists. Unknown numbers use the fallback."""
import http.server, re, threading
from datetime import date
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
CHROME = '/usr/bin/google-chrome'
CANON = 'https://bit-fathom-daily-next.gigantic-stranger.workers.dev'
EPOCH = date(2026, 10, 12)
THROUGH = date(2027, 1, 31)
COUNT = (THROUGH - EPOCH).days + 1
fail = 0


def check(name, cond, detail=''):
    global fail
    fail += 0 if cond else 1
    print(('PASS ' if cond else 'FAIL ') + name + (f' ({detail})' if detail else ''))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def log_message(self, *args):
        return

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        rel = path.lstrip('/')
        if rel.endswith('/'):
            rel += 'index.html'
        target = (DIST / rel).resolve()
        if str(target).startswith(str(DIST.resolve())) and target.is_file():
            return super().do_GET()
        if re.fullmatch(r'/r/\d+/?', path):
            self.path = '/r/fallback/index.html'
            return super().do_GET()
        self.send_error(404)


def main():
    check('puzzle count through Jan 31', COUNT == 112, str(COUNT))
    missing = []
    for n in range(1, COUNT + 1):
        page = DIST / 'r' / f'{n:03d}' / 'index.html'
        if not page.is_file():
            missing.append(f'{n:03d}')
            continue
        html = page.read_text()
        url = f'{CANON}/r/{n:03d}/'
        if f'og:url" content="{url}"' not in html and f"og:url\" content=\"{url}\"" not in html:
            if url not in html:
                missing.append(f'{n:03d}:ogurl')
        if f'/?d={n:03d}' not in html:
            missing.append(f'{n:03d}:link')
        if 'unsafe-inline' in html:
            missing.append(f'{n:03d}:csp')
    check('pages 001-112 with og:url', not missing, ','.join(missing[:8]))
    check('029 is a real page', (DIST / 'r' / '029' / 'index.html').is_file() and 'go.js' not in (DIST / 'r' / '029' / 'index.html').read_text())
    redirects = (DIST / '_redirects').read_text()
    check('splat redirect', '/r/* /r/fallback/index.html 200' in redirects, redirects.strip())
    fb = (DIST / 'r' / 'fallback' / 'index.html').read_text()
    check('fallback generic card', 'today.png' in fb and '/r/fallback/go.js' in fb and 'og:url' in fb)
    check('fallback script is absolute', 'src="/r/fallback/go.js"' in fb)

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{srv.server_address[1]}'
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME if Path(CHROME).exists() else None)
        page = browser.new_page()
        page.goto(origin + '/r/999/', wait_until='domcontentloaded')
        page.wait_for_url('**/?d=999')
        check('unknown /r/999 redirects to ?d=999', page.url.endswith('/?d=999') or '?d=999' in page.url, page.url)
        page.goto(origin + '/r/029/', wait_until='domcontentloaded')
        page.wait_for_url('**/?d=029')
        check('029 plays instead of the generic fallback', '?d=029' in page.url, page.url)
        browser.close()
    srv.shutdown()
    print('RESULT', 'PASS' if fail == 0 else f'FAIL ({fail})')
    raise SystemExit(1 if fail else 0)


if __name__ == '__main__':
    main()
