"""Exact cubic resolvents and factorization of the two relative quartics."""
import json
from math import prod
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


def encode(value):
    return [[str(c) for c in list(vector)] for vector in list(value)]


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
    global_disc = json.loads(paths['global_discriminant'].read_text())
    replay = json.loads(paths['root_replay'].read_text())
    assert global_disc['status'] == 'PASS_GLOBAL_QUARTIC_DISCRIMINANT_SQUARE_TEST'
    assert replay['status'] == 'PASS_SERIALIZED_GLOBAL_DISCRIMINANT_ROOT_REPLAY'
    assert replay['global_disc_result_sha256'] == sha256(paths['global_discriminant'].read_bytes()).hexdigest()
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    Ly = PolynomialRing(L, 'y')
    y = Ly.gen()
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    rows = []
    for side, factor, root_row in zip(protocol['sides'], octic['factors'], global_disc['rows']):
        assert side == root_row['side']
        g = Lz([relative_element(v, alpha, s, K, L)
                for v in factor['coefficients_low_to_high']])
        assert g.degree() == 4 and g.is_monic() and g.is_irreducible()
        d, c, b, a, one = g.list()
        assert one == 1
        resolvent = y ** 3 - b * y ** 2 + (a * c - 4 * d) * y + \
            (4 * b * d - a ** 2 * d - c ** 2)
        assert resolvent.degree() == 3 and resolvent.is_monic()
        assert resolvent.discriminant() == g.discriminant()
        root = relative_element(root_row['square_root_coefficients'], alpha, s, K, L)
        assert root * root == g.discriminant()
        factorization = list(resolvent.factor())
        assert prod(h ** e for h, e in factorization) == resolvent
        degrees = sorted(int(h.degree()) for h, e in factorization for _ in range(int(e)))
        assert degrees in ([3], [1, 1, 1])
        group = 'A4' if degrees == [3] else 'V4'
        rows.append({'side': side, 'galois_group_over_L': group,
                     'cubic_factor_degrees': degrees,
                     'quartic_discriminant_square_root': root_row['square_root_coefficients'],
                     'resolvent_coefficients_low_to_high': [encode(v) for v in resolvent.list()],
                     'resolvent_factors': [{'degree': int(h.degree()), 'exponent': int(e),
                                            'coefficients_low_to_high': [encode(v) for v in h.list()]}
                                           for h, e in factorization]})
        save(rows, protocol_path, 'PARTIAL_CUBIC_RESOLVENT_GALOIS_CLASSIFICATION')
        print(json.dumps({'side': side, 'degrees': degrees, 'group': group}, sort_keys=True), flush=True)
    save(rows, protocol_path, 'PASS_CUBIC_RESOLVENT_GALOIS_CLASSIFICATION')
    print(json.dumps({'status': 'PASS_CUBIC_RESOLVENT_GALOIS_CLASSIFICATION'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
