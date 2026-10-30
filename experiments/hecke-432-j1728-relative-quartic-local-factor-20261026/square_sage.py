"""Classify one repeated quadratic block by its normalized discriminant."""
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
    protocol_path = HERE / 'square_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {key: ROOT / path for key, path in protocol['input_paths'].items()}
    for key, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][key]
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    screen = json.loads(paths['local_screen'].read_text())
    support = json.loads(paths['relative_discriminant_support'].read_text())
    p = protocol['rational_prime']
    i = protocol['base_place_index_in_local_screen']
    saved = next(r for r in screen['rows'] if r['prime'] == p)['places'][i]
    assert saved['left']['reduced_factor_degrees_exponents'] == protocol['expected_reduction']
    assert saved['left']['discriminant_valuation'] == 2
    assert next(r for r in support['rows'] if r['prime'] == p)['places'][i][
        'left_relative_discriminant_valuation'] == 0
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    Rt = PolynomialRing(K, 't')
    L = K.extension(Rt.gen() ** 2 - 2, 's')
    s = L.gen()
    P = L.primes_above(p)[i]
    assert [str(x) for x in P.gens()] == saved['ideal_generators']
    F = P.residue_field()
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    g = PolynomialRing(L, 'z')([relative_element(v, alpha, s, K, L)
                                for v in octic['factors'][0]['coefficients_low_to_high']])
    assert g.degree() == 4 and g.is_monic()
    disc = g.discriminant()
    assert int(L.ideal(disc).valuation(P)) == 2
    unit = F(disc / (p * p))
    assert unit != 0
    q = int(F.cardinality())
    assert q == p ** int(P.residue_class_degree())
    quadratic_character = unit ** ((q - 1) // 2)
    assert quadratic_character in (F(1), F(-1))
    square = quadratic_character == F(1)
    degrees = [1, 1, 1, 1] if square else [1, 1, 2]
    out = {'status': 'PASS_NORMALIZED_DISCRIMINANT_SQUARE_CLASS',
           'rational_prime': p, 'base_place_index_in_local_screen': i,
           'residue_field_order': q,
           'polynomial_discriminant_valuation': 2,
           'normalized_discriminant_residue': str(unit),
           'quadratic_character': 1 if square else -1,
           'repeated_block_splits': square,
           'relative_residue_degrees': degrees,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'square_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'relative_residue_degrees': degrees,
                      'quadratic_character': out['quadratic_character']}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
