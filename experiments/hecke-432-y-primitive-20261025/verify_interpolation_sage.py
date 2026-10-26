"""Replay the independently interpolated polynomial in Sage's finite fields."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def decode(coefficients, field):
    assert len(coefficients) == 4
    return sum((field(c)*field.gen()**i for i,c in enumerate(coefficients)),field(0))


def main():
    certificate_path = HERE/'interpolation.json'
    data_path = ROOT/'hecke-432-geometric-fiber-20261025'/'evaluation.json'
    cert = json.loads(certificate_path.read_text())
    data = json.loads(data_path.read_text())
    assert cert['status'] == 'PASS_SPECIAL_FIBER_Y_INTERPOLATION'
    field = GF(997**4,'u')
    assert [int(c) for c in field.modulus().list()] == cert['field_modulus']
    base = GF(997)
    ring = PolynomialRing(base,'T')
    T = ring.gen()
    M = ring(cert['M_coefficients_low_to_high'])
    P = ring(cert['P_coefficients_low_to_high'])
    Q = ring(cert['Q_in_z_equals_y_squared_coefficients_low_to_high'])
    R = ring(cert['R_for_x_in_z_equals_y_squared_coefficients_low_to_high'])
    assert M.degree() == 24 and P.degree() == 22
    assert Q.degree() == 12 and R.degree() == 11
    assert M == Q(T**2) and P == R(T**2)
    assert (P**3-T**2+432) % M == 0
    assert (R**3-T+432) % Q == 0
    ys = []
    xs = []
    for row in data['rows']:
        x = decode(row['E_point'][0],field)
        y = decode(row['E_point'][1],field)
        assert M(y) == 0 and P(y) == x
        assert y**2 == x**3+432
        ys.append(y)
        xs.append(x)
    assert len(set(ys)) == 24 and len(set(xs)) == 12
    degree_counts = Counter()
    for poly,exponent in M.factor():
        degree_counts[int(poly.degree())] += int(exponent)
    assert sum(d*n for d,n in degree_counts.items()) == 24
    result = {'status':'PASS_SAGE_INTERPOLATION_REPLAY',
              'M_degree':24,'P_degree':22,'Q_degree':12,'R_degree':11,
              'M_irreducible_factor_degree_counts':dict(sorted(degree_counts.items())),
              'source_sha256':sha256(certificate_path.read_bytes()).hexdigest(),
              'evaluated_points':len(ys),'distinct_y':len(set(ys)),
              'distinct_x':len(set(xs))}
    (HERE/'interpolation_verification.json').write_text(
        json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()
