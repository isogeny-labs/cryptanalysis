#!/usr/bin/env python3
"""Freeze terminal producer evidence and audit code before independent replay."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
sha = lambda name: hashlib.sha256((P / name).read_bytes()).hexdigest()
names = ['protocol.json', 'launch.json', 'stdout.txt', 'stderr.txt',
         'data/exp11_class_walk_D39_f6.json', 'sage_runtime.json',
         'tools/exp11_class_walk.py', 'tools/hecke11.py',
         'tools/validate.py', 'tools/degree_subset_audit.py',
         'tools/degree2_graph_audit.py']
assert all((P / name).exists() for name in names)
launch = json.loads((P / 'launch.json').read_text())
assert launch['status'] == 'PROCESS_COMPLETE' and launch['exit_code'] == 0
assert launch['result_sha256'] == sha('data/exp11_class_walk_D39_f6.json')
gate = {'status': 'FROZEN_BEFORE_D39_F6_AUDIT',
        'audit_sha256': sha('audit.py'), 'floor_sha256': sha('floor.py'),
        'files': {name: sha(name) for name in names}}
path = P / 'audit_protocol.json'
assert not path.exists()
path.write_text(json.dumps(gate, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': gate['status'], 'files': len(names),
                  'audit_protocol_sha256': sha('audit_protocol.json')}))
