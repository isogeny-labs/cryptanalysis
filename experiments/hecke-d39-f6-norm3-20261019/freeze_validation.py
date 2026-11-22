#!/usr/bin/env python3
"""Freeze both audit outcomes before the independent certificate replay."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
sha = lambda name: hashlib.sha256((P / name).read_bytes()).hexdigest()
names = ['protocol.json', 'audit_protocol.json', 'launch.json',
         'data/exp11_class_walk_D39_f6.json', 'audit.json', 'floor.json']
assert all((P / name).exists() for name in names)
gate = {'status': 'FROZEN_BEFORE_D39_F6_VALIDATION',
        'validator_sha256': sha('validate_floor.py'),
        'files': {name: sha(name) for name in names}}
path = P / 'validation_protocol.json'
assert not path.exists()
path.write_text(json.dumps(gate, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': gate['status'], 'files': len(names),
                  'validation_protocol_sha256': sha('validation_protocol.json')}))
