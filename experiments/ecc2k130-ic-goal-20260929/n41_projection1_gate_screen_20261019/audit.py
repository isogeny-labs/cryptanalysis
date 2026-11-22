"""Audit one-bit N41 projected-resultant structural gate screen."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocols={}
checks=0
for path in sorted(HERE.glob('*protocol.json')):
    row=json.loads(path.read_text())
    assert row['candidate_id'] is None
    for source,digest in row['sources'].items():
        assert sha(source)==digest,source
        checks+=1
    protocols[path.name]=sha(path)
build=json.loads((HERE/'build_result.json').read_text())
slice_result=json.loads((HERE/'slice_result.json').read_text())
assert build['protocol_sha256']==protocols['build_protocol.json']
assert slice_result['protocol_sha256']==protocols['slice_protocol.json']
assert build['projected_field_bits']==[5]
assert build['formula_sha256']==sha(HERE/'fivepair_projection.xcnf')
assert slice_result['formula_sha256']==sha(HERE/'fivepair_projection_sliced.xcnf')
assert slice_result['map_sha256']==sha(HERE/'slice_map.json')
assert build['reference_control']=={
    'clauses':build['counts']['clauses'],
    'native_xor_rows':build['counts']['xor_rows']}
assert slice_result['old_and_gates']==build['counts']['and_gates']
assert slice_result['new_and_gates']==20791
result={'status':'PASS_N41_ONE_BIT_GATE_SCREEN_AUDIT','candidate_id':None,
        'curve_id':build['curve_id'],'protocols':protocols,
        'source_hashes_checked':checks,
        'old_and_gates':slice_result['old_and_gates'],
        'retained_and_gates':slice_result['new_and_gates']}
(HERE/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'source_hashes_checked':checks}))
