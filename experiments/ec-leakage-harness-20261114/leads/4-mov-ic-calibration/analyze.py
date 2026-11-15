import json, math, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = json.load(open("results.json")); rows = [r for r in d["rows"] if r["mov_all_ok"]]
b = np.array([r["rbits"] for r in rows]); tm = np.array([r["mov_median_total"] for r in rows])
sl, ic = np.polyfit(b, np.log2(tm), 1)       # t ~ r^sl
gb, gt, gcens = [], [], []
for r in d["rows"]:
    for g in r["generic"]["trials"]:
        gb.append(r["generic"]["rbits"]); gt.append(g["seconds"]); gcens.append(not g["finished"])
gb, gt, gcens = map(np.array, (gb, gt, gcens))
fin = ~gcens; gsl = np.polyfit(gb[fin], np.log2(gt[fin]), 1)[0] if fin.sum() >= 2 else None
# generic median of finished per size for slope
sizes = sorted(set(gb[fin])); gm = [np.median(gt[fin & (gb == s)]) for s in sizes]
gsl_med = np.polyfit(sizes, np.log2(gm), 1)[0]
# last-two-points slopes of MOV
loc = np.diff(np.log2(tm)) / np.diff(b)
res = dict(mov_fit_exponent_in_r=sl, mov_fit_intercept_log2=ic, mov_local_slopes=loc.tolist(),
           generic_fit_exponent_in_r_finished_only=gsl, generic_fit_exponent_medians=gsl_med, rho_exponent=0.5,
           mov_bits=b.tolist(), mov_median=tm.tolist())
json.dump(res, open("fit.json", "w"), indent=1)
print(json.dumps(res, indent=1))
fig, ax = plt.subplots(figsize=(5, 3.4))
ax.semilogy(b, tm, "o-", c="#2a7", label=f"MOV transfer + znlog (median; fit r^{sl:.2f})")
ax.semilogy(gb[fin], gt[fin], "s", c="#c44", label="generic elllog finished")
ax.semilogy(gb[gcens], gt[gcens], "v", c="#c44", mfc="none", label="generic elllog timed out (budget)")
ax.set_xlabel("subgroup bits log2 r"); ax.set_ylabel("seconds"); ax.legend(fontsize=6); ax.set_title("[pcc:unverified] weak-curve calibration", fontsize=8)
fig.tight_layout(); fig.savefig("time_vs_bits.png", dpi=70)
