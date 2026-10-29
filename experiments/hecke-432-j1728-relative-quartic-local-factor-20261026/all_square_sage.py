"""Classify all quartic places with one repeated linear residue factor."""
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


def save(rows, protocol_path, status):
    out = {'status': status, 'rows': rows,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'all_square_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    protocol_path = HERE / 'all_square_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {key: ROOT / path for key, path in protocol['input_paths'].items()}
    for key, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][key]
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    screen = json.loads(paths['local_screen'].read_text())
    support = json.loads(paths['relative_discriminant_support'].read_text())
    assert len(protocol['sites']) == protocol['site_count'] == 42
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    Lz = PolynomialRing(L, 'z')
    factors = [Lz([relative_element(v, alpha, s, K, L)
                   for v in factor['coefficients_low_to_high']])
               for factor in octic['factors']]
    assert len(factors) == 2 and all(g.degree() == 4 and g.is_monic() for g in factors)
    discriminants = {'left': factors[0].discriminant(),
                     'right': factors[1].discriminant()}
    screen_rows = {r['prime']: r for r in screen['rows']}
    support_rows = {r['prime']: r for r in support['rows']}
    places = {p: L.primes_above(p) for p in sorted(screen_rows)}
    rows = []
    for site in protocol['sites']:
        p, i, side = site['prime'], site['place_index'], site['side']
        P = places[p][i]
        source = screen_rows[p]['places'][i]
        assert [str(x) for x in P.gens()] == source['ideal_generators']
        assert source[side]['reduced_factor_degrees_exponents'] == [[1, 1], [1, 1], [1, 2]]
        assert source[side]['discriminant_valuation'] == 2
        assert support_rows[p]['places'][i][side + '_relative_discriminant_valuation' +
                                           ('_from_conjugation' if side == 'right' else '')] == 0
        disc = discriminants[side]
        assert int(L.ideal(disc).valuation(P)) == 2
        F = P.residue_field()
        u = F(disc / (p * p))
        assert u != 0
        q = int(F.cardinality())
        assert q == p ** int(P.residue_class_degree())
        chi = u ** ((q - 1) // 2)
        assert chi in (F(1), F(-1))
        square = chi == F(1)
        rows.append({'prime': p, 'place_index': i, 'side': side,
                     'base_residue_degree': int(P.residue_class_degree()),
                     'normalized_discriminant_residue': str(u),
                     'residue_field_order': q,
                     'quadratic_character': 1 if square else -1,
                     'relative_residue_degrees': [1, 1, 1, 1] if square else [1, 1, 2]})
        save(rows, protocol_path, 'PARTIAL_SINGLE_DOUBLE_RESIDUE_CLASSES')
    save(rows, protocol_path, 'PASS_ALL_SINGLE_DOUBLE_RESIDUE_CLASSES')
    print(json.dumps({'status': 'PASS_ALL_SINGLE_DOUBLE_RESIDUE_CLASSES',
                      'sites': len(rows),
                      'split': sum(r['quadratic_character'] == 1 for r in rows),
                      'inert': sum(r['quadratic_character'] == -1 for r in rows)},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
