"""Build managers.json: how each league manager trades, from Sleeper history.

Stats (record, trades, waiver moves) are recomputed every run. Hand-kept fields per
manager -- notes, rules, rejected -- are carried over from the existing file.

  rules:    {"keepRBDepth": true}  never sends two RBs in one deal
            {"needsNowGain": true} only takes deals that help their lineup this week
  rejected: [{"date","give":[my ids],"get":[their ids]}]  offers they turned down
"""
import json, os, sys, urllib.request

LEAGUES = ['1349553170841374720', '1349508410898399232']
OUT = os.path.join(os.path.dirname(__file__), '..', 'managers.json')
API = 'https://api.sleeper.app/v1'


def get(path):
    with urllib.request.urlopen(API + path, timeout=30) as r:
        return json.load(r)


def season_activity(lid):
    """Per user_id: trades, waiver/FA moves, and trade partners for one league season."""
    rosters, users = get(f'/league/{lid}/rosters'), get(f'/league/{lid}/users')
    owner = {r['roster_id']: r['owner_id'] for r in rosters}
    act = {u['user_id']: {'trades': 0, 'moves': 0, 'partners': []} for u in users}
    for w in range(1, 19):
        try:
            txs = get(f'/league/{lid}/transactions/{w}')
        except Exception:
            continue
        for t in txs:
            if t['status'] != 'complete':
                continue
            ids = [owner.get(r) for r in t['roster_ids']]
            for i, uid in enumerate(ids):
                a = act.setdefault(uid, {'trades': 0, 'moves': 0, 'partners': []})
                if t['type'] == 'trade':
                    a['trades'] += 1
                    a['partners'] += [x for x in ids if x != uid]
                elif t['type'] in ('waiver', 'free_agent'):
                    a['moves'] += 1
    return rosters, users, act


def rate(n):
    return 'never' if n == 0 else 'rare' if n <= 1 else 'active' if n <= 3 else 'very active'


def build(lid, old):
    league = get(f'/league/{lid}')
    rosters, users, now = season_activity(lid)
    prev = {}
    if league.get('previous_league_id'):
        _, _, prev = season_activity(league['previous_league_id'])
    ranked = sorted(rosters, key=lambda r: (-r['settings']['wins'], -(r['settings']['fpts'] + r['settings'].get('fpts_decimal', 0) / 100)))
    rank = {r['owner_id']: i + 1 for i, r in enumerate(ranked)}
    n = len(rosters)
    playoff = league['settings'].get('playoff_teams') or 6
    names = {u['user_id']: u for u in users}
    out = {}
    for r in rosters:
        uid, s = r['owner_id'], r['settings']
        u = names.get(uid, {})
        a, p = now.get(uid, {}), prev.get(uid)
        total = a.get('trades', 0) + (p['trades'] if p else 0)
        seasons = 2 if p else 1
        rk = rank[uid]
        stance = 'contender' if rk <= 3 else 'bubble' if rk <= playoff else 'desperate' if rk > n - 3 else 'chaser'
        keep = (old.get(uid) or {})
        out[uid] = {
            'name': u.get('display_name'),
            'team': (u.get('metadata') or {}).get('team_name') or u.get('display_name'),
            'record': f"{s['wins']}-{s['losses']}",
            'rank': rk,
            'stance': stance,
            'trades': {'season': a.get('trades', 0), 'last': p['trades'] if p else None},
            'moves': a.get('moves', 0),
            'tradeRate': rate(total / seasons),
            'partners': sorted(set(a.get('partners', []) + (p['partners'] if p else []))),
            'notes': keep.get('notes', []),
            'rules': keep.get('rules', {}),
            'rejected': keep.get('rejected', []),
        }
    return out


def main():
    old = {}
    if os.path.exists(OUT):
        old = json.load(open(OUT)).get('leagues', {})
    res = {}
    for lid in LEAGUES:
        try:
            res[lid] = build(lid, old.get(lid, {}))
        except Exception as e:
            print('skip', lid, e, file=sys.stderr)
            if lid in old:
                res[lid] = old[lid]
    # people behave the same across leagues: rate trading on every league they're in
    seen = {}
    for m in res.values():
        for uid, x in m.items():
            t = seen.setdefault(uid, [0, 0])
            t[0] += x['trades']['season'] + (x['trades']['last'] or 0)
            t[1] += 1 + (x['trades']['last'] is not None)
    for m in res.values():
        for uid, x in m.items():
            x['tradeRate'] = rate(seen[uid][0] / seen[uid][1])
    from datetime import datetime, timezone
    json.dump({'updated': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'leagues': res}, open(OUT, 'w'), indent=1, ensure_ascii=False)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
