"""Read-only verification of frozen quadratic-lift producer and Sage replay."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())
for name in ('protocol.json','audit_protocol.json'):
    p=read(name)
    assert p['status']=='FROZEN'
    for path,digest in p['sources'].items():assert sha(Path(path))==digest,path
for protocol_name,run_name in (('protocol.json','run_result.json'),
                               ('audit_protocol.json','audit_run_result.json')):
    run=read(run_name)
    assert run['status']=='EXIT_0' and run['exit_code']==0 and run['stop_reason'] is None
    assert run['protocol_sha256']==sha(HERE/protocol_name)
    assert run['wall_ns']<120_000_000_000
    for name,digest in run['sha256'].items():assert sha(HERE/name)==digest,name
native=read('result.json');audit=read('audit_result.json')
assert native['status']=='COMPLETE_QUADRATIC_LIFT_SCREEN'
assert audit['status']=='PASS_INDEPENDENT_QUADRATIC_LIFT_REPLAY'
assert native['width']==16 and native['feature_dimension']==862
assert (native['left_unique'],native['right_unique'],native['right_lift_rank'])==(120,128,128)
for key in ('right_lift_rank','root_proposals','lift_passes','set_hits'):
    assert native[key]==audit[key]
assert (native['root_proposals'],native['lift_passes'],native['set_hits'],native['lift_false_positives'])==(240,1,1,0)
print(json.dumps({'status':'PASS_QUADRATIC_LIFT_RECEIPTS',
                  'native_wall_ns':read('run_result.json')['wall_ns'],
                  'audit_wall_ns':read('audit_run_result.json')['wall_ns'],
                  'result_sha256':sha(HERE/'result.json'),
                  'audit_sha256':sha(HERE/'audit_result.json')},sort_keys=True))
