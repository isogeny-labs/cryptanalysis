"""Combine exact local factors and discriminant parity into complete prime tables."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = load('all_square_protocol.json')
    paths = {key: ROOT / value for key, value in protocol['input_paths'].items()}
    for key, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][key]
    screen = json.loads(paths['local_screen'].read_text())
    support = json.loads(paths['relative_discriminant_support'].read_text())
    one_double = load('all_square_result.json')
    two_linear = load('double_linear_result.json')
    global_square = load('global_disc_result.json')
    assert one_double['status'] == 'PASS_ALL_SINGLE_DOUBLE_RESIDUE_CLASSES'
    assert two_linear['status'] == 'PASS_DOUBLE_LINEAR_TAYLOR_TEST'
    assert global_square['status'] == 'PASS_GLOBAL_QUARTIC_DISCRIMINANT_SQUARE_TEST'
    assert all(row['global_square'] and row['square_root_coefficients']
               for row in global_square['rows'])
    single = {(r['prime'], r['place_index'], r['side']): r for r in one_double['rows']}
    double = {(r['prime'], r['place_index'], r['side']): r for r in two_linear['rows']}
    assert len(single) == 42 and len(double) == 12
    support_rows = {r['prime']: r for r in support['rows']}
    output_rows = []
    used_single = set()
    used_double = set()
    parity_cases = []
    for row in screen['rows']:
        p = row['prime']
        sides = {}
        for side in ('left', 'right'):
            counts = Counter()
            places = []
            for i, place in enumerate(row['places']):
                f_base = place['residue_degree']
                pattern = place[side]['reduced_factor_degrees_exponents']
                assert support_rows[p]['places'][i][side + '_relative_discriminant_valuation' +
                                                   ('_from_conjugation' if side == 'right' else '')] == 0
                key = (p, i, side)
                if all(e == 1 for _, e in pattern):
                    degrees = sorted(d for d, _ in pattern)
                    source = 'SQUAREFREE_REDUCTION'
                elif pattern == [[1, 1], [1, 1], [1, 2]]:
                    assert key in single
                    used_single.add(key)
                    degrees = single[key]['relative_residue_degrees']
                    source = 'NORMALIZED_DISCRIMINANT_SQUARE_CLASS'
                elif pattern == [[1, 2], [1, 2]]:
                    assert key in double
                    used_double.add(key)
                    degrees = double[key]['relative_residue_degrees']
                    source = 'NORMALIZED_TAYLOR_QUADRATICS'
                elif pattern == [[2, 2]]:
                    # An unramified quartic over this place can have degrees [2,2] or [4].
                    # The [4] Frobenius cycle is odd, whereas the exact global
                    # discriminant square forces an even Frobenius permutation.
                    assert p == 23 and f_base == 1
                    degrees = [2, 2]
                    source = 'GLOBAL_DISCRIMINANT_SQUARE_AND_UNRAMIFIED_PARITY'
                    parity_cases.append(key)
                else:
                    raise AssertionError((key, pattern))
                assert sum(degrees) == 4
                for d in degrees:
                    counts[d * f_base] += 1
                places.append({'place_index': i, 'base_residue_degree': f_base,
                               'relative_residue_degrees': degrees, 'source': source})
            assert sum(d * n for d, n in counts.items()) == 144
            sides[side] = {'absolute_residue_degree_counts':
                           [[d, n] for d, n in sorted(counts.items())],
                           'absolute_prime_count': sum(counts.values()),
                           'base_place_count': len(places), 'places': places}
        output_rows.append({'prime': p, 'sides': sides})
    assert used_single == set(single)
    assert used_double == set(double)
    assert sorted(parity_cases) == [(23, 0, 'left'), (23, 3, 'right')]
    out = {'status': 'PASS_COMPLETE_RELATIVE_QUARTIC_SPLITTING',
           'input_sha256': protocol['input_sha256'],
           'all_square_result_sha256': sha256((HERE / 'all_square_result.json').read_bytes()).hexdigest(),
           'double_linear_result_sha256': sha256((HERE / 'double_linear_result.json').read_bytes()).hexdigest(),
           'global_disc_result_sha256': sha256((HERE / 'global_disc_result.json').read_bytes()).hexdigest(),
           'parity_case_keys': [list(key) for key in sorted(parity_cases)],
           'rows': output_rows}
    (HERE / 'final_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    for row in output_rows:
        print(json.dumps({'prime': row['prime'],
                          'left': row['sides']['left']['absolute_residue_degree_counts'],
                          'right': row['sides']['right']['absolute_residue_degree_counts']},
                         sort_keys=True))


if __name__ == '__main__':
    main()
