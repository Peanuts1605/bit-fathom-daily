#!/usr/bin/env python3
"""Build the Daily Riddle site.

Writes index.html (repo root, for the existing tests) and a complete site in dist/:
index.html, r/NNN/index.html, og/NNN.png, manifest, icon, service worker, assets.
"""
import json, os, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
ORIGIN = os.environ.get('BF_ORIGIN', 'https://bit-fathom-daily-next.gigantic-stranger.workers.dev').rstrip('/')
MAX_PUZZLE = int(os.environ.get('BF_OG_DAYS', '28'))
BUDGET = 2_500_000


def esc(s):
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


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
    return html


def static_page(num, riddle, encore):
    n = f'{num:03d}'
    hook = (riddle.get('hook') or riddle['title']).strip()
    title = f'Bit & Fathom Daily Riddle #{n}'
    desc = hook + ' Guess first. The answer is not on this card.'
    alt = f'Bit the robot asks: {hook}'
    image = f'{ORIGIN}/og/{n}.png'
    badge = ' Encore.' if encore else ''
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
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
<link rel="canonical" href="{ORIGIN}/r/{n}/">
</head><body>
<main>
<p>Bit &amp; Fathom Daily Riddle</p>
<h1>{esc(hook)}</h1>
<p>{esc(desc)}{esc(badge)}</p>
<p><a href="/?d={n}">Play riddle #{n}</a></p>
</main>
</body></html>
'''


def copy_tree(src, dest):
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def quantize_backgrounds(folder):
    if not shutil.which('pngquant'):
        return
    for png in folder.glob('*.png'):
        tmp = png.with_suffix('.q.png')
        r = subprocess.run(['pngquant', '--quality', '60-85', '--speed', '1', '--force', '--output', str(tmp), str(png)], capture_output=True)
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size < png.stat().st_size:
            tmp.replace(png)
        elif tmp.exists():
            tmp.unlink()


def dir_size(path):
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())


def main():
    riddles = json.loads((ROOT / 'riddles.json').read_text())
    html = build_html(riddles)
    if 'fetch(' in html:
        raise SystemExit('FAIL build: index.html contains fetch(')
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
    copy_tree(ROOT / 'assets', DIST / 'assets')
    quantize_backgrounds(DIST / 'assets' / 'backgrounds')
    for n in range(1, MAX_PUZZLE + 1):
        r = riddles[(n - 1) % len(riddles)]
        folder = DIST / 'r' / f'{n:03d}'
        folder.mkdir(parents=True)
        (folder / 'index.html').write_text(static_page(n, r, n - 1 >= len(riddles)))
    # OG cards (Playwright). Import after the HTML exists so a failure still leaves the page.
    os.environ['BF_OG_DAYS'] = str(MAX_PUZZLE)
    import importlib.util
    spec = importlib.util.spec_from_file_location('render_og', ROOT / 'og' / 'render_og.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.render_all()
    total = dir_size(DIST)
    mb = total / 1_000_000
    print(f'dist bytes {total} ({mb:.2f} MB), puzzles 001-{MAX_PUZZLE:03d} + today')
    if total > BUDGET:
        print('WARN dist over 2.5MB — switch to Workers Static Assets')
    print('PASS build')


if __name__ == '__main__':
    main()
