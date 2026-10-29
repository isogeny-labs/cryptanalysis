"""Account for fully resolved local quartics after square-class tests."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    protocol_path = HERE / 'all_square_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    screen_path = ROOT / protocol['input_paths']['local_screen']
    assert sha256(screen_path.read_bytes()).hexdigest() == protocol['input_sha256']['local_screen']
    screen = json.loads(screen_path.read_text())
    square_path = HERE / 'all_square_result.json'
    square = json.loads(square_path.read_text())
    assert square['status'] == 'PASS_ALL_SINGLE_DOUBLE_RESIDUE_CLASSES'
    assert square['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    site_keys = [(s['prime'], s['place_index'], s['side']) for s in protocol['sites']]
    row_keys = [(r['prime'], r['place_index'], r['side']) for r in square['rows']]
    assert site_keys == row_keys and len(set(site_keys)) == 42
    classified = dict(zip(row_keys, square['rows']))
    pilot = json.loads((HERE / 'square_result.json').read_text())
    key = (pilot['rational_prime'], pilot['base_place_index_in_local_screen'], 'left')
    assert classified[key]['quadratic_character'] == pilot['quadratic_character']
    output_rows = []
    for row in screen['rows']:
        p = row['prime']
        sides = {}
        for side in ('left', 'right'):
            absolute_degrees = Counter()
            unresolved_absolute_mass = 0
            unresolved_places = []
            local_rows = []
            for i, place in enumerate(row['places']):
                f_base = place['residue_degree']
                factors = place[side]['reduced_factor_degrees_exponents']
                site = (p, i, side)
                if all(e == 1 for _, e in factors):
                    degrees = sorted(d for d, _ in factors)
                    source = 'SQUAREFREE_REDUCTION'
                elif site in classified:
                    degrees = classified[site]['relative_residue_degrees']
                    assert degrees in ([1, 1, 1, 1], [1, 1, 2])
                    source = 'NORMALIZED_DISCRIMINANT_SQUARE_CLASS'
                else:
                    degrees = None
                    source = 'UNRESOLVED_REPEATED_BLOCKS'
                    unresolved_places.append(i)
                    unresolved_absolute_mass += 4 * f_base
                if degrees is not None:
                    assert sum(degrees) == 4
                    for d in degrees:
                        absolute_degrees[d * f_base] += 1
                local_rows.append({'place_index': i, 'base_residue_degree': f_base,
                                   'relative_degrees': degrees, 'source': source})
            known_mass = sum(d * count for d, count in absolute_degrees.items())
            assert known_mass + unresolved_absolute_mass == 144
            sides[side] = {'absolute_degree_counts': [[d, n] for d, n in sorted(absolute_degrees.items())],
                           'known_absolute_degree_mass': known_mass,
                           'unresolved_absolute_degree_mass': unresolved_absolute_mass,
                           'unresolved_place_indices': unresolved_places,
                           'complete': unresolved_absolute_mass == 0,
                           'places': local_rows}
        output_rows.append({'prime': p, 'sides': sides})
    out = {'status': 'PASS_AGGREGATED_LOCAL_QUARTIC_FACTORS',
           'screen_sha256': sha256(screen_path.read_bytes()).hexdigest(),
           'square_result_sha256': sha256(square_path.read_bytes()).hexdigest(),
           'rows': output_rows}
    (HERE / 'aggregate_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    for row in output_rows:
        print(json.dumps({'prime': row['prime'],
                          'left': {key: row['sides']['left'][key] for key in
                                   ('absolute_degree_counts', 'unresolved_absolute_degree_mass', 'complete')},
                          'right': {key: row['sides']['right'][key] for key in
                                    ('absolute_degree_counts', 'unresolved_absolute_degree_mass', 'complete')}},
                         sort_keys=True))


if __name__ == '__main__':
    main()
