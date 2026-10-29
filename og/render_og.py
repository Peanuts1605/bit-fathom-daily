#!/usr/bin/env python3
"""Render 1200x630 og:image cards with Playwright (dpr 1) and quantize to <=150 KB.

Usage:
  python3 og/render_og.py            # write dist/og/*.png
  python3 og/render_og.py --check    # verify dims and size only
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
OG = DIST / 'og'
TPL = Path(__file__).with_name('template.html')
CHROME = '/usr/bin/google-chrome'
MAX_BYTES = 150 * 1024
# Puzzle numbers 001..MAX_PUZZLE (1-based day index from the Oct 12 2026 epoch).
# 018 is 2026-10-29. 042 keeps a few weeks of links without a huge worker bundle.
def max_puzzle():
    return int(os.environ.get('BF_OG_DAYS', '28'))

SCENES = ('space', 'ocean', 'lab')
POSES = ('bit-thinking.svg', 'bit-curious.svg', 'bit-surprised.svg', 'bit-happy.svg')


def load_meta():
    riddles = json.loads((ROOT / 'riddles.json').read_text())
    colors = json.loads((ROOT / 'assets' / 'backgrounds' / 'backgrounds.json').read_text())
    return riddles, colors


def card_for(n, riddles, colors):
    """n is 1-based puzzle number. None -> generic today card."""
    if n is None:
        scene = 'space'
        pose = 'bit-waving.svg'
        return {
            'kicker': "Today's riddle",
            'hook': "A new science riddle is waiting.",
            'scene': scene,
            'pose': pose,
            'colors': colors[scene],
            'file': 'today.png',
        }
    r = riddles[(n - 1) % len(riddles)]
    scene = SCENES[(n - 1) % len(SCENES)]
    pose = POSES[(n - 1) % len(POSES)]
    hook = (r.get('hook') or r['title']).strip()
    return {
        'kicker': f'Daily Riddle #{n:03d}',
        'hook': hook,
        'scene': scene,
        'pose': pose,
        'colors': colors[scene],
        'file': f'{n:03d}.png',
        'riddle': r,
    }


def render_html(card):
    """Relative URLs, so a file:// page can load kit fonts, backgrounds and Bit."""
    c = card['colors']
    dark = bool(c.get('dark'))
    if dark:
        s0, s1, s2 = 'rgba(7,21,38,.92)', 'rgba(7,21,38,.72)', 'rgba(7,21,38,.28)'
    else:
        s0, s1, s2 = 'rgba(244,252,252,.94)', 'rgba(244,252,252,.78)', 'rgba(244,252,252,.35)'
    def esc(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    html = TPL.read_text()
    # Card HTML is written to dist/og/_card.html, two levels below the repo root.
    mapping = {
        '%%FONT_DISPLAY%%': '../../assets/fonts/BricolageGrotesque-opsz-wdth-wght.ttf',
        '%%FONT_BODY%%': '../../assets/fonts/AtkinsonHyperlegibleNext-wght.ttf',
        '%%BG%%': f"../../assets/backgrounds/{card['scene']}-1200x675.png",
        '%%BIT%%': f"../../assets/characters/{card['pose']}",
        '%%SCRIM0%%': s0,
        '%%SCRIM1%%': s1,
        '%%SCRIM2%%': s2,
        '%%KICK_BG%%': c['kicker_bg'],
        '%%KICK_FG%%': c['kicker_fg'],
        '%%HOOK%%': c['hook'],
        '%%HANDLE%%': c['handle'],
        '%%KICKER%%': esc(card['kicker']),
        '%%HOOKTEXT%%': esc(card['hook']),
        '%%HANDLETEXT%%': '@RippleParade',
    }
    for k, v in sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True):
        html = html.replace(k, v)
    return html


def quantize(path: Path):
    """pngquant in place. Repeat at lower quality until <=150 KB or give up."""
    if path.stat().st_size <= MAX_BYTES:
        return
    if not shutil_which('pngquant'):
        return
    tmp = path.with_suffix('.q.png')
    for q in ('65-85', '50-70', '35-55', '20-40', '10-30'):
        r = subprocess.run(
            ['pngquant', '--quality', q, '--speed', '1', '--force', '--output', str(tmp), str(path)],
            capture_output=True)
        if r.returncode == 0 and tmp.exists():
            tmp.replace(path)
        if path.stat().st_size <= MAX_BYTES:
            return


def shutil_which(name):
    from shutil import which
    return which(name)


def render_all():
    from playwright.sync_api import sync_playwright
    riddles, colors = load_meta()
    OG.mkdir(parents=True, exist_ok=True)
    cards = [card_for(n, riddles, colors) for n in range(1, max_puzzle() + 1)]
    cards.append(card_for(None, riddles, colors))
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME if Path(CHROME).exists() else None)
        ctx = browser.new_context(viewport={'width': 1200, 'height': 630}, device_scale_factor=1)
        page = ctx.new_page()
        card_path = OG / '_card.html'
        try:
            for card in cards:
                card_path.write_text(render_html(card))
                page.goto(card_path.as_uri(), wait_until='load')
                page.wait_for_function('document.fonts.ready.then(()=>true)')
                page.wait_for_timeout(30)
                out = OG / card['file']
                page.screenshot(path=str(out), type='png', full_page=False)
                quantize(out)
                kb = out.stat().st_size / 1024
                print(f"og {card['file']} {kb:.1f} KB")
                if out.stat().st_size > MAX_BYTES:
                    raise SystemExit(f'FAIL og {card["file"]} is over 150 KB')
        finally:
            browser.close()
            card_path.unlink(missing_ok=True)
    return cards


def check():
    from PIL import Image
    fails = 0
    files = sorted(OG.glob('*.png'))
    if not files:
        print('FAIL no og pngs')
        return 1
    for f in files:
        im = Image.open(f)
        ok = im.size == (1200, 630) and f.stat().st_size <= MAX_BYTES
        print(('PASS' if ok else 'FAIL'), f.name, im.size, f'{f.stat().st_size}B')
        fails += not ok
    print('RESULT', 'PASS' if not fails else f'FAIL ({fails})')
    return 1 if fails else 0


if __name__ == '__main__':
    if '--check' in sys.argv:
        sys.exit(check())
    render_all()
