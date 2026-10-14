"""Read-only receipt and source-law verification for N41 selector control."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())
p=read('protocol.json')
assert p['status']=='FROZEN_BEFORE_N41_W8_SELECTOR_CONTROL_AND_PUBLIC'
for path,digest in p['source_sha256'].items():assert sha(Path(path))==digest,path
assert sha(Path(p['solver_path']))==p['solver_sha256']
assert sha(HERE/'preflight.json')==p['preflight_sha256']
pre=read('preflight.json')
assert (pre['support_masks'],pre['codes_checked'],pre['source_product_rank'],pre['permitted_pair_codes'])==(125,128,7,40)
for protocol_name,run_name in (('control_run_protocol.json','control_run_result.json'),
                               ('public_protocol.json','public_result.json'),
                               ('audit_protocol.json','audit_run_result.json'),
                               ('audit_protocol_v2.json','audit_run_result_v2.json')):
    protocol=read(protocol_name)
    for path,digest in protocol['sources'].items():assert sha(Path(path))==digest,path
    run=read(run_name)
    assert run['protocol_sha256']==sha(HERE/protocol_name)
    for name,digest in run['sha256'].items():assert sha(HERE/name)==digest,name
control=read('control_result.json');control_run=read('control_run_result.json')
assert control['status']=='PASS_N41_SELECTOR_CONSTRUCTED_ASSIGNMENT'
assert control_run['status']=='EXIT_0' and control_run['exit_code']==0
assert control['formula_sha256']==sha(HERE/'public.xcnf')
assert control['assignment_check']=={'clauses':control['clauses'],'native_xor_rows':control['xor_rows']}
query=read('public_result.json')
assert query['status']=='BOUNDED_UNKNOWN' and query['stop_reason']=='PARENT_WALL_CAP'
assert query['exit_code']==-15 and not query['terminal_lines']
assert query['wall_ns']>=185_000_000_000 and not query['monitor_degraded']
log=(HERE/'solver.stdout').read_text(errors='replace')
assert log.count('c rst ')>=100 and 's SATISFIABLE' not in log and 's UNSATISFIABLE' not in log
failed=read('audit_run_result.json')
assert failed['status']=='EXIT_ERROR' and failed['exit_code']==1
assert 'AssertionError' in (HERE/'audit.stderr').read_text()
audit=read('audit_result_v2.json');audit_run=read('audit_run_result_v2.json')
assert audit['status']=='PASS_INDEPENDENT_N41_SEVENPAIR_PUBLIC_REPLAY'
assert audit_run['status']=='EXIT_0' and audit_run['exit_code']==0
assert len(audit['pairs'])==7 and audit['distinct_columns']==14
assert audit['raw_target']==p['raw_target'] and audit['public_target']==p['public_point']
print(json.dumps({'status':'PASS_N41_W8_SELECTOR_CONTROL_RECEIPTS',
 'formula_sha256':control['formula_sha256'],'variables':control['variables'],
 'query_status':query['status'],'query_wall_ns':query['wall_ns'],
 'sage_audit_status':audit['status'],'sage_audit_wall_ns':audit_run['wall_ns']},sort_keys=True))
