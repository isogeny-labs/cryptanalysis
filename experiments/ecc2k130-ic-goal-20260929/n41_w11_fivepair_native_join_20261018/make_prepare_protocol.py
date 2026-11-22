"""Freeze the checked Sage producer before signed-state generation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'prepare_protocol.json'
assert not out.exists()
paths = [HERE / 'prepare_sage.py', HERE / 'sage_runtime_info.json',
         ROOT / 'n41_w11_n131_w33_density_20261018' / 'n41_count_result.json',
         ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n41_model_fixture.json']
record = {'status': 'FROZEN_BEFORE_N41_W11_FIVEPAIR_NATIVE_INPUT',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'input_law': 'all 281 exact canonical W11 codes, four signed pair outputs each, aligned rotations 0,0,12,12,24, frozen public N41 raw point',
          'check_seed': 41112018, 'addition_checks': 128,
          'wall_cap_seconds': 180,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
