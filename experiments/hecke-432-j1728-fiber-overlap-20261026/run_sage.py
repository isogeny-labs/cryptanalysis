"""Replay frozen quartic/octic root-overlap prediction at three primes."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'prime_result': ROOT / 'experiments/hecke-432-j1728-octic-factor-search-20261026/prime_result.json',
    'control_result': ROOT / 'experiments/hecke-432-j1728-octic-factor-search-20261026/control_result.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
    'source_helpers': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/classify_large_sage.py',
}


def specialized_factor(factor, x, F, Rz):
    return Rz([sum((F(QQ(c)) * x ** i for i, c in enumerate(vector)), F(0))
               for vector in factor['coefficients_low_to_high']])


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    field = json.loads(INPUTS['factor_certificate'].read_text())
    assert [len(f['coefficients_low_to_high']) - 1 for f in field['factors']] == [4, 8]
    saved = json.loads(INPUTS['prime_result'].read_text())['rows']
    saved.append(json.loads(INPUTS['control_result'].read_text())['row'])
    assert [int(r['prime']) for r in saved] == protocol['primes']
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
        source_rows = []
        for source in registered['rows']:
            x, y = (F(int(v)) for v in source['C_point'])
            quartic, octic = (specialized_factor(f, x, F, Rz)
                              for f in field['factors'])
            q_roots = {z for z, _ in quartic.roots()}
            o_roots = {z for z, _ in octic.roots()}
            overlap = q_roots & o_roots
            union = q_roots | o_roots
            assert len(union) == source['rational_x_E_roots']
            saved_pairs = source['pairs']
            pair_by_x = {}
            for pair in saved_pairs:
                z = F(int(pair['E_point'][0]))
                pair_by_x.setdefault(z, []).append(pair)
            roots = []
            for z in sorted(union, key=int):
                bn = helpers.chain_expression(branch['numerator_terms'], x, y, z, F)
                bd = helpers.chain_expression(branch['denominator_terms'], x, y, z, F)
                rhs = z ** 3 + 432
                lift_count = 1 if rhs == 0 else (2 if rhs.is_square() else 0)
                assert len(pair_by_x.get(z, [])) == lift_count
                roots.append({'x_E': str(int(z)), 'quartic': z in q_roots,
                              'octic': z in o_roots, 'overlap': z in overlap,
                              'E_lift_count': lift_count,
                              'branch_numerator_zero': bool(bn == 0),
                              'branch_denominator_zero': bool(bd == 0)})
            source_rows.append({'C_point': source['C_point'],
                                'quartic_roots': len(q_roots),
                                'octic_roots': len(o_roots),
                                'overlap_roots': len(overlap),
                                'union_roots': len(union),
                                'E_lifts': sum(row['E_lift_count'] for row in roots),
                                'roots': roots})
        results.append({'prime': str(p), 'sources': len(source_rows),
                        'quartic_roots': sum(r['quartic_roots'] for r in source_rows),
                        'octic_roots': sum(r['octic_roots'] for r in source_rows),
                        'overlap_roots': sum(r['overlap_roots'] for r in source_rows),
                        'E_lifts': sum(r['E_lifts'] for r in source_rows),
                        'branch_zero_roots': sum(v['branch_numerator_zero'] and
                                                 v['branch_denominator_zero']
                                                 for r in source_rows for v in r['roots']),
                        'branch_zero_iff_overlap': all(
                            v['branch_numerator_zero'] == v['overlap'] and
                            v['branch_denominator_zero'] == v['overlap']
                            for r in source_rows for v in r['roots']),
                        'rows': source_rows})
    prediction = protocol['prediction']
    matches = []
    for result in results[:2]:
        expected = prediction['exceptional']
        matches.append(result['sources'] == expected['sources'] and
                       result['quartic_roots'] == 18 * expected['quartic_roots_per_source'] and
                       result['octic_roots'] == 18 * expected['octic_roots_per_source'] and
                       result['overlap_roots'] == expected['overlap_sources'] *
                       expected['overlap_roots_per_overlap_source'] and
                       result['branch_zero_roots'] * 2 ==
                       expected['branch_zero_E_pairs_per_prime'] and
                       result['branch_zero_iff_overlap'])
    control = results[2]
    expected = prediction['control']
    matches.append(control['sources'] == expected['sources'] and
                   control['quartic_roots'] == 18 * expected['quartic_roots_per_source'] and
                   control['octic_roots'] == 0 and control['overlap_roots'] == 0 and
                   control['E_lifts'] == 0 and control['branch_zero_iff_overlap'])
    out = {'status': 'PASS_FROZEN_FACTOR_OVERLAP_PREDICTION' if all(matches)
                     else 'PREDICTION_MISMATCH',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'prediction_matches': matches, 'results': results}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'summary': [{k: r[k] for k in ('prime', 'quartic_roots',
                        'octic_roots', 'overlap_roots', 'E_lifts',
                        'branch_zero_roots', 'branch_zero_iff_overlap')}
                        for r in results]}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
