"""Exact local reduction and discriminant screen for relative quartic factors."""
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
    out = {'status': status, 'base_degree': 8, 'relative_factor_degree': 4,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(INPUTS['factor_certificate'].read_text())
    split = json.loads(INPUTS['split_certificate'].read_text())
    known = json.loads(INPUTS['relative_discriminant_result'].read_text())
    relative = next(r for r in known['rows'] if r['base_degree'] == 8)
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    Rt = PolynomialRing(K, 't')
    L = K.extension(Rt.gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    factors = [Lz([relative_element(v, alpha, s, K, L)
                   for v in factor['coefficients_low_to_high']])
               for factor in octic['factors']]
    assert len(factors) == 2 and all(g.degree() == 4 and g.is_monic() and g.is_irreducible()
                                     for g in factors)
    discs = [g.discriminant() for g in factors]
    assert all(ZZ(d.norm()) == ZZ(relative['relative_discriminant_norm_numerator']) for d in discs)
    ideals = [L.ideal(d) for d in discs]
    rows = []
    for p in protocol['primes']:
        primes = L.primes_above(p)
        assert sum(int(P.residue_class_degree()) for P in primes) == 36
        places = []
        weighted = [0, 0]
        for P in primes:
            F = P.residue_field()
            Fz = PolynomialRing(F, 'z')
            f = int(P.residue_class_degree())
            data = []
            for side, g in enumerate(factors):
                coeff_valuations = [int(L.ideal(c).valuation(P)) if c else None for c in g.list()]
                assert all(v is None or v >= 0 for v in coeff_valuations)
                reduced = Fz([F(c) for c in g.list()])
                assert reduced.degree() == 4
                pattern = sorted([[int(h.degree()), int(e)] for h, e in reduced.factor()])
                v = int(ideals[side].valuation(P))
                weighted[side] += f * v
                repeated = any(e > 1 for _, e in pattern)
                assert repeated == (v > 0)
                data.append({'discriminant_valuation': v,
                             'coefficient_valuations': coeff_valuations,
                             'reduced_factor_degrees_exponents': pattern,
                             'repeated_reduction': repeated})
            places.append({'ideal_generators': [str(x) for x in P.gens()],
                           'residue_degree': f,
                           'left': data[0], 'right': data[1]})
        assert weighted == [valuation(d.norm(), p) for d in discs]
        row = {'prime': p, 'places': places,
               'weighted_discriminant_valuations': weighted,
               'left_repeated_places': sum(x['left']['repeated_reduction'] for x in places),
               'right_repeated_places': sum(x['right']['repeated_reduction'] for x in places),
               'left_odd_discriminant_places': sum(x['left']['discriminant_valuation'] % 2 for x in places),
               'right_odd_discriminant_places': sum(x['right']['discriminant_valuation'] % 2 for x in places)}
        rows.append(row)
        save(rows, protocol_path, 'PARTIAL_RELATIVE_QUARTIC_LOCAL_SCREEN')
        print(json.dumps({'prime': p,
                          'repeated': [row['left_repeated_places'], row['right_repeated_places']],
                          'odd': [row['left_odd_discriminant_places'], row['right_odd_discriminant_places']]},
                         sort_keys=True), flush=True)
    save(rows, protocol_path, 'PASS_RELATIVE_QUARTIC_LOCAL_SCREEN')
    print(json.dumps({'status': 'PASS_RELATIVE_QUARTIC_LOCAL_SCREEN'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
