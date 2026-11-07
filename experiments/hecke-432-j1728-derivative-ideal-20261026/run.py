"""Check cubic/quadratic common factors at every saved resolvent root."""
import json
import runpy
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'multiplicity_result': ROOT / 'experiments/hecke-432-j1728-fiber-overlap-20261026/multiplicity_result.json',
    'multiplicity_audit': ROOT / 'experiments/hecke-432-j1728-fiber-overlap-20261026/audit_result.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
    'relative_b_resolvent': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/relative_b_resolvent.json',
    'fast_gate_source': ROOT / 'experiments/hecke-432-j1728-fast-local-root-gate-20261026/run.py',
}


def polynomial_at_source(terms, x, y, p):
    degree = max(t['x_B_exponent'] for t in terms)
    coefficients = [0] * (degree + 1)
    for t in terms:
        k = t['x_B_exponent']
        coefficients[k] = (coefficients[k] + int(t['integer_coefficient'])
                           * pow(x, t['x_C_exponent'], p)
                           * pow(y, t['y_C_exponent'], p)) % p
    return coefficients


def main():
    path = HERE / 'protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    branch = json.loads(INPUTS['branch_formula'].read_text())
    relative = json.loads(INPUTS['relative_b_resolvent'].read_text())
    assert branch['source_sha256'] == sha256(INPUTS['relative_b_resolvent'].read_bytes()).hexdigest()
    assert int(branch['primitive_content_removed']) == 1
    saved = json.loads(INPUTS['multiplicity_result'].read_text())
    gate = runpy.run_path(str(INPUTS['fast_gate_source']))
    results = []
    all_match = True
    for field in saved['results']:
        p = int(field['prime'])
        arith = gate['PolynomialArithmetic'](p)
        rows = []
        histogram = Counter()
        for source in field['rows']:
            x, y = map(int, source['C_point'])
            pb = polynomial_at_source(relative['terms'], x, y, p)
            for root in source['roots']:
                z = int(root['x_E'])
                F = [(-64) % p, 0, (-z) % p, 1]
                R = arith.remainder(pb, F)
                assert len(R) <= 3
                a = R[2] if len(R) > 2 else 0
                b = R[1] if len(R) > 1 else 0
                c = R[0] if R else 0
                D = (b * (a * z + b) - a * c) % p
                N = (64 * a * a - c * (a * z + b)) % p
                assert (N == 0) == root['branch_numerator_zero']
                assert (D == 0) == root['branch_denominator_zero']
                gcd = arith.gcd(F, R)
                degree = len(gcd) - 1
                derivative = [(i * gcd[i]) % p for i in range(1, len(gcd))]
                squarefree = len(arith.gcd(gcd, derivative)) == 1
                expected_degree = 2 if root['derivative_zero'] else 1
                match = degree == expected_degree
                all_match &= match
                histogram[degree] += 1
                rows.append({'C_point': source['C_point'], 'x_E': root['x_E'],
                             'factor_degree': root['factor_degree'],
                             'repeated_factor_root': root['derivative_zero'],
                             'branch_values_zero': bool(N == 0 and D == 0),
                             'common_B_gcd_degree': degree,
                             'common_B_gcd_squarefree': squarefree,
                             'gcd_coefficients_low_to_high': [str(v) for v in gcd],
                             'prediction_matches': match})
        results.append({'prime': str(p), 'root_count': len(rows),
                        'gcd_degree_histogram': {str(k): v for k, v in sorted(histogram.items())},
                        'polynomial_multiplications': arith.counts['polynomial_multiplications'],
                        'rows': rows})
    out = {'status': 'PASS_FROZEN_CUBIC_QUADRATIC_GCD_CRITERION' if all_match
                     else 'CUBIC_QUADRATIC_GCD_PREDICTION_MISMATCH',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'prediction_matches': bool(all_match), 'results': results}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'summary': [{k: r[k] for k in ('prime', 'root_count',
                                  'gcd_degree_histogram')} for r in results]},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
