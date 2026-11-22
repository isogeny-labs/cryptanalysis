"""Versioned shorter CPU cap after the immutable pilot receipt."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
prior=json.loads((D/'protocol.json').read_text())
pilot=json.loads((D/'pilot_result.json').read_text())
assert pilot['status']=='PILOT_CENSORED'
record=dict(prior)
record['schema']=2
record['per_call_cpu_cap_s']=5
record['supersedes_protocol_sha256']=sha(D/'protocol.json')
record['pilot_result_sha256']=sha(D/'pilot_result.json')
(D/'protocol_v2.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
run={'schema':2,'protocol_sha256':sha(D/'protocol_v2.json'),
     'runner_sha256':sha(D/'run_v2.py'),
     'runtime_info_sha256':sha(D/'sage_runtime_info.json')}
(D/'run_protocol_v2.json').write_text(json.dumps(run,sort_keys=True,indent=2)+'\n')
print(json.dumps({'protocol_v2_sha256':sha(D/'protocol_v2.json'),
                  'run_protocol_v2_sha256':sha(D/'run_protocol_v2.json')}))
