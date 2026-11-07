"""Exact discriminant product over the sqrt(2) conjugate factor field."""
import json
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ
from sympy import integer_nthroot

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'base_factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'sqrt2_factor_certificate': ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json',
    'pair_resultants': ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/resultant_norms.json',
    'base_discriminant_result': HERE / 'result.json',
}


def base_element(values, alpha, K):
    return sum((K(QQ(v)) * alpha ** i for i, v in enumerate(values)), K(0))


def relative_element(values, alpha, s, K, L):
    return sum((L(base_element(vector, alpha, K)) * s ** i
                for i, vector in enumerate(values)), L(0))


def to_base(value, K):
    if value.parent() is K:
        return value
    coordinates = value.list()
    assert all(v == 0 for v in coordinates[1:])
    return K(coordinates[0])


def exact_root(n, exponent):
    root, exact = integer_nthroot(n, exponent)
    assert exact and int(root) ** exponent == n
    return int(root)


def rational_fraction(value):
    value = QQ(value)
    return Fraction(int(value.numerator()), int(value.denominator()))


def main():
    path = HERE / 'relative_protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    base = json.loads(INPUTS['base_factor_certificate'].read_text())
    relative = json.loads(INPUTS['sqrt2_factor_certificate'].read_text())
    pairs = json.loads(INPUTS['pair_resultants'].read_text())
    norms = json.loads(INPUTS['base_discriminant_result'].read_text())
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(v) for v in base['field_polynomial_coefficients_low_to_high']]),
                    'alpha')
    alpha = K.gen()
    Qt = PolynomialRing(K, 't')
    L = K.extension(Qt.gen() ** 2 - 2, 's')
    s = L.gen()
    Kz = PolynomialRing(K, 'z')
    Lz = PolynomialRing(L, 'z')
    pair_rows = {r['base_degree']: r for r in pairs['rows']}
    norm_rows = {r['factor_degree']: r for r in norms['rows']}
    rows = []
    for original, record in zip(base['factors'], relative['records']):
        degree = len(original['coefficients_low_to_high']) - 1
        assert degree == record['base_degree']
        q = Kz([base_element(v, alpha, K)
                for v in original['coefficients_low_to_high']])
        unit = relative_element(record['unit'], alpha, s, K, L)
        assert unit == 1
        left, right = [Lz([relative_element(v, alpha, s, K, L)
                           for v in factor['coefficients_low_to_high']])
                       for factor in record['factors']]
        assert Lz([L(v) for v in q.list()]) == left * right
        assert [left.degree(), right.degree()] == [degree // 2] * 2
        disc_left = left.discriminant()
        disc_right = right.discriminant()
        pair_res = left.resultant(right)
        disc_base = q.discriminant()
        assert L(disc_base) == disc_left * disc_right * pair_res ** 2
        pair_norm = Fraction(int(pair_rows[degree]['norm_numerator']),
                             int(pair_rows[degree]['norm_denominator']))
        computed_pair_norm = rational_fraction(to_base(pair_res, K).norm())
        assert pair_norm == computed_pair_norm, (degree, pair_norm, computed_pair_norm)
        relative_norm = rational_fraction(disc_left.norm())
        base_norm = Fraction(int(norm_rows[degree]['discriminant_norm_numerator']),
                             int(norm_rows[degree]['discriminant_norm_denominator']))
        assert base_norm == relative_norm * pair_norm ** 2, (degree, base_norm, relative_norm * pair_norm ** 2)
        assert relative_norm.denominator == pair_norm.denominator == base_norm.denominator == 1
        assert relative_norm.numerator > 0 and pair_norm.numerator > 0
        relative_sixth_root = exact_root(relative_norm.numerator, 6)
        pair_cube_root = exact_root(pair_norm.numerator, 3)
        base_sixth_root = exact_root(base_norm.numerator, 6)
        assert base_sixth_root == relative_sixth_root * pair_cube_root
        rows.append({'base_degree': degree,
                     'relative_factor_degree': degree // 2,
                     'unit_is_one': True,
                     'discriminant_product_identity': True,
                     'relative_discriminant_norm_numerator': str(relative_norm.numerator),
                     'relative_discriminant_norm_denominator': str(relative_norm.denominator),
                     'relative_discriminant_sixth_root': str(relative_sixth_root),
                     'pair_resultant_norm_cube_root': str(pair_cube_root),
                     'base_discriminant_norm_sixth_root': str(base_sixth_root),
                     'sixth_root_product_identity': True})
        print(json.dumps({'degree': degree,
                          'relative_norm_digits': len(str(relative_norm.numerator)),
                          'relative_sixth_root_digits': len(str(relative_sixth_root))},
                         sort_keys=True), flush=True)
    out = {'status': 'PASS_RELATIVE_DISCRIMINANT_PRODUCT_AND_SIXTH_POWER',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'relative_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'degrees': [r['base_degree'] for r in rows]},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
