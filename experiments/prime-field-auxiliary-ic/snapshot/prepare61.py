"""Prepare a 61-bit-field, mixed-order test for projected index calculus."""
import json
from pathlib import Path
from sympy import isprime
from prepare import Curve, chain

ROOT = Path(__file__).resolve().parent / 'run61'


def main():
    ROOT.mkdir(exist_ok=True)
    p = 2**61-1
    curve_order = 2305843006203085756
    r = 157632877033
    h = curve_order//r
    E = Curve(p, a6=3)
    W = (1, 2)
    d = 104811045736503898
    factors = [2, 11, 30223, r]
    assert isprime(p) and all(isprime(ell) for ell in factors)
    assert d == 2*11*30223*r and E.mul(d, W) is None
    assert all(E.mul(d//ell, W) is not None for ell in factors)
    # d divides #E; there is exactly one multiple of d in Hasse's interval.
    assert (curve_order-(p+1))**2 <= 4*p and d*d > 16*p
    assert curve_order % d == 0
    assert curve_order == 4*11**2*30223*r
    secret = 9876543210987654
    Q_full = E.mul(secret, W)
    P = E.mul(h, W)
    Q = E.mul(h, Q_full)
    assert P is not None and E.mul(r, P) is None
    aux, V = chain(p, 11, enumerate_all=True)
    (ROOT/'auxiliary.json').write_text(json.dumps(aux, indent=2)+'\n')
    representatives, raw_points, seen = [], [], set()
    for x in V:
        rhs = (x**3+3) % p
        y = pow(rhs, (p+1)//4, p)
        if y*y % p != rhs:
            continue
        raw = (x, min(y, p-y))
        projected = E.mul(h, raw)
        if projected is None or projected[0] in seen:
            continue
        seen.add(projected[0])
        representatives.append((projected[0], min(projected[1], p-projected[1])))
        raw_points.append(raw)
    public = dict(p=p, a=0, b=3, n=r, curve_order=curve_order,
                  cofactor=h, full_point_order=d, full_order_prime_factors=factors,
                  P_full=W, Q_full=Q_full, P=P, Q=Q,
                  factor_base_x_size=len(V),
                  factor_base_representatives=representatives,
                  raw_factor_base_points=raw_points)
    (ROOT/'public.json').write_text(json.dumps(public, indent=2)+'\n')
    with (ROOT/'public.txt').open('w') as out:
        out.write(f'{p} {r} 0 3\n{P[0]} {P[1]} {Q[0]} {Q[1]}\n{len(representatives)}\n')
        out.writelines(f'{x} {y}\n' for x,y in representatives)
    (ROOT/'expected.json').write_text(json.dumps(dict(secret=secret))+'\n')
    print(json.dumps({k:v for k,v in public.items() if k not in ['factor_base_representatives','raw_factor_base_points']},indent=2))
    print('Factor-base representatives:',len(representatives))


if __name__ == '__main__':
    main()
