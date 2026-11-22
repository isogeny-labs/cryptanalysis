"""Freeze the N131 complete-miss lower bound from an audited subset."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'n131_projection_protocol.json'
assert not out.exists()
paths = [HERE / 'project_n131.py', HERE / 'verification_result.json',
         ROOT / 'n131_w20_sevenpair_gate_20261010' / 'count_result_v2.json',
         ROOT / 'n131_w20_code_trace_bitset_20261014' / 'native_result.json',
         ROOT / 'n41_w11_fivepair_native_join_20261018' / 'projection_result.json']
record = {'status': 'FROZEN_BEFORE_N131_W33_IMPLICIT_MISS_PROJECTION',
          'candidate_id': None, 'curve_id': 'EC1N131Ckb1heb5f1998f20b',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
