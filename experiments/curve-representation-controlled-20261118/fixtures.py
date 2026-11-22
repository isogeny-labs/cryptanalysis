"""Frozen-rule fixture generation. Called only after experiment admission."""
from math import isqrt
import random
import importlib.util
from pathlib import Path
from core import Curve, prime, digest

PRIMES = [101, 229, 461, 929, 1861, 3733]
SEEDS = [2026111801, 2026111802]


def source(p):
    squares = {y*y % p for y in range(p)}
    for A in range(3, min(p-2, 1000)):
        if (A*A-4) % p == 0 or (-A-2) % p not in squares:
            continue
        d = -(A-2)*pow(A+2, -1, p) % p
        if d in squares:
            continue
        C = Curve(p, A, 1)
        points = C.points()
        n = len(points)
        if n % 8 or n//8 < 11 or not prime(n//8):
            continue
        r = n//8
        for P in points[1:]:
            G = C.mul(8, P)
            if G is not None and C.mul(r, G) is None:
                return C, r, G
    raise ValueError(f'no source within frozen coefficient bound for p={p}')


def control(p, required_order=None):
    for b in range(1, p):
        if (4*(-3)**3+27*b*b) % p == 0:
            continue
        C = Curve(p, 0, -3, b)
        points = C.points()
        n = len(points)
        if n == p or not prime(n):
            continue
        if required_order is None or required_order == n:
            return C, n, points[1]
    return None


def same_order(r):
    # A fixed finite search, not a post-result choice of a favourable control.
    bound = 2*isqrt(r)+5
    for q in range(max(5, r-bound), r+bound+1):
        if q == r or not prime(q):
            continue
        result = control(q, r)
        if result:
            return result
    return None


def base_points(C, r, k):
    out = []
    for P in C.points()[1:]:
        if P < C.neg(P) and C.mul(r, P) is None:
            out.append(P)
            if len(out) == k:
                return out
    raise ValueError('insufficient eligible sign classes')


def identity(C, r, G, cofactor, tag):
    helper = Path(__file__).resolve().parents[2]/'tools/curve_identity.py'
    spec = importlib.util.spec_from_file_location('lab_curve_identity', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    field = {'characteristic': C.p, 'degree': 1,
             'representation': 'prime_field', 'modulus': C.p,
             'element_encoding': 'least_nonnegative_integer'}
    record = {'model': 'generalized_weierstrass',
              'coefficients': [0, C.a2 % C.p, 0, C.a4 % C.p, C.a6 % C.p],
              'order': cofactor*r, 'subgroup_order': r, 'cofactor': cofactor,
              'generator': list(G), 'target_group': 'subgroup_generated_by_generator'}
    return dict(module.curve_identity(field, record, tag), field=field, curve=record)


def make():
    instances = []
    missing = []
    for p in PRIMES:
        C, r, G = source(p)
        choices = [('torsion', (C, r, G)),
                   ('same_field_control', control(p)),
                   ('same_order_control', same_order(r))]
        for kind, value in choices:
            if value is None:
                missing.append({'source_field': p, 'kind': kind,
                                'status': 'no_fixture_in_frozen_search'})
                continue
            D, n, H = value
            k = 1
            while k**3 < n:
                k += 1
            k = min(5, k, (n-1)//2)
            B = base_points(D, n, k)
            data = D.data(n, H)
            data.update({'source_field': p, 'kind': kind,
                         'cofactor': 8 if kind == 'torsion' else 1,
                         'curve_order': 8*n if kind == 'torsion' else n,
                         'base': [list(P) for P in B], 'sign_classes': k,
                         'actual_signed_points': 2*k})
            data['identity'] = identity(D, n, H, data['cofactor'],
                                        'mont' if kind == 'torsion' else 'swcontrol')
            if kind == 'torsion':
                u, v = H
                target = Curve(D.p, -2*D.a2, D.a2*D.a2-4)
                mapped = ((u+D.a2+pow(u, -1, D.p)) % D.p,
                          v*(1-pow(u*u, -1, D.p)) % D.p)
                data['isogeny_target_identity'] = identity(target, n, mapped, 8, 'iso2')
                data['isogeny_map'] = {'degree': 2, 'kernel': ['infinity', [0, 0]],
                    'x': 'u+A+1/u', 'y': 'v*(1-1/u^2)',
                    'source_curve_uid': data['identity']['curve_uid'],
                    'target_curve_uid': data['isogeny_target_identity']['curve_uid'],
                    'standing': 'unverified'}
            data['fixture_id'] = digest(data)
            instances.append(data)
    return {'instances': instances, 'missing': missing}


def workload(instance, seed):
    C = Curve(*(instance[k] for k in ['p', 'a2', 'a4', 'a6']))
    r = instance['r']
    G = tuple(instance['G'])
    rng = random.Random(seed + int(instance['fixture_id'][:12], 16))
    secret = rng.randrange(1, r)
    Q = C.mul(secret, G)
    stream = []
    for _ in range(24):
        draws = []
        while True:
            a, b = rng.randrange(r), rng.randrange(r)
            draws.append([a, b])
            if C.add(C.mul(a, G), C.mul(b, Q)) is not None:
                break
        stream.append({'draws': draws, 'a': a, 'b': b})
    return {'seed': seed, 'target': list(Q), 'fixture_scalar': secret,
            'queries': stream, 'input_law': 'uniform_nonidentity_group_query_conditioned_by_rejection'}
