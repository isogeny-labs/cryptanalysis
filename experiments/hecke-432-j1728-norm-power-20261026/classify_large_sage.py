"""Registered original-source and C-E replay at the new 83-bit exception."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
}


def source_expression(terms, x, y, F):
    return sum((F(QQ(term['coefficient']))
                * x ** term['x_power'] * y ** term['y_power']
                for term in terms), F(0))


def chain_expression(terms, x, y, z, F):
    return sum((F(ZZ(term['integer_coefficient']))
                * x ** term['x_C_exponent']
                * y ** term['y_C_exponent']
                * z ** term['x_E_exponent'] for term in terms), F(0))


def main():
    pp = HERE / 'protocol.json'
    protocol = json.loads(pp.read_text())
    ap = HERE / 'audit_protocol.json'
    audit_protocol = json.loads(ap.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    p = protocol['large_prime']
    assert ZZ(p).is_prime(proof=True) and p % 24 == 11
    F = GF(p)
    cert = json.loads(INPUTS['factor_certificate'].read_text())
    coord = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    resolvent = json.loads(INPUTS['resolvent'].read_text())['terms']
    branch = json.loads(INPUTS['branch_formula'].read_text())
    Rx = PolynomialRing(F, 'x')
    xvar = Rx.gen()
    Ry = PolynomialRing(Rx, 'y')
    yvar = Ry.gen()
    H = (source_expression(coord['numerator'], xvar, yvar, F)
         + 1728 * source_expression(coord['denominator'], xvar, yvar, F))
    curve = yvar ** 2 + yvar - xvar ** 3 + 7
    eliminant = H.resultant(curve)
    f = Rx([F(QQ(c)) for c in cert['field_polynomial_coefficients_low_to_high']])
    assert eliminant.degree() == 36
    assert eliminant.monic() == (f * f).monic()
    sources = []
    undefined_map = []
    for x, _ in f.roots():
        Fy = PolynomialRing(F, 'v')
        v = Fy.gen()
        for y, _ in (v ** 2 + v - x ** 3 + 7).roots():
            numerator = source_expression(coord['numerator'], x, y, F)
            denominator = source_expression(coord['denominator'], x, y, F)
            if not denominator:
                undefined_map.append([str(int(x)), str(int(y))])
            elif numerator + 1728 * denominator == 0:
                sources.append((x, y))
    Rz = PolynomialRing(F, 'z')
    zvar = Rz.gen()
    rows = []
    for x, y in sources:
        R = chain_expression(resolvent, x, y, zvar, F)
        pairs = []
        x_roots = R.roots()
        for z, _ in x_roots:
            square = z ** 3 + 432
            if not square.is_square():
                continue
            y_values = [F(0)] if square == 0 else [square.sqrt(), -square.sqrt()]
            for ye in y_values:
                assert ye ** 2 == square
                numerator = chain_expression(branch['numerator_terms'], x, y, z, F)
                denominator = chain_expression(branch['denominator_terms'], x, y, z, F)
                pairs.append({'E_point': [str(int(z)), str(int(ye))],
                              'branch_numerator_zero': bool(numerator == 0),
                              'branch_denominator_zero': bool(denominator == 0),
                              'status': ('ZERO_DENOMINATOR' if denominator == 0 else
                                         'NONZERO_BRANCH_DENOMINATOR')})
        rows.append({'C_point': [str(int(x)), str(int(y))],
                     'resolvent_degree': int(R.degree()),
                     'rational_x_E_roots': len(x_roots),
                     'rational_CE_pairs': len(pairs), 'pairs': pairs})
    rows.sort(key=lambda row: row['C_point'])
    total_pairs = sum(row['rational_CE_pairs'] for row in rows)
    zero_branch_pairs = sum(pair['status'] == 'ZERO_DENOMINATOR'
                            for row in rows for pair in row['pairs'])
    assert len(sources) == audit_protocol['expected_large_prime_C_points']
    assert total_pairs == audit_protocol['expected_large_prime_CE_pairs']
    assert zero_branch_pairs == audit_protocol['expected_large_prime_zero_branch_pairs']
    out = {'status': 'PASS_REGISTERED_LARGE_PRIME_SOURCE_AND_BRANCH_REPLAY',
           'protocol_sha256': sha256(pp.read_bytes()).hexdigest(),
           'audit_protocol_sha256': sha256(ap.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'prime': str(p), 'source_eliminant_degree': int(eliminant.degree()),
           'source_eliminant_equals_scalar_field_square': True,
           'source_points': len(sources), 'undefined_source_j_points': undefined_map,
           'rational_CE_pairs': total_pairs, 'zero_branch_pairs': zero_branch_pairs,
           'rows': rows}
    (HERE / 'large_prime_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: out[key] for key in
                      ('status', 'prime', 'source_points', 'rational_CE_pairs',
                       'zero_branch_pairs')}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
