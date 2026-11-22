"""Pin the exact free-code two-pair circuit before its build."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'build_protocol.json'
assert not out.exists()
paths = [HERE / 'build.py', HERE / 'fixture.json',
         HERE / 'sage_runtime_info.json',
         ROOT / 'n41_w9_lazy_source_20261017' / 'circuit.py',
         ROOT / 'n131_w18_allseed_fourpair_20261012' / 'fourpair_v2.py',
         ROOT / 'n131_w20_selector_elimination_v2_20261013' / 'selector.py']
record = {'status': 'FROZEN_BEFORE_N41_W11_EXACT_TWO_PAIR_BUILD',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'wall_cap_seconds': 120,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
