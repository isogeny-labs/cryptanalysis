"""Independent checked-Sage group audit of every eligible two-slot pair."""
import hashlib
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, EllipticCurve

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
g = json.loads((ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
hit = json.loads((ROOT / 'n41_sixpair_shared_target_20261017/join_audit_result.json').read_text())
result = json.loads((HERE / 'result.json').read_text())
assert result['source_sha256']['n41_w8_fixed_sum_table_20261009/geometry.json'] == hashlib.sha256((ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json').read_bytes()).hexdigest()
R = PolynomialRing(GF(2), 't')
t = R.gen()
F = GF(2**41, 't', modulus=t**41 + t**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))
def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

def point(p):
    q = E(dec(p[0]), dec(p[1]))
    assert enc(q[0]) == p[0]
    assert enc(q[1]) == p[1]
    return q

fixed_states = [g['blocks'][i]['states'][hit['pair_rows'][i]['state_id']] for i in range(2, 6)]
fixed = sum((point(s['raw_sum']) for s in fixed_states), E(0))
target = point(hit['raw_target'])
used = {c for s in fixed_states for c in s['columns']}
eligible = [[(i, s) for i, s in enumerate(g['blocks'][j]['states']) if not used.intersection(s['columns'])] for j in (0, 1)]
left = [(i, s, point(s['raw_sum'])) for i, s in eligible[0]]
right = [(j, s, point(s['raw_sum'])) for j, s in eligible[1]]
all_group = []
valid_group = []
for i, a, pa in left:
    residual = target - fixed - pa
    for j, b, pb in right:
        if residual == pb:
            all_group.append([i, j])
            if set(a['columns']).isdisjoint(b['columns']):
                valid_group.append([i, j])
assert all_group == result['matches']
assert valid_group == result['matches']
assert result['expected_pair'] in valid_group
audit = {'status': 'PASS', 'method': 'independent Sage group subtraction',
         'field_modulus': str(t**41+t**3+1), 'curve_order': int(E.cardinality()),
         'eligible_states': [len(left), len(right)],
         'group_pairs_checked': len(left)*len(right),
         'raw_group_matches': all_group, 'distinct_column_group_matches': valid_group,
         'runner_result_sha256': hashlib.sha256((HERE/'result.json').read_bytes()).hexdigest()}
(HERE / 'audit_sage.json').write_text(json.dumps(audit, indent=2, sort_keys=True) + '\n')
print(json.dumps(audit, sort_keys=True))
