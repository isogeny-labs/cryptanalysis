#!/usr/bin/env python3
"""Build a Z[tau]-multiplier closure base header from B's K600 header, deterministically.

Column representatives: the first K' representatives R_0 .. R_{K'-1} of B's
K600 header (`base_n83_K600.jsonl`, base hash d4a4da26...). Multipliers: every
alpha = a + b tau with a odd, a > 0 and norm N(alpha) = a^2 + ab + 2b^2 <= cap
(tau^2 - tau + 2 = 0 on this a = 1 curve; lambda^2 - lambda + 2 = 0 mod r is
checked). One alpha per class up to sign and powers of tau: alpha and
+-tau^k alpha give the same signed Frobenius orbit, and alpha is divisible by
tau iff a is even, so a odd and a > 0 pick one per class. Norm <= 16 gives
M = 10 multipliers, norm <= 64 gives M = 38.

Orbit (c, alpha) is the signed Frobenius orbit of alpha(R_c) = [a]R_c +
[b]phi(R_c), computed in the pinned pure-Python oracle; its members are
+-phi^k(alpha(R_c)), k = 0..82, with labels (c, +-(a + b lambda) lambda^k
mod r), in the order of B's header (P, -P, phi P, -phi P, ...). alpha = 1
comes first in each column, so the column's first orbit is B's orbit c,
point for point and label for label (checked).

The header keeps B's format (`point_defined_factor_base`, decimal strings)
and adds `orbit_representatives` (one per orbit: the root index),
`orbit_labels` ([c, a, b] per orbit) and `closure` (the parameters).
`factor_base_representatives` holds the K' column representatives (the
logs). `base_hash` is a SHA-256 over the points and labels (domain
`n83-closure-base-v1`).

The generator stops on any repeated orbit key (min x over the 83
conjugates), across columns as well as within one. `verify_closure.py` is
the independent check.

Usage: make_closure_base.py --columns K' --norm cap --out path [--k600 header]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "snapshots" / "r770"
K600 = SNAPSHOT / "experiments/koblitz-single-target-n83-20261006/base_n83_K600.jsonl"
DOMAIN = b"n83-closure-base-v1"


def oracle():
    sys.path.insert(0, str(HERE))
    from verify_receipt import oracle as pinned  # noqa: E402  (the pinned harness's oracle.Curve)
    return pinned()


def multipliers(cap):
    """alpha = a + b tau, a odd > 0, N <= cap; (1, 0) first, then by (N, a, b)."""
    out = []
    bound = int(cap ** 0.5) + 2
    for a in range(1, 2 * bound + 2, 2):
        for b in range(-2 * bound, 2 * bound + 1):
            norm = a * a + a * b + 2 * b * b
            if norm <= cap:
                out.append((norm, a, b))
    out.sort()
    assert out[0] == (1, 1, 0)
    return [(a, b, norm) for norm, a, b in out]


def orbit_key(curve, x):
    key = x
    for _ in range(1, curve.n):
        x = curve.fm(x, x)
        key = min(key, x)
    return key


def image(curve, point, a, b):
    """[a]P + [b]phi(P) in the oracle."""
    pa = curve.mul(point, a)
    pb = curve.mul(curve.frob(point), abs(b)) if b else None
    if b < 0:
        pb = curve.neg(pb)
    return curve.add(pa, pb)


def base_hash(points, labels):
    digest = hashlib.sha256(DOMAIN)
    for (x, y), (column, coefficient) in zip(points, labels):
        digest.update(int(x).to_bytes(16, "little"))
        digest.update(int(y).to_bytes(16, "little"))
        digest.update(int(column).to_bytes(8, "little"))
        digest.update(int(coefficient).to_bytes(8, "little"))
    return digest.hexdigest()


def build(columns, cap, k600=K600, curve=None):
    curve = curve or oracle()
    source = json.loads(Path(k600).read_text().splitlines()[0])
    assert source["kind"] == "point_defined_factor_base" and source["n"] == curve.n == 83
    r, lam = curve.r, curve.lam
    assert (lam * lam - lam + 2) % r == 0, "tau^2 - tau + 2 = 0 must hold for lambda"
    assert columns <= len(source["factor_base_representatives"])
    mults = multipliers(cap)
    points, labels, orbit_reps, orbit_labels, seen = [], [], [], [], {}
    column_reps = source["factor_base_representatives"][:columns]
    for column, rep in enumerate(column_reps):
        base_point = curve.decode([int(rep[0]), int(rep[1])])
        for a, b, _ in mults:
            p = image(curve, base_point, a, b)
            if p is None:
                raise ValueError("alpha(R_%d) is the identity for alpha = %d + %d tau" % (column, a, b))
            key = orbit_key(curve, p[0])
            if key in seen:
                raise ValueError("orbit (%d, %d + %d tau) repeats orbit %s" % (column, a, b, seen[key]))
            seen[key] = (column, a, b)
            orbit_reps.append([str(p[0]), str(p[1])])
            orbit_labels.append([column, a, b])
            coefficient = (a + b * lam) % r
            x, y = p
            for _ in range(curve.n):
                points.append([str(x), str(y)])
                labels.append([column, coefficient])
                points.append([str(x), str(x ^ y)])
                labels.append([column, (r - coefficient) % r])
                x, y = curve.fm(x, x), curve.fm(y, y)
                coefficient = coefficient * lam % r
            if (x, y) != p or coefficient != (a + b * lam) % r:
                raise ValueError("Frobenius orbit does not close")
    # alpha = 1 orbits are B's orbits c, point for point and label for label.
    span = 2 * curve.n
    for column in range(columns):
        start = column * len(mults) * span
        if (points[start:start + span] != source["factor_base_point_coordinates"][column * span:(column + 1) * span]
                or labels[start:start + span] != source["factor_base_point_labels"][column * span:(column + 1) * span]):
            raise ValueError("column %d's alpha = 1 orbit differs from B's orbit" % column)
    header = {
        "kind": "point_defined_factor_base",
        "n": source["n"], "a": source["a"], "subgroup_order": source["subgroup_order"],
        "field_modulus_low_terms": source["field_modulus_low_terms"],
        "field_value_encoding": source["field_value_encoding"],
        "orbit_columns": columns,
        "factor_base_points": len(points),
        "base_hash": base_hash(points, labels),
        "factor_base_point_coordinates": points,
        "factor_base_point_labels": labels,
        "factor_base_representatives": column_reps,
        "orbit_representatives": orbit_reps,
        "orbit_labels": orbit_labels,
        "closure": {
            "construction": "orbit (c, alpha) = signed Frobenius orbit of alpha(R_c) = [a]R_c + [b]phi(R_c); "
                            "label of +-phi^k(alpha(R_c)) is (c, +-(a + b lambda) lambda^k mod r)",
            "column_representatives": "the first %d representatives of B's K600 header" % columns,
            "source_base_hash": source["base_hash"],
            "norm": "a^2 + ab + 2b^2 (tau^2 - tau + 2 = 0)",
            "norm_cap": cap,
            "multipliers": [[a, b, norm] for a, b, norm in mults],
            "orbits_per_column": len(mults),
            "columns": columns,
            "orbits": len(orbit_reps),
            "generator": "make_closure_base.py (pinned oracle.py arithmetic)",
        },
    }
    return header


def text(header):
    return json.dumps(header, sort_keys=True, separators=(",", ":")) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--columns", type=int, required=True)
    parser.add_argument("--norm", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--k600", type=Path, default=K600)
    args = parser.parse_args()
    body = text(build(args.columns, args.norm, args.k600))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(body)
    print(json.dumps({"out": str(args.out), "sha256": hashlib.sha256(body.encode()).hexdigest()}))


if __name__ == "__main__":
    main()
