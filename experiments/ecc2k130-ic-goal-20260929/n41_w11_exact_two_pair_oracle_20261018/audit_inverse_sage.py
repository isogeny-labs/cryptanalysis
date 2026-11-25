"""Independent direct-group two-list check of implicit hit and miss rows."""
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'inverse_audit_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
out = HERE / 'inverse_audit_result.json'
assert not out.exists()
inverse = json.loads((HERE / 'inverse_result.json').read_text())
assert inverse['status'] == 'COMPLETE_N41_W11_IMPLICIT_TWO_PAIR_ORACLE'
started = time.monotonic()
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])


def dec(number):
    return K(P([(number >> i) & 1 for i in range(41)]))


lists = {3: [], 4: []}
for line in (ROOT / 'n41_w11_fivepair_native_join_20261018' /
             'join_input.tsv').read_text().splitlines():
    parts = line.split()
    if parts[0] != 'S' or int(parts[1]) not in lists:
        continue
    slot, sid, code, branch, _a, _b, col_a, col_b, x, y = map(int, parts[1:])
    assert sid == len(lists[slot])
    lists[slot].append({'sid': sid, 'code': code, 'branch': branch,
                        'cols': {col_a, col_b},
                        'point': E(dec(x), dec(y))})
assert len(lists[3]) == len(lists[4]) == 1124
right = defaultdict(list)
for row in lists[4]:
    right[row['point']].append(row)
rows = []
for observed in inverse['query_rows']:
    target = E(*map(dec, observed['target_point']))
    matches = []
    for first in lists[3]:
        second_point = target - first['point']
        for second in right.get(second_point, []):
            if first['code'] == second['code'] or first['cols'] & second['cols']:
                continue
            assert first['point'] + second['point'] == target
            matches.append({'source_codes': [first['code'], second['code']],
                            'branches': [first['branch'], second['branch']],
                            'state_ids': [first['sid'], second['sid']]})
    if observed['status'] == 'EXACT_TWO_PAIR_HIT':
        assert matches
        assert any(row['source_codes'] == observed['source_codes'] and
                   row['branches'] == observed['branch_indices']
                   for row in matches)
    else:
        assert observed['status'] == 'EXACT_TWO_PAIR_MISS' and not matches
    rows.append({'name': observed['name'], 'direct_exact_matches': len(matches),
                 'matches': matches})
result = {'status': 'PASS_INDEPENDENT_N41_W11_IMPLICIT_ORACLE_HIT_MISS',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'first_states': len(lists[3]), 'second_states': len(lists[4]),
          'query_rows': rows, 'wall_seconds': time.monotonic()-started,
          'protocol_sha256': sha(HERE / 'inverse_audit_protocol.json')}
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'query_rows', 'wall_seconds')}, sort_keys=True))
