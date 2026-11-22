#!/usr/bin/env python3
"""Toy rational 2-isogeny transfer audit; stdlib only. Unverified producer replay."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from math import ceil, isqrt, pi, sqrt
from pathlib import Path
from random import Random

P, A, B, R, SEED = 1009, 11, 13, 491, 20261118
SOURCE = (A, B)
TARGET = (-2 * A, A * A - 4 * B)
FIELDS = ("fadd", "fmul", "fsqr", "finv", "group_add", "group_double", "group_identity", "point_neg", "map_phi", "map_psi")

class Meter:
    def __init__(self):
        self.c = Counter()
    def add(self, x, y):
        self.c["fadd"] += 1
        return (x + y) % P
    def sub(self, x, y):
        self.c["fadd"] += 1
        return (x - y) % P
    def mul(self, x, y):
        self.c["fmul"] += 1
        return (x * y) % P
    def sq(self, x):
        self.c["fsqr"] += 1
        return (x * x) % P
    def inv(self, x):
        self.c["finv"] += 1
        return pow(x % P, -1, P)
    def neg(self, Q):
        self.c["point_neg"] += 1
        return None if Q is None else (Q[0], (-Q[1]) % P)
    def counts(self):
        return {k: self.c[k] for k in FIELDS}

def on_curve(Q, curve):
    if Q is None: return True
    x, y = Q
    a, b = curve
    return 0 <= x < P and 0 <= y < P and (y * y - x * x * x - a * x * x - b * x) % P == 0

def points(curve):
    a, b = curve
    ys = defaultdict(list)
    for y in range(P): ys[(y * y) % P].append(y)
    return [None] + [(x, y) for x in range(P) for y in ys[(x*x*x+a*x*x+b*x)%P]]

def add(X, Y, curve, m):
    if X is None or Y is None:
        m.c["group_identity"] += 1
        return Y if X is None else X
    x, y = X
    u, v = Y
    if x == u and (y + v) % P == 0:
        m.c["group_identity"] += 1
        return None
    a, b = curve
    if x == u:
        m.c["group_double"] += 1
        num = m.add(m.add(m.mul(3, m.sq(x)), m.mul(2*a, x)), b)
        den = m.mul(2, y)
    else:
        m.c["group_add"] += 1
        num, den = m.sub(v, y), m.sub(u, x)
    lam = m.mul(num, m.inv(den))
    rx = m.sub(m.sub(m.sub(m.sq(lam), a), x), u)
    ry = m.sub(m.mul(lam, m.sub(x, rx)), y)
    return rx, ry

def scalar(k, Q, curve, m):
    if k < 0: return scalar(-k, m.neg(Q), curve, m)
    out = None
    while k:
        if k & 1: out = add(out, Q, curve, m)
        k >>= 1
        if k: Q = add(Q, Q, curve, m)
    return out

def phi(Q, curve, m):
    m.c["map_phi"] += 1
    if Q is None or Q == (0, 0): return None
    x, y = Q
    a, b = curve
    xi = m.inv(x)
    rx = m.add(m.add(x, a), m.mul(b, xi))
    ry = m.mul(y, m.sub(m.mul(b, m.sq(xi)), 1))
    return rx, ry

def dual(Q, m, inv4, inv8):
    m.c["map_psi"] += 1
    z = phi(Q, TARGET, m)
    if z is None: return None
    return m.mul(z[0], inv4), m.mul(z[1], inv8)

def bsgs(g, q, curve, m):
    width = isqrt(R)
    if width * width < R: width += 1
    baby, s = {}, None
    for j in range(width):
        baby.setdefault(s, j)
        s = add(s, g, curve, m)
    step = scalar(-width, g, curve, m)
    s = q
    for i in range(width + 1):
        if s in baby: return (i * width + baby[s]) % R
        s = add(s, step, curve, m)
    return None

def audit():
    assert B % P and (A*A - 4*B) % P
    src, dst = points(SOURCE), points(TARGET)
    assert len(src) == len(dst) == 2 * R
    assert all(on_curve(z, SOURCE) for z in src)
    assert all(on_curve(z, TARGET) for z in dst)
    test = Meter()
    T = (0, 0)
    assert scalar(2, T, SOURCE, test) is None
    g = next(scalar(2, z, SOURCE, Meter()) for z in src[1:]
             if scalar(2, z, SOURCE, Meter()) is not None)
    assert scalar(R, g, SOURCE, Meter()) is None
    source_h = [scalar(k, g, SOURCE, Meter()) for k in range(R)]
    assert len(set(source_h)) == R
    mapped = {z: phi(z, SOURCE, Meter()) for z in src}
    assert all(z in set(dst) for z in mapped.values())
    fibers = Counter(mapped.values())
    assert len(fibers) == R and set(fibers.values()) == {2}
    assert mapped[None] is None and mapped[T] is None
    image_h = [mapped[z] for z in source_h]
    assert set(image_h) == set(fibers)
    assert len(set(image_h)) == R
    assert all(scalar(R, z, TARGET, Meter()) is None for z in image_h)
    inv4, inv8 = pow(4, -1, P), pow(8, -1, P)
    assert all(dual(mapped[z], Meter(), inv4, inv8) == scalar(2, z, SOURCE, Meter()) for z in src)
    assert all(dual(z, Meter(), inv4, inv8) in set(src) for z in dst)
    for z in source_h:
        inverse = scalar(pow(2, -1, R), dual(mapped[z], Meter(), inv4, inv8), SOURCE, Meter())
        assert inverse == z
    for z in source_h:
        for w in source_h:
            assert mapped[add(z, w, SOURCE, Meter())] == add(mapped[z], mapped[w], TARGET, Meter())
    samples = Random(SEED).sample(range(1, R), 64)
    rows = []
    for k in samples:
        q = scalar(k, g, SOURCE, Meter())
        direct_meter = Meter()
        found = bsgs(g, q, SOURCE, direct_meter)
        assert found == k
        assert scalar(found, g, SOURCE, direct_meter) == q
        transfer_meter = Meter()
        tg, tq = phi(g, SOURCE, transfer_meter), phi(q, SOURCE, transfer_meter)
        found2 = bsgs(tg, tq, TARGET, transfer_meter)
        assert found2 == k
        assert scalar(found2, g, SOURCE, transfer_meter) == q
        inverse_meter = Meter()
        inverse = scalar(pow(2, -1, R), dual(tq, inverse_meter, inv4, inv8), SOURCE, inverse_meter)
        assert inverse == q
        rows.append({"k": k, "source_log": found, "transferred_log": found2,
                     "source_ops": direct_meter.counts(), "transferred_ops": transfer_meter.counts(),
                     "optional_inverse_ops": inverse_meter.counts()})
    def totals(key):
        return {name: sum(row[key][name] for row in rows) for name in FIELDS}
    return {"protocol": "toy rational 2-isogeny; exploratory", "seed": SEED, "p": P,
            "source": {"a": A, "b": B, "order": len(src), "factorization": "2 * 491"},
            "target": {"a": TARGET[0], "b": TARGET[1], "order": len(dst), "factorization": "2 * 491"},
            "kernel": [None, [0, 0]], "kernel_size": 2, "image_size": len(fibers),
            "fibers_each": 2, "source_generator": list(g), "subgroup_order": R,
            "image_subgroup_order": len(set(image_h)), "inverse_2_mod_r": pow(2, -1, R),
            "map_checks": len(src), "dual_composition_checks": len(src),
            "homomorphism_checks": R * R, "inverse_subgroup_checks": R,
            "target_matches_source_order": len(src) == len(dst),
            "rho_reference_expected_steps": round(sqrt(pi * R / 2), 9),
            "measured_samples": len(rows), "correct_source_logs": len(rows),
            "correct_transferred_logs": len(rows), "rows": rows,
            "totals": {"direct": totals("source_ops"), "transferred": totals("transferred_ops"),
                       "inverse_optional": totals("optional_inverse_ops")},
            "verdict": "no measured ECDLP speedup; field arithmetic overhead from maps; no independently certified claim"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path)
    p.add_argument("--verify-json", type=Path)
    args = p.parse_args()
    payload = audit()
    payload["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.verify_json:
        original = json.loads(args.verify_json.read_text())
        if payload != original: raise SystemExit("FAIL: JSON replay mismatch")
        print("PASS: deterministic replay equals saved result")
    else:
        data = json.dumps(payload, sort_keys=True, indent=2) + "\n"
        if args.out: args.out.write_text(data)
        else: print(data)

if __name__ == "__main__": main()
