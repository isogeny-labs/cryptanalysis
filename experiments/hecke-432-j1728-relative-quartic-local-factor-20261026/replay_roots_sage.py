"""Independently replay the serialized global discriminant-square witnesses."""
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


def main():
    protocol = json.loads((HERE / 'global_disc_protocol.json').read_text())
    paths = {key: ROOT / path for key, path in protocol['input_paths'].items()}
    for key, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][key]
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    result_path = HERE / 'global_disc_result.json'
    result = json.loads(result_path.read_text())
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    checks = []
    for row, factor in zip(result['rows'], octic['factors']):
        g = Lz([relative_element(v, alpha, s, K, L)
                for v in factor['coefficients_low_to_high']])
        root = relative_element(row['square_root_coefficients'], alpha, s, K, L)
        assert root != 0 and root * root == g.discriminant()
        checks.append({'side': row['side'], 'exact_square_replayed': True})
    assert [r['side'] for r in checks] == ['left', 'right']
    out = {'status': 'PASS_SERIALIZED_GLOBAL_DISCRIMINANT_ROOT_REPLAY',
           'global_disc_result_sha256': sha256(result_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'checks': checks}
    (HERE / 'root_replay.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
