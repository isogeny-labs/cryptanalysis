"""Check the shifted Γ0 containment and modular-curve invariants exactly."""
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import random

from sage.all import EllipticCurve, Gamma0, O, QQ

HERE = Path(__file__).resolve().parent


def multiply(u, v):
    return [[sum(u[i][k]*v[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def shifted(a, b, c, d, shift):
    t = [[Fraction(1), shift], [Fraction(0), Fraction(1)]]
    ti = [[Fraction(1), -shift], [Fraction(0), Fraction(1)]]
    return multiply(multiply(t, [[a, b], [c, d]]), ti)


def main():
    p = json.loads((HERE/'protocol.json').read_text())
    assert p['status'] == 'FROZEN_BEFORE_PERSISTED_SUBGROUP_AND_GENUS_RUN_AFTER_SYMBOLIC_DERIVATION'
    source, target = p['source_level'], p['target_level']
    assert source == 432 and target == 27
    assert source == 16*target
    rng = random.Random(p['sample_seed'])
    checks = 0
    examples = []
    for _ in range(p['sample_count']):
        k = rng.choice([j for j in range(-20, 21) if j])
        c = source*k
        a = rng.randrange(-1000, 1000)
        while a == 0 or __import__('math').gcd(a, c) != 1:
            a = rng.randrange(-1000, 1000)
        d = pow(a, -1, abs(c)) + rng.randrange(-3, 4)*abs(c)
        b = (a*d-1)//c
        assert a*d-b*c == 1
        for s in (Fraction(1, 4), Fraction(-1, 4)):
            m = shifted(a, b, c, d, s)
            assert all(x.denominator == 1 for row in m for x in row)
            assert m[0][0]*m[1][1]-m[0][1]*m[1][0] == 1
            assert m[1][0] % target == 0
            checks += 1
            if len(examples) < 4:
                examples.append({'input': [a,b,c,d], 'shift': str(s),
                                 'conjugate': [int(x) for row in m for x in row]})
    g_source, g_target = Gamma0(source), Gamma0(target)
    index_source, index_target = int(g_source.index()), int(g_target.index())
    assert (index_source, index_target) == (864, 36)
    assert index_source//index_target == 24
    A = EllipticCurve(QQ, [0, 0, 1, 0, 0])
    xa, ya = A.modular_parametrization().power_series(prec=64)
    fa = A.q_expansion(65)
    q = xa.parent().gen()
    assert xa.derivative()/(2*ya+1) + O(q**52) == fa/q + O(q**52)
    # Necessity: [[1,0],[N,1]] has upper-right entry -N/16 after +1/4 conjugation.
    minimality = {}
    for n in (27, 54, 108, 216, 432):
        m = shifted(1, 0, n, 1, Fraction(1,4))
        minimality[str(n)] = {'integral': all(x.denominator == 1 for row in m for x in row),
                              'lower_left_divisible_27': m[1][0] % 27 == 0}
    assert [n for n, v in minimality.items() if v['integral'] and v['lower_left_divisible_27']] == ['432']
    out = {'status': 'PASS_SHIFTED_SUBGROUP_DIAGNOSTICS',
           'protocol_sha256': sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
           'source_index': index_source, 'target_index': index_target,
           'source_genus': int(g_source.genus()), 'target_genus': int(g_target.genus()),
           'map_degree_each_shift': index_source//index_target,
           'A_differential_identity_q_exclusive': 52,
           'exact_matrix_samples': checks, 'examples': examples,
           'minimality_controls': minimality}
    (HERE/'result.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','source_genus','target_genus','map_degree_each_shift','exact_matrix_samples')},sort_keys=True))


if __name__ == '__main__':
    main()
