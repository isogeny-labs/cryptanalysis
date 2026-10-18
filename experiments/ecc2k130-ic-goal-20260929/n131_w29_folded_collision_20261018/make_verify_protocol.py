"""Freeze independent Sage replay of all collision cases."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = HERE / 'verify_protocol.json'
assert not out.exists()
paths = [HERE / 'verify_sage.py', HERE / 'audit_result.json',
         HERE / 'filter_result.json', HERE / 'sage_runtime_info.json']
record = {
    'status': 'FROZEN_BEFORE_INDEPENDENT_SAGE_COLLISION_REPLAY',
    'curve_id': 'EC1N131Ckb1heb5f1998f20b',
    'wall_cap_seconds': 120,
    'rss_cap_bytes': 4294967296,
    'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
