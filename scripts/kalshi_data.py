#!/usr/bin/env python3
"""Kalshi sports market snapshot for the Bets panel (kalshi.json).

Reads Kalshi's public market data (no account or key) for NFL, college
football, MLB and NBA game markets closing in the next few days. Quotes are a
snapshot for research only: always recheck the live order preview before
acting. Seattle Seahawks markets are excluded by rule. Standard library only.
"""
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

OUT = "kalshi.json"
API = "https://api.elections.kalshi.com/trade-api/v2"
PT = ZoneInfo("America/Los_Angeles")
UA = {"User-Agent": "trade-war-room-kalshi-snapshot", "Accept": "application/json"}
SPORTS = {"NFL": "NFL", "NCAAF": "CFB", "CFB": "CFB", "MLB": "MLB", "NBA": "NBA"}
KINDS = ("GAME", "SPREAD", "TOTAL")
FALLBACK_SERIES = ["KXNFLGAME", "KXNCAAFGAME", "KXMLBGAME", "KXNBAGAME",
                   "KXNFLSPREAD", "KXNFLTOTAL", "KXNCAAFSPREAD", "KXNCAAFTOTAL"]
HORIZON = timedelta(days=4)
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
    t = ticker.upper()
    for k, v in SPORTS.items():
        if k in t:
            return v
    return None


def discover():
    try:
        series = get("/series", category="Sports").get("series") or []
    except Exception as e:
        print("series discovery failed:", e)
        return FALLBACK_SERIES
    found = [s["ticker"] for s in series
             if s.get("ticker") and sport_of(s["ticker"]) and any(k in s["ticker"].upper() for k in KINDS)]
    return sorted(set(found)) or FALLBACK_SERIES


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
    for s in discover():
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
            rows.append({
                "ticker": m.get("ticker"), "event": m.get("event_ticker"), "series": s, "sport": sport,
                "title": m.get("title"), "yes": m.get("yes_sub_title") or m.get("subtitle"), "no": m.get("no_sub_title"),
                "yesBid": dollars(m, "yes_bid"), "yesAsk": dollars(m, "yes_ask"),
                "noBid": dollars(m, "no_bid"), "noAsk": dollars(m, "no_ask"), "last": dollars(m, "last_price"),
                "volume": m.get("volume"), "openInterest": m.get("open_interest"),
                "close": close, "expectedEnd": exp,
                "rules": (m.get("rules_primary") or "")[:500],
            })
    # keep markets whose game resolves soon (expected expiration within the horizon)
    def soon(r):
        try:
            return datetime.fromisoformat(r["expectedEnd"].replace("Z", "+00:00")) - now <= HORIZON
        except (AttributeError, ValueError):
            return True
    rows = [r for r in rows if soon(r)]
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
