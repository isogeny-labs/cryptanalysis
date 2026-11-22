"""Bind frozen affine chart, both independent audits, and proof output."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
files=['RESULT.md','PROOF_MAP.md','SpanObstruction.lean','lean-toolchain',
       'lean.stdout','lean.stderr','freeze.py','prepare.py','screen.py',
       'audit_sage.py','freeze_group.py','group_audit_sage.py',
       'freeze_columns.py','column_audit_sage.py','terminal_v1.json',
       'terminal.py','verify.py','protocol.json','sage_runtime_info.json',
       'panel.json','result.json','audit_result.json',
       'group_protocol.json','group_audit_result.json',
       'column_protocol.json','column_audit_result.json',
       'prepare.stdout','prepare.stderr','screen.stdout','screen.stderr',
       'audit.stdout','audit.stderr','group_audit.stdout','group_audit.stderr',
       'column_audit.stdout','column_audit.stderr']
p=json.loads((D/'protocol.json').read_text())
r=json.loads((D/'result.json').read_text())
a=json.loads((D/'audit_result.json').read_text())
g=json.loads((D/'group_audit_result.json').read_text())
c=json.loads((D/'column_audit_result.json').read_text())
assert r['status']=='COMPLETE_N131_AFFINE_RR_RANK_SCREEN'
assert a['status']=='PASS_INDEPENDENT_N131_AFFINE_RR_REPLAY'
assert g['status']=='PASS_INDEPENDENT_N131_AFFINE_GROUP_REPLAY'
assert c['status']=='PASS_INDEPENDENT_W23_FOLDED_COLUMNS'
record={'schema':1,'status':'PASS_AFFINE_RR_COMPONENT',
        'files':{name:sha(D/name) for name in files},
        'external':p['source_sha256']}
with (D/'terminal.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
print(sha(D/'terminal.json'))
