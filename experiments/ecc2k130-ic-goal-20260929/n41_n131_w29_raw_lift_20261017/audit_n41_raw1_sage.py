"""Independent group replay of a second-lift five-pair relation."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'n41_raw1_protocol.json').read_text())
result = json.loads((HERE / 'n41_raw1_result.json').read_text())
lift = json.loads((HERE / 'lift_targets.json').read_text())['rows'][0]
source = json.loads((SOURCE / 'n41_states.json').read_text())
assert result['status'] == 'HIT_PENDING_SAGE_REPLAY'
assert result['protocol_sha256'] == sha(HERE / 'n41_raw1_protocol.json')
assert result['stdout_sha256'] == sha(HERE / 'n41_raw1.stdout')
assert result['stderr_sha256'] == sha(HERE / 'n41_raw1.stderr')
assert len(result['hit_lines']) == 1 and not (HERE / 'n41_raw1.stderr').read_bytes()
for name, path in {'input': HERE / 'n41_raw1_join_input.tsv',
                   'lift_targets': HERE / 'lift_targets.json',
                   'native_binary': SOURCE / 'join_orbit',
                   'native_source': SOURCE / 'join_orbit.cpp',
                   'states': SOURCE / 'n41_states.json',
                   'runtime': HERE / 'sage_runtime_info.json'}.items():
    assert sha(path) == protocol['source_sha256'][name], name

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
        point = E.lift_x(1 + 1 / h, all=True)[0]
        if sign:
            point = -point
        pair_leaves.append(point)
        leaves.append({'mask': mask, 'sign': sign,
                       'folded_column_representative': orbit_column(point)})
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
    total += rotated
    pair_rows.append({'slot': slot, 'state_id': sid, 'masks': row['masks'],
                      'signs': row['signs'], 'columns': row['columns'],
                      'rotated_point': xy(rotated)})

assert len({leaf['folded_column_representative'] for leaf in leaves}) == 10
target = E(*map(dec, lift['raw1']))
subgroup = E(*map(dec, lift['subgroup_point']))
oriented = E(target[0]**(1 << orientation), target[1]**(1 << orientation))
assert total == oriented
transported = E(total[0]**(1 << (41 - orientation)),
                total[1]**(1 << (41 - orientation)))
assert transported == target and 4 * transported == subgroup
audit = {'status': 'PASS_INDEPENDENT_N41_RAW1_PUBLIC_RELATION',
         'orientation': orientation, 'state_ids': ids, 'pair_rows': pair_rows,
         'raw_oriented_point': xy(total), 'raw_public_point': xy(transported),
         'subgroup_public_point': xy(4 * transported),
         'distinct_folded_columns': len(leaves),
         'source_sha256': sha(SOURCE / 'n41_states.json'),
         'search_result_sha256': sha(HERE / 'n41_raw1_result.json'),
         'lift_targets_sha256': sha(HERE / 'lift_targets.json'),
         'auditor_sha256': sha(Path(__file__))}
with (HERE / 'n41_raw1_audit_result.json').open('x') as out:
    json.dump(audit, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({k: audit[k] for k in ('status', 'orientation', 'state_ids',
                                       'distinct_folded_columns', 'raw_public_point')}))
