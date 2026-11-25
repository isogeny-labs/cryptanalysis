"""Independently replay every frozen oracle key with Sage group arithmetic."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017' / 'n41_states.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'audit_protocol.json').read_text())
for name, expected in cfg['source_sha256'].items():
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    assert sha(path) == expected, name
query = json.loads((HERE / 'query_result.json').read_text())
source = json.loads(SOURCE.read_text())
assert query['status'] == 'COMPLETE_PENDING_INDEPENDENT_REPLAY'
assert query['stdout_sha256'] == sha(HERE / 'query.stdout')
assert query['stderr_sha256'] == sha(HERE / 'query.stderr')
assert not (HERE / 'query.stderr').read_bytes()
assert source['states_per_slot'] == 284

began = time.monotonic()
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def xy(point):
    return None if point == E(0) else (enc(point[0]), enc(point[1]))


states = []
for slot in source['states']:
    states.append([E(*(dec(value) for value in row['point'])) for row in slot])
target = E(*(dec(value) for value in source['target_raw_point']))
lookup_all = {}
lookup_disjoint = {}
for a, A in enumerate(states[0]):
    columns_a = set(source['states'][0][a]['columns'])
    for b, B in enumerate(states[1]):
        key = xy(A+B)
        lookup_all.setdefault(key, []).append((a, b))
        if columns_a.isdisjoint(source['states'][1][b]['columns']):
            lookup_disjoint.setdefault(key, []).append((a, b))
assert sum(map(len, lookup_all.values())) == 284**2
assert sum(map(len, lookup_disjoint.values())) == 79424

panel = (HERE / 'panel.tsv').read_text().splitlines()
cases = [line for line in (HERE / 'query.stdout').read_text().splitlines()
         if line.startswith('CASE ')]
assert len(panel) == len(cases) == 385
positive = misses = total_hits = 0
for index, (panel_line, case_line) in enumerate(zip(panel, cases)):
    raw = panel_line.split()
    found = case_line.split()
    assert len(raw) == 7 and len(found) == 10
    kind, orientation, c, a, b, kx, ky = raw
    orientation, c, a, b, kx, ky = map(int, (orientation, c, a, b, kx, ky))
    assert found[:4] == ['CASE', str(index), kind, str(orientation)]
    assert int(found[4]) == 284
    key = E(dec(kx), dec(ky))
    if kind == 'P':
        assert index == 0 and orientation == 3
        assert (c, a, b) == (233, 283, 152)
        assert key == states[0][0] + states[1][130]
        positive += 1
    else:
        assert kind == 'M' and 0 <= orientation < 3
        oriented = E(target[0]**(1 << orientation),
                     target[1]**(1 << orientation))
        assert key == oriented-states[2][c]-(states[3][a]+states[4][b])
        cols = [set(source['states'][slot][sid]['columns'])
                for slot, sid in ((2, c), (3, a), (4, b))]
        assert len(set.union(*cols)) == 6
        misses += 1
    all_matches = lookup_all.get((kx, ky), [])
    valid_matches = lookup_disjoint.get((kx, ky), [])
    assert int(found[5]) == int(found[6]) == len(all_matches)
    expected = valid_matches[0] if valid_matches else (-1, -1)
    assert tuple(map(int, found[7:9])) == expected
    total_hits += len(all_matches)
assert positive == 1 and misses == 384 and total_hits == 1
assert query['total_lines'] == ['TOTAL 385 109340 1 1']

result = {'status': 'PASS_INDEPENDENT_N41_IMPLICIT_PAIR_PANEL',
          'candidate_id': None, 'curve_id': source['curve_id'],
          'panel_cases': len(panel), 'positive_cases': positive,
          'target_derived_cases': misses,
          'direct_group_pair_sums': 284**2,
          'disjoint_group_pair_sums': 79424,
          'all_pair_hits': total_hits,
          'first_positive_state_ids': [0, 130],
          'public_raw_point': source['target_raw_point'],
          'wall_seconds': time.monotonic()-began,
          'source_sha256': sha(SOURCE),
          'query_result_sha256': sha(HERE / 'query_result.json'),
          'audit_protocol_sha256': sha(HERE / 'audit_protocol.json'),
          'auditor_sha256': sha(Path(__file__))}
assert not (HERE / 'audit_result.json').exists()
(HERE / 'audit_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({k: result[k] for k in ('status', 'panel_cases',
                                        'all_pair_hits', 'wall_seconds')},
                 sort_keys=True))
