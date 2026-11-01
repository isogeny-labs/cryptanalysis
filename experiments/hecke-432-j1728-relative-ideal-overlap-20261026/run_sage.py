"""Prime-ideal valuation table for discriminant and resultant components."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'split_certificate': ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json',
    'field_index_result': ROOT / 'experiments/hecke-432-j1728-field-index-gate-20261026/result.json',
    'relative_discriminant_result': ROOT / 'experiments/hecke-432-j1728-discriminant-norms-20261026/relative_result.json',
}


def base_element(values, alpha, K):
    return sum((K(QQ(v)) * alpha ** i for i, v in enumerate(values)), K(0))


def relative_element(values, alpha, s, K, L):
    return sum((L(base_element(vector, alpha, K)) * s ** i
                for i, vector in enumerate(values)), L(0))


def to_base(value, K):
    coordinates = value.list()
    assert all(c == 0 for c in coordinates[1:])
    return K(coordinates[0])


def valuation(n, p):
    n = abs(ZZ(n))
    v = 0
    while n and n % p == 0:
        n //= p
        v += 1
    return v


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(INPUTS['factor_certificate'].read_text())
    split = json.loads(INPUTS['split_certificate'].read_text())
    field = json.loads(INPUTS['field_index_result'].read_text())
    relative = json.loads(INPUTS['relative_discriminant_result'].read_text())
    relative_rows = {r['base_degree']: r for r in relative['rows']}
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    R = PolynomialRing(K, 's')
    L = K.extension(R.gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    Kz = PolynomialRing(K, 'z')
    assert all(next(r for r in field['local'] if r['prime'] == p)['field_discriminant_valuation'] == 0
               for p in protocol['primes'])
    rows = []
    for original, record in zip(cert['factors'], split['records']):
        degree = record['base_degree']
        assert degree == len(original['coefficients_low_to_high']) - 1
        q = Kz([base_element(v, alpha, K) for v in original['coefficients_low_to_high']])
        left, right = [Lz([relative_element(v, alpha, s, K, L)
                           for v in factor['coefficients_low_to_high']])
                       for factor in record['factors']]
        assert Lz([L(c) for c in q.list()]) == left * right
        e = to_base(left.discriminant() * right.discriminant(), K)
        r = to_base(left.resultant(right), K)
        assert q.discriminant() == e * r ** 2
        known = relative_rows[degree]
        assert ZZ(e.norm()) == ZZ(known['relative_discriminant_norm_numerator'])
        assert ZZ(r.norm()) == ZZ(known['pair_resultant_norm_cube_root']) ** 3
        ideal_e = K.ideal(e)
        ideal_r = K.ideal(r)
        prime_rows = []
        for p in protocol['primes']:
            ideals = K.primes_above(p)
            assert sum(int(P.residue_class_degree()) for P in ideals) == 18
            places = []
            weighted_e = weighted_r = 0
            for P in ideals:
                f = int(P.residue_class_degree())
                ve = int(ideal_e.valuation(P))
                vr = int(ideal_r.valuation(P))
                weighted_e += f * ve
                weighted_r += f * vr
                places.append({'ideal_generators': [str(g) for g in P.gens()],
                               'residue_degree': f,
                               'relative_discriminant_valuation': ve,
                               'pair_resultant_valuation': vr,
                               'same_place_overlap': ve > 0 and vr > 0})
            assert weighted_e == valuation(e.norm(), p)
            assert weighted_r == valuation(r.norm(), p)
            prime_rows.append({'prime': p, 'places': places,
                               'weighted_relative_discriminant_valuation': weighted_e,
                               'weighted_pair_resultant_valuation': weighted_r,
                               'overlap_place_count': sum(x['same_place_overlap'] for x in places)})
        rows.append({'base_degree': degree,
                     'relative_discriminant_in_K_coefficients_low_to_high':
                         [str(c) for c in e.polynomial().list()],
                     'pair_resultant_in_K_coefficients_low_to_high':
                         [str(c) for c in r.polynomial().list()],
                     'primes': prime_rows})
        print(json.dumps({'degree': degree,
                          'overlap_counts': [[x['prime'], x['overlap_place_count']] for x in prime_rows]},
                         sort_keys=True), flush=True)
    result = {'status': 'PASS_RELATIVE_IDEAL_VALUATION_OVERLAP',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'rows': rows}
    (HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status']}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
