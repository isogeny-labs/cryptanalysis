"""Independently reconstruct a native five-pair hit and its subgroup relation."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'audit_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
out = HERE / 'audit_result.json'
assert not out.exists()
query = json.loads((HERE / 'query_result.json').read_text())
assert query['status'] == 'N41_W11_NATIVE_RELATION_UNVERIFIED'
fixture = json.loads((ROOT / 'n41_n131_w29_rotation_alignment_20261017' /
                      'n41_model_fixture.json').read_text())
started = time.monotonic()
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])
r = 549756390943
O = E(0)


def dec(number):
    return K(P([(number >> i) & 1 for i in range(41)]))


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
    x = K.one() + ~h
    points = E.lift_x(x, all=True)
    assert len(points) == 2
    return points


def column(mask):
    x = K.one() + ~halftrace(mask)
    seen = []
    for _ in range(41):
        seen.append(enc(x))
        x = x*x
    return min(seen)


selected = {}
for line in (HERE / 'join_input.tsv').read_text().splitlines():
    parts = line.split()
    if parts[0] != 'S':
        continue
    slot, sid = map(int, parts[1:3])
    if sid == query['hit']['state_ids'][slot]:
        assert slot not in selected
        selected[slot] = [int(value) for value in parts[3:]]
assert len(selected) == 5
bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
rows = []
source_columns = []
raw_sum = O
projected_sum = O
for slot in range(5):
    code, branch, mask_a, mask_b, col_a, col_b, raw_x, raw_y = selected[slot]
    reconstructed_a = sum((dec(1 << (bit+1)) for index, bit in enumerate(bits)
                           if code >> index & 1), K.zero())
    reconstructed_b = reconstructed_a + dec(112)
    assert enc(reconstructed_a) == mask_a and enc(reconstructed_b) == mask_b
    assert column(reconstructed_a) == col_a and column(reconstructed_b) == col_b
    a_points, b_points = source_points(reconstructed_a), source_points(reconstructed_b)
    observed = E(dec(raw_x), dec(raw_y))
    options = []
    for sa, pa in enumerate(a_points):
        for sb, pb in enumerate(b_points):
            summed = pa + pb
            rotation = fixture['rotations'][slot]
            rotated = E(summed[0]**(1 << rotation), summed[1]**(1 << rotation))
            if rotated == observed:
                options.append((sa, sb, pa, pb))
    assert len(options) == 1
    sa, sb, pa, pb = options[0]
    assert branch == 2*sa + sb
    assert observed != O and observed[0]
    raw_sum += observed
    projected_sum += 4*observed
    source_columns.extend([col_a, col_b])
    assert r*(4*pa) == O and r*(4*pb) == O
    rows.append({'slot': slot, 'state_id': query['hit']['state_ids'][slot],
                 'source_code': code, 'source_masks': [mask_a, mask_b],
                 'source_signs': [sa, sb],
                 'folded_columns': [col_a, col_b],
                 'pair_point': [raw_x, raw_y],
                 'rotation': fixture['rotations'][slot]})
assert len(set(source_columns)) == 10
Q = E(dec(fixture['raw_oriented_point'][0]), dec(fixture['raw_oriented_point'][1]))
assert Q != O and raw_sum == Q
assert projected_sum == 4*Q and 4*Q != O and r*(4*Q) == O
result = {'status': 'PASS_INDEPENDENT_N41_W11_FIVEPAIR_PUBLIC_RELATION',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'target_point': fixture['raw_oriented_point'],
          'subgroup_order': r, 'cofactor': 4,
          'summand_count': 10, 'distinct_folded_columns': len(set(source_columns)),
          'raw_group_sum_matches_target': True,
          'projected_subgroup_sum_matches_target': True,
          'projected_target_nonidentity': True,
          'relation_rank_from_empty_unfolded_matrix': 1,
          'rows': rows,
          'wall_seconds': time.monotonic() - started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'audit_protocol.json')}
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'summand_count', 'distinct_folded_columns',
                   'wall_seconds')}, sort_keys=True))
