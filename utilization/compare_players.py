"""Side-by-side utilization comparison for any players, across custom week windows.
Usage: python compare_players.py "Caleb Douglas" "Josh Downs" [--windows "Season:1-10" "Wks 7-10:7-10" ...]"""
import sys, json, os, argparse
import pandas as pd
import build_utilization as b

ap = argparse.ArgumentParser()
ap.add_argument("players", nargs="+")
ap.add_argument("--season", type=int, default=2026)
ap.add_argument("--windows", nargs="*")
ap.add_argument("--out", default="data/compare.json")
a = ap.parse_args()
sys.argv = sys.argv[:1]
g, pbp_wk, snap_wk = b.build(a.season, ".cache", 4)
wk = min(pbp_wk, snap_wk)
wins = a.windows or [f"Season:1-{wk}", f"Last 4:{max(1, wk-3)}-{wk}", f"Week {wk}:{wk}"]
rows = []
for w in wins:
    label, rng = w.split(":")
    lo, hi = map(int, rng.split("-")) if "-" in rng else (int(rng), int(rng))
    s = b.summarize(g, list(range(lo, hi + 1)))
    for p in a.players:
        r = s[s.name == p]
        if r.empty:
            continue
        r = r.iloc[0].to_dict()
        n, tier, hits = b.wr_checklist(r)
        rows.append({"key": f"{p}|{label}", "player": p, "window": label, "team": r["team"], "games": r["games"],
                     **{k: r[k] for k in ["snap_pct", "route_part", "tgt", "tgt_share", "fr_share", "tprr", "yprr", "adot",
                                           "ay_share", "wopr", "catchable", "ez_tgt", "rz_tgt", "rec", "rec_yds", "ppr_pg"]},
                     "wr_checks": n, "wr_tier": tier, "wr_hits": "; ".join(hits)})
df = pd.DataFrame(rows)
print(df.drop(columns=["key", "wr_hits"]).round(3).to_string())
json.dump({"rows": json.loads(df.to_json(orient="records", double_precision=4)),
           "meta": [{"label": "Command", "value": " ".join(["compare_players.py"] + [f'"{p}"' for p in a.players] + ["--windows"] + [f'"{w}"' for w in wins])},
                    {"label": "compare_players.py", "value": open(os.path.abspath(__file__)).read(), "type": "code", "lang": "python"}]},
          open(a.out, "w"))
