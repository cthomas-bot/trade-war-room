Trade War Room backup (Oct 14, 2026)

index.html          The app (trade engine is in <script id="engine">). This is what Netlify serves.
news.json           Latest daily news (Oct 13, 34 players).
yahoo_league.json   All Yahoo league rosters.
yahoo_roster.json   Your Yahoo team.
status_snapshot.json + scripts/ + .github/workflows/
                    Hourly GitHub Action that refreshes injury statuses (from fantasydynastysuggester).
tools/              Helper scripts used for the daily news job and trade checks (not needed by the site).

To rebuild on a new GitHub account:
1. Create a new repo (e.g. trade-war-room) and upload everything in this folder except tools/ (optional).
2. In Netlify, point the site at the new repo (Site configuration > Build & deploy > Link repository).
3. Start a new Claude Code session with the new repo selected so the daily news job can push again.
