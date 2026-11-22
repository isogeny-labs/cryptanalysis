"""Freeze terminal verification of all native and Sage evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = HERE / 'verify_protocol.json'
assert not out.exists()
paths = [HERE / 'verify.py', HERE / 'prepare_protocol.json',
         HERE / 'prepare_result.json', HERE / 'query_protocol.json',
         HERE / 'query_result.json', HERE / 'audit_protocol.json',
         HERE / 'audit_result.json', HERE / 'projection_protocol.json',
         HERE / 'projection_result.json', HERE / 'join_input.tsv',
         HERE / 'join.stdout', HERE / 'join.stderr',
         HERE / 'PairTableFloor.lean', HERE / 'lean_check.log']
record = {'status': 'FROZEN_BEFORE_N41_NATIVE_RELATION_TERMINAL_VERIFY',
          'candidate_id': None,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
