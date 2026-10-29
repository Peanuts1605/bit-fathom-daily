/* On-device stats. Distribution: 1st / 2nd / 3rd try, and Learned (not ok). */
(function(global){
  function aggregate(state, api){
    var played=0, wins=0, dist=[0,0,0,0];
    var plays=state.plays||{};
    for(var k in plays){
      var n=api.kday(k);
      if(!(n>=0)||n>api.today) continue;
      var p=plays[k];
      if(!p||!p.done) continue;
      played++;
      if(p.ok){
        wins++;
        var len=(p.tries&&p.tries.length)||1;
        var b=len<=1?0:len===2?1:2;
        dist[b]++;
      } else dist[3]++;
    }
    return {
      played:played,
      wins:wins,
      winPct:played?Math.round(100*wins/played):0,
      streak:state.streak|0,
      best:state.best|0,
      dist:dist
    };
  }
  global.BFStats={aggregate:aggregate};
})(window);
