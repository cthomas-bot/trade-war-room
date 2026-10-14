const fs=require('fs');const E=require('./engine_live.js');
const PALL=JSON.parse(fs.readFileSync('players.json'));const players={};for(const [id,x] of Object.entries(PALL)){if(!x||!['QB','RB','WR','TE'].includes(x.position))continue;if(!x.team&&!x.injury_status)continue;players[id]={t:x.team||null,i:x.injury_status||null};}
const news=JSON.parse(fs.readFileSync('/home/user/trade-war-room/news.json'));const stats=[1,2,3,4,5].map(w=>JSON.parse(fs.readFileSync('stats_'+w+'.json')));
const L='1349553170841374720',rd=f=>JSON.parse(fs.readFileSync(L+'/'+f+'.json'));
const league=rd('league'),users=rd('users');const me=users.find(u=>u.display_name==='socasual').user_id;
const M=E.buildModel({league,rosters:rd('rosters'),users,tradedPicks:rd('traded_picks'),fc:JSON.parse(fs.readFileSync('fc_now.json')),stats,season:league.season,draftDone:true,myUserId:me,redraft:true,players,news});
const pts=id=>stats.map(s=>((s[id]||{}).pts_half_ppr||0)).reduce((a,b)=>a+b,0);
// RB2-caliber targets on other teams
for(const t of M.teams){if(t===M.me)continue;const rbs=t.assets.filter(a=>a.kind==='player'&&a.pos==='RB'&&a.value>=1500&&a.value<=6000&&!a.inj);const st=E.lineupDetail(t.assets,M.slots,'redraft').starters.map(a=>a.name);
 if(rbs.length)console.log(t.owner.padEnd(16),'RBs:',rbs.map(a=>a.name+' '+Math.round(a.value)+' ('+pts(a.id).toFixed(0)+'pts)'+(st.includes(a.name)?'*':'')).join(', '),'| WRs started:',t.assets.filter(a=>a.pos==='WR'&&st.includes(a.name)).map(a=>a.name).join('/'));}
const f=(t,n)=>t.assets.find(a=>a.name===n);const base=E.lineupDetail(M.me.assets,M.slots,'redraft').total;
const deals=process.argv.slice(2).map(s=>s.split('|'));
for(const [owner,g,r] of deals){const o=M.teams.find(t=>t.owner===owner);const give=g.split('+').map(n=>f(M.me,n)),get=r.split('+').map(n=>f(o,n));if(give.includes(undefined)||get.includes(undefined)){console.log('missing',g,r);continue;}
 const my=M.me.assets.filter(a=>!give.includes(a)).concat(get),op=o.assets.filter(a=>!get.includes(a)).concat(give);const ob=E.lineupDetail(o.assets,M.slots,'redraft').total;
 const dS=E.lineupDetail(my,M.slots,'redraft').total-base,oS=E.lineupDetail(op,M.slots,'redraft').total-ob;const raw=get.reduce((s,a)=>s+a.value,0)-give.reduce((s,a)=>s+a.value,0);
 console.log(owner,g,'->',r,'| me',(dS/M.avgStarter*100).toFixed(1)+'%','| them',(oS/M.avgStarter*100).toFixed(1)+'%','| raw',Math.round(raw),'| vals',get.map(a=>a.name+' '+Math.round(a.value)).join(', '));}
