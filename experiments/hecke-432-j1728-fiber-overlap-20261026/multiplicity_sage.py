"""Test branch-zero roots against factor derivatives in four frozen fields."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'failed_overlap_result': HERE / 'result.json',
    'large_prime_result': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/large_prime_result.json',
    'prime_result': ROOT / 'experiments/hecke-432-j1728-octic-factor-search-20261026/prime_result.json',
    'control_result': ROOT / 'experiments/hecke-432-j1728-octic-factor-search-20261026/control_result.json',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
    'source_helpers': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/classify_large_sage.py',
}


def specialized_factor(factor, x, F, Rz):
    return Rz([sum((F(QQ(c)) * x ** i for i, c in enumerate(vector)), F(0))
               for vector in factor['coefficients_low_to_high']])


def main():
    protocol_path = HERE / 'multiplicity_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    saved = json.loads(INPUTS['prime_result'].read_text())['rows']
    saved.append(json.loads(INPUTS['control_result'].read_text())['row'])
    saved.append(json.loads(INPUTS['large_prime_result'].read_text()))
    assert [int(r.get('prime', 0)) for r in saved] == protocol['primes']
    field = json.loads(INPUTS['factor_certificate'].read_text())
    branch = json.loads(INPUTS['branch_formula'].read_text())
    spec = importlib.util.spec_from_file_location('helpers', INPUTS['source_helpers'])
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    results = []
    for registered in saved:
        p = ZZ(registered['prime'])
        assert p.is_prime(proof=True)
        F = GF(p)
        Rz = PolynomialRing(F, 'z')
        sources = []
        for source in registered['rows']:
            x, y = (F(int(v)) for v in source['C_point'])
            root_rows = []
            for factor in field['factors']:
                degree = len(factor['coefficients_low_to_high']) - 1
                polynomial = specialized_factor(factor, x, F, Rz)
                derivative = polynomial.derivative()
                for z, multiplicity in polynomial.roots():
                    bn = helpers.chain_expression(branch['numerator_terms'], x, y, z, F)
                    bd = helpers.chain_expression(branch['denominator_terms'], x, y, z, F)
                    repeated = bool(derivative(z) == 0)
                    assert repeated == (multiplicity > 1)
                    root_rows.append({'factor_degree': degree, 'x_E': str(int(z)),
                                      'multiplicity': int(multiplicity),
                                      'derivative_zero': repeated,
                                      'branch_numerator_zero': bool(bn == 0),
                                      'branch_denominator_zero': bool(bd == 0)})
            assert len({r['x_E'] for r in root_rows}) == source['rational_x_E_roots']
            sources.append({'C_point': source['C_point'],
                            'quartic_repeated': sum(r['factor_degree'] == 4 and
                                                    r['derivative_zero'] for r in root_rows),
                            'octic_repeated': sum(r['factor_degree'] == 8 and
                                                  r['derivative_zero'] for r in root_rows),
                            'branch_zero': sum(r['branch_numerator_zero'] and
                                               r['branch_denominator_zero'] for r in root_rows),
                            'criterion_matches': all(r['derivative_zero'] ==
                                                     r['branch_numerator_zero'] ==
                                                     r['branch_denominator_zero'] for r in root_rows),
                            'roots': root_rows})
        results.append({'prime': str(p), 'sources': len(sources),
                        'quartic_repeated': sum(s['quartic_repeated'] for s in sources),
                        'octic_repeated': sum(s['octic_repeated'] for s in sources),
                        'branch_zero': sum(s['branch_zero'] for s in sources),
                        'criterion_matches': all(s['criterion_matches'] for s in sources),
                        'rows': sources})
    prediction_matches = (all(r['criterion_matches'] for r in results) and
                          results[3]['quartic_repeated'] == 1 and
                          results[3]['octic_repeated'] == 0)
    out = {'status': 'PASS_FROZEN_DERIVATIVE_BRANCH_CRITERION'
                     if prediction_matches else 'DERIVATIVE_PREDICTION_MISMATCH',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'prediction_matches': prediction_matches,
           'results': results}
    (HERE / 'multiplicity_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'summary': [{k: r[k] for k in ('prime', 'sources',
                        'quartic_repeated', 'octic_repeated', 'branch_zero',
                        'criterion_matches')} for r in results]}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
