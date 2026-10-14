// Runs the engine against the real Sleeper leagues for every team and checks the rules.
const fs=require('fs');const path=require('path');
const D=__dirname;
const enginePath=process.argv[2]||path.join(D,'engine.js');
const E=require(enginePath);
const PALL=JSON.parse(fs.readFileSync(path.join(D,'players.json')));
const news=JSON.parse(fs.readFileSync('/home/user/trade-war-room/news.json'));
const stats=[1,2,3].map(w=>JSON.parse(fs.readFileSync(path.join(D,'stats_'+w+'.json'))));
// Stand-in for FantasyCalc (blocked here): value curve from Sleeper search_rank, age-adjusted for dynasty
function fcProxy(dynasty,sf){
  const ps=Object.entries(PALL).filter(([id,x])=>x&&['QB','RB','WR','TE'].includes(x.position)&&x.search_rank&&x.search_rank<2000)
    .sort((a,b)=>a[1].search_rank-b[1].search_rank);
  const out=ps.map(([id,x],i)=>{
    let v=10000*Math.exp(-i/60);
    if(x.position==='QB')v*=sf?1.5:.55;
    if(x.position==='TE')v*=.85;
    let dv=v;const age=x.age||26;
    if(dynasty){dv*=age<=23?1.3:age<=25?1.15:age>=31?.55:age>=29?.75:1;}
    v=Math.min(v,11000);dv=Math.min(dv,11000);
    return {player:{name:x.full_name,position:x.position,sleeperId:id,maybeAge:x.age,maybeTeam:x.team},value:Math.round(dynasty?dv:v),redraftValue:Math.round(v),trend30Day:0};
  });
  if(dynasty)for(const y of [2027,2028,2029])for(const [r,v] of [[1,5200],[2,2300],[3,1100]])out.push({player:{name:y+' '+['','1st','2nd','3rd'][r],position:'PICK'},value:Math.round(v*Math.pow(.95,y-2027))});
  return out;
}
const players={};for(const [id,x] of Object.entries(PALL)){if(!x||!['QB','RB','WR','TE'].includes(x.position))continue;if(!x.team&&!x.injury_status)continue;players[id]={t:x.team||null,i:x.injury_status||null,d:x.depth_chart_order||null};}
const fails=[];const summary=[];const examples=[];
let total=0,n31=0,shapes={};
for(const lid of ['1349508410898399232','1349553170841374720']){
  const rd=f=>JSON.parse(fs.readFileSync(path.join(D,lid,f+'.json')));
  const league=rd('league'),rosters=rd('rosters'),users=rd('users'),tradedPicks=rd('traded_picks');
  const redraft=!(league.settings&&(league.settings.type===1||league.settings.type===2));
  const rp=league.roster_positions;const sf=rp.includes('SUPER_FLEX');
  const fc=fcProxy(!redraft,sf);
  for(const r of rosters){
    const uid=r.owner_id;if(!uid)continue;
    for(const mode of (redraft?['auto']:['auto','contend','rebuild']))for(const aggr of ['balanced','aggressive','max']){
      const t0=Date.now();
      const M=E.buildModel({league,rosters,users,tradedPicks,fc,stats,season:league.season,draftDone:true,myUserId:uid,redraft,players,news});
      const trades=E.generateTrades(M,{mode,aggr});
      const ms=Date.now()-t0;
      const me=M.me;const tag=league.name+' | '+me.name+' | '+mode+'/'+aggr;
      // boards: no hurt/demoted targets
      for(const x of M.boards.targets){if(x.p.hurt||x.p.demoted||x.p.inj)fails.push(tag+' TARGET hurt/demoted: '+x.p.name+' '+x.p.inj);}
      for(const x of M.boards.sells){if(x.p.hurt)fails.push(tag+' SELL-HIGH hurt: '+x.p.name);}
      for(const tr of trades){
        total++;shapes[tr.shape]=(shapes[tr.shape]||0)+1;
        // 1) nothing I receive is injured / Out / demoted
        for(const a of tr.get){if(a.kind==='player'&&(a.inj||a.hurt||a.demoted))fails.push(tag+' receives hurt/demoted '+a.name+' ('+a.inj+')');
          const st=players[a.id];if(a.kind==='player'&&st&&st.i)fails.push(tag+' receives Sleeper-injured '+a.name+' '+st.i);
          const nw=news.players.find(n=>n.sleeperId===a.id);if(nw&&(nw.status||nw.redraftAdj<1))fails.push(tag+' receives news-flagged '+a.name+' '+nw.status+' '+nw.redraftAdj);}
        // 2) roster legality using raw Sleeper rosters
        const opp=tr.opp;
        const rawMe=rosters.find(x=>x.owner_id===uid),rawOpp=rosters.find(x=>x.roster_id===opp.rid);
        const act=(raw,ids)=>ids.filter(id=>!(raw.reserve||[]).includes(id)&&!(raw.taxi||[]).includes(id));
        const gIds=tr.give.filter(a=>a.kind==='player').map(a=>a.id),rIds=tr.get.filter(a=>a.kind==='player').map(a=>a.id),dIds=tr.drops.map(a=>a.id);
        const meAfter=act(rawMe,rawMe.players).filter(id=>!gIds.includes(id)&&!dIds.includes(id)).length+rIds.length;
        const oppAfter=act(rawOpp,rawOpp.players).filter(id=>!rIds.includes(id)).length+gIds.length;
        if(meAfter>rp.length)fails.push(tag+' my roster over limit '+meAfter+'/'+rp.length);
        if(oppAfter>rp.length)fails.push(tag+' opp roster over limit '+oppAfter+'/'+rp.length);
        for(const id of gIds)if(!rawMe.players.includes(id))fails.push(tag+' give not on my roster '+id);
        for(const id of rIds)if(!rawOpp.players.includes(id))fails.push(tag+' get not on opp roster '+id);
        for(const d of tr.drops)if(d.starter||d.value>=700)fails.push(tag+' bad drop '+d.name);
        // 3) consolidation premium
        const bG=Math.max(...tr.give.map(a=>a.value)),bR=Math.max(...tr.get.map(a=>a.value));
        if(bR>bG&&tr.give.length>tr.get.length&&tr.gv<tr.rv*1.079)fails.push(tag+' consolidation: gave '+tr.give.length+' for stud without premium');
        if(bG>bR&&tr.get.length>tr.give.length&&tr.rv<tr.gv*1.079)fails.push(tag+' consolidation: sold stud for pieces without premium');
        if(tr.shape==='3x1'){n31++;if(tr.dS<.01||tr.newStarters.length<2)fails.push(tag+' unjustified 3x1');}
        if(!['1x1','2x1','1x2','2x2','3x1'].includes(tr.shape))fails.push(tag+' odd shape '+tr.shape);
        if(!tr.gainLine||!tr.acceptLine)fails.push(tag+' missing lines');
        if(aggr==='aggressive'&&mode==='auto')examples.push({tag,league:league.name,team:me.name,opp:opp.name,shape:tr.shape,give:tr.give.map(a=>a.name+' ('+a.value+')'),get:tr.get.map(a=>a.name+' ('+a.value+')'),drops:tr.drops.map(a=>a.name),gain:tr.gainLine,accept:tr.acceptLine,acc:tr.accept,rank:+tr.rank.toFixed(4)});
      }
      const per31=trades.filter(t=>t.shape==='3x1').length;if(per31>1)fails.push(tag+' more than one 3x1');
      // ranking order
      for(let i=1;i<trades.length;i++)if(trades[i].rank>trades[i-1].rank+1e-12)fails.push(tag+' not ranked');
      summary.push({tag,n:trades.length,ms,t:M.boards.targets.length,s:M.boards.sells.length,o:M.boards.offload.length});
    }
  }
}
console.log('runs',summary.length,'trades',total,'shapes',JSON.stringify(shapes),'3x1',n31);
console.log('zero-trade runs',summary.filter(s=>!s.n).length,'max ms',Math.max(...summary.map(s=>s.ms)),'avg trades',(total/summary.length).toFixed(2));
console.log('boards avg targets/sells/offload',['t','s','o'].map(k=>(summary.reduce((a,s)=>a+s[k],0)/summary.length).toFixed(1)).join('/'));
console.log('FAILS',fails.length);fails.slice(0,40).forEach(f=>console.log('  ',f));
fs.writeFileSync(path.join(D,'examples.json'),JSON.stringify(examples,null,1));
fs.writeFileSync(path.join(D,'summary.json'),JSON.stringify(summary,null,1));
