/* Local shim for Tinker's juice kit. Swap this file for experiments/_shared/juice.js later.
   Web Audio only, after the first call (a user gesture). No bare sine oscillators. */
(function(global){
  var soundOn=true, reduced=false, ac=null, canvas=null, raf=0;
  function syncMotion(){
    try{reduced=matchMedia('(prefers-reduced-motion: reduce)').matches}catch(e){reduced=false}
    juice.reducedMotion=reduced;
  }
  function ctx(){
    if(ac) return ac;
    var C=global.AudioContext||global.webkitAudioContext;
    if(!C) return null;
    ac=new C();
    juice._audio=true;
    return ac;
  }
  function tone(type,freq,t,dur,peak,cut){
    var a=ctx(); if(!a) return;
    var o=a.createOscillator(), f=a.createBiquadFilter(), g=a.createGain();
    o.type=type;
    o.frequency.setValueAtTime(freq,t);
    f.type='lowpass';
    f.frequency.setValueAtTime(cut||1800,t);
    f.Q.value=0.6;
    g.gain.setValueAtTime(0.0001,t);
    g.gain.exponentialRampToValueAtTime(Math.max(0.0002,peak), t+0.018);
    g.gain.exponentialRampToValueAtTime(0.0001, t+dur);
    o.connect(f); f.connect(g); g.connect(a.destination);
    o.start(t); o.stop(t+dur+0.02);
  }
  function play(name){
    if(!soundOn) return;
    var a=ctx(); if(!a) return;
    if(a.state==='suspended'){try{a.resume()}catch(e){}}
    var t=a.currentTime+0.01;
    if(name==='tap'){
      tone('triangle',740,t,0.05,0.04,2200);
    } else if(name==='wrong'){
      tone('sawtooth',311,t,0.14,0.045,900);
      tone('triangle',220,t+0.09,0.2,0.06,700);
    } else if(name==='correct'){
      [261.63,329.63,392,523.25].forEach(function(f,i){tone('triangle',f,t+i*0.09,0.26,0.1,2400)});
    } else if(name==='finish'){
      tone('triangle',392,t+0.32,0.16,0.07,2000);
      tone('sawtooth',392,t+0.32,0.16,0.02,1100);
      tone('triangle',523.25,t+0.46,0.3,0.1,2400);
    } else if(name==='streak'){
      [261.63,329.63,392,523.25,659.25,783.99,1046.5].forEach(function(f,i){
        tone('triangle',f,t+i*0.07,0.24,0.09,2600);
        if(i%2===0) tone('sawtooth',f,t+i*0.07,0.12,0.02,1400);
      });
    }
  }
  function burst(origin){
    if(reduced) return;
    if(canvas&&canvas.parentNode) canvas.parentNode.removeChild(canvas);
    canvas=document.createElement('canvas');
    canvas.className='juice-confetti';
    canvas.width=global.innerWidth;
    canvas.height=global.innerHeight;
    document.body.appendChild(canvas);
    var g=canvas.getContext('2d');
    var colors=['#2CC6C3','#F2C14E','#F2795E','#F4FCFC','#7FE7FF','#5BE3A8'];
    var rect=origin&&origin.getBoundingClientRect?origin.getBoundingClientRect():{left:canvas.width/2,top:canvas.height/3,width:0,height:0};
    var x0=rect.left+rect.width/2, y0=rect.top+rect.height/3;
    var bits=[];
    for(var i=0;i<70;i++){
      var ang=Math.random()*Math.PI*2, sp=3+Math.random()*7;
      bits.push({x:x0,y:y0,vx:Math.cos(ang)*sp,vy:Math.sin(ang)*sp-4,w:6+Math.random()*6,h:8+Math.random()*8,c:colors[i%colors.length],r:Math.random()*6,vr:(Math.random()-.5)*.4,life:1});
    }
    var start=performance.now();
    cancelAnimationFrame(raf);
    function frame(now){
      var k=(now-start)/900;
      g.clearRect(0,0,canvas.width,canvas.height);
      var alive=false;
      bits.forEach(function(b){
        b.vy+=0.18; b.x+=b.vx; b.y+=b.vy; b.r+=b.vr; b.life=1-k;
        if(b.life<=0) return;
        alive=true;
        g.save(); g.translate(b.x,b.y); g.rotate(b.r); g.globalAlpha=Math.max(0,b.life);
        g.fillStyle=b.c; g.fillRect(-b.w/2,-b.h/2,b.w,b.h); g.restore();
      });
      if(alive&&k<1) raf=requestAnimationFrame(frame);
      else if(canvas&&canvas.parentNode) canvas.parentNode.removeChild(canvas);
    }
    raf=requestAnimationFrame(frame);
  }
  var juice={
    reducedMotion:false,
    _audio:false,
    sound:{
      on:function(){soundOn=true},
      off:function(){soundOn=false}
    },
    press:function(el){
      if(!el) return;
      el.classList.add('is-down');
      setTimeout(function(){el.classList.remove('is-down')},100);
    },
    pop:function(el){
      if(!el) return;
      el.classList.remove('juice-pop');
      if(reduced){el.classList.add('juice-flash'); return}
      void el.offsetWidth;
      el.classList.add('juice-pop');
    },
    shake:function(el){
      if(!el) return;
      el.classList.remove('juice-shake'); el.classList.remove('juice-flash');
      void el.offsetWidth;
      el.classList.add(reduced?'juice-flash':'juice-shake');
    },
    confetti:function(el){if(!reduced) burst(el)},
    countUp:function(el,n){
      if(!el) return;
      n=n|0;
      if(reduced){el.textContent=String(n); return}
      var from=0, start=performance.now(), dur=420;
      function step(t){
        var k=Math.min(1,(t-start)/dur);
        var eased=1-Math.pow(1-k,3);
        el.textContent=String(Math.round(from+(n-from)*eased));
        if(k<1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    },
    sfx:function(name){try{play(name)}catch(e){}},
    haptic:function(kind){
      try{
        if(!navigator.vibrate) return;
        if(kind==='ok') navigator.vibrate(15);
        else navigator.vibrate([30,40,30]);
      }catch(e){}
    }
  };
  syncMotion();
  try{
    var mq=matchMedia('(prefers-reduced-motion: reduce)');
    if(mq.addEventListener) mq.addEventListener('change',syncMotion);
    else if(mq.addListener) mq.addListener(syncMotion);
  }catch(e){}
  global.juice=juice;
})(window);
