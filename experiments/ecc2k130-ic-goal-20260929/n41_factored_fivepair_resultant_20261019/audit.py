"""Audit frozen factorization, circuit, solver, and proof receipts."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocols={}
source_checks=0
for path in sorted(HERE.glob('*protocol.json')):
    row=json.loads(path.read_text())
    assert row['candidate_id'] is None,path
    for name,digest in row['sources'].items():
        assert sha(name)==digest,name
        source_checks+=1
    protocols[path.name]=sha(path)

factor=json.loads((HERE/'factor_retry_result.json').read_text())
assert factor['protocol_sha256']==protocols['factor_retry_protocol.json']
assert factor['term_count']==37 and factor['degree_p_q_t']==[4,4,8]
first_factor=json.loads((HERE/'factor_first_attempt_failure.json').read_text())
assert first_factor['protocol_sha256']==protocols['factor_protocol.json']
build=json.loads((HERE/'build_result.json').read_text())
assert build['protocol_sha256']==protocols['build_protocol.json']
assert build['formula_sha256']==sha(HERE/'fivepair_factored.xcnf')
assert build['reference_control']=={
    'clauses':build['counts']['clauses'],
    'native_xor_rows':build['counts']['xor_rows']}
probe=json.loads((HERE/'probe_result.json').read_text())
assert probe['protocol_sha256']==protocols['probe_protocol.json']
assert probe['status']=='INDETERMINATE'
assert sha(HERE/'probe.stdout')==probe['stdout_sha256']
assert sha(HERE/'probe.stderr')==probe['stderr_sha256']
first_query=json.loads((HERE/'query_first_attempt_failure.json').read_text())
assert first_query['protocol_sha256']==protocols['query_protocol.json']
assert (HERE/'query.stdout').stat().st_size==0
assert (HERE/'query.stderr').stat().st_size==0
query=json.loads((HERE/'query_retry_result.json').read_text())
assert query['protocol_sha256']==protocols['query_retry_protocol.json']
assert query['status']=='BOUNDED_UNKNOWN'
assert query['stop_reason']=='PARENT_WALL_CAP' and not query['status_lines']
assert query['monitor_errors']==0 and query['rss_samples']>0
assert query['sampled_peak_worker_rss_bytes']<query['rss_cap_bytes']
assert sha(HERE/'query_retry.stdout')==query['stdout_sha256']
assert sha(HERE/'query_retry.stderr')==query['stderr_sha256']
lean=(HERE/'lean.stdout').read_text()
assert 'two_pair_factored_necessary' in lean
assert 'sorryAx' not in lean
assert lean.count('depends on axioms: [propext, Classical.choice, Quot.sound]')==5
assert (HERE/'lean.stderr').read_text()==''
result={'status':'PASS_N41_FACTORED_FIVEPAIR_AUDIT','candidate_id':None,
        'curve_id':build['curve_id'],'source_hashes_checked':source_checks,
        'protocols':protocols,'formula_sha256':build['formula_sha256'],
        'public_query_status':query['status'],'public_query_elapsed_ns':query['elapsed_ns'],
        'lean_theorems_checked':5}
(HERE/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'source_hashes_checked':source_checks,
                  'protocol_count':len(protocols),'lean_theorems_checked':5}))
