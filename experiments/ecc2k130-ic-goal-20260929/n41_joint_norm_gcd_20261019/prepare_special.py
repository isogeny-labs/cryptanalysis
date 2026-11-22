"""Freeze a key with x(K) in the first-family x support."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'special_prepare_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'special_keys.json').exists()
source = json.loads(Path(protocol['source_states']).read_text())
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


def point(row):
    return E(*map(dec, row['point']))


K = point(source['states'][0][0])
left_points = [point(row) for row in source['states'][0]]
right_points = [point(row) for row in source['states'][1]]
witnesses = []
eligible = 0
for a, A in enumerate(left_points):
    ca = set(source['states'][0][a]['columns'])
    for b, B in enumerate(right_points):
        if not ca.isdisjoint(source['states'][1][b]['columns']):
            continue
        eligible += 1
        if A+B == K:
            witnesses.append([a, b])
assert eligible == 79424
result = {'status': 'PASS_N41_SPECIAL_X_KEY_CENSUS',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'keys': [{'key_id': 'E0', 'point': source['states'][0][0]['point'],
                    'exact_member': bool(witnesses),
                    'reference_witnesses': witnesses}],
          'eligible_pair_entries': eligible,
          'protocol_sha256': sha(HERE / 'special_prepare_protocol.json')}
(HERE / 'special_keys.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status':result['status'], 'exact_member':bool(witnesses),
                  'witness_count':len(witnesses)}))
