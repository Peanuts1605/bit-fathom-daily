/* Bit & Fathom Daily Riddle — web streak rules + app shell.
 * Streak (STREAK.md): playing today counts right or wrong, once per local day;
 * archive never changes it; a skipped local day resets it. Dates are local.
 * Tries: up to choices.length-1. A correct pick or the last miss ends the riddle.
 */
(function(){
var K1='bf-riddle-v1', K2='bf-riddle-v2', KAPP='bfdr.v1', OK=true, S;
var EPOCH=new Date(2026,9,12), R=[], today=0, cur=0, grownOK=false, lastFocus=null;
var $=function(i){return document.getElementById(i)};
var WHY=[
  'Not that one. Cross it out and look again.',
  'The science goes a different way. Try another.',
  'That guess stays on the bench. One more look.'
];
var LEARNED=[
  'Not this time, and that is how robots learn.',
  'Crossed out and remembered. That is science.',
  'Misses are clues. I am proud you looked.'
];
var POSE={
  thinking:'assets/characters/bit-thinking.svg',
  happy:'assets/characters/bit-happy.svg',
  surprised:'assets/characters/bit-surprised.svg',
  curious:'assets/characters/bit-curious.svg'
};
var SCENES=['space','ocean','lab'];

function blank(){return {v:2,plays:{},streak:0,best:0,last:null,sound:true,haptics:true,ans:{}}}
function num(x){return (typeof x==='number'&&isFinite(x)&&x>=0)?Math.floor(x):0}
function localMidnight(d){return new Date(d.getFullYear(),d.getMonth(),d.getDate())}
function dayNum(d){return Math.round((localMidnight(d)-EPOCH)/864e5)}
function dateOf(n){var d=new Date(EPOCH.getTime());d.setDate(EPOCH.getDate()+n);return d}
function key(d){return d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate()}
function kday(k){if(!k)return -1e9;var p=String(k).split('-'),n=dayNum(new Date(+p[0],p[1]-1,+p[2]));return isNaN(n)?-1e9:n}
function lday(k){var n=kday(k),t=Math.max(0,dayNum(new Date()));return n>t?t:n}
function future(k){return kday(k)>Math.max(0,dayNum(new Date()))}
function fmt(d){return d.toLocaleDateString(undefined,{weekday:'long',month:'long',day:'numeric'})}
function rid(n){return R[((n%R.length)+R.length)%R.length]}
function isEncore(n){return n>=R.length}
function todayKey(){return key(dateOf(today))}
function yesterdayKey(){return key(dateOf(today-1))}
function stale(o){return o.last&&kday(o.last)<today-1}
function maxTries(r){return Math.max(1,(r.choices||[]).length-1)}
function normKey(k){var n=kday(k); if(!(n>-1e8)||isNaN(n)) return null; return key(dateOf(n))}
function syncAnsOn(s){
  s.ans={};
  for(var k in s.plays){
    var p=s.plays[k];
    if(p&&p.done&&p.tries&&p.tries.length) s.ans[k]=p.tries[p.tries.length-1];
  }
}
function preferPlay(a,b){
  if(!a||!a.tries) return b||null;
  if(!b||!b.tries) return a;
  if(!!a.done!==!!b.done) return a.done?a:b;
  return a.tries.length>=b.tries.length?a:b;
}
function mergePlays(a,b){
  var m={}, seen={};
  if(b) for(var k in b) seen[k]=1;
  if(a) for(var k2 in a) seen[k2]=1;
  for(var k3 in seen){
    var w=preferPlay(a&&a[k3], b&&b[k3]);
    if(w) m[k3]=w;
  }
  return m;
}
function merge(a,b){
  a=a||blank(); b=b||blank();
  var m={v:2,plays:mergePlays(a.plays,b.plays),sound:a.sound,haptics:a.haptics};
  var la=lday(a.last), lb=lday(b.last);
  if(la>lb){m.last=a.last;m.streak=a.streak|0}
  else if(lb>la){m.last=b.last;m.streak=b.streak|0}
  else{m.last=(a.last&&!future(a.last))?a.last:(b.last&&!future(b.last))?b.last:(a.last||b.last||null);m.streak=Math.max(a.streak|0,b.streak|0)}
  m.best=Math.max(a.best|0,b.best|0,m.streak|0);
  if(stale(m)) m.streak=0;
  syncAnsOn(m);
  return m;
}
function readJSON(k){
  try{var t=localStorage.getItem(k); if(!t) return null; var o=JSON.parse(t); return (o&&typeof o==='object'&&!Array.isArray(o))?o:null}
  catch(e){return null}
}
function playFromGuess(k,idx,okFlag){
  var n=kday(k), r=rid(n);
  var ok = (okFlag===true||okFlag===false) ? okFlag===true : idx===r.answer_index;
  return {id:r.id, tries:[idx], ok:ok, t:0, done:true};
}
function v1ToState(o){
  var s=blank(); if(!o) return s;
  s.streak=num(o.streak); s.best=num(o.best); s.last=(typeof o.last==='string')?o.last:null;
  var ans=(o.ans&&typeof o.ans==='object'&&!Array.isArray(o.ans))?o.ans:{};
  for(var k in ans){
    if(typeof ans[k]!=='number') continue;
    var nk=normKey(k); if(!nk) continue;
    s.plays[nk]=playFromGuess(nk, ans[k]);
  }
  syncAnsOn(s); return s;
}
function appToState(o){
  if(!o||!o.h||typeof o.h!=='object'||Array.isArray(o.h)) return null;
  var s=blank(); s.sound=o.sound===true; s.best=num(o.best); s.haptics=true;
  for(var k in o.h){
    var e=o.h[k]; if(!e||typeof e!=='object'||Array.isArray(e)) continue;
    var nk=normKey(k); if(!nk) continue;
    var g=(typeof e.g==='number')?e.g:0;
    s.plays[nk]=playFromGuess(nk, g, e.ok===true);
  }
  syncAnsOn(s); return s;
}
function v2ToState(o){
  if(!o||!o.plays||typeof o.plays!=='object'||Array.isArray(o.plays)) return null;
  var s=blank();
  s.streak=num(o.streak); s.best=num(o.best); s.last=(typeof o.last==='string')?o.last:null;
  s.sound=o.sound!==false; s.haptics=o.haptics!==false;
  for(var k in o.plays){
    var p=o.plays[k]; if(!p||typeof p!=='object') continue;
    var nk=normKey(k); if(!nk) continue;
    var tries=Array.isArray(p.tries)?p.tries.filter(function(x){return typeof x==='number'}):[];
    if(!tries.length) continue;
    s.plays[nk]={id:p.id||rid(kday(nk)).id, tries:tries, ok:p.ok===true, t:p.t||0, done:p.done===true||p.ok===true};
  }
  syncAnsOn(s); return s;
}
function load(){
  var rawApp=readJSON(KAPP), raw1=readJSON(K1), raw2=readJSON(K2);
  var app=appToState(rawApp), v1=raw1?v1ToState(raw1):null, v2=v2ToState(raw2);
  var s=blank();
  if(app) s=merge(app,s);
  if(v1) s=merge(v1,s);
  if(v2) s=merge(v2,s);
  if(raw2) s.sound=raw2.sound!==false;
  else if(rawApp && rawApp.sound===false) s.sound=false;
  else if(rawApp && rawApp.sound===true) s.sound=true;
  if(raw2 && raw2.haptics===false) s.haptics=false;
  s.best=Math.max(s.best|0, app?num(app.best):0, v1?num(v1.best):0, v2?num(v2.best):0, s.streak|0);
  syncAnsOn(s);
  return s;
}
function persist(s){return {v:2,plays:s.plays,streak:s.streak|0,best:s.best|0,last:s.last||null,sound:!!s.sound,haptics:s.haptics!==false}}
function v1view(s){
  var ans={}; syncAnsOn(s);
  for(var k in s.ans) ans[k]=s.ans[k];
  var o={ans:ans,streak:s.streak|0,best:s.best|0};
  if(s.last) o.last=s.last;
  return o;
}
function probe(){try{localStorage.setItem(K2+'-t','1'); localStorage.removeItem(K2+'-t'); return true}catch(e){return false}}
function notice(){var n=$('noStore'); if(n) n.hidden=OK}
function sync(){if(!OK) return; S=merge(S, load())}
function save(){
  if(!OK) return;
  S=merge(S, load());
  try{localStorage.setItem(K2, JSON.stringify(persist(S))); localStorage.setItem(K1, JSON.stringify(v1view(S)))}
  catch(e){OK=false; notice()}
}
function applySkipReset(){
  var tk=todayKey();
  if(S.ans[tk]!=null&&S.last!==tk&&lday(S.last)>=today-1){S.last=tk; save()}
  if(stale(S)) S.streak=0;
}
function refreshDay(){
  if(!R.length) return;
  var t=Math.max(0,dayNum(new Date()));
  sync();
  if(t!==today){var was=cur===today; today=t; if(was||cur>today) cur=today}
  applySkipReset(); render();
}
var mt=null;
function armMidnight(){
  clearTimeout(mt);
  var n=new Date(), m=new Date(n.getFullYear(),n.getMonth(),n.getDate()+1,0,0,1);
  mt=setTimeout(function(){refreshDay(); armMidnight()}, Math.max(1000, m-n));
}
window.addEventListener('storage', function(e){if(!e.key||e.key===K1||e.key===K2||e.key===KAPP) refreshDay()});
window.addEventListener('focus', refreshDay);
document.addEventListener('visibilitychange', function(){if(!document.hidden) refreshDay()});

function applyDeepLink(){
  var d=null;
  try{d=new URLSearchParams(location.search).get('d')}catch(e){}
  if(!d) return;
  var n=parseInt(d,10);
  if(!n||n<1) return;
  var idx=n-1;
  if(idx<0) return;
  if(idx>today) return;
  cur=idx;
}
function paintSound(){
  ['soundBtn','soundBtn2'].forEach(function(id){
    var b=$(id); if(!b) return;
    b.textContent=S.sound?'🔊':'🔇';
    b.setAttribute('aria-pressed', S.sound?'true':'false');
    b.setAttribute('aria-label', S.sound?'Sound on':'Sound off');
  });
}
function paintHap(){
  var b=$('hapBtn'); if(!b) return;
  b.textContent=S.haptics?'📳':'📴';
  b.setAttribute('aria-pressed', S.haptics?'true':'false');
  b.setAttribute('aria-label', S.haptics?'Vibration on':'Vibration off');
}
function setBit(name){
  var img=$('bit'); if(!img) return;
  var src=POSE[name]||POSE.thinking;
  if(img.getAttribute('src')!==src) img.setAttribute('src', src);
  img.alt='Bit, '+name;
}
function sceneFor(r){return SCENES[(parseInt(r.id,10)-1)%SCENES.length]}
function currentPlay(){return S.plays[key(dateOf(cur))]||null}
function shareText(){
  return window.BFShare.shareGrid(S, cur, {rid:rid, key:key, dateOf:dateOf, today:today, origin:location.origin, maxTries:maxTries});
}
function paintStats(){
  var agg=window.BFStats.aggregate(S, {kday:kday, today:today});
  $('stPlayed').textContent=agg.played;
  $('stPct').textContent=agg.winPct+'%';
  $('stStreak').textContent=agg.streak;
  $('stBest').textContent=agg.best;
  if($('best')) $('best').textContent=agg.best;
  $('streak').textContent=S.streak;
}
function paintBars(){
  var agg=window.BFStats.aggregate(S, {kday:kday, today:today});
  $('mPlayed').textContent=agg.played;
  $('mPct').textContent=agg.winPct+'%';
  $('mStreak').textContent=agg.streak;
  $('mBest').textContent=agg.best;
  var labels=['1st try','2nd try','3rd try','Learned'];
  var peak=1; agg.dist.forEach(function(n){if(n>peak) peak=n});
  var tp=S.plays[todayKey()];
  var bucket=-1;
  if(tp&&tp.done) bucket=tp.ok?Math.min(Math.max((tp.tries||[]).length,1),3)-1:3;
  var box=$('bars'); box.textContent='';
  labels.forEach(function(lab,i){
    var row=document.createElement('div');
    row.className='bar'+(i===bucket?' is-today':'');
    var name=document.createElement('span'); name.textContent=lab;
    var track=document.createElement('span'); track.className='track';
    var fill=document.createElement('span'); fill.className='fill';
    fill.style.width=Math.round(100*agg.dist[i]/peak)+'%';
    var count=document.createElement('b'); count.textContent=String(agg.dist[i]);
    track.appendChild(fill); row.appendChild(name); row.appendChild(track); row.appendChild(count);
    box.appendChild(row);
  });
}
function renderGrid(r,p){
  var box=$('grid'); if(!box) return;
  box.textContent='';
  var text=shareText();
  if($('sharePreview')) $('sharePreview').textContent=text;
  if(!p||!p.done) return;
  var cells=[];
  if(p.ok){
    for(var i=0;i<p.tries.length-1;i++) cells.push('miss');
    cells.push('hit');
  } else {
    for(var j=0;j<p.tries.length;j++) cells.push('miss');
    cells.push('book');
  }
  cells.forEach(function(kind){
    var s=document.createElement('i');
    s.className=kind;
    s.textContent=kind==='hit'?'🟩':kind==='book'?'📘':'🟥';
    box.appendChild(s);
  });
  var frac=document.createElement('b');
  frac.textContent=p.ok?(' '+p.tries.length+'/'+maxTries(r)):' learned';
  box.appendChild(frac);
}
function render(){
  var r=rid(cur), d=dateOf(cur), p=currentPlay();
  var whenB=$('label');
  whenB.textContent='';
  whenB.appendChild(document.createTextNode(cur===today?"Today's riddle":'Riddle #'+r.id));
  if(isEncore(cur)){whenB.appendChild(document.createTextNode(' ')); var en=document.createElement('span'); en.className='encore'; en.textContent='Encore'; whenB.appendChild(en)}
  $('date').textContent=fmt(d);
  $('prev').disabled=cur<=0||today-cur>=R.length-1;
  $('next').disabled=cur>=today;
  $('title').textContent=r.hook||r.title;
  $('question').textContent=r.question;
  var topic=$('topic');
  if(topic) topic.textContent=(window.BFShare.emoji(r.topic)+' '+(r.topic||'Science'));
  var sc=sceneFor(r);
  var simg=$('sceneImg');
  if(simg) simg.src='assets/backgrounds/'+sc+'-1200x675.png';
  document.body.setAttribute('data-scene', sc);
  paintStats();
  if($('shareMsg')) $('shareMsg').textContent='';
  var c=$('choices'); c.textContent='';
  var done=p&&p.done;
  r.choices.forEach(function(t,i){
    var b=document.createElement('button');
    b.type='button';
    b.className='choice';
    b.textContent=t;
    var picked=p&&p.tries&&p.tries.indexOf(i)>=0;
    if(done){
      b.disabled=true;
      if(i===r.answer_index) b.classList.add('right');
      else if(picked) b.classList.add('wrong');
    } else if(picked){
      b.disabled=true; b.classList.add('wrong');
    } else if(cur>today){
      b.disabled=true;
    } else {
      b.addEventListener('click', function(){guess(i)});
    }
    c.appendChild(b);
  });
  var why=$('whynot');
  if(why){
    if(p&&p.tries&&p.tries.length&&!done){
      why.hidden=false;
      why.textContent=WHY[(p.tries.length-1)%WHY.length];
    } else why.hidden=true;
  }
  var dots=$('dots');
  if(dots){
    dots.textContent='';
    var n=Math.min(R.length, today+1);
    for(var j=today-n+1;j<=today;j++){
      var dot=document.createElement('i');
      if(j===cur) dot.className='on';
      else if(S.ans[key(dateOf(j))]!=null) dot.className='done';
      dots.appendChild(dot);
    }
  }
  var rev=$('reveal');
  if(!done){
    rev.hidden=true;
    if(p&&p.tries&&p.tries.length) setBit('surprised');
    else setBit('thinking');
    return;
  }
  rev.hidden=false;
  var ok=!!p.ok;
  $('verdict').textContent=ok?'Yes! You fathomed it!':'Nice try — robots learn from mistakes too!';
  var line=(ok?(r.bit_line):(LEARNED[(p.tries.length)%LEARNED.length]))||'';
  $('bitLine').textContent=line;
  $('kept').textContent=cur===today?('🔥 Streak: '+S.streak+(S.streak===1?' day':' days')+'. A new riddle arrives tomorrow!'):'';
  var whoName=r.speaker==='fathom'?'Fathom':'Bit';
  var expl=$('explainer');
  expl.textContent='';
  var strong=document.createElement('b');
  strong.textContent=whoName+': ';
  expl.appendChild(strong);
  expl.appendChild(document.createTextNode(r.explainer));
  $('tryit').textContent=r.try_it||'';
  $('tryBox').hidden=!r.try_it;
  var src=$('src');
  src.textContent=r.source_title||'';
  if(r.source_url) src.href=r.source_url; else src.removeAttribute('href');
  src.parentNode.hidden=!r.source_title;
  setBit(ok?'happy':'curious');
  var who=$('whoBit');
  if(who) who.setAttribute('src', ok?POSE.happy:POSE.curious);
  renderGrid(r,p);
  if($('rise')&&ok&&cur===today) $('rise').textContent=String(S.streak);
}
function guess(i){
  if(cur>today) return;
  sync();
  var dkey=key(dateOf(cur)), r=rid(cur);
  var p=S.plays[dkey];
  if(p&&p.done){render(); return}
  if(p&&p.tries&&p.tries.indexOf(i)>=0) return;
  if(!p){p={id:r.id, tries:[], ok:false, t:Date.now(), done:false}; S.plays[dkey]=p}
  var first=p.tries.length===0;
  p.tries.push(i);
  var correct=i===r.answer_index;
  if(correct){p.ok=true; p.done=true}
  else if(p.tries.length>=maxTries(r)){p.ok=false; p.done=true}
  var milestone=false;
  if(cur===today && first){
    var l=lday(S.last);
    if(l===today){}
    else if(l===today-1) S.streak=S.streak+1;
    else S.streak=1;
    S.last=dkey;
    if(S.streak>S.best) S.best=S.streak;
    milestone=(S.streak===3||S.streak===7||S.streak===14);
  }
  syncAnsOn(S);
  save();
  render();
  var btn=$('choices').children[i];
  juice.press(btn);
  juice.sfx('tap');
  if(correct){
    juice.pop(btn); juice.pop($('bit')); juice.confetti($('card'));
    juice.sfx('correct');
    if(milestone) juice.sfx('streak'); else juice.sfx('finish');
    if(S.haptics) juice.haptic('ok');
    if(cur===today && $('rise')) juice.countUp($('rise'), S.streak);
  } else {
    juice.shake(btn);
    juice.sfx('wrong');
    if(p.done) juice.sfx('finish');
    if(S.haptics) juice.haptic('bad');
  }
}
function go(dl){
  var n=cur+dl;
  if(n>today||n<0||today-n>R.length-1) return;
  cur=n; render(); window.scrollTo(0,0);
}
function showTab(name){
  ['today','journal','grown'].forEach(function(id){var el=$(id); if(el) el.hidden=id!==name});
  document.querySelectorAll('nav button').forEach(function(b){
    if(b.getAttribute('data-tab')===name) b.setAttribute('aria-current','page');
    else b.removeAttribute('aria-current');
  });
  if(name==='journal') renderJournal();
  window.scrollTo(0,0);
}
function renderJournal(){
  var ul=$('histList'); if(!ul) return;
  ul.textContent='';
  var keys=Object.keys(S.plays).filter(function(k){return S.plays[k]&&S.plays[k].done&&kday(k)>=0&&kday(k)<=today});
  keys.sort(function(a,b){return kday(b)-kday(a)});
  if(!keys.length){
    var empty=document.createElement('li');
    empty.className='empty';
    empty.textContent='No riddles yet. Play today to start your journal.';
    ul.appendChild(empty); return;
  }
  keys.forEach(function(k){
    var p=S.plays[k], n=kday(k), r=rid(n);
    var li=document.createElement('li');
    var mark=document.createElement('b'); mark.textContent=p.ok?'🟩':'📘';
    var text=document.createElement('span');
    text.textContent=' #'+window.BFShare.pad(n+1)+' · '+(r.hook||r.title)+' · '+(p.ok?'Fathomed':'Learned');
    li.appendChild(mark); li.appendChild(text); ul.appendChild(li);
  });
}
function focusables(root){
  return Array.prototype.filter.call(root.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'), function(el){
    return !el.disabled && el.offsetParent!==null;
  });
}
function trapKey(e, root, closer){
  if(e.key==='Escape'){e.preventDefault(); closer(); return}
  if(e.key!=='Tab') return;
  var f=focusables(root); if(!f.length){e.preventDefault(); return}
  var first=f[0], last=f[f.length-1];
  if(e.shiftKey && document.activeElement===first){e.preventDefault(); last.focus()}
  else if(!e.shiftKey && document.activeElement===last){e.preventDefault(); first.focus()}
}
function openStats(){
  lastFocus=document.activeElement;
  paintBars();
  $('statsModal').hidden=false;
  $('statsX').focus();
}
function closeStats(){
  $('statsModal').hidden=true;
  if(lastFocus&&lastFocus.focus) lastFocus.focus();
  else if($('statsBtn')) $('statsBtn').focus();
}
var gAns=null, gAfter=null;
function openGate(after){
  var a=6+Math.floor(Math.random()*7), b=3+Math.floor(Math.random()*6);
  gAns=a*b; gAfter=after;
  $('gQ').textContent=a+' × '+b+' = ?';
  $('gA').value=''; $('gErr').textContent='';
  $('gate').hidden=false; $('gA').focus();
}
function closeGate(){
  $('gate').hidden=true; gAfter=null;
  var tab=$('tabToday'); if(tab) tab.focus();
}
function submitGate(){
  if(parseInt($('gA').value,10)===gAns){
    var fn=gAfter; $('gate').hidden=true; gAfter=null; grownOK=true; if(fn) fn();
  } else $('gErr').textContent='Not quite. Ask a grown-up.';
}
function wire(){
  $('prev').addEventListener('click', function(){go(-1)});
  $('next').addEventListener('click', function(){go(1)});
  $('share').addEventListener('click', function(){
    var t=shareText(), m=$('shareMsg');
    function copied(){m.textContent='Copied! Paste it anywhere'}
    var write=(navigator.clipboard&&navigator.clipboard.writeText)?navigator.clipboard.writeText(t):Promise.reject();
    var coarse=false; try{coarse=matchMedia('(pointer:coarse)').matches}catch(e){}
    if(coarse&&navigator.share){
      write.then(copied, function(){m.textContent=t});
      navigator.share({text:t}).catch(function(err){
        if(err&&err.name==='AbortError') return;
        write.then(copied, function(){m.textContent=t});
      });
    } else write.then(copied, function(){m.textContent=t});
  });
  $('statsBtn').addEventListener('click', openStats);
  $('statsX').addEventListener('click', closeStats);
  $('statsModal').addEventListener('keydown', function(e){trapKey(e, $('statsModal'), closeStats)});
  $('statsModal').addEventListener('click', function(e){if(e.target===$('statsModal')) closeStats()});
  function toggleSound(){S.sound=!S.sound; if(S.sound) juice.sound.on(); else juice.sound.off(); paintSound(); if(S.sound) juice.sfx('tap'); save()}
  $('soundBtn').addEventListener('click', toggleSound);
  if($('soundBtn2')) $('soundBtn2').addEventListener('click', toggleSound);
  if($('hapBtn')) $('hapBtn').addEventListener('click', function(){S.haptics=!S.haptics; paintHap(); save()});
  if($('resetBtn')) $('resetBtn').addEventListener('click', function(){
    if(!confirm('Erase streaks and journal on this device?')) return;
    var sound=S.sound, hap=S.haptics;
    S=blank(); S.sound=sound; S.haptics=hap; syncAnsOn(S); save(); location.reload();
  });
  document.querySelectorAll('nav button').forEach(function(b){
    b.addEventListener('click', function(){
      var name=b.getAttribute('data-tab');
      if(name==='grown' && !grownOK) openGate(function(){showTab('grown')});
      else showTab(name);
    });
  });
  $('gNo').addEventListener('click', closeGate);
  $('gGo').addEventListener('click', submitGate);
  $('gate').addEventListener('keydown', function(e){
    if(e.key==='Enter'&&e.target===$('gA')){e.preventDefault(); submitGate(); return}
    trapKey(e, $('gate'), closeGate);
  });
  document.addEventListener('keydown', function(e){
    if(e.key==='Escape'){
      if(!$('statsModal').hidden){closeStats(); return}
      if(!$('gate').hidden){closeGate(); return}
    }
    if(e.target&&(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')) return;
    if(!$('statsModal').hidden||!$('gate').hidden) return;
    if(e.key==='ArrowLeft') go(-1);
    if(e.key==='ArrowRight') go(1);
  });
  var sx=null, sy=0, card=$('card');
  card.addEventListener('touchstart', function(e){sx=e.touches[0].clientX; sy=e.touches[0].clientY},{passive:true});
  card.addEventListener('touchend', function(e){
    if(sx==null) return;
    var dx=e.changedTouches[0].clientX-sx, dy=e.changedTouches[0].clientY-sy; sx=null;
    if(Math.abs(dx)>60&&Math.abs(dx)>1.5*Math.abs(dy)) go(dx<0?1:-1);
  },{passive:true});
}
function start(data){
  R=(data.riddles||data).slice();
  OK=probe();
  today=Math.max(0, dayNum(new Date()));
  S=OK?load():blank();
  cur=today;
  sync();
  applyDeepLink();
  applySkipReset();
  notice();
  if(S.sound) juice.sound.on(); else juice.sound.off();
  paintSound(); paintHap();
  wire();
  render();
  armMidnight();
  if(window.BFCount) window.BFCount.startTicker({el:$('count'), liveEl:$('countLive')});
  if('serviceWorker' in navigator && location.protocol.indexOf('http')===0){
    window.addEventListener('load', function(){navigator.serviceWorker.register('sw.js').catch(function(){})});
  }
}
if(location.protocol==='file:'||location.hostname==='localhost'||location.hostname==='127.0.0.1'){
  window.__BF={
    getState:function(){return {streak:S.streak,best:S.best,last:S.last,ans:Object.assign({},S.ans),today:today,cur:cur,storage:OK}},
    dayNum:dayNum, key:key, dateOf:dateOf, rid:function(n){return rid(n)}, isEncore:isEncore,
    applySkipReset:applySkipReset, todayKey:todayKey, yesterdayKey:yesterdayKey, refreshDay:refreshDay, shareText:shareText,
    setState:function(o){
      if(o.streak!=null) S.streak=o.streak;
      if(o.best!=null) S.best=o.best;
      if('last' in o) S.last=o.last;
      if(o.ans){
        S.plays={};
        for(var k in o.ans){
          if(typeof o.ans[k]!=='number') continue;
          var nk=normKey(k)||k;
          var n=kday(nk);
          var r=rid(n);
          S.plays[nk]={id:r.id, tries:[o.ans[k]], ok:o.ans[k]===r.answer_index, t:0, done:true};
        }
      }
      syncAnsOn(S);
      if(OK){try{localStorage.setItem(K2, JSON.stringify(persist(S))); localStorage.setItem(K1, JSON.stringify(v1view(S)))}catch(e){}}
    },
    remount:function(){applySkipReset(); cur=today; render()}
  };
  window.__bf=window.__BF;
}
start(JSON.parse($('inline-riddles').textContent));
})();
