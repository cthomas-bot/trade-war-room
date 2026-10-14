# Kalshi Sports Scan — rules for the daily scan (condensed from the user's framework)

Research, not a trading bot. It never places orders. No method guarantees profit; any stake can be lost.

## Nonnegotiables
- Sports only: MLB, NFL, college football, NBA, when actually scheduled (verify the schedule). No political or nonsports markets.
- **No Seattle Seahawks exposure of any kind** (their games, team or player props, bets against them, entries containing them).
- Straight, clearly understood contracts by default. Never add legs to raise a payout. Avoid correlated exposure (same game/player/outcome).
- **PASS is a successful result.** Never force a pick, chase losses or a moving price, or bet on popularity/streaks/"a chance of a comeback".
- Stakes: **$5 default, $10 ceiling, including fees**, only for unusually well-supported opportunities within the user's budget. If no bankroll and daily cap are set, the scan is research-only: conditional candidates, no funded direction. Never invent limits.
- PrizePicks (NFL Sunday only, when requested) uses a separate bankroll and ledger.

## Workflow
1. Identify the event (date, teams, venue, start time PT, ticker) and verify it is scheduled.
2. Read the exact contract: purchased side, threshold, settlement source, OT/ties/postponement rules. NO is the complement of the defined event.
3. Capture executable terms: bid/ask, quantity, quote timestamp, fees. The snapshot in `kalshi.json` is a research snapshot, not a fresh executable quote — candidates are conditional on rechecking it.
4. Evidence: official lineups/injury reports, probable pitchers, weather, named beat reporters, transparent models, multiple sportsbooks (de-vig: r1/(r1+r2); American +A → 100/(A+100), −A → A/(A+100)). Label confirmed facts vs reported expectations vs model estimates vs inference. Never invent prices, injuries, sources or probabilities.
5. Build a defensible probability range for the purchased side (state the basis; a judgment range is not a confidence interval).
6. Price after costs, conservative end of the range.

## Math ($1/$0 binary held to settlement)
- C = n·q + F; break-even p_BE = q + F/n; edge pp = 100·(p − p_BE); EV = n·p − C; win nets n − C; loss is −C.
- Kalshi general taker fee (verify against the official schedule / order preview): ceil(0.07 × n × q × (1 − q)) to the cent.
- Screening buffer: **≥ 3 pp of edge at the LOW end of the range after costs**, plus strong evidence and no unresolved material facts. q_max = p_low − 0.03 − F/n (fixed fees).
- Unknown fees, stale quotes, ambiguous settlement, unresolved lineup/injury news, or an edge that vanishes under conservative assumptions → WATCH or PASS.

## Verdicts
- **PASS** — fails the screen, weak evidence, excluded, or essential info missing. $0.
- **WATCH** — a specific price or confirmation could change it. $0 now; state the trigger and recheck time.
- **QUALIFIED CANDIDATE** — clears the guardrails at a verified price; up to $5 (≤ $10 under budget rules); recheck before entry.
At most three candidates. Zero is fine. A "lean" never overrides PASS.

## Output: `bets.json` (read by the site's Bets tab)
```json
{
 "date": "YYYY-MM-DD", "scanned": "YYYY-MM-DD h:mm AM PT", "dataCutoff": "h:mm AM PT",
 "verdict": "No qualifying bets | N conditional candidates",
 "budget": "Research-only: no bankroll or daily cap set",
 "limitations": "what could not be verified (or empty)",
 "candidates": [{
   "sport": "MLB", "event": "Away @ Home", "startPT": "Wed 5:08 PM PT", "contract": "Team wins (YES)",
   "ticker": "KX...", "ask": 0.55, "askTime": "9:37 PM PT snapshot", "contracts": 8, "fees": 0.14,
   "pLow": 0.58, "pMid": 0.60, "pHigh": 0.62, "breakEven": 0.5675, "edgeLow": 1.3, "edgeHigh": 5.3,
   "evLow": 0.10, "evHigh": 0.42, "maxPrice": 0.53, "maxStake": "$0 (research-only)",
   "verdict": "PASS | WATCH | QUALIFIED CANDIDATE",
   "yesMeans": "...", "noMeans": "...",
   "evidence": [{"text": "claim (source, time)", "url": "https://..."}],
   "against": "evidence against / uncertainty", "reason": "why this verdict", "recheck": "trigger + time"
 }],
 "watchlist": [{"event": "...", "trigger": "...", "recheck": "..."}],
 "passes": [{"market": "...", "reason": "..."}],
 "prizepicks": null,
 "sources": [{"title": "...", "url": "https://...", "time": "..."}],
 "gaps": ["missing facts / stale data"]
}
```
Probabilities are 0–1; edges in percentage points; money in dollars.
