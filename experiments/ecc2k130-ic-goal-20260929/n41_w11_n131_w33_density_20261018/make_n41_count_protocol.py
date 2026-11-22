"""Freeze a complete N41 W11 source population audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = HERE / 'n41_count_protocol.json'
assert not out.exists()
paths = [HERE / 'count_n41_sage.py', HERE / 'sage_runtime_info.json',
         HERE / 'n41_build_result.json']
record = {'status': 'FROZEN_BEFORE_EXACT_N41_W11_SOURCE_COUNT',
          'candidate_id': None,
          'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'wall_cap_seconds': 120,
          'rss_cap_bytes': 4294967296,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
