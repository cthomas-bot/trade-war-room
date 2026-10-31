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

**At most 4 LEANs per day** (whole slate, primetime included; YES is not capped). If more games qualify, keep the 4 with the strongest market signal (sharp/handle move, reverse line movement, Kalshi hanging a stale number) and mark the rest PASS with a why like "Fair price; outside today's top 4." A price that only matches the books, with no market signal behind it, is a PASS, not a LEAN. Rechecks keep the cap: upgrading a WAIT to LEAN on a full day means dropping the weakest LEAN.
Compare Kalshi prices (kalshi.json snapshot; recheck live before betting) with de-vigged sportsbook odds: American +A → 100/(A+100), −A → A/(A+100); de-vig two sides r1/(r1+r2). Kalshi taker fee ≈ ceil(0.07 × contracts × p × (1−p)) to the cent.

**Say exactly what to tap in Kalshi:** for spreads/totals write the pick as the Kalshi contract side, e.g. `NO on “Toledo wins by over 6.5” (= EMU +6.5)` or `YES on “Over 52.5”`. Moneylines stay `Team ML`.

**Keep text short:** each "why" is one sentence (~15 words max). No essays.

## How we think: Market → Trends → Matchup
Every YES/LEAN/WAIT pick (games and props) is built in this order, and the pick JSON carries one short line for each: `"market"`, `"trend"`, `"matchup"` (≤ ~25 words each; omit a field only if nothing real was found). PASS games don't need them.

1. **📈 Market (most weight): follow the sharp money, then shop for a stale number.**
   - Anchor on the sharp book (Pinnacle; Circa/BetOnline if Pinnacle isn't findable). Report the opening → current line and price, e.g. "SEA −1.5 → −3, no tick back; KC ML +116 → +136".
   - Compare public splits (tickets % vs money %, from Action Network / VSiN / DraftKings splits) with the move. **Reverse line movement** (line moves against the side with most tickets) is the strongest signal; a move with the public is weak.
   - Edge = a retail book **or Kalshi** still showing the old number after the sharp book moved (e.g. Pinnacle 78.5, DraftKings still 80.5). Price Kalshi against the sharp book's no-vig line, not the retail average.
   - Steam/firming prices (−110 → −133 on the same number) count as a move.
2. **📊 Trends (support only, never the sole reason):** state the record and sample, e.g. "SNF teams with ≤25% of tickets are 6-2 ATS". Prefer situational/market trends (low-ticket side, line moving toward the low-ticket side, primetime road favorites/dogs), QB/coach ATS records, and **player game logs vs the line** ("lead backs vs SEA: 51, 29, 36, 45, 68, 41 — none reached 70"). Small samples (<20) are tiebreakers only.
3. **🔍 Matchup (unit vs unit):** the specific mismatch that explains the market: pressure rate, rush/pass EPA, yards per carry allowed, RB yards allowed per game, red-zone TD rate, pace, weather, injuries/inactives. One concrete chain: "If KC can't run (SEA 3.65 ypc allowed, #3 rush EPA), Mahomes throws into the #2 pass D."

**Totals (game and team totals):** same three lines, plus a totals checklist:
- Market: total moving *against* the heavy side (e.g. 66% of tickets / 74% of money on the Over, yet 44.5 → 42.5 and Pinnacle 43 → 42) is reverse line movement on a total; note the lowest/highest number available (42 at BetMGM vs 42.5 elsewhere) and whether Kalshi still shows the old number.
- Trends to check: primetime unders when 65%+ of tickets are on the Over; small home favorites (≤3) in primetime vs the total; totals that dropped 2+ points with the public on the Over; the QBs'/teams' over-under records; **the referee crew's** over-under record (especially primetime).
- Matchup: both defenses' EPA and points allowed (season and last 3), red-zone TD rate allowed, offensive pace and PROE (pass rate over expected: a run-first team that can't run = slow game), and weather at kickoff (temperature, wind, rain).

**Props:** same three lines. Favor props where the sharp book moved and a retail book (or Kalshi) lags, and where the game log hit rate agrees (e.g. "4 of 5 lead backs under 52.5 vs KC"). Correlate with the game read (a slow, low-total game → RB unders, QB scramble overs vs heavy-pressure defenses).

**Honesty rules:** only report splits, line moves and trends you actually found with a source (put the URLs in `sources`). If sharp-book movement or split data isn't findable, say "no sharp-line data found" in `market` and don't upgrade past LEAN on trends alone. Never invent percentages or records.

## Extra sections
- **Primetime** (on days with an upcoming TNF/SNF/MNF this week): one card per game with line, pick, call, 1–2 solid props, recheck. TNF: also report the season's real TNF underdog record (straight up / ATS) with a source.
- **Sunday props** (NFL Sundays): best props split into Morning (10 AM PT), Afternoon (1 PM PT) and Late (SNF) slates, 2–4 per slate, realistic lines with odds.
- **Props on college Saturdays too**: slates like "College · Morning (9 AM PT)", "College · Afternoon", "College · Night", 2–4 props each with real odds.
- **Fun parlays** (optional): up to 3 in `parlays` (each with a `name`, e.g. "Safe favorites", "CFB props"), 2–4 likely legs each, ≤ about +400. A single `parlay` object still works.

## Schedule
- **Morning scan** (~7:50 AM PT daily): full scan, written fresh.
- **Recheck** (~2:50 PM PT daily, plus ~12:20 PM PT Sundays): light update of the existing bets.json, with no rewrite. Recheck only games that haven't started, mainly WAIT/LEAN calls and anything hit by new injuries, lineups or starters, or line moves. Upgrade or downgrade calls, update price and recheck, and drop finished games. Set `"scanned"` to e.g. "Oct 15, 2:52 PM PT · recheck". On Sundays, also refresh the Afternoon/Late props for NFL inactives. If nothing changed, update only `scanned`. If no games are left today, make no commit.

## Results tracker: `results.json`
The morning scan grades yesterday's picks first, before writing the new bets.json.
- Take every YES/LEAN game pick (and primetime pick) from the previous day's last bets.json version that had it before kickoff (`git log -- bets.json`). Use the call it had at kickoff.
- Find each final score (WebSearch, two sources if possible) and grade W / L / P (push, refund). Moneyline = winner; "X wins by over N" YES needs margin > N, NO needs margin < N; totals vs the line.
- $5 per pick at the listed price: win pays 5/p − 5, loss −5, push 0; subtract the Kalshi taker fee 0.07 × (5/p) × p × (1−p). Round to cents.
- Append to `picks` as {date, sport, game, pick, price, call, result, final, pl}; skip games already in the file; set "updated". If a final can't be found, leave it out and try again the next day.

## Output: `bets.json` at the repo root
```json
{
 "date": "Wed Oct 14", "scanned": "Oct 14, 7:50 AM PT",
 "slate": [{"sport": "MLB", "game": "Brewers @ Dodgers · NLCS G3", "time": "5:00 PM PT",
            "pick": "Dodgers ML", "price": "62¢", "call": "YES|LEAN|WAIT|PASS",
            "why": "one short sentence", "recheck": "short trigger + time, or empty",
            "market": "📈 sharp move / splits / stale number", "trend": "📊 record + sample", "matchup": "🔍 unit-vs-unit edge"}],
 "upcoming": [ same shape — notable games in the next few days, usually WAIT ],
 "primetime": {"tnf": {"game": "...", "kickoff": "Thu 5:15 PM PT · Prime", "trend": "...", "note": "...", "call": "SKIP|YES|LEAN|PASS"},
               "games": [{"slot": "SNF", "game": "...", "kickoff": "...", "line": "GB -1.5 · O/U 52.5",
                          "pick": "...", "price": "...", "call": "...", "why": "...",
                          "props": [{"pick": "...", "odds": "-150", "why": "..."}], "recheck": "..."}]},
 "props": [{"slate": "Morning · 10 AM PT", "picks": [{"pick": "...", "odds": "...", "why": "...", "call": "YES|LEAN", "market": "...", "trend": "...", "matchup": "..."}]}],
 "parlay": {"legs": [{"leg": "...", "odds": "-150"}], "odds": "+300", "why": "...", "call": "FUN"},
 "sources": [{"title": "...", "url": "https://..."}]
}
```
Omit "primetime"/"props"/"parlay" (or use null/[]) when there's nothing for them.
