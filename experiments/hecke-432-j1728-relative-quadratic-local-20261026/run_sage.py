"""Local discriminant valuation parity for the relative quadratic factors."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'split_certificate': ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json',
    'relative_discriminant_result': ROOT / 'experiments/hecke-432-j1728-discriminant-norms-20261026/relative_result.json',
    'relative_ideal_overlap_result': ROOT / 'experiments/hecke-432-j1728-relative-ideal-overlap-20261026/result.json',
}


def base_element(values, alpha, K):
    return sum((K(QQ(v)) * alpha ** i for i, v in enumerate(values)), K(0))


def relative_element(values, alpha, s, K, L):
    return sum((L(base_element(vector, alpha, K)) * s ** i
                for i, vector in enumerate(values)), L(0))


def valuation(n, p):
    n = abs(ZZ(n))
    count = 0
    while n and n % p == 0:
        n //= p
        count += 1
    return count


def save(rows, protocol_path, status):
    output = {'status': status,
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'base_degree': 4, 'relative_factor_degree': 2,
              'rows': rows}
    (HERE / 'result.json').write_text(json.dumps(output, sort_keys=True, indent=2) + '\n')


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(INPUTS['factor_certificate'].read_text())
    split = json.loads(INPUTS['split_certificate'].read_text())
    known = json.loads(INPUTS['relative_discriminant_result'].read_text())
    overlap = json.loads(INPUTS['relative_ideal_overlap_result'].read_text())
    quartic = next(r for r in split['records'] if r['base_degree'] == 4)
    known_quartic = next(r for r in known['rows'] if r['base_degree'] == 4)
    overlap_quartic = next(r for r in overlap['rows'] if r['base_degree'] == 4)
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    Rt = PolynomialRing(K, 't')
    L = K.extension(Rt.gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    factors = [Lz([relative_element(v, alpha, s, K, L)
                   for v in factor['coefficients_low_to_high']])
               for factor in quartic['factors']]
    assert len(factors) == 2 and all(g.degree() == 2 and g.is_monic() and g.is_irreducible()
                                     for g in factors)
    left, right = factors
    discs = [g.discriminant() for g in factors]
    assert all(d == g[1] ** 2 - 4 * g[0] for g, d in zip(factors, discs))
    assert discs[0] * discs[1] != 0
    assert ZZ(discs[0].norm()) == ZZ(known_quartic['relative_discriminant_norm_numerator'])
    assert ZZ(discs[1].norm()) == ZZ(known_quartic['relative_discriminant_norm_numerator'])
    ideals = [L.ideal(d) for d in discs]
    rows = []
    for p in protocol['primes']:
        prime_ideals = L.primes_above(p)
        assert sum(int(P.residue_class_degree()) for P in prime_ideals) == 36
        places = []
        weighted = [0, 0]
        for P in prime_ideals:
            f = int(P.residue_class_degree())
            coefficient_valuations = [[int(L.ideal(c).valuation(P)) if c else None
                                       for c in g.list()] for g in factors]
            assert all(v is None or v >= 0 for values in coefficient_valuations for v in values)
            values = [int(I.valuation(P)) for I in ideals]
            assert all(v >= 0 for v in values)
            for i, v in enumerate(values):
                weighted[i] += f * v
            places.append({'ideal_generators': [str(g) for g in P.gens()],
                           'residue_degree': f,
                           'left_discriminant_valuation': values[0],
                           'right_discriminant_valuation': values[1],
                           'left_coefficient_valuations': coefficient_valuations[0],
                           'right_coefficient_valuations': coefficient_valuations[1],
                           'left_local_order_index_exponent': values[0] // 2,
                           'right_local_order_index_exponent': values[1] // 2,
                           'left_ramifies_by_odd_discriminant_valuation': bool(values[0] % 2),
                           'right_ramifies_by_odd_discriminant_valuation': bool(values[1] % 2)})
        assert weighted == [valuation(d.norm(), p) for d in discs]
        previous = next(r for r in overlap_quartic['primes'] if r['prime'] == p)
        assert weighted[0] == weighted[1] == previous['weighted_relative_discriminant_valuation']
        row = {'prime': p, 'places': places,
               'weighted_discriminant_valuations': weighted,
               'odd_left_place_count': sum(x['left_ramifies_by_odd_discriminant_valuation'] for x in places),
               'odd_right_place_count': sum(x['right_ramifies_by_odd_discriminant_valuation'] for x in places)}
        rows.append(row)
        save(rows, protocol_path, 'PARTIAL_LOCAL_QUADRATIC_VALUATIONS')
        print(json.dumps({'prime': p, 'places': len(places),
                          'odd_counts': [row['odd_left_place_count'], row['odd_right_place_count']]},
                         sort_keys=True), flush=True)
    save(rows, protocol_path, 'PASS_LOCAL_QUADRATIC_DISCRIMINANT_PARITY')
    print(json.dumps({'status': 'PASS_LOCAL_QUADRATIC_DISCRIMINANT_PARITY'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
