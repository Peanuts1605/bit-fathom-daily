#!/usr/bin/env python3
"""Share-loop Playwright E2E.

Desktop 1366×900, mobile 390×844 (dpr 2, touch), and reduced motion.
Serves dist/ over http. Screenshots and clips go to a temp dir (or BF_SHOT_DIR),
never to review/share-loop/.
"""
import functools, http.server, json, os, re, shutil, subprocess, tempfile, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
SHOTS = Path(os.environ['BF_SHOT_DIR']) if os.environ.get('BF_SHOT_DIR') else Path(tempfile.mkdtemp(prefix='bf-e2e-'))
CHROME = '/usr/bin/google-chrome'
READY = 'window.__BF && document.querySelectorAll("#choices button").length>0'
SHARE_RE = re.compile(r'^Bit & Fathom Daily #\d{3}')
CANON = 'https://bit-fathom-daily-next.gigantic-stranger.workers.dev'
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
        bitH: bit.height,
        bitTop: bit.top,
        bitBottom: bit.bottom,
        objectFit: getComputedStyle(document.getElementById('bit')).objectFit,
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
    check('share uses canonical origin', CANON in (text or '') and '127.0.0.1' not in (text or '') and 'capacitor://' not in (text or ''))
    rise = page.locator('#rise').inner_text()
    check('streak count-up is labeled', 'day streak' in rise, rise)


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
    ratio = (m['bitH'] / m['bitW']) if m['bitW'] else 0
    check(f'{tag} bit not cropped', m['objectFit'] == 'contain' and 0.9 <= ratio <= 1.35, f"fit {m['objectFit']} ratio {ratio:.2f}")
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
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / name))


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
        page.locator('#reveal').screenshot(path=str(SHOTS / f'{tag}-share.png'))
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
        page.locator('#statsModal .sheet').screenshot(path=str(SHOTS / f'{tag}-stats.png'))
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
    tmp = SHOTS / '_video'
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
    raw = SHOTS / f'{name}-raw.webm'
    video.save_as(str(raw))
    dest = SHOTS / f'{name}.webm'
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
    check('home og tags', 'og:image' in home and 'og:url' in home and 'summary_large_image' in home and '1200' in home)
    check('page 029', (DIST / 'r' / '029' / 'index.html').is_file())
    check('page 112', (DIST / 'r' / '112' / 'index.html').is_file())


def focus_share(browser, width, height):
    ctx = browser.new_context(viewport={'width': width, 'height': height})
    page = ctx.new_page()
    open_ready(page)
    info = riddle_info(page)
    page.locator('#choices button').nth(info['idx']).click()
    page.wait_for_function('() => !document.getElementById("reveal").hidden')
    page.evaluate('() => window.scrollTo(0, 0)')
    page.locator('#share').focus()
    box = page.evaluate('''() => {
      const b = document.getElementById('share').getBoundingClientRect();
      const nav = document.querySelector('nav').getBoundingClientRect();
      return {top: b.top, bottom: b.bottom, navTop: nav.top, vh: innerHeight};
    }''')
    clear = box['top'] >= -1 and box['bottom'] <= box['navTop'] + 1
    check(
        f'focus share {width}x{height} clears tab bar',
        clear,
        f"top {box['top']:.0f} bottom {box['bottom']:.0f} nav {box['navTop']:.0f}",
    )
    ctx.close()


def band_999(browser):
    ctx = browser.new_context(viewport={'width': 999, 'height': 900})
    page = ctx.new_page()
    open_ready(page)
    m = metrics(page)
    q_top = m['qTop']
    fit = (
        m['nChoices'] >= 4
        and m['scrollY'] == 0
        and q_top >= 0
        and m['lastTop'] >= 0
        and m['lastBottom'] <= m['navTop'] + 1
    )
    check(
        '999x900 question and options above nav',
        fit,
        f"n {m['nChoices']} q {q_top:.0f} bottom {m['lastBottom']:.0f} nav {m['navTop']:.0f}",
    )
    ctx.close()


def bit_head_after_answer(browser, width, height):
    ctx = browser.new_context(viewport={'width': width, 'height': height})
    page = ctx.new_page()
    open_ready(page)
    info = riddle_info(page)
    page.locator('#choices button').nth(info['idx']).click()
    page.wait_for_function('() => !document.getElementById("reveal").hidden')
    if width >= 1000:
        page.evaluate('() => window.scrollTo(0, 500)')
        page.wait_for_function('() => window.scrollY >= 500')
    box = page.evaluate('''() => {
      const bit = document.getElementById('bit').getBoundingClientRect();
      return {top: bit.top, height: bit.height, head: bit.top + bit.height * 0.32, vh: innerHeight, y: window.scrollY};
    }''')
    head_in_view = box['top'] >= -1 and box['top'] < box['vh'] * 0.45 and 0 <= box['head'] <= box['vh'] - 8
    if width >= 1000:
        head_in_view = head_in_view and box['y'] >= 500
    check(
        f'{width}x{height} bit head stays in view after answer',
        head_in_view,
        f"top {box['top']:.0f} head {box['head']:.0f} y {box['y']:.0f} vh {box['vh']}",
    )
    ctx.close()


def desktop_1024(browser):
    ctx = browser.new_context(viewport={'width': 1024, 'height': 768})
    page = ctx.new_page()
    open_ready(page)
    m = metrics(page)
    fit = (
        m['nChoices'] >= 4
        and m['scrollY'] == 0
        and m['lastTop'] >= 0
        and m['lastBottom'] <= m['navTop'] + 1
    )
    check(
        '1024x768 last option clears nav',
        fit,
        f"n {m['nChoices']} bottom {m['lastBottom']:.0f} nav {m['navTop']:.0f}",
    )
    ctx.close()


def short_phone(browser):
    ctx = browser.new_context(
        viewport={'width': 375, 'height': 667},
        device_scale_factor=2,
        has_touch=True,
        is_mobile=True,
    )
    page = ctx.new_page()
    open_ready(page)
    m = metrics(page)
    fit = m['nChoices'] >= 4 and m['scrollY'] == 0 and m['lastTop'] >= 0 and m['lastBottom'] <= m['navTop'] + 1
    check('375x667 all options visible', fit, f"n {m['nChoices']} bottom {m['lastBottom']:.0f} nav {m['navTop']:.0f} y {m['scrollY']}")
    ctx.close()


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    print('e2e shots', SHOTS)
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
        short_phone(browser)
        band_999(browser)
        desktop_1024(browser)
        bit_head_after_answer(browser, 1366, 900)
        bit_head_after_answer(browser, 1366, 768)
        bit_head_after_answer(browser, 1024, 768)
        focus_share(browser, 320, 700)
        focus_share(browser, 375, 667)
        focus_share(browser, 768, 1024)
        record_clip(browser, 'wrong', True)
        record_clip(browser, 'right', False)
        browser.close()
    og_http()
    print('RESULT', 'PASS' if fail == 0 else f'FAIL ({fail})')
    raise SystemExit(1 if fail else 0)


if __name__ == '__main__':
    main()
