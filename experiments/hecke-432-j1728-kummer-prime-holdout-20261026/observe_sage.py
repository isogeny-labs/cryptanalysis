"""Observe quartic reductions without reading the sealed Kummer predictions."""
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


def save(rows, seal_path, status):
    out = {'status': status, 'rows': rows,
           'observation_protocol_sha256': sha256(seal_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'observations.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    seal_path = HERE / 'observation_protocol.json'
    seal = json.loads(seal_path.read_text())
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert seal['status'] == 'FROZEN_AFTER_PREDICTION_BEFORE_QUARTIC_OBSERVATION'
    assert sha256(protocol_path.read_bytes()).hexdigest() == seal['protocol_sha256']
    assert sha256((HERE / 'predictions.json').read_bytes()).hexdigest() == seal['prediction_sha256']
    paths = {name: ROOT / rel for name, rel in protocol['input_paths'].items()}
    for name in ('factor_certificate', 'split_certificate'):
        assert sha256(paths[name].read_bytes()).hexdigest() == seal[name + '_sha256']
    cert = json.loads(paths['factor_certificate'].read_text())
    split = json.loads(paths['split_certificate'].read_text())
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    factors = octic['factors']
    assert len(factors) == 2
    quartics = {side: [relative_element(v, alpha, s, K, L)
                       for v in factor['coefficients_low_to_high']]
                for side, factor in zip(protocol['target_sides'], factors)}
    assert all(len(v) == 5 and v[-1] == 1 for v in quartics.values())
    rows = []
    for p in seal['rational_primes']:
        places = L.primes_above(p)
        assert sum(int(P.residue_class_degree()) for P in places) == 36
        for i, P in enumerate(places):
            assert int(P.absolute_ramification_index()) == 1
            F = P.residue_field()
            Fz = PolynomialRing(F, 'z')
            for side in seal['target_sides']:
                identity = {'prime': p, 'base_place_index': i, 'side': side,
                            'ideal_generators': [str(x) for x in P.gens()],
                            'base_residue_degree': int(P.residue_class_degree())}
                try:
                    reduced = Fz([F(value) for value in quartics[side]])
                    factorization = reduced.factor()
                    factors_out = [{'degree': int(f.degree()), 'multiplicity': int(e),
                                    'polynomial': str(f)} for f, e in factorization]
                    squarefree = all(e == 1 for _, e in factorization)
                    degrees = sorted(int(f.degree()) for f, e in factorization) if squarefree else None
                    row = {**identity, 'status': 'SQUAREFREE' if squarefree else 'REPEATED_REDUCTION',
                           'reduced_polynomial': str(reduced), 'factors': factors_out,
                           'observed_relative_degrees': degrees}
                except (ValueError, ZeroDivisionError, TypeError) as exc:
                    row = {**identity, 'status': 'REDUCTION_ERROR',
                           'error_type': type(exc).__name__, 'error': str(exc),
                           'observed_relative_degrees': None}
                rows.append(row)
        save(rows, seal_path, 'PARTIAL_QUARTIC_OBSERVATION')
        print(json.dumps({'prime': p, 'rows': len(rows),
                          'squarefree': sum(r['status'] == 'SQUAREFREE' for r in rows)},
                         sort_keys=True), flush=True)
    save(rows, seal_path, 'PASS_QUARTIC_OBSERVATION')
    print(json.dumps({'status': 'PASS_QUARTIC_OBSERVATION', 'rows': len(rows)},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
