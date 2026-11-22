"""Measure degree-two coordinate-feature rank on exact N41 right partials."""
import hashlib
import json
import random
import resource
import signal
import time
from itertools import combinations
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
out = HERE / 'result.json'
assert not out.exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('rank sample wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])
bits = [i for i in range(11) if i != 5]
base = [K(P([int(j == bit+1) for j in range(41)])) for bit in bits]
seed = K(P([(112 >> j) & 1 for j in range(41)]))
valid_codes = set(json.loads((ROOT / 'n41_w11_n131_w33_density_20261018' /
                             'n41_count_result.json').read_text())['valid_codes'])


def integer(value):
    return sum(int(coefficient) << i
               for i, coefficient in enumerate(value.polynomial().list()))


def halftrace(value):
    out, power = K.zero(), value
    for _ in range(21):
        out += power
        power = power**4
    assert out*out + out == value
    return out


states = []
for code in sorted(valid_codes):
    a = K.zero()
    for i, word in enumerate(base):
        if code >> i & 1:
            a += word
    b = a + seed
    assert a and b and not a.trace() and not (~a).trace() and not (~b).trace()
    left = E.lift_x(K.one() + ~halftrace(a), all=True)
    right = E.lift_x(K.one() + ~halftrace(b), all=True)
    options = [p + q for p in left for q in right]
    assert len(options) == 4
    assert all(point != E(0) and point[0] for point in options)
    for branch, point in enumerate(options):
        states.append((code, branch, point))
assert len(states) == 1124
construction_seconds = time.monotonic() - started

rotated_left = [E(point[0]**(1 << 12), point[1]**(1 << 12))
                for _code, _branch, point in states]
rotated_right = [E(point[0]**(1 << 24), point[1]**(1 << 24))
                 for _code, _branch, point in states]
features = [(i,) for i in range(41)] + list(combinations(range(41), 2))
assert len(features) + 1 == 862


def feature_row(x):
    positions = [i for i in range(41) if x >> i & 1]
    row = 1
    row |= sum(1 << (1 + i) for i in positions)
    active = set(positions)
    row |= sum(1 << (1 + index) for index, (i, j) in
               enumerate(features[41:], start=41) if i in active and j in active)
    return row


rng = random.Random(protocol['sample_seed'])
pivots = {}
witnesses = []
attempts = 0
accepted = 0
while attempts < protocol['max_attempts'] and len(pivots) < 862:
    left_id = rng.randrange(len(states))
    right_id = rng.randrange(len(states))
    attempts += 1
    if states[left_id][0] == states[right_id][0]:
        continue
    partial = rotated_left[left_id] + rotated_right[right_id]
    if partial == E(0) or not partial[0]:
        continue
    x = integer(~partial[0])
    row = feature_row(x)
    accepted += 1
    while row:
        pivot = row.bit_length() - 1
        if pivot not in pivots:
            pivots[pivot] = row
            witnesses.append({'left_state': left_id,
                              'right_state': right_id,
                              'left_code': states[left_id][0],
                              'right_code': states[right_id][0],
                              'left_branch': states[left_id][1],
                              'right_branch': states[right_id][1],
                              'left_point': [integer(states[left_id][2][0]),
                                             integer(states[left_id][2][1])],
                              'right_point': [integer(states[right_id][2][0]),
                                              integer(states[right_id][2][1])],
                              'partial_reciprocal_x': x,
                              'pivot': pivot})
            break
        row ^= pivots[pivot]

signal.alarm(0)
result = {'status': 'FULL_N41_W11_PARTIAL_QUADRATIC_RANK' if len(pivots) == 862
          else 'PARTIAL_N41_W11_PARTIAL_QUADRATIC_RANK',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'field_modulus_integer': (1 << 41) | (1 << 3) | 1,
          'source_code_count': len(valid_codes), 'signed_pair_state_count': len(states),
          'partial_slots': [3, 4], 'rotations': [12, 24],
          'feature_law': 'constant plus 41 coordinate bits plus 820 distinct pairwise bit products of reciprocal x',
          'feature_dimension': 862, 'rank': len(pivots),
          'sample_attempts': attempts, 'accepted_samples': accepted,
          'basis_witnesses': witnesses,
          'source_construction_seconds': construction_seconds,
          'total_wall_seconds': time.monotonic() - started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'protocol.json')}
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'rank', 'sample_attempts', 'accepted_samples',
                   'total_wall_seconds')}, sort_keys=True))
