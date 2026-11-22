"""Checked-Sage 2+1+2 lookup control on a planted W9 state subset."""
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'
states_path = PRIOR / 'n41_states.json'
audit_path = PRIOR / 'orbit_audit_result.json'
fixture_path = HERE / 'fixture.json'
states = json.loads(states_path.read_text())
audit = json.loads(audit_path.read_text())
fixture = json.loads(fixture_path.read_text())
assert audit['status'] == 'PASS_INDEPENDENT_N41_W9_FIVEPAIR_PUBLIC_RELATION'
assert audit['orientation'] == fixture['orientation'] == 3
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


def state(slot, index):
    row = states['states'][slot][index]
    return {'id': index, 'point': E(*map(dec, row['point'])),
            'columns': frozenset(row['columns'])}


start = time.monotonic_ns()
lists = []
for slot, planted in enumerate(audit['state_ids']):
    ids = [planted] + [index for index in range(284) if index != planted][:7]
    lists.append([state(slot, index) for index in ids])
assert all(len(row) == 8 for row in lists)
target = E(*map(dec, fixture['oriented_raw_point']))
left = defaultdict(list)
left_count = 0
for A in lists[0]:
    for B in lists[1]:
        if A['columns'].isdisjoint(B['columns']):
            left[A['point'] + B['point']].append((A, B))
            left_count += 1
right = []
for D in lists[3]:
    for E_state in lists[4]:
        if D['columns'].isdisjoint(E_state['columns']):
            right.append((D['point'] + E_state['point'], D, E_state))
probes = 0
hits = []
for C in lists[2]:
    for right_sum, D, E_state in right:
        if not C['columns'].isdisjoint(D['columns'] | E_state['columns']):
            continue
        need = (target - right_sum) - C['point']
        probes += 1
        for A, B in left.get(need, ()):
            selected = (A, B, C, D, E_state)
            columns = [column for row in selected for column in row['columns']]
            if len(set(columns)) != 10:
                continue
            if sum((row['point'] for row in selected), E(0)) == target:
                hits.append([row['id'] for row in selected])
assert audit['state_ids'] in hits
result = {'status': 'PASS_CHECKED_SAGE_TARGET_CONDITIONED_W9_CONTROL',
          'curve_id': states['curve_id'], 'orientation': 3,
          'states_per_slot': 8, 'left_pair_entries': left_count,
          'right_pair_entries': len(right), 'target_dependent_probes': probes,
          'hit_ids': hits, 'elapsed_ns': time.monotonic_ns() - start,
          'source_sha256': {'script': sha(Path(__file__)),
                            'states': sha(states_path), 'audit': sha(audit_path),
                            'fixture': sha(fixture_path),
                            'runtime': sha(HERE / 'sage_runtime_info.json')}}
with (HERE / 'join_sage_control_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'left_pair_entries': left_count,
                  'target_dependent_probes': probes,
                  'hit_count': len(hits)}))
