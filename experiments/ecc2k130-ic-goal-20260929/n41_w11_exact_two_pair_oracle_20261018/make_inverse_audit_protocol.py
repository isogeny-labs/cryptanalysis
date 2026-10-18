"""Freeze direct-group replay of the exact implicit membership oracle."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'inverse_audit_protocol.json'
assert not out.exists()
paths = [HERE / 'audit_inverse_sage.py', HERE / 'inverse_result.json',
         HERE / 'sage_runtime_info.json',
         ROOT / 'n41_w11_fivepair_native_join_20261018' / 'join_input.tsv']
record = {'status': 'FROZEN_BEFORE_N41_W11_IMPLICIT_ORACLE_GROUP_AUDIT',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
