"""Audit frozen all-deferred N41 source query after archive relocation."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ORIGINAL=Path('/private/tmp/n41_deferred5_source_20261019')


def local(path):
    path=Path(path)
    return HERE/path.relative_to(ORIGINAL) if path==ORIGINAL or ORIGINAL in path.parents else path


def sha(path):
    return hashlib.sha256(local(path).read_bytes()).hexdigest()


protocols={}
checked=0
for path in sorted(HERE.glob('*protocol.json')):
    row=json.loads(path.read_text())
    assert row['candidate_id'] is None
    for name,digest in row['sources'].items():
        assert sha(name)==digest,name
        checked+=1
    protocols[path.name]=sha(path)
build=json.loads((HERE/'build_result.json').read_text())
query=json.loads((HERE/'query_result.json').read_text())
assert build['protocol_sha256']==protocols['build_protocol.json']
assert query['protocol_sha256']==protocols['query_protocol.json']
assert build['formula_sha256']==sha(HERE/'deferred5.xcnf')
assert build['constructed_control']=={
    'clauses':build['counts']['clauses'],
    'native_xor_rows':build['counts']['xor_rows']}
assert query['stdout_sha256']==sha(HERE/'query.stdout')
assert query['stderr_sha256']==sha(HERE/'query.stderr')
assert query['status']=='BOUNDED_UNKNOWN'
assert query['stop_reason']=='PARENT_WALL_CAP'
assert not query['status_lines']
assert query['monitor_errors']==0 and query['rss_samples']>0
assert query['sampled_peak_worker_rss_bytes']<query['rss_cap_bytes']
failure=json.loads((HERE/'build_first_attempt_failure.json').read_text())
assert failure['protocol_sha256']==protocols['build_protocol.json']
assert failure['status']=='PRODUCER_FAILURE_PYTHON_ENVIRONMENT'
workspace=json.loads((HERE/'workspace_first_attempt_failure.json').read_text())
assert workspace['status']=='PRODUCER_FAILURE_WORKSPACE_ENOSPC'
result={'status':'PASS_N41_ALL_DEFERRED_AUDIT','candidate_id':None,
        'curve_id':build['curve_id'],'protocols':protocols,
        'source_hashes_checked':checked,'formula_sha256':build['formula_sha256'],
        'query_status':query['status'],'query_elapsed_ns':query['elapsed_ns']}
(HERE/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'source_hashes_checked':checked}))
