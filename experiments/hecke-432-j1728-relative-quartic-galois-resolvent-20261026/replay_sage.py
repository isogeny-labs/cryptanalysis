"""Independently replay serialized resolvent and Kummer witnesses."""
import json
from math import prod
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def lift_vector(values, alpha, K):
    return sum((K(QQ(value)) * alpha ** i for i, value in enumerate(values)), K(0))


def lift_relative(values, alpha, s, K, L):
    return sum((L(lift_vector(vector, alpha, K)) * s ** i
                for i, vector in enumerate(values)), L(0))


def main():
    protocol = json.loads((HERE / 'kummer_protocol.json').read_text())
    paths = {name: ROOT / rel for name, rel in protocol['input_paths'].items()}
    for name, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    result_path = HERE / 'kummer_result.json'
    result = json.loads(result_path.read_text())
    assert result['status'] == 'PASS_KUMMER_SQUARE_CLASS_TEST'
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    Ly = PolynomialRing(L, 'y')
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    checks = []
    for row, factor in zip(result['rows'], octic['factors']):
        g = Lz([lift_relative(v, alpha, s, K, L)
                for v in factor['coefficients_low_to_high']])
        a, b = g[3], g[2]
        roots = [lift_relative(v, alpha, s, K, L) for v in row['resolvent_roots']]
        radicands = [lift_relative(v, alpha, s, K, L) for v in row['radicands']]
        assert len(set(roots)) == 3
        resolvent = Ly([lift_relative(v, alpha, s, K, L)
                        for v in json.loads(paths['resolvent_result'].read_text())['rows'][
                            0 if row['side'] == 'left' else 1]['resolvent_coefficients_low_to_high']])
        assert all(resolvent(y) == 0 for y in roots)
        assert radicands == [a * a - 4 * b + 4 * y for y in roots]
        assert all(value != 0 for value in radicands)
        witness = lift_relative(row['triple_square_root_coefficients'], alpha, s, K, L)
        assert witness != 0 and witness * witness == prod(radicands)
        checks.append({'side': row['side'], 'three_roots_replayed': True,
                       'three_radicands_replayed': True, 'triple_square_replayed': True})
    assert [r['side'] for r in checks] == ['left', 'right']
    out = {'status': 'PASS_SERIALIZED_KUMMER_WITNESS_REPLAY',
           'kummer_result_sha256': sha256(result_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'checks': checks}
    (HERE / 'replay.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
