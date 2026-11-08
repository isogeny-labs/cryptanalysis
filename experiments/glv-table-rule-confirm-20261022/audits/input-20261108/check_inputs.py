#!/usr/bin/env python3
"""Independent metadata/target checks for the archived GLV confirmation rows.

This does not verify the original solver returns: the archive records only a
producer-reported equality flag, not the returned scalar or target point.
"""
import gzip
import hashlib
import json
import math
import os
import random
from pathlib import Path

ROOT = Path(os.environ.get('GLV_CONFIRM_ARCHIVE_ROOT', Path(__file__).resolve().parents[2]))
OUT = Path(__file__).resolve().parent / 'receipt.json'
MR_BASES = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)


def prime(n):
    if n < 2:
        return False
    for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % q == 0:
            return n == q
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in MR_BASES:
        a %= n
        if a == 0:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def sqrt_mod(v, p):
    v %= p
    if v == 0:
        return 0
    if pow(v, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        return pow(v, (p + 1) // 4, p)
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    c, x, t, m = pow(z, q, p), pow(v, (q + 1) // 2, p), pow(v, q, p), s
    while t != 1:
        i, u = 1, t * t % p
        while u != 1:
            u = u * u % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        x, t, c, m = x * b % p, t * b * b % p, b * b % p, i
    return x


def add(P, Q, p, a):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if P == Q:
        slope = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        slope = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (slope * slope - x1 - x2) % p
    return x3, (slope * (x1 - x3) - y1) % p


def mul(P, n, p, a):
    out = None
    while n:
        if n & 1:
            out = add(out, P, p, a)
        P = add(P, P, p, a)
        n >>= 1
    return out


def main():
    curves = {}
    counts = {}
    rows = 0
    for arm in ('main', 'c12'):
        count = 0
        with gzip.open(ROOT / ('rows_' + arm + '.jsonl.gz'), 'rt') as fh:
            for line in fh:
                x = json.loads(line)
                fam, bits, ci, ti = (x[k] for k in ('family', 'bits', 'curve', 'target'))
                assert x['arm'] == arm and 0 <= ci < 200 and 0 <= ti < 25
                assert x['k'] == random.Random('20261023:%s:%s:%s:%s' %
                                               (x['p'], x['a'], x['b'], ti)).randrange(1, x['r'])
                key = (fam, bits, ci)
                data = tuple(x[k] for k in ('p', 'a', 'b', 'N', 'r'))
                if key in curves:
                    assert curves[key] == data
                else:
                    curves[key] = data
                count += 1
        counts[arm] = count
        rows += count
    assert counts == {'main': 80000, 'c12': 80000}
    assert len(curves) == 3200
    checked = []
    for (fam, bits, ci), (p, a, b, N, r) in sorted(curves.items()):
        assert r.bit_length() == bits and N % r == 0 and 1 <= N // r <= 16
        assert abs(N - (p + 1)) <= 2 * math.isqrt(p) + 1
        assert (fam == 'j0' and a == 0 and p % 3 == 1) or \
               (fam == 'j1728' and b == 0 and p % 4 == 1)
        assert (4 * a ** 3 + 27 * b ** 2) % p != 0
        assert prime(p) and prime(r)
        if ci not in (0, 199):
            continue
        assert N < 2 ** 64 and r < 2 ** 64
        seed = hashlib.sha256(('%s:%s:%s' % (fam, bits, ci)).encode()).digest()
        x0 = int.from_bytes(seed[:8], 'big') % p
        found = False
        for step in range(256):
            x = (x0 + step) % p
            y = sqrt_mod((x * x * x + a * x + b) % p, p)
            if y is None:
                continue
            P = (x, y)
            if mul(P, N, p, a) is not None:
                raise AssertionError('recorded group order does not annihilate sampled point')
            G = mul(P, N // r, p, a)
            if G is None:
                continue
            assert mul(G, r, p, a) is None
            k = random.Random('20261023:%s:%s:%s:%s' % (p, a, b, 0)).randrange(1, r)
            Q = mul(G, k, p, a)
            assert Q is not None and mul(Q, r, p, a) is None
            checked.append({'family': fam, 'bits': bits, 'curve': ci,
                            'point_x': x, 'point_y': y, 'subgroup_x': G[0],
                            'subgroup_y': G[1], 'target_x': Q[0], 'target_y': Q[1]})
            found = True
            break
        assert found
    out = {'schema': 'glv-confirm-independent-input-audit/v1',
           'input_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                            for name in ('rows_main.jsonl.gz', 'rows_c12.jsonl.gz')},
           'rows_checked': rows, 'curves_metadata_checked': len(curves),
           'sampled_curves_checked': len(checked), 'sampled_curves': checked,
           'scope': 'metadata, seed-derived k, and sampled subgroup point arithmetic; no solver return in raw rows'}
    path = OUT
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: out[k] for k in ('rows_checked', 'curves_metadata_checked', 'sampled_curves_checked', 'scope')}))
    print('receipt_sha256', hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
