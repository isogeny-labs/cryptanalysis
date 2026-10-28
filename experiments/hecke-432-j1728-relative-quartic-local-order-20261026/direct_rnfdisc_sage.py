"""Call PARI rnfdisc directly, bypassing Sage's rnfpolredbest step."""
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
    nf = L.pari_nf()
    polynomial = g._pari_with_name('x')
    print(json.dumps({'side': side, 'phase': 'direct_rnfdisc_started',
                      'pari_degree': int(polynomial.poldegree())}, sort_keys=True), flush=True)
    D, index_ideal = nf.rnfdisc(polynomial)
    relative_discriminant = L.ideal(nf.idealhnf(D))
    rows = []
    polynomial_discriminant = L.ideal(g.discriminant())
    for prior in screen['rows']:
        p = prior['prime']
        previous = {tuple(v['ideal_generators']): v for v in prior['places']}
        places = []
        for P in L.primes_above(p):
            generators = tuple(str(x) for x in P.gens())
            v_poly = int(polynomial_discriminant.valuation(P))
            assert v_poly == previous[generators][('left', 'right')[side]]['discriminant_valuation']
            v_field = int(relative_discriminant.valuation(P))
            difference = v_poly - v_field
            assert v_field >= 0 and difference >= 0 and difference % 2 == 0
            places.append({'ideal_generators': list(generators),
                           'residue_degree': int(P.residue_class_degree()),
                           'polynomial_discriminant_valuation': v_poly,
                           'maximal_order_relative_discriminant_valuation': v_field,
                           'local_order_index_exponent': difference // 2})
        rows.append({'prime': p, 'places': places,
                     'ramified_places': sum(v['maximal_order_relative_discriminant_valuation'] > 0
                                           for v in places),
                     'positive_index_places': sum(v['local_order_index_exponent'] > 0 for v in places)})
        print(json.dumps({'side': side, 'prime': p,
                          'ramified_places': rows[-1]['ramified_places'],
                          'positive_index_places': rows[-1]['positive_index_places']},
                         sort_keys=True), flush=True)
    out = {'status': 'PASS_DIRECT_RNFDISC_RELATIVE_IDEAL',
           'side': side,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'relative_discriminant_ideal_generators': [str(x) for x in relative_discriminant.gens()],
           'pari_index_ideal': str(index_ideal),
           'rows': rows}
    (HERE / f'direct_rnfdisc_side{side}.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'side': side}, sort_keys=True), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--side', type=int, choices=(0, 1), required=True)
    main(parser.parse_args().side)
