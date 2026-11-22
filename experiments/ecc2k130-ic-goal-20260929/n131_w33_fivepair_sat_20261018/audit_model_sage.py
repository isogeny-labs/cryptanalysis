"""Independently verify a W33 positive SAT model through the curve sum."""
import hashlib
import itertools
import json
import math
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import circuit_w33 as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'audit_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    assert sha(name) == expected, name
solver = json.loads((HERE / 'solver_0_result.json').read_text())
assert solver['status'] == 'SAT_MODEL_UNVERIFIED'
assert solver['solver_terminal_sat'] is True
assert not (HERE / 'positive_model_audit_result.json').exists()
control = json.loads((ROOT / 'n41_n131_fivepair_w9_w29_20261017' / 'n131_control_3p2.json').read_text())
started = time.monotonic()
circ, wires, counts = design.build(control['target_reciprocal'])
assert counts == json.loads((HERE / 'build_0_result.json').read_text())['counts']
stdout = (HERE / 'solver_0.stdout').read_text()
literals = [int(token) for line in stdout.splitlines() if line.startswith('v ')
            for token in line.split()[1:]]
positive = {value for value in literals if value > 0}
assigned = {abs(value) for value in literals if value}
assert len(assigned) == counts['variables']


def truth(lit):
    return lit in positive if lit > 0 else -lit not in positive


for row in circ.clauses:
    assert any(truth(int(token)) for token in row.split()[:-1])
for row in circ.xors:
    assert sum(truth(int(token)) for token in row.split()[1:-1]) % 2 == 1


def word(wires):
    return sum((wire in positive) << j for j, wire in enumerate(wires))


codes = [word(row) for row in wires['mask']]
masks = [sum(((code >> j) & 1) << bit for j, bit in enumerate(design.BITS))
         for code in codes]
outputs = [word(row) for row in wires['out']]
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**131, name='u', modulus=u**131+u**13+u**2+u+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
ORDER = 680564733841876926932320129493409985129


def dec(value):
    return F(R([(value >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    result = F.zero()
    term = value
    for _ in range(66):
        result += term
        term = term**4
    assert result*result+result == value
    return result


def endpoint(mask):
    a = dec(mask << 1)
    assert a and a.trace() == 0 and (1/a).trace() == 0
    x = 1+1/halftrace(a)
    points = E.lift_x(x, all=True)
    assert len(points) == 2
    assert all(ORDER * (4 * point) == E(0) for point in points)
    return points


def folded_column(point):
    return min(enc(point[0]**(1 << k)) for k in range(131))


options, columns, source_rows = [], [], []
for slot, (a, output, rotation) in enumerate(zip(masks, outputs, design.ROTATIONS)):
    b = a ^ design.SEED_MASK
    assert 0 < a < b < (1 << 33)
    left, right = endpoint(a), endpoint(b)
    ca, cb = folded_column(left[0]), folded_column(right[0])
    columns.extend([ca, cb])
    sums = [p+q for p, q in itertools.product(left, right)]
    matches = [p for p in sums if p != E(0) and p[0] and enc(1/p[0]) == output]
    options.append([E(p[0]**(1 << rotation), p[1]**(1 << rotation))
                    for p in matches])
    source_rows.append({'slot': slot, 'mask_code': codes[slot],
                        'masks': [a, b], 'folded_columns': [ca, cb],
                        'matching_signed_pair_sums': len(matches)})

raw = E(*(dec(v) for v in control['target_raw_point']))
assert raw != E(0)
hits = []
if all(options):
    for choices in itertools.product(*(range(len(slot)) for slot in options)):
        points = [slot[choice] for slot, choice in zip(options, choices)]
        if sum(points, E(0)) == raw:
            hits.append({'choice_indices': list(choices),
                         'pair_points': [[enc(p[0]), enc(p[1])] for p in points]})
distinct = len(set(columns)) == 10
status = ('PASS_INDEPENDENT_POSITIVE_MODEL_GROUP_REPLAY' if hits and distinct else
          'MODEL_COLUMN_COLLISION' if hits else 'MODEL_GROUP_REPLAY_MISS')
result = {'status': status, 'candidate_id': None,
          'curve_id': cfg['curve_id'], 'target_raw_point': control['target_raw_point'],
          'mask_codes': codes, 'source_rows': source_rows,
          'group_hits': hits, 'distinct_columns': len(set(columns)),
          'enumerated_signed_combinations': math.prod(map(len, options)),
          'verified_clauses': counts['clauses'],
          'verified_xor_rows': counts['xor_rows'],
          'assigned_variables': len(assigned),
          'wall_seconds': time.monotonic()-started,
          'protocol_sha256': sha(HERE / 'audit_protocol.json')}
(HERE / 'positive_model_audit_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': status, 'group_hits': len(hits),
                  'distinct_columns': result['distinct_columns']}, sort_keys=True))
