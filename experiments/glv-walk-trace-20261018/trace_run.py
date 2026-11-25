#!/usr/bin/env python3
"""Where glv_rho_solve's group operations go, on j = 1728 and j = 0 curves.

Needs the library built with -DCA_GLV_TRACE (CRYPTANALYSIS_LIB pointing at
it). For each curve and target it runs the negation-map rho and curve_solve
on the same target and seed; every curve_solve appends one trace line to
CA_GLV_TRACE_FILE. Output: one JSON line per (curve, target) with both
solvers' group_ops and the curve_solve trace fields.

Curves: largest prime factor r of #E with exactly the requested bits and
cofactor <= 16; j = 1728 is y^2 = x^3 + a x (p = 1 mod 4), j = 0 is
y^2 = x^3 + b (p = 1 mod 3). Sampling and targets are seeded
("<seed>:<family>:<bits>", "<seed>:<p>:<a>:<b>:<target>")."""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bindings" / "python"))
import cryptanalysis as ca  # noqa: E402


def sample_curve(rng: random.Random, family: str, bits: int):
    while True:
        p = ca.next_prime(rng.getrandbits(bits + 3) | (1 << (bits + 2)))
        if family == "j0":
            if p % 3 != 1:
                continue
            a, b = 0, rng.randrange(1, p)
        else:
            if p % 4 != 1:
                continue
            a, b = rng.randrange(1, p), 0
        N = ca.Group.ec_count_points(p, a, b)
        r = max(q for q, _ in ca.factorize(N))
        if r.bit_length() == bits and N // r <= 16 and ca.is_prime(r):
            return p, a, b, N, r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", default="j1728,j0")
    ap.add_argument("--sizes", default="24,28,32")
    ap.add_argument("--curves", type=int, default=20)
    ap.add_argument("--targets", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261017)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    trace = Path(os.environ["CA_GLV_TRACE_FILE"])
    trace.unlink(missing_ok=True)
    labels = []
    for bits in map(int, a.sizes.split(",")):
        for fam in a.families.split(","):
            rng = random.Random(f"{a.seed}:{fam}:{bits}")
            for ci in range(a.curves):
                p, a_, b_, N, r = sample_curve(rng, fam, bits)
                G = ca.Group.ec(p, a_, b_, N)
                G.set_order(r, N // r)
                g = G.find_generator(1)
                for s in range(a.targets):
                    k = random.Random(f"{a.seed}:{p}:{a_}:{b_}:{s}").randrange(1, r)
                    Q = G.mul(g, k)
                    x1, st1 = G.rho(g, Q, ca.Options(seed=s + 1, threads=1))
                    x2, _, st2 = G.curve_solve(g, Q, s + 1)
                    assert x1 == k and x2 == k
                    labels.append({"family": fam, "r_bits": bits, "curve_index": ci, "target": s, "p": p, "a": a_, "b": b_, "r": r,
                                   "rho_ops": st1.group_ops, "curve_solve_ops": st2.group_ops})
            print(f"{bits} bits {fam} done", flush=True)
    rows = [json.loads(l) for l in trace.read_text().splitlines()]
    assert len(rows) == len(labels), (len(rows), len(labels))
    with open(a.out, "w") as fh:
        for lab, row in zip(labels, rows):
            assert row["total_ops"] == lab["curve_solve_ops"]
            assert row["table_ops"] + row["start_ops"] + row["restart_ops"] + row["step_ops"] == row["total_ops"]
            fh.write(json.dumps({**lab, **row}) + "\n")
    print(f"{len(rows)} traced solves; every trace sums to its group_ops")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
