"""Use exact factor conjugation and an integral discriminant generator."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def base_element(values, alpha, K):
    return sum((K(QQ(v)) * alpha ** i for i, v in enumerate(values)), K(0))


def relative_element(values, alpha, s, K, L):
    return sum((L(base_element(vector, alpha, K)) * s ** i
                for i, vector in enumerate(values)), L(0))


def conjugate(value, K, L, s):
    coefficients = value.list()
    assert len(coefficients) <= 2
    return L(coefficients[0]) - L(coefficients[1] if len(coefficients) > 1 else K(0)) * s


def main():
    protocol_path = HERE / 'conjugate_support_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    inputs = {
        'side0_discriminant': HERE / 'direct_rnfdisc_side0.json',
        'local_screen_result': HERE / 'result.json',
        'split_certificate': ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json',
    }
    for name, path in inputs.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    side0 = json.loads(inputs['side0_discriminant'].read_text())
    screen = json.loads(inputs['local_screen_result'].read_text())
    split = json.loads(inputs['split_certificate'].read_text())
    assert side0['status'] == 'PASS_DIRECT_RNFDISC_RELATIVE_IDEAL'
    assert '96' in side0['relative_discriminant_ideal_generators']
    cert = json.loads((ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json').read_text())
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    Rt = PolynomialRing(K, 't')
    L = K.extension(Rt.gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    left, right = [Lz([relative_element(v, alpha, s, K, L)
                        for v in factor['coefficients_low_to_high']])
                   for factor in octic['factors']]
    assert [conjugate(c, K, L, s) for c in left.list()] == right.list()
    assert conjugate(left.discriminant(), K, L, s) == right.discriminant()
    left_by_prime = {r['prime']: {tuple(v['ideal_generators']): v for v in r['places']}
                     for r in side0['rows']}
    rows = []
    for prior in screen['rows']:
        p = prior['prime']
        assert 96 % p != 0
        places = []
        for place in prior['places']:
            key = tuple(place['ideal_generators'])
            direct_left = left_by_prime[p][key]
            assert direct_left['maximal_order_relative_discriminant_valuation'] == 0
            v_left = place['left']['discriminant_valuation']
            v_right = place['right']['discriminant_valuation']
            assert direct_left['polynomial_discriminant_valuation'] == v_left
            assert v_left % 2 == v_right % 2 == 0
            places.append({'ideal_generators': list(key),
                           'residue_degree': place['residue_degree'],
                           'left_local_order_index_exponent': v_left // 2,
                           'right_local_order_index_exponent': v_right // 2,
                           'left_relative_discriminant_valuation': 0,
                           'right_relative_discriminant_valuation_from_conjugation': 0})
        rows.append({'prime': p, 'places': places,
                     'left_positive_index_places': sum(v['left_local_order_index_exponent'] > 0
                                                       for v in places),
                     'right_positive_index_places': sum(v['right_local_order_index_exponent'] > 0
                                                        for v in places)})
    out = {'status': 'PASS_CONJUGATE_RELATIVE_DISCRIMINANT_SUPPORT',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'exact_factor_conjugation': True,
           'exact_polynomial_discriminant_conjugation': True,
           'fixed_integer_in_left_discriminant_ideal': 96,
           'rows': rows}
    (HERE / 'conjugate_support_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'index_counts': [[r['prime'], r['left_positive_index_places'],
                                        r['right_positive_index_places']] for r in rows]},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
