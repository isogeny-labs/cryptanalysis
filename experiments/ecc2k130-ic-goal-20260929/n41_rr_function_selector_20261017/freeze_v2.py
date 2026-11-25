"""Freeze selected-row formula against the first bounded query."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

base = json.loads((D/'protocol.json').read_text())
first = json.loads((D/'query_result.json').read_text())
assert first['status'] == 'BOUNDED_UNKNOWN'
assert first['protocol_sha256'] == sha(D/'query_protocol.json')
protocol = dict(base)
protocol['schema'] = 2
protocol['builder_sha256'] = sha(D/'build_v2.py')
protocol['source_encoding'] = 'select one point row by native XOR, then evaluate six variable field-coordinate products'
protocol['predecessor_query_result_sha256'] = sha(D/'query_result.json')
(D/'protocol_v2.json').write_text(json.dumps(protocol,indent=2,sort_keys=True)+'\n')
print(json.dumps({'protocol_sha256':sha(D/'protocol_v2.json'),
                  'builder_sha256':protocol['builder_sha256']}))
