"""Transport the left relative discriminant ideal by sqrt(2) conjugation."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ
from sage.misc.sage_eval import sage_eval

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
    protocol_path = HERE / 'conjugate_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    side0_path = HERE / 'direct_rnfdisc_side0.json'
    split_path = ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json'
    assert sha256(side0_path.read_bytes()).hexdigest() == protocol['input_sha256']['side0_discriminant']
    assert sha256(split_path.read_bytes()).hexdigest() == protocol['input_sha256']['split_certificate']
    side0 = json.loads(side0_path.read_text())
    split = json.loads(split_path.read_text())
    cert = json.loads((ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json').read_text())
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    Rt = PolynomialRing(K, 't')
    L = K.extension(Rt.gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    factors = [Lz([relative_element(v, alpha, s, K, L)
                   for v in record['coefficients_low_to_high']])
               for record in octic['factors']]
    left, right = factors
    assert [conjugate(c, K, L, s) for c in left.list()] == right.list()
    assert conjugate(left.discriminant(), K, L, s) == right.discriminant()
    context = {'alpha': alpha, 's': s}
    generators = [L(sage_eval(value, locals=context))
                  for value in side0['relative_discriminant_ideal_generators']]
    left_ideal = L.ideal(generators)
    transported = L.ideal([conjugate(value, K, L, s) for value in generators])
    screen = json.loads((HERE / 'result.json').read_text())
    rows = []
    for prior in screen['rows']:
        p = prior['prime']
        previous = {tuple(v['ideal_generators']): v for v in prior['places']}
        places = []
        for P in L.primes_above(p):
            key = tuple(str(x) for x in P.gens())
            v_poly = int(L.ideal(right.discriminant()).valuation(P))
            assert v_poly == previous[key]['right']['discriminant_valuation']
            v_field = int(transported.valuation(P))
            difference = v_poly - v_field
            assert v_field >= 0 and difference >= 0 and difference % 2 == 0
            places.append({'ideal_generators': list(key),
                           'residue_degree': int(P.residue_class_degree()),
                           'polynomial_discriminant_valuation': v_poly,
                           'transported_maximal_discriminant_valuation': v_field,
                           'local_order_index_exponent': difference // 2})
        rows.append({'prime': p, 'places': places,
                     'ramified_places': sum(x['transported_maximal_discriminant_valuation'] > 0
                                           for x in places),
                     'positive_index_places': sum(x['local_order_index_exponent'] > 0
                                                  for x in places)})
        print(json.dumps({'prime': p, 'ramified_places': rows[-1]['ramified_places'],
                          'positive_index_places': rows[-1]['positive_index_places']},
                         sort_keys=True), flush=True)
    out = {'status': 'PASS_CONJUGATE_MAXIMAL_DISCRIMINANT_TRANSPORT',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'coefficient_conjugation_identity': True,
           'discriminant_conjugation_identity': True,
           'left_ideal_generators_reconstructed': len(left_ideal.gens()),
           'rows': rows}
    (HERE / 'conjugate_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status']}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
