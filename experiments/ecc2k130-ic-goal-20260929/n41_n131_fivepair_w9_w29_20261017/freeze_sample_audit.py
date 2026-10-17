"""Freeze the independent Sage sample replay after the native sample."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


names = ['audit_w29_sage.py', 'sample_protocol.json',
         'sample_result.json', 'sage_runtime_info.json']
protocol = {'status': 'FROZEN_BEFORE_INDEPENDENT_SAMPLE_AUDIT',
            'samples': 65536, 'source_sha256': {name: sha(HERE / name) for name in names}}
with (HERE / 'sample_audit_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': protocol['status'], 'source_sha256': protocol['source_sha256']}))
