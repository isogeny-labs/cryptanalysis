"""Pin an independent integer-field audit of the sampled rank certificate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = HERE / 'verify_protocol.json'
assert not out.exists()
paths = [HERE / 'verify_rank.py', HERE / 'protocol.json', HERE / 'result.json']
record = {'status': 'FROZEN_BEFORE_INDEPENDENT_N41_W11_PARTIAL_RANK_AUDIT',
          'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
