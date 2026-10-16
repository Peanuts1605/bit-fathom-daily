import html,base64,os
R='/workspace/proto-bot/bit-fathom-daily/'
P='https://bit-fathom-daily-preview.gigantic-stranger.workers.dev/'
def full(f): return '<details><summary>📖 Read the full text</summary><pre>'+html.escape(open(R+f).read())+'</pre></details>'
def img(n,cap): return f'<figure><img src="img/{n}.jpg" alt="{cap}" loading="lazy"><figcaption>{cap}</figcaption></figure>'
docs=[('🎯','Scope','devpost/scope.md','What we are making',
 ['<b>One science riddle a day</b> for kids 7–12.','Two robots ask it: <b>Bit</b> and <b>Fathom</b>.','Kid picks an answer, then gets the <b>why</b>, a <b>try-at-home</b> test, and a <b>real source</b>.','<b>No accounts, no ads, no tracking.</b>']),
 ('🧭','PRD (the plan)','devpost/prd.md','How it works for the kid',
 ['Open the page → see <b>today\'s riddle</b>.','Tap an answer → <b>right ✓ or kind "nice try"</b>.','A wrong guess <b>still counts</b> for the streak 🔥.','Tap <b>‹ ›</b> to replay past riddles. After 14 days they come back as <b>Encores</b>.','<b>📤 Share</b> an emoji-only result, see <b>📊 stats</b>, and read <b>❓ How to play</b>.']),
 ('🛠️','Spec (the build)','devpost/spec.md','How it is built',
 ['<b>One single web page</b>, no server needed.','<b>14 riddles</b>, all fact-checked.','The streak is saved <b>only on the phone</b>.','Uses the phone\'s own date, so the riddle changes at <b>local midnight</b>.'])]
cards=''.join(f'<section class="box"><h2>{e} {t}</h2><p class="sub">{s}</p><ul>'+''.join(f'<li>{x}</li>' for x in b)+'</ul>'+full(f)+'</section>' for e,t,f,s,b in docs)
dev=open(R+'DEVPOST.md').read(); vs=dev[dev.index('## Video script'):]
vid=''.join(f'<li>{html.escape(l[3:].strip()).replace("**","")}</li>' for l in vs.splitlines() if l[:1].isdigit())
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review: Bit & Fathom Daily Riddle</title><meta name="robots" content="noindex"><link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>
body{{margin:0;background:#0b1a33;color:#f4f8ff;font-family:Verdana,Tahoma,system-ui,sans-serif;font-size:21px;line-height:1.6;letter-spacing:.02em}}
main{{max-width:760px;margin:auto;padding:20px}}h1{{font-size:1.7em;line-height:1.25;margin:.3em 0}}h2{{font-size:1.3em;margin:.2em 0}}
.big{{display:block;text-align:center;background:#f2c14e;color:#0b1a33;font-weight:800;font-size:1.35em;padding:22px;border-radius:20px;text-decoration:none;margin:18px 0}}
.big:focus,.big:hover{{outline:4px solid #7fe7ff}}
.box{{background:#13284d;border:3px solid #2ec4b6;border-radius:20px;padding:18px 20px;margin:20px 0}}
.sub{{color:#f2c14e;font-weight:700;margin:0}}ul,ol{{padding-left:1.2em}}li{{margin:.45em 0}}
details summary{{cursor:pointer;font-weight:700;color:#7fe7ff;padding:10px 0;min-height:44px}}
pre{{white-space:pre-wrap;font-family:inherit;font-size:.8em;background:#0b1a33;padding:14px;border-radius:12px}}
.shots{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}}
figure{{margin:0}}img{{width:100%;border-radius:12px;border:2px solid #2b4677}}figcaption{{font-size:.8em;text-align:center;font-weight:700}}
.todo li{{list-style:none;margin-left:-1.2em}}.todo label{{display:flex;gap:12px;align-items:flex-start;cursor:pointer}}
.todo input{{width:28px;height:28px;flex:none;margin-top:4px}}.due{{background:#9a3b1e;padding:12px 16px;border-radius:14px;font-weight:800}}
</style></head><body><main>
<p>🧩 <b>Bit &amp; Fathom Daily Riddle</b></p>
<h1>Your 10-minute review ✅</h1>
<p class="due">⏰ Due: <b>Mon Oct 26, 5 PM ET</b></p>
<a class="big" href="{P}" target="_blank" rel="noopener">▶️ Try the app</a>
<section class="box"><h2>✅ Your to-do list</h2><ol class="todo">
<li><label><input type="checkbox"><span><b>Try the app</b> (button above). Answer one riddle.</span></label></li>
<li><label><input type="checkbox"><span><b>Read the 3 boxes below</b> (Scope, Plan, Build).</span></label></li>
<li><label><input type="checkbox"><span><b>Say "approved"</b> to Grok Bot, or tell it what to change.</span></label></li>
<li><label><input type="checkbox"><span><b>Pick the license name:</b> "Naumio" or your name.</span></label></li>
<li><label><input type="checkbox"><span><b>Join on Devpost</b> as the adult entrant (18+) and submit by <b>Oct 26, 5 PM ET</b>.</span></label></li>
</ol><p>💡 The checkmarks are just for you. Nothing is sent.</p></section>
{cards}
<section class="box"><h2>📸 Pictures</h2><p class="sub">📱 Phone</p><div class="shots">{img('mobile-1-question','1. The riddle')}{img('mobile-2-right','2. Right answer')}{img('mobile-3-wrong','3. Wrong answer')}</div>
<p class="sub">💻 Computer</p><div class="shots">{img('desktop-1-question','1. The riddle')}{img('desktop-2-right','2. Right answer')}</div></section>
<section class="box"><h2>🎬 Video script (about 2 min)</h2><ol>{vid}</ol></section>
<section class="box"><h2>🔒 Safety check</h2><ul><li><b>No trackers</b>, no ads, no cookies.</li><li><b>No personal info</b> and no passwords in the code.</li><li>Every button and link was <b>tested on phone and computer</b>.</li></ul></section>
</main></body></html>'''
os.makedirs('site',exist_ok=True);open('site/index.html','w').write(page)
