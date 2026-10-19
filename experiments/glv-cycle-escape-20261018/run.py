#!/usr/bin/env python3
"""Paired rho vs curve_solve (GLV-folded rho) on j=1728, j=0 and random
curves, through libcryptanalysis. Emits one JSON line per (curve, target,
arm). See PROTOCOL.md; this script is the instrument it freezes."""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from csd.bulk.paths import cryptanalysis_root, git_commit, load_cryptanalysis  # noqa: E402

FAMILIES = ("j1728", "j0", "random")


def sample_curve(ca, rng: random.Random, family: str, r_bits: int):
    """A curve of the family whose largest prime factor r of #E has exactly
    r_bits bits and a cofactor of at most 16 (j=1728 curves always have the
    2-torsion point (0, 0), so cofactor 1 is impossible there)."""
    while True:
        p = ca.next_prime(rng.getrandbits(r_bits + 3) | (1 << (r_bits + 2)))
        if family == "j0":
            if p % 3 != 1:
                continue
            a, b = 0, rng.randrange(1, p)
        elif family == "j1728":
            if p % 4 != 1:
                continue
            a, b = rng.randrange(1, p), 0
        else:
            a, b = rng.randrange(p), rng.randrange(p)
            if (4 * a ** 3 + 27 * b ** 2) % p == 0 or a == 0 or b == 0:
                continue
        N = ca.Group.ec_count_points(p, a, b)
        r = max(q for q, _ in ca.factorize(N))
        if r.bit_length() == r_bits and N // r <= 16 and ca.is_prime(r):
            return p, a, b, N, r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="24,28,32")
    ap.add_argument("--curves", type=int, default=30, help="curves per family and size")
    ap.add_argument("--targets", type=int, default=100, help="targets per curve")
    ap.add_argument("--seed", type=int, default=20261017)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    ca, err = load_cryptanalysis()
    assert ca is not None, err
    out = open(a.out, "w")
    meta = {"kind": "meta", "seed": a.seed, "sizes": a.sizes, "curves": a.curves, "targets": a.targets,
            "cryptanalysis_commit": git_commit(cryptanalysis_root()), "rho_options": "Options(seed=s+1, threads=1), negation map on (default)",
            "curve_solve": "Group.curve_solve(gen, Q, s+1)"}
    out.write(json.dumps(meta) + "\n")
    t0 = time.time()
    for bits in map(int, a.sizes.split(",")):
        for family in FAMILIES:
            rng = random.Random(f"{a.seed}:{family}:{bits}")
            for ci in range(a.curves):
                p, a_, b_, N, r = sample_curve(ca, rng, family, bits)
                G = ca.Group.ec(p, a_, b_, N)
                G.set_order(r, N // r)
                det = ca.curve_detect(p, a_, b_, r)
                gen = G.find_generator(1)
                curve = {"family": family, "r_bits": bits, "p": p, "a": a_, "b": b_, "N": N, "r": r, "endo": int(det.endo), "aut_order": det.aut_order,
                         "lambda_found": det.lambda_ != 0}
                for s in range(a.targets):
                    k = random.Random(f"{a.seed}:{p}:{a_}:{b_}:{s}").randrange(1, r)
                    Q = G.mul(gen, k)
                    x1, st1 = G.rho(gen, Q, ca.Options(seed=s + 1, threads=1))
                    x2, info, st2 = G.curve_solve(gen, Q, s + 1)
                    for arm, x, st in (("rho", x1, st1), ("curve_solve", x2, st2)):
                        out.write(json.dumps({"kind": "run", **curve, "curve_index": ci, "target": s, "arm": arm, "correct": x == k,
                                              "group_ops": st.group_ops, "S": st.group_ops / math.sqrt(r), "seconds": st.seconds}) + "\n")
                out.flush()
            print(f"{bits} bits {family}: {a.curves} curves done, {time.time() - t0:.0f}s", flush=True)
    out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
