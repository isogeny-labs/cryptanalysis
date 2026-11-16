#!/usr/bin/env python3
"""CT146: independent finite-field test of 2-torsion correction transport.

This is not native q223 execution, not a genus-2 Jacobian norm proof and not
an ECDLP benchmark. All group operations are independently implemented here.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

MOD, NONSQUARE = 5, 2


def addf(a: int, b: int) -> int:
    return (a % MOD + b % MOD) % MOD + MOD * ((a // MOD + b // MOD) % MOD)


def negf(a: int) -> int:
    return (-(a % MOD) % MOD) + MOD * (-(a // MOD) % MOD)


def subf(a: int, b: int) -> int:
    return addf(a, negf(b))


def mulf(a: int, b: int) -> int:
    x, y, z, w = a % MOD, a // MOD, b % MOD, b // MOD
    return (x * z + NONSQUARE * y * w) % MOD + MOD * ((x * w + y * z) % MOD)


def powf(a: int, n: int) -> int:
    result = 1
    while n:
        if n & 1:
            result = mulf(result, a)
        a = mulf(a, a)
        n //= 2
    return result


def divf(a: int, b: int) -> int:
    if b == 0:
        raise ValueError('CT146: division by zero')
    return mulf(a, powf(b, 23))


def oncurve(p):
    return p is None or mulf(p[1], p[1]) == addf(mulf(mulf(p[0], p[0]), p[0]), 1)


def negate(p):
    return None if p is None else (p[0], negf(p[1]))


def plus(p, q):
    if p is None:
        return q
    if q is None:
        return p
    x, y = p
    a, b = q
    if x == a and y == negf(b):
        return None
    if x == a:
        if y == 0:
            return None
        slope = divf(mulf(3, mulf(x, x)), mulf(2, y))
    else:
        slope = divf(subf(b, y), subf(a, x))
    xx = subf(subf(mulf(slope, slope), x), a)
    yy = subf(mulf(slope, subf(x, xx)), y)
    return xx, yy


def multiple(p, n: int):
    if n < 0:
        return multiple(negate(p), -n)
    result = None
    while n:
        if n & 1:
            result = plus(result, p)
        p = plus(p, p)
        n >>= 1
    return result


def frob(p):
    return None if p is None else (powf(p[0], 5), powf(p[1], 5))


def rational(p):
    return p is None or (p[0] < 5 and p[1] < 5)


def require(cond, message):
    if not cond:
        raise ValueError('CT146 rejected: ' + message)


def pinned_source_check(original_file: Path, builder_file: Path):
    source = original_file.read_text(encoding='utf-8')
    blob = hashlib.sha1(b'blob ' + str(len(source.encode())).encode() + b'\0' + source.encode()).hexdigest()
    require(blob == '8016634385d76207b23a3eb3a4dae9b0366ac68d', 'original Rust Git blob changed')
    for needle in (
        'if curve::pmul(f, e, p, 2) != q {',
        'if !curve::on_curve(f, e, &p) || curve::pmul(f, e, &p, 2) != Pt::Inf {',
        'point: lift(p),',
        'let lifted = curve::padd(',
        'let class = self.target_phi(to, self.gamma(input.domain, to, lifted)?)?;',
        'let norm = descend_point(self.gamma(input.domain, to, lift(input.norm))?);',
        'if ep(n.norm(&entry.class)?) != entry.norm {',
    ):
        require(needle in source, 'missing frozen source condition: ' + needle)
    spec = importlib.util.spec_from_file_location('ct125_builder', builder_file)
    require(spec is not None and spec.loader is not None, 'CT125 generator cannot load')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    derived = builder.transform(source)
    require('let norm = self.norm_from_target_point(to, z)?;' in derived,
            'direct norm reuse route absent')
    require('let norm = self.norm_from_target_point(to, point)?;' in derived,
            'retained norm reuse route absent')
    require('if ep(n.norm(&entry.class)?) != entry.norm {' in derived,
            'independent actual Jacobian norm check removed')
    require('let norm = descend_point(self.gamma(from, to, lift(input.norm))?);' in derived,
            'diagnostic/reference norm path changed')
    return {'original_git_blob': blob, 'derivative_git_blob': builder.git_blob(derived)}


def run():
    points = [None] + [(x, y) for x in range(25) for y in range(25) if oncurve((x, y))]
    require(len(points) == 36, 'unexpected group cardinality')
    two = [t for t in points if multiple(t, 2) is None]
    require(len(two) == 4, 'full geometric E[2] expected')
    require(sum(rational(t) for t in two) == 2, 'toy rational E[2] subgroup qualification')
    for point in points:
        require(oncurve(point) and oncurve(frob(point)), 'curve/Frobenius closure')
    direct = chained = 0
    nonrational_double = 0
    for p in points:
        q = multiple(p, 2)
        for t in two:
            z = plus(p, t)
            require(multiple(z, 2) == q, '2-torsion correction no longer cancels')
            for m in (2, 3, 5, 7, 13):
                require(multiple(z, 2*m) == multiple(q, m), 'single homomorphism map')
                direct += 1
            for m, n in ((3, 5), (5, 7), (13, 13)):
                require(multiple(multiple(z, m), 2*n) == multiple(multiple(q, m), n),
                        'composed homomorphism maps')
                chained += 1
            if rational(q) and not rational(z) and plus(z, frob(z)) != multiple(z, 2):
                nonrational_double += 1
    witness = (9, 3)  # (4+u,3), in integer-encoded F25
    require(oncurve(witness) and multiple(witness, 2) == (0, 1), 'CT145 witness changed')
    require(plus(witness, frob(witness)) == (2, 2), 'CT145 trace changed')
    require(multiple(witness, 10) == multiple(multiple(witness, 2), 5),
            'reuse must work even for a Frobenius trace counterexample')
    non_two = next(p for p in points if multiple(p, 2) is not None)
    require(multiple(plus(witness, non_two), 2*5) != multiple(multiple(witness, 2), 5),
            'non-2-torsion correction should break equality')
    shifted = lambda p: plus(multiple(p, 5), non_two)
    require(multiple(shifted(witness), 2) != shifted(multiple(witness, 2)),
            'nonhomomorphic map should break equality')
    require(nonrational_double > 0, 'missing nonrational trace counterexample')
    return {
        'field': 'F5[u]/(u^2-2)', 'curve': 'y^2=x^3+1',
        'extension_points': len(points), 'two_torsion': len(two),
        'corrected_lifts': len(points)*len(two),
        'rational_two_torsion': sum(rational(t) for t in two),
        'direct_homomorphism_checks': direct, 'composed_homomorphism_checks': chained,
        'rational_double_nonrational_trace_witnesses': nonrational_double,
        'negative_controls': ['non_two_torsion_correction', 'nonhomomorphic_translation'],
        'scope': 'finite group-law canary plus exact source contract, no original q223 native parity',
        'standing': '[pcc:unverified]',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original-rust', type=Path)
    parser.add_argument('--ct125-builder', type=Path)
    args = parser.parse_args()
    require((args.original_rust is None) == (args.ct125_builder is None), 'source inputs must be paired')
    result = run()
    if args.original_rust is not None:
        result['source'] = pinned_source_check(args.original_rust, args.ct125_builder)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
