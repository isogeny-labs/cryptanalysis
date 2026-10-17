"""Pin independent folded-column reconstruction for selected W23 masks."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
record={'schema':1,'worker_count':1,'wall_cap_s':600,
        'panel_sha256':sha(D/'panel.json'),
        'source_sha256':sha(D/'column_audit_sage.py')}
with (D/'column_protocol.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
print(sha(D/'column_protocol.json'))
