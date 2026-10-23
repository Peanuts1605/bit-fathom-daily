#!/usr/bin/env python3
"""Clock-skew regression: a saved 'last' date in the FUTURE (device clock was ahead, then corrected).
Spec: the streak must not freeze. Visiting keeps the streak, playing today saves today's date (not the
future one) and grows the streak, and the next day grows it again. Seeds storage with an init script
before the page runs, and waits on state instead of fixed sleeps. Served over local http like multitab_test.py."""
import json, functools, http.server, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
_srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),
    {'log_message':lambda *a:None}),directory=str(Path(__file__).resolve().parent.parent)))
threading.Thread(target=_srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{_srv.server_address[1]}/index.html'; fail=0
def check(n,c,d=''):
    global fail; fail+=0 if c else 1; print(('PASS ' if c else 'FAIL ')+n+(f' ({d})' if d else ''))
def fake(y,m,d,H=12):
    return f"""(()=>{{const R=Date;const t0=new R({y},{m-1},{d},{H},0,0).getTime(),r0=R.now();
    const now=()=>t0+(R.now()-r0);
    class F extends R{{constructor(...a){{a.length?super(...a):super(now())}}static now(){{return now()}}}};F.parse=R.parse;F.UTC=R.UTC;window.Date=F}})();"""
def seed(obj): return "if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');localStorage.setItem('bf-riddle-v1',%s)}"%json.dumps(json.dumps(obj))
READY='window.__BF && document.querySelectorAll("#choices button").length>0'
def st(pg): return pg.evaluate('()=>window.__BF.getState()')
def disk(pg): return json.loads(pg.evaluate("()=>localStorage.getItem('bf-riddle-v1')") or 'null')
def play_today(pg):
    a=pg.evaluate('()=>window.__BF.rid(window.__BF.getState().today).answer_index')
    pg.locator('#choices button').nth(a).click()
    pg.wait_for_function('()=>document.querySelectorAll("#choices button:disabled").length>0')
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    # Clock was 4 days ahead: last play saved as Oct 20 with streak 7. Real date is Oct 16.
    future={'streak':7,'best':7,'last':'2026-10-20','ans':{'2026-10-20':0}}
    c=b.new_context(); c.add_init_script(fake(2026,10,16)); c.add_init_script(seed(future))
    t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    check('future date: visit keeps streak 7 (not wiped)',st(t)['streak']==7,st(t))
    play_today(t); s=st(t); d=disk(t)
    check('future date: play today grows streak to 8',s['streak']==8,s)
    check('future date: saved last is today, not the future date',d and d['last']=='2026-10-16',d)
    check('future date: on-screen streak matches saved',t.locator('#streak').inner_text()==str(d and d['streak']),(t.locator('#streak').inner_text(),d))
    saved=d; c.close()
    # Next real day: the streak must keep growing (a frozen streak would stay at 7 or 8)
    c=b.new_context(); c.add_init_script(fake(2026,10,17)); c.add_init_script(seed(saved))
    t=c.new_page(); t.goto(URL); t.wait_for_function(READY); play_today(t); d=disk(t)
    check('next day after skew: streak 9',d and d['streak']==9,d)
    c.close()
    # A far-future junk year must not freeze it either
    c=b.new_context(); c.add_init_script(fake(2026,10,16)); c.add_init_script(seed({'streak':3,'best':3,'last':'2099-1-1','ans':{}}))
    t=c.new_page(); t.goto(URL); t.wait_for_function(READY); play_today(t); d=disk(t)
    check('year 2099 saved: today saved and streak not frozen at 3',d and d['last']=='2026-10-16' and d['streak']!=3,d)
    c.close(); b.close()
print('RESULT','PASS' if fail==0 else f'FAIL ({fail})'); raise SystemExit(1 if fail else 0)
