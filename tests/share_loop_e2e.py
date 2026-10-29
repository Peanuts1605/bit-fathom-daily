#!/usr/bin/env python3
"""Share-loop Playwright E2E.

Desktop 1366×900, mobile 390×844 (dpr 2, touch), and reduced motion.
Serves dist/ over http. Writes review/share-loop screenshots and clips.
"""
import functools, http.server, json, re, shutil, subprocess, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
REVIEW = ROOT / 'review' / 'share-loop'
CHROME = '/usr/bin/google-chrome'
READY = 'window.__BF && document.querySelectorAll("#choices button").length>0'
SHARE_RE = re.compile(r'^Bit & Fathom Daily #\d{3}')
fail = 0

_srv = http.server.ThreadingHTTPServer(
    ('127.0.0.1', 0),
    functools.partial(
        type('Q', (http.server.SimpleHTTPRequestHandler,), {'log_message': lambda *a: None}),
        directory=str(DIST),
    ),
)
threading.Thread(target=_srv.serve_forever, daemon=True).start()
ORIGIN = f'http://127.0.0.1:{_srv.server_address[1]}'
URL = ORIGIN + '/'


def check(name, cond, detail=''):
    global fail
    fail += 0 if cond else 1
    line = ('PASS ' if cond else 'FAIL ') + name
    if detail:
        line += f' ({detail})'
    print(line)


def fake(y, m, d, H=12):
    return f"""(()=>{{const R=Date;const t0=new R({y},{m-1},{d},{H},0,0).getTime(),r0=R.now();
    const now=()=>t0+(R.now()-r0);
    class F extends R{{constructor(...a){{a.length?super(...a):super(now())}}static now(){{return now()}}}};F.parse=R.parse;F.UTC=R.UTC;window.Date=F}})();"""


def seed_items(pairs):
    body = ''.join(
        f"localStorage.setItem({json.dumps(k)}, {json.dumps(v)});" for k, v in pairs.items()
    )
    return '(()=>{ ' + body + ' })();'


SHARE_STUB = """() => {
  try {
    Object.defineProperty(navigator, 'share', {
      configurable: true,
      writable: true,
      value: function(){ return Promise.resolve(); }
    });
  } catch (e) {}
}"""


def launch_kwargs():
    return {'executable_path': CHROME} if Path(CHROME).exists() else {}


def metrics(page):
    return page.evaluate('''() => {
      const h1 = document.querySelector('h1');
      const hs = getComputedStyle(h1);
      const fam = hs.fontFamily.replace(/["']/g, '');
      const body = getComputedStyle(document.body).fontFamily.replace(/["']/g, '');
      const q = document.getElementById('question');
      const buttons = [...document.querySelectorAll('#choices button')];
      const last = buttons.length ? buttons[buttons.length-1].getBoundingClientRect() : null;
      const bit = document.getElementById('bit').getBoundingClientRect();
      const card = document.querySelector('.cardface').getBoundingClientRect();
      const play = document.querySelector('.play').getBoundingClientRect();
      const nav = document.querySelector('nav').getBoundingClientRect();
      const doc = document.documentElement;
      const bad = [];
      document.querySelectorAll('button, a, summary, input, [role="button"]').forEach(el => {
        if (el.closest('[hidden]')) return;
        const s = getComputedStyle(el);
        if (s.display === 'none' || s.visibility === 'hidden') return;
        const r = el.getBoundingClientRect();
        if (r.width < 1 && r.height < 1) return;
        if (r.width < 44 || r.height < 44) {
          bad.push((el.id || el.tagName) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
        }
      });
      return {
        hook: h1.textContent.trim(),
        words: h1.textContent.trim().split(/\\s+/).filter(Boolean).length,
        font: fam,
        body: body,
        brico: document.fonts.check('16px "Bricolage Grotesque"'),
        atk: document.fonts.check('16px "Atkinson Hyperlegible Next"'),
        qSize: parseFloat(getComputedStyle(q).fontSize),
        qTop: q.getBoundingClientRect().top,
        nChoices: buttons.length,
        lastBottom: last ? last.bottom : 9999,
        lastTop: last ? last.top : -1,
        vh: innerHeight,
        vw: innerWidth,
        navTop: nav.top,
        bitW: bit.width,
        bitTop: bit.top,
        bitBottom: bit.bottom,
        cardW: card.width,
        playW: play.width,
        hScroll: doc.scrollWidth > doc.clientWidth + 1,
        bad44: bad,
        scrollY: scrollY
      };
    }''')


def riddle_info(page):
    return page.evaluate('''() => {
      const s = window.__BF.getState();
      const r = window.__BF.rid(s.cur);
      return {choices: r.choices, answer: r.choices[r.answer_index], idx: r.answer_index, hook: r.hook};
    }''')


def open_ready(page):
    page.goto(URL)
    page.wait_for_function(READY)
    page.evaluate('() => document.fonts.ready')


def wrong_index(info):
    for i, _c in enumerate(info['choices']):
        if i != info['idx']:
            return i
    return 0


def play_wrong_then_right(page, info):
    w = wrong_index(info)
    page.locator('#choices button').nth(w).click()
    page.wait_for_function('() => !document.getElementById("whynot").hidden')
    struck = page.evaluate('''(i) => {
      const b = document.querySelectorAll('#choices button')[i];
      const td = getComputedStyle(b).textDecorationLine;
      return b.classList.contains('wrong') && (td.includes('line-through') || b.style.textDecoration.includes('line'));
    }''', w)
    check('wrong strike and why-not', struck and page.locator('#whynot').inner_text().strip() != '')
    page.locator('#choices button').nth(info['idx']).click()
    page.wait_for_function('() => !document.getElementById("reveal").hidden')
    src = page.locator('#bit').get_attribute('src') or ''
    check('bit happy after correct', 'bit-happy' in src, src)
    check('bit line present', len(page.locator('#bitLine').inner_text().strip()) > 8)


def assert_share(page, info):
    page.locator('#share').click()
    page.wait_for_function("() => document.getElementById('shareMsg').textContent.includes('Copied')")
    text = page.evaluate('() => navigator.clipboard.readText()')
    live = page.evaluate('() => window.__BF.shareText()')
    check('clipboard matches shareText', text == live, (text or '')[:160].replace('\n', ' | '))
    check('share header', bool(text and SHARE_RE.match(text)), (text or '').split('\n')[0])
    symbols = sum(text.count(ch) for ch in '🟩🟥🟨📘⬜') if text else 0
    check('share has >=3 symbols', symbols >= 3, str(symbols))
    spoiled = [c for c in info['choices'] if c and c in (text or '')]
    check('share hides choices and answer', not spoiled and info['answer'] not in (text or ''), str(spoiled))
    check('share has no option letters', not re.search(r'\b[A-D]\)', text or ''))


def assert_countdown(page):
    c1 = page.locator('#count').inner_text().strip()
    page.wait_for_timeout(1100)
    c2 = page.locator('#count').inner_text().strip()
    check('countdown running', bool(re.match(r'\d{2}:\d{2}:\d{2}', c1)) and c1 != c2 and c1 > c2, f'{c1} -> {c2}')


def assert_layout(page, tag, phone):
    page.evaluate('() => document.fonts.ready')
    m = metrics(page)
    check(f'{tag} hook <=12 words', 1 <= m['words'] <= 12 and '?' in m['hook'], m['hook'])
    check(f'{tag} brand font', m['font'].startswith('Bricolage') and m['brico'], m['font'])
    check(f'{tag} body font', 'Atkinson' in m['body'] and m['atk'], m['body'])
    check(f'{tag} question >=21px', m['qSize'] >= 21, str(m['qSize']))
    check(f'{tag} one button per choice', m['nChoices'] >= 3, str(m['nChoices']))
    check(f'{tag} no h-scroll', not m['hScroll'])
    check(f'{tag} 44px targets', m['bad44'] == [], ', '.join(m['bad44'][:8]))
    check(f'{tag} bit >=40% card', m['cardW'] > 0 and m['bitW'] / m['cardW'] >= 0.40, f"{m['bitW']:.0f}/{m['cardW']:.0f}")
    check(f'{tag} bit above fold', m['bitTop'] >= -1 and m['bitBottom'] <= m['vh'] + 1, f"{m['bitTop']:.0f}-{m['bitBottom']:.0f}")
    wide = m['playW'] / m['vw'] >= 0.60
    check(f'{tag} play area >=60% width', wide, f"{m['playW']:.0f}/{m['vw']}")
    if phone:
        fit = m['scrollY'] == 0 and m['lastTop'] >= 0 and m['lastBottom'] <= m['navTop'] + 1 and m['lastBottom'] <= m['vh']
        check(f'{tag} options fit above nav', fit, f"bottom {m['lastBottom']:.0f} nav {m['navTop']:.0f} vh {m['vh']}")
    else:
        fit = m['lastTop'] >= 0 and m['lastBottom'] <= m['vh'] and m['scrollY'] == 0
        check(f'{tag} options visible without scroll', fit, f"bottom {m['lastBottom']:.0f} vh {m['vh']}")
    return m


def shot(page, name):
    REVIEW.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(REVIEW / name))


def gameplay(browser, tag, ctx_kwargs, shots, reduced=False):
    ctx = browser.new_context(**ctx_kwargs)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    if tag == 'mobile':
        ctx.add_init_script(SHARE_STUB)
    page = ctx.new_page()
    open_ready(page)
    audio = page.evaluate('() => window.juice && window.juice._audio === false')
    check(f'{tag} no audio before gesture', audio)
    info = riddle_info(page)
    check(f'{tag} hook matches riddle', page.locator('#title').inner_text().strip() == (info['hook'] or '').strip(), info['hook'])
    assert_layout(page, tag, phone=(tag == 'mobile'))
    if shots:
        shot(page, f'{tag}-first.png')
    play_wrong_then_right(page, info)
    if reduced:
        confetti = page.locator('.juice-confetti').count()
        shake = page.evaluate('''() => [...document.querySelectorAll('#choices button')].some(b => b.classList.contains('juice-shake'))''')
        check(f'{tag} no confetti', confetti == 0, str(confetti))
        check(f'{tag} no shake motion', not shake)
        shot(page, 'reduced-result.png')
    if shots and not reduced:
        page.wait_for_timeout(500)
        page.locator('#reveal').screenshot(path=str(REVIEW / f'{tag}-share.png'))
        page.locator('#count').scroll_into_view_if_needed()
        shot(page, f'{tag}-countdown.png')
    assert_share(page, info)
    assert_countdown(page)
    page.locator('#soundBtn').click()
    page.wait_for_function("() => document.getElementById('soundBtn').getAttribute('aria-pressed')==='false'")
    page.reload()
    page.wait_for_function(READY)
    pressed = page.locator('#soundBtn').get_attribute('aria-pressed')
    disk = page.evaluate("() => JSON.parse(localStorage.getItem('bf-riddle-v2')||'{}')")
    check(f'{tag} sound persists off', pressed == 'false' and disk.get('sound') is False, pressed)
    check(f'{tag} still no audio before gesture', page.evaluate('() => window.juice._audio === false'))
    ctx.close()


def migration(browser, tag, ctx_kwargs):
    v1 = json.dumps({'streak': 2, 'best': 2, 'last': '2026-10-15', 'ans': {'2026-10-15': 0}})
    app = json.dumps({'h': {'2026-10-14': {'id': 3, 'g': 1, 'ok': True}}, 'sound': False, 'best': 9})
    ctx = browser.new_context(**ctx_kwargs)
    ctx.add_init_script(fake(2026, 10, 16))
    ctx.add_init_script(seed_items({'bf-riddle-v1': v1, 'bfdr.v1': app}))
    page = ctx.new_page()
    open_ready(page)
    st = page.evaluate('() => window.__BF.getState()')
    ans = st.get('ans') or {}
    check(f'{tag} migrate both days', '2026-10-14' in ans and '2026-10-15' in ans, str(sorted(ans)))
    check(f'{tag} migrate best', st.get('best', 0) >= 9, str(st.get('best')))
    check(f'{tag} migrate sound off', page.locator('#soundBtn').inner_text().strip() == '🔇')
    check(f'{tag} old keys kept', page.evaluate('''() => !!(localStorage.getItem('bf-riddle-v1') && localStorage.getItem('bfdr.v1'))'''))
    page.evaluate('() => window.__BF.setState({})')
    v2 = page.evaluate("() => JSON.parse(localStorage.getItem('bf-riddle-v2'))")
    plays = (v2 or {}).get('plays') or {}
    check(f'{tag} v2 plays written', '2026-10-14' in plays and '2026-10-15' in plays and v2.get('sound') is False and v2.get('best', 0) >= 9)
    page.reload()
    page.wait_for_function(READY)
    st2 = page.evaluate('() => window.__BF.getState()')
    v2b = page.evaluate("() => JSON.parse(localStorage.getItem('bf-riddle-v2'))")
    same = sorted((st2.get('ans') or {})) == sorted(ans) and st2.get('best') == st.get('best') and (v2b or {}).get('sound') is False
    check(f'{tag} migration idempotent', same and page.locator('#soundBtn').inner_text().strip() == '🔇', str(st2.get('best')))
    check(f'{tag} old keys survive reload', page.evaluate('''() => !!(localStorage.getItem('bf-riddle-v1') && localStorage.getItem('bfdr.v1'))'''))
    ctx.close()


def scripted_stats(browser, tag, ctx_kwargs, shots):
    ctx = browser.new_context(**ctx_kwargs)
    ctx.add_init_script(fake(2026, 10, 16))
    page = ctx.new_page()
    open_ready(page)

    def play():
        idx = page.evaluate('() => window.__BF.rid(window.__BF.getState().today).answer_index')
        page.locator('#choices button').nth(idx).click()
        page.wait_for_function('() => !document.getElementById("reveal").hidden')

    play()
    s1 = page.evaluate('() => window.__BF.getState().streak')
    check(f'{tag} day1 streak 1', s1 == 1, str(s1))
    saved = page.evaluate('''() => ({
      'bf-riddle-v1': localStorage.getItem('bf-riddle-v1'),
      'bf-riddle-v2': localStorage.getItem('bf-riddle-v2')
    })''')
    ctx.close()

    ctx = browser.new_context(**ctx_kwargs)
    ctx.add_init_script(fake(2026, 10, 17))
    ctx.add_init_script(seed_items(saved))
    page = ctx.new_page()
    open_ready(page)
    play()
    s2 = page.evaluate('() => window.__BF.getState().streak')
    check(f'{tag} +1 day streak 2', s2 == 2, str(s2))
    saved = page.evaluate('''() => ({
      'bf-riddle-v1': localStorage.getItem('bf-riddle-v1'),
      'bf-riddle-v2': localStorage.getItem('bf-riddle-v2')
    })''')
    ctx.close()

    ctx = browser.new_context(**ctx_kwargs)
    ctx.add_init_script(fake(2026, 10, 19))
    ctx.add_init_script(seed_items(saved))
    page = ctx.new_page()
    open_ready(page)
    shown = page.locator('#streak').inner_text().strip()
    check(f'{tag} +2 days resets before play', shown == '0', shown)
    play()
    s3 = page.evaluate('() => window.__BF.getState().streak')
    check(f'{tag} play after gap streak 1', s3 == 1, str(s3))
    page.locator('#statsBtn').click()
    page.wait_for_function('() => !document.getElementById("statsModal").hidden')
    played = page.locator('#mPlayed').inner_text().strip()
    pct = page.locator('#mPct').inner_text().strip()
    today_bar = page.locator('.bar.is-today').count()
    check(f'{tag} stats played', played == '3', played)
    check(f'{tag} stats win pct', pct == '100%', pct)
    check(f'{tag} today bar highlighted', today_bar == 1, str(today_bar))
    if shots:
        page.locator('#statsModal .sheet').screenshot(path=str(REVIEW / f'{tag}-stats.png'))
    page.keyboard.press('Escape')
    page.wait_for_function('() => document.getElementById("statsModal").hidden')
    focused = page.evaluate('() => document.activeElement && document.activeElement.id')
    check(f'{tag} stats escape restores focus', focused == 'statsBtn', focused)
    ctx.close()


def hscroll_320(browser):
    ctx = browser.new_context(viewport={'width': 320, 'height': 700})
    page = ctx.new_page()
    open_ready(page)
    wide = page.evaluate('''() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1''')
    check('320 no h-scroll', not wide)
    ctx.close()


def record_clip(browser, name, wrong):
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
    open_ready(page)
    info = riddle_info(page)
    if wrong:
        page.locator('#choices button').nth(wrong_index(info)).click()
        page.wait_for_function('() => !document.getElementById("whynot").hidden')
    else:
        page.locator('#choices button').nth(info['idx']).click()
        page.wait_for_function('() => !document.getElementById("reveal").hidden')
    page.wait_for_timeout(1600)
    video = page.video
    ctx.close()
    raw = REVIEW / f'{name}-raw.webm'
    video.save_as(str(raw))
    dest = REVIEW / f'{name}.webm'
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        subprocess.run(
            [ffmpeg, '-y', '-sseof', '-5', '-i', str(raw), '-c', 'copy', str(dest)],
            check=False, capture_output=True,
        )
        if not dest.exists() or dest.stat().st_size < 1000:
            shutil.copy(raw, dest)
    else:
        shutil.copy(raw, dest)
    raw.unlink(missing_ok=True)
    shutil.rmtree(tmp, ignore_errors=True)
    check(f'clip {name}', dest.exists() and dest.stat().st_size > 1000, str(dest.stat().st_size if dest.exists() else 0))


def og_http():
    import urllib.request
    home = urllib.request.urlopen(URL, timeout=10).read().decode()
    check('home og tags', 'og:image' in home and 'summary_large_image' in home and '1200' in home)
    pages = sorted((DIST / 'r').glob('*/index.html'))
    check('riddle pages', len(pages) >= 15, str(len(pages)))
    bad = []
    for page in pages:
        html = page.read_text()
        if 'og:image' not in html or 'summary_large_image' not in html or '1200' not in html:
            bad.append(page.parent.name)
    check('every /r/NNN/ og meta', not bad, ','.join(bad[:8]))
    pngs = [p for p in (DIST / 'og').glob('*.png')]
    check('og pngs present', len(pngs) >= 15, str(len(pngs)))


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    desktop = {'viewport': {'width': 1366, 'height': 900}}
    mobile = {
        'viewport': {'width': 390, 'height': 844},
        'device_scale_factor': 2,
        'has_touch': True,
        'is_mobile': True,
    }
    reduced = {'viewport': {'width': 1366, 'height': 900}, 'reduced_motion': 'reduce'}
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs())
        gameplay(browser, 'desktop', desktop, shots=True)
        gameplay(browser, 'mobile', mobile, shots=True)
        # Reduced-motion wrong frame, then the shared gameplay path finishes the riddle.
        ctx = browser.new_context(**reduced)
        page = ctx.new_page()
        open_ready(page)
        info = riddle_info(page)
        page.locator('#choices button').nth(wrong_index(info)).click()
        page.wait_for_function('() => !document.getElementById("whynot").hidden')
        shot(page, 'reduced-wrong.png')
        ctx.close()
        gameplay(browser, 'reduced', reduced, shots=False, reduced=True)
        migration(browser, 'desktop', desktop)
        migration(browser, 'mobile', mobile)
        migration(browser, 'reduced', reduced)
        scripted_stats(browser, 'desktop', desktop, shots=True)
        scripted_stats(browser, 'mobile', mobile, shots=True)
        scripted_stats(browser, 'reduced', reduced, shots=False)
        hscroll_320(browser)
        record_clip(browser, 'wrong', True)
        record_clip(browser, 'right', False)
        browser.close()
    og_http()
    print('RESULT', 'PASS' if fail == 0 else f'FAIL ({fail})')
    raise SystemExit(1 if fail else 0)


if __name__ == '__main__':
    main()
