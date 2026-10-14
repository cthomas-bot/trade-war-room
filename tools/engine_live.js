
/* ================= TRADE ENGINE (pure functions) ================= */
const POS=['QB','RB','WR','TE'];
const SLOT_ELIG={QB:['QB'],RB:['RB'],WR:['WR'],TE:['TE'],FLEX:['RB','WR','TE'],WRRB_FLEX:['RB','WR'],REC_FLEX:['WR','TE'],SUPER_FLEX:['QB','RB','WR','TE']};
const AGE_CLIFF={QB:33,RB:27,WR:29,TE:30};
let REDRAFT=false;
// long absences only: a one-week "Out" isn't a dead roster spot
const INJ_ADJ_OUT={IR:1,PUP:1,NFI:1,Sus:1};
// any injury designation: never recommend these as targets
const HURT=new Set(['IR','Out','Doubtful','Questionable','PUP','NFI','Sus','NA','COV','DNR']);
// consolidation premium: value is compared as sum of (v/1000)^CONS_P, so one stud beats several average players
const CONS_P=1.5;
const SHAPE_MULT={'1x1':1,'2x1':.92,'1x2':.9,'2x2':.82,'3x1':.7};
const SHAPE_ORDER=['1x1','2x1','1x2','2x2','3x1'];
const SIMPLE_KEEP=.65;

function cv(vals){return vals.reduce((s,v)=>s+Math.pow(Math.max(0,v)/1000,CONS_P),0);}
function sortSlots(slots){return slots.filter(s=>SLOT_ELIG[s]).sort((a,b)=>SLOT_ELIG[a].length-SLOT_ELIG[b].length);}
function lineupDetail(players,slots,key){
  const av=players.filter(p=>p.kind==='player'&&POS.includes(p.pos)).sort((a,b)=>b[key]-a[key]);
  const used=new Array(av.length).fill(false);let total=0,filled=0;const starters=[];
  for(const s of slots){const el=SLOT_ELIG[s];for(let i=0;i<av.length;i++){if(!used[i]&&el.includes(av[i].pos)){used[i]=true;total+=av[i][key];filled++;starters.push(av[i]);break;}}}
  return {total,filled,starters};
}
function lineup(players,slots,key){return lineupDetail(players,slots,key).total;}
function ageFactor(a){
  if(REDRAFT)return 1;
  if(a.kind==='pick')return 1.08;
  const age=a.age;if(!age)return 1;
  const c=AGE_CLIFF[a.pos]||30;
  if(age<=23)return 1.18; if(age<=25)return 1.08; if(age<c-1)return 1;
  if(age<c)return .85; return .62;
}
function futureVal(assets){return assets.reduce((s,a)=>s+a.value*ageFactor(a),0);}
function isOld(a){return a.kind==='player'&&a.age&&a.age>=(AGE_CLIFF[a.pos]||30);}
function isYoung(a){return a.kind==='pick'||(a.age&&a.age<=24);}
function shortNote(s,n){s=String(s||'').replace(/\s+/g,' ').trim();n=n||110;return s.length>n?s.slice(0,n-1).replace(/[\s,;:.]+\S*$/,'')+'…':s;}

function buildModel(d){
  // d: {league, rosters, users, tradedPicks, fc, stats, season, draftDone, myUserId, redraft, players, news}
  REDRAFT=!!d.redraft;
  const L=d.league, nTeams=L.total_rosters||d.rosters.length;
  const rp=L.roster_positions||[];
  const slots=sortSlots(rp);
  const rosterLimit=rp.length; // starters + bench (IR and taxi are separate)
  const nQb=rp.filter(s=>s==='QB').length+(rp.includes('SUPER_FLEX')?1:0);
  const ptsKey=(L.scoring_settings&&L.scoring_settings.rec)>=1?'pts_ppr':(L.scoring_settings&&L.scoring_settings.rec)>0?'pts_half_ppr':'pts_std';
  const fcBy={},pickVals={};
  for(const e of d.fc){
    const p=e.player||{};
    if(p.position==='PICK'){
      const m=(p.name||'').match(/(\d{4})\s+(?:Round\s+(\d)|Pick\s+(\d)\.\d+|(\d)(?:st|nd|rd|th))/i);
      if(m){const k=m[1]+'-'+(m[2]||m[3]||m[4]);(pickVals[k]=pickVals[k]||{gen:null,list:[]});
        if(m[2]||m[4])pickVals[k].gen=e.value;else pickVals[k].list.push(e.value);}
      continue;
    }
    if(p.sleeperId)fcBy[String(p.sleeperId)]={name:p.name,pos:p.position,age:p.maybeAge?Math.floor(p.maybeAge):null,team:p.maybeTeam||'FA',
      value:e.value||0,redraft:REDRAFT?(e.value||0):(e.redraftValue??e.value??0),trend:e.trend30Day||0,posRank:e.positionRank,rank:e.overallRank};
  }
  const fallbackPick={1:5200,2:2300,3:1100,4:550,5:300};
  function pickValue(season,round){
    const k=season+'-'+round,pv=pickVals[k];
    if(pv){if(pv.gen)return pv.gen;if(pv.list.length)return pv.list.reduce((a,b)=>a+b,0)/pv.list.length;}
    const yrs=Object.keys(pickVals).filter(x=>x.endsWith('-'+round)).map(x=>+x.split('-')[0]).sort();
    if(yrs.length){const y=yrs[yrs.length-1];return pickValue(y,round)*Math.pow(.95,Math.max(0,season-y));}
    return fallbackPick[round]||200;
  }
  const userBy={};for(const u of d.users)userBy[u.user_id]=u;
  const teams=d.rosters.map(r=>{
    const u=userBy[r.owner_id]||{};
    const name=(u.metadata&&u.metadata.team_name)||u.display_name||('Team '+r.roster_id);
    const res=new Set(r.reserve||[]),taxi=new Set(r.taxi||[]);
    const ids=r.players||[];
    const players=ids.map(id=>{const f=fcBy[id];return f?{kind:'player',id,...f,onIR:res.has(id),onTaxi:taxi.has(id)}:null;}).filter(Boolean);
    const st=r.settings||{};
    return {rid:r.roster_id,ownerId:r.owner_id,owner:u.display_name||name,name,players,picks:[],
      wins:st.wins||0,losses:st.losses||0,ties:st.ties||0,fpts:(st.fpts||0)+(st.fpts_decimal||0)/100,
      unvalued:ids.length-players.length,
      limit:rosterLimit,active:ids.filter(id=>!res.has(id)&&!taxi.has(id)).length};
  });
  const byRid={};teams.forEach(t=>byRid[t.rid]=t);
  // --- news overlay, injuries, usage (applied before strength calc) ---
  const norm=x=>(x||'').toLowerCase().replace(/[^a-z]/g,'').replace(/(jr|sr|ii|iii|iv)$/,'');
  const newsBy={};for(const n of ((d.news&&d.news.players)||[])){if(n.sleeperId)newsBy['id:'+n.sleeperId]=n;if(n.name)newsBy['nm:'+norm(n.name)]=n;}
  const PL=d.players||{};const weeks0=d.stats||[];
  const teamOf=id=>(PL[id]&&PL[id].t)||(fcBy[id]&&fcBy[id].team);
  const teamTgt=weeks0.map(w=>{const t={};for(const [id,st] of Object.entries(w)){const tm=teamOf(id);if(tm&&st&&st.rec_tgt)t[tm]=(t[tm]||0)+st.rec_tgt;}return t;});
  const INJ_ADJ={IR:.6,PUP:.6,NFI:.7,Sus:.8};
  teams.forEach(t=>t.players.forEach(p=>{
    const sp=PL[p.id];if(sp){p.inj=sp.i||null;p.depth=sp.d||null;if(sp.t)p.team=sp.t;}
    const n=newsBy['id:'+p.id]||newsBy['nm:'+norm(p.name)];
    if(n){p.news=n;
      const ra=n.redraftAdj??1,da=n.dynastyAdj??1;
      if(REDRAFT){p.value*=ra;p.redraft*=ra;}else{p.value*=da;p.redraft*=ra;}
      if(n.status)p.inj=n.status;
    }else if(p.inj&&INJ_ADJ[p.inj]){p.redraft*=INJ_ADJ[p.inj];if(REDRAFT)p.value*=INJ_ADJ[p.inj];}
    // usage over recent weeks
    const snaps=[],tsh=[],yds=[];let tdPts=0,allPts=0,tds=0;
    weeks0.forEach((w,i)=>{const st=w[p.id];if(!st)return;
      if(st.tm_off_snp>0&&st.off_snp!=null)snaps.push(st.off_snp/st.tm_off_snp);
      const tt=teamTgt[i][p.team];if(tt&&st.rec_tgt!=null)tsh.push(st.rec_tgt/tt);
      if(st.rec_yd!=null||st.rush_yd!=null||st.pass_yd!=null)yds.push((st.rec_yd||0)+(st.rush_yd||0)+(p.pos==='QB'?(st.pass_yd||0):0));
      const td=(st.rec_td||0)+(st.rush_td||0);tds+=td;tdPts+=td*6+(p.pos==='QB'?(st.pass_td||0)*4:0);allPts+=st[ptsKey]||0;});
    const avg=a=>a.length?a.reduce((x,y)=>x+y,0)/a.length:null;
    p.snap=avg(snaps);p.tgtShare=avg(tsh);p.yds=avg(yds);
    p.tdShare=p.pos!=='QB'&&tds>=2&&allPts>=20?tdPts/allPts:null;
    if(snaps.length>=2){p.snapLast=snaps[snaps.length-1];const pr=avg(snaps.slice(0,-1));p.snapPrior=pr;p.snapDelta=p.snapLast-pr;}
    const tag=n&&n.tag;
    p.roleUp=tag==='role_up'||(tag!=='role_down'&&p.snapDelta!=null&&p.snapDelta>=.15&&p.snapLast>=.55&&p.snapPrior<.6);
    // a snap drop only means a demotion when the player isn't hurt
    p.roleDown=tag==='role_down'||(tag!=='role_up'&&tag!=='injury'&&!p.inj&&p.snapDelta!=null&&p.snapDelta<=-.15);
    p.hurt=!!((p.inj&&HURT.has(p.inj))||(n&&n.status));
    p.demoted=p.roleDown||!!(n&&n.tag!=='injury'&&(n.redraftAdj??1)<1);
    // a role bump that only exists because someone else is hurt
    p.tempRole=!!(n&&n.tag==='role_up'&&/\b(while|until|with\b.{0,40}\b(out|sidelined|hurt|injured|on IR)|in place of|fill-?in|returns?)\b/i.test(n.note||''));
    // healthy again but still priced off an injury
    p.injDiscount=!!(n&&n.tag==='injury'&&!n.status&&(n.redraftAdj??1)>=.97);
  }));
  // strength first (for pick slot adjustment)
  teams.forEach(t=>{t.starter=lineup(t.players,slots,'redraft');t.starterDyn=lineup(t.players,slots,'value');});
  const sRank=[...teams].sort((a,b)=>b.starter-a.starter);sRank.forEach((t,i)=>t.starterRank=i+1);
  // picks
  const rounds=(L.settings&&L.settings.draft_rounds)||4;
  const base=+d.season;const seasons=[];if(!d.draftDone)seasons.push(base);for(let i=1;i<=3;i++)seasons.push(base+i);
  const own={};
  for(const s of seasons)for(let r=1;r<=rounds;r++)for(const t of teams)own[s+'-'+r+'-'+t.rid]=t.rid;
  for(const tp of d.tradedPicks||[]){const k=tp.season+'-'+tp.round+'-'+tp.roster_id;if(k in own)own[k]=tp.owner_id;}
  if(!REDRAFT)for(const [k,ownerRid] of Object.entries(own)){
    const [s,r,orig]=k.split('-').map(Number);const holder=byRid[ownerRid],origT=byRid[orig];if(!holder||!origT)continue;
    let v=pickValue(s,r);
    if(s<=base+1&&r<=2){const pct=origT.starterRank/nTeams;v*=pct<=.34?.85:pct>.66?1.15:1;}
    const ord=['','1st','2nd','3rd','4th','5th','6th'][r]||r+'th';
    holder.picks.push({kind:'pick',id:k,name:s+' '+ord+(orig!==ownerRid?' ('+origT.name+')':''),pos:'PICK',season:s,round:r,value:Math.round(v),redraft:0,age:null,trend:0});
  }
  // recent performance signals
  const weeks=d.stats||[];
  teams.forEach(t=>{
    t.players.forEach(p=>{
      if(weeks.length>=2){
        const last=(weeks[weeks.length-1][p.id]||{})[ptsKey];
        const prior=weeks.slice(0,-1).map(w=>(w[p.id]||{})[ptsKey]).filter(x=>x!=null);
        if(last!=null&&prior.length){p.lastWk=last;p.avgPrior=prior.reduce((a,b)=>a+b,0)/prior.length;}
      }
      const tp=p.value?p.trend/p.value:0;p.trendPct=tp;
      p.downWeek=p.avgPrior>=9&&p.lastWk!=null&&p.lastWk<p.avgPrior*.6;
      p.spikeWeek=p.avgPrior>=5&&p.lastWk!=null&&p.lastWk>p.avgPrior*1.7;
      p.tdLuck=p.tdShare!=null&&p.tdShare>=.45;
      p.buyLow=p.value>=1200&&!isOld(p)&&!p.hurt&&!p.demoted&&(tp<=-.06||p.downWeek||p.injDiscount||(p.roleUp&&tp<.05));
      p.sellHigh=p.value>=1200&&!p.hurt&&(tp>=.07||p.spikeWeek||p.tdLuck||p.tempRole);
      if(p.sellHigh)p.buyLow=false; // one call per player: a borrowed or inflated role is a sell, not a buy
      p.ageCliff=!REDRAFT&&isOld(p)&&p.value>=1500;
      p.nearCliff=!REDRAFT&&!!p.age&&p.age>=(AGE_CLIFF[p.pos]||30)-1&&p.value>=2000;
    });
    t.assets=[...t.players,...t.picks];
    t.total=t.assets.reduce((s,a)=>s+a.value,0);
    t.future=futureVal(t.assets);
    const g=t.wins+t.losses+t.ties;t.winPct=g?(t.wins+t.ties*.5)/g:null;
    t.baseL=lineupDetail(t.assets,slots,'redraft');
    const ss=new Set(t.baseL.starters.map(p=>p.id));t.players.forEach(p=>p.starter=ss.has(p.id));
  });
  const tRank=[...teams].sort((a,b)=>b.total-a.total);tRank.forEach((t,i)=>t.totalRank=i+1);
  // positional strength & needs
  const need={QB:Math.max(1,nQb),RB:3,WR:4,TE:1};
  for(const pos of POS){
    teams.forEach(t=>{t['ps_'+pos]=t.players.filter(p=>p.pos===pos).sort((a,b)=>b.redraft-a.redraft).slice(0,need[pos]).reduce((s,p)=>s+p.redraft,0);});
    [...teams].sort((a,b)=>b['ps_'+pos]-a['ps_'+pos]).forEach((t,i)=>t['pr_'+pos]=i+1);
  }
  teams.forEach(t=>{
    t.needs=POS.filter(p=>t['pr_'+p]>nTeams*.6);
    t.surplus=POS.filter(p=>t['pr_'+p]<=Math.ceil(nTeams*.25));
    const sPct=1-(t.starterRank-1)/Math.max(1,nTeams-1);
    const c=t.winPct==null?sPct:.6*sPct+.4*t.winPct;t.contendScore=c;
    t.mode=REDRAFT?'contend':c>=.6?'contend':c<=.38?'rebuild':'fringe';
    t.baseF=futureVal(t.assets);
  });
  const me=teams.find(t=>t.ownerId===d.myUserId);
  const avgStarter=teams.reduce((s,t)=>s+t.starter,0)/teams.length||1;
  const avgFuture=teams.reduce((s,t)=>s+t.future,0)/teams.length||1;
  const M={teams,me,slots,nTeams,nQb,avgStarter,avgFuture,ptsKey,rounds,redraft:REDRAFT,rosterLimit,yahoo:!!d.yahoo,market:!!d.market};
  M.boards=me?tradeBoards(M):{targets:[],sells:[],offload:[]};
  return M;
}

/* Targets (their players to buy), Sell-highs and Offload (mine) */
function tradeBoards(M){
  REDRAFT=!!M.redraft;
  const me=M.me,pc=x=>Math.round(x*100)+'%';
  const targets=[];
  const vals=M.teams.flatMap(t=>t.players.map(p=>p.value)).sort((a,b)=>b-a);const elite=vals[Math.min(vals.length-1,M.nTeams)]||Infinity;
  for(const o of M.teams){if(o===me)continue;
    for(const p of o.players){
      if(p.hurt||p.demoted||p.sellHigh||p.tempRole||p.value<800)continue;
      if(!REDRAFT&&isOld(p))continue;
      const add=lineup(me.assets.concat([p]),M.slots,'redraft')-me.baseL.total;
      let why=null,kind=null;
      const newsBacked=p.news&&(p.news.tag==='role_up'||p.injDiscount);
      if(p.value>=elite&&!newsBacked)continue;
      if(p.roleUp){kind='Rising role';why=p.news&&p.news.tag==='role_up'?shortNote(p.news.note):'Snaps up to '+pc(p.snapLast)+' last week'+(p.tgtShare?' with a '+pc(p.tgtShare)+' target share':'')+' — the market hasn’t caught up.';}
      else if(p.injDiscount){kind='Injury discount';why='Healthy again, but his price still reflects the injury'+(p.news.note?': '+shortNote(p.news.note,80):'.');}
      else if(p.downWeek){kind='Buy low';why='Down week ('+p.lastWk.toFixed(1)+' vs '+p.avgPrior.toFixed(1)+' avg) — the manager may sell cheap.';}
      else if(p.trendPct<=-.06){kind='Buy low';why='Value down '+Math.abs(Math.round(p.trendPct*100))+'% in 30 days with his role intact.';}
      else if(!M.market&&!p.starter&&o.surplus.includes(p.pos)&&add>0){kind='Stuck on a deep roster';why='Benched behind '+o.name+'’s deep '+p.pos+' room — he’d start for you.';}
      if(!why)continue;
      const score=p.value*(1+(add>0?.35:0)+(me.needs.includes(p.pos)?.25:0)+(p.roleUp?.15:0));
      targets.push({p,owner:o,kind,why,add,score});
    }
  }
  targets.sort((a,b)=>b.score-a.score);
  const sells=[];
  for(const p of me.players){
    if(p.hurt||p.value<1000)continue;
    let why=null,kind=null;
    if(p.tempRole){kind='Borrowed role';why='His bump depends on a teammate being out: '+shortNote(p.news.note,90);}
    else if(p.tdLuck){kind='Touchdown luck';why=pc(p.tdShare)+' of his recent points came from touchdowns — that rarely holds.';}
    else if(p.spikeWeek){kind='Hot streak';why='Just scored '+p.lastWk.toFixed(1)+' vs a '+p.avgPrior.toFixed(1)+' average — sell into the headline.';}
    else if(p.trendPct>=.07){kind='Value peak';why='Up '+Math.round(p.trendPct*100)+'% in 30 days — near his ceiling price.';}
    else if(!REDRAFT&&(p.ageCliff||p.nearCliff)){kind='Age cliff';why='Age '+p.age+' '+p.pos+' — still valued as a starter, but the decline is close.';}
    if(!why)continue;
    sells.push({p,kind,why});
  }
  sells.sort((a,b)=>b.p.value-a.p.value);
  const offload=[];
  const selling=new Set(sells.map(x=>x.p));
  const lowCut=REDRAFT?650:900;
  for(const p of me.players){
    if(selling.has(p))continue;
    let why=null,kind=null,pri=0;
    if(p.demoted){kind='Role shrinking';pri=3;why=p.news&&p.news.tag!=='injury'?shortNote(p.news.note):'Snap share falling'+(p.snapLast!=null?' ('+pc(p.snapLast)+' last week)':'')+' — move him before his value follows.';}
    else if(REDRAFT&&p.hurt&&(INJ_ADJ_OUT[p.inj]||(p.news&&(p.news.redraftAdj??1)<=.7))){kind='Dead roster spot';pri=2;why='Out for a long stretch — '+(p.news?shortNote(p.news.note,80):'listed '+p.inj+'.');}
    else if(!REDRAFT&&p.ageCliff&&(p.trendPct<0||p.hurt||M.me.mode!=='contend')){kind='Past the cliff';pri=2;why='Age '+p.age+(p.trendPct<0?' and his value is already sliding':' and his value only drops from here')+' — package him while he still has some.';}
    else if(!p.starter&&!p.roleUp&&!p.onTaxi&&p.value<lowCut&&p.value>=150){kind='Bench filler';pri=1;why='Not starting for you and low value — use him as a throw-in.';}
    if(!why)continue;
    p.offload=true;
    offload.push({p,kind,why,pri});
  }
  offload.sort((a,b)=>b.pri-a.pri||b.p.value-a.p.value);
  return {targets:targets.slice(0,10),sells:sells.slice(0,8),offload:offload.slice(0,8)};
}

function teamWeights(mode){return REDRAFT?[.75,.25]:mode==='contend'?[.6,.4]:mode==='rebuild'?[.15,.85]:[.4,.6];}
function canReceive(a){return a.kind==='pick'||(!a.hurt&&!a.demoted);}

function generateTrades(M,opts){
  const me=M.me;if(!me)return [];
  REDRAFT=!!M.redraft;
  const mode=M.redraft?'contend':opts.mode==='auto'?me.mode:opts.mode;
  const W=teamWeights(mode);
  // minMv: least consolidated value the other manager accepts; maxMv: most we overpay
  const band={balanced:{minMv:.98,maxMv:1.15,minU:.006,edgeW:.15},aggressive:{minMv:.94,maxMv:1.1,minU:0,edgeW:.3},max:{minMv:.9,maxMv:1.06,minU:-.006,edgeW:.45}}[opts.aggr]||{minMv:.94,maxMv:1.1,minU:0,edgeW:.3};
  const locked=opts.locked||new Set(),only=opts.only||null;
  const pool=me.assets.filter(a=>a.value>=250&&!locked.has(a.id)).sort((a,b)=>b.value-a.value).slice(0,18);
  me.assets.filter(a=>a.offload&&a.value>=150&&!locked.has(a.id)&&!pool.includes(a)).forEach(a=>pool.push(a));
  const pkgs=[];
  for(let i=0;i<pool.length;i++){pkgs.push([pool[i]]);
    for(let j=i+1;j<pool.length;j++){pkgs.push([pool[i],pool[j]]);
      const top=Math.min(12,pool.length);if(j<top)for(let k=j+1;k<top;k++)pkgs.push([pool[i],pool[j],pool[k]]);}}
  pkgs.forEach(g=>{g.raw=g.reduce((s,a)=>s+a.value,0);g.cons=cv(g.map(a=>a.value));});
  // my spare bench players I could cut to make room (never starters, never valuable)
  const dropMax=REDRAFT?700:600;
  const myDroppable=me.players.filter(p=>!p.starter&&!p.onIR&&!p.onTaxi&&p.value<dropMax).sort((a,b)=>a.value-b.value);
  const activeOut=g=>g.filter(a=>a.kind==='player'&&!a.onIR&&!a.onTaxi).length;
  const nPlayers=g=>g.filter(a=>a.kind==='player').length;
  const best={};
  for(const opp of M.teams){if(opp===me||(only&&opp.rid!==only.rid))continue;
    const Wo=teamWeights(opp.mode);
    const recv=opp.assets.filter(a=>canReceive(a)&&a.value>=300);
    const targets=only?recv.filter(a=>a.id===only.id):recv.filter(a=>a.value>=700&&(REDRAFT?true:!(mode==='rebuild'&&isOld(a)))).map(a=>{
      const add=a.kind==='player'?lineup(me.assets.concat([a]),M.slots,'redraft')-me.baseL.total:0;
      let s=a.value*(1+Math.max(0,add)/(M.avgStarter*.05));
      if(a.buyLow)s*=1.15;if(a.roleUp)s*=1.1;
      if(mode==='contend'&&a.kind==='pick')s*=.4;
      if(mode==='rebuild')s*=ageFactor(a);
      return {a,s};}).sort((x,y)=>y.s-x.s).slice(0,8).map(x=>x.a);
    for(const t of targets){
      const gets=[[t]];
      recv.filter(x=>x!==t&&x.value<=t.value&&x.value>=Math.max(500,t.value*.2)).sort((a,b)=>b.value-a.value).slice(0,6).forEach(s=>gets.push([t,s]));
      for(const get of gets){
        const rR=get.reduce((s,a)=>s+a.value,0),rC=cv(get.map(a=>a.value));
        const bestGet=Math.max(...get.map(a=>a.value));
        for(const give of pkgs){
          const shape=give.length+'x'+get.length;
          if(!SHAPE_MULT[shape])continue;
          const mv=give.cons/rC; // what they receive vs give, in consolidated value
          if(mv<band.minMv||mv>band.maxMv)continue;
          const gR=give.raw;
          // consolidation premium: the side taking more players must get clearly more raw value
          const bestGive=Math.max(...give.map(a=>a.value));
          if(bestGet>bestGive&&give.length>get.length&&gR<rR*(1+.08*(give.length-get.length)))continue;
          if(bestGive>bestGet&&get.length>give.length&&rR<gR*(1+.08*(get.length-give.length)))continue;
          // roster legality: no one over the limit (I may cut spare bench players; they never have to)
          const oppDelta=nPlayers(give)-activeOut(get);
          if(opp.active+oppDelta>opp.limit)continue;
          const myDelta=nPlayers(get)-activeOut(give);
          const over=me.active+myDelta-me.limit;
          let drops=[];
          if(over>0){drops=myDroppable.filter(p=>!give.includes(p)).slice(0,over);if(drops.length<over)continue;}
          const myAfter=me.assets.filter(x=>!give.includes(x)&&!drops.includes(x)).concat(get);
          const oppAfter=opp.assets.filter(x=>!get.includes(x)).concat(give);
          const myL=lineupDetail(myAfter,M.slots,'redraft'),oL=lineupDetail(oppAfter,M.slots,'redraft');
          // both teams must still field a full lineup
          if(myL.filled<Math.min(M.slots.length,me.baseL.filled)||oL.filled<Math.min(M.slots.length,opp.baseL.filled))continue;
          const dS=(myL.total-me.baseL.total)/M.avgStarter,dF=(futureVal(myAfter)-me.baseF)/M.avgFuture;
          const myGain=W[0]*dS+W[1]*dF;
          if(myGain<.004)continue;
          if(mode==='contend'&&dS<0)continue;
          if(!M.redraft&&mode==='contend'&&dF<-.03)continue;
          if(mode==='rebuild'&&dF<=0)continue;
          const oDS=(oL.total-opp.baseL.total)/M.avgStarter,oDF=(futureVal(oppAfter)-opp.baseF)/M.avgFuture;
          const oppU=Wo[0]*oDS+Wo[1]*oDF+(mv-1)*.25;
          if(oppU<band.minU)continue;
          const newStarters=give.filter(a=>oL.starters.includes(a));
          // there has to be a reason for them to say yes: a lineup hole filled, youth for a rebuilder, or a clear value win
          const hook=oDS>.004||(!M.redraft&&opp.mode==='rebuild'&&oDF>.004)||mv>=1.04;
          if(!hook)continue;
          if(shape==='3x1'){
            // rare: only when I have the depth, my lineup clearly improves, and they need bodies at those spots
            if(dS<.01||newStarters.length<2||oppDelta<2)continue;
          }
          const edge=(rC-give.cons)/rC;
          let sig=0;
          get.forEach(x=>{if(x.buyLow)sig+=.004;if(x.roleUp)sig+=.004;if(x.sellHigh)sig-=.004;});
          give.forEach(x=>{if(x.sellHigh)sig+=.004;if(x.offload)sig+=.005;if(x.buyLow)sig-=.004;if(x.ageCliff&&mode!=='contend')sig+=.003;});
          const accept=Math.max(10,Math.min(92,Math.round(55+oppU*700+(mv-1)*120)));
          const rank=(myGain+sig+band.edgeW*edge*.05)*SHAPE_MULT[shape]*(.6+accept/250);
          if(rank<=0)continue;
          const key=opp.rid+'|'+t.id+'|'+shape;
          if(!best[key]||best[key].rank<rank)best[key]={opp,give,get,drops,gv:gR,rv:rR,gc:give.cons,rc:rC,mv,dS,dF,oDS,oDF,oppU,edge,accept,rank,mode,shape,newStarters,myGain,myAfter,myL};
        }
      }
    }
  }
  // per target, keep the simplest deal that is nearly as good as the best one (1-for-1 beats a 2-for-2 that adds little)
  const byTarget={};
  for(const tr of Object.values(best)){const k=tr.opp.rid+'|'+tr.get[0].id;(byTarget[k]=byTarget[k]||[]).push(tr);}
  let list=Object.values(byTarget).map(c=>{
    const top=Math.max(...c.map(x=>x.rank));
    return c.filter(x=>x.rank>=top*SIMPLE_KEEP).sort((a,b)=>SHAPE_ORDER.indexOf(a.shape)-SHAPE_ORDER.indexOf(b.shape)||b.rank-a.rank)[0];
  }).sort((a,b)=>b.rank-a.rank);
  if(only){list.forEach(tr=>{tr.gainLine=gainLine(tr,M);tr.acceptLine=acceptLine(tr,M);tr.reasons=explain(tr,M);});return list;}
  // at most 2 per opponent, one 3-for-1 at most, no reused give-asset among the top 3, no asset offered more than twice
  const perOpp={},usedGive=new Set(),giveCount={},out=[];let n31=0;
  for(const tr of list){
    if((perOpp[tr.opp.rid]||0)>=2)continue;
    if(tr.shape==='3x1'&&n31>=1)continue;
    if(out.length<3&&tr.give.some(g=>usedGive.has(g.id)))continue;
    if(tr.give.some(g=>(giveCount[g.id]||0)>=2))continue;
    if(out.some(o=>o.opp===tr.opp&&o.get.some(x=>tr.get.includes(x))))continue;
    out.push(tr);perOpp[tr.opp.rid]=(perOpp[tr.opp.rid]||0)+1;tr.give.forEach(g=>{usedGive.add(g.id);giveCount[g.id]=(giveCount[g.id]||0)+1;});if(tr.shape==='3x1')n31++;
    if(out.length>=8)break;
  }
  out.forEach(tr=>{tr.gainLine=gainLine(tr,M);tr.acceptLine=acceptLine(tr,M);tr.reasons=explain(tr,M);});
  return out;
}

function gainLine(tr,M){
  const pct=x=>(x>=0?'+':'')+(x*100).toFixed(1)+'%';
  const d=Math.round(tr.rv-tr.gv);
  return 'Starting lineup '+pct(tr.dS)+' · '+(M.redraft?'roster depth ':'long-term value ')+pct(tr.dF)+' · raw value '+(d>=0?'+':'−')+Math.abs(d).toLocaleString();
}
function acceptLine(tr,M){
  const o=tr.opp,bits=[];
  if(tr.oDS>.004){const ps=[...new Set(tr.newStarters.map(x=>x.pos))];bits.push('it fills their '+(ps.join('/')||'lineup')+' hole (their lineup +'+(tr.oDS*100).toFixed(1)+'%)');}
  if(!M.redraft&&o.mode==='rebuild'&&tr.give.some(isYoung))bits.push('a rebuilding team gets younger');
  if(tr.give.length<tr.get.length)bits.push('they consolidate into the best player in the deal');
  else if(tr.give.length>tr.get.length)bits.push('they turn one roster spot into '+tr.give.length+' useful pieces');
  if(tr.gv>=tr.rv)bits.push('they get more total value ('+Math.round(tr.gv).toLocaleString()+' vs '+Math.round(tr.rv).toLocaleString()+')');
  else if(tr.mv>=1)bits.push('they win on consolidated value');
  return bits.length?bits[0].charAt(0).toUpperCase()+bits.slice(0,2).join(', and ').slice(1)+'.':'Close to even on value and fits their roster.';
}

function explain(tr,M){
  const r=[],me=M.me,o=tr.opp;
  tr.get.forEach(x=>{
    if(x.news&&x.news.note)r.push(x.name+': '+x.news.note);
    else if(x.roleUp&&x.snapDelta>=.12)r.push(x.name+'’s role is growing: '+Math.round(x.snapLast*100)+'% of snaps last week. Buy before the market catches up.');
    else if(x.downWeek)r.push(x.name+' just had a down week ('+x.lastWk.toFixed(1)+' vs '+x.avgPrior.toFixed(1)+' avg). Buy before he bounces.');
    else if(x.buyLow&&x.trendPct<=-.06)r.push(x.name+' has dropped '+Math.abs(Math.round(x.trendPct*100))+'% in value over 30 days — buy-low window.');
    if(x.kind==='player'&&me.needs.includes(x.pos))r.push('Fills a weak spot: '+x.pos+' (you rank '+me['pr_'+x.pos]+' of '+M.nTeams+').');
  });
  tr.give.forEach(x=>{
    if(x.news&&x.news.note)r.push('Selling '+x.name+': '+x.news.note);
    else if(x.tdLuck)r.push('Selling '+x.name+' while touchdowns ('+Math.round(x.tdShare*100)+'% of his points) prop up his value.');
    else if(x.spikeWeek)r.push('Selling '+x.name+' right after a spike week ('+x.lastWk.toFixed(1)+' pts).');
    else if(x.sellHigh)r.push(x.name+' is up '+Math.round(x.trendPct*100)+'% in 30 days — sell at the top.');
    else if(x.roleDown)r.push(x.name+'’s snaps are falling — move him before his value does.');
    if(x.ageCliff)r.push(x.name+' is '+x.age+' — past the '+x.pos+' age cliff.');
  });
  if(tr.drops.length)r.push('To stay at the roster limit, drop '+tr.drops.map(x=>x.name).join(' and ')+' (bench, low value).');
  else if(tr.get.length<tr.give.length)r.push('Opens '+(tr.give.length-tr.get.length)+' roster spot'+(tr.give.length-tr.get.length>1?'s':'')+' for a waiver add.');
  return [...new Set(r)].slice(0,5);
}

/* Buy-low game plan: the best offer from my roster for each target on the board */
const AGGR_STEPS=['balanced','aggressive','max'];
function targetPlans(M,opts){
  const out=[];
  for(const t of (M.boards.targets||[]).slice(0,6)){
    let trade=null,stretch=false;const start=Math.max(0,AGGR_STEPS.indexOf(opts.aggr));
    for(let i=start;i<AGGR_STEPS.length&&!trade;i++){
      const list=generateTrades(M,{...opts,aggr:AGGR_STEPS[i],only:{rid:t.owner.rid,id:t.p.id}});
      if(list.length){trade=list[0];stretch=i>start;}
    }
    out.push({target:t,trade,stretch});
  }
  return out;
}

/* What a trade really does to my roster, with an unvarnished verdict */
function consequences(tr,M){
  const me=M.me,lines=[],risks=[];
  const pct=x=>(x>=0?'+':'')+(x*100).toFixed(1)+'%';
  const nm=a=>a.name+' ('+a.pos+')';
  const before=me.baseL.starters,after=tr.myL.starters;
  const bI=new Set(before.map(p=>p.id)),aI=new Set(after.map(p=>p.id));
  const ins=after.filter(p=>!bI.has(p.id)),outs=before.filter(p=>!aI.has(p.id));
  if(ins.length)lines.push('Lineup: '+ins.map(nm).join(', ')+(ins.length>1?' start':' starts')+(outs.length?' in place of '+outs.map(nm).join(', '):'')+'. Weekly lineup strength '+pct(tr.dS)+(tr.dS<-.005?' — you give up some strength now for the future':'')+'.');
  else lines.push('Your starting lineup doesn’t change — this is a '+(M.redraft?'depth':'depth and long-term')+' move.');
  // depth: bench players at each position involved who could start in a pinch
  const allStarters=M.teams.flatMap(t=>t.baseL.starters);
  const poss=[...new Set([...tr.give,...tr.get].filter(a=>a.kind==='player').map(a=>a.pos))];
  for(const p of poss){
    const sv=allStarters.filter(x=>x.pos===p).map(x=>x.redraft).sort((a,b)=>a-b);
    const floor=(sv[Math.floor(sv.length/2)]||0)*.45;
    const bench=(set,st)=>set.filter(x=>x.kind==='player'&&x.pos===p&&!st.has(x.id)&&!x.hurt&&x.redraft>=floor).length;
    const b0=bench(me.players,bI),b1=bench(tr.myAfter,aI);
    if(b0!==b1)lines.push('Usable '+p+' backups: '+b0+' → '+b1+'.');
    if(b1===0&&b0>0&&after.some(x=>x.pos===p))risks.push('No real '+p+' backup afterward — one injury and you’re starting a waiver pickup.');
  }
  // roster spots
  const nP=g=>g.filter(a=>a.kind==='player').length;
  const open=nP(tr.give)-nP(tr.get);
  if(tr.drops.length)lines.push('Roster spots: you’d have to drop '+tr.drops.map(x=>x.name).join(' and ')+'.');
  else if(open>0)lines.push('Roster spots: opens '+open+' — use '+(open>1?'them':'it')+' on the best waiver add at your thinnest spot.');
  else if(open<0)lines.push('Roster spots: uses '+(-open)+' open spot'+(open<-1?'s':'')+'.');
  // consolidation check
  if(tr.give.length>tr.get.length){
    const star=tr.get.reduce((a,b)=>b.value>a.value?b:a);
    if(star.kind==='player'&&!aI.has(star.id))risks.push(star.name+' wouldn’t start for you — that’s giving up depth for a bench player.');
    else lines.push('Consolidation: '+tr.give.length+' pieces become 1 better starter. Fewer bodies, stronger lineup.');
  }else if(tr.get.length>tr.give.length)lines.push('Depth play: you split one asset into '+tr.get.length+' pieces.');
  // long-term
  if(!M.redraft){
    const avgAge=g=>{const a=g.filter(x=>x.kind==='player'&&x.age).map(x=>x.age);return a.length?a.reduce((s,v)=>s+v,0)/a.length:null;};
    const ag=avgAge(tr.give),ar=avgAge(tr.get);
    lines.push('Long-term value '+pct(tr.dF)+(ag&&ar&&Math.abs(ag-ar)>=.5?'; you get '+Math.abs(ag-ar).toFixed(1)+' years '+(ar<ag?'younger':'older')+' on average':'')+'.');
    const picks=tr.give.filter(a=>a.kind==='pick');
    if(picks.length)lines.push('Draft capital out: '+picks.map(a=>a.name).join(', ')+'.');
    tr.get.forEach(x=>{if(x.kind==='player'&&(isOld(x)||x.nearCliff))risks.push(x.name+' is '+x.age+' — '+x.pos+' value falls fast around '+AGE_CLIFF[x.pos]+'.');});
  }
  // concentration
  const tot=tr.myAfter.reduce((s,a)=>s+a.value,0)||1;
  const top=tr.get.reduce((a,b)=>b.value>a.value?b:a);
  if(top.value/tot>=.3)risks.push(top.name+' would be '+Math.round(top.value/tot*100)+'% of your total value — a lot riding on one player.');
  // helping a rival
  if(tr.opp.starterRank<=3&&tr.oDS>.015)risks.push('It makes '+tr.opp.name+' (a top-3 lineup) stronger: their lineup '+pct(tr.oDS)+'.');
  const g=tr.myGain;let verdict,tone;
  if(g>=.03&&!risks.length){verdict='Strong yes';tone='up';}
  else if(g>=.015){verdict=risks.length?'Yes, with a catch':'Yes';tone=risks.length?'gold':'up';}
  else{verdict=risks.length>=2?'Pass unless you need it':'Small edge';tone=risks.length>=2?'down':'gold';}
  return {verdict,tone,lines,risks};
}
if(typeof module!=='undefined')module.exports={buildModel,generateTrades,tradeBoards,targetPlans,consequences,cv,lineup,lineupDetail};
