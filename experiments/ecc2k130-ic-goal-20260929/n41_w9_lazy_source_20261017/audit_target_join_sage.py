"""Independent Sage replay of the target-conditioned N41 W9 orbit hit."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol_path = HERE / 'target_join_protocol.json'
result_path = HERE / 'target_join_result.json'
states_path = PRIOR / 'n41_states.json'
protocol = json.loads(protocol_path.read_text())
result = json.loads(result_path.read_text())
source = json.loads(states_path.read_text())
assert protocol['status'] == 'FROZEN_BEFORE_TARGET_CONDITIONED_JOIN'
assert result['status'] == 'HIT_PENDING_SAGE_REPLAY'
assert result['protocol_sha256'] == sha(protocol_path)
assert result['stdout_sha256'] == sha(HERE / 'target_join.stdout')
assert result['stderr_sha256'] == sha(HERE / 'target_join.stderr')
assert len(result['hits']) == 1 and not (HERE / 'target_join.stderr').read_bytes()
assert protocol['source_sha256']['input'] == sha(PRIOR / 'join_input.tsv')
assert protocol['source_sha256']['source'] == sha(HERE / 'join_target_conditioned.cpp')
assert protocol['source_sha256']['binary'] == sha(HERE / 'join_target_conditioned')
assert protocol['source_sha256']['runner'] == sha(HERE / 'run_target_join.py')
assert protocol['source_sha256']['fixture'] == sha(HERE / 'fixture.json')

R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


def enc(value):
    return sum(int(bit) << index for index, bit in enumerate(value.polynomial().list()))


def xy(point):
    return [enc(point[0]), enc(point[1])]


def halftrace(value):
    return sum((value**(1 << (2 * bit)) for bit in range(21)), F.zero())


def folded_column(point):
    return min(enc(point[0]**(1 << bit)) for bit in range(41))


parts = result['hits'][0].split()
assert len(parts) == 10 and parts[0] == 'HIT'
orientation = int(parts[1])
ids = list(map(int, parts[2:7]))
assert 0 <= orientation < 41
assert all(0 <= state_id < source['states_per_slot'] for state_id in ids)
assert [int(row.split()[1]) for row in result['orientation_done']] == list(range(orientation))
total = E(0)
columns = []
rows = []
for slot, state_id in enumerate(ids):
    row = source['states'][slot][state_id]
    leaves = []
    for mask, sign in zip(row['masks'], row['signs']):
        w = dec(mask << 1)
        assert w and w.trace() == 0 and (1 / w).trace() == 0
        h = halftrace(w)
        assert h and h**2 + h == w
        point = E.lift_x(1 + 1 / h, all=True)[0]
        if sign:
            point = -point
        columns.append(folded_column(point))
        leaves.append(point)
    pair = leaves[0] + leaves[1]
    assert pair != E(0) and pair[0]
    rotated = E(pair[0]**(1 << source['rotations'][slot]),
                pair[1]**(1 << source['rotations'][slot]))
    assert xy(rotated) == row['point']
    assert sorted(row['columns']) == sorted(columns[-2:])
    total += rotated
    rows.append({'slot': slot, 'state_id': state_id,
                 'masks': row['masks'], 'signs': row['signs'],
                 'folded_columns': row['columns'], 'rotated_point': xy(rotated)})
assert len(set(columns)) == 10
target = E(*map(dec, source['target_raw_point']))
oriented = E(target[0]**(1 << orientation),
             target[1]**(1 << orientation))
assert total == oriented
transported = E(total[0]**(1 << (41 - orientation)),
                total[1]**(1 << (41 - orientation)))
assert transported == target
fixture = json.loads((HERE / 'fixture.json').read_text())
subgroup = E(*map(dec, fixture['original_subgroup_point']))
assert 4 * transported == subgroup
audit = {'status': 'PASS_INDEPENDENT_TARGET_CONDITIONED_N41_PUBLIC_RELATION',
         'curve_id': source['curve_id'], 'orientation': orientation,
         'state_ids': ids, 'source_rows': rows,
         'distinct_folded_columns': len(set(columns)),
         'raw_public_point': xy(transported),
         'subgroup_public_point': xy(4 * transported),
         'source_sha256': {'auditor': sha(Path(__file__)),
                           'result': sha(result_path),
                           'protocol': sha(protocol_path),
                           'states': sha(states_path),
                           'runtime': sha(HERE / 'sage_runtime_info.json')}}
with (HERE / 'target_join_audit_result.json').open('x') as out:
    json.dump(audit, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': audit['status'], 'orientation': orientation,
                  'state_ids': ids, 'distinct_folded_columns': len(set(columns))}))
