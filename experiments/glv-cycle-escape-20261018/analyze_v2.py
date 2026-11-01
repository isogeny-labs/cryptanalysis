#!/usr/bin/env python3
"""Protocol v2 decision rule: per curve, log(mean S of a variant's
curve_solve / mean S of the legacy curve_solve) over the same targets;
family mean with a two-stage bootstrap; Bonferroni over 2 variants x 2 GLV
families (98.75% intervals). Also checks the invariants the protocol states:
rho identical across the three runs, random curves identical across variants,
every answer correct. Descriptive: ratios against rho and theory."""
from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent  # run from this directory with the three rows files beside it
THEORY = {"j1728": math.sqrt(2 / 4), "j0": math.sqrt(2 / 6), "random": 1.0}
VARIANTS = ("legacy", "patched", "escape")
LABEL = {"legacy": "legacy walk", "patched": "look-ahead fix", "escape": "look-ahead fix + cycle escape"}
SIZES = (24, 28, 32)
CURVES = 40
TARGETS = 200


def load(path: Path):
    op = gzip.open if path.suffix == ".gz" else open
    runs = defaultdict(dict)
    wrong = 0
    with op(path, "rt") as stream:
        for line in stream:
            r = json.loads(line)
            if r["kind"] != "run":
                continue
            wrong += r["correct"] is not True
            key = (r["family"], r["r_bits"], r["curve_index"], r["target"], r["arm"])
            if key in runs:
                raise ValueError(f"{path}: duplicate solve {key}")
            if r["r"] <= 0 or r["group_ops"] <= 0:
                raise ValueError(f"{path}: nonpositive order or operation count for {key}")
            cost = r["group_ops"] / math.sqrt(r["r"])
            if not math.isfinite(cost):
                raise ValueError(f"{path}: nonfinite cost for {key}")
            runs[key] = cost
    return runs, wrong


def boot_ratio(pairs, rng, B):
    lr = np.array([math.log(a.mean() / b.mean()) for a, b in pairs])
    boot = np.empty(B)
    for i in range(B):
        idx = rng.integers(0, len(pairs), len(pairs))
        v = []
        for j in idx:
            a, b = pairs[j]
            t = rng.integers(0, len(a), len(a))
            v.append(math.log(a[t].mean() / b[t].mean()))
        boot[i] = np.mean(v)
    return lr.mean(), boot


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--json-out", default=str(HERE / "results_v2.json"))
    a = ap.parse_args(argv)
    if a.boot <= 0:
        ap.error("--boot must be positive")
    data = {}
    problems = []
    expected = {(family, bits, curve, target, arm)
                for family in THEORY for bits in SIZES
                for curve in range(CURVES) for target in range(TARGETS)
                for arm in ("rho", "curve_solve")}
    for v in VARIANTS:
        p = HERE / f"rows_v2_{v}.jsonl.gz"
        p = p if p.exists() else HERE / f"rows_v2_{v}.jsonl"
        data[v], wrong = load(p)
        print(f"{v}: {len(data[v])} solves, {wrong} wrong answers")
        if wrong:
            problems.append(f"{v}: {wrong} incorrect answers or solver failures")
        missing = expected - data[v].keys()
        extra = data[v].keys() - expected
        if missing or extra:
            problems.append(f"{v}: protocol grid differs ({len(missing)} missing, {len(extra)} unexpected solves)")
    if problems:
        raise ValueError("invalid comparison: " + "; ".join(problems))
    keys = sorted({k[:4] for k in data["legacy"]})
    rho_mismatch = sum(data[v][k + ("rho",)] != data["legacy"][k + ("rho",)] for v in VARIANTS for k in keys)
    rand_mismatch = sum(data[v][k + ("curve_solve",)] != data["legacy"][k + ("curve_solve",)] for v in VARIANTS for k in keys if k[0] == "random")
    print(f"invariants: rho differs across runs on {rho_mismatch} solves; random-curve curve_solve differs on {rand_mismatch} solves (both must be 0)")
    if rho_mismatch or rand_mismatch:
        raise ValueError(f"invalid comparison: {rho_mismatch} rho control mismatches; {rand_mismatch} random-curve control mismatches")
    level = 0.05 / 4
    rng = np.random.default_rng(20261017)
    out = {"ci_level": 1 - level, "rho_mismatch": rho_mismatch, "random_mismatch": rand_mismatch, "primary": [], "vs_rho": []}

    def pairs_for(fam, bits, num, den):
        cur = defaultdict(lambda: ([], []))
        for k in keys:
            if k[0] == fam and (bits is None or k[1] == bits):
                c = cur[k[1:3]]
                c[0].append(data[num[0]][k + (num[1],)])
                c[1].append(data[den[0]][k + (den[1],)])
        return [(np.array(x), np.array(y)) for x, y in cur.values()]

    print(f"\nPrimary (verdicts): variant curve_solve / legacy curve_solve, {100 * (1 - level):.2f}% CI")
    print("| variant | family | curves | ratio | CI | verdict |\n|---|---|---|---|---|---|")
    for v in ("patched", "escape"):
        for fam in ("j1728", "j0"):
            pr = pairs_for(fam, None, (v, "curve_solve"), ("legacy", "curve_solve"))
            m, boot = boot_ratio(pr, rng, a.boot)
            lo, hi = np.quantile(boot, [level / 2, 1 - level / 2])
            verdict = "fewer operations than legacy" if hi < 0 else ("more operations than legacy" if lo > 0 else "no measured difference")
            row = {"variant": v, "family": fam, "curves": len(pr), "ratio": math.exp(m), "ci": [math.exp(lo), math.exp(hi)], "verdict": verdict}
            out["primary"].append(row)
            print(f"| {LABEL[v]} | {fam} | {len(pr)} | {row['ratio']:.3f} | [{row['ci'][0]:.3f}, {row['ci'][1]:.3f}] | {verdict} |")
    print("\nDescriptive: curve_solve / rho per variant (theory in brackets); per size and pooled")
    print("| variant | family | r bits | ratio vs rho | CI | theory |\n|---|---|---|---|---|---|")
    for v in VARIANTS:
        for fam in ("j1728", "j0", "random"):
            for bits in (24, 28, 32, None):
                pr = pairs_for(fam, bits, (v, "curve_solve"), (v, "rho"))
                m, boot = boot_ratio(pr, rng, 2000)
                lo, hi = np.quantile(boot, [level / 2, 1 - level / 2])
                row = {"variant": v, "family": fam, "r_bits": bits or "all", "ratio": math.exp(m), "ci": [math.exp(lo), math.exp(hi)], "theory": THEORY[fam]}
                out["vs_rho"].append(row)
                print(f"| {LABEL[v]} | {fam} | {row['r_bits']} | {row['ratio']:.3f} | [{row['ci'][0]:.3f}, {row['ci'][1]:.3f}] | {THEORY[fam]:.3f} |")
    Path(a.json_out).write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
