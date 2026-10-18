"""Freeze the native five-pair query after the complete input and build."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = HERE / 'query_protocol.json'
assert not out.exists()
paths = [HERE / 'run.py', HERE / 'join.cpp', HERE / 'join',
         HERE / 'compiler_version.txt', HERE / 'join_input.tsv',
         HERE / 'prepare_result.json', HERE / 'sage_runtime_info.json']
record = {'status': 'FROZEN_BEFORE_N41_W11_FIVEPAIR_NATIVE_QUERY',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'input_law': 'same frozen public N41 raw point, all W11 signed pair states free, five aligned slots, distinct folded columns',
          'query_seed': 411153130, 'max_probes': 20000000,
          'worker_count': 1, 'parent_wall_cap_seconds': 600,
          'rss_cap_bytes': 4294967296,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
