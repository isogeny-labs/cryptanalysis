#!/usr/bin/env python3
"""Bind the generated independent Sage replay before execution."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / 'n41_w7_entropy_cubic_20261011/w8'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


paths = {'audit_source': HERE / 'audit_sage.py',
         'native_receipt': HERE / 'receipt.json',
         'stdout': HERE / 'stdout.log',
         'input': HERE / 'adjacent_input.tsv',
         'geometry': BASE / 'geometry.json',
         'fixture': BASE / 'fixture.json',
         'sage_runtime': HERE / 'sage_runtime_info.json'}
record = {'status': 'FROZEN_N41_ADJACENT_SAGE_REPLAY',
          'sha256': {name: sha(path) for name, path in paths.items()}}
with (HERE / 'audit_protocol.json').open('x') as file:
    json.dump(record, file, sort_keys=True, indent=2)
    file.write('\n')
print(record['status'])
