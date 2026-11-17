#!/usr/bin/env python3
"""Attach precisely the prospective working-store raw inventory."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
p = argparse.ArgumentParser()
p.add_argument('record', type=Path)
a = p.parse_args()
record = a.record.resolve()
assert not json.loads(record.read_text())['raw']
plan = json.loads((P/'raw-reference-plan.json').read_text())
assert len(plan['paths']) == len(set(plan['paths'])) == plan['expected_references'] == 25
for name in plan['paths']:
    path = P/name
    path.resolve().relative_to(P.resolve())
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    uri = 's3://crypto-autoresearcher/store/sha256/'+h[:2]+'/'+h
    subprocess.run(['python3', 'tools/benchrec.py', 'add-raw', str(record), str(path.relative_to(ROOT)), '--s3-uri', uri], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
assert len(json.loads(record.read_text())['raw']) == 25
print('Attached exactly 25 predeclared raw references; upload verification is a separate gate')
