#!/usr/bin/env python3
"""Render RESULTS.md tables from results.json (post-hoc formatting only; no new statistics except the labelled dispersion check)."""
import json, math, sys
sys.path.insert(0, ".")
from analyze import fit

R = json.load(open("results.json"))
U = R["units"]
f = lambda x, n=2: "n/a" if x is None else f"{x:.{n}f}"
out = []
w = out.append

def pooled_table(name):
    w("| p | trials (ok) | successes | rate | 95% CI (Garwood) | p x rate | non-line | recovers l | F_p-box relation |")
    w("|--:|--:|--:|--:|:--|--:|--:|--:|--:|")
    for p, c in U[name]["cells"].items():
        ci = c["ci95"]
        w(f"| {p} | {c['T']} | {c['succ']} | {c['rate']:.3e} | [{ci[0]:.2e}, {ci[1]:.2e}] | {int(p)*c['rate']:.2f} | {c['nonline']} | {c['dl']} | {c['fp_rel']} |")

for name in ("pool/all", "pool/generic", "pool/j0"):
    w(f"### {name}\n"); pooled_table(name); w("")
tables = "\n".join(out); out.clear()

w("| unit (curve / lift / r) | successes p>=127 | beta | 99.7% interval | C0_hat | class | non-line succ. (p>=127) |")
w("|:--|--:|--:|:--|--:|:--|--:|")
for name, u in U.items():
    a = u["fit_all_success"]; b = u["fit_nonline"]
    iv = "n/a" if a["beta"] is None else f"[{a['lo']:.2f}, {a['hi']:.2f}]"
    w(f"| {name.replace('family/','') if name.startswith('family/') else name} | {a['succ']} | {f(a['beta'])} | {iv} | {f(a.get('C0_hat'))} | {a['cls']} | {b['succ']} |")
units = "\n".join(out); out.clear()

# post-hoc Pearson dispersion of the pooled fit (not preregistered)
disp = {}
for name in ("pool/all", "pool/generic", "pool/j0"):
    pts = [(int(p), c["T"], c["succ"]) for p, c in U[name]["cells"].items() if int(p) >= R["window_min_p"]]
    b, se = fit(pts)
    # recover alpha by one-dimensional ML at the fitted beta
    xs = [(math.log(p), T, S) for p, T, S in pts]
    a = math.log(sum(S for _, _, S in xs) / sum(T * math.exp(b * x) for x, T, _ in xs))
    chi = sum((S - T * math.exp(a + b * x)) ** 2 / (T * math.exp(a + b * x)) for x, T, S in xs)
    disp[name] = chi / (len(xs) - 2)
open("dispersion.json", "w").write(json.dumps(disp, indent=1))
open("_tables.md", "w").write(f"{tables}\n\n#### Units\n\n{units}\n")
print(disp)
