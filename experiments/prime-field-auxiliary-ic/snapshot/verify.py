"""Independently verify every relation and the elimination certificate."""
import json
from pathlib import Path
from sympy import isprime
from prepare import Curve, chain

ROOT = Path(__file__).resolve().parent
public = json.loads((ROOT/'public.json').read_text())
cert = json.loads((ROOT/'certificate.json').read_text())
p, n = public['p'], public['n']
E = Curve(p, a4=public['a'], a6=public['b'])
P, Q = tuple(public['P']), tuple(public['Q'])
assert isprime(p) and isprime(n)
assert E.contains(P) and E.contains(Q) and E.mul(n, P) is None
assert abs(n-(p+1))**2 <= 4*p
assert 2*n > p+1+2*p**0.5  # Only one positive multiple in Hasse interval.
aux, V = chain(p, 10)
assert json.loads(json.dumps(aux)) == json.loads((ROOT/'auxiliary_31.json').read_text())
F = [tuple(R) for R in public['factor_base_representatives']]
expected_x = {x for x in V if pow((x**3+E.a4*x+E.a6)%p, (p-1)//2, p) == 1}
assert {R[0] for R in F} == expected_x
assert all(E.contains(R) for R in F)


def f3(x, y, z):
    a, b = E.a4, E.a6
    return ((x-y)**2*z*z - 2*((x+y)*(x*y+a)+2*b)*z
            + (x*y-a)**2 - 4*b*(x+y)) % p


rels = [json.loads(line) for line in (ROOT/'relations.jsonl').read_text().splitlines()]
assert len(rels) == cert['relations'] == len(cert['weights'])
coefficients = [0]*len(F)
aug_a = aug_b = 0
for rel, weight in zip(rels, cert['weights']):
    points = []
    for code in rel['codes']:
        R = F[code//2]
        points.append(E.neg(R) if code & 1 else R)
        coefficients[code//2] += weight*(-1 if code & 1 else 1)
    left = E.add(E.mul(rel['a'], P), E.mul(rel['b'], Q))
    U = E.add(points[0], points[1])
    assert E.add(U, points[2]) == left
    assert U is not None and left is not None
    # These two quartics imply the relevant Semaev S4 equation.
    assert f3(points[0][0], points[1][0], U[0]) == 0
    assert f3(U[0], points[2][0], left[0]) == 0
    aug_a -= weight*rel['a']
    aug_b -= weight*rel['b']
assert all(c % n == 0 for c in coefficients)
assert aug_a % n == cert['dependency_A']
assert aug_b % n == cert['dependency_B'] != 0
recovered = -aug_a*pow(aug_b, -1, n) % n
assert recovered == cert['recovered']
assert E.mul(recovered, P) == Q
assert recovered == json.loads((ROOT/'expected.json').read_text())['secret']
print(f'PASS: all {len(rels)} relations, both Semaev quartics per relation,')
print(f'all {len(V)} map roots, all {len(F)} canceled factor-base columns,')
print(f'and recovered k={recovered} independently verified.')
