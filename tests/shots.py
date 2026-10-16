from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent.parent; U=(R/'index.html').as_uri(); O=R/'shots'
def fake(d):
    return "(()=>{const R=Date,f=new R(%s,12,0,0);class F extends R{constructor(...a){a.length?super(...a):super(f.getTime())}static now(){return f.getTime()}};F.parse=R.parse;F.UTC=R.UTC;window.Date=F})();"%d
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    for name,(w,h) in {'mobile':(390,844),'desktop':(1280,800)}.items():
        for tag,date,pick in [('1-today','2026,9,16',None),('2-wrong','2026,9,16','wrong'),('3-right','2026,9,16','right'),('4-encore','2026,9,27',None)]:
            c=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if name=='mobile' else 1)
            c.add_init_script(fake(date)); pg=c.new_page(); errs=[]
            pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('requestfailed',lambda r:errs.append(r.url))
            pg.goto(U); pg.wait_for_timeout(300)
            if pick:
                ai=pg.evaluate("(()=>{try{return JSON.parse(document.querySelector('script[type=\"application/json\"]')?.textContent||'null')}catch(e){return null}})()")
                btns=pg.locator('button.choice, .choices button')
                n=btns.count()
                # find correct by trying evaluate of app state not available: click and inspect
                btns.nth(0).click(); pg.wait_for_timeout(200)
                ok=pg.locator('.right, .correct').count()>0 and pg.locator('.wrong').count()==0
                if (pick=='right')!=ok:
                    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(300)
                    btns=pg.locator('button.choice, .choices button')
                    target = None
                    # correct index is the one that got 'right' class
                    btns.nth(1 if pick=='wrong' and ok else 0).click()
                pg.wait_for_timeout(300)
                if pick=='wrong' and pg.locator('.wrong').count()==0:
                    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(300)
                    pg.locator('button.choice, .choices button').nth(2).click(); pg.wait_for_timeout(300)
            pg.screenshot(path=str(O/f'{name}-{tag}.png'),full_page=True)
            print(name,tag,'errors:',errs, 'wrong:',pg.locator('.wrong').count())
            c.close()
    b.close()
