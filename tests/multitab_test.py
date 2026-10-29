#!/usr/bin/env python3
"""Lens QA regressions: multi-tab stale overwrite, next-day zero, midnight rollover, blocked storage, share/stats.
Tinker 2026-10-23 race fix: no fixed sleeps. Chrome hands one tab's localStorage write to another tab
asynchronously, so a step that needs another tab's save now WAITS until that tab can see it (Lens 10/23:
about 1 in 20 runs false-FAILed when tab 2 acted on 100 ms of sleep). A wait that never comes true is a FAIL."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import functools, http.server, threading
# Serve the page over http://127.0.0.1 (a random free port), like kids load it over https. Under load, headless
# Chrome on file:// sometimes dropped one tab's saves for any NEW page or reload (blank storage), which false-FAILed.
_srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),
    {'log_message':lambda *a:None}),directory=str(Path(__file__).resolve().parent.parent)))
threading.Thread(target=_srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{_srv.server_address[1]}/index.html'; fail=0
def check(n,c,d=''):
    global fail; fail+=0 if c else 1; print(('PASS ' if c else 'FAIL ')+n+(f' ({d})' if d else ''))
def fake(y,m,d,H=12,M=0,S=0):
    return f"""(()=>{{const R=Date;const t0=new R({y},{m-1},{d},{H},{M},{S}).getTime(),r0=R.now();
    const now=()=>t0+(R.now()-r0)+(window.__skip||0);
    class F extends R{{constructor(...a){{a.length?super(...a):super(now())}}static now(){{return now()}}}};F.parse=R.parse;F.UTC=R.UTC;window.Date=F}})();"""
READY='window.__BF && document.querySelectorAll("#choices button").length>0'
def st(pg): return pg.evaluate('()=>window.__BF.getState()')
def wait_js(pg,js,arg=None,what='',ms=5000):  # wait on real state; a timeout is reported as a FAIL, not a crash
    try: pg.wait_for_function(js,arg=arg,timeout=ms); return True
    except Exception: check('wait: '+what,False,f'not true within {ms} ms'); return False
SAVED="(k)=>{try{return JSON.parse(localStorage.getItem('bf-riddle-v1')).ans[k]!=null}catch(e){return false}}"
def wait_saved(pg,k,who): return wait_js(pg,SAVED,k,f'{who} sees the save for {k}')  # this tab's view of storage
def wait_cur(pg,back): return wait_js(pg,'(n)=>{const s=window.__BF.getState();return s.cur===s.today-n}',back,f'archive -{back} shown')
def play_today(pg,right=True):
    a=pg.evaluate('()=>window.__BF.rid(window.__BF.getState().today).answer_index')
    n=pg.locator('#choices button').count()
    if right:
        pg.locator('#choices button').nth(a).click()
    else:
        # Use up every miss (choices.length-1). The day still counts, right or wrong.
        for i in range(n):
            if i==a: continue
            pg.locator('#choices button').nth(i).click()
    wait_js(pg,'()=>document.querySelectorAll("#choices button:disabled").length>0',None,'answer shown')  # click handled
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    # 1. Lens repro: streak 4, two tabs, tab1 plays today (5), stale tab2 plays a past riddle, reload tab1
    c=b.new_context(); c.add_init_script(fake(2026,10,16))
    t1=c.new_page(); t1.goto(URL); t1.wait_for_function(READY)
    t1.evaluate("()=>{window.__BF.setState({streak:4,best:4,last:'2026-10-15',ans:{'2026-10-15':0}});window.__BF.remount()}")
    t2=c.new_page(); t2.goto(URL); t2.wait_for_function(READY)
    play_today(t1); wait_saved(t1,'2026-10-16','tab1'); check('tab1 today -> 5',st(t1)['streak']==5,st(t1)['streak'])
    wait_saved(t2,'2026-10-16','tab2')  # THE race: tab 2 must see tab 1's save before tab 2 saves
    t2.evaluate("()=>{window.__BF.remount()}")  # stale-tab path is merge-on-save; storage event also syncs
    t2.locator('#prev').click(); t2.locator('#prev').click(); wait_cur(t2,2)
    a2=t2.evaluate('()=>window.__BF.rid(window.__BF.getState().cur).answer_index')
    t2.locator('#choices button').nth(a2).click(); wait_saved(t2,'2026-10-14','tab2')
    wait_saved(t1,'2026-10-14','tab1')  # and tab 1 sees tab 2's save before it reloads
    t1.reload(); t1.wait_for_function(READY); s=st(t1)
    check('multi-tab: streak survives stale tab save',s['streak']==5,s)
    check('multi-tab: today play kept','2026-10-16' in s['ans'],s['ans'])
    check('multi-tab: archive play kept','2026-10-14' in s['ans'],s['ans'])
    wait_js(t2,'()=>window.__BF.getState().streak===5',None,'tab2 streak becomes 5'); check('storage event synced tab2 streak',st(t2)['streak']==5,st(t2)['streak'])
    c.close()
    # 1b. Pure stale write (no storage event): tab2 S older than disk
    c=b.new_context(); c.add_init_script(fake(2026,10,16)); t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    t.evaluate("()=>{window.__BF.setState({streak:4,best:4,last:'2026-10-15',ans:{}});localStorage.setItem('bf-riddle-v1',JSON.stringify({streak:5,best:5,last:'2026-10-16',ans:{'2026-10-16':1}}))}")
    t.locator('#prev').click(); wait_cur(t,1)
    aa=t.evaluate('()=>window.__BF.rid(window.__BF.getState().cur).answer_index')
    t.locator('#choices button').nth(aa).click(); wait_saved(t,'2026-10-15','tab')
    import json; raw=json.loads(t.evaluate("()=>localStorage.getItem('bf-riddle-v1')"))
    check('merge-on-save: newer disk streak not overwritten',raw['streak']==5 and '2026-10-16' in raw['ans'],raw)
    c.close()
    # 2. Next day after the multi-tab scenario: streak must not be 0 before playing, and becomes 6 after
    # Seed saved progress before the page's own scripts run (an init script, once per tab). Setting it from the
    # page and then reloading raced Chrome's storage flush (~3 in 8 runs saw a blank save after the reload).
    c=b.new_context(); c.add_init_script(fake(2026,10,17))
    c.add_init_script("if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');localStorage.setItem('bf-riddle-v1',JSON.stringify({streak:5,best:5,last:'2026-10-16',ans:{'2026-10-16':0,'2026-10-14':0}}))}")
    t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    check('next day: streak still 5 before play',st(t)['streak']==5,st(t)); play_today(t,False)
    check('next day: play -> 6',st(t)['streak']==6,st(t)); c.close()
    # 3. Tab left open across midnight rolls over
    c=b.new_context(); c.add_init_script(fake(2026,10,16,23,59,58)); t=c.new_page(); t.goto(URL); t.wait_for_function(READY)
    play_today(t); d0=st(t)['today']
    wait_js(t,'(d)=>window.__BF.getState().today===d+1',d0,'midnight passes',8000); s=st(t)  # midnight is ~2 s away
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
    check('share text grid, no answer', txt.startswith('Bit & Fathom Daily #005') and '🟩' in txt and 'This week' in txt and 'Electrons' not in txt and '🔥' in txt and '/r/005/' in txt, txt.replace('\n',' | '))
    check('share link uses canonical origin','bit-fathom-daily-next.gigantic-stranger.workers.dev/r/005/' in txt and '127.0.0.1' not in txt,txt.replace('\n',' | '))
    check('stats played 1 / 100%',t.locator('#stPlayed').inner_text()=='1' and t.locator('#stPct').inner_text()=='100%')
    check('how-to-play present',t.locator('#howto summary').count()==1)
    fs=t.evaluate("()=>[getComputedStyle(document.querySelector('#choices button')).fontSize,getComputedStyle(document.querySelector('#question')).fontSize,getComputedStyle(document.querySelector('.hint')).fontSize,getComputedStyle(document.querySelector('small')).opacity]")
    check('text sizes (buttons/riddle >=20, meta >=16, footer opaque)',float(fs[0][:-2])>=20 and float(fs[1][:-2])>=20 and float(fs[2][:-2])>=16 and fs[3]=='1',fs)
    c.close(); b.close()
print('RESULT','PASS' if fail==0 else f'FAIL ({fail})'); raise SystemExit(1 if fail else 0)
