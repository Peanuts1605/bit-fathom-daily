/* Countdown to the next local midnight. Ticks every second, pauses while hidden.
   The aria-live label changes when its sentence changes: once a minute until the
   last minute, then once a second. */
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
  function piece(n, one, many){return n+' '+(n===1?one:many)}
  function liveText(ms){
    if(ms<0) ms=0;
    if(ms<60000){
      var sec=Math.ceil(ms/1000);
      if(sec>=60) return 'Next riddle in 1 minute';
      if(sec<=0) return 'Next riddle in less than a minute';
      return 'Next riddle in '+piece(sec,'second','seconds');
    }
    var h=Math.floor(ms/3600000), m=Math.floor((ms%3600000)/60000);
    if(h===0) return 'Next riddle in '+piece(m,'minute','minutes');
    if(m===0) return 'Next riddle in '+piece(h,'hour','hours');
    return 'Next riddle in '+piece(h,'hour','hours')+' and '+piece(m,'minute','minutes');
  }
  function startTicker(opts){
    var timer=null, lastText='';
    function tick(){
      var ms=msUntilNextLocalMidnight(new Date());
      if(opts.el) opts.el.textContent=formatHMS(ms);
      if(opts.liveEl){
        var text=liveText(ms);
        if(text!==lastText){ lastText=text; opts.liveEl.textContent=text; }
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
  global.BFCount={msUntilNextLocalMidnight:msUntilNextLocalMidnight, formatHMS:formatHMS, liveText:liveText, startTicker:startTicker};
})(window);
