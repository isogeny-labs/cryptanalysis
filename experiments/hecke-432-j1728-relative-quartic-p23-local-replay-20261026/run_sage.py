"""Replay p=23 doubled-quadratic splitting over the residue extension."""
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
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {name: ROOT / rel for name, rel in protocol['input_paths'].items()}
    for name, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    screen = json.loads(paths['local_screen'].read_text())
    support = json.loads(paths['relative_discriminant_support'].read_text())
    p = protocol['rational_prime']
    assert p == 23
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    factors = {'left': Lz([relative_element(v, alpha, s, K, L)
                            for v in octic['factors'][0]['coefficients_low_to_high']]),
               'right': Lz([relative_element(v, alpha, s, K, L)
                             for v in octic['factors'][1]['coefficients_low_to_high']])}
    primes = L.primes_above(p)
    screen_row = next(r for r in screen['rows'] if r['prime'] == p)
    support_row = next(r for r in support['rows'] if r['prime'] == p)
    rows = []
    for site in protocol['sites']:
        side, i = site['side'], site['place_index']
        P = primes[i]
        saved = screen_row['places'][i]
        assert [str(x) for x in P.gens()] == saved['ideal_generators']
        assert saved['residue_degree'] == 1
        assert int(P.absolute_ramification_index()) == 1
        assert saved[side]['reduced_factor_degrees_exponents'] == [[2, 2]]
        assert saved[side]['discriminant_valuation'] == 4
        assert support_row['places'][i][side + '_relative_discriminant_valuation' +
                                       ('_from_conjugation' if side == 'right' else '')] == 0
        F = P.residue_field()
        assert int(F.cardinality()) == p
        g = factors[side]
        Fz = PolynomialRing(F, 'z')
        reduced = Fz([F(c) for c in g.list()])
        fac = list(reduced.factor())
        assert len(fac) == 1 and fac[0][0].degree() == 2 and int(fac[0][1]) == 2
        h = fac[0][0]
        E = F.extension(h, 'u')
        u = E.gen()
        assert int(E.cardinality()) == p * p and h(u) == 0
        H = Lz([L(F.lift(c)) for c in h.list()]).monic()
        assert H.degree() == 2 and H.is_monic()
        assert Fz([F(c) for c in H.list()]) == h
        remnants = [g % H, g.derivative() % H,
                     g.derivative().derivative() % H]

        def scaled(poly, power):
            divisor = p ** power
            values = []
            for coeff in poly.list():
                if coeff:
                    assert int(L.ideal(coeff).valuation(P)) >= power
                values.append(E(F(coeff / divisor)))
            return sum((values[j] * u ** j for j in range(len(values))), E(0))

        C = scaled(remnants[0], 2)
        B = scaled(remnants[1], 1)
        A = scaled(remnants[2], 0) / 2
        assert A != 0
        delta = B * B - 4 * A * C
        assert delta != 0
        chi = delta ** ((int(E.cardinality()) - 1) // 2)
        assert chi in (E(1), E(-1))
        square = chi == E(1)
        rows.append({'side': side, 'place_index': i,
                     'residue_quadratic': [str(c) for c in h.list()],
                     'lifted_quadratic': [str(c) for c in H.list()],
                     'taylor_coefficients_over_residue_extension': [str(A), str(B), str(C)],
                     'normalized_discriminant': str(delta),
                     'quadratic_character': 1 if square else -1,
                     'relative_residue_degrees': [2, 2] if square else [4]})
        save(rows, protocol_path, 'PARTIAL_P23_QUADRATIC_CLUSTER_REPLAY')
    save(rows, protocol_path, 'PASS_P23_QUADRATIC_CLUSTER_REPLAY')
    print(json.dumps({'status': 'PASS_P23_QUADRATIC_CLUSTER_REPLAY',
                      'rows': len(rows),
                      'relative_degrees': [r['relative_residue_degrees'] for r in rows]},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
