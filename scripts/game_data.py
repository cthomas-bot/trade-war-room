#!/usr/bin/env python3
"""Vegas lines + weekly projections for the site (games.json).

Pulls this week's NFL games and betting lines from ESPN's public scoreboard and
Sleeper's weekly projections, then writes games.json next to index.html. The
page reads these live when the browser allows it and falls back to this file.
Standard library only.
"""
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

OUT = "games.json"
PT = ZoneInfo("America/Los_Angeles")
UA = {"User-Agent": "trade-war-room-game-data"}
# home stadiums: (lat, lon, roof) — roof "dome" (fixed/usually closed), "retract" (retractable), "open"
STADIUM = {
    "ARI": (33.5276, -112.2626, "retract"), "ATL": (33.7554, -84.4008, "retract"), "BAL": (39.2780, -76.6227, "open"),
    "BUF": (42.7738, -78.7870, "open"), "CAR": (35.2258, -80.8528, "open"), "CHI": (41.8623, -87.6167, "open"),
    "CIN": (39.0955, -84.5161, "open"), "CLE": (41.5061, -81.6995, "open"), "DAL": (32.7473, -97.0945, "retract"),
    "DEN": (39.7439, -105.0201, "open"), "DET": (42.3400, -83.0456, "dome"), "GB": (44.5013, -88.0622, "open"),
    "HOU": (29.6847, -95.4107, "retract"), "IND": (39.7601, -86.1639, "retract"), "JAX": (30.3239, -81.6373, "open"),
    "KC": (39.0489, -94.4839, "open"), "LV": (36.0909, -115.1833, "dome"), "LAC": (33.9535, -118.3392, "dome"),
    "LAR": (33.9535, -118.3392, "dome"), "MIA": (25.9580, -80.2389, "open"), "MIN": (44.9737, -93.2577, "dome"),
    "NE": (42.0909, -71.2643, "open"), "NO": (29.9511, -90.0812, "dome"), "NYG": (40.8135, -74.0745, "open"),
    "NYJ": (40.8135, -74.0745, "open"), "PHI": (39.9008, -75.1675, "open"), "PIT": (40.4468, -80.0158, "open"),
    "SF": (37.4030, -121.9700, "open"), "SEA": (47.5952, -122.3316, "open"), "TB": (27.9759, -82.5033, "open"),
    "TEN": (36.1665, -86.7713, "open"), "WAS": (38.9076, -76.8645, "open"),
}
NEUTRAL = {"wembley": (51.5560, -0.2795, "open"), "tottenham": (51.6043, -0.0664, "open"),
           "allianz": (48.2188, 11.6247, "open"), "bernab": (40.4531, -3.6883, "retract"),
           "maracan": (-22.9122, -43.2302, "open"), "croke": (53.3607, -6.2511, "open")}
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


def weather(g):
    """Roof + kickoff-hour forecast from Open-Meteo (free, no key) for open-air stadiums."""
    venue = (g.get("venue") or "").lower()
    spot = next((v for k, v in NEUTRAL.items() if k in venue), None) or STADIUM.get(g.get("home"))
    if not spot or not g.get("kickoff"):
        return None
    lat, lon, roof = spot
    if roof == "dome":
        return {"roof": "dome"}
    ko = datetime.fromisoformat(g["kickoff"].replace("Z", "+00:00"))
    if ko - datetime.now(timezone.utc) > timedelta(days=15):
        return {"roof": roof}
    day = ko.strftime("%Y-%m-%d")
    data = get("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&hourly=temperature_2m,"
               "precipitation_probability,weather_code,wind_speed_10m&temperature_unit=fahrenheit"
               "&wind_speed_unit=mph&timezone=UTC&start_date=%s&end_date=%s" % (lat, lon, day, day))
    h = data.get("hourly") or {}
    times = h.get("time") or []
    key = ko.strftime("%Y-%m-%dT%H:00")
    if key not in times:
        return {"roof": roof}
    i = times.index(key)
    pick = lambda k: (h.get(k) or [None] * len(times))[i]
    return {"roof": roof, "temp": pick("temperature_2m"), "precip": pick("precipitation_probability"),
            "code": pick("weather_code"), "wind": pick("wind_speed_10m"), "night": not 6 <= (ko.hour + lon / 15) % 24 < 18}  # solar local time at the stadium


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
    for g in doc["games"]:
        try:
            w = weather(g)
            if w:
                g["weather"] = w
        except Exception as e:
            errors.append(f"weather {g.get('home')}: {e}")
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
