"""Predict right splitting from left residue factors and the V4 simple-root rule."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def base_element(v, alpha, K):
    return sum((K(QQ(c)) * alpha ** i for i, c in enumerate(v)), K(0))


def relative_element(v, alpha, s, K, L):
    return sum((L(base_element(w, alpha, K)) * s ** i for i, w in enumerate(v)), L(0))


def save(rows, protocol_path, status):
    out = {'status': status, 'rows': rows,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'predictions.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {name: ROOT / rel for name, rel in protocol['input_paths'].items()}
    for name, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    galois = json.loads(paths['galois_result'].read_text())
    support = json.loads(paths['relative_discriminant_support'].read_text())
    assert {r['side']: r['galois_group_over_L'] for r in galois['rows']} == \
        {'left': 'V4', 'right': 'V4'}
    assert support['fixed_integer_in_left_discriminant_ideal'] == 96
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    sigma = L.hom([-s], L)
    assert sigma(s) == -s and sigma(L(alpha)) == L(alpha)
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    left = [relative_element(v, alpha, s, K, L)
            for v in octic['factors'][0]['coefficients_low_to_high']]
    assert len(left) == 5 and left[-1] == 1
    rows = []
    for p in protocol['holdout_primes']:
        assert 96 % p != 0
        places = L.primes_above(p)
        assert sum(int(P.residue_class_degree()) for P in places) == 36
        permutation = []
        for i, P in enumerate(places):
            assert int(P.absolute_ramification_index()) == 1
            image = L.ideal([sigma(v) for v in P.gens()])
            hits = [j for j, Q in enumerate(places) if Q == image]
            assert len(hits) == 1
            j = hits[0]
            permutation.append(j)
            F = P.residue_field()
            Fz = PolynomialRing(F, 'z')
            try:
                reduced = Fz([F(c) for c in left])
                factors = reduced.factor()
                factor_data = [{'degree': int(h.degree()), 'multiplicity': int(e),
                                'polynomial': str(h)} for h, e in factors]
                squarefree = all(e == 1 for _, e in factors)
                simple_linear = any(h.degree() == 1 and e == 1 for h, e in factors)
                if squarefree:
                    degrees = sorted(int(h.degree()) for h, _ in factors)
                    status = 'PREDICTED_SQUAREFREE'
                elif simple_linear:
                    degrees = [1, 1, 1, 1]
                    status = 'PREDICTED_SIMPLE_ROOT_V4'
                else:
                    degrees, status = None, 'UNRESOLVED_REDUCTION'
                error = None
            except (ValueError, ZeroDivisionError, TypeError) as exc:
                degrees, status, factor_data, simple_linear = \
                    None, 'REDUCTION_ERROR', None, None
                error = {'type': type(exc).__name__, 'message': str(exc)}
            rows.append({'prime': p, 'left_place_index': i, 'right_place_index': j,
                         'right_ideal_generators': [str(v) for v in places[j].gens()],
                         'base_residue_degree': int(P.residue_class_degree()),
                         'left_factors': factor_data, 'left_simple_linear': simple_linear,
                         'predicted_right_relative_degrees': degrees,
                         'error': error, 'status': status})
        assert sorted(permutation) == list(range(len(places)))
        assert all(permutation[permutation[i]] == i for i in range(len(places)))
        save(rows, protocol_path, 'PARTIAL_SHORTCUT_PREDICTIONS')
        print(json.dumps({'prime': p, 'base_places': len(places),
                          'simple_root_shortcut': sum(r['prime'] == p and
                              r['status'] == 'PREDICTED_SIMPLE_ROOT_V4' for r in rows),
                          'unresolved': sum(r['prime'] == p and r['predicted_right_relative_degrees']
                                            is None for r in rows)}, sort_keys=True), flush=True)
    save(rows, protocol_path, 'PASS_SHORTCUT_PREDICTIONS')
    print(json.dumps({'status': 'PASS_SHORTCUT_PREDICTIONS', 'rows': len(rows),
                      'simple_root_shortcut': sum(r['status'] == 'PREDICTED_SIMPLE_ROOT_V4'
                                                  for r in rows),
                      'unresolved': sum(r['predicted_right_relative_degrees'] is None
                                        for r in rows)}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
