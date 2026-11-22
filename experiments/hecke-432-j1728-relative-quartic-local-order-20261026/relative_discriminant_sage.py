"""Exact relative discriminant ideal and local order index for one side."""
import argparse
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'split_certificate': ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json',
    'local_screen_result': HERE / 'result.json',
}


def base_element(values, alpha, K):
    return sum((K(QQ(v)) * alpha ** i for i, v in enumerate(values)), K(0))


def relative_element(values, alpha, s, K, L):
    return sum((L(base_element(vector, alpha, K)) * s ** i
                for i, vector in enumerate(values)), L(0))


def main(side):
    protocol_path = HERE / 'relative_discriminant_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(INPUTS['factor_certificate'].read_text())
    split = json.loads(INPUTS['split_certificate'].read_text())
    screen = json.loads(INPUTS['local_screen_result'].read_text())
    assert screen['status'] == 'PASS_RELATIVE_QUARTIC_LOCAL_SCREEN'
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    Rt = PolynomialRing(K, 't')
    L = K.extension(Rt.gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    record = octic['factors'][side]
    g = Lz([relative_element(v, alpha, s, K, L)
            for v in record['coefficients_low_to_high']])
    assert g.degree() == 4 and g.is_monic() and g.is_irreducible()
    F = L.extension(g, 'theta')
    assert F.absolute_degree() == 144
    print(json.dumps({'side': side, 'phase': 'relative_field_constructed',
                      'absolute_degree': 144}, sort_keys=True), flush=True)
    actual_discriminant = F.relative_discriminant()
    print(json.dumps({'side': side, 'phase': 'relative_discriminant_computed'},
                     sort_keys=True), flush=True)
    polynomial_discriminant = L.ideal(g.discriminant())
    rows = []
    for prior in screen['rows']:
        p = prior['prime']
        assert p in protocol['primes']
        by_generators = {tuple(place['ideal_generators']): place for place in prior['places']}
        places = []
        for P in L.primes_above(p):
            generators = tuple(str(x) for x in P.gens())
            before = by_generators[generators][('left', 'right')[side]]
            v_poly = int(polynomial_discriminant.valuation(P))
            assert v_poly == before['discriminant_valuation']
            v_maximal = int(actual_discriminant.valuation(P))
            difference = v_poly - v_maximal
            assert v_maximal >= 0 and difference >= 0 and difference % 2 == 0
            places.append({'ideal_generators': list(generators),
                           'residue_degree': int(P.residue_class_degree()),
                           'polynomial_discriminant_valuation': v_poly,
                           'maximal_order_relative_discriminant_valuation': v_maximal,
                           'local_order_index_exponent': difference // 2,
                           'ramified': bool(v_maximal > 0)})
        rows.append({'prime': p, 'places': places,
                     'ramified_places': sum(x['ramified'] for x in places),
                     'positive_index_places': sum(x['local_order_index_exponent'] > 0 for x in places),
                     'weighted_maximal_discriminant_valuation':
                         sum(x['residue_degree'] * x['maximal_order_relative_discriminant_valuation']
                             for x in places)})
        print(json.dumps({'side': side, 'prime': p, 'ramified': rows[-1]['ramified_places'],
                          'positive_index': rows[-1]['positive_index_places']},
                         sort_keys=True), flush=True)
    out = {'status': 'PASS_RELATIVE_QUARTIC_MAXIMAL_DISCRIMINANT',
           'side': side,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'absolute_field_degree': 144,
           'relative_discriminant_ideal_generators': [str(x) for x in actual_discriminant.gens()],
           'rows': rows}
    (HERE / f'relative_discriminant_side{side}.json').write_text(
        json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'side': side}, sort_keys=True), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--side', type=int, choices=(0, 1), required=True)
    main(parser.parse_args().side)
