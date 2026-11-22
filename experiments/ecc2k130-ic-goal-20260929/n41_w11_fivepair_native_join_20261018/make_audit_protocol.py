"""Freeze independent checked-Sage relation replay before its run."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'audit_protocol.json'
assert not out.exists()
paths = [HERE / 'audit_sage.py', HERE / 'join_input.tsv',
         HERE / 'query_result.json', HERE / 'prepare_result.json',
         HERE / 'sage_runtime_info.json',
         ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n41_model_fixture.json']
record = {'status': 'FROZEN_BEFORE_INDEPENDENT_N41_W11_FIVEPAIR_AUDIT',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
