"""Generates the dashboard page (index.html) for the GM Utilization Report artifact."""
import json
COLS = {
 "wr": [("name","Player","txt"),("team","Team","txt"),("games","G","int"),("snap_pct","Snap %","pct"),("route_part","Route % (est)","pct"),
        ("tgt","Tgts","int"),("tgt_share","Tgt share","pct"),("fr_share","1st-read share","pct"),("tprr","TPRR (est)","pct"),("yprr","YPRR (est)","dec2"),
        ("adot","aDOT","dec1"),("ay_share","Air yds share","pct"),("wopr","WOPR","dec2"),("catchable","Catchable","int"),("ez_tgt","EZ tgts","int"),
        ("rz_tgt","RZ tgts","int"),("ppr_pg","PPR/G","dec1"),("role_score","Role","int"),("wr_checks","Checklist","checks")],
 "te": [("name","Player","txt"),("team","Team","txt"),("games","G","int"),("snap_pct","Snap %","pct"),("route_part","Route % (est)","pct"),
        ("tgt","Tgts","int"),("tgt_share","Tgt share","pct"),("fr_share","1st-read share","pct"),("tprr","TPRR (est)","pct"),("yprr","YPRR (est)","dec2"),
        ("adot","aDOT","dec1"),("ay_share","Air yds share","pct"),("wopr","WOPR","dec2"),("catchable","Catchable","int"),("ez_tgt","EZ tgts","int"),
        ("rz_tgt","RZ tgts","int"),("ppr_pg","PPR/G","dec1"),("role_score","Role","int")],
 "rb": [("name","Player","txt"),("team","Team","txt"),("games","G","int"),("snap_pct","Snap %","pct"),("car","Carries","int"),("rush_share","Rush share","pct"),
        ("tgt","Tgts","int"),("tgt_share","Tgt share","pct"),("i10_car","Inside-10 car","int"),("i10_share","Inside-10 share","pct"),("i5_share","Inside-5 share","pct"),
        ("rz_share","Red-zone opp share","pct"),("sdd_share","Short-yardage share","pct"),("ldd_share","Long-down share","pct"),("two_min_share","2-min share","pct"),
        ("hvt_pg","HVT/G","dec1"),("exp_run_rate","10+ yd run rate","pct"),("ppr_pg","PPR/G","dec1"),("role_score","Role","int")],
 "qb": [("name","Player","txt"),("team","Team","txt"),("games","G","int"),("dropbacks","Dropbacks","int"),("att","Att","int"),("pass_yds","Pass yds","int"),
        ("scramble_rate","Scramble rate","pct"),("designed_rush_pg","Designed runs/G","dec1"),("rush_share","Team rush share","pct"),("i10_car","Inside-10 car","int"),
        ("ppr_pg","PPR/G","dec1")],
}
CMP = [("player","Player","txt"),("window","Window","txt"),("team","Team","txt"),("games","G","int"),("route_part","Route % (est)","pct"),("tgt_share","Tgt share","pct"),
       ("fr_share","1st-read share","pct"),("tprr","TPRR (est)","pct"),("yprr","YPRR (est)","dec2"),("adot","aDOT","dec1"),("ay_share","Air yds share","pct"),
       ("wopr","WOPR","dec2"),("rz_tgt","RZ tgts","int"),("ppr_pg","PPR/G","dec1"),("wr_checks","Checklist","checks")]
SPOT = [("player","Player","txt"),("window","Window","txt"),("metric","Metric","txt"),("fantasy_life","Fantasy Life","num"),("ours","Ours","num"),
        ("diff","Gap","num"),("status","Result","status")]
SORT_DEFAULT = {"wr":"role_score","te":"role_score","rb":"role_score","qb":"ppr_pg"}
TITLES = {"wr":"Wide receivers","te":"Tight ends","rb":"Running backs","qb":"Quarterbacks"}
NUMERIC = {"int","pct","dec1","dec2","num","checks"}

def thead(cols, sortable):
    out=[]
    for f,l,t in cols:
        cls = ' class="num"' if t in NUMERIC else ''
        attr = f' data-sort="{f}" tabindex="0" aria-sort="none"' if sortable else ''
        out.append(f'<th data-field="{f}"{cls}{attr}>{l}</th>')
    return "<tr>"+"".join(out)+"</tr>"

secs=[]
for pos in ["wr","te","rb","qb"]:
    hid = "" if pos=="wr" else " hidden"
    secs.append(f'''<section class="ur-sec" id="{pos}" data-pos="{pos}"{hid}>
  <h2 class="ur-h2">{TITLES[pos]}</h2>
  <div class="ur-scroll"><table class="ur-table" data-source="{pos}" data-row-key="key" data-default-sort="{SORT_DEFAULT[pos]}">
    <thead>{thead(COLS[pos], True)}</thead>
    <tbody data-draw="body-{pos}"></tbody>
  </table></div>
  <div class="ur-more"><button type="button" class="ur-btn" data-more="{pos}">Show every player</button><button type="button" class="ur-btn" data-less="{pos}" hidden>Show top 40</button></div>
</section>''')

html = f'''<meta name="dash-one-writer">
<style>
.ur {{ font-family: var(--font-anthropic-sans); color: var(--color-fg); display: grid; gap: var(--cds-gap-lg); }}
.ur-title {{ font-family: var(--font-anthropic-serif); font-weight: 400; font-size: var(--cds-font-size-title); margin: 0; text-wrap: balance; }}
.ur-lede {{ margin: 0; max-width: 68ch; line-height: 1.5; }}
.ur-asof {{ margin: 0; color: var(--color-fg-muted); font-size: var(--cds-font-size-caption); }}
.ur-controls {{ display: flex; flex-wrap: wrap; gap: var(--cds-gap-sm); align-items: center; }}
.ur-tabs {{ display: flex; flex-wrap: wrap; gap: 4px; }}
.ur-tab {{ font: inherit; font-size: var(--cds-font-size-body); padding: 6px 12px; border: 1px solid var(--color-border-line); border-radius: 999px; background: var(--color-bg); color: var(--color-fg); cursor: pointer; }}
.ur-tab[aria-selected="true"] {{ background: var(--color-fg); color: var(--color-bg); border-color: var(--color-fg); }}
.ur-tab:focus-visible, .ur-btn:focus-visible, .ur-table th:focus-visible {{ outline: 2px solid var(--color-fg); outline-offset: 2px; }}
.ur-search {{ font: inherit; padding: 6px 10px; border: 1px solid var(--color-border-line); border-radius: var(--cds-radius); background-color: var(--color-bg); color: var(--color-fg); min-width: 0; width: 14rem; max-width: 100%; }}
.ur-h2 {{ font-size: var(--cds-font-size-heading); font-weight: var(--cds-font-weight-medium); margin: 0 0 var(--cds-gap-sm); }}
.ur-scroll {{ overflow-x: auto; border: 1px solid var(--color-border-line); border-radius: var(--cds-radius); }}
.ur-table {{ border-collapse: collapse; width: 100%; font-size: var(--cds-font-size-caption); font-variant-numeric: tabular-nums; }}
.ur-table th, .ur-table td {{ padding: 6px 8px; text-align: left; white-space: nowrap; border-bottom: 1px solid var(--color-border-line); }}
.ur-table th {{ position: sticky; top: 0; background: var(--color-panel); font-weight: var(--cds-font-weight-medium); color: var(--color-fg-muted); user-select: none; }}
.ur-table th[data-sort] {{ cursor: pointer; }}
.ur-table th[aria-sort="descending"]::after {{ content: " \\2193"; }}
.ur-table th[aria-sort="ascending"]::after {{ content: " \\2191"; }}
.ur-table .num {{ text-align: right; }}
.ur-table th:first-child, .ur-table td:first-child {{ position: sticky; left: 0; background: var(--color-bg); z-index: 1; }}
.ur-table th:first-child {{ background: var(--color-panel); z-index: 2; }}
.ur-table tr.ur-hl td {{ background: var(--color-panel); }}
.ur-table td.hit {{ color: var(--color-ok); font-weight: var(--cds-font-weight-medium); }}
.ur-pill {{ display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: var(--cds-font-size-caption); border: 1px solid currentColor; }}
.ur-pill.t1 {{ color: var(--color-ok); }} .ur-pill.t2 {{ color: var(--color-warn); }} .ur-pill.t3 {{ color: var(--color-bad); }}
.ur-more {{ display: flex; gap: var(--cds-gap-sm); margin-top: var(--cds-gap-sm); }}
.ur-btn {{ font: inherit; font-size: var(--cds-font-size-caption); padding: 4px 10px; border: 1px solid var(--color-border-line); border-radius: var(--cds-radius); background: var(--color-bg); color: var(--color-fg); cursor: pointer; }}
.ur-note {{ color: var(--color-fg-muted); font-size: var(--cds-font-size-caption); margin: var(--cds-gap-sm) 0 0; max-width: 80ch; line-height: 1.5; }}
.ur-card {{ background: var(--color-panel); border: 1px solid var(--color-border-line); border-radius: var(--cds-radius); padding: var(--cds-pad-lg); display: grid; gap: var(--cds-gap-md); }}
.ur-take {{ display: grid; gap: var(--cds-gap-sm); line-height: 1.55; max-width: 80ch; }}
.ur-take p {{ margin: 0; }}
.ur-defs {{ line-height: 1.55; }}
.ur-defs summary {{ cursor: pointer; font-weight: var(--cds-font-weight-medium); }}
.ur-defs dl {{ display: grid; grid-template-columns: minmax(8rem, max-content) 1fr; gap: 6px 16px; margin: var(--cds-gap-md) 0 0; }}
.ur-defs dt {{ font-weight: var(--cds-font-weight-medium); }} .ur-defs dd {{ margin: 0; }}
@media (max-width: 560px) {{ .ur-defs dl {{ grid-template-columns: 1fr; }} .ur-defs dd {{ margin-bottom: 8px; }} }}
@media print {{ .ur-sec[hidden] {{ display: block !important; }} .ur-scroll {{ overflow: visible; }} .ur-controls, .ur-more {{ display: none; }} }}
</style>
<div class="ur">
  <header id="top" style="display:grid;gap:var(--cds-gap-sm)">
    <h1 class="ur-title">GM Utilization Report</h1>
    <p class="ur-lede" data-read lang="en">Through Week <b data-draw="thru">—</b>, <b data-draw="topwr">—</b> owns the best WR role in football by our Role Score, and <b data-draw="wr1n">—</b> WRs check at least 4 of the 5 boxes on Chris's WR checklist this season.</p>
    <p class="ur-asof" data-draw="asof">—</p>
  </header>

  <div class="ur-controls" id="controls">
    <div class="ur-tabs" role="tablist" aria-label="Position">
      <button type="button" class="ur-tab" role="tab" data-tab="wr" aria-selected="true">WR</button>
      <button type="button" class="ur-tab" role="tab" data-tab="te" aria-selected="false">TE</button>
      <button type="button" class="ur-tab" role="tab" data-tab="rb" aria-selected="false">RB</button>
      <button type="button" class="ur-tab" role="tab" data-tab="qb" aria-selected="false">QB</button>
      <button type="button" class="ur-tab" role="tab" data-tab="compare" aria-selected="false">Douglas vs Downs</button>
      <button type="button" class="ur-tab" role="tab" data-tab="spotcheck" aria-selected="false">Accuracy check</button>
    </div>
    <select class="dash-select" id="ur-window" aria-label="Weeks">
      <option value="season">Season to date</option>
      <option value="last4">Last 4 weeks</option>
      <option value="week">Latest week</option>
    </select>
    <input class="ur-search" id="ur-q" type="search" placeholder="Find a player or team" aria-label="Find a player or team">
  </div>

  {"".join(secs)}

  <section class="ur-sec" id="compare" hidden>
    <h2 class="ur-h2">Caleb Douglas vs Josh Downs</h2>
    <div class="ur-card">
      <div class="ur-scroll"><table class="ur-table" data-source="compare" data-row-key="key">
        <thead>{thead(CMP, False)}</thead>
        <tbody data-draw="body-compare"></tbody>
      </table></div>
      <div class="ur-take" data-read lang="en">
        <p><b>Verdict: Douglas is the better dynasty asset, and it isn't close on role.</b> As of Week 10, Douglas has the alpha profile in Miami: deep aDOT, the biggest air-yards share of the two, a first-read share above 30%, and YPRR above 2.0. Since he came back in Week 7 he checks all 5 boxes, which is a WR1 profile. He is 23 and a 2026 rookie, so the role is still growing.</p>
        <p>Downs never showed a WR1 profile in Indianapolis either. His YPRR sat near 1.2 to 1.4, his aDOT is short, and his WOPR stayed under 0.5. That makes him a volume slot receiver whose points lean on catches and touchdowns. In his first Kansas City game he ran a route on roughly 1 in 5 dropbacks (Fantasy Life had 21%) and drew 5 targets on those few routes. That target rate is exciting but it is one game on about 8 routes, so it is noise until his route share climbs.</p>
        <p>What to watch: Downs' route share over the next two or three KC games. If it gets above 60% next to Mahomes he becomes a real buy-low WR3 with upside. Until then, value Douglas well above Downs, and treat Downs as a cheap hold or a throw-in, not a centerpiece.</p>
      </div>
    </div>
    <p class="ur-note">The table uses its own fixed week windows, so the Weeks menu above does not change it.</p>
  </section>

  <section class="ur-sec" id="spotcheck" hidden>
    <h2 class="ur-h2">How close we are to Fantasy Life</h2>
    <p class="ur-note" style="margin:0 0 var(--cds-gap-sm)"><span data-draw="spotsum">—</span> We checked our numbers against figures Fantasy Life printed in its Week 11 articles (Nov 16 to 19). Shares and counts match within a point or two. Route participation is an estimate and lands within about 5 points for WRs. RB route participation can't be rebuilt from public data, so we leave it blank.</p>
    <div class="ur-scroll"><table class="ur-table" data-source="spotcheck" data-row-key="key">
      <thead>{thead(SPOT, False)}</thead>
      <tbody data-draw="body-spotcheck"></tbody>
    </table></div>
  </section>

  <details class="ur-defs" id="definitions">
    <summary>How each number is worked out, and what we can't rebuild</summary>
    <dl>
      <dt>Route % (est)</dt><dd>Share of team dropbacks the player ran a route on. Public 2026 data has no per-play routes, so we estimate it as team dropbacks times the player's offensive snap share, nudged up 5% for WRs because they are on the field more on passing downs. That nudge was set from Fantasy Life's own numbers. For TEs it is raw, and it runs high for blocking TEs. RBs are left blank.</dd>
      <dt>Tgt share</dt><dd>Player targets divided by team targets, in games he played. Matches Fantasy Life's definition.</dd>
      <dt>1st-read share</dt><dd>Share of the team's first-read targets that went to him, from FTN charting. This is the "first-read share" in Chris's checklist.</dd>
      <dt>TPRR / YPRR (est)</dt><dd>Targets and receiving yards per estimated route. They move with the route estimate, so treat 1 to 2 points of TPRR as noise.</dd>
      <dt>aDOT, Air yds share</dt><dd>Average air yards per target, and his share of all team air yards.</dd>
      <dt>WOPR</dt><dd>1.5 × target share + 0.7 × air yards share.</dd>
      <dt>Catchable, EZ, RZ</dt><dd>Catchable targets (FTN), end-zone targets (air yards reach the goal line) and targets inside the 20.</dd>
      <dt>Rush share</dt><dd>His designed carries divided by the team's designed carries (QB scrambles and kneels left out).</dd>
      <dt>Inside-10 / Inside-5 share</dt><dd>His share of the team's designed carries inside the opponent's 10 or 5.</dd>
      <dt>Red-zone, short-yardage, long-down, 2-min share</dt><dd>His share of team carries plus targets inside the 20; on 3rd or 4th and 2 or less; on 2nd and 8+ or 3rd/4th and 5+; and in the last two minutes of each half. Fantasy Life measures these by snaps, which public data doesn't have per play, so ours count touches instead.</dd>
      <dt>HVT/G</dt><dd>High-value touches per game: targets plus carries inside the 10.</dd>
      <dt>Role score</dt><dd>Our own 0 to 100 score, not Fantasy Life's Utilization Score, whose weights are private. It is a percentile blend within the position of the same inputs Fantasy Life lists (route participation or snaps, rush and target share, air yards, catchable targets, red-zone work) at about 90%, plus PPR per game at 10%.</dd>
      <dt>Checklist (WR)</dt><dd>Chris's 5 marks: route % 70+, TPRR 22%+, YPRR 2.0+, target or first-read share 25%+, WOPR 0.6+. 4 or 5 is a WR1 profile, 3 is a WR2 or buy riser, 2 or fewer is TD-dependent.</dd>
      <dt>Not rebuilt</dt><dd>Fantasy Life's exact Utilization Score, RB route participation, slot and motion rates, route depth, and personnel splits. Those come from paid charting data.</dd>
    </dl>
  </details>
</div>
<script>
window.UR = (function () {{
  const COLS = {json.dumps({k: v for k, v in COLS.items()} | {"compare": CMP, "spotcheck": SPOT})};
  const st = {{ win: 'season', q: '', all: {{}}, sort: {{}} }};
  document.querySelectorAll('table[data-default-sort]').forEach((t) => {{
    const pos = t.getAttribute('data-source'); st.sort[pos] = {{ f: t.getAttribute('data-default-sort'), d: -1 }};
  }});
  const pct = d3.format('.0%'), d1 = d3.format('.1f'), d2 = d3.format('.2f');
  function fmt(v, t) {{
    if (v === null || v === undefined || v === '' || (typeof v === 'number' && !isFinite(v))) return '–';
    if (t === 'pct') return pct(v);
    if (t === 'dec1') return d1(v);
    if (t === 'dec2') return d2(v);
    if (t === 'int') return d3.format(',')(Math.round(v));
    if (t === 'num') return Math.abs(v) < 1 && v !== 0 ? (v * 100).toFixed(1) + (t === 'num' ? '' : '') : String(v);
    return String(v);
  }}
  function tier(n) {{ return n >= 4 ? 't1' : n === 3 ? 't2' : 't3'; }}
  function cell(tr, r, c) {{
    const [f, , t] = c; const td = document.createElement('td');
    if (t !== 'txt' && t !== 'status') td.className = 'num';
    if (t === 'checks') {{
      const s = document.createElement('span'); s.className = 'ur-pill ' + tier(r.wr_checks);
      s.textContent = (r.wr_checks ?? '–') + '/5'; s.title = r.wr_hits || 'No marks hit'; td.appendChild(s);
    }} else if (t === 'status') {{
      const s = document.createElement('span');
      s.className = 'ur-pill ' + (r.status === 'match' ? 't1' : r.status === 'close' ? 't2' : 't3'); s.textContent = r.status; td.appendChild(s);
    }} else if (t === 'num') {{
      const isCount = r.metric === 'tgt' || r.metric === 'ay' || r.metric === 'yprr';
      td.textContent = r[f] === null || r[f] === undefined ? '–' : isCount ? d2(r[f]).replace(/\\.00$/, '') : (f === 'diff' ? (r[f] > 0 ? '+' : '') : '') + (r[f] * 100).toFixed(0) + (f === 'diff' ? ' pts' : '%');
    }} else td.textContent = fmt(r[f], t);
    tr.appendChild(td);
  }}
  function body(pos, el, opts) {{
    const g = dash.data(pos);
    const cols = COLS[pos];
    if (g.status !== 'ok') {{
      const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = cols.length;
      td.textContent = g.status === 'error' ? 'This table did not load.' : '—'; tr.appendChild(td); el.replaceChildren(tr); return;
    }}
    let rows = g.data.slice();
    if (opts && opts.windowed) rows = rows.filter((r) => r.window === st.win);
    const q = st.q.trim().toLowerCase();
    if (q && opts && opts.windowed) rows = rows.filter((r) => (r.name || '').toLowerCase().includes(q) || (r.team || '').toLowerCase() === q);
    const s = st.sort[pos];
    if (s) rows.sort((a, b) => {{
      const x = a[s.f], y = b[s.f];
      if (typeof x === 'string' || typeof y === 'string') return s.d * String(x ?? '').localeCompare(String(y ?? ''));
      return s.d * (((x ?? -Infinity)) - ((y ?? -Infinity)));
    }});
    if (opts && opts.windowed && !st.all[pos] && !q) rows = rows.slice(0, 40);
    el.replaceChildren(...rows.map((r) => {{
      const tr = document.createElement('tr'); tr.setAttribute('data-key', encodeURIComponent(r.key));
      if (/Caleb Douglas|Josh Downs/.test(r.name || r.player || '') && pos !== 'compare') tr.className = 'ur-hl';
      cols.forEach((c) => cell(tr, r, c)); return tr;
    }}));
    if (!rows.length) {{
      const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = cols.length;
      td.textContent = 'No players match.'; tr.appendChild(td); el.replaceChildren(tr);
    }}
  }}
  return {{ st, body }};
}})();
</script>
<script>
['wr', 'te', 'rb', 'qb'].forEach((pos) => dash.draw('body-' + pos, (el) => UR.body(pos, el, {{ windowed: true }})));
dash.draw('body-compare', (el) => UR.body('compare', el, {{}}));
dash.draw('body-spotcheck', (el) => UR.body('spotcheck', el, {{}}));

dash.calc('wr1_count', {{
  inputs: ['wr'], title: 'WRs with a WR1 checklist profile',
  description: 'Season-to-date WRs hitting 4 or 5 of the 5 checklist marks.',
  fn: (wr) => wr.filter((r) => r.window === 'season' && r.wr_checks >= 4).length,
}});
dash.calc('spot_matches', {{
  inputs: ['spotcheck'], title: 'Checks that match Fantasy Life',
  description: 'Spot checks where our number is within 5 points (or 5 targets/yards) of Fantasy Life, out of the checks we can compute.',
  fn: (spotcheck) => [{{ matched: spotcheck.filter((r) => r.status === 'match').length, comparable: spotcheck.filter((r) => r.status !== 'not reproducible').length }}],
}});

dash.draw('thru', (el) => {{
  const g = dash.data('run'); el.replaceChildren();
  const s = document.createElement('span'); s.setAttribute('data-source', 'run'); s.setAttribute('data-field', 'through_week'); s.setAttribute('data-row', '0');
  s.textContent = g.status === 'ok' && g.data[0] ? String(g.data[0].through_week) : '—'; el.appendChild(s);
}});
dash.draw('topwr', (el) => {{
  const g = dash.data('wr'); el.replaceChildren();
  if (g.status !== 'ok') {{ el.textContent = '—'; return; }}
  const top = g.data.filter((r) => r.window === 'season').sort((a, b) => b.role_score - a.role_score)[0];
  if (!top) {{ el.textContent = '—'; return; }}
  const n = document.createElement('span'); n.setAttribute('data-source', 'wr'); n.setAttribute('data-field', 'name'); n.setAttribute('data-where', 'key=' + encodeURIComponent(top.key));
  n.textContent = top.name; el.append(n, ' (');
  const sc = document.createElement('span'); sc.setAttribute('data-source', 'wr'); sc.setAttribute('data-field', 'role_score'); sc.setAttribute('data-where', 'key=' + encodeURIComponent(top.key));
  sc.textContent = String(top.role_score); el.append(sc, ')');
}});
dash.draw('wr1n', (el) => {{
  const g = dash.data('wr1_count'); el.replaceChildren();
  const s = document.createElement('span'); s.setAttribute('data-source', 'wr1_count');
  s.textContent = g.status === 'ok' && g.data !== null ? String(g.data) : '—'; el.appendChild(s);
}});
dash.draw('spotsum', (el) => {{
  const g = dash.data('spot_matches'); el.replaceChildren();
  if (g.status !== 'ok' || !g.data || !g.data[0]) {{ el.textContent = '—'; return; }}
  const a = document.createElement('span'); a.setAttribute('data-source', 'spot_matches'); a.setAttribute('data-field', 'matched'); a.setAttribute('data-row', '0'); a.textContent = String(g.data[0].matched);
  const b = document.createElement('span'); b.setAttribute('data-source', 'spot_matches'); b.setAttribute('data-field', 'comparable'); b.setAttribute('data-row', '0'); b.textContent = String(g.data[0].comparable);
  el.append(a, ' of ', b, ' comparable checks match.');
}});
dash.draw('asof', (el) => {{
  const g = dash.data('run');
  if (g.status !== 'ok' || !g.data[0]) {{ el.textContent = '—'; return; }}
  const r = g.data[0];
  el.textContent = 'Built ' + r.built + ' from public nflverse play-by-play, FTN charting and snap counts. Latest week = Week ' + r.through_week + '; last 4 = Weeks ' + Math.max(1, r.through_week - 3) + ' to ' + r.through_week + '. Rows highlighted are Douglas and Downs.';
}});
</script>
<script>
(function () {{
  const sections = () => document.querySelectorAll('.ur-sec');
  function openTab(id) {{
    sections().forEach((s) => {{ s.hidden = s.id !== id; }});
    document.querySelectorAll('.ur-tab').forEach((b) => b.setAttribute('aria-selected', b.getAttribute('data-tab') === id ? 'true' : 'false'));
    const w = document.getElementById('ur-window'); if (w) w.disabled = id === 'compare' || id === 'spotcheck';
    dash.setLink(id);
  }}
  document.querySelectorAll('.ur-tab').forEach((b) => b.addEventListener('click', () => openTab(b.getAttribute('data-tab'))));
  const w = document.getElementById('ur-window');
  if (w) w.addEventListener('change', () => {{ UR.st.win = w.value; ['wr', 'te', 'rb', 'qb'].forEach((p) => dash.draw('body-' + p)); }});
  const q = document.getElementById('ur-q');
  if (q) q.addEventListener('input', () => {{ UR.st.q = q.value; ['wr', 'te', 'rb', 'qb'].forEach((p) => dash.draw('body-' + p)); }});
  document.querySelectorAll('th[data-sort]').forEach((th) => {{
    const go = () => {{
      const table = th.closest('table'); const pos = table.getAttribute('data-source'); const f = th.getAttribute('data-sort');
      const cur = UR.st.sort[pos] || {{}};
      UR.st.sort[pos] = {{ f, d: cur.f === f ? -cur.d : (f === 'name' || f === 'team' ? 1 : -1) }};
      table.querySelectorAll('th[data-sort]').forEach((h) => h.setAttribute('aria-sort', h === th ? (UR.st.sort[pos].d < 0 ? 'descending' : 'ascending') : 'none'));
      dash.draw('body-' + pos);
    }};
    th.addEventListener('click', go);
    th.addEventListener('keydown', (e) => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); go(); }} }});
    const pos = th.closest('table').getAttribute('data-source');
    if (UR.st.sort[pos] && UR.st.sort[pos].f === th.getAttribute('data-sort')) th.setAttribute('aria-sort', 'descending');
  }});
  document.querySelectorAll('[data-more]').forEach((b) => b.addEventListener('click', () => {{
    const p = b.getAttribute('data-more'); UR.st.all[p] = true; b.hidden = true;
    document.querySelectorAll('[data-less="' + p + '"]').forEach((x) => {{ x.hidden = false; }}); dash.draw('body-' + p);
  }}));
  document.querySelectorAll('[data-less]').forEach((b) => b.addEventListener('click', () => {{
    const p = b.getAttribute('data-less'); UR.st.all[p] = false; b.hidden = true;
    document.querySelectorAll('[data-more="' + p + '"]').forEach((x) => {{ x.hidden = false; }}); dash.draw('body-' + p);
  }}));
  const h = (location.hash || '').slice(1);
  if (['wr', 'te', 'rb', 'qb', 'compare', 'spotcheck'].includes(h)) openTab(h);
}})();
</script>
'''
open("index.html","w").write(html)
print(len(html))
