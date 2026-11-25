#!/usr/bin/env python3
"""Paired arm measurement for ca_rho_solve (selection round).

Needs the library built with -DCA_RHO_MEASURE_ARMS (arms read from the
environment once per solve) for the full arm list, or the plain main build with
--arms main.  Every arm solves the same targets with the same solver seed.
Output: one JSON line per (size, curve, target, arm) with group_ops and
whether the recovered logarithm was right.

Curves: y^2 = x^3 + a x + b, random a, b != 0 over a prime p of about bits+3
bits whose largest prime factor r of #E has exactly `bits` bits and cofactor
<= 16. Sampling and targets are seeded ("<seed>:<bits>", "<seed>:<p>:<a>:<b>:<target>")."""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bindings" / "python"))
import cryptanalysis as ca  # noqa: E402

ENV_KEYS = ["CA_RHO_TABLE_DIV", "CA_RHO_DP_DIV", "CA_RHO_FAST_CYCLE", "CA_RHO_FIXED_BASE", "CA_RHO_R_SQRT"]
_FBD = {"CA_RHO_FAST_CYCLE": "1", "CA_RHO_FIXED_BASE": "1", "CA_RHO_DP_DIV": "128"}
ARMS = {
    "base": {},
    "control": {"CA_RHO_TABLE_DIV": "48", "CA_RHO_DP_DIV": "32", "CA_RHO_FAST_CYCLE": "0", "CA_RHO_FIXED_BASE": "0",
                "CA_RHO_R_SQRT": "0"},
    "T12": {"CA_RHO_TABLE_DIV": "12"},
    "R1.0": {"CA_RHO_R_SQRT": "100"},
    "F": {"CA_RHO_FAST_CYCLE": "1"},
    "B": {"CA_RHO_FIXED_BASE": "1"},
    "D128": {"CA_RHO_DP_DIV": "128"},
    "F+B+D128": dict(_FBD),
    "F+B+D128+T12": {**_FBD, "CA_RHO_TABLE_DIV": "12"},
    "F+B+D128+R0.7": {**_FBD, "CA_RHO_R_SQRT": "70"},
    "F+B+D128+R1.0": {**_FBD, "CA_RHO_R_SQRT": "100"},
    "F+B+D128+R1.5": {**_FBD, "CA_RHO_R_SQRT": "150"},
}


def sample_curve(rng: random.Random, bits: int):
    while True:
        p = ca.next_prime(rng.getrandbits(bits + 3) | (1 << (bits + 2)))
        a, b = rng.randrange(1, p), rng.randrange(1, p)
        N = ca.Group.ec_count_points(p, a, b)
        r = max(q for q, _ in ca.factorize(N))
        if r.bit_length() == bits and N // r <= 16 and ca.is_prime(r):
            return p, a, b, N, r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="20,24,28,32,36,40")
    ap.add_argument("--curves", type=int, default=40)
    ap.add_argument("--targets", type=int, default=30)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arms", default=",".join(ARMS), help="comma list, or 'main' for the unflagged build")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    names = ["main"] if a.arms == "main" else a.arms.split(",")
    with open(a.out, "w") as fh:
        for bits in map(int, a.sizes.split(",")):
            rng = random.Random(f"{a.seed}:{bits}")
            for ci in range(a.curves):
                p, a_, b_, N, r = sample_curve(rng, bits)
                G = ca.Group.ec(p, a_, b_, N)
                G.set_order(r, N // r)
                g = G.find_generator(1)
                for s in range(a.targets):
                    k = random.Random(f"{a.seed}:{p}:{a_}:{b_}:{s}").randrange(1, r)
                    Q = G.mul(g, k)
                    for name in names:
                        for key in ENV_KEYS:
                            os.environ.pop(key, None)
                        os.environ.update(ARMS.get(name, {}))
                        x, st = G.rho(g, Q, ca.Options(seed=s + 1, threads=1))
                        fh.write(json.dumps({"bits": bits, "curve": ci, "target": s, "arm": name, "p": p, "a": a_, "b": b_,
                                             "order": r, "ops": st.group_ops, "ok": x == k}) + "\n")
                fh.flush()
            print(f"{bits} bits done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
