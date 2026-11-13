#!/usr/bin/env python3
"""Frozen analysis for PROTOCOL.md: counts, Poisson slope fits, classification, SVG."""
import glob, json, math, sys, collections

WINDOW_MIN_P = 127
Z = 2.97             # two-sided 99.7% (Bonferroni over the 16 units, 0.05/16)
LEAD_LOWER = -0.75
MIN_INFORM, MIN_LEAD = 10, 30


def load(d):
    rows = []
    for f in sorted(glob.glob(d + "/rows-p*.jsonl")):
        rows += [json.loads(l) for l in open(f)]
    return rows


def pois_cdf(k, mu):
    t = s = math.exp(-mu)
    for i in range(1, k + 1):
        t *= mu / i; s += t
    return s


def garwood(k, alpha=0.05):
    lo = 0.0
    if k > 0:
        a, b = 0.0, k + 10.0 * math.sqrt(k) + 10
        for _ in range(100):
            m = (a + b) / 2
            (a, b) = (m, b) if 1 - pois_cdf(k - 1, m) < alpha / 2 else (a, m)
        lo = (a + b) / 2
    a, b = 0.0, k + 10.0 * math.sqrt(k) + 20
    for _ in range(100):
        m = (a + b) / 2
        (a, b) = (m, b) if pois_cdf(k, m) > alpha / 2 else (a, m)
    return lo, (a + b) / 2


def fit(points):
    """Poisson ML for lambda_p = T_p exp(a + b ln p); points=[(p, T, S)]. Returns b, se, a, loglik info."""
    pts = [(math.log(p), T, S) for p, T, S in points if T > 0]
    tot = sum(S for _, _, S in pts)
    if tot == 0 or len(pts) < 2: return None
    a, b = math.log(tot / sum(T for _, T, _ in pts)), -1.0
    lx0 = sum(x * T for x, T, _ in pts) / sum(T for _, T, _ in pts)
    for _ in range(200):
        g = [0.0, 0.0]; H = [[0.0, 0.0], [0.0, 0.0]]
        for x, T, S in pts:
            x = x - lx0
            mu = T * math.exp(a + b * x)
            g[0] += S - mu; g[1] += (S - mu) * x
            H[0][0] += mu; H[0][1] += mu * x; H[1][1] += mu * x * x
        H[1][0] = H[0][1]
        det = H[0][0] * H[1][1] - H[0][1] ** 2
        if det <= 0: return None
        da = (H[1][1] * g[0] - H[0][1] * g[1]) / det
        db = (-H[1][0] * g[0] + H[0][0] * g[1]) / det
        a += da; b += db
        if abs(da) + abs(db) < 1e-12: break
    se = math.sqrt(H[0][0] / det)
    return b, se


def fixed_c(points):
    """C0-hat with beta fixed at -1: lambda = C/p, ML C = sum S / sum(T/p)."""
    den = sum(T / p for p, T, _ in points)
    return sum(S for _, _, S in points) / den if den else None


def classify(points):
    S = sum(s for _, _, s in points)
    f = fit(points)
    if S < MIN_INFORM or f is None: return dict(cls="uninformative", succ=S, beta=None)
    b, se = f
    lo, hi = b - Z * se, b + Z * se
    if lo <= -1 <= hi: cls = "tracks 1/p"
    elif hi < -1: cls = "faster than 1/p"
    elif S >= MIN_LEAD and lo > LEAD_LOWER: cls = "LEAD (slower than 1/p)"
    else: cls = "slower than 1/p, below lead threshold"
    return dict(cls=cls, succ=S, beta=b, se=se, lo=lo, hi=hi, C0_hat=fixed_c(points))


def main(d):
    rows = load(d)
    ok = [r for r in rows if r["status"] == "ok"]
    status = collections.Counter(r["status"] for r in rows)
    primes = sorted({r["p"] for r in rows})
    units = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0]))
    # cell tuple: T_ok, S_all, S_nonline, S_dl, T_fprel, S_fprel
    def add(key, p, r):
        u = units[key][p]
        u[0] += 1; u[1] += r["success"]
        line = r["success"] and r["weight"] == 3 and all(abs(k) <= 1 for k in r["rel"])
        u[2] += int(bool(r["success"] and not line))
        u[3] += r.get("dl_recovered", 0) if r["success"] else 0
        u[4] += r.get("fp_rel", 0)
    for r in ok:
        add(("family", r["family"], r["lift"], r["r"]), r["p"], r)
        add(("pool", r["family"]), r["p"], r)
        add(("pool", "all"), r["p"], r)
    out = dict(window_min_p=WINDOW_MIN_P, z=Z, status_counts=dict(status), primes=primes,
               n_rows=len(rows), n_ok=len(ok), units={})
    for key, per in sorted(units.items()):
        name = "/".join(map(str, key))
        cells = {p: dict(T=v[0], succ=v[1], nonline=v[2], dl=v[3], fp_rel=v[4],
                         rate=v[1] / v[0] if v[0] else None,
                         ci95=garwood(v[1]) if v[0] else None) for p, v in sorted(per.items())}
        for c in cells.values(): c["ci95"] = [c["ci95"][0] / c["T"], c["ci95"][1] / c["T"]]
        win = [(p, v[0], v[1]) for p, v in sorted(per.items()) if p >= WINDOW_MIN_P]
        winnl = [(p, v[0], v[2]) for p, v in sorted(per.items()) if p >= WINDOW_MIN_P]
        out["units"][name] = dict(cells=cells, fit_all_success=classify(win), fit_nonline=classify(winnl))
    return out


def svg(res, path):
    W, H, ml, mr, mt, mb = 760, 520, 70, 20, 40, 60
    ps = [p for p in res["primes"]]
    xs = lambda p: ml + (math.log(p) - math.log(min(ps) * 0.8)) / (math.log(max(ps) * 1.25) - math.log(min(ps) * 0.8)) * (W - ml - mr)
    ymin, ymax = -6.0, 0.0
    ys = lambda r: mt + (ymax - math.log10(r)) / (ymax - ymin) * (H - mt - mb)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="sans-serif" font-size="12">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<text x="{W/2}" y="22" text-anchor="middle" font-size="14">Certified lift success per trial vs p (log-log), pooled over r=3..6 and lift family</text>']
    for e in range(int(ymin), 1):
        y = ys(10.0 ** e)
        o.append(f'<line x1="{ml}" x2="{W-mr}" y1="{y}" y2="{y}" stroke="#ddd"/><text x="{ml-6}" y="{y+4}" text-anchor="end">1e{e}</text>')
    for p in ps:
        x = xs(p)
        o.append(f'<line x1="{x}" x2="{x}" y1="{mt}" y2="{H-mb}" stroke="#eee"/><text x="{x}" y="{H-mb+16}" text-anchor="middle">{p}</text>')
    o.append(f'<text x="{(ml+W-mr)/2}" y="{H-12}" text-anchor="middle">prime p (log scale)</text>')
    o.append(f'<text transform="translate(16,{(mt+H-mb)/2}) rotate(-90)" text-anchor="middle">success rate per trial (log scale)</text>')
    cols = {"generic": "#1f77b4", "j0": "#d62728"}
    for i, fam in enumerate(("generic", "j0")):
        u = res["units"].get(f"pool/{fam}")
        if not u: continue
        pts = []
        for p, c in u["cells"].items():
            if c["succ"] > 0:
                x, y = xs(int(p)), ys(c["rate"])
                pts.append((x, y))
                o.append(f'<line x1="{x}" x2="{x}" y1="{ys(max(c["ci95"][0],1e-6))}" y2="{ys(min(c["ci95"][1],1))}" stroke="{cols[fam]}"/>')
                o.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{cols[fam]}"/>')
            else:
                hi = c["ci95"][1]
                x = xs(int(p))
                o.append(f'<path d="M{x-4},{ys(hi)+7} L{x},{ys(hi)} L{x+4},{ys(hi)+7}" stroke="{cols[fam]}" fill="none"/>')
        if len(pts) > 1:
            o.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{cols[fam]}" stroke-width="1" opacity="0.5"/>')
        win = [(int(p), c["T"], c["succ"]) for p, c in u["cells"].items() if int(p) >= res["window_min_p"]]
        C = fixed_c(win)
        if C:
            a, b = min(ps), max(ps)
            o.append(f'<line x1="{xs(a)}" y1="{ys(min(C/a,1))}" x2="{xs(b)}" y2="{ys(C/b)}" stroke="{cols[fam]}" stroke-dasharray="6 4"/>')
        f = u["fit_all_success"]
        b = f.get("beta")
        lab = f'{fam}: slope {b:.2f} [{f["lo"]:.2f},{f["hi"]:.2f}] (99.7%), C0_hat(beta=-1)={f["C0_hat"]:.1f}' if b is not None else f"{fam}: uninformative"
        o.append(f'<rect x="{ml+10}" y="{mt+8+16*i}" width="10" height="10" fill="{cols[fam]}"/><text x="{ml+26}" y="{mt+17+16*i}">{lab}</text>')
    o.append(f'<text x="{ml+10}" y="{mt+17+32}" fill="#444">dashed: C0/p with C0 fitted at slope -1 on p>={res["window_min_p"]}; arrows: 95% upper limit at zero successes</text>')
    o.append("</svg>")
    open(path, "w").write("\n".join(o) + "\n")


if __name__ == "__main__":
    d = sys.argv[1]
    res = main(d)
    json.dump(res, open(d + "/results.json", "w"), indent=1, sort_keys=True)
    svg(res, d + "/success_vs_p.svg")
    print(json.dumps({k: v for k, v in res.items() if k != "units"}))
    for name, u in res["units"].items():
        f = u["fit_all_success"]; g = u["fit_nonline"]
        print(name, f["cls"], f["succ"], None if f["beta"] is None else round(f["beta"], 2), "| nonline", g["cls"], g["succ"])
