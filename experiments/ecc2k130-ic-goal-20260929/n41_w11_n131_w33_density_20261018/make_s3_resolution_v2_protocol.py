"""Freeze Frobenius-corrected direct S3 resolution after first failure."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 's3_resolution_v2_protocol.json'
assert not out.exists()
paths = [HERE / 'resolve_s3_v2_n41.py',
         HERE / 's3_resolution_failure_0.json',
         HERE / 'fixed_roots_query_result.json',
         HERE / 'sage_runtime_info.json',
         ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n41_model_fixture.json',
         ROOT / 'n41_w9_lazy_source_20261017' / 'circuit.py',
         ROOT / 'n131_w18_allseed_fourpair_20261012' / 'fourpair_v2.py']
record = {'status': 'FROZEN_BEFORE_N41_W11_DIRECT_S3_RESOLUTION_V2',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'input_law': 'five independently verified pair reciprocal outputs, with frozen Frobenius rotations, on the public N41 point',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
