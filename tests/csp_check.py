#!/usr/bin/env python3
"""Hash CSP is present, has no unsafe-inline, and the page still plays."""
import functools, http.server, re, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
CHROME = '/usr/bin/google-chrome'
fail = 0


def check(name, cond, detail=''):
    global fail
    fail += 0 if cond else 1
    print(('PASS ' if cond else 'FAIL ') + name + (f' ({detail})' if detail else ''))


def csp_of(html):
    m = re.search(r'Content-Security-Policy" content="([^"]+)"', html)
    return m.group(1) if m else ''


def main():
    home = (DIST / 'index.html').read_text()
    policy = csp_of(home)
    check('home csp hash', "script-src 'sha256-" in policy and "style-src 'sha256-" in policy, policy[:180])
    check('home csp no unsafe-inline', policy and 'unsafe-inline' not in policy and "script-src 'self'" not in policy)
    check('home csp worker and img', "worker-src 'self'" in policy and "img-src 'self' data:" in policy)
    numbered = csp_of((DIST / 'r' / '001' / 'index.html').read_text())
    check('numbered page csp', "script-src 'none'" in numbered and 'unsafe-inline' not in numbered, numbered)
    fallback = csp_of((DIST / 'r' / 'fallback' / 'index.html').read_text())
    check('fallback csp allows its script', "script-src 'self'" in fallback and 'unsafe-inline' not in fallback)
    headers = (DIST / '_headers').read_text()
    check('headers carry csp and nosniff', 'Content-Security-Policy:' in headers and "frame-ancestors 'none'" in headers and 'nosniff' in headers and 'no-referrer' in headers and 'unsafe-inline' not in headers)
    check('meta omits frame-ancestors', 'frame-ancestors' not in policy and 'frame-ancestors' not in numbered)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            return

    srv = http.server.ThreadingHTTPServer(
        ('127.0.0.1', 0),
        functools.partial(Quiet, directory=str(DIST)),
    )
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{srv.server_address[1]}/'
    violations = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME if Path(CHROME).exists() else None)
        page = browser.new_page()
        page.on('console', lambda msg: violations.append(msg.text) if 'Content Security Policy' in msg.text or msg.text.startswith('Refused to') else None)
        page.on('pageerror', lambda err: violations.append(str(err)))
        page.goto(url)
        page.wait_for_function('document.querySelectorAll("#choices button").length > 0')
        page.locator('#choices button').first.click()
        struck = page.locator('#choices button.wrong, #choices button.right').count()
        check('play works under csp', struck >= 1, str(struck))
        check('no csp console violations', not violations, ' | '.join(violations[:3]))
        browser.close()
    srv.shutdown()
    print('RESULT', 'PASS' if fail == 0 else f'FAIL ({fail})')
    raise SystemExit(1 if fail else 0)


if __name__ == '__main__':
    main()
