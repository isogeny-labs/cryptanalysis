"""Pin the two-pair target and source-collision fixture before construction."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'fixture_protocol.json'
assert not out.exists()
paths = [HERE / 'make_fixture_sage.py', HERE / 'sage_runtime_info.json',
         ROOT / 'n41_w11_fivepair_native_join_20261018' / 'audit_result.json',
         ROOT / 'n41_w11_fivepair_native_join_20261018' / 'join_input.tsv']
record = {'status': 'FROZEN_BEFORE_N41_W11_TWO_PAIR_RESIDUAL_FIXTURE',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
