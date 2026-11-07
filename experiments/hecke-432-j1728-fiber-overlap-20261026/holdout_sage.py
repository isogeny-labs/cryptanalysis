"""Classify two frozen quartic-norm primes and test the derivative criterion."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
    'source_helpers': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/classify_large_sage.py',
    'prime_classifier': ROOT / 'experiments/hecke-432-j1728-octic-factor-search-20261026/classify_primes_sage.py',
    'power_certificate': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/power_certificate.json',
}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def factor_at_x(factor, x, F, Rz):
    return Rz([sum((F(QQ(c)) * x ** i for i, c in enumerate(vector)), F(0))
               for vector in factor['coefficients_low_to_high']])


def main():
    protocol_path = HERE / 'holdout_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    factors = json.loads(INPUTS['factor_certificate'].read_text())['factors']
    coord = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    resolvent = json.loads(INPUTS['resolvent'].read_text())['terms']
    branch = json.loads(INPUTS['branch_formula'].read_text())
    power = json.loads(INPUTS['power_certificate'].read_text())
    helper = load('helpers', INPUTS['source_helpers'])
    classifier = load('classifier', INPUTS['prime_classifier'])
    results = []
    for raw in protocol['primes']:
        p = ZZ(raw)
        assert p.is_prime(proof=True)
        assert ZZ(power['pair_resultant_4']['root']) % p == 0
        F = GF(p)
        Rz = PolynomialRing(F, 'z')
        classified = classifier.classify(p, json.loads(INPUTS['factor_certificate'].read_text()),
                                         coord, resolvent, branch, helper)
        root_rows = []
        repeated_quartic = 0
        criterion_matches = True
        for source in classified['rows']:
            x, y = (F(int(v)) for v in source['C_point'])
            factor_roots = []
            for factor in factors:
                degree = len(factor['coefficients_low_to_high']) - 1
                polynomial = factor_at_x(factor, x, F, Rz)
                for z, multiplicity in polynomial.roots():
                    repeated = bool(polynomial.derivative()(z) == 0)
                    assert repeated == (multiplicity > 1)
                    bn = helper.chain_expression(branch['numerator_terms'], x, y, z, F)
                    bd = helper.chain_expression(branch['denominator_terms'], x, y, z, F)
                    entry = {'factor_degree': degree, 'x_E': str(int(z)),
                             'multiplicity': int(multiplicity),
                             'derivative_zero': repeated,
                             'branch_numerator_zero': bool(bn == 0),
                             'branch_denominator_zero': bool(bd == 0)}
                    factor_roots.append(entry)
                    repeated_quartic += degree == 4 and repeated
                    criterion_matches &= repeated == (bn == 0) == (bd == 0)
            assert len({row['x_E'] for row in factor_roots}) == source['rational_x_E_roots']
            root_rows.append({'C_point': source['C_point'], 'roots': factor_roots})
        results.append({'prime': str(p), 'classification': classified,
                        'factor_roots': root_rows,
                        'repeated_quartic_roots': repeated_quartic,
                        'criterion_matches': bool(criterion_matches)})
    matches = all(r['repeated_quartic_roots'] >= 1 and r['criterion_matches']
                  for r in results)
    out = {'status': 'PASS_FROZEN_QUARTIC_HOLDOUT_DERIVATIVE_CRITERION'
                     if matches else 'QUARTIC_HOLDOUT_PREDICTION_MISMATCH',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'prediction_matches': matches, 'results': results}
    (HERE / 'holdout_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'summary': [{'prime': r['prime'],
                                   'sources': r['classification']['rational_C_points'],
                                   'pairs': r['classification']['rational_CE_pairs'],
                                   'repeated_quartic_roots': r['repeated_quartic_roots'],
                                   'criterion_matches': r['criterion_matches']}
                                  for r in results]}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
