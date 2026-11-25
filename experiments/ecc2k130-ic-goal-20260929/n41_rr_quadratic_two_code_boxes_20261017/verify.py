"""Replay the finite certificate cover and bind its independent group audit."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / 'run.py'
SOURCE = HERE.parent / 'n41_sixpair_shared_target_20261017/join_input.tsv'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location('box_run', RUN)
box = importlib.util.module_from_spec(spec)
spec.loader.exec_module(box)
protocol = json.loads((HERE/'protocol.json').read_text())
partition = json.loads((HERE/'partition_result.json').read_text())
audit = json.loads((HERE/'audit.json').read_text())
assert protocol['source_sha256']['source'] == sha(SOURCE)
assert protocol['source_sha256']['runner'] == sha(RUN)
assert partition['protocol_sha256'] == sha(HERE/'partition_protocol.json')
assert audit['protocol_sha256'] == sha(HERE/'protocol.json')
assert audit['source_sha256'] == sha(SOURCE)
assert audit['status'] == 'PASS_EXACT_GROUP_BOX_AUDIT'
assert [r['relation_count'] for r in audit['rows']] == [1,0,1,0]
points = {}
for line in SOURCE.read_text().splitlines()[1:]:
    v = line.split()
    points[int(v[1]), int(v[2])] = (int(v[9]), int(v[10]))
codes = protocol['extra_codes']
ids = [[4*c+s for s in range(4)] for c in codes]
left_keys = list(itertools.product(*ids[:3]))
right_keys = list(itertools.product(*ids[3:]))
left = [box.rr.left_vector(tuple(points[j, key[j]] for j in range(3))) for key in left_keys]
target = protocol['target']
neg = (target[0], target[1] ^ target[0])
right = [box.rr.right_vector(tuple(points[j+3, key[j]] for j in range(3))+(neg,))
         for key in right_keys]
certs = {(tuple(r['prefix'])): int(r['coefficient_bits_hex'], 16)
         for r in partition['rows'] if r['depth']==2 and r['status']=='CERTIFIED_NO_ZERO'}
assert len(certs)==16
checks = 0
for i, lv in enumerate(left):
    coeff = certs[left_keys[i][:2]]
    for rv in right:
        value = box.rr.dot(lv, rv)
        active = [j for j in range(41) if value >> j & 1]
        features = value
        for a, b in itertools.combinations(active, 2):
            offset = a*(81-a)//2 + (b-a-1)
            features |= 1 << (41+offset)
        assert bin(features & coeff).count('1') % 2 == 1
        checks += 1
assert checks==4096
assert [r['status'] for r in partition['rows'] if r['depth']<2] == \
       ['NO_QUADRATIC_CERTIFICATE']*5
result = {'status':'PASS_16_CERTIFICATE_COVER_AND_GROUP_AUDIT',
          'covered_states':checks,'certificate_count':len(certs),
          'source_sha256':sha(SOURCE),
          'protocol_sha256':sha(HERE/'protocol.json'),
          'result_sha256':sha(HERE/'result.json'),
          'partition_result_sha256':sha(HERE/'partition_result.json'),
          'audit_sha256':sha(HERE/'audit.json')}
with (HERE/'terminal.json').open('x') as f:
    json.dump(result,f,indent=2,sort_keys=True)
    f.write('\n')
print(result['status'])
