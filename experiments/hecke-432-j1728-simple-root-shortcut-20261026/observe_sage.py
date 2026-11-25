"""Observe right quartic residue factors without reading prediction contents."""
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


def save(rows, seal_path, status):
    out = {'status': status, 'rows': rows,
           'observation_protocol_sha256': sha256(seal_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'observations.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    seal_path = HERE / 'observation_protocol.json'
    seal = json.loads(seal_path.read_text())
    assert seal['status'] == 'FROZEN_AFTER_SHORTCUT_PREDICTIONS_BEFORE_RIGHT_OBSERVATION'
    assert sha256((HERE / 'protocol.json').read_bytes()).hexdigest() == seal['protocol_sha256']
    assert sha256((HERE / 'combined_predictions.json').read_bytes()).hexdigest() == \
        seal['combined_predictions_sha256']
    protocol = json.loads((HERE / 'protocol.json').read_text())
    cert_path = ROOT / protocol['input_paths']['factor_certificate']
    split_path = ROOT / protocol['input_paths']['split_certificate']
    assert sha256(cert_path.read_bytes()).hexdigest() == seal['factor_certificate_sha256']
    assert sha256(split_path.read_bytes()).hexdigest() == seal['split_certificate_sha256']
    cert = json.loads(cert_path.read_text())
    split = json.loads(split_path.read_text())
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    quartic = next(r for r in split['records'] if r['base_degree'] == 8)['factors'][1]
    right = [relative_element(v, alpha, s, K, L)
             for v in quartic['coefficients_low_to_high']]
    assert len(right) == 5 and right[-1] == 1
    rows = []
    for p in seal['holdout_primes']:
        places = L.primes_above(p)
        assert sum(int(P.residue_class_degree()) for P in places) == 36
        for j, P in enumerate(places):
            F = P.residue_field()
            Fz = PolynomialRing(F, 'z')
            try:
                reduced = Fz([F(c) for c in right])
                factors = reduced.factor()
                squarefree = all(e == 1 for _, e in factors)
                degrees = sorted(int(h.degree()) for h, _ in factors) if squarefree else None
                status = 'SQUAREFREE' if squarefree else 'REPEATED_REDUCTION'
                factor_data = [{'degree': int(h.degree()), 'multiplicity': int(e),
                                'polynomial': str(h)} for h, e in factors]
                error = None
            except (ValueError, ZeroDivisionError, TypeError) as exc:
                degrees, status, factor_data = None, 'REDUCTION_ERROR', None
                error = {'type': type(exc).__name__, 'message': str(exc)}
            rows.append({'prime': p, 'right_place_index': j,
                         'right_ideal_generators': [str(v) for v in P.gens()],
                         'base_residue_degree': int(P.residue_class_degree()),
                         'right_factors': factor_data, 'error': error,
                         'observed_right_relative_degrees': degrees, 'status': status})
        save(rows, seal_path, 'PARTIAL_RIGHT_OBSERVATIONS')
        print(json.dumps({'prime': p, 'base_places': len(places),
                          'squarefree': sum(r['prime'] == p and r['status'] == 'SQUAREFREE'
                                            for r in rows)}, sort_keys=True), flush=True)
    save(rows, seal_path, 'PASS_RIGHT_OBSERVATIONS')
    print(json.dumps({'status': 'PASS_RIGHT_OBSERVATIONS', 'rows': len(rows),
                      'unresolved': sum(r['status'] != 'SQUAREFREE' for r in rows)},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
