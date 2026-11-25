#!/usr/bin/env python3
"""Where ca_rho_solve's group operations go on generic (aut order 2) curves.

Needs the library built with -DCA_RHO_TRACE and CA_RHO_TRACE_FILE set for the
traced pass; the same script run against an untraced build with --labels-only
gives the fingerprint to compare.  For each curve and target it runs the
negation-map rho (Options(seed=s+1, threads=1)) and appends one trace line per
solve.  Output: one JSON line per (curve, target) with group_ops, the recovered
logarithm and (traced pass) the trace fields.

Curves: y^2 = x^3 + a x + b with random a, b != 0 over a prime p of about
bits+3 bits, whose largest prime factor r of #E has exactly the requested bits
and cofactor <= 16.  Sampling and targets are seeded
("<seed>:<bits>", "<seed>:<p>:<a>:<b>:<target>")."""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bindings" / "python"))
import cryptanalysis as ca  # noqa: E402


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
    ap.add_argument("--sizes", default="24,28,32,36,40")
    ap.add_argument("--curves", type=int, default=30)
    ap.add_argument("--targets", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20261024)
    ap.add_argument("--labels-only", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    trace = None
    if not a.labels_only:
        trace = Path(os.environ["CA_RHO_TRACE_FILE"])
        trace.unlink(missing_ok=True)
    labels = []
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
                x1, st1 = G.rho(g, Q, ca.Options(seed=s + 1, threads=1))
                assert x1 == k
                labels.append({"r_bits": bits, "curve_index": ci, "target": s, "p": p, "a": a_, "b": b_,
                               "order": r, "x": x1, "rho_ops": st1.group_ops})
        print(f"{bits} bits done", flush=True)
    rows = [None] * len(labels)
    if trace is not None:
        rows = [json.loads(l) for l in trace.read_text().splitlines()]
        assert len(rows) == len(labels), (len(rows), len(labels))
    with open(a.out, "w") as fh:
        for lab, row in zip(labels, rows):
            if row is not None:
                assert row["total_ops"] == lab["rho_ops"]
                assert (row["table_ops"] + row["start_ops"] + sum(row["restart_ops"]) + row["step_ops"]
                        + row["escape_ops"]) == row["total_ops"]
                lab = {**lab, **row}
            fh.write(json.dumps(lab) + "\n")
    print(f"{len(labels)} solves" + ("" if trace is None else "; every trace sums to its group_ops"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
