#!/usr/bin/env python3
"""Refresh review/share-loop/ after the tests. Not imported by the e2e suite."""
import functools, http.server, os, shutil, subprocess, tempfile, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
OG = ROOT / 'static-assets' / 'og'
REVIEW = Path(os.environ['BF_REVIEW_DIR']) if os.environ.get('BF_REVIEW_DIR') else Path(tempfile.mkdtemp(prefix='bf-review-'))
CHROME = '/usr/bin/google-chrome'
READY = 'document.querySelectorAll("#choices button").length>0'


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        return


def serve():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(DIST)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}/'


def open_ready(page, url):
    page.goto(url)
    page.wait_for_function(READY)
    page.evaluate('() => document.fonts.ready')


def solve(page):
    idx = page.evaluate('''() => {
      const raw = document.getElementById('inline-riddles').textContent;
      const riddles = JSON.parse(raw);
      const epoch = new Date(2026, 9, 12);
      const now = new Date();
      const day = Math.round((new Date(now.getFullYear(), now.getMonth(), now.getDate()) - epoch) / 86400000);
      return riddles[((day % riddles.length) + riddles.length) % riddles.length].answer_index;
    }''')
    page.locator('#choices button').nth(idx).click()
    page.wait_for_function('() => !document.getElementById("reveal").hidden')
    page.wait_for_timeout(500)


def shot(page, name):
    page.screenshot(path=str(REVIEW / name))


def record(browser, url, name, wrong):
    tmp = REVIEW / '_video'
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    ctx = browser.new_context(
        viewport={'width': 1366, 'height': 900},
        record_video_dir=str(tmp),
        record_video_size={'width': 1366, 'height': 900},
    )
    page = ctx.new_page()
    open_ready(page, url)
    if wrong:
        page.locator('#choices button').nth(0).click()
        page.wait_for_timeout(400)
        # If the first button was the answer, the reveal is showing; otherwise why-not is.
        page.wait_for_timeout(700)
    else:
        solve(page)
    page.wait_for_timeout(1200)
    video = page.video
    ctx.close()
    raw = REVIEW / f'{name}-raw.webm'
    video.save_as(str(raw))
    dest = REVIEW / f'{name}.webm'
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        subprocess.run([ffmpeg, '-y', '-sseof', '-5', '-i', str(raw), '-c', 'copy', str(dest)], check=False, capture_output=True)
        if not dest.exists() or dest.stat().st_size < 1000:
            shutil.copy(raw, dest)
    else:
        shutil.copy(raw, dest)
    raw.unlink(missing_ok=True)
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    lines = []
    for png in sorted(OG.glob('*.png')):
        lines.append(f'{png.name}\t1200x630\t{png.stat().st_size}B')
    (REVIEW / 'og-sizes.txt').write_text('\n'.join(lines) + '\n')
    for name in ('001.png', '004.png'):
        src = OG / name
        if src.exists():
            (REVIEW / f'og-{name[:3]}.png').write_bytes(src.read_bytes())
    srv, url = serve()
    desktop = {'viewport': {'width': 1366, 'height': 900}}
    mobile = {'viewport': {'width': 390, 'height': 844}, 'device_scale_factor': 2, 'has_touch': True, 'is_mobile': True}
    reduced = {'viewport': {'width': 1366, 'height': 900}, 'reduced_motion': 'reduce'}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME if Path(CHROME).exists() else None)
        for tag, kwargs in (('desktop', desktop), ('mobile', mobile)):
            ctx = browser.new_context(**kwargs)
            page = ctx.new_page()
            open_ready(page, url)
            shot(page, f'{tag}-first.png')
            solve(page)
            page.locator('#reveal').screenshot(path=str(REVIEW / f'{tag}-share.png'))
            page.locator('#count').scroll_into_view_if_needed()
            shot(page, f'{tag}-countdown.png')
            page.locator('#statsBtn').click()
            page.wait_for_function('() => !document.getElementById("statsModal").hidden')
            page.locator('#statsModal .sheet').screenshot(path=str(REVIEW / f'{tag}-stats.png'))
            ctx.close()
        ctx = browser.new_context(**reduced)
        page = ctx.new_page()
        open_ready(page, url)
        page.locator('#choices button').first.click()
        page.wait_for_timeout(400)
        shot(page, 'reduced-wrong.png')
        ctx.close()
        ctx = browser.new_context(**reduced)
        page = ctx.new_page()
        open_ready(page, url)
        solve(page)
        shot(page, 'reduced-result.png')
        ctx.close()
        for width, height, name in ((1024, 900, 'desktop-1024.png'), (1366, 900, 'desktop-1366.png'), (1920, 1080, 'desktop-1920.png')):
            ctx = browser.new_context(viewport={'width': width, 'height': height})
            page = ctx.new_page()
            open_ready(page, url)
            shot(page, name)
            ctx.close()
        record(browser, url, 'wrong', True)
        record(browser, url, 'right', False)
        browser.close()
    srv.shutdown()
    print('PASS review artifacts', REVIEW)


if __name__ == '__main__':
    main()
