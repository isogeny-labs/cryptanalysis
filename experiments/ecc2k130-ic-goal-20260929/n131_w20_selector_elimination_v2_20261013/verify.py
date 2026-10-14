"""Read-only audit of frozen W20 selector-projector control."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())
p=read('protocol.json')
assert p['status']=='FROZEN_BEFORE_SELECTOR_ELIMINATION_CONTROL'
for path,digest in p['source_sha256'].items():assert sha(Path(path))==digest,path
assert p['basis_result_sha256']==sha(HERE/'basis_result.json')
b=read('basis_result.json')
assert b['status']=='PASS_ALL_19_BIT_SOURCE_CODES' and b['codes_checked']==1<<19
assert len(b['pivots'])==len(b['code_images'])==len(b['product_images'])==19
rp=read('control_run_protocol.json')
for path,digest in rp['sources'].items():assert sha(Path(path))==digest,path
run=read('control_run_result.json')
assert run['status']=='EXIT_0' and run['exit_code']==0 and run['stop_reason'] is None
assert run['protocol_sha256']==sha(HERE/'control_run_protocol.json')
for name,digest in run['sha256'].items():assert sha(HERE/name)==digest,name
c=read('control_result.json')
assert c['status']=='PASS_SELECTOR_ELIMINATED_CONSTRUCTED_CONTROL'
assert c['formula_sha256']==sha(HERE/'control.xcnf')
assert c['assignment_check']=={'clauses':c['clauses'],'native_xor_rows':c['native_xor_rows']}
assert c['protocol_sha256']==sha(HERE/'protocol.json')
proof=(HERE.parent/'n131_w20_selector_elimination_20261013/lean_check.log').read_text()
assert 'does not depend on any axioms' in proof and 'sorryAx' not in proof
print(json.dumps({'status':'PASS_SELECTOR_ELIMINATION_V2_RECEIPTS',
 'variables':c['variables'],'clauses':c['clauses'],'xor_rows':c['native_xor_rows'],
 'wall_ns':run['wall_ns'],'formula_sha256':c['formula_sha256']},sort_keys=True))
