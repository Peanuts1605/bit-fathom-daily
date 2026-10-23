#!/usr/bin/env python3
"""Clock-skew regression: a saved 'last' date in the FUTURE (device clock was ahead, then corrected).
Spec: a saved future date counts as TODAY. Visiting keeps the streak, playing again the same real day does not
count twice (Tinker's edge case) but saves the real date, and the next real day grows the streak (no freeze). Seeds storage with an init script
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
    # Tinker's edge case. Real date Oct 16, but the clock runs 4 days ahead (Oct 20). The kid plays: 6 -> 7, saved as Oct 20.
    c=b.new_context(); c.add_init_script(fake(2026,10,20)); c.add_init_script(seed({'streak':6,'best':6,'last':'2026-10-19','ans':{'2026-10-19':0}}))
    t=c.new_page(); t.goto(URL); t.wait_for_function(READY); play_today(t); ahead=disk(t)
    check('clock ahead: play saves the future date, streak 7',ahead and ahead['last']=='2026-10-20' and ahead['streak']==7,ahead); c.close()
    # Clock corrected to the real Oct 16. Visit keeps 7. Playing again the SAME real day must not count twice.
    c=b.new_context(); c.add_init_script(fake(2026,10,16)); c.add_init_script(seed(ahead))
    t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    check('future date: visit keeps streak 7 (not wiped)',st(t)['streak']==7,st(t))
    play_today(t); s=st(t); d=disk(t)
    check('same real day after correction: no double count, streak stays 7',s['streak']==7 and d and d['streak']==7,(s,d))
    check('future date: saved last is the real today, not the future date',d and d['last']=='2026-10-16',d)
    check('future date: on-screen streak matches saved',t.locator('#streak').inner_text()==str(d and d['streak']),(t.locator('#streak').inner_text(),d))
    saved=d; c.close()
    # Next real day: the streak grows again (a frozen streak would stay at 7)
    c=b.new_context(); c.add_init_script(fake(2026,10,17)); c.add_init_script(seed(saved))
    t=c.new_page(); t.goto(URL); t.wait_for_function(READY); play_today(t); d=disk(t)
    check('next day after skew: streak 8',d and d['streak']==8 and d['last']=='2026-10-17',d)
    c.close()
    # A far-future junk year: today's real date is saved (no freeze) and the next day grows the streak
    c=b.new_context(); c.add_init_script(fake(2026,10,16)); c.add_init_script(seed({'streak':3,'best':3,'last':'2099-1-1','ans':{}}))
    t=c.new_page(); t.goto(URL); t.wait_for_function(READY); play_today(t); d=disk(t)
    check('year 2099 saved: real today saved, no double count',d and d['last']=='2026-10-16' and d['streak']==3,d); c.close()
    c=b.new_context(); c.add_init_script(fake(2026,10,17)); c.add_init_script(seed(d))
    t=c.new_page(); t.goto(URL); t.wait_for_function(READY); play_today(t); d=disk(t)
    check('year 2099 then next day: streak 4',d and d['streak']==4 and d['last']=='2026-10-17',d)
    c.close(); b.close()
print('RESULT','PASS' if fail==0 else f'FAIL ({fail})'); raise SystemExit(1 if fail else 0)
