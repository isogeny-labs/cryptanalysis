"""Freeze exact source-product inverse membership on two N41 points."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'inverse_protocol.json'
assert not out.exists()
paths = [HERE / 'inverse_query_sage.py', HERE / 'fixture.json',
         HERE / 'sage_runtime_info.json',
         ROOT / 'n41_w11_n131_w33_density_20261018' / 'n41_count_result.json',
         ROOT / 'n41_w11_fivepair_native_join_20261018' / 'audit_result.json']
record = {'status': 'FROZEN_BEFORE_N41_W11_IMPLICIT_TWO_PAIR_ORACLE',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'input_law': 'verified two-pair relation residual, then frozen public raw point; all 281 valid first-pair codes and four signs scanned, second code recovered from its candidate output',
          'wall_cap_seconds': 180,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
