"""Replay resolvent roots and test the three Kummer square classes."""
import json
from itertools import combinations
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
    (HERE / 'kummer_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    protocol_path = HERE / 'kummer_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {name: ROOT / rel for name, rel in protocol['input_paths'].items()}
    for name, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    result = json.loads(paths['resolvent_result'].read_text())
    assert result['status'] == 'PASS_CUBIC_RESOLVENT_GALOIS_CLASSIFICATION'
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    Ly = PolynomialRing(L, 'y')
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    rows = []
    for row, factor in zip(result['rows'], octic['factors']):
        g = Lz([relative_element(v, alpha, s, K, L)
                for v in factor['coefficients_low_to_high']])
        resolvent = Ly([relative_element(v, alpha, s, K, L)
                        for v in row['resolvent_coefficients_low_to_high']])
        factors = [Ly([relative_element(v, alpha, s, K, L)
                       for v in item['coefficients_low_to_high']])
                   for item in row['resolvent_factors']]
        assert len(factors) == 3 and all(h.degree() == 1 and h.is_monic() for h in factors)
        assert prod(factors) == resolvent
        roots = [-h[0] for h in factors]
        assert len(set(roots)) == 3 and all(resolvent(y) == 0 for y in roots)
        a, b = g[3], g[2]
        radicands = [a * a - 4 * b + 4 * y for y in roots]
        assert all(value != 0 for value in radicands)
        singles = [bool(value.is_square()) for value in radicands]
        pairs = [{'indices': [i, j], 'square': bool((radicands[i] * radicands[j]).is_square())}
                 for i, j in combinations(range(3), 2)]
        triple = prod(radicands)
        triple_square = bool(triple.is_square())
        if triple_square:
            triple_root = triple.sqrt(extend=False)
            assert triple_root.parent() == L and triple_root * triple_root == triple
            triple_root_coefficients = encode(triple_root)
        else:
            triple_root_coefficients = None
        rank_two = not any(singles) and not any(item['square'] for item in pairs) and triple_square
        rows.append({'side': row['side'], 'distinct_resolvent_roots_replayed': True,
                     'resolvent_roots': [encode(value) for value in roots],
                     'radicands': [encode(value) for value in radicands],
                     'individual_square_flags': singles,
                     'pair_square_flags': pairs,
                     'triple_square': triple_square,
                     'triple_square_root_coefficients': triple_root_coefficients,
                     'kummer_rank_two': rank_two})
        save(rows, protocol_path, 'PARTIAL_KUMMER_SQUARE_CLASS_TEST')
        print(json.dumps({'side': row['side'], 'individual_square': singles,
                          'pair_square': [item['square'] for item in pairs],
                          'triple_square': triple_square,
                          'rank_two': rank_two}, sort_keys=True), flush=True)
    save(rows, protocol_path, 'PASS_KUMMER_SQUARE_CLASS_TEST')
    print(json.dumps({'status': 'PASS_KUMMER_SQUARE_CLASS_TEST'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
