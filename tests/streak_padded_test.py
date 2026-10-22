#!/usr/bin/env python3
"""Lens F3 (2026-10-22): the streak must treat padded ('2027-03-12') and unpadded ('2027-3-12') saved dates as the same day.
Seeds localStorage bf-riddle-v1, fixes the clock (America/New_York), answers today's riddle, reads the saved streak.
Usage: $PYTHON tests/streak_padded_test.py [index.html] [--expect-old-bug]   exit 1 on FAIL. (Run by check.sh.)"""
import sys, json, pathlib, datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
_a = [x for x in sys.argv[1:] if not x.startswith('--')]
f = pathlib.Path(_a[0] if _a else pathlib.Path(__file__).resolve().parent.parent/'index.html').resolve(); URL = f.as_uri(); OLD = '--expect-old-bug' in sys.argv
NY = ZoneInfo('America/New_York')
# (name, clock (y,m,d,H,M), seeded last, seeded streak, expected streak after answering today)
CASES = [
 ('padded yesterday -> +1 (Lens S8 repro)', (2027,3,13,12,0), '2027-03-12', 4, 5),
 ('unpadded yesterday -> +1',               (2027,3,13,12,0), '2027-3-12',  4, 5),
 ('padded yesterday across DST end -> +1',  (2026,11,2,12,0), '2026-11-01', 6, 7),
 ('padded single-digit both parts -> +1',   (2027,1,2,9,0),   '2027-01-01', 2, 3),
 ('padded today -> unchanged',              (2027,3,13,12,0), '2027-03-13', 4, 4),
 ('unpadded today -> unchanged',            (2027,3,13,12,0), '2027-3-13',  4, 4),
 ('gap, padded (2 days ago) -> 1',          (2027,3,13,12,0), '2027-03-11', 4, 1),
 ('gap, unpadded (2 days ago) -> 1',        (2027,3,13,12,0), '2027-3-11',  4, 1),
 ('garbage last -> 1',                      (2027,3,13,12,0), 'not-a-date', 4, 1),
 ('ISO timestamp last -> 1 (Lens S22)',     (2027,3,13,12,0), '2027-03-12T23:00:00Z', 4, 1),
 ('no last (first play) -> 1',              (2027,3,13,12,0), None,         0, 1),
]
fails = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, (y,m,d,H,M), last, st, want in CASES:
        c = b.new_context(timezone_id='America/New_York', viewport={'width':375,'height':812})
        c.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
        c.clock.set_fixed_time(datetime.datetime(y,m,d,H,M,tzinfo=NY))
        seed = {'streak': st, 'best': st, 'ans': {}}
        if last is not None: seed['last'] = last
        c.add_init_script(f"if(!sessionStorage.getItem('seeded')){{localStorage.setItem('bf-riddle-v1',{json.dumps(json.dumps(seed))});sessionStorage.setItem('seeded','1')}}")
        pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL); pg.wait_for_selector('#choices button')
        before = int(pg.text_content('#streak'))
        pg.click('#choices button >> nth=0'); pg.wait_for_timeout(150)
        S = json.loads(pg.evaluate("localStorage.getItem('bf-riddle-v1')"))
        got = S['streak']; shown = int(pg.text_content('#streak'))
        good = got == want and shown == want and not errs
        if OLD and 'padded' in name and 'unpadded' not in name and want != 1: good = not good  # old file should show the bug
        print(('PASS ' if good else 'FAIL ') + f"{name}: seeded last={last!r} streak={st}, shown on visit={before}, after play={got} (want {want}{'; old file expected wrong' if OLD and not (got==want) else ''}), saved last={S.get('last')!r} errs={errs}")
        fails += not good; c.close()
    b.close()
print('RESULT ' + ('PASS' if not fails else f'FAIL ({fails})')); sys.exit(1 if fails else 0)
