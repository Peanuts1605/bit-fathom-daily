/* Countdown to the next local midnight. Ticks every second, pauses while hidden.
   The aria-live label changes once a minute, not once a second. */
(function(global){
  function msUntilNextLocalMidnight(now){
    var n=now||new Date();
    var next=new Date(n.getFullYear(), n.getMonth(), n.getDate()+1, 0, 0, 0, 0);
    return next.getTime()-n.getTime();
  }
  function pad(x){return (x<10?'0':'')+x}
  function formatHMS(ms){
    if(ms<0) ms=0;
    var s=Math.floor(ms/1000);
    return pad(Math.floor(s/3600))+':'+pad(Math.floor((s%3600)/60))+':'+pad(s%60);
  }
  function startTicker(opts){
    var timer=null, lastMin=-1;
    function tick(){
      var ms=msUntilNextLocalMidnight(new Date());
      if(opts.el) opts.el.textContent=formatHMS(ms);
      var minute=Math.floor(ms/60000);
      if(opts.liveEl && minute!==lastMin){
        lastMin=minute;
        var h=Math.floor(ms/3600000), m=Math.floor((ms%3600000)/60000);
        opts.liveEl.textContent='Next riddle in '+h+' hours and '+m+' minutes';
      }
    }
    function stop(){if(timer){clearInterval(timer); timer=null}}
    function arm(){
      stop();
      tick();
      if(document.hidden) return;
      timer=setInterval(tick,1000);
    }
    document.addEventListener('visibilitychange', function(){if(document.hidden) stop(); else arm()});
    arm();
    return {stop:stop, tick:tick, arm:arm};
  }
  global.BFCount={msUntilNextLocalMidnight:msUntilNextLocalMidnight, formatHMS:formatHMS, startTicker:startTicker};
})(window);
