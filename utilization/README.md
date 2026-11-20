# Our Utilization Report

Our own version of Fantasy Life's weekly Utilization Report, computed from free public data
(nflverse play-by-play, FTN charting, PFR snap counts). No Fantasy Life tables are copied; we only
use their published definitions and a few of their printed numbers to check our math.

**Dashboard:** https://claude.ai/artifact/HkJFXiPoiFPvjNSQsB4neU

## Refresh

- Automatic: `.github/workflows/utilization.yml` runs every Tuesday (retry Wednesday) and commits
  fresh files to `utilization/data/`. You can also run it by hand from the Actions tab.
- By hand: `cd utilization && pip install pandas pyarrow && python3 build_utilization.py --season 2026 --out data`
- Compare players: `python3 compare_players.py "Caleb Douglas" "Josh Downs" --windows "Season:1-10" "Weeks 7-10:7-10"`
- The dashboard reads uploaded copies of `data/dash_*.json`, `data/run.json`, `data/compare.json`
  and `data/spotcheck.json`; ask Claude to "refresh the utilization dashboard" to re-upload them.

## How the daily GM report uses it

Read `utilization/data/wr.csv` (and te/rb/qb). Each row has a `window` (`season`, `last4`, `week`).
For WR buy/sell targets, quote `route_part`, `tprr`, `yprr`, `tgt_share`/`fr_share`, `wopr` and the
`wr_checks` / `wr_tier` columns (Chris's 5-metric checklist is already scored).

## Metrics and how they're built

| Metric | Our formula | vs Fantasy Life |
|---|---|---|
| Snap % | PFR offensive snap share | matches (±1 pt) |
| Route % (est) | team dropbacks × snap share (× 1.05 for WRs, capped at 100%) | WRs within ~5 pts; TEs raw; **RBs not reproducible** (blank) |
| Target share | targets ÷ team targets in games played | matches (±2 pts) |
| 1st-read share | targets on FTN `read_thrown == 1` ÷ team first-read targets | FL doesn't publish one |
| TPRR / YPRR (est) | targets / receiving yards ÷ estimated routes | follows route estimate |
| aDOT, air yards share | air yards ÷ targets; player ÷ team air yards | matches (±2 pts) |
| WOPR | 1.5 × target share + 0.7 × air yards share | standard formula |
| Catchable / EZ / RZ targets | FTN `is_catchable_ball`; air yards ≥ distance to goal; inside the 20 | FL columns, unverified |
| Rush share | designed carries ÷ team designed carries (no scrambles/kneels) | matches (±1 pt) |
| Inside-10 / inside-5 share | designed carries inside the 10 / 5 ÷ team | matches on spot check |
| Short-yardage / long-down / 2-min share | share of team carries + targets in those situations | FL uses snaps; we use touches |
| HVT/G | targets + inside-10 carries per game | |
| QB scramble rate, designed runs | scrambles ÷ dropbacks; designed QB carries per game | |
| Role score (0–100) | our percentile blend of role inputs (~90%) + PPR/G (~10%) | **not** FL's Utilization Score (weights private; FL says ~75% role, 25% PPG) |

**Can't rebuild from public data:** FL's exact Utilization Score, RB route participation, slot/motion
rates, average route depth, personnel splits (all from paid charting).

Spot check vs FL Week 11 articles (Nov 16–19, 2026): 30 of 32 comparable numbers match within 5 pts;
the 2 misses are Josh Downs' 1-game TPRR (tiny route sample) and DJ Moore's YPRR. See `data/spotcheck.csv`.
