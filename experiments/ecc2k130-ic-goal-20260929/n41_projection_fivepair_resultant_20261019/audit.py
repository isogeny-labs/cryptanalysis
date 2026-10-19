"""Audit the frozen N41 projected-resultant build, query, and slice."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocols={}
checked=0
for path in sorted(HERE.glob('*protocol.json')):
    row=json.loads(path.read_text())
    assert row['candidate_id'] is None
    for source,digest in row['sources'].items():
        assert sha(source)==digest,source
        checked+=1
    protocols[path.name]=sha(path)
build=json.loads((HERE/'build_result.json').read_text())
query=json.loads((HERE/'query_result.json').read_text())
slice_result=json.loads((HERE/'slice_result.json').read_text())
assert build['protocol_sha256']==protocols['build_protocol.json']
assert query['protocol_sha256']==protocols['query_protocol.json']
assert slice_result['protocol_sha256']==protocols['slice_protocol.json']
assert build['formula_sha256']==sha(HERE/'fivepair_projection.xcnf')
assert slice_result['formula_sha256']==sha(HERE/'fivepair_projection_sliced.xcnf')
assert slice_result['map_sha256']==sha(HERE/'slice_map.json')
assert query['stdout_sha256']==sha(HERE/'query.stdout')
assert query['stderr_sha256']==sha(HERE/'query.stderr')
assert build['reference_control']=={
    'clauses':build['counts']['clauses'],
    'native_xor_rows':build['counts']['xor_rows']}
assert build['counts']['and_gates']==slice_result['old_and_gates']
assert query['status']=='BOUNDED_UNKNOWN'
assert query['stop_reason']=='PARENT_WALL_CAP'
assert not query['status_lines']
assert query['monitor_errors']==0 and query['rss_samples']>0
assert query['sampled_peak_worker_rss_bytes']<query['rss_cap_bytes']
assert slice_result['new_and_gates']<=slice_result['old_and_gates']
assert slice_result['new_variables']<=slice_result['old_variables']
result={'status':'PASS_N41_PROJECTED_FIVEPAIR_AUDIT','candidate_id':None,
        'curve_id':build['curve_id'],'protocols':protocols,
        'source_hashes_checked':checked,
        'full_and_gates':slice_result['old_and_gates'],
        'retained_and_gates':slice_result['new_and_gates'],
        'public_query_status':query['status']}
(HERE/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'protocol_count':len(protocols),
                  'source_hashes_checked':checked}))
