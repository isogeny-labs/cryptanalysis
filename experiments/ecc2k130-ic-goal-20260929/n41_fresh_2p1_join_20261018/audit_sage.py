"""Independent checked-Sage replay of a fresh N41 two-plus-one hit."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'audit_protocol.json').read_text())
assert cfg['status'] == 'FROZEN_BEFORE_AUDIT'
for name, item in cfg['sources'].items():
    assert sha(item['path']) == item['sha256'], name
run = json.loads(Path(cfg['sources']['run_result']['path']).read_text())
protocol = json.loads(Path(cfg['sources']['protocol']['path']).read_text())
source = json.loads(Path(cfg['sources']['states']['path']).read_text())
fixture = json.loads(Path(cfg['sources']['fresh_scalar_fixture']['path']).read_text())
fresh = json.loads(Path(cfg['sources']['fresh_protocol']['path']).read_text())
assert run['status'] == 'HIT_PENDING_SAGE_REPLAY'
assert run['protocol_sha256'] == sha(HERE / 'protocol.json')
assert run['stdout_sha256'] == sha(HERE / 'join.stdout')
assert run['stderr_sha256'] == sha(HERE / 'join.stderr')
assert not (HERE / 'join.stderr').read_bytes()
assert fresh['raw_target'] == protocol['target_raw_point']
assert fresh['public_target'] == protocol['target_subgroup_point']
assert len(run['hit_lines']) == 1

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


parts = run['hit_lines'][0].split()
assert len(parts) == 11 and parts[0] == 'HIT'
orientation = int(parts[1])
ids = list(map(int, parts[2:7]))
assert 0 <= orientation < 41 and all(0 <= sid < 284 for sid in ids)
assert [int(line.split()[1]) for line in run['orientation_done_lines']] == list(range(orientation))
assert source['states_per_slot'] == 284

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
        leaves.append({'mask': mask, 'sign': sign,
                       'folded_column_representative': orbit_column(point)})
        pair_leaves.append(point)
    raw = pair_leaves[0] + pair_leaves[1]
    assert raw != E(0)
    rotated = E(raw[0]**(1 << source['rotations'][slot]),
                raw[1]**(1 << source['rotations'][slot]))
    assert xy(rotated) == row['point']
    assert len(set(row['columns'])) == 2
    total += rotated
    pair_rows.append({'slot':slot,'state_id':sid,'masks':row['masks'],
                      'signs':row['signs'],'columns':row['columns'],
                      'rotated_point':xy(rotated)})

assert len({leaf['folded_column_representative'] for leaf in leaves}) == 10
raw_target = E(*map(dec, protocol['target_raw_point']))
subgroup_target = E(*map(dec, protocol['target_subgroup_point']))
assert int(fixture['subgroup_order']) == 549756390943
assert 4 * raw_target == subgroup_target
assert 549756390943 * subgroup_target == E(0)
generator = E(*map(dec, fixture['generator']))
assert fixture['scalar_for_validation_only'] * generator == subgroup_target
oriented = E(raw_target[0]**(1 << orientation), raw_target[1]**(1 << orientation))
assert total == oriented
transported = E(total[0]**(1 << (41 - orientation)),
                total[1]**(1 << (41 - orientation)))
assert transported == raw_target

result = {
    'status':'PASS_INDEPENDENT_FRESH_N41_RELATION',
    'orientation':orientation,'state_ids':ids,'pair_rows':pair_rows,
    'distinct_folded_columns':len(leaves),
    'raw_public_point':xy(transported),'subgroup_public_point':xy(4 * transported),
    'scalar_fixture_replay':True,'source_sha256':sha(cfg['sources']['states']['path']),
    'run_result_sha256':sha(HERE/'run_result.json'),
    'audit_protocol_sha256':sha(HERE/'audit_protocol.json'),
    'auditor_sha256':sha(Path(__file__))}
(HERE/'audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','orientation','state_ids','distinct_folded_columns','raw_public_point','subgroup_public_point')}),flush=True)
