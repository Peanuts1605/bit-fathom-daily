#!/usr/bin/env python3
"""Static og:image and per-riddle HTML checks. No browser."""
import re, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
MAX = 150 * 1024
NEED = ('og:title', 'og:description', 'og:image', 'og:image:width', 'og:image:height', 'og:image:alt', 'twitter:card')
fail = 0

def check(name, cond, detail=''):
    global fail
    if cond:
        print('PASS', name)
    else:
        fail += 1
        print('FAIL', name, detail)

def meta(html, prop):
    m = re.search(r'<meta[^>]+(?:property|name)="' + re.escape(prop) + r'"[^>]+content="([^"]*)"', html)
    if not m:
        m = re.search(r'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="' + re.escape(prop) + r'"', html)
    return m.group(1) if m else ''

pages = [DIST / 'index.html'] + sorted((DIST / 'r').glob('*/index.html'))
check('static pages exist', len(pages) > 14, str(len(pages)))
riddles = __import__('json').loads((ROOT / 'riddles.json').read_text())

def page_choices(page):
    """Spoilers are this page's own choices. A one-digit choice must not flag every #001."""
    parent = page.parent.name
    if parent.isdigit():
        r = riddles[(int(parent) - 1) % len(riddles)]
        return list(r['choices'])
    return [c for r in riddles for c in r['choices']]

for page in pages:
    html = page.read_text()
    rel = str(page.relative_to(DIST))
    title = meta(html, 'og:title')
    desc = meta(html, 'og:description')
    image = meta(html, 'og:image')
    alt = meta(html, 'og:image:alt')
    card = meta(html, 'twitter:card')
    ok = all([
        title, desc, alt,
        image.startswith('https://') and image.endswith('.png'),
        meta(html, 'og:image:width') == '1200',
        meta(html, 'og:image:height') == '630',
        card == 'summary_large_image',
    ])
    blob = '\n'.join((title, desc, alt))
    def leaked_choice(choice):
        if not choice:
            return False
        if choice.isdigit():
            return re.search(r'(?<!\d)' + re.escape(choice) + r'(?!\d)', blob) is not None
        return choice in blob
    leaked = [a for a in page_choices(page) if leaked_choice(a)]
    check(f'og meta {rel}', ok and not leaked, f'title={title[:40]!r} image={image} leaked={leaked[:3]}')

pngs = sorted((DIST / 'og').glob('*.png'))
check('og png count', len(pngs) >= 15, str(len(pngs)))
lines = []
for png in pngs:
    im = Image.open(png)
    size = png.stat().st_size
    ok = im.size == (1200, 630) and size <= MAX
    check(f'png {png.name}', ok, f'{im.size} {size}B')
    lines.append(f'{png.name}\t{im.size[0]}x{im.size[1]}\t{size}B')
review = ROOT / 'review' / 'share-loop'
review.mkdir(parents=True, exist_ok=True)
(review / 'og-sizes.txt').write_text('\n'.join(lines) + '\n')
for name in ('001.png', '004.png'):
    src = DIST / 'og' / name
    if src.exists():
        (review / f'og-{name[:3]}.png').write_bytes(src.read_bytes())
total = sum(f.stat().st_size for f in DIST.rglob('*') if f.is_file())
print(f'dist bytes {total}')
if total > 2_500_000:
    print('WARN dist over 2.5MB — switch to Workers Static Assets')
print('RESULT', 'PASS' if fail == 0 else f'FAIL ({fail})')
sys.exit(1 if fail else 0)
