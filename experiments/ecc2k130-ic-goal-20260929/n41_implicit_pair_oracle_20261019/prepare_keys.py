"""Freeze exact positive and public-query negative keys for a two-pair oracle."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'key_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'keys.json').exists()
source = json.loads(Path(protocol['source_states']).read_text())
audit = json.loads(Path(protocol['public_audit']).read_text())
assert source['states_per_slot'] == 284
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


def enc(value):
    return sum(int(coefficient) << bit
               for bit, coefficient in enumerate(value.polynomial().list()))


def point(row):
    return E(*map(dec, row['point']))


def key(point_value):
    assert point_value != E(0) and point_value[0] != 0
    return (enc(point_value[0]), enc(point_value[1]))


states = [[point(row) for row in slot] for slot in source['states']]
left = {}
left_count = 0
for a in range(284):
    for b in range(284):
        if set(source['states'][0][a]['columns']) & set(source['states'][1][b]['columns']):
            continue
        total = states[0][a] + states[1][b]
        if total == E(0) or total[0] == 0:
            continue
        left.setdefault(key(total), [a, b])
        left_count += 1
assert left_count == 79424
hit_a, hit_b = audit['state_ids'][:2]
positive = [key(states[0][hit_a] + states[1][hit_b])]
for candidate in left:
    if candidate not in positive:
        positive.append(candidate)
    if len(positive) == 4:
        break
assert all(item in left for item in positive)
target = E(*map(dec, source['target_raw_point']))
negative = []
for c in range(4):
    for a in range(284):
        for b in range(284):
            if set(source['states'][3][a]['columns']) & set(source['states'][4][b]['columns']):
                continue
            candidate = target - states[2][c] - states[3][a] - states[4][b]
            if candidate == E(0) or candidate[0] == 0:
                continue
            encoded = key(candidate)
            if encoded not in left and encoded not in negative:
                negative.append(encoded)
            if len(negative) == 4:
                break
        if len(negative) == 4:
            break
    if len(negative) == 4:
        break
assert len(negative) == 4
rows = []
for index, (truth, values) in enumerate(((True, positive), (False, negative))):
    for x, y in values:
        rows.append({'key_id': ('P' if truth else 'N') + str(index),
                     'point': [x, y], 'reciprocal_x': enc(1 / dec(x)),
                     'exact_member': truth,
                     'reference_witness': left.get((x, y))})
        index += 1
result = {'status': 'PASS_N41_TWO_PAIR_KEY_CENSUS', 'candidate_id': None,
          'curve_id': protocol['curve_id'], 'left_entries': left_count,
          'distinct_left_keys': len(left), 'keys': rows,
          'source_states_sha256': sha(protocol['source_states']),
          'public_audit_sha256': sha(protocol['public_audit']),
          'protocol_sha256': sha(HERE / 'key_protocol.json')}
(HERE / 'keys.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'left_entries': left_count,
                  'distinct_left_keys': len(left), 'keys': len(rows)}))
