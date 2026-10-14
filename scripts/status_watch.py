#!/usr/bin/env python3
"""Hourly, free status watch for rostered players.

Compares Sleeper's live injury status, team and QB1 depth-chart spot for every
player rostered in the leagues below (plus the Yahoo league files) against the last
snapshot. Any change becomes an entry in news.json, so the site reacts within
the hour without waiting for the daily research run. Standard library only.
"""
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

LEAGUES = ["1349508410898399232", "1349553170841374720"]
SLEEPER = "https://api.sleeper.app/v1"
NEWS = "news.json"
SNAPSHOT = "status_snapshot.json"
YAHOO = "yahoo_roster.json"
YAHOO_LEAGUE = "yahoo_league.json"  # every Yahoo team, from screenshots
POSITIONS = {"QB", "RB", "WR", "TE"}
KEEP_HOURS = 72  # re-add an auto entry for this long if the daily run drops it
PT = ZoneInfo("America/Los_Angeles")

# Sleeper injury_status -> (news.json status, redraftAdj, dynastyAdj, severity)
INJURY = {
    None: (None, 1.0, 1.0, 0),
    "Questionable": ("Questionable", 0.98, 1.0, 1),
    "Doubtful": ("Out", 0.93, 1.0, 2),
    "Out": ("Out", 0.9, 1.0, 3),
    "COV": ("Out", 0.95, 1.0, 3),
    "NA": ("Out", 0.95, 1.0, 3),
    "DNR": ("Out", 0.95, 1.0, 3),
    "Sus": ("Out", 0.85, 0.97, 3),
    "IR": ("IR", 0.7, 0.97, 4),
    "PUP": ("IR", 0.75, 0.98, 4),
    "NFI": ("IR", 0.75, 0.98, 4),
}
WORDS = {"Questionable": "questionable", "Doubtful": "doubtful", "Out": "out",
         "COV": "out (illness list)", "NA": "not active", "DNR": "out (did not report)",
         "Sus": "suspended", "IR": "on injured reserve", "PUP": "on the PUP list",
         "NFI": "on the non-football injury list"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "trade-war-room-status-watch"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def rostered_ids():
    ids = set()
    for lid in LEAGUES:
        for roster in get(f"{SLEEPER}/league/{lid}/rosters") or []:
            ids.update(roster.get("players") or [])
            ids.update(roster.get("reserve") or [])
            ids.update(roster.get("taxi") or [])
    for p in load(YAHOO, []):
        if p.get("sleeperId"):
            ids.add(str(p["sleeperId"]))
    for team in load(YAHOO_LEAGUE, {}).get("teams", []):
        for p in team.get("players", []):
            if p.get("sleeperId"):
                ids.add(str(p["sleeperId"]))
    return ids


def current_state(p):
    inj = p.get("injury_status") or None  # Sleeper sometimes sends "" for healthy
    return {
        "i": inj if inj in INJURY else (inj and "Out"),
        "t": p.get("team"),
        "qb1": (p.get("depth_chart_order") == 1) if p.get("position") == "QB" and p.get("depth_chart_order") else None,
    }


def stamp(now):
    t = now.astimezone(PT)
    return t.strftime("%-I:%M %p PT %b %-d")


def injury_entry(pid, p, old_entry, prev_i, cur_i, now):
    status, ra, da, sev = INJURY[cur_i]
    prev_sev = INJURY.get(prev_i, INJURY["Out"])[3]
    name = p.get("full_name") or pid
    part = p.get("injury_body_part")
    when = stamp(now)
    if cur_i is None:
        note = f"Cleared: no longer on Sleeper's injury report (was {WORDS.get(prev_i, prev_i)}) as of {when}."
        # healthy again: keep a small injury tag so the site can flag a buy-low window
        ra = 0.98 if prev_sev >= 3 else 1.0
    else:
        note = f"Sleeper now lists him {WORDS.get(cur_i, cur_i)}" + (f" ({part.lower()})" if part else "") + f" as of {when}."
    entry = {"sleeperId": pid, "name": name, "note": note, "tag": "injury",
             "redraftAdj": ra, "dynastyAdj": da, "status": status, "auto": True}
    if old_entry:
        if not old_entry.get("auto") and old_entry.get("note"):
            entry["note"] = note + " Earlier: " + old_entry["note"]
        o_ra, o_da = old_entry.get("redraftAdj", 1), old_entry.get("dynastyAdj", 1)
        if cur_i is None:
            entry["dynastyAdj"] = o_da
        elif sev >= prev_sev:
            entry["redraftAdj"] = min(o_ra, ra)
            entry["dynastyAdj"] = min(o_da, da)
    return entry


def main():
    now = datetime.now(timezone.utc)
    ids = rostered_ids()
    players = get(f"{SLEEPER}/players/nfl")
    snap = load(SNAPSHOT, {"players": {}})
    prev_all = snap.get("players", {})
    news = load(NEWS, {"updated": "", "players": []})
    by_id = {str(e.get("sleeperId")): e for e in news.get("players", []) if e.get("sleeperId")}
    events = []
    new_snap = {}

    for pid in sorted(ids):
        p = players.get(pid)
        if not p or p.get("position") not in POSITIONS:
            continue
        cur = current_state(p)
        prev = prev_all.get(pid)
        rec = dict(cur)
        if prev:
            rec["changed"], rec["entry"] = prev.get("changed"), prev.get("entry")
        new_snap[pid] = rec
        if not prev:
            continue  # first sighting: baseline only
        name = p.get("full_name") or pid
        entry = None
        if cur["i"] != prev.get("i"):
            entry = injury_entry(pid, p, by_id.get(pid), prev.get("i"), cur["i"], now)
            events.append(f"{name}: {prev.get('i') or 'healthy'} -> {cur['i'] or 'healthy'}")
        elif cur["t"] != prev.get("t") and prev.get("t"):
            where = f"moved from {prev['t']} to {cur['t']}" if cur["t"] else f"was released by {prev['t']}"
            entry = {"sleeperId": pid, "name": name, "tag": "rumor", "redraftAdj": 1, "dynastyAdj": 1,
                     "status": (by_id.get(pid) or {}).get("status"), "auto": True,
                     "note": f"Sleeper shows he {where} as of {stamp(now)}; check his new role."}
            events.append(f"{name}: {prev['t']} -> {cur['t'] or 'FA'}")
        elif cur["qb1"] is not None and prev.get("qb1") is not None and cur["qb1"] != prev["qb1"]:
            up = cur["qb1"]
            entry = {"sleeperId": pid, "name": name, "tag": "role_up" if up else "role_down",
                     "redraftAdj": 1.2 if up else 0.8, "dynastyAdj": 1.05 if up else 0.95,
                     "status": (by_id.get(pid) or {}).get("status"), "auto": True,
                     "note": f"Sleeper's depth chart now has him as {cur['t']}'s {'starting' if up else 'backup'} QB as of {stamp(now)}."}
            events.append(f"{name}: QB1 {'gained' if up else 'lost'}")
        if entry:
            by_id[pid] = entry
            rec["changed"], rec["entry"] = now.isoformat(), entry

    # keep recent auto entries alive if the daily research run rewrote news.json without them
    cutoff = now - timedelta(hours=KEEP_HOURS)
    for pid, rec in new_snap.items():
        if rec.get("entry") and rec.get("changed") and pid not in by_id:
            if datetime.fromisoformat(rec["changed"]) >= cutoff:
                by_id[pid] = rec["entry"]
                events.append(f"{rec['entry'].get('name')}: re-added recent status note")
        if rec.get("changed") and datetime.fromisoformat(rec["changed"]) < cutoff:
            rec.pop("entry", None)

    old_players = news.get("players", [])
    news["players"] = list(by_id.values()) + [e for e in old_players if not e.get("sleeperId")]
    if events:
        news["statusChecked"] = stamp(now)
        with open(NEWS, "w") as f:
            json.dump(news, f, indent=2, ensure_ascii=False)
            f.write("\n")
    snap = {"players": new_snap}
    if snap != load(SNAPSHOT, None):
        with open(SNAPSHOT, "w") as f:
            json.dump(snap, f, indent=1, sort_keys=True)
            f.write("\n")
    print(f"{len(new_snap)} rostered players checked; {len(events)} change(s)")
    for e in events:
        print(" -", e)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"changes={len(events)}\n")


if __name__ == "__main__":
    main()
