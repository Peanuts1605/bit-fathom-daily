#!/usr/bin/env python3
"""Share-text contract: grid line, no answer or choice text, countdown running."""
import re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / 'index.html').as_uri()
CHROME = '/usr/bin/google-chrome'
fail = 0

def check(name, cond, detail=''):
    global fail
    fail += 0 if cond else 1
    print(('PASS ' if cond else 'FAIL ') + name + (f' ({detail})' if detail else ''))

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME if Path(CHROME).exists() else None)
    ctx = browser.new_context(viewport={'width': 1366, 'height': 900})
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_function('window.__BF && document.querySelectorAll("#choices button").length>0')
    info = page.evaluate('''() => {
      const s = window.__BF.getState();
      const r = window.__BF.rid(s.cur);
      return {answer: r.choices[r.answer_index], choices: r.choices, id: r.id, idx: r.answer_index};
    }''')
    page.locator('#choices button').nth(info['idx']).click()
    page.wait_for_function('() => !document.getElementById("reveal").hidden')
    page.locator('#share').click()
    page.wait_for_function("() => document.getElementById('shareMsg').textContent.includes('Copied')")
    text = page.evaluate('() => navigator.clipboard.readText()')
    live = page.evaluate('() => window.__BF.shareText()')
    check('clipboard matches shareText', text == live, text.replace('\n', ' | ')[:180])
    check('share header', bool(re.match(r'^Bit & Fathom Daily #\d{3}', text)), text.split('\n')[0])
    symbols = text.count('🟩') + text.count('🟥') + text.count('🟨') + text.count('📘') + text.count('⬜')
    check('at least 3 symbols', symbols >= 3, str(symbols))
    spoiled = [c for c in info['choices'] if c and c in text]
    check('no choice or answer text', not spoiled and info['answer'] not in text, str(spoiled))
    check('no option letters', not re.search(r'\b[A-D]\)', text))
    canon = 'https://bit-fathom-daily-next.gigantic-stranger.workers.dev'
    check('canonical share host', canon in text and '127.0.0.1' not in text and 'file://' not in text, text.split('\n')[-1])
    lab_today = page.locator('#label').inner_text()
    shared_no = re.search(r'Daily #(\d{3})', text)
    check('today shows the share number', bool(shared_no) and f'#{shared_no.group(1)}' in lab_today, lab_today.replace('\n', ' '))
    rise = page.locator('#rise').inner_text()
    check('streak label', 'day streak' in rise, rise)
    page.locator('#prev').click()
    lab = page.locator('#label').inner_text()
    num = page.evaluate('() => window.BFShare.pad(window.__BF.getState().cur + 1)')
    check('archive number matches puzzle number', f'#{num}' in lab, lab.replace('\n', ' '))
    plurals = page.evaluate('''() => ({
      oneMin: window.BFCount.liveText(60000),
      twoMin: window.BFCount.liveText(120000),
      oneHour: window.BFCount.liveText(3600000),
      both: window.BFCount.liveText(3660000),
      zero: window.BFCount.liveText(0),
      secs: window.BFCount.liveText(42000),
      oneSec: window.BFCount.liveText(1000)
    })''')
    check('1 minute', plurals['oneMin'] == 'Next riddle in 1 minute', plurals['oneMin'])
    check('2 minutes', plurals['twoMin'] == 'Next riddle in 2 minutes', plurals['twoMin'])
    check('1 hour', plurals['oneHour'] == 'Next riddle in 1 hour', plurals['oneHour'])
    check('1 hour and 1 minute', plurals['both'] == 'Next riddle in 1 hour and 1 minute', plurals['both'])
    check('last minute is not 0 minutes', plurals['zero'] == 'Next riddle in less than a minute' and '0 minutes' not in plurals['zero'], plurals['zero'])
    check('42 seconds', plurals['secs'] == 'Next riddle in 42 seconds', plurals['secs'])
    check('1 second', plurals['oneSec'] == 'Next riddle in 1 second', plurals['oneSec'])
    c1 = page.locator('#count').inner_text()
    page.wait_for_timeout(1100)
    c2 = page.locator('#count').inner_text()
    check('countdown decreases', c1 != c2 and c1 > c2, f'{c1} -> {c2}')
    browser.close()

print('RESULT', 'PASS' if fail == 0 else f'FAIL ({fail})')
sys.exit(1 if fail else 0)
