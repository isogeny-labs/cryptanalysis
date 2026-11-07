"""Independent direct-resultant and quartic/octic factor audit over K."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'exact_result': HERE / 'exact_result.json',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'relative_b_resolvent': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/relative_b_resolvent.json',
    'relative_xe_resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
}


def at_alpha(values, alpha, K):
    return sum((K(QQ(v)) * alpha ** i for i, v in enumerate(values)), K(0))


def main():
    path = HERE / 'exact_audit_protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    first = json.loads(INPUTS['exact_result'].read_text())
    assert first['status'] == 'PASS_EXACT_SOURCE_FIELD_RESULTANT_IDENTITY'
    field = json.loads(INPUTS['factor_certificate'].read_text())
    Qx = PolynomialRing(QQ, 'x')
    f = Qx([QQ(v) for v in field['field_polynomial_coefficients_low_to_high']])
    assert f.degree() == 18 and f.is_irreducible()
    K = NumberField(f, 'alpha')
    alpha = K.gen()
    y = (at_alpha(field['source_y_numerator_coefficients_low_to_high'], alpha, K) /
         at_alpha(field['source_y_denominator_coefficients_low_to_high'], alpha, K))
    assert y ** 2 + y == alpha ** 3 - 7
    Rz = PolynomialRing(K, 'z')
    z = Rz.gen()
    RT = PolynomialRing(Rz, 'T')
    T = RT.gen()
    b_terms = json.loads(INPUTS['relative_b_resolvent'].read_text())['terms']
    x_terms = json.loads(INPUTS['relative_xe_resolvent'].read_text())['terms']
    PB = sum((K(int(v['integer_coefficient']))
              * alpha ** v['x_C_exponent'] * y ** v['y_C_exponent']
              * T ** v['x_B_exponent'] for v in b_terms), RT.zero())
    XE = sum((K(int(v['integer_coefficient']))
              * alpha ** v['x_C_exponent'] * y ** v['y_C_exponent']
              * z ** v['x_E_exponent'] for v in x_terms), Rz.zero())
    F = T ** 3 - z * T ** 2 - 64
    direct = F.resultant(PB)
    assert direct.degree() == XE.degree() == 12
    assert direct == -16 * XE
    unit = at_alpha(field['unit'], alpha, K)
    factors = [Rz([at_alpha(vector, alpha, K)
                    for vector in record['coefficients_low_to_high']])
               for record in field['factors']]
    assert [q.degree() for q in factors] == [4, 8]
    assert all(q.is_irreducible() for q in factors)
    assert XE == unit * factors[0] * factors[1]
    assert [str(v) for v in first['scalar_coordinates_low_to_high']] == ['-16']
    coefficient_record = [[str(v) for v in c.polynomial().list()]
                          for c in direct.list()]
    out = {'status': 'PASS_DIRECT_EXACT_RESULTANT_AND_FACTOR_AUDIT',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'source_field_polynomial_irreducible': True,
           'source_curve_identity': True,
           'direct_resultant_scalar': '-16',
           'resultant_degree': 12, 'factor_degrees': [4, 8],
           'factors_irreducible': True,
           'factor_product_exact': True,
           'direct_resultant_coefficient_sha256': sha256(
               json.dumps(coefficient_record, sort_keys=True,
                          separators=(',', ':')).encode()).hexdigest()}
    (HERE / 'exact_audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
