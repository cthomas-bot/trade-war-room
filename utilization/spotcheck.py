"""Compare our computed metrics with numbers Fantasy Life published (Week 11 articles, Nov 16-19 2026).
Update CHECKS with fresh FL numbers each week you want to re-verify."""
import sys, json, os, pandas as pd, numpy as np
sys.argv=['x']; import build_utilization as b
g,_,_=b.build(2026,'.cache',4)
def S(weeks): return b.summarize(g,weeks).set_index('name')
w10=S([10]); dg=S([7,8,9,10]); se=S(range(1,11))
WIN={id(w10):'Week 10',id(dg):'Weeks 7-10',id(se):'Season (Wk 1-10)'}
cols=['snap_pct','route_part','tgt','tgt_share','tprr','ay','ay_share','rush_share','i5_share']
checks=[  # (window df, name, metric, FL value)
 (w10,'Josh Downs','route_part',.21),(w10,'Josh Downs','tprr',.63),(w10,'Josh Downs','tgt',5),
 (w10,'Jordyn Tyson','route_part',.72),(w10,'Jordyn Tyson','tgt_share',.42),(w10,'Jordyn Tyson','tgt',13),(w10,'Jordyn Tyson','ay',82),
 (w10,'Nico Collins','route_part',.90),(w10,'Nico Collins','tgt_share',.46),(w10,'Nico Collins','ay_share',.40),
 (w10,'Xavier Worthy','route_part',.97),(w10,'Xavier Worthy','tgt_share',.09),
 (w10,'Justin Jefferson','tgt',13),(w10,'George Pickens','ay_share',.52),
 (w10,'Cam Skattebo','snap_pct',.89),(w10,'Cam Skattebo','rush_share',.78),(w10,'Cam Skattebo','route_part',.57),(w10,'Cam Skattebo','tgt_share',.12),
 (w10,'Zach Charbonnet','snap_pct',.73),(w10,'Zach Charbonnet','rush_share',.67),(w10,'Zach Charbonnet','route_part',.68),
 (w10,'Bhayshul Tuten','snap_pct',.71),(w10,'Bhayshul Tuten','rush_share',.76),
 (w10,'Jonathan Taylor','rush_share',.53),(w10,'Jonathan Taylor','route_part',.80),(w10,'Jonathan Taylor','tgt_share',.18),
 (w10,'Tony Pollard','snap_pct',.72),(w10,'Tony Pollard','rush_share',.64),(w10,'Tony Pollard','route_part',.49),(w10,'Tony Pollard','tgt_share',.26),
 (w10,'Breece Hall','snap_pct',.59),(w10,'Breece Hall','route_part',.48),
 (dg,'Caleb Douglas','route_part',.83),(dg,'Caleb Douglas','ay_share',.43),(se,'Caleb Douglas','tgt_share',.22),
 (se,'DJ Moore','yprr',2.48),(se,'DJ Moore','tgt_share',.23),
]
rows=[]
for df,n,m,v in checks:
    ours=df.loc[n,m] if n in df.index else np.nan
    if isinstance(ours,pd.Series): ours=ours.iloc[0]
    rows.append(dict(key=f'{n}|{m}|{WIN[id(df)]}',player=n,window=WIN[id(df)],metric=m,fantasy_life=v,ours=round(float(ours),3) if pd.notna(ours) else None,
                     diff=round(float(ours)-v,3) if pd.notna(ours) else None))
r=pd.DataFrame(rows); print(r.to_string()); r.to_csv('data/spotcheck.csv',index=False)
r['status']=np.where(r.ours.isna(),'not reproducible',np.where(r['diff'].abs()<=0.05,'match',np.where(r['diff'].abs()<=0.10,'close','off')))
r.loc[r.metric.isin(['tgt','ay']),'status']=np.where(r.loc[r.metric.isin(['tgt','ay']),'diff'].abs()<=5,'match','off')
json.dump({'rows':json.loads(r.to_json(orient='records')),'meta':[{'label':'FL source','value':'fantasylife.com Week 11 Utilization Report takeaways, WR upgrades, Start/Sit (Nov 16-19, 2026)'},{'label':'spotcheck.py','value':open(os.path.abspath(__file__)).read(),'type':'code','lang':'python'}]},open('data/spotcheck.json','w'))
