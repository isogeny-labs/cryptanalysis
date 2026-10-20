#!/usr/bin/env python3
"""Freeze exact certificate inputs and generated Lean source before build."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
sha = lambda name: hashlib.sha256((P / name).read_bytes()).hexdigest()
names = ['protocol.json', 'audit_protocol.json', 'validation_protocol.json',
         'data/exp11_class_walk_D39_f6.json', 'audit.json', 'floor.json',
         'validation.json', 'make_floor_lean.py', 'FloorSix.lean',
         'lean-toolchain', 'lakefile.toml', 'lake-manifest.json']
assert all((P / name).exists() for name in names)
gate = {'status': 'FROZEN_BEFORE_D39_F6_LEAN_BUILD',
        'mathlib_rev': '021c46bdd042f67b538b9f9871d556a93713a9a9',
        'files': {name: sha(name) for name in names}}
path = P / 'formal_protocol.json'
assert not path.exists()
path.write_text(json.dumps(gate, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': gate['status'], 'files': len(names),
                  'formal_protocol_sha256': sha('formal_protocol.json')}))
