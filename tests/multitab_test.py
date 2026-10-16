#!/usr/bin/env python3
"""Lens QA regressions: multi-tab stale overwrite, next-day zero, midnight rollover, blocked storage, share/stats."""
from pathlib import Path
from playwright.sync_api import sync_playwright
URL=(Path(__file__).resolve().parent.parent/'index.html').as_uri(); fail=0
def check(n,c,d=''):
    global fail; fail+=0 if c else 1; print(('PASS ' if c else 'FAIL ')+n+(f' ({d})' if d else ''))
def fake(y,m,d,H=12,M=0,S=0):
    return f"""(()=>{{const R=Date;const t0=new R({y},{m-1},{d},{H},{M},{S}).getTime(),r0=R.now();
    const now=()=>t0+(R.now()-r0)+(window.__skip||0);
    class F extends R{{constructor(...a){{a.length?super(...a):super(now())}}static now(){{return now()}}}};F.parse=R.parse;F.UTC=R.UTC;window.Date=F}})();"""
READY='window.__BF && document.querySelectorAll("#choices button").length>0'
def st(pg): return pg.evaluate('()=>window.__BF.getState()')
def play_today(pg,right=True):
    a=pg.evaluate('()=>window.__BF.rid(window.__BF.getState().today).answer_index')
    pg.locator('#choices button').nth(a if right else (a+1)%4).click(); pg.wait_for_timeout(100)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    # 1. Lens repro: streak 4, two tabs, tab1 plays today (5), stale tab2 plays a past riddle, reload tab1
    c=b.new_context(); c.add_init_script(fake(2026,10,16))
    t1=c.new_page(); t1.goto(URL); t1.wait_for_function(READY)
    t1.evaluate("()=>{window.__BF.setState({streak:4,best:4,last:'2026-10-15',ans:{'2026-10-15':0}});window.__BF.remount()}")
    t2=c.new_page(); t2.goto(URL); t2.wait_for_function(READY)
    play_today(t1); check('tab1 today -> 5',st(t1)['streak']==5,st(t1)['streak'])
    t2.evaluate("()=>{window.__BF.remount()}")  # stale-tab path is merge-on-save; storage event also syncs
    t2.locator('#prev').click(); t2.locator('#prev').click(); t2.wait_for_timeout(50)
    t2.locator('#choices button').nth(0).click(); t2.wait_for_timeout(100)
    t1.reload(); t1.wait_for_function(READY); s=st(t1)
    check('multi-tab: streak survives stale tab save',s['streak']==5,s)
    check('multi-tab: today play kept','2026-10-16' in s['ans'],s['ans'])
    check('multi-tab: archive play kept','2026-10-14' in s['ans'],s['ans'])
    check('storage event synced tab2 streak',st(t2)['streak']==5,st(t2)['streak'])
    c.close()
    # 1b. Pure stale write (no storage event): tab2 S older than disk
    c=b.new_context(); c.add_init_script(fake(2026,10,16)); t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    t.evaluate("()=>{window.__BF.setState({streak:4,best:4,last:'2026-10-15',ans:{}});localStorage.setItem('bf-riddle-v1',JSON.stringify({streak:5,best:5,last:'2026-10-16',ans:{'2026-10-16':1}}))}")
    t.locator('#prev').click(); t.locator('#choices button').nth(0).click(); t.wait_for_timeout(100)
    import json; raw=json.loads(t.evaluate("()=>localStorage.getItem('bf-riddle-v1')"))
    check('merge-on-save: newer disk streak not overwritten',raw['streak']==5 and '2026-10-16' in raw['ans'],raw)
    c.close()
    # 2. Next day after the multi-tab scenario: streak must not be 0 before playing, and becomes 6 after
    c=b.new_context(); c.add_init_script(fake(2026,10,17)); t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    t.evaluate("()=>{localStorage.setItem('bf-riddle-v1',JSON.stringify({streak:5,best:5,last:'2026-10-16',ans:{'2026-10-16':0,'2026-10-14':0}}))}")
    t.reload(); t.wait_for_function(READY)
    check('next day: streak still 5 before play',st(t)['streak']==5,st(t)); play_today(t,False)
    check('next day: play -> 6',st(t)['streak']==6,st(t)); c.close()
    # 3. Tab left open across midnight rolls over
    c=b.new_context(); c.add_init_script(fake(2026,10,16,23,59,58)); t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    play_today(t); d0=st(t)['today']; t.wait_for_timeout(4500); s=st(t)
    check('midnight rollover: today advances',s['today']==d0+1,(d0,s['today']))
    check('midnight rollover: shows new riddle unanswered',t.locator('#choices button:disabled').count()==0)
    play_today(t); check('midnight rollover: streak 2',st(t)['streak']==2,st(t)); c.close()
    # 3b. focus/visibility recompute
    c=b.new_context(); c.add_init_script(fake(2026,10,16)); t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    t.evaluate("()=>{window.__skip=864e5;window.dispatchEvent(new Event('focus'))}")
    check('focus recomputes today',st(t)['today']==5,st(t)['today']); c.close()
    # 4. Blocked storage -> friendly notice
    c=b.new_context(); c.add_init_script(fake(2026,10,16)+"Object.defineProperty(window,'localStorage',{get(){throw new DOMException('blocked','SecurityError')}});")
    t=c.new_page(); errs=[]; t.on('pageerror',lambda e:errs.append(str(e))); t.goto(URL); t.wait_for_function(READY)
    check('blocked storage: notice visible',t.locator('#noStore').is_visible())
    play_today(t); check('blocked storage: play still works, no errors',st(t)['streak']==1 and not errs,errs); c.close()
    c=b.new_context(); c.add_init_script(fake(2026,10,16)); t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    check('normal storage: notice hidden',not t.locator('#noStore').is_visible())
    # 5. share + stats
    play_today(t); txt=t.evaluate('()=>window.__BF.shareText()')
    check('share text single symbol, no answer/position','🟩 Got it!' in txt and 'Riddle #005' in txt and 'Electrons' not in txt and '⬜' not in txt and txt.count('🟩')+txt.count('🟥')==1 and 'Streak' in txt,txt.replace('\n',' | '))
    check('share link uses location.origin','workers.dev' not in txt or t.evaluate('()=>location.origin') in txt,txt.replace('\n',' | '))
    check('stats played 1 / 100%',t.locator('#stPlayed').inner_text()=='1' and t.locator('#stPct').inner_text()=='100%')
    check('how-to-play present',t.locator('#howto summary').count()==1)
    fs=t.evaluate("()=>[getComputedStyle(document.querySelector('#choices button')).fontSize,getComputedStyle(document.querySelector('#question')).fontSize,getComputedStyle(document.querySelector('.hint')).fontSize,getComputedStyle(document.querySelector('small')).opacity]")
    check('text sizes (buttons/riddle >=20, meta >=16, footer opaque)',float(fs[0][:-2])>=20 and float(fs[1][:-2])>=20 and float(fs[2][:-2])>=16 and fs[3]=='1',fs)
    c.close(); b.close()
print('RESULT','PASS' if fail==0 else f'FAIL ({fail})'); raise SystemExit(1 if fail else 0)
