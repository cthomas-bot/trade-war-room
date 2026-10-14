#!/usr/bin/env python3
"""Kalshi sports market snapshot for the Bets panel (kalshi.json).

Reads Kalshi's public market data (no account or key) for NFL, college
football, MLB and NBA game markets closing in the next few days. Quotes are a
snapshot for research only: always recheck the live order preview before
acting. Seattle Seahawks markets are excluded by rule. Standard library only.
"""
import json
import time
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

OUT = "kalshi.json"
API = "https://api.elections.kalshi.com/trade-api/v2"
PT = ZoneInfo("America/Los_Angeles")
UA = {"User-Agent": "trade-war-room-kalshi-snapshot", "Accept": "application/json"}
SPORTS = {"NFL": "NFL", "NCAAF": "CFB", "MLB": "MLB", "NBA": "NBA"}
KINDS = ("GAME", "SPREAD", "TOTAL")
SERIES = [f"KX{sp}{k}" for sp in SPORTS for k in KINDS]
PER_EVENT = 3  # spread/total lines kept per game: the ones priced closest to 50/50
HORIZON = timedelta(days=6)  # covers NFL Sunday from midweek
EXCLUDE = re.compile(r"seahawks|\bseattle\b(?!\s+mariners)|\bSEA\b", re.I)


def get(path, **params):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def dollars(m, key):
    """Price in dollars from either the *_dollars string or the legacy cents field."""
    v = m.get(key + "_dollars")
    if v not in (None, ""):
        try:
            return round(float(v), 4)
        except ValueError:
            pass
    v = m.get(key)
    return round(v / 100, 4) if isinstance(v, (int, float)) else None


def sport_of(ticker):
    m = re.match(r"KX(NFL|NCAAF|MLB|NBA)(GAME|SPREAD|TOTAL)\b", ticker.upper())
    return SPORTS[m.group(1)] if m else None


def game_name(rules, fallback):
    m = re.search(r" the (.+?) (?:pro|college|professional) (?:football|basketball|baseball) game", rules or "", re.I)
    return m.group(1) if m else fallback


def markets_for(series):
    out, cursor = [], None
    for _ in range(10):
        params = {"series_ticker": series, "status": "open", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        page = get("/markets", **params)
        out += page.get("markets") or []
        cursor = page.get("cursor")
        if not cursor:
            break
    return out


def main():
    now = datetime.now(timezone.utc)
    rows, used, errors, excluded = [], [], [], 0
    for s in SERIES:
        time.sleep(0.4)  # stay well under the public rate limit
        try:
            ms = markets_for(s)
        except Exception as e:
            errors.append(f"{s}: {e}")
            continue
        if ms:
            used.append(s)
        for m in ms:
            close = m.get("close_time") or m.get("expected_expiration_time")
            try:
                ct = datetime.fromisoformat(close.replace("Z", "+00:00"))
            except (AttributeError, ValueError):
                continue
            if ct - now > HORIZON + timedelta(days=14):  # game markets often close ~2 weeks after kickoff
                continue
            text = " ".join(str(m.get(k) or "") for k in ("title", "subtitle", "yes_sub_title", "no_sub_title", "event_ticker"))
            sport = sport_of(m.get("ticker", ""))
            teams = re.match(r".*-\d{2}[A-Z]{3}\d{2}([A-Z]+)", m.get("event_ticker") or "")
            if sport == "NFL" and (EXCLUDE.search(text) or (teams and "SEA" in teams.group(1))):
                excluded += 1
                continue
            exp = m.get("expected_expiration_time") or close
            ask = dollars(m, "yes_ask")
            if s.endswith(("SPREAD", "TOTAL")) and not (ask and 0.12 <= ask <= 0.88):
                continue  # far-off alternate lines
            rows.append({
                "ticker": m.get("ticker"), "event": m.get("event_ticker"), "series": s, "sport": sport,
                "title": m.get("title"), "yes": m.get("yes_sub_title") or m.get("subtitle"), "no": m.get("no_sub_title"),
                "yesBid": dollars(m, "yes_bid"), "yesAsk": dollars(m, "yes_ask"),
                "noBid": dollars(m, "no_bid"), "noAsk": dollars(m, "no_ask"), "last": dollars(m, "last_price"),
                "volume": m.get("volume"), "openInterest": m.get("open_interest"),
                "close": close, "expectedEnd": exp,
                "game": game_name(m.get("rules_primary"), m.get("title")),
                "kind": s[len("KX"):].replace("NCAAF", "").replace("NFL", "").replace("MLB", "").replace("NBA", ""),
                "rules": (m.get("rules_primary") or "")[:500],
            })
    # keep markets whose game resolves soon (expected expiration within the horizon)
    def soon(r):
        try:
            return datetime.fromisoformat(r["expectedEnd"].replace("Z", "+00:00")) - now <= HORIZON
        except (AttributeError, ValueError):
            return True
    def started(r):  # expected expiration is ~3h after kickoff for football, less for others
        try:
            end = datetime.fromisoformat(r["expectedEnd"].replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            return False
        return end - now < timedelta(hours=3 if r["sport"] in ("NFL", "CFB") else 2.5)
    rows = [r for r in rows if soon(r) and not started(r)]
    # trim alternate spread/total lines to the few closest to a coin flip per game
    keep, groups = [], {}
    for r in rows:
        if r["kind"] == "GAME":
            keep.append(r)
        else:
            groups.setdefault((r["event"], r["kind"]), []).append(r)
    for g in groups.values():
        keep += sorted(g, key=lambda r: abs((r["yesAsk"] or 0) - 0.5))[:PER_EVENT]
    rows = keep
    rows.sort(key=lambda r: (r["expectedEnd"] or "", r["event"] or "", r["ticker"] or ""))
    doc = {"updated": now.astimezone(PT).strftime("%Y-%m-%d %-I:%M %p PT"), "quotedAt": now.isoformat(),
           "series": used, "excludedSeahawks": excluded, "markets": rows}
    if errors:
        doc["errors"] = errors[:10]
    with open(OUT, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"{len(rows)} markets from {len(used)} series; excluded {excluded} Seahawks markets", errors[:3] or "")


if __name__ == "__main__":
    main()
