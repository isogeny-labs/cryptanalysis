"""Independently replay the recovered source codes as curve points."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'replay_protocol.json').read_text())
for path, expected in cfg['sources'].items():
    assert sha(path) == expected, path
solve = json.loads((HERE / 'quadratic_result.json').read_text())
assert solve['status'] == 'GB_COMPLETE' and solve['pinned_bits'] == 32
codes = [cfg['first_code'], solve['recovered_second_code']]
assert codes == [3, 16722]
coeff = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' / 'coefficients.json').read_text())
P = PolynomialRing(GF(2), 'u')
u = P.gen()
F = GF(2**131, name='u', modulus=u**131+u**13+u**2+u+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(n):
    return F(P([(n >> i) & 1 for i in range(131)]))


def enc(v):
    return sum(int(b) << i for i, b in enumerate(v.polynomial().list()))


def halftrace(value):
    result = F.zero()
    term = value
    for _ in range(66):
        result += term
        term = term**4
    assert result*result+result == value
    return result


seed_mask = 898618
bits = [bit for bit in range(33) if bit != seed_mask.bit_length()-1]
seed = dec(seed_mask << 1)


def points_for_mask(mask):
    a = dec(mask << 1)
    assert a and a.trace() == 0 and (1/a).trace() == 0
    root = halftrace(a)
    x = 1+1/root
    points = sorted(E.lift_x(x, all=True), key=lambda point: enc(point[1]))
    assert len(points) == 2
    return points


pair_choices = []
source_masks = []
for code, rotation in zip(codes, (0, 18)):
    mask = sum(1 << bits[j] for j in range(32) if code >> j & 1)
    companion = mask ^ seed_mask
    assert mask != companion
    a = dec(mask << 1)
    b = dec(companion << 1)
    assert a+b == seed
    assert a.trace() == 0 and b.trace() == 0
    assert (1/a).trace() == 0 and (1/b).trace() == 0
    choices = []
    for i, j in itertools.product(range(2), repeat=2):
        pair = points_for_mask(mask)[i] + points_for_mask(companion)[j]
        assert pair != E(0)
        rotated = E(pair[0]**(1 << rotation), pair[1]**(1 << rotation))
        choices.append((i, j, rotated))
    pair_choices.append(choices)
    source_masks.append([mask, companion])

target_coords = coeff['rows'][0]['point']
target = E(*(dec(v) for v in target_coords))
matches = []
for i, j in itertools.product(range(4), repeat=2):
    pair1, pair2 = pair_choices[0][i], pair_choices[1][j]
    if pair1[2] + pair2[2] == target:
        matches.append({'first_branches': list(pair1[:2]),
                        'second_branches': list(pair2[:2])})
assert matches
result = {'status': 'PASS_INDEPENDENT_N131_CURVE_REPLAY',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'source_codes': codes, 'source_masks': source_masks,
          'target_point': target_coords, 'matching_branch_pairs': matches,
          'protocol_sha256': sha(HERE / 'replay_protocol.json')}
(HERE / 'replay_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result, sort_keys=True))
