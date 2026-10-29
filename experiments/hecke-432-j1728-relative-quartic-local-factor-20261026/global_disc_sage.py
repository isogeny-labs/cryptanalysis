"""Test whether each relative quartic discriminant has an exact global square root."""
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
    protocol_path = HERE / 'global_disc_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {key: ROOT / path for key, path in protocol['input_paths'].items()}
    for key, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][key]
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    rows = []
    for side, factor in zip(('left', 'right'), octic['factors']):
        g = Lz([relative_element(v, alpha, s, K, L)
                for v in factor['coefficients_low_to_high']])
        assert g.degree() == 4 and g.is_monic()
        disc = g.discriminant()
        square = bool(disc.is_square())
        if square:
            root = disc.sqrt(extend=False)
            assert root.parent() == L and root * root == disc
            root_coefficients = [[str(c) for c in list(v)] for v in list(root)]
        else:
            root_coefficients = None
        rows.append({'side': side, 'global_square': square,
                     'square_root_coefficients': root_coefficients})
        print(json.dumps({'side': side, 'global_square': square}, sort_keys=True), flush=True)
    out = {'status': 'PASS_GLOBAL_QUARTIC_DISCRIMINANT_SQUARE_TEST',
           'rows': rows,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'global_disc_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
