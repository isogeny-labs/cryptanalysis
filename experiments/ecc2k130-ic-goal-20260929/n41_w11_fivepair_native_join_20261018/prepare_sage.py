"""Export exact W11 signed pair points and orbit columns for native join."""
import hashlib
import json
import random
import resource
import signal
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'prepare_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
out = HERE / 'join_input.tsv'
assert not out.exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('W11 native input cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])
count = json.loads((ROOT / 'n41_w11_n131_w33_density_20261018' /
                    'n41_count_result.json').read_text())
fixture = json.loads((ROOT / 'n41_n131_w29_rotation_alignment_20261017' /
                      'n41_model_fixture.json').read_text())
assert fixture['rotations'] == [0, 0, 12, 12, 24]
assert count['valid_pair_codes'] == 281
bits = [i for i in range(11) if i != 5]
base = [K(P([int(j == bit+1) for j in range(41)])) for bit in bits]
seed = K(P([(112 >> j) & 1 for j in range(41)]))


def enc(value):
    return sum(int(coefficient) << i
               for i, coefficient in enumerate(value.polynomial().list()))


def halftrace(value):
    out, power = K.zero(), value
    for _ in range(21):
        out += power
        power = power**4
    assert out*out + out == value
    return out


def source_points(mask):
    h = halftrace(mask)
    assert h
    x = K.one() + ~h
    points = E.lift_x(x, all=True)
    assert len(points) == 2
    return points


def column(mask):
    x = K.one() + ~halftrace(mask)
    values = []
    for _ in range(41):
        values.append(enc(x))
        x = x*x
    return min(values)


base_states = []
for code in count['valid_codes']:
    a = K.zero()
    for index, word in enumerate(base):
        if code >> index & 1:
            a += word
    b = a + seed
    assert a and b and not a.trace() and not (~a).trace() and not (~b).trace()
    col_a, col_b = column(a), column(b)
    left, right = source_points(a), source_points(b)
    for branch, (p, q) in enumerate((p, q) for p in left for q in right):
        point = p + q
        assert point != E(0) and point[0]
        base_states.append({'code': int(code), 'branch': branch,
                            'mask_a': enc(a), 'mask_b': enc(b),
                            'column_a': col_a, 'column_b': col_b,
                            'point': point})
assert len(base_states) == 1124
states = []
lines = [f'W11FIVE 5 {len(base_states)} 1',
         f'T 0 {fixture["raw_oriented_point"][0]} {fixture["raw_oriented_point"][1]}']
for slot, rotation in enumerate(fixture['rotations']):
    row = []
    for sid, item in enumerate(base_states):
        point = item['point']
        rotated = E(point[0]**(1 << rotation), point[1]**(1 << rotation))
        row.append(rotated)
        lines.append(f'S {slot} {sid} {item["code"]} {item["branch"]} '
                     f'{item["mask_a"]} {item["mask_b"]} '
                     f'{item["column_a"]} {item["column_b"]} '
                     f'{enc(rotated[0])} {enc(rotated[1])}')
    states.append(row)
Q = E(*[K(P([(value >> i) & 1 for i in range(41)]))
        for value in fixture['raw_oriented_point']])
assert Q != E(0)
rng = random.Random(protocol['check_seed'])
for _ in range(protocol['addition_checks']):
    slot_a, slot_b = rng.sample(range(5), 2)
    first = states[slot_a][rng.randrange(len(base_states))]
    second = states[slot_b][rng.randrange(len(base_states))]
    total = first + second
    x3, y3 = (-1, -1) if total == E(0) else (enc(total[0]), enc(total[1]))
    lines.append(f'C {enc(first[0])} {enc(first[1])} '
                 f'{enc(second[0])} {enc(second[1])} {x3} {y3}')
out.write_text('\n'.join(lines) + '\n')
signal.alarm(0)
result = {'status': 'PASS_N41_W11_FIVEPAIR_NATIVE_INPUT',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'target_point': fixture['raw_oriented_point'],
          'source_codes': len(count['valid_codes']),
          'signed_states_per_slot': len(base_states),
          'slots': 5, 'rotations': fixture['rotations'],
          'same_folded_column_source_codes': sum(
              1 for item in base_states[::4]
              if item['column_a'] == item['column_b']),
          'addition_checks': protocol['addition_checks'],
          'input_bytes': out.stat().st_size, 'input_sha256': sha(out),
          'wall_seconds': time.monotonic() - started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'prepare_protocol.json')}
(HERE / 'prepare_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'source_codes', 'signed_states_per_slot',
                   'same_folded_column_source_codes', 'wall_seconds')}, sort_keys=True))
