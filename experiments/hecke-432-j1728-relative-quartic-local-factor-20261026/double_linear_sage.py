"""Resolve doubled linear residue clusters by normalized Taylor quadratics."""
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
    (HERE / 'double_linear_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    protocol_path = HERE / 'double_linear_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {key: ROOT / path for key, path in protocol['input_paths'].items()}
    for key, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][key]
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    screen = json.loads(paths['local_screen'].read_text())
    support = json.loads(paths['relative_discriminant_support'].read_text())
    assert len(protocol['sites']) == protocol['site_count'] == 12
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    Lz = PolynomialRing(L, 'z')
    factors = {'left': Lz([relative_element(v, alpha, s, K, L)
                            for v in octic['factors'][0]['coefficients_low_to_high']]),
               'right': Lz([relative_element(v, alpha, s, K, L)
                             for v in octic['factors'][1]['coefficients_low_to_high']])}
    screen_rows = {r['prime']: r for r in screen['rows']}
    support_rows = {r['prime']: r for r in support['rows']}
    places = {p: L.primes_above(p) for p in sorted(screen_rows)}
    rows = []
    for site in protocol['sites']:
        p, i, side = site['prime'], site['place_index'], site['side']
        P = places[p][i]
        source = screen_rows[p]['places'][i]
        assert [str(x) for x in P.gens()] == source['ideal_generators']
        assert source[side]['reduced_factor_degrees_exponents'] == [[1, 2], [1, 2]]
        assert source[side]['discriminant_valuation'] == 4
        assert support_rows[p]['places'][i][side + '_relative_discriminant_valuation' +
                                           ('_from_conjugation' if side == 'right' else '')] == 0
        g = factors[side]
        F = P.residue_field()
        Fz = PolynomialRing(F, 'z')
        reduced = Fz([F(c) for c in g.list()])
        residue_factors = list(reduced.factor())
        assert len(residue_factors) == 2 and all(h.degree() == 1 and e == 2
                                                 for h, e in residue_factors)
        q = int(F.cardinality())
        assert q == p ** int(P.residue_class_degree())
        clusters = []
        for h, _ in residue_factors:
            root_residue = -h[0] / h[1]
            root_lift = L(F.lift(root_residue))
            assert F(root_lift) == root_residue
            g0 = g(root_lift)
            g1 = g.derivative()(root_lift)
            g2 = g.derivative().derivative()(root_lift)
            assert int(L.ideal(g0).valuation(P)) >= 2
            assert int(L.ideal(g1).valuation(P)) >= 1
            A = F(g2 / 2)
            B = F(g1 / p)
            C = F(g0 / (p * p))
            assert A != 0
            delta = B * B - 4 * A * C
            assert delta != 0
            chi = delta ** ((q - 1) // 2)
            assert chi in (F(1), F(-1))
            square = chi == F(1)
            clusters.append({'residue_root': str(root_residue),
                             'lift': str(root_lift),
                             'normalized_taylor_coefficients': [str(A), str(B), str(C)],
                             'normalized_discriminant': str(delta),
                             'quadratic_character': 1 if square else -1,
                             'relative_residue_degrees': [1, 1] if square else [2]})
        assert len(clusters) == 2
        relative_degrees = sorted(d for cluster in clusters
                                  for d in cluster['relative_residue_degrees'])
        assert relative_degrees in ([1, 1, 1, 1], [2, 2])
        rows.append({'prime': p, 'place_index': i, 'side': side,
                     'base_residue_degree': int(P.residue_class_degree()),
                     'clusters': clusters, 'relative_residue_degrees': relative_degrees})
        save(rows, protocol_path, 'PARTIAL_DOUBLE_LINEAR_TAYLOR_TEST')
    save(rows, protocol_path, 'PASS_DOUBLE_LINEAR_TAYLOR_TEST')
    print(json.dumps({'status': 'PASS_DOUBLE_LINEAR_TAYLOR_TEST', 'sites': len(rows),
                      'fully_split': sum(r['relative_residue_degrees'] == [1, 1, 1, 1]
                                         for r in rows),
                      'double_inert': sum(r['relative_residue_degrees'] == [2, 2]
                                          for r in rows)}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
