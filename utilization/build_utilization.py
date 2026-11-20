#!/usr/bin/env python3
"""Weekly NFL Utilization Report, built from public nflverse data.

Recreates the metrics Fantasy Life's Utilization Report tracks (route participation,
target share, TPRR, YPRR, air yards share, WOPR, snap share, rush share, red-zone /
inside-10 usage, catchable / end-zone / play-action / 3rd-4th-down targets), computed
from nflverse play-by-play, FTN charting and PFR snap counts.

Usage:  python build_utilization.py --season 2026 [--out out_dir] [--last 4]
Outputs: utilization_<season>.json (all positions, season / last-N / latest week)
         wr.csv, te.csv, rb.csv, qb.csv
See METHODOLOGY.md for definitions and what is estimated.
"""
import argparse, json, os, sys, urllib.request
import numpy as np
import pandas as pd

BASE = "https://github.com/nflverse/nflverse-data/releases/download"
FILES = {
    "pbp": "pbp/play_by_play_{s}.parquet",
    "ftn": "ftn_charting/ftn_charting_{s}.parquet",
    "snaps": "snap_counts/snap_counts_{s}.parquet",
    "roster": "rosters/roster_{s}.parquet",
}

ROUTE_FACTOR = {"WR": 1.05, "TE": 1.0}

# Chris's WR checklist (docs/gm.md): 4/5 = WR1 profile, 3/5 = WR2 / buy riser, <=2 = TD-dependent
WR_CHECKS = [
    ("route_part", 0.70, "Route participation 70%+"),
    ("tprr", 0.22, "TPRR 22%+"),
    ("yprr", 2.0, "YPRR 2.0+"),
    ("tgt_or_fr_share", 0.25, "Target or first-read share 25%+"),
    ("wopr", 0.60, "WOPR 0.6+"),
]


def fetch(kind, season, cache):
    os.makedirs(cache, exist_ok=True)
    rel = FILES[kind].format(s=season)
    path = os.path.join(cache, os.path.basename(rel))
    if not os.path.exists(path) or kind != "roster":
        urllib.request.urlretrieve(f"{BASE}/{rel}", path)
    return pd.read_parquet(path)


def ppr_points(df):
    return (df.pass_yds * 0.04 + df.pass_td * 4 - df.ints * 2 + df.rush_yds * 0.1 + df.rush_td * 6
            + df.rec * 1 + df.rec_yds * 0.1 + df.rec_td * 6 - df.fumbles_lost * 2)


def build(season, cache, last_n):
    pbp, ftn, snaps, roster = (fetch(k, season, cache) for k in ("pbp", "ftn", "snaps", "roster"))
    pbp = pbp[(pbp.season_type == "REG") & (pbp.two_point_attempt != 1)].copy()
    ftn = ftn.rename(columns={"nflverse_game_id": "game_id", "nflverse_play_id": "play_id"})
    ftn["play_id"] = ftn.play_id.astype(float)
    pbp = pbp.merge(ftn[["game_id", "play_id", "read_thrown", "is_catchable_ball", "is_play_action"]],
                    on=["game_id", "play_id"], how="left")
    pbp["has_ftn"] = pbp.read_thrown.notna()

    f = lambda c: pbp[c].fillna(0)
    pbp["is_db"] = f("qb_dropback").eq(1) & pbp.play_type.isin(["pass", "run"])
    pbp["is_tgt"] = f("pass_attempt").eq(1) & f("sack").eq(0) & pbp.receiver_player_id.notna()
    pbp["is_drush"] = f("rush_attempt").eq(1) & f("qb_scramble").eq(0) & f("qb_kneel").eq(0) & pbp.rusher_player_id.notna()
    pbp["is_scram"] = f("qb_scramble").eq(1)
    pbp["ay"] = np.where(pbp.is_tgt, f("air_yards"), 0)
    pbp["first_read"] = pbp.is_tgt & pbp.read_thrown.astype(str).eq("1")
    pbp["catchable"] = pbp.is_tgt & pbp.is_catchable_ball.fillna(False).astype(bool)
    pbp["ez_tgt"] = pbp.is_tgt & (f("air_yards") >= pbp.yardline_100)
    pbp["rz"] = pbp.yardline_100 <= 20
    pbp["i10"] = pbp.yardline_100 <= 10
    pbp["i5"] = pbp.yardline_100 <= 5
    pbp["late_down"] = pbp.down.isin([3, 4])
    pbp["pa"] = pbp.is_tgt & pbp.is_play_action.fillna(False).astype(bool)
    pbp["two_min"] = (pbp.half_seconds_remaining <= 120)
    pbp["sdd"] = pbp.down.isin([3, 4]) & (pbp.ydstogo <= 2)          # short down & distance
    pbp["ldd"] = ((pbp.down == 2) & (pbp.ydstogo >= 8)) | (pbp.down.isin([3, 4]) & (pbp.ydstogo >= 5))  # long
    pbp["opp"] = pbp.is_tgt | pbp.is_drush

    key = ["game_id", "week", "posteam"]
    t = pbp.groupby(key).agg(
        t_db=("is_db", "sum"), t_tgt=("is_tgt", "sum"), t_ay=("ay", "sum"), t_drush=("is_drush", "sum"),
        t_fr=("first_read", "sum"), t_ftn=("has_ftn", "max"),
        t_rz_opp=("opp", lambda s: (s & pbp.loc[s.index, "rz"]).sum()),
        t_i10_rush=("is_drush", lambda s: (s & pbp.loc[s.index, "i10"]).sum()),
        t_i5_rush=("is_drush", lambda s: (s & pbp.loc[s.index, "i5"]).sum()),
        t_sdd_opp=("opp", lambda s: (s & pbp.loc[s.index, "sdd"]).sum()),
        t_ldd_opp=("opp", lambda s: (s & pbp.loc[s.index, "ldd"]).sum()),
        t_2m_opp=("opp", lambda s: (s & pbp.loc[s.index, "two_min"]).sum()),
    ).reset_index()

    # ---- receiving (per player-game)
    r = pbp[pbp.is_tgt].copy()
    r["rec_td"] = f("pass_touchdown").loc[r.index]
    rec = r.groupby(key + ["receiver_player_id"]).agg(
        tgt=("is_tgt", "sum"), rec=("complete_pass", "sum"), rec_yds=("receiving_yards", "sum"),
        ay=("ay", "sum"), fr_tgt=("first_read", "sum"), catchable=("catchable", "sum"), ez_tgt=("ez_tgt", "sum"),
        rz_tgt=("rz", "sum"), i10_tgt=("i10", "sum"), ld_tgt=("late_down", "sum"), pa_tgt=("pa", "sum"),
        sdd_tgt=("sdd", "sum"), ldd_tgt=("ldd", "sum"), tm_tgt=("two_min", "sum"), rec_td=("rec_td", "sum"),
    ).reset_index().rename(columns={"receiver_player_id": "pid"})

    # ---- rushing
    q = pbp[f("rush_attempt").eq(1) & pbp.rusher_player_id.notna() & f("qb_kneel").eq(0)].copy()
    q["drush"] = q.is_drush
    q["rush_td"] = f("rush_touchdown").loc[q.index]
    rush = q.groupby(key + ["rusher_player_id"]).agg(
        car=("rush_attempt", "sum"), drush=("drush", "sum"), scram=("is_scram", "sum"), rush_yds=("rushing_yards", "sum"),
        rush_td=("rush_td", "sum"),
        i10_car=("drush", lambda s: (s & q.loc[s.index, "i10"]).sum()),
        i5_car=("drush", lambda s: (s & q.loc[s.index, "i5"]).sum()),
        rz_car=("drush", lambda s: (s & q.loc[s.index, "rz"]).sum()),
        sdd_car=("drush", lambda s: (s & q.loc[s.index, "sdd"]).sum()),
        ldd_car=("drush", lambda s: (s & q.loc[s.index, "ldd"]).sum()),
        tm_car=("drush", lambda s: (s & q.loc[s.index, "two_min"]).sum()),
        exp_run=("rushing_yards", lambda s: (s >= 10).sum()),
    ).reset_index().rename(columns={"rusher_player_id": "pid"})

    # ---- passing
    pa = pbp[pbp.is_db & pbp.passer_player_id.notna()]
    pas = pa.groupby(key + ["passer_player_id"]).agg(
        dropbacks=("is_db", "sum"), att=("pass_attempt", "sum"), pass_yds=("passing_yards", "sum"),
        pass_td=("pass_touchdown", "sum"), ints=("interception", "sum"),
        pass_ay=("ay", "sum"),
    ).reset_index().rename(columns={"passer_player_id": "pid"})
    pas = pas.merge(pbp[pbp.is_scram].groupby(key + ["rusher_player_id"]).size().rename("db_scram").reset_index()
                    .rename(columns={"rusher_player_id": "pid"}), on=key + ["pid"], how="left")

    # ---- fumbles lost
    fl = pbp[f("fumble_lost").eq(1) & pbp.fumbled_1_player_id.notna()].groupby(
        key + ["fumbled_1_player_id"]).size().rename("fumbles_lost").reset_index().rename(columns={"fumbled_1_player_id": "pid"})

    g = rec.merge(rush, on=key + ["pid"], how="outer").merge(pas, on=key + ["pid"], how="outer").merge(fl, on=key + ["pid"], how="outer")

    # ---- snaps (PFR) -> gsis via roster
    ro = roster.dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
    pfr2gsis = ro.dropna(subset=["pfr_id"]).set_index("pfr_id").gsis_id
    snaps = snaps[snaps.game_type == "REG"].copy()
    snaps["pid"] = snaps.pfr_player_id.map(pfr2gsis)
    snaps = snaps[snaps.offense_snaps > 0].rename(columns={"team": "posteam"})
    sn = snaps[["pid", "week", "posteam", "offense_snaps", "offense_pct"]].dropna(subset=["pid"])
    g = g.merge(sn, on=["pid", "week", "posteam"], how="outer")
    gid = pbp[key].drop_duplicates()
    g = g.drop(columns="game_id").merge(gid, on=["week", "posteam"], how="left")
    g = g.merge(t, on=key, how="left")
    num = g.columns.difference(["pid", "game_id", "posteam"])
    g[num] = g[num].fillna(0)
    g["has_snaps"] = g.offense_snaps > 0
    # Estimated routes: team dropbacks x player's offensive snap share (no public 2026 route data)
    meta = ro.set_index("gsis_id")[["full_name", "position", "team", "birth_date", "years_exp"]]
    g = g.join(meta, on="pid")
    # WRs are on the field more on pass plays than on runs, so snap share reads low as a route
    # proxy; ROUTE_FACTOR was calibrated against Fantasy Life spot checks (see out/spotcheck.csv).
    # RB routes can't be estimated from snaps (pass-pro / run-only snaps), so they stay blank.
    fac = g.position.map(ROUTE_FACTOR)
    g["routes_est"] = np.where(g.has_snaps & fac.notna(), g.t_db * np.minimum(1.0, g.offense_pct * fac), np.nan)
    g["ppr"] = ppr_points(g)
    g = g[g.position.isin(["QB", "RB", "WR", "TE"])]
    return g, int(pbp.week.max()), int(snaps.week.max())


def summarize(g, weeks):
    d = g[g.week.isin(weeks)].sort_values("week")
    s = d.groupby("pid").agg(
        name=("full_name", "first"), pos=("position", "first"),
        team=("posteam", "last"), games=("game_id", "nunique"),
        **{c: (c, "sum") for c in ["tgt", "rec", "rec_yds", "ay", "fr_tgt", "catchable", "ez_tgt", "rz_tgt", "i10_tgt",
                                   "ld_tgt", "pa_tgt", "sdd_tgt", "ldd_tgt", "tm_tgt", "car", "drush", "scram", "rush_yds",
                                   "i10_car", "i5_car", "rz_car", "sdd_car", "ldd_car", "tm_car", "exp_run", "dropbacks",
                                   "att", "pass_yds", "pass_ay", "db_scram", "ppr", "rec_td", "rush_td", "pass_td",
                                   "offense_snaps"]},
    )
    # team denominators only from games the player appeared in
    ds = d[d.has_snaps]
    den = d.groupby("pid")[["t_tgt", "t_ay", "t_drush", "t_rz_opp", "t_i10_rush", "t_i5_rush",
                            "t_sdd_opp", "t_ldd_opp", "t_2m_opp"]].sum()
    snapd = ds.groupby("pid").agg(routes_est=("routes_est", lambda x: x.sum(min_count=1)), t_db_snapgames=("t_db", "sum"),
                                  snap_pct=("offense_pct", "mean"), snap_games=("game_id", "nunique"))
    # first-read share only over FTN-charted games
    dfr = d[d.t_ftn == 1].groupby("pid").agg(fr_num=("fr_tgt", "sum"), fr_den=("t_fr", "sum"))
    s = s.join(den).join(snapd).join(dfr)
    div = lambda a, b: np.where(b > 0, a / b.replace(0, np.nan), np.nan)
    s["tgt_share"] = div(s.tgt, s.t_tgt)
    s["ay_share"] = div(s.ay, s.t_ay)
    s["wopr"] = 1.5 * s.tgt_share + 0.7 * s.ay_share
    s["fr_share"] = div(s.fr_num, s.fr_den)
    s["route_part"] = div(s.routes_est, s.t_db_snapgames)
    # TPRR/YPRR use only games with snap data (routes are estimated from snaps)
    sg = ds.groupby("pid")[["tgt", "rec_yds"]].sum()
    s["tprr"] = div(sg.tgt.reindex(s.index), s.routes_est)
    s["yprr"] = div(sg.rec_yds.reindex(s.index), s.routes_est)
    s["adot"] = div(s.ay, s.tgt)
    s["rush_share"] = div(s.drush, s.t_drush)
    s["i10_share"] = div(s.i10_car, s.t_i10_rush)
    s["i5_share"] = div(s.i5_car, s.t_i5_rush)
    s["rz_share"] = div(s.rz_tgt + s.rz_car, s.t_rz_opp)
    s["sdd_share"] = div(s.sdd_tgt + s.sdd_car, s.t_sdd_opp)
    s["ldd_share"] = div(s.ldd_tgt + s.ldd_car, s.t_ldd_opp)
    s["two_min_share"] = div(s.tm_tgt + s.tm_car, s.t_2m_opp)
    s["hvt"] = s.tgt + s.i10_car                                     # high-value touches
    s["hvt_pg"] = div(s.hvt, s.games)
    s["ppr_pg"] = div(s.ppr, s.games)
    s["catchable_pg"] = div(s.catchable, s.games)
    s["exp_run_rate"] = div(s.exp_run, s.drush)
    s["scramble_rate"] = div(s.db_scram, s.dropbacks)
    s["designed_rush_pg"] = div(s.drush, s.games)
    s["tgt_or_fr_share"] = s[["tgt_share", "fr_share"]].max(axis=1)
    return s.reset_index()


def pct_rank(x):
    return x.rank(pct=True).fillna(0)


def role_score(df, pos):
    """Our own 0-100 Role Score (NOT Fantasy Life's proprietary Utilization Score).
    Percentile blend within position of the role inputs FL says drive its score."""
    w = {
        "WR": {"route_part": .15, "tgt_share": .25, "tprr": .15, "ay_share": .15, "catchable_pg": .10, "fr_share": .10, "ppr_pg": .10},
        "TE": {"route_part": .25, "tgt_share": .20, "tprr": .15, "ay_share": .10, "catchable_pg": .10, "fr_share": .10, "ppr_pg": .10},
        "RB": {"snap_pct": .15, "rush_share": .25, "tgt_share": .15, "i10_share": .15, "hvt_pg": .10, "ldd_share": .10, "ppr_pg": .10},
    }.get(pos)
    if not w:
        return pd.Series(np.nan, index=df.index)
    sc = sum(pct_rank(df[k]) * v for k, v in w.items())
    return (sc * 100).round(0)


def wr_checklist(row):
    hits = [lbl for k, thr, lbl in WR_CHECKS if pd.notna(row.get(k)) and row[k] >= thr]
    n = len(hits)
    tier = "WR1 profile" if n >= 4 else "WR2 / buy riser" if n == 3 else "TD-dependent / regression risk"
    return n, tier, hits


DASH_COLS = {
    "WR": ["key", "window", "pid", "name", "team", "games", "snap_pct", "route_part", "tgt", "tgt_share", "fr_share", "tprr", "yprr",
           "adot", "ay_share", "wopr", "catchable", "ez_tgt", "rz_tgt", "rec", "rec_yds", "ppr_pg", "role_score", "wr_checks", "wr_tier", "wr_hits"],
    "TE": ["key", "window", "pid", "name", "team", "games", "snap_pct", "route_part", "tgt", "tgt_share", "fr_share", "tprr", "yprr",
           "adot", "ay_share", "wopr", "catchable", "ez_tgt", "rz_tgt", "rec", "rec_yds", "ppr_pg", "role_score"],
    "RB": ["key", "window", "pid", "name", "team", "games", "snap_pct", "car", "rush_share", "tgt", "tgt_share", "i10_car", "i10_share",
           "i5_share", "rz_share", "sdd_share", "ldd_share", "two_min_share", "hvt_pg", "exp_run_rate", "ppr_pg", "role_score"],
    "QB": ["key", "window", "pid", "name", "team", "games", "dropbacks", "att", "pass_yds", "scramble_rate", "designed_rush_pg",
           "rush_share", "i10_car", "ppr_pg"],
}


def write_dash_json(full, out_dir, info):
    """One JSON per position for the dashboard: {rows, meta}; meta carries this script's code."""
    code = open(os.path.abspath(__file__)).read()
    for pos, cols in DASH_COLS.items():
        d = full[full.pos == pos].copy()
        d["key"] = d.window + ":" + d.pid
        if "wr_hits" in d:
            d["wr_hits"] = d.wr_hits.apply(lambda h: "; ".join(h) if isinstance(h, list) else "")
        d = d[[c for c in cols if c in d.columns]]
        rows = json.loads(d.to_json(orient="records", double_precision=4))
        meta = [{"label": "Built from", "value": "nflverse play-by-play + FTN charting + PFR snap counts, "
                 f"season {info['season']}, through Week {info['through_week']}"},
                {"label": "build_utilization.py", "value": code, "type": "code", "lang": "python"}]
        with open(os.path.join(out_dir, f"dash_{pos.lower()}.json"), "w") as fh:
            json.dump({"rows": rows, "meta": meta}, fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--out", default="data")
    ap.add_argument("--cache", default=".cache")
    ap.add_argument("--last", type=int, default=4)
    a = ap.parse_args()
    g, pbp_wk, snap_wk = build(a.season, a.cache, a.last)
    wk = min(pbp_wk, snap_wk)  # only report weeks with both pbp + snap data
    windows = {"season": list(range(1, wk + 1)), f"last{a.last}": list(range(max(1, wk - a.last + 1), wk + 1)), "week": [wk]}
    minimum = {"WR": 3, "TE": 3, "RB": 3, "QB": 2}
    out = {"season": a.season, "through_week": wk, "pbp_through_week": pbp_wk, "snaps_through_week": snap_wk,
           "windows": windows, "players": {}}
    os.makedirs(a.out, exist_ok=True)
    allrows = []
    for wname, weeks in windows.items():
        s = summarize(g, weeks)
        for pos in ["QB", "RB", "WR", "TE"]:
            d = s[s.pos == pos].copy()
            if wname == "season":
                d = d[(d.games >= minimum[pos]) | (d.tgt + d.car + d.dropbacks >= 20)]
            d["role_score"] = role_score(d, pos)
            if pos == "WR":
                c = d.apply(wr_checklist, axis=1, result_type="expand")
                d["wr_checks"], d["wr_tier"], d["wr_hits"] = c[0], c[1], c[2]
            d["window"] = wname
            allrows.append(d)
    full = pd.concat(allrows, ignore_index=True)
    full = full.replace([np.inf, -np.inf], np.nan)
    keep = ["window", "pid", "name", "pos", "team", "games", "snap_pct", "route_part", "routes_est", "tgt", "tgt_share", "fr_share",
            "tprr", "yprr", "rec", "rec_yds", "ay", "ay_share", "adot", "wopr", "catchable", "ez_tgt", "rz_tgt", "pa_tgt", "ld_tgt",
            "car", "drush", "rush_share", "rush_yds", "i10_car", "i10_share", "i5_share", "rz_share", "sdd_share", "ldd_share",
            "two_min_share", "hvt", "hvt_pg", "exp_run_rate", "dropbacks", "att", "pass_yds", "scramble_rate", "designed_rush_pg",
            "ppr", "ppr_pg", "role_score", "wr_checks", "wr_tier", "wr_hits"]
    full = full[[c for c in keep if c in full.columns]]
    for pos in ["QB", "RB", "WR", "TE"]:
        full[full.pos == pos].drop(columns=["wr_hits"], errors="ignore").to_csv(os.path.join(a.out, f"{pos.lower()}.csv"), index=False, float_format="%.4f")
    write_dash_json(full, a.out, out)
    with open(os.path.join(a.out, "run.json"), "w") as fh:
        json.dump({"rows": [{"season": a.season, "through_week": wk, "pbp_week": pbp_wk, "snaps_week": snap_wk,
                             "built": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC")}]}, fh)
    rows = json.loads(full.to_json(orient="records", double_precision=4))
    out["rows"] = rows
    del out["players"]
    with open(os.path.join(a.out, f"utilization_{a.season}.json"), "w") as fh:
        json.dump(out, fh)
    print(f"Wrote {len(rows)} rows through Week {wk} (pbp wk {pbp_wk}, snaps wk {snap_wk}) to {a.out}/")


if __name__ == "__main__":
    main()
