"""Analysis fixed in PROTOCOL.md: per-trial cost ratios with a paired target bootstrap."""
import json
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = [json.loads(l) for l in (HERE / "data" / "rows.jsonl").read_text().splitlines()]
ARMS = {0: "W64a", 1: "W64b", 2: "W128", 3: "W256", 4: "W512"}
bad = [r for r in rows if not (r["solved"] and r["verified"])]
targets = sorted({r["target"] for r in rows})
# per arm, per target: summed ns and trials over the rounds
agg = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
for r in rows:
    a = agg[ARMS[r["arm"]]][r["target"]]
    a[0] += r["ns"]
    a[1] += r["trials"]
    a[2] += 1

def stats(arm, ts):
    ns = sum(agg[arm][t][0] for t in ts)
    tr = sum(agg[arm][t][1] for t in ts)
    n = sum(agg[arm][t][2] for t in ts)
    return ns, tr, n

def merged(ts, arms):
    return [sum(x) for x in zip(*(stats(a, ts) for a in arms))]

def cpt(ts, arms):
    ns, tr, _ = merged(ts, arms)
    return ns / tr

def per_descent(ts, arms):
    ns, _, n = merged(ts, arms)
    return ns / n

def trials_mean(ts, arms):
    _, tr, n = merged(ts, arms)
    return tr / n

BASE = ["W64a", "W64b"]
rng = random.Random(1)
B = 10_000
boots = [[rng.choice(targets) for _ in targets] for _ in range(B)]

def ci(f):
    v = sorted(f(b) for b in boots)
    return [v[int(0.025 * B)], v[int(0.975 * B) - 1]]

out = {"rows": len(rows), "invalid_rows": len(bad), "targets": len(targets), "arms": {}}
for arm in ARMS.values():
    ns, tr, n = stats(arm, targets)
    out["arms"][arm] = {
        "ns_per_trial": ns / tr,
        "mean_trials": tr / n,
        "mean_ns_per_descent": ns / n,
        "descents": n,
    }
aa = lambda ts: cpt(ts, ["W64a"]) / cpt(ts, ["W64b"])
out["aa_ratio"] = aa(targets)
out["aa_ci95"] = ci(aa)
h_aa = max(abs(out["aa_ratio"] - 1), (out["aa_ci95"][1] - out["aa_ci95"][0]) / 2)
out["h_aa"] = h_aa
for arm in ["W128", "W256", "W512"]:
    f = lambda ts, a=arm: cpt(ts, BASE) / cpt(ts, [a])
    g = lambda ts, a=arm: per_descent(ts, BASE) / per_descent(ts, [a])
    t = lambda ts, a=arm: trials_mean(ts, [a]) / trials_mean(ts, BASE)
    out["arms"][arm].update(
        rho=f(targets), rho_ci95=ci(f),
        per_descent_ratio=g(targets), per_descent_ci95=ci(g),
        trials_ratio=t(targets), trials_ci95=ci(t),
    )
best = max(["W128", "W256", "W512"], key=lambda a: out["arms"][a]["rho"])
b = out["arms"][best]
adopt = (out["invalid_rows"] == 0 and b["rho_ci95"][0] > 1 + h_aa and b["per_descent_ci95"][1] >= 1)
out["w_star"] = best
out["decision"] = f"adopt {best}" if adopt else "keep W64"
(HERE / "data" / "analysis.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
