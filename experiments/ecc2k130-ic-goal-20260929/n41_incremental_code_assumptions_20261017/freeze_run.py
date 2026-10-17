"""Bind the monitored runner after the native source has been frozen."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
record={'schema':1,'protocol_sha256':sha(D/'protocol.json'),
        'runner_sha256':sha(D/'run.py'),
        'runtime_info_sha256':sha(D/'sage_runtime_info.json')}
(D/'run_protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'run_protocol_sha256':sha(D/'run_protocol.json')}))
