"""Universal eight-term resultant and source-local projection replay."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'multiplicity_result': ROOT / 'experiments/hecke-432-j1728-fiber-overlap-20261026/multiplicity_result.json',
    'branch_gcd_result': ROOT / 'experiments/hecke-432-j1728-derivative-ideal-20261026/result.json',
    'relative_b_resolvent': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/relative_b_resolvent.json',
    'relative_xe_resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
}


def term_coefficients(terms, x, y, degree, exponent_name, F):
    values = [F(0)] * (degree + 1)
    for term in terms:
        k = term[exponent_name]
        values[k] += (F(int(term['integer_coefficient']))
                      * x ** term['x_C_exponent']
                      * y ** term['y_C_exponent'])
    return values


def universal_identity():
    M = PolynomialRing(ZZ, names=('a', 'b', 'c', 'z'))
    a, b, c, z = M.gens()
    RT = PolynomialRing(M, 'T')
    T = RT.gen()
    F = T ** 3 - z * T ** 2 - 64
    R = a * T ** 2 + b * T + c
    formula = (4096 * a ** 3 - 128 * a ** 2 * c * z + 64 * a * b ** 2 * z
               - 192 * a * b * c + a * c ** 2 * z ** 2 + 64 * b ** 3
               + b * c ** 2 * z + c ** 3)
    assert F.resultant(R) == formula
    return str(formula)


def main():
    path = HERE / 'protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    formula = universal_identity()
    b_terms = json.loads(INPUTS['relative_b_resolvent'].read_text())['terms']
    x_terms = json.loads(INPUTS['relative_xe_resolvent'].read_text())['terms']
    sources = json.loads(INPUTS['multiplicity_result'].read_text())['results']
    gcd_results = json.loads(INPUTS['branch_gcd_result'].read_text())['results']
    assert [r['prime'] for r in sources] == [r['prime'] for r in gcd_results]
    result_rows = []
    all_coefficients_match = True
    all_derivatives_match = True
    root_total = 0
    for field, gcd_field in zip(sources, gcd_results):
        p = ZZ(field['prime'])
        assert p.is_prime(proof=True)
        Fp = GF(p)
        Rz = PolynomialRing(Fp, 'z')
        z = Rz.gen()
        RT = PolynomialRing(Rz, 'T')
        T = RT.gen()
        gcd_map = {(tuple(row['C_point']), row['x_E']): row
                   for row in gcd_field['rows']}
        for source in field['rows']:
            x, y = (Fp(int(v)) for v in source['C_point'])
            bc = term_coefficients(b_terms, x, y, 12, 'x_B_exponent', Fp)
            xc = term_coefficients(x_terms, x, y, 12, 'x_E_exponent', Fp)
            PB = RT([Rz(v) for v in bc])
            F = T ** 3 - z * T ** 2 - 64
            Q = F.resultant(PB)
            XE = Rz(xc)
            degree_12 = Q.degree() == XE.degree() == 12
            scalar = (Q.leading_coefficient() / XE.leading_coefficient()
                      if degree_12 else Fp(0))
            coefficients_match = bool(degree_12 and scalar and Q == scalar * XE)
            all_coefficients_match &= coefficients_match
            derivative_matches = True
            for root in source['roots']:
                zr = Fp(int(root['x_E']))
                pair = gcd_map[(tuple(source['C_point']), root['x_E'])]
                derivative_zero = bool(Q.derivative()(zr) == 0)
                derivative_matches &= bool(Q(zr) == 0 and XE(zr) == 0 and
                                           derivative_zero ==
                                           (pair['common_B_gcd_degree'] == 2))
                root_total += 1
            all_derivatives_match &= derivative_matches
            result_rows.append({'prime': str(p), 'C_point': source['C_point'],
                                'resultant_degree': int(Q.degree()),
                                'xe_resolvent_degree': int(XE.degree()),
                                'scalar': str(int(scalar)),
                                'coefficient_identity': coefficients_match,
                                'root_derivative_criterion': derivative_matches,
                                'rational_roots_checked': len(source['roots']),
                                'resultant_coefficients_low_to_high':
                                    [str(int(v)) for v in Q.list()]})
    assert len(result_rows) == protocol['source_points']
    assert root_total == protocol['rational_roots']
    out = {'status': 'PASS_RESULTANT_PROJECTION_AND_DERIVATIVE_BRIDGE'
                     if all_coefficients_match and all_derivatives_match
                     else 'RESULTANT_PROJECTION_PREDICTION_MISMATCH',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'universal_resultant_formula_verified': True,
           'universal_resultant_formula': formula,
           'source_points_checked': len(result_rows),
           'rational_roots_checked': root_total,
           'coefficient_identities_match': bool(all_coefficients_match),
           'derivative_criteria_match': bool(all_derivatives_match),
           'rows': result_rows}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: out[key] for key in ('status',
          'source_points_checked', 'rational_roots_checked',
          'coefficient_identities_match', 'derivative_criteria_match')},
          sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
