# Daily bet scan — rules and output (Bets tab)

Research only: this never places orders. No method guarantees profit.

## User's rules
- Sports: MLB, NFL, college football, NBA when actually scheduled (verify). No political/nonsports markets.
- No Seattle Seahawks picks (the user never bets them) — show a Seahawks game only as "SKIP".
- Bankroll: **$50 per week, $5–10 per day**. Default stake $5; $10 only for the strongest YES.
- No chasing losses, no bigger stakes after a loss.
- Straight bets by default. Parlays are for fun only: 2–4 legs that are each likely (e.g. anytime TDs for heavy-usage players, a solid favorite), total around +400 or shorter. Never +1000 longshots.
- Use correct, current data: verify schedule, lines from at least two books, injuries, lineups/probable pitchers, weather. Never invent prices, injuries or stats. If a trend the user mentions isn't real, say so plainly.

## How to call each game
For every game on today's slate give ONE pick — the best of moneyline side, spread, or game total (over/under) — and a call:
- **YES** — bet it. Our probability beats the price after fees by a real margin (aim for ≥3 points at the conservative end). Green on the site.
- **LEAN** — we like the side but the price is about fair; small/optional.
- **WAIT** — could become a YES; give the exact trigger (price, injury news) and when to recheck.
- **PASS** — no clear side (shows as "NO CLEAR SIDE").
Compare Kalshi prices (kalshi.json snapshot; recheck live before betting) with de-vigged sportsbook odds: American +A → 100/(A+100), −A → A/(A+100); de-vig two sides r1/(r1+r2). Kalshi taker fee ≈ ceil(0.07 × contracts × p × (1−p)) to the cent.

**Keep text short:** each "why" is one sentence (~15 words max). No essays.

## Extra sections
- **Primetime** (on days with an upcoming TNF/SNF/MNF this week): one card per game with line, pick, call, 1–2 solid props, recheck. TNF: also report the season's real TNF underdog record (straight up / ATS) with a source.
- **Sunday props** (NFL Sundays): best props split into Morning (10 AM PT), Afternoon (1 PM PT) and Late (SNF) slates, 2–4 per slate, realistic lines with odds.
- **Fun parlay** (optional): 2–4 likely legs, ≤ about +400.

## Output: `bets.json` at the repo root
```json
{
 "date": "Wed Oct 14", "scanned": "Oct 14, 7:50 AM PT",
 "slate": [{"sport": "MLB", "game": "Brewers @ Dodgers · NLCS G3", "time": "5:00 PM PT",
            "pick": "Dodgers ML", "price": "62¢", "call": "YES|LEAN|WAIT|PASS",
            "why": "one short sentence", "recheck": "short trigger + time, or empty"}],
 "upcoming": [ same shape — notable games in the next few days, usually WAIT ],
 "primetime": {"tnf": {"game": "...", "kickoff": "Thu 5:15 PM PT · Prime", "trend": "...", "note": "...", "call": "SKIP|YES|LEAN|PASS"},
               "games": [{"slot": "SNF", "game": "...", "kickoff": "...", "line": "GB -1.5 · O/U 52.5",
                          "pick": "...", "price": "...", "call": "...", "why": "...",
                          "props": [{"pick": "...", "odds": "-150", "why": "..."}], "recheck": "..."}]},
 "props": [{"slate": "Morning · 10 AM PT", "picks": [{"pick": "...", "odds": "...", "why": "...", "call": "YES|LEAN"}]}],
 "parlay": {"legs": [{"leg": "...", "odds": "-150"}], "odds": "+300", "why": "...", "call": "FUN"},
 "sources": [{"title": "...", "url": "https://..."}]
}
```
Omit "primetime"/"props"/"parlay" (or use null/[]) when there's nothing for them.
