import json,re,sys
S=sys.argv[1];R='/home/user/trade-war-room'
P=json.load(open(S+'/players.json'))
ids=set()
for L in ['1349508410898399232','1349553170841374720']:
    for r in json.load(open(f'{S}/r_{L}.json')):
        for k in ('players','reserve','taxi'):
            ids.update(r.get(k) or [])
sl=set(i for i in ids if P.get(i) and P[i].get('position') in ('QB','RB','WR','TE'))
norm=lambda s:re.sub(r'[^a-z]','',re.sub(r'\b(jr|sr|ii|iii|iv)\b','',(s or '').lower()))
byname={}
for i,x in P.items():
    if x and x.get('position') in ('QB','RB','WR','TE'):byname.setdefault(norm(x.get('full_name')),[]).append(i)
yset=set();unm=[]
yl=json.load(open(R+'/yahoo_league.json'));yr=json.load(open(R+'/yahoo_roster.json'))
yp=[p for t in yl.get('teams',[]) for p in t.get('players',[])]
yp+= yr.get('players',[]) if isinstance(yr,dict) else yr
for p in yp:
    pos=(p.get('pos') or '').upper()
    if pos in ('K','DEF','DST'):continue
    sid=str(p.get('sleeperId') or '')
    if sid and sid in P: yset.add(sid);continue
    c=[i for i in byname.get(norm(p.get('name')),[]) if (P[i].get('team') or '')==(p.get('team') or '') or len(byname[norm(p.get('name'))])==1]
    if c: yset.add(c[0])
    else: unm.append(p.get('name'))
allids=sl|yset
out={i:{'name':P[i]['full_name'],'pos':P[i]['position'],'team':P[i].get('team'),'inj':P[i].get('injury_status')} for i in allids if P.get(i) and P[i].get('position') in ('QB','RB','WR','TE')}
json.dump(out,open(S+'/roster.json','w'))
def fmt(i):x=out[i];return f"{x['name']} ({x['team']},{i}{','+x['inj'] if x['inj'] else ''})"
grp={}
for i,x in sorted(out.items(),key=lambda k:k[1]['name']):grp.setdefault(x['pos'],[]).append(fmt(i))
wr=grp.get('WR',[]);h=len(wr)//2
for n,l in [('QBK',grp.get('QB',[])),('RB',grp.get('RB',[])),('WR1',wr[:h]),('WR2',wr[h:]),('TE',grp.get('TE',[]))]:
    open(f'{S}/list_{n}.txt','w').write('; '.join(l))
print('sleeper',len(sl),'yahoo',len(yset),'yahoo-only',len(yset-sl),'total',len(out),'unmatched',unm)
print({k:len(v) for k,v in grp.items()})
