/* Spoiler-free Wordle-style share grid. No answer text, no choice text, no option letters. */
(function(global){
  var EMOJI={
    Robots:'🤖', Electricity:'⚡', Space:'🚀', Computers:'💻', Learning:'🧠',
    Weather:'⛈️', Earth:'🧭', Time:'⏱️', Moon:'🌙', Light:'🌈', Sound:'🔊',
    Magnetism:'🧭', AI:'🧠', Colors:'🌈'
  };
  function emoji(topic){return EMOJI[topic]||'🔬'}
  function pad(n){n=String(n); while(n.length<3) n='0'+n; return n}
  function shareGrid(state, cur, api){
    var r=api.rid(cur);
    var num=pad(cur+1);
    var play=state.plays[api.key(api.dateOf(cur))];
    var max=api.maxTries(r);
    var cells='', frac='';
    if(play&&play.tries&&play.tries.length&&play.done){
      if(play.ok){
        for(var i=0;i<play.tries.length-1;i++) cells+='🟥';
        cells+='🟩';
        frac=play.tries.length+'/'+max;
      } else {
        for(var j=0;j<play.tries.length;j++) cells+='🟥';
        cells+='📘';
      }
    }
    var week='';
    for(var d=cur-6; d<=cur; d++){
      if(d<0){week+='⬜'; continue}
      var p=state.plays[api.key(api.dateOf(d))];
      if(!p||!p.done) week+='⬜';
      else if(!p.ok) week+='📘';
      else if(!p.tries||p.tries.length<=1) week+='🟩';
      else week+='🟨';
    }
    var tail=(cur===api.today)?('🔥 '+state.streak):'(archive)';
    var row=cells+(frac?('  '+frac):'');
    var origin=api.origin||'';
    return 'Bit & Fathom Daily #'+num+' '+emoji(r.topic)+'\n'+row+'\nThis week '+week+'  '+tail+'\n'+origin+'/r/'+num+'/';
  }
  global.BFShare={shareGrid:shareGrid, emoji:emoji, pad:pad};
})(window);
