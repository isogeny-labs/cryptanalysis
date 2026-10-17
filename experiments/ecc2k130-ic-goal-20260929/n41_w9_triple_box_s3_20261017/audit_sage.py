"""Independent group-law replay of every frozen three-code box."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_words(values):
    return hashlib.sha256(json.dumps(sorted(values), separators=(',', ':')).encode()).hexdigest()


protocol = json.loads((HERE/'audit_protocol.json').read_text())
for name, path in {'script': Path(__file__), 'runtime': HERE/'sage_runtime_info.json',
                   'states': SOURCE, 'panel': HERE/'panel.json',
                   'producer': HERE/'result.json'}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE/'audit_result.json').exists()
panel = json.loads((HERE/'panel.json').read_text())
producer = json.loads((HERE/'result.json').read_text())
source = json.loads(SOURCE.read_text())
assert len(panel['boxes']) == len(producer['rows']) == 1025

R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(F, [1,0,0,0,1])


def dec(word):
    return F(R([(int(word)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(c)<<i for i,c in enumerate(value.polynomial().list()))


states = [[E(dec(row['point'][0]), dec(row['point'][1])) for row in slot]
          for slot in source['states']]
raw = E(dec(source['target_raw_point'][0]),dec(source['target_raw_point'][1]))
public = E(raw[0]**(1<<6),raw[1]**(1<<6))
target = public-states[0][panel['fixed_slot_state_ids']['0']]-states[4][panel['fixed_slot_state_ids']['4']]
assert target != E(0) and target[0]
assert producer['target_partial_point'] == [enc(target[0]),enc(target[1])]

start = time.monotonic()
group_exceptions = 0
exact_hit_boxes = 0
for box, row in zip(panel['boxes'],producer['rows']):
    assert box['codes'] == row['codes'] and box['kind'] == row['kind']
    c1,c2,c3 = box['codes']
    left = {}
    for i in range(4*c1,4*c1+4):
        for j in range(4*c2,4*c2+4):
            point = states[1][i]+states[2][j]
            if point == E(0) or not point[0]:
                group_exceptions += 1
                continue
            word = enc(1/point[0])
            left.setdefault(word,[]).append((i,j,point))
    right = {}
    for k in range(4*c3,4*c3+4):
        point = target-states[3][k]
        if point == E(0) or not point[0]:
            group_exceptions += 1
            continue
        word = enc(1/point[0])
        right.setdefault(word,[]).append((k,point))
    assert digest_words(left) == row['left_digest']
    assert digest_words(right) == row['right_digest']
    intersection = sorted(left.keys()&right.keys())
    assert intersection == row['intersection']
    exact = sorted([[i,j,k]
                    for word in intersection
                    for i,j,lpoint in left[word]
                    for k,rpoint in right[word]
                    if lpoint == rpoint])
    assert exact == row['exact_state_triples']
    assert row['algebraic_hit'] == bool(intersection)
    if exact:
        exact_hit_boxes += 1
    if not intersection and not row['unknown_exception']:
        assert not exact

assert group_exceptions == 0
assert exact_hit_boxes == producer['exact_hit_boxes'] == 1
assert producer['rows'][0]['exact_state_triples'] == [[244,66,47]]
result = {
    'status': 'PASS_INDEPENDENT_N41_TRIPLE_BOX_GROUP_REPLAY',
    'boxes': len(panel['boxes']),
    'signed_assignment_comparisons': len(panel['boxes'])*64,
    'group_chart_exceptions': group_exceptions,
    'exact_hit_boxes': exact_hit_boxes,
    'elapsed_seconds': time.monotonic()-start,
    'self_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE/'audit_protocol.json'),
    'source_sha256': {'producer': sha(HERE/'result.json'),
                      'panel': sha(HERE/'panel.json'), 'states': sha(SOURCE)},
}
(HERE/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k: result[k] for k in
                  ('status','boxes','signed_assignment_comparisons',
                   'group_chart_exceptions','exact_hit_boxes')}))
