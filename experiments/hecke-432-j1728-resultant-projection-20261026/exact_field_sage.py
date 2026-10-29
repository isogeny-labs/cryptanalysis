"""Exact characteristic-zero source-field projection identity."""
import json
import time
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'relative_b_resolvent': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/relative_b_resolvent.json',
    'relative_xe_resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'finite_field_result': HERE / 'result.json',
}


def main():
    protocol_path = HERE / 'exact_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    start = time.monotonic()
    field = json.loads(INPUTS['factor_certificate'].read_text())
    Rx = PolynomialRing(QQ, 'x')
    f = Rx([QQ(c) for c in field['field_polynomial_coefficients_low_to_high']])
    assert f.degree() == 18
    K = NumberField(f, 'alpha')
    alpha = K.gen()
    numerator = sum((K(QQ(c)) * alpha ** i for i, c in enumerate(
        field['source_y_numerator_coefficients_low_to_high'])), K(0))
    denominator = sum((K(QQ(c)) * alpha ** i for i, c in enumerate(
        field['source_y_denominator_coefficients_low_to_high'])), K(0))
    assert denominator != 0
    y = numerator / denominator
    assert y ** 2 + y == alpha ** 3 - 7
    build_seconds = round(time.monotonic() - start, 3)
    print(json.dumps({'phase': 'source_field_ready', 'elapsed_seconds': build_seconds}),
          flush=True)
    Rz = PolynomialRing(K, 'z')
    z = Rz.gen()
    RT = PolynomialRing(Rz, 'T')
    T = RT.gen()
    b_terms = json.loads(INPUTS['relative_b_resolvent'].read_text())['terms']
    x_terms = json.loads(INPUTS['relative_xe_resolvent'].read_text())['terms']
    pb_coeffs = [K(0)] * 13
    xe_coeffs = [K(0)] * 13
    for term in b_terms:
        i = term['x_B_exponent']
        pb_coeffs[i] += (K(int(term['integer_coefficient']))
                         * alpha ** term['x_C_exponent']
                         * y ** term['y_C_exponent'])
    for term in x_terms:
        i = term['x_E_exponent']
        xe_coeffs[i] += (K(int(term['integer_coefficient']))
                         * alpha ** term['x_C_exponent']
                         * y ** term['y_C_exponent'])
    PB = RT([Rz(c) for c in pb_coeffs])
    F = T ** 3 - z * T ** 2 - 64
    rem = PB % F
    assert rem.degree() <= 2
    a, b, c = rem[2], rem[1], rem[0]
    Q = (4096 * a ** 3 - 128 * a ** 2 * c * z + 64 * a * b ** 2 * z
         - 192 * a * b * c + a * c ** 2 * z ** 2
         + 64 * b ** 3 + b * c ** 2 * z + c ** 3)
    XE = Rz(xe_coeffs)
    assert Q.degree() == XE.degree() == 12
    scalar = Q.leading_coefficient() / XE.leading_coefficient()
    assert scalar != 0
    identity = bool(Q == scalar * XE)
    out = {'status': 'PASS_EXACT_SOURCE_FIELD_RESULTANT_IDENTITY'
                     if identity else 'EXACT_SOURCE_FIELD_IDENTITY_MISMATCH',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'source_field_degree': 18, 'source_curve_identity': True,
           'b_remainder_degree': int(rem.degree()),
           'resultant_degree': int(Q.degree()),
           'xe_resolvent_degree': int(XE.degree()),
           'scalar_coordinates_low_to_high': [str(v) for v in scalar.polynomial().list()],
           'coefficient_identity': identity,
           'elapsed_seconds': round(time.monotonic() - start, 3)}
    (HERE / 'exact_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: out[k] for k in ('status', 'source_field_degree',
          'resultant_degree', 'coefficient_identity', 'elapsed_seconds')},
          sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
