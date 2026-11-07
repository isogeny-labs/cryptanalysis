"""Factor only the left quartic and transfer patterns by exact conjugacy."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def lift_base(v, alpha, K):
    return sum((K(QQ(c)) * alpha ** i for i, c in enumerate(v)), K(0))


def lift_relative(v, alpha, s, K, L):
    return sum((L(lift_base(w, alpha, K)) * s ** i for i, w in enumerate(v)), L(0))


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
    conjugacy = json.loads(paths['conjugacy_result'].read_text())
    assert conjugacy['status'] == 'PASS_EXACT_SQRT2_CONJUGACY'
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    sigma = L.hom([-s], L)
    assert sigma(s) == -s and sigma(L(alpha)) == L(alpha)
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    left = [lift_relative(v, alpha, s, K, L)
            for v in octic['factors'][0]['coefficients_low_to_high']]
    assert len(left) == 5 and left[-1] == 1
    rows = []
    for p in protocol['rational_primes']:
        places = L.primes_above(p)
        assert sum(int(P.residue_class_degree()) for P in places) == 36
        image_indices = []
        for i, P in enumerate(places):
            image = L.ideal([sigma(v) for v in P.gens()])
            hits = [j for j, Q in enumerate(places) if Q == image]
            assert len(hits) == 1
            j = hits[0]
            image_indices.append(j)
            F = P.residue_field()
            Fz = PolynomialRing(F, 'z')
            try:
                reduced = Fz([F(c) for c in left])
                factors = reduced.factor()
                squarefree = all(e == 1 for _, e in factors)
                degrees = sorted(int(f.degree()) for f, _ in factors) if squarefree else None
                status = 'PREDICTED' if squarefree else 'REPEATED_LEFT_REDUCTION'
                factor_data = [{'degree': int(f.degree()), 'multiplicity': int(e),
                                'polynomial': str(f)} for f, e in factors]
                error = None
            except (ValueError, ZeroDivisionError, TypeError) as exc:
                degrees, status, factor_data = None, 'LEFT_REDUCTION_ERROR', None
                error = {'type': type(exc).__name__, 'message': str(exc)}
            rows.append({'prime': p, 'left_place_index': i, 'right_place_index': j,
                         'right_ideal_generators': [str(v) for v in places[j].gens()],
                         'base_residue_degree': int(P.residue_class_degree()),
                         'left_factors': factor_data, 'left_error': error,
                         'predicted_right_relative_degrees': degrees, 'status': status})
        assert sorted(image_indices) == list(range(len(places)))
        assert all(image_indices[image_indices[i]] == i for i in range(len(places)))
        save(rows, protocol_path, 'PARTIAL_SINGLE_SIDED_PREDICTIONS')
        print(json.dumps({'prime': p, 'base_places': len(places),
                          'predicted': sum(r['prime'] == p and r['status'] == 'PREDICTED'
                                           for r in rows)}, sort_keys=True), flush=True)
    save(rows, protocol_path, 'PASS_SINGLE_SIDED_PREDICTIONS')
    print(json.dumps({'status': 'PASS_SINGLE_SIDED_PREDICTIONS',
                      'right_rows': len(rows),
                      'unknown': sum(r['status'] != 'PREDICTED' for r in rows)},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
