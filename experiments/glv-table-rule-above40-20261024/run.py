#!/usr/bin/env python3
"""One arm of the above-40-bit GLV table-rule experiment (PROTOCOL.md).

    CRYPTANALYSIS_LIB=b-<arm>/libcryptanalysis.so python3 run.py --arm <arm> --out rows_<arm>.jsonl [--rho]

Every arm samples the same curves and targets (seeded); only the library build
differs. One JSON line per (family, bits, curve, target): curve_solve group_ops
and correctness, plus the negation-map rho reference with --rho."""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bindings" / "python"))
import cryptanalysis as ca  # noqa: E402


def sample_curve(rng: random.Random, family: str, bits: int):
    """Largest prime factor r of #E with exactly `bits` bits and cofactor <= 16;
    j = 1728: y^2 = x^3 + a x (p = 1 mod 4); j = 0: y^2 = x^3 + b (p = 1 mod 3)."""
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
    ap.add_argument("--arm", required=True)
    ap.add_argument("--families", default="j1728,j0")
    ap.add_argument("--sizes", default="40:800,42:650,44:450,46:300,48:170,50:85",
                    help="comma list of bits:curves (one target per curve), the frozen grid by default")
    ap.add_argument("--targets", type=int, default=1)
    ap.add_argument("--seed", type=int, default=20261031)
    ap.add_argument("--rho", action="store_true", help="also run the negation-map rho reference")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    t0 = time.time()
    with open(a.out, "w") as fh:
        for spec in a.sizes.split(","):
            bits, ncurves = map(int, spec.split(":"))
            for fam in a.families.split(","):
                rng = random.Random(f"{a.seed}:{fam}:{bits}")
                for ci in range(ncurves):
                    p, a_, b_, N, r = sample_curve(rng, fam, bits)
                    G = ca.Group.ec(p, a_, b_, N)
                    G.set_order(r, N // r)
                    g = G.find_generator(1)
                    for s in range(a.targets):
                        k = random.Random(f"{a.seed}:{p}:{a_}:{b_}:{s}").randrange(1, r)
                        Q = G.mul(g, k)
                        row = {"arm": a.arm, "family": fam, "bits": bits, "curve": ci, "target": s,
                               "p": p, "a": a_, "b": b_, "N": N, "r": r, "k": k}
                        x, _, st = G.curve_solve(g, Q, s + 1)
                        row.update(ops=st.group_ops, correct=x == k)
                        if a.rho:
                            x1, st1 = G.rho(g, Q, ca.Options(seed=s + 1, threads=1))
                            row.update(rho_ops=st1.group_ops, rho_correct=x1 == k)
                        fh.write(json.dumps(row) + "\n")
                        fh.flush()
                print(f"[{time.time() - t0:7.0f}s] {a.arm} {bits} bits {fam} done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
