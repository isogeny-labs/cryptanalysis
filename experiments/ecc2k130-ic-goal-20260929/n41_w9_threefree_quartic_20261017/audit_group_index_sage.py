"""Independently audit all three-free-slot signed assignments by group sums."""
import hashlib
import json
import resource
import time
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'group_audit_protocol.json').read_text())
for name, path in {
    'script': Path(__file__), 'runtime': HERE / 'group_audit_runtime_info.json',
    'states': SOURCE, 'producer': HERE / 'result.json',
}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'group_audit_result.json').exists()
source = json.loads(SOURCE.read_text())
producer = json.loads((HERE / 'result.json').read_text())
K = PolynomialRing(GF(2), 'u')
u = K.gen()
F = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(K([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def key(point):
    if point == E(0):
        return None
    return (enc(point[0]), enc(point[1]))


states = [[E(dec(row['point'][0]), dec(row['point'][1])) for row in slot]
          for slot in source['states']]
raw = E(dec(source['target_raw_point'][0]),
        dec(source['target_raw_point'][1]))
public = E(raw[0]**(1 << 6), raw[1]**(1 << 6))

table = defaultdict(list)
build_start = time.monotonic()
for left_id, left in enumerate(states[2]):
    for right_id, right in enumerate(states[3]):
        table[key(left+right)].append((left_id, right_id))
build_seconds = time.monotonic()-build_start
assert sum(len(v) for v in table.values()) == 284*284

fixed0 = states[0][105]
fixed4 = states[4][111]
fixed_columns = set(source['states'][0][105]['columns']+
                    source['states'][4][111]['columns'])
query_start = time.monotonic()
raw_hits = 0
witnesses = []
for outer_id, outer in enumerate(states[1]):
    residual = public-fixed0-fixed4-outer
    matches = table.get(key(residual), ())
    raw_hits += len(matches)
    for left_id, right_id in matches:
        cols = (fixed_columns |
                set(source['states'][1][outer_id]['columns']) |
                set(source['states'][2][left_id]['columns']) |
                set(source['states'][3][right_id]['columns']))
        if len(cols) != 10:
            continue
        assert fixed0+outer+states[2][left_id]+states[3][right_id]+fixed4 == public
        witnesses.append([105, outer_id, left_id, right_id, 111])
query_seconds = time.monotonic()-query_start
witnesses.sort()
assert witnesses == sorted(producer['exact_witnesses'])

result = {
    'status': 'PASS_INDEPENDENT_N41_THREEFREE_GROUP_INDEX',
    'pair_signed_assignments_indexed': 284*284,
    'outer_signed_states_queried': 284,
    'raw_group_hits': raw_hits,
    'distinct_pair_sum_keys': len(table),
    'exact_witnesses': witnesses,
    'index_build_seconds': build_seconds,
    'outer_query_seconds': query_seconds,
    'total_group_stage_seconds': build_seconds+query_seconds,
    'self_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE / 'group_audit_protocol.json'),
    'source_sha256': {'script': sha(Path(__file__)),
                      'runtime': sha(HERE / 'group_audit_runtime_info.json'),
                      'states': sha(SOURCE), 'producer': sha(HERE / 'result.json')},
}
(HERE / 'group_audit_result.json').write_text(
    json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': result['status'], 'witnesses': witnesses,
                  'seconds': result['total_group_stage_seconds']}))
