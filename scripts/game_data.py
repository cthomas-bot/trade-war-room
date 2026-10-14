#!/usr/bin/env python3
"""Vegas lines + weekly projections for the site (games.json).

Pulls this week's NFL games and betting lines from ESPN's public scoreboard and
Sleeper's weekly projections, then writes games.json next to index.html. The
page reads these live when the browser allows it and falls back to this file.
Standard library only.
"""
import json
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

OUT = "games.json"
PT = ZoneInfo("America/Los_Angeles")
UA = {"User-Agent": "trade-war-room-game-data"}
# ESPN abbreviations that differ from Sleeper's
ESPN_TO_SLEEPER = {"WSH": "WAS", "JAC": "JAX", "LA": "LAR"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def team(abbr):
    abbr = (abbr or "").upper()
    return ESPN_TO_SLEEPER.get(abbr, abbr)


def parse_line(details, total):
    """'KC -3.5' -> ('KC', 3.5); 'EVEN' -> (None, 0)."""
    try:
        abbr, num = details.rsplit(" ", 1)
        return team(abbr), abs(float(num))
    except (AttributeError, ValueError):
        return None, 0.0


def games(season, week):
    data = get("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
               f"?seasontype=2&week={week}&dates={season}")
    out = []
    for ev in data.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        sides = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        home, away = sides.get("home", {}), sides.get("away", {})
        g = {
            "id": ev.get("id"),
            "kickoff": ev.get("date"),
            "state": ((ev.get("status") or {}).get("type") or {}).get("state"),
            "home": team((home.get("team") or {}).get("abbreviation")),
            "away": team((away.get("team") or {}).get("abbreviation")),
            "homeScore": home.get("score"),
            "awayScore": away.get("score"),
            "venue": ((comp.get("venue") or {}).get("fullName")),
            "tv": ", ".join(b.get("names", [""])[0] for b in comp.get("broadcasts", []) if b.get("names")),
        }
        odds = (comp.get("odds") or [None])[0]
        if odds:
            total = odds.get("overUnder")
            fav, line = parse_line(odds.get("details"), total)
            g.update({"details": odds.get("details"), "total": total, "fav": fav, "spread": line,
                      "homeML": (odds.get("homeTeamOdds") or {}).get("moneyLine"),
                      "awayML": (odds.get("awayTeamOdds") or {}).get("moneyLine")})
            if total:
                for side in ("home", "away"):
                    t = g[side]
                    implied = total / 2 + (line / 2 if t == fav else -line / 2 if fav else 0)
                    g[side + "Implied"] = round(implied, 1)
        out.append(g)
    return out


def projections(season, week):
    pos = "&".join(f"position[]={p}" for p in ("QB", "RB", "WR", "TE"))
    rows = get(f"https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular&{pos}")
    out = {}
    for r in rows or []:
        st = r.get("stats") or {}
        pts = st.get("pts_half_ppr")
        if r.get("player_id") and pts and pts >= 0.5:
            out[str(r["player_id"])] = {"half": round(pts, 2), "ppr": round(st.get("pts_ppr") or pts, 2),
                                        "std": round(st.get("pts_std") or pts, 2), "opp": r.get("opponent")}
    return out


def main():
    st = get("https://api.sleeper.app/v1/state/nfl")
    season, week = st.get("season"), st.get("week") or st.get("display_week") or 1
    now = datetime.now(timezone.utc)
    doc = {"season": season, "week": week, "updated": now.astimezone(PT).strftime("%Y-%m-%d %-I:%M %p PT")}
    errors = []
    try:
        doc["games"] = games(season, week)
    except Exception as e:  # keep going: projections alone are still useful
        errors.append(f"games: {e}")
        doc["games"] = []
    try:
        doc["projections"] = projections(season, week)
    except Exception as e:
        errors.append(f"projections: {e}")
        doc["projections"] = {}
    if errors:
        doc["errors"] = errors
    try:
        old = json.load(open(OUT))
    except (FileNotFoundError, json.JSONDecodeError):
        old = {}
    # keep the last good data if a source failed this run
    for k in ("games", "projections"):
        if not doc[k] and old.get(k) and old.get("week") == week:
            doc[k] = old[k]
    if {k: v for k, v in doc.items() if k != "updated"} != {k: v for k, v in old.items() if k != "updated"}:
        with open(OUT, "w") as f:
            json.dump(doc, f, indent=1, ensure_ascii=False)
            f.write("\n")
    print(f"week {week}: {len(doc['games'])} games, {len(doc['projections'])} projections", errors or "")


if __name__ == "__main__":
    main()
