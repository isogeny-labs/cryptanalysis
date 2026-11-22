"""Independent local-gcd and modular-equation audit of both octic factors."""
import json
import runpy
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'prime_result': HERE / 'prime_result.json',
    'fast_gate_source': ROOT / 'experiments/hecke-432-j1728-fast-local-root-gate-20261026/run.py',
    'audit_helpers': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/audit_large.py',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
}


def main():
    protocol_path = HERE / 'audit_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    sage_result = json.loads(INPUTS['prime_result'].read_text())
    gate = runpy.run_path(str(INPUTS['fast_gate_source']))
    helper = runpy.run_path(str(INPUTS['audit_helpers']))
    field = json.loads(INPUTS['factor_certificate'].read_text())
    coord = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    resolvent = json.loads(INPUTS['resolvent'].read_text())['terms']
    branch = json.loads(INPUTS['branch_formula'].read_text())
    results = []
    for row in sage_result['rows']:
        p = int(row['prime'])
        field_roots, sources, undefined = gate['source_points'](p, field, coord)
        expected = sorted([int(v) for v in item['C_point']] for item in row['rows'])
        assert sources == expected and not undefined
        total_pairs = 0
        poly_mults = 0
        factor_counter = Counter()
        branch_counter = Counter()
        for item in row['rows']:
            x, y = map(int, item['C_point'])
            assert (y * y + y - x ** 3 + 7) % p == 0
            num = helper['rational_terms'](coord['numerator'], x, y, p)
            den = helper['rational_terms'](coord['denominator'], x, y, p)
            assert den and (num + 1728 * den) % p == 0
            fiber = gate['fiber_gate'](p, x, y, resolvent)
            assert fiber['rational_x_E_roots'] == item['rational_x_E_roots']
            assert fiber['rational_CE_pairs'] == len(item['pairs'])
            total_pairs += fiber['rational_CE_pairs']
            poly_mults += fiber['arithmetic_counts']['polynomial_multiplications']
            assert len({tuple(pair['E_point']) for pair in item['pairs']}) == len(item['pairs'])
            for pair in item['pairs']:
                z, ye = map(int, pair['E_point'])
                assert (ye * ye - z ** 3 - 432) % p == 0
                assert helper['integer_terms'](resolvent, x, y, z, p) == 0
                bn = helper['integer_terms'](branch['numerator_terms'], x, y, z, p)
                bd = helper['integer_terms'](branch['denominator_terms'], x, y, z, p)
                assert (bn == 0) == pair['branch_numerator_zero']
                assert (bd == 0) == pair['branch_denominator_zero']
                factor_degrees = [len(factor['coefficients_low_to_high']) - 1
                                  for factor in field['factors']
                                  if helper['base_factor_value'](factor, x, z, p) == 0]
                assert factor_degrees == pair['base_factor_degrees']
                factor_counter[','.join(map(str, factor_degrees))] += 1
                branch_counter[f'{int(bn == 0)}{int(bd == 0)}'] += 1
        assert total_pairs == row['rational_CE_pairs']
        assert branch_counter['11'] == row['zero_branch_pairs']
        results.append({'prime': str(p), 'field_poly_rational_roots': len(field_roots),
                        'source_points': len(sources), 'rational_CE_pairs': total_pairs,
                        'polynomial_multiplications': poly_mults,
                        'base_factor_degrees': dict(factor_counter),
                        'branch_zero_pattern': dict(branch_counter)})
    out = {'status': 'PASS_INDEPENDENT_TWO_PRIME_LOCAL_GCD_AND_EQUATION_AUDIT',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': results}
    (HERE / 'audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
