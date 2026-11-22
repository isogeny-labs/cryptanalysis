"""Freeze a second panel with dispersed first states and public-query misses."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'diverse_prepare_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'diverse_keys.json').exists()
source = json.loads(Path(protocol['source_states']).read_text())
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


def enc(value):
    return sum(int(coefficient) << bit
               for bit, coefficient in enumerate(value.polynomial().list()))


def packed(point):
    assert point != E(0) and point[0] != 0
    return (enc(point[0]), enc(point[1]))


states = [[E(*map(dec, row['point'])) for row in slot]
          for slot in source['states']]


def disjoint(slot_a, a, slot_b, b):
    return not (set(source['states'][slot_a][a]['columns']) &
                set(source['states'][slot_b][b]['columns']))


left = {}
entries = 0
for a in range(284):
    for b in range(284):
        if not disjoint(0, a, 1, b):
            continue
        value = states[0][a] + states[1][b]
        if value == E(0) or value[0] == 0:
            continue
        left.setdefault(packed(value), [a, b])
        entries += 1
assert entries == len(left) == 79424
rows = []
used = set()
for index, a in enumerate((0, 71, 142, 213)):
    for offset in range(284):
        b = ((13, 77, 141, 205)[index] + offset) % 284
        if not disjoint(0, a, 1, b):
            continue
        value = states[0][a] + states[1][b]
        if value == E(0) or value[0] == 0:
            continue
        key = packed(value)
        if key in used:
            continue
        used.add(key)
        rows.append({'key_id': f'H{index}', 'point': list(key),
                     'exact_member': True, 'reference_witness': [a, b]})
        break
    else:
        raise AssertionError('positive selection exhausted')
target = E(*map(dec, source['target_raw_point']))
for index, c in enumerate((0, 71, 142, 213)):
    for a in range(284):
        for b in range(284):
            if not disjoint(3, a, 4, b):
                continue
            if set(source['states'][2][c]['columns']) & (
                    set(source['states'][3][a]['columns']) |
                    set(source['states'][4][b]['columns'])):
                continue
            value = target - states[2][c] - states[3][a] - states[4][b]
            if value == E(0) or value[0] == 0:
                continue
            key = packed(value)
            if key in left or key in used:
                continue
            used.add(key)
            rows.append({'key_id': f'H{index+4}', 'point': list(key),
                         'exact_member': False,
                         'public_probe_state_ids': [c, a, b]})
            break
        else:
            continue
        break
    else:
        raise AssertionError('negative selection exhausted')
assert len(rows) == 8 and len({row['reference_witness'][0]
                              for row in rows[:4]}) == 4
result = {'status': 'PASS_N41_DIVERSE_KEY_CENSUS', 'candidate_id': None,
          'curve_id': protocol['curve_id'], 'keys': rows,
          'left_entries': entries, 'distinct_left_keys': len(left),
          'protocol_sha256': sha(HERE / 'diverse_prepare_protocol.json')}
(HERE / 'diverse_keys.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'first_ids':
                  [row['reference_witness'][0] for row in rows[:4]],
                  'third_ids':[row['public_probe_state_ids'][0] for row in rows[4:]]}))
