from playwright.sync_api import sync_playwright
U='file:///workspace/proto-bot/bit-fathom-daily/index.html'
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  for name,(w,h,fp) in {'mobile':(390,844,False),'desktop':(1280,800,True)}.items():
    for tag,i in [('1-question',None),('2-right',0),('3-wrong',1)]:
      c=b.new_context(viewport={'width':w,'height':h},reduced_motion='reduce');pg=c.new_page();pg.goto(U);pg.wait_for_timeout(300)
      if i is not None: pg.locator('#choices button').nth(i).click();pg.wait_for_timeout(300); pg.locator('#reveal').scroll_into_view_if_needed()
      if name=='mobile' and i is not None: pg.evaluate("document.querySelector('#verdict').scrollIntoView({block:'start'})"); 
      pg.screenshot(path=f'img/{name}-{tag}.jpg',type='jpeg',quality=72,full_page=fp);c.close()
