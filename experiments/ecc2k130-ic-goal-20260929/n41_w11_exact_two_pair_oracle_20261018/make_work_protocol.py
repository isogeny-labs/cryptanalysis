"""Freeze exact work accounting for serial implicit-oracle reuse."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'work_protocol.json'
assert not out.exists()
paths = [HERE / 'work_projection.py', HERE / 'inverse_result.json',
         HERE / 'inverse_audit_result.json',
         ROOT / 'n41_w11_fivepair_native_join_20261018' / 'join.cpp',
         ROOT / 'n41_w11_fivepair_native_join_20261018' / 'query_result.json',
         ROOT / 'n41_w11_fivepair_native_join_20261018' / 'verification_result.json']
record = {'status': 'FROZEN_BEFORE_N41_W11_SERIAL_ORACLE_WORK_LEDGER',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
