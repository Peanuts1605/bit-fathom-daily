#!/usr/bin/env python3
"""Build the Daily Riddle site.

dist/ is the inline-worker bundle (HTML, shell, fonts, backgrounds). It must
stay <= 2.5 MB. og cards live in static-assets/og/ and are served as Workers
Static Assets, not inlined into the worker.

Puzzle pages run from #001 (12 Oct 2026) through at least 31 Jan 2027.
Unknown /r/NNN/ URLs are rewritten to r/fallback/ (see dist/_redirects).
"""
import base64, hashlib, json, os, re, shutil, subprocess, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
OG_DIR = ROOT / 'static-assets' / 'og'
ORIGIN = os.environ.get('BF_ORIGIN', 'https://bit-fathom-daily-next.gigantic-stranger.workers.dev').rstrip('/')
EPOCH = date(2026, 10, 12)
THROUGH = date(2027, 1, 31)
BUDGET = 2_500_000
UNICODES = 'U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+2013-2014,U+2018-201A,U+201C-201E,U+2022,U+2026,U+2030,U+20AC,U+2122'


def puzzle_count():
    """1-based puzzle number for THROUGH, inclusive. #001 is EPOCH."""
    return (THROUGH - EPOCH).days + 1


def esc(s):
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def csp_hash(text):
    digest = hashlib.sha256(text.encode('utf-8')).digest()
    return 'sha256-' + base64.b64encode(digest).decode('ascii')


def page_policy(script_hash, style_hash):
    return (
        "default-src 'self'; "
        f"script-src '{script_hash}'; "
        "worker-src 'self'; "
        f"style-src '{style_hash}'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'none'"
    )


def r_policy(script):
    return (
        "default-src 'self'; "
        f"script-src {script}; "
        "style-src 'none'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'none'"
    )


def apply_csp(html):
    style = re.search(r'<style>(.*?)</style>', html, re.S)
    script = re.search(r'<script>(.*?)</script>', html, re.S)
    if not style or not script:
        raise SystemExit('FAIL build: missing inline style or script for CSP')
    policy = page_policy(csp_hash(script.group(1)), csp_hash(style.group(1)))
    if 'unsafe-inline' in policy:
        raise SystemExit('FAIL build: CSP contains unsafe-inline')
    if '%%CSP%%' not in html:
        raise SystemExit('FAIL build: CSP placeholder missing')
    return html.replace('%%CSP%%', policy), policy


def build_html(riddles):
    raw = json.dumps(riddles, ensure_ascii=False).replace('</', '<\\/')
    html = (ROOT / 'src.html').read_text()
    html = html.replace('%%JUICECSS%%', (ROOT / 'src' / 'juice.css').read_text())
    html = html.replace('%%JUICEJS%%', (ROOT / 'src' / 'juice.js').read_text())
    html = html.replace('%%SHAREJS%%', (ROOT / 'src' / 'share.js').read_text())
    html = html.replace('%%STATSJS%%', (ROOT / 'src' / 'stats.js').read_text())
    html = html.replace('%%COUNTDOWNJS%%', (ROOT / 'src' / 'countdown.js').read_text())
    html = html.replace('%%APPJS%%', (ROOT / 'src' / 'app.js').read_text())
    html = html.replace('%%INLINE%%', raw)
    html = html.replace('%%ORIGIN%%', ORIGIN)
    hook = 'true' if os.environ.get('BF_TEST_HOOK') == '1' else 'false'
    html = html.replace('%%TESTHOOK%%', hook)
    return html


def static_page(num, riddle, encore):
    n = f'{num:03d}'
    hook = (riddle.get('hook') or riddle['title']).strip()
    title = f'Bit & Fathom Daily Riddle #{n}'
    desc = hook + ' Guess first. The answer is not on this card.'
    alt = f'Bit the robot asks: {hook}'
    image = f'{ORIGIN}/og/{n}.png'
    url = f'{ORIGIN}/r/{n}/'
    badge = f' Encore of #{riddle["id"]}.' if encore else ''
    policy = esc(r_policy("'none'"))
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{policy}">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(alt)}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{image}">
<meta name="twitter:image:alt" content="{esc(alt)}">
<meta http-equiv="refresh" content="0;url=/?d={n}">
<link rel="canonical" href="{url}">
</head><body>
<main>
<p>Bit &amp; Fathom Daily Riddle</p>
<h1>{esc(hook)}</h1>
<p>{esc(desc)}{esc(badge)}</p>
<p><a href="/?d={n}">Play riddle #{n}</a></p>
</main>
</body></html>
'''


def fallback_page():
    policy = esc(r_policy("'self'"))
    image = f'{ORIGIN}/og/today.png'
    desc = 'A new science riddle is waiting. Guess first. The answer is not on this card.'
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{policy}">
<title>Bit &amp; Fathom Daily Riddle</title>
<meta name="description" content="{desc}">
<meta property="og:url" content="{ORIGIN}/">
<meta property="og:title" content="Bit &amp; Fathom Daily Riddle">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Bit the robot on a starry card that says a new riddle is waiting. No answer is shown.">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Bit &amp; Fathom Daily Riddle">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{image}">
<link rel="canonical" href="{ORIGIN}/">
</head><body>
<main>
<p>Bit &amp; Fathom Daily Riddle</p>
<h1>A new science riddle is waiting.</h1>
<p>{desc}</p>
<p><a href="/">Play today's riddle</a></p>
</main>
<script src="/r/fallback/go.js"></script>
</body></html>
'''


FALLBACK_JS = """(function(){
  var m = location.pathname.match(/\\/r\\/(\\d+)/);
  if (!m) return;
  var n = String(parseInt(m[1], 10));
  if (!n || n === 'NaN') return;
  while (n.length < 3) n = '0' + n;
  location.replace('/?d=' + n);
})();
"""


def write_headers(policy):
    # frame-ancestors is ignored in a meta tag, so it lives only in these headers.
    policy = policy + "; frame-ancestors 'none'"
    nosniff = 'X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer'
    rpol = r_policy("'self'") + "; frame-ancestors 'none'"
    text = (
        '/\n'
        f'  Content-Security-Policy: {policy}\n'
        f'  {nosniff}\n'
        '\n'
        '/index.html\n'
        f'  Content-Security-Policy: {policy}\n'
        f'  {nosniff}\n'
        '\n'
        '/r/*\n'
        f'  Content-Security-Policy: {rpol}\n'
        f'  {nosniff}\n'
    )
    (DIST / '_headers').write_text(text)
    (DIST / '_redirects').write_text('/r/* /r/fallback/index.html 200\n')


def require_pngquant():
    if not shutil.which('pngquant'):
        raise SystemExit('FAIL build: pngquant is not installed (see requirements.txt)')


def quantize_backgrounds(folder):
    require_pngquant()
    for png in folder.glob('*.png'):
        tmp = png.with_suffix('.q.png')
        r = subprocess.run(
            ['pngquant', '--quality', '60-85', '--speed', '1', '--force', '--output', str(tmp), str(png)],
            capture_output=True)
        if r.returncode != 0 or not tmp.exists():
            raise SystemExit(f'FAIL build: pngquant failed on {png.name}')
        if tmp.stat().st_size < png.stat().st_size:
            tmp.replace(png)
        else:
            tmp.unlink()


def subset_fonts():
    src = ROOT / 'assets' / 'fonts'
    jobs = (
        ('BricolageGrotesque-opsz-wdth-wght.ttf', 'BricolageGrotesque-subset.woff2'),
        ('AtkinsonHyperlegibleNext-wght.ttf', 'AtkinsonHyperlegibleNext-subset.woff2'),
    )
    for name, out_name in jobs:
        out = src / out_name
        cmd = [
            sys.executable, '-m', 'fontTools.subset',
            str(src / name),
            f'--output-file={out}',
            '--flavor=woff2',
            f'--unicodes={UNICODES}',
            '--layout-features=*',
            '--ignore-missing-unicodes',
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            raise SystemExit('FAIL build: font subset ' + name + '\n' + (r.stderr or r.stdout or ''))


def copy_tree(src, dest):
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def dir_size(path):
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())


def main():
    require_pngquant()
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise SystemExit('FAIL build: Pillow is not installed (pip install -r requirements.txt)')
    count = puzzle_count()
    riddles = json.loads((ROOT / 'riddles.json').read_text())
    html = build_html(riddles)
    if 'fetch(' in html:
        raise SystemExit('FAIL build: index.html contains fetch(')
    if 'location.origin' in html:
        raise SystemExit('FAIL build: share URL still uses location.origin')
    html, policy = apply_csp(html)
    (ROOT / 'index.html').write_text(html)
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / 'index.html').write_text(html)
    (DIST / 'sw.js').write_text((ROOT / 'src' / 'sw.js').read_text())
    shutil.copy(ROOT / 'app-src' / 'www' / 'manifest.json', DIST / 'manifest.json')
    shutil.copy(ROOT / 'app-src' / 'www' / 'icon.svg', DIST / 'icon.svg')
    shutil.copy(ROOT / 'app-src' / 'www' / 'icon.svg', ROOT / 'icon.svg')
    shutil.copy(ROOT / 'app-src' / 'www' / 'manifest.json', ROOT / 'manifest.json')
    subset_fonts()
    copy_tree(ROOT / 'assets', DIST / 'assets')
    for ttf in (DIST / 'assets' / 'fonts').glob('*.ttf'):
        ttf.unlink()
    quantize_backgrounds(DIST / 'assets' / 'backgrounds')
    for n in range(1, count + 1):
        r = riddles[(n - 1) % len(riddles)]
        folder = DIST / 'r' / f'{n:03d}'
        folder.mkdir(parents=True)
        (folder / 'index.html').write_text(static_page(n, r, n - 1 >= len(riddles)))
    fb = DIST / 'r' / 'fallback'
    fb.mkdir(parents=True)
    (fb / 'index.html').write_text(fallback_page())
    (fb / 'go.js').write_text(FALLBACK_JS)
    write_headers(policy)
    os.environ['BF_OG_DAYS'] = str(count)
    os.environ['BF_OG_DIR'] = str(OG_DIR)
    have = len(list(OG_DIR.glob('*.png'))) if OG_DIR.exists() else 0
    if os.environ.get('BF_SKIP_OG') == '1' and have >= count + 1:
        print(f'skip og render ({have} pngs already in static-assets/og)')
    else:
        import importlib.util
        spec = importlib.util.spec_from_file_location('render_og', ROOT / 'og' / 'render_og.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.render_all()
    total = dir_size(DIST)
    og_total = dir_size(OG_DIR) if OG_DIR.exists() else 0
    print(f'dist bytes {total} ({total/1_000_000:.2f} MB), puzzles 001-{count:03d} through {THROUGH.isoformat()}')
    print(f'static-assets/og bytes {og_total} ({og_total/1_000_000:.2f} MB) excluded from the worker bundle')
    if total > BUDGET:
        print('FAIL dist over 2.5MB — Workers Static Assets hold og/; the HTML bundle must still fit')
        raise SystemExit(1)
    print('PASS build')


if __name__ == '__main__':
    main()
