"""Residue square classes for the unramified relative quadratic factors."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'split_certificate': ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json',
    'quadratic_local_result': ROOT / 'experiments/hecke-432-j1728-relative-quadratic-local-20261026/result.json',
}


def base_element(values, alpha, K):
    return sum((K(QQ(v)) * alpha ** i for i, v in enumerate(values)), K(0))


def relative_element(values, alpha, s, K, L):
    return sum((L(base_element(vector, alpha, K)) * s ** i
                for i, vector in enumerate(values)), L(0))


def save(rows, protocol_path, status):
    out = {'status': status,
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
    local = json.loads(INPUTS['quadratic_local_result'].read_text())
    assert local['status'] == 'PASS_LOCAL_QUADRATIC_DISCRIMINANT_PARITY'
    quartic = next(r for r in split['records'] if r['base_degree'] == 4)
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
    discs = [g.discriminant() for g in factors]
    rows = []
    for old in local['rows']:
        p = old['prime']
        assert p in protocol['primes'] and p % 2 == 1
        primes = L.primes_above(p)
        old_by_generators = {tuple(v['ideal_generators']): v for v in old['places']}
        assert len(primes) == len(old_by_generators)
        places = []
        for P in primes:
            generators = tuple(str(g) for g in P.gens())
            previous = old_by_generators[generators]
            assert int(L.ideal(p).valuation(P)) == 1
            F = P.residue_field()
            assert int(F.characteristic()) == p
            Ft = PolynomialRing(F, 'T')
            T = Ft.gen()
            classes = []
            for side, disc in enumerate(discs):
                v = previous['left_discriminant_valuation' if side == 0
                             else 'right_discriminant_valuation']
                assert v % 2 == 0
                unit = disc / L(p) ** v
                assert int(L.ideal(unit).valuation(P)) == 0
                residue = F(unit)
                assert residue != 0
                square = bool(residue.is_square())
                assert square == bool(residue ** ((F.cardinality() - 1) // 2) == F(1))
                degrees = sorted(int(h.degree()) for h, exponent in (T ** 2 - residue).factor()
                                 for _ in range(int(exponent)))
                assert degrees == ([1, 1] if square else [2])
                classes.append({'normalized_unit_residue': str(residue),
                                'residue_square': square,
                                'quadratic_factor_degrees': degrees,
                                'local_type': 'split' if square else 'inert'})
            places.append({'ideal_generators': list(generators),
                           'residue_degree': int(P.residue_class_degree()),
                           'left': classes[0], 'right': classes[1]})
        row = {'prime': p, 'places': places,
               'left_split_places': sum(v['left']['local_type'] == 'split' for v in places),
               'left_inert_places': sum(v['left']['local_type'] == 'inert' for v in places),
               'right_split_places': sum(v['right']['local_type'] == 'split' for v in places),
               'right_inert_places': sum(v['right']['local_type'] == 'inert' for v in places)}
        rows.append(row)
        save(rows, protocol_path, 'PARTIAL_QUADRATIC_RESIDUE_CLASSES')
        print(json.dumps({'prime': p, 'left_split': row['left_split_places'],
                          'right_split': row['right_split_places']}, sort_keys=True), flush=True)
    save(rows, protocol_path, 'PASS_QUADRATIC_RESIDUE_CLASSES')
    print(json.dumps({'status': 'PASS_QUADRATIC_RESIDUE_CLASSES'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
