"""Pin an ordinary N41 two-pair partial-sum feature-rank sample."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'protocol.json'
assert not out.exists()
paths = [HERE / 'sample_rank_sage.py', HERE / 'sage_runtime_info.json',
         ROOT / 'n41_w11_n131_w33_density_20261018' / 'n41_count_result.json']
record = {'status': 'FROZEN_BEFORE_N41_W11_PARTIAL_QUADRATIC_RANK',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'input_law': 'deterministic random distinct-code pairs of all 1124 signed W11 pair states in slots 3 and 4, Frobenius rotations 12 and 24',
          'sample_seed': 209641118, 'max_attempts': 4000,
          'wall_cap_seconds': 180,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
