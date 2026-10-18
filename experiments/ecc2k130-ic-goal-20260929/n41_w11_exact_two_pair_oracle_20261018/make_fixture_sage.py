"""Freeze a positive target residual from the unpinned N41 relation."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'fixture_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
out = HERE / 'fixture.json'
assert not out.exists()
audit = json.loads((ROOT / 'n41_w11_fivepair_native_join_20261018' /
                    'audit_result.json').read_text())
assert audit['status'] == 'PASS_INDEPENDENT_N41_W11_FIVEPAIR_PUBLIC_RELATION'
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])


def dec(number):
    return K(P([(number >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coefficient) << i
               for i, coefficient in enumerate(value.polynomial().list()))


points = [E(dec(row['pair_point'][0]), dec(row['pair_point'][1]))
          for row in audit['rows']]
Q = E(dec(audit['target_point'][0]), dec(audit['target_point'][1]))
R = points[3] + points[4]
assert R == Q - points[0] - points[1] - points[2]
assert R != E(0) and R[0]
positive = []
for slot in (3, 4):
    row = audit['rows'][slot]
    rotation = row['rotation']
    unrotated = E(points[slot][0]**(1 << (41-rotation)),
                  points[slot][1]**(1 << (41-rotation)))
    a, b = map(dec, row['source_masks'])
    product = a*b
    assert product
    positive.append({'code': row['source_code'],
                     'source_masks': row['source_masks'],
                     'source_inverse_product': enc(~product),
                     'out_unrotated_reciprocal': enc(~unrotated[0]),
                     'pair_point_rotated': row['pair_point'],
                     'state_id': row['state_id'],
                     'rotation': rotation})
input_path = ROOT / 'n41_w11_fivepair_native_join_20261018' / 'join_input.tsv'
by_code = {}
for line in input_path.read_text().splitlines():
    parts = line.split()
    if parts[0] != 'S' or parts[1] != '3':
        continue
    slot, sid, code, branch, _mask_a, _mask_b, col_a, col_b, _x, _y = map(int, parts[1:])
    if branch == 0:
        assert code not in by_code
        by_code[code] = (col_a, col_b)
assert len(by_code) == 281
collisions = []
for a in sorted(by_code):
    for b in sorted(by_code):
        if a >= b:
            continue
        if set(by_code[a]) & set(by_code[b]):
            collisions.append([a, b])
assert len(collisions) == 5
result = {'status': 'PASS_N41_W11_TWO_PAIR_POSITIVE_RESIDUAL_FIXTURE',
          'candidate_id': None, 'curve_id': audit['curve_id'],
          'target_residual_point': [enc(R[0]), enc(R[1])],
          'target_residual_reciprocal': enc(~R[0]),
          'positive_pair_rows': positive,
          'distinct_code_folded_column_collision_pairs': collisions,
          'source_valid_codes': len(by_code),
          'protocol_sha256': sha(HERE / 'fixture_protocol.json')}
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'target_residual_point',
                   'target_residual_reciprocal',
                   'distinct_code_folded_column_collision_pairs')}, sort_keys=True))
