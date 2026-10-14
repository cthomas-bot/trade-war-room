const fs=require('fs');const E=require('./engine_live.js');
const PALL=JSON.parse(fs.readFileSync('players.json'));const players={};for(const [id,x] of Object.entries(PALL)){if(!x||!['QB','RB','WR','TE'].includes(x.position))continue;if(!x.team&&!x.injury_status)continue;players[id]={t:x.team||null,i:x.injury_status||null};}
const news=JSON.parse(fs.readFileSync('/home/user/trade-war-room/news.json'));const stats=[1,2,3,4].map(w=>JSON.parse(fs.readFileSync('stats_'+w+'.json')));
for(const [L,fcf,red] of [['1349553170841374720','fc_now.json',true],['1349508410898399232','fcd_now.json',false]]){
const rd=f=>JSON.parse(fs.readFileSync(L+'/'+f+'.json'));
const league=rd('league'),users=rd('users');const me=users.find(u=>u.display_name==='socasual').user_id;
const M=E.buildModel({league,rosters:rd('rosters'),users,tradedPicks:rd('traded_picks'),fc:JSON.parse(fs.readFileSync(fcf)),stats,season:league.season,draftDone:true,myUserId:me,redraft:red,players,news});
const o=M.teams.find(t=>t.owner==='chaLee323');
const mode=red?'redraft':'dynasty';
console.log('\n=====',league.name,'| opp',o.name,'active',o.active,'/',o.limit,'| me active',M.me.active);
const show=t=>t.assets.filter(a=>a.kind==='player').sort((a,b)=>b.value-a.value).map(a=>a.pos+' '+a.name+' '+Math.round(a.value)+(a.inj?'['+a.inj+']':'')+(a.news?'{'+a.news.tag+'}':'')).join(', ');
console.log('THEM:',show(o));console.log('ME:',show(M.me));
const ld=E.lineupDetail(o.assets,M.slots,mode);console.log('their lineup',JSON.stringify(ld.slots?ld.slots.map(s=>s.slot+':'+(s.a?s.a.name:'-')):Object.keys(ld)));
const tr=E.generateTrades(M,{mode:'auto',aggr:'aggressive'}).filter(t=>t.opp===o||t.opp.rid===o.rid);
tr.forEach(t=>console.log('ENGINE',t.shape,'give',t.give.map(a=>a.name).join('+'),'get',t.get.map(a=>a.name).join('+'),'|',t.gainLine,'|',t.acceptLine));
global['M'+(red?'r':'d')]={M,o,mode};
}
