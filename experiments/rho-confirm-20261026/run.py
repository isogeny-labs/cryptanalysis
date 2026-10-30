#!/usr/bin/env python3
"""One arm of the held-out confirmation: solve every (curve, target) with the library
named by $CRYPTANALYSIS_LIB and record group_ops.  Run once per library (main and candidate);
`analyze.py` pairs the rows.

Curves: y^2 = x^3 + a x + b, random a, b != 0 over a prime p of about bits+3 bits whose
largest prime factor r of #E has exactly `bits` bits and cofactor <= 16.  Sampling and targets
are seeded ("<seed>:<bits>", "<seed>:<p>:<a>:<b>:<target>"); solver seed = target + 1, one thread."""
import argparse, json, random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bindings" / "python"))
import cryptanalysis as ca  # noqa: E402


def sample_curve(rng, bits):
    while True:
        p = ca.next_prime(rng.getrandbits(bits + 3) | (1 << (bits + 2)))
        a, b = rng.randrange(1, p), rng.randrange(1, p)
        N = ca.Group.ec_count_points(p, a, b)
        r = max(q for q, _ in ca.factorize(N))
        if r.bit_length() == bits and N // r <= 16 and ca.is_prime(r):
            return p, a, b, N, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--sizes", default="20,24,28,32,36,40")
    ap.add_argument("--curves", type=int, default=40)
    ap.add_argument("--targets", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
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
                    x, st = G.rho(g, G.mul(g, k), ca.Options(seed=s + 1, threads=1))
                    fh.write(json.dumps({"label": a.label, "bits": bits, "curve": ci, "target": s, "p": p, "a": a_, "b": b_,
                                         "order": r, "ops": st.group_ops, "ok": x == k}) + "\n")
            print(f"{bits} bits done", flush=True)


main()
