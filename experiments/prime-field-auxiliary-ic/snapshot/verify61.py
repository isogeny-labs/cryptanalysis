"""Audit projected index calculus and recover the full mixed-order logarithm."""
import json
from pathlib import Path
from sympy import isprime
from sympy.ntheory.modular import crt
from prepare import Curve, chain

ROOT = Path(__file__).resolve().parent/'run61'


def main():
    public = json.loads((ROOT/'public.json').read_text())
    cert = json.loads((ROOT/'certificate.json').read_text())
    p, r = public['p'], public['n']
    N, h, d = public['curve_order'], public['cofactor'], public['full_point_order']
    E = Curve(p, a6=3)
    P, Q = tuple(public['P']), tuple(public['Q'])
    W, Q_full = tuple(public['P_full']), tuple(public['Q_full'])
    factors = public['full_order_prime_factors']
    assert isprime(p) and all(isprime(ell) for ell in factors)
    assert d == 2*11*30223*r and N == 22*d
    assert E.contains(W) and E.contains(Q_full)
    assert E.mul(d,W) is None and all(E.mul(d//ell,W) is not None for ell in factors)
    assert (N-(p+1))**2 <= 4*p and d*d > 16*p
    assert P == E.mul(h,W) and Q == E.mul(h,Q_full)
    assert E.mul(r,P) is None and P is not None

    aux, V = chain(p, 11, enumerate_all=True)
    assert json.loads(json.dumps(aux)) == json.loads((ROOT/'auxiliary.json').read_text())
    V = set(V)
    F = [tuple(R) for R in public['factor_base_representatives']]
    raw = [tuple(R) for R in public['raw_factor_base_points']]
    assert len(F) == len(raw) and len({R[0] for R in F}) == len(F)
    for R, projected in zip(raw,F):
        assert R[0] in V and E.contains(R)
        image = E.mul(h,R)
        assert projected == image or projected == E.neg(image)
        assert E.mul(r,projected) is None

    def f3(x,y,z):
        return ((x-y)**2*z*z - 2*((x+y)*x*y+6)*z + (x*y)**2-12*(x+y)) % p

    rels = [json.loads(line) for line in (ROOT/'relations.jsonl').read_text().splitlines()]
    assert len(rels) == cert['relations'] == len(cert['weights'])
    coefficients = [0]*len(F)
    aug_a = aug_b = 0
    for rel,weight in zip(rels,cert['weights']):
        points = []
        for code in rel['codes']:
            R = F[code//2]
            points.append(E.neg(R) if code & 1 else R)
            coefficients[code//2] += weight*(-1 if code & 1 else 1)
        left = E.add(E.mul(rel['a'],P),E.mul(rel['b'],Q))
        U = E.add(points[0],points[1])
        assert E.add(U,points[2]) == left
        assert U is not None and left is not None
        assert f3(points[0][0],points[1][0],U[0]) == 0
        assert f3(U[0],points[2][0],left[0]) == 0
        aug_a -= weight*rel['a']
        aug_b -= weight*rel['b']
    assert all(c % r == 0 for c in coefficients)
    assert aug_a % r == cert['dependency_A']
    assert aug_b % r == cert['dependency_B'] != 0
    k_r = -aug_a*pow(aug_b,-1,r) % r
    assert k_r == cert['recovered'] and E.mul(k_r,P) == Q

    # Ordinary Pohlig-Hellman decomposition for the three small components.
    # The largest (38-bit) component came only from index calculus above.
    residues = []
    for ell in factors[:-1]:
        S, T = E.mul(d//ell,W), E.mul(d//ell,Q_full)
        R = None
        for j in range(ell):
            if R == T:
                residues.append(j)
                break
            R = E.add(R,S)
        else:
            raise AssertionError('Small-component logarithm not found')
    residues.append(k_r)
    recovered, modulus = map(int,crt(factors,residues))
    assert modulus == d and E.mul(recovered,W) == Q_full
    assert recovered == json.loads((ROOT/'expected.json').read_text())['secret']
    result = dict(field_prime=p,curve_order=N,point_order=d,
                  largest_prime_factor=r,subgroup_log=k_r,
                  small_component_moduli=factors[:-1],
                  small_component_residues=residues[:-1],
                  full_recovered=recovered,verified=True,
                  auxiliary_roots_checked=len(V),factor_base_columns=len(F),
                  relations=len(rels))
    (ROOT/'full_result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    print('PASS: all relations, Semaev equations, map roots, projected points,')
    print('elimination weights, group-order certificates, and full [k]W=Q verified.')


if __name__ == '__main__':
    main()
