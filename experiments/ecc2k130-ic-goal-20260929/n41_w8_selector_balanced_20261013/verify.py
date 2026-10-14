"""Read-only receipt check for balanced same-point N41 W8 selector run."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'n41_w8_selector_elimination_control_20261013'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
p=read(HERE/'protocol.json')
assert p['status']=='FROZEN_BEFORE_N41_W8_SELECTOR_CONTROL_AND_PUBLIC'
for path,digest in p['source_sha256'].items():assert sha(Path(path))==digest,path
assert sha(Path(p['solver_path']))==p['solver_sha256']
assert sha(HERE/'preflight.json')==p['preflight_sha256']
assert read(HERE/'preflight.json')['status']=='PASS_N41_W8_SELECTOR_PREFLIGHT'
for protocol_name,run_name in (('control_run_protocol.json','control_run_result.json'),
                               ('public_protocol.json','public_result.json')):
    protocol=read(HERE/protocol_name)
    for path,digest in protocol['sources'].items():assert sha(Path(path))==digest,path
    run=read(HERE/run_name)
    assert run['protocol_sha256']==sha(HERE/protocol_name)
    for name,digest in run['sha256'].items():assert sha(HERE/name)==digest,name
control=read(HERE/'control_result.json')
assert control['status']=='PASS_N41_SELECTOR_CONSTRUCTED_ASSIGNMENT'
assert read(HERE/'control_run_result.json')['status']=='EXIT_0'
assert control['assignment_check']=={'clauses':control['clauses'],'native_xor_rows':control['xor_rows']}
assert control['formula_sha256']==sha(HERE/'public.xcnf')
prior=read(PRIOR/'control_result.json')
assert (control['variables'],control['clauses'],control['xor_rows'],control['formula_bytes'])==(
        prior['variables'],prior['clauses'],prior['xor_rows'],prior['formula_bytes'])
assert p['public_point']==read(PRIOR/'protocol.json')['public_point']
query=read(HERE/'public_result.json')
assert query['status']=='BOUNDED_UNKNOWN' and query['stop_reason']=='PARENT_WALL_CAP'
assert query['exit_code']==-15 and not query['terminal_lines'] and not query['monitor_degraded']
assert query['wall_ns']>=185_000_000_000
log=(HERE/'solver.stdout').read_text(errors='replace')
assert log.count('c rst ')>=100 and 's SATISFIABLE' not in log and 's UNSATISFIABLE' not in log
sage=read(PRIOR/'audit_result_v2.json')
assert sage['status']=='PASS_INDEPENDENT_N41_SEVENPAIR_PUBLIC_REPLAY'
assert sage['raw_target']==p['raw_target'] and sage['public_target']==p['public_point']
print(json.dumps({'status':'PASS_BALANCED_N41_W8_SELECTOR_RECEIPTS',
 'formula_sha256':control['formula_sha256'],'query_status':query['status'],
 'query_wall_ns':query['wall_ns'],'restarts':log.count('c rst ')},sort_keys=True))
