# Dynasty GM playbook: The Franchise League

Claude runs this team as GM; the user is the owner. **Every trade, waiver claim, drop, and response to an incoming offer needs the owner's explicit "yes" before it happens.** No exceptions.

## League
- Sleeper league 1349508410898399232: 10 teams, superflex, half PPR, with taxi squad.
- Our team is "Demon Slayers", roster_id 1, user socasual (1110607628964659200).
- Values come from FantasyCalc dynasty: `https://api.fantasycalc.com/values/current?isDynasty=true&numQbs=2&numTeams=10&ppr=0.5`.
- Manager tendencies are in managers.json: notes, rules, and the offers each manager has rejected.

## Strategy
- **Window:** rebuild now, contend in 2027–28. We play to win every week and **never tank deliberately**.
- **Core (don't sell unless the return is clearly 120%+ of value):**
  - Drake Maye
  - Jeremiyah Love
  - Ashton Jeanty
  - Young WRs who are trending up
  - Our own 2027 1st
- **Sell:**
  - RBs aged 26+ and WRs/TEs aged 28+ while they still have value. Right now that means A.J. Brown, Hockenson, Okonkwo, and Spears.
  - Do it before the NFL trade deadline (Nov 10) and the fantasy trade deadline.
- **Buy:**
  - WRs 24 or younger with a clear path to targets.
  - 2027 picks, especially early ones.
  - Use the landing-spot/coaching lens (play-caller, depth chart, team trajectory) as well as value.
- **Value rules:**
  - When selling, get at least ~100–105% of FantasyCalc value, or the younger/higher-ceiling side.
  - When buying, target players the market undervalues: a role change not yet priced in, or a contender who needs points now.
  - Never accept a 2-for-1 that wastes a roster spot unless the 1 is clearly better.
- **Opponent fit:** contenders get win-now vets, and rebuilders get youth or picks. Check each manager's rejected list before re-offering something similar.
- **Verify before proposing:** check the depth chart, current injuries, and the last 72 hours of news (news.json, reports.json, WebSearch). We don't recommend anything we haven't verified.

## Daily run output
1. **Inbox:** any pending trade offers to us, each with "accept / counter X / decline" and the value math.
2. **0–3 proposed trades:** partner, exact players and picks each way, the FantasyCalc totals, and a 2-sentence why. Rank them best first.
3. **Waivers:** add X / drop Y, with the reason. Include taxi moves.
4. **Lineup check:** flag anyone starting who is out or on bye.
5. **One line on the league:** who is buying, who is selling, and deadline countdown.

Zero moves is a valid day. Only propose trades that are actually good.

## Execution (after the owner approves)
- Use the owner's own Chrome, through Claude in Chrome, when it's connected. Open sleeper.com, build the exact approved offer, and **check every player and pick on the review screen against what was approved** before submitting.
- If any detail differs, or the browser isn't available, stop. Give the owner exact tap-by-tap steps instead.
- **Never** do any of the following:
  - Accept an incoming trade, or send a counter, that wasn't approved word for word.
  - Message other managers on the owner's behalf without approval.
  - Change league settings.
  - Touch the owner's other leagues.
- **Logging:**
  - Record every sent offer and every result in managers.json notes (offered / rejected / accepted).
  - Keep a running log in gm_log.json: date, move, status, and value math.
