"""Replay the saved square-class counts and predicted local splitting degrees."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
protocol = json.loads((HERE / 'protocol.json').read_text())
result = json.loads((HERE / 'result.json').read_text())
assert result['status'] == 'PASS_QUADRATIC_RESIDUE_CLASSES'
local_path = ROOT / 'experiments/hecke-432-j1728-relative-quadratic-local-20261026/result.json'
assert sha256(local_path.read_bytes()).hexdigest() == protocol['input_sha256']['quadratic_local_result']
local = json.loads(local_path.read_text())
old = {row['prime']: {tuple(place['ideal_generators']): place for place in row['places']}
       for row in local['rows']}
rows = []
for row in result['rows']:
    p = row['prime']
    assert p in protocol['primes']
    places = row['places']
    assert len(places) == len(old[p])
    summary = {}
    for side in ('left', 'right'):
        split = inert = 0
        degrees = []
        for place in places:
            prior = old[p][tuple(place['ideal_generators'])]
            f = place['residue_degree']
            assert f == prior['residue_degree']
            classification = place[side]
            square = classification['residue_square']
            assert classification['local_type'] == ('split' if square else 'inert')
            assert classification['quadratic_factor_degrees'] == ([1, 1] if square else [2])
            assert prior[f'{side}_discriminant_valuation'] % 2 == 0
            if square:
                split += 1
                degrees.extend((f, f))
            else:
                inert += 1
                degrees.append(2 * f)
        assert split == row[f'{side}_split_places']
        assert inert == row[f'{side}_inert_places']
        assert sum(degrees) == 72
        summary[side] = {'split_base_places': split, 'inert_base_places': inert,
                         'extension_prime_count': len(degrees),
                         'extension_residue_degree_multiset': sorted(degrees)}
    rows.append({'prime': p, **summary})
assert [r['prime'] for r in rows] == protocol['primes']
audit = {'status': 'PASS_QUADRATIC_SPLITTING_COUNT_REPLAY',
         'result_sha256': sha256((HERE / 'result.json').read_bytes()).hexdigest(),
         'rows': rows}
(HERE / 'audit.json').write_text(json.dumps(audit, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': audit['status'],
                  'summary': {str(row['prime']):
                              [row['left']['split_base_places'], row['left']['inert_base_places'],
                               row['left']['extension_prime_count']] for row in rows}}, sort_keys=True))
