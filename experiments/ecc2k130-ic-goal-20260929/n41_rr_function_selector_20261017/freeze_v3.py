"""Freeze selected-row formula against the first bounded query."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

base = json.loads((D/'protocol_v2.json').read_text())
first = json.loads((D/'query_result_v2.json').read_text())
assert first['status'] == 'BOUNDED_UNKNOWN'
assert first['protocol_sha256'] == sha(D/'query_protocol_v2.json')
protocol = dict(base)
protocol['schema'] = 3
protocol['builder_sha256'] = sha(D/'build_v3.py')
protocol['source_encoding'] = 'selected point row by native XOR with sequential at-most-one; six variable field-coordinate products'
protocol['predecessor_query_result_sha256'] = sha(D/'query_result_v2.json')
(D/'protocol_v3.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'protocol_v3.json'),
                  'builder_sha256':protocol['builder_sha256']}))
