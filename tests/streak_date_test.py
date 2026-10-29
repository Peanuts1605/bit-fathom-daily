#!/usr/bin/env python3
"""Headless proofs for streak + local-date riddle mapping. Fakes Date via init script."""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = (Path(__file__).resolve().parent.parent/'index.html').as_uri()
CHROME = '/usr/bin/google-chrome'
fail = 0

def fake_date_script(y, m, d, H=12, M=0, S=0):
    # m is 1-based calendar month
    return f"""
    (() => {{
      const Real = Date;
      const fixed = new Real({y}, {m-1}, {d}, {H}, {M}, {S});
      class FakeDate extends Real {{
        constructor(...a) {{
          if (a.length === 0) super(fixed.getTime());
          else super(...a);
        }}
        static now() {{ return fixed.getTime(); }}
        static parse = Real.parse;
        static UTC = Real.UTC;
      }}
      FakeDate.prototype = Real.prototype;
      window.Date = FakeDate;
    }})();
    """

def open_page(p, y, m, d, storage=None):
    ctx = p.chromium.launch(executable_path=CHROME).new_context()
    # reuse browser across? simpler: one browser
    return ctx  # placeholder

def check(name, cond, detail=''):
    global fail
    if cond:
        print(f'PASS {name}' + (f' ({detail})' if detail else ''))
    else:
        fail += 1
        print(f'FAIL {name}' + (f' ({detail})' if detail else ''))

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME)

    def page_at(y, m, d, clear=True, seed=None):
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.add_init_script(fake_date_script(y, m, d))
        if clear:
            pg.add_init_script("localStorage.removeItem('bf-riddle-v1');")
        pg.goto(URL, wait_until='domcontentloaded')
        pg.wait_for_function('window.__BF && document.querySelectorAll("#choices button").length > 0')
        if seed is not None:
            pg.evaluate('(s) => { window.__BF.setState(s); window.__BF.remount(); }', seed)
            pg.wait_for_timeout(50)
        return ctx, pg

    # --- Date mapping: Oct 16 2026 local -> day 4 -> riddle 005 ---
    ctx, pg = page_at(2026, 10, 16)
    st = pg.evaluate('() => ({...window.__BF.getState(), id: window.__BF.rid(window.__BF.getState().today).id, title: document.getElementById("title").textContent, encore: !!document.querySelector(".encore"), day: window.__BF.dayNum(new Date())})')
    check('local dayNum Oct16', st['day'] == 4, str(st['day']))
    check('today riddle 005', st['id'] == '005', st['id'])
    check('no encore on day 4', st['encore'] is False)
    ctx.close()

    # --- DST-ish: late evening local still same calendar day ---
    ctx, pg = page_at(2026, 10, 16)
    # override to 23:30
    pg.evaluate('''() => {
      const Real = Date;
      const fixed = new Real(2026, 9, 16, 23, 30, 0);
      class FakeDate extends Real {
        constructor(...a){ if(a.length===0) super(fixed.getTime()); else super(...a); }
        static now(){ return fixed.getTime(); }
        static parse = Real.parse; static UTC = Real.UTC;
      }
      window.Date = FakeDate;
      // recompute via remount using existing helpers that call new Date()
      // force today recalc by reload with init — instead call dayNum
    }''')
    day_late = pg.evaluate('() => window.__BF.dayNum(new Date(2026, 9, 16, 23, 30, 0))')
    day_early = pg.evaluate('() => window.__BF.dayNum(new Date(2026, 9, 16, 0, 5, 0))')
    check('same local calendar day morning/night', day_late == day_early == 4, f'{day_early}/{day_late}')
    ctx.close()

    # --- Encore on day 14 (0-based: day 14 = 15th day = first loop of 001) ---
    ctx, pg = page_at(2026, 10, 26)  # epoch Oct12 + 14 days = Oct26
    st = pg.evaluate('() => ({day: window.__BF.dayNum(new Date()), id: window.__BF.rid(window.__BF.getState().today).id, encore: !!document.querySelector(".encore"), label: document.getElementById("label").textContent})')
    check('day 14 maps to 001', st['id'] == '001' and st['day'] == 14, str(st))
    check('Encore label on day 14+', st['encore'] is True and 'Encore' in st['label'], st['label'])
    ctx.close()

    # day 15 -> 002 encore
    ctx, pg = page_at(2026, 10, 27)
    st = pg.evaluate('() => ({day: window.__BF.dayNum(new Date()), id: window.__BF.rid(window.__BF.getState().today).id, encore: !!document.querySelector(".encore")})')
    check('day 15 maps to 002 + encore', st['day'] == 15 and st['id'] == '002' and st['encore'], str(st))
    ctx.close()

    # --- Streak: wrong answer still counts as played (kid-friendly), +1 once ---
    ctx, pg = page_at(2026, 10, 16)
    # Misses allowed = choices.length-1. Exhaust them so the riddle resolves as "learned".
    ans = pg.evaluate('() => window.__BF.rid(window.__BF.getState().today).answer_index')
    nbtn = pg.evaluate('() => document.querySelectorAll("#choices button").length')
    for i in range(nbtn):
        if i == ans:
            continue
        pg.click(f'#choices button:nth-child({i+1})')
        pg.wait_for_timeout(80)
    st = pg.evaluate('() => window.__BF.getState()')
    check('wrong answer sets streak to 1', st['streak'] == 1, str(st))
    check('wrong marked on UI', pg.evaluate('() => !!document.querySelector(".choices button.wrong")'))
    check('right highlighted with class', pg.evaluate('() => !!document.querySelector(".choices button.right")'))
    verdict = pg.inner_text('#verdict')
    check('wrong-answer feedback text', 'Nice try' in verdict, verdict[:80])
    # Persist across a fresh load (no clear) — same origin storage
    raw = pg.evaluate("() => localStorage.getItem('bf-riddle-v1')")
    check('localStorage written after play', bool(raw) and '"streak":1' in raw, str(raw)[:120])
    ctx2 = browser.new_context()
    pg2 = ctx2.new_page()
    pg2.add_init_script(fake_date_script(2026, 10, 16))
    pg2.add_init_script(f"localStorage.setItem('bf-riddle-v1', {raw!r});")
    pg2.goto(URL, wait_until='domcontentloaded')
    pg2.wait_for_function('window.__BF && document.querySelectorAll("#choices button").length > 0')
    st2 = pg2.evaluate('() => window.__BF.getState()')
    check('reload keeps streak 1', st2['streak'] == 1 and st2['last'] == '2026-10-16', str(st2))
    ctx2.close()
    ctx.close()

    # --- Consecutive day: yesterday played -> streak becomes 2 ---
    ctx, pg = page_at(2026, 10, 17, seed={
        'streak': 1, 'best': 1, 'last': '2026-10-16', 'ans': {'2026-10-16': 0}
    })
    st = pg.evaluate('() => window.__BF.getState()')
    check('visit next day keeps streak until play', st['streak'] == 1, str(st))
    ans = pg.evaluate('() => window.__BF.rid(window.__BF.getState().today).answer_index')
    wrong = 0 if ans != 0 else 1
    pg.click(f'#choices button:nth-child({wrong+1})')
    pg.wait_for_timeout(200)
    st = pg.evaluate('() => window.__BF.getState()')
    check('next-day play increments to 2 (even if wrong)', st['streak'] == 2, str(st))
    ctx.close()

    # --- Skip a day resets on visit ---
    ctx, pg = page_at(2026, 10, 18, seed={
        'streak': 5, 'best': 5, 'last': '2026-10-16', 'ans': {'2026-10-16': 0}
    })
    # Oct 18 visit, last was Oct 16 -> gap -> streak 0
    st = pg.evaluate('() => window.__BF.getState()')
    check('skip day resets streak to 0 on visit', st['streak'] == 0, str(st))
    check('best preserved after skip reset', st['best'] == 5, str(st))
    ans = pg.evaluate('() => window.__BF.rid(window.__BF.getState().today).answer_index')
    wrong = 0 if ans != 0 else 1
    pg.click(f'#choices button:nth-child({wrong+1})')
    pg.wait_for_timeout(200)
    st = pg.evaluate('() => window.__BF.getState()')
    check('play after skip starts streak at 1', st['streak'] == 1, str(st))
    ctx.close()

    # --- Archive never changes streak ---
    ctx, pg = page_at(2026, 10, 16, seed={
        'streak': 3, 'best': 3, 'last': '2026-10-16', 'ans': {'2026-10-16': 1}
    })
    # today already answered; go prev and answer archive
    pg.click('#prev')
    pg.wait_for_timeout(100)
    # ensure choices enabled (archive unanswered)
    enabled = pg.evaluate('() => [...document.querySelectorAll("#choices button")].some(b => !b.disabled)')
    if enabled:
        before = pg.evaluate('() => window.__BF.getState().streak')
        pg.click('#choices button:nth-child(1)')
        pg.wait_for_timeout(200)
        after = pg.evaluate('() => window.__BF.getState().streak')
        check('archive answer does not change streak', before == after == 3, f'{before}->{after}')
    else:
        # already had archive ans somehow
        check('archive choices available', False, 'disabled')
    ctx.close()

    # --- Only one increment per day even if we tried to re-guess ---
    ctx, pg = page_at(2026, 10, 16)
    ans = pg.evaluate('() => window.__BF.rid(window.__BF.getState().today).answer_index')
    # first wrong
    wrong = 0 if ans != 0 else 1
    pg.click(f'#choices button:nth-child({wrong+1})')
    pg.wait_for_timeout(150)
    s1 = pg.evaluate('() => window.__BF.getState().streak')
    # try programmatic second guess same day
    pg.evaluate('() => { try { document.querySelectorAll("#choices button")[0].click() } catch(e) {} }')
    s2 = pg.evaluate('() => window.__BF.getState().streak')
    check('one increment per day', s1 == s2 == 1, f'{s1}/{s2}')
    ctx.close()

    # --- Correct answer also increments (parity with wrong) ---
    ctx, pg = page_at(2026, 10, 16)
    ans = pg.evaluate('() => window.__BF.rid(window.__BF.getState().today).answer_index')
    pg.click(f'#choices button:nth-child({ans+1})')
    pg.wait_for_timeout(150)
    st = pg.evaluate('() => window.__BF.getState()')
    check('correct answer also sets streak 1', st['streak'] == 1, str(st))
    check('no wrong class on correct', pg.evaluate('() => !document.querySelector(".choices button.wrong")'))
    ctx.close()

    browser.close()

print('RESULT', 'PASS' if fail == 0 else f'FAIL ({fail})')
sys.exit(0 if fail == 0 else 1)
