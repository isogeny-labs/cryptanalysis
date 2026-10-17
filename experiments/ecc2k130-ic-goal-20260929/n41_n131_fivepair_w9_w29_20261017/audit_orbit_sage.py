"""Independent Sage replay of the unpinned W9 five-pair orbit hit."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'orbit_protocol.json').read_text())
result = json.loads((HERE / 'orbit_result.json').read_text())
source = json.loads((HERE / 'n41_states.json').read_text())
assert result['status'] == 'HIT_PENDING_SAGE_REPLAY'
assert result['protocol_sha256'] == sha(HERE / 'orbit_protocol.json')
assert result['stdout_sha256'] == sha(HERE / 'orbit.stdout')
assert result['stderr_sha256'] == sha(HERE / 'orbit.stderr')
assert len(result['hit_lines']) == 1 and not (HERE / 'orbit.stderr').read_bytes()
for name, digest in protocol['source_sha256'].items():
    assert sha(HERE / name) == digest, name

R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coefficient) << index
               for index, coefficient in enumerate(value.polynomial().list()))


def xy(point):
    return [enc(point[0]), enc(point[1])]


def halftrace(value):
    return sum((value**(1 << (2 * i)) for i in range(21)), F.zero())


def orbit_column(point):
    return min(enc(point[0]**(1 << i)) for i in range(41))


parts = result['hit_lines'][0].split()
assert len(parts) == 10 and parts[0] == 'HIT'
orientation = int(parts[1])
ids = list(map(int, parts[2:7]))
assert 0 <= orientation < 41 and all(0 <= sid < source['states_per_slot'] for sid in ids)
assert [int(row.split()[1]) for row in result['orientation_done_lines']] == list(range(orientation))

leaves = []
pair_rows = []
total = E(0)
for slot, sid in enumerate(ids):
    row = source['states'][slot][sid]
    pair_leaves = []
    for mask, sign in zip(row['masks'], row['signs']):
        w = dec(mask << 1)
        assert w and w.trace() == 0 and (1 / w).trace() == 0
        h = halftrace(w)
        assert h**2 + h == w and h
        x = 1 + 1 / h
        point = E.lift_x(x, all=True)[0]
        if sign:
            point = -point
        leaves.append({'mask': mask, 'sign': sign,
                       'folded_column_representative': orbit_column(point)})
        pair_leaves.append(point)
    raw = pair_leaves[0] + pair_leaves[1]
    assert raw != E(0)
    rotated = E(raw[0]**(1 << source['rotations'][slot]),
                raw[1]**(1 << source['rotations'][slot]))
    assert xy(rotated) == row['point']
    z = 1 / raw[0]
    product = dec(row['masks'][0] << 1) * dec(row['masks'][1] << 1)
    seed = dec(source['seed'] << 1)
    H = halftrace(seed)**2
    assert (1 + H) * z**2 + product * z + H == 0
    assert len(set(row['columns'])) == 2
    total += rotated
    pair_rows.append({'slot': slot, 'state_id': sid, 'masks': row['masks'],
                      'signs': row['signs'], 'columns': row['columns'],
                      'rotated_point': xy(rotated)})

assert len({leaf['folded_column_representative'] for leaf in leaves}) == 10
geometry = json.loads(GEOMETRY.read_text())
target = E(*map(dec, geometry['positive_control']['raw_target']))
subgroup = E(*map(dec, geometry['positive_control']['subgroup_target']))
oriented = E(target[0]**(1 << orientation), target[1]**(1 << orientation))
assert total == oriented
transported = E(total[0]**(1 << (41 - orientation)),
                total[1]**(1 << (41 - orientation)))
assert transported == target
assert 4 * transported == subgroup

audit = {'status': 'PASS_INDEPENDENT_N41_W9_FIVEPAIR_PUBLIC_RELATION',
         'orientation': orientation, 'state_ids': ids, 'pair_rows': pair_rows,
         'raw_oriented_point': xy(total), 'raw_public_point': xy(transported),
         'subgroup_public_point': xy(4 * transported),
         'distinct_folded_columns': len(leaves),
         'source_sha256': sha(HERE / 'n41_states.json'),
         'orbit_result_sha256': sha(HERE / 'orbit_result.json'),
         'geometry_sha256': sha(GEOMETRY),
         'auditor_sha256': sha(Path(__file__))}
with (HERE / 'orbit_audit_result.json').open('x') as out:
    json.dump(audit, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({key: audit[key] for key in
                  ('status', 'orientation', 'state_ids', 'distinct_folded_columns',
                   'raw_public_point', 'subgroup_public_point')}))
