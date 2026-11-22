"""Read-only check of frozen functional root-table preflight and failed build."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((HERE/n).read_text())
p=read('protocol.json')
assert p['status']=='FROZEN_BEFORE_N41_W8_SELECTOR_CONTROL_AND_PUBLIC'
for path,digest in p['source_sha256'].items():assert sha(Path(path))==digest,path
assert sha(HERE/'preflight.json')==p['preflight_sha256']
a=read('preflight.json')
assert a['status']=='PASS_N41_W8_FUNCTIONAL_ROOT_PREFLIGHT'
assert (a['exact_pair_codes'],a['root_entries'],a['support_masks'])==(40,80,125)
rp=read('control_run_protocol.json')
for path,digest in rp['sources'].items():assert sha(Path(path))==digest,path
r=read('control_run_result.json')
assert r['status']=='EXIT_ERROR' and r['exit_code']==1
assert r['protocol_sha256']==sha(HERE/'control_run_protocol.json')
for name,digest in r['sha256'].items():assert sha(HERE/name)==digest,name
assert "NameError: name 'trace_basis' is not defined" in (HERE/'control.stderr').read_text()
assert not (HERE/'control_result.json').exists() and not (HERE/'public.xcnf').exists()
print(json.dumps({'status':'PASS_FUNCTIONAL_ROOT_V1_FAILURE_RECEIPT',
                  'exact_pair_codes':40,'root_entries':80,'run_status':r['status']},sort_keys=True))
