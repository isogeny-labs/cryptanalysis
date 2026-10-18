"""Freeze exact source roots and implementation before branch elimination."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
base = here.parent/'n41_n131_pairroot_functional_20261018'
out = here/'protocol.json'
assert not out.exists()
n41,n131 = base/'n41_result.json',base/'n131_result.json'
paths = [here/'run.py',n41,n131]
record = {'status': 'FROZEN_BEFORE_BRANCH_ADAPTIVE_QUADRATIC_SECTION_AUDIT',
          'candidate_id': None, 'n41_source': str(n41),
          'n131_source': str(n131),
          'input_law': 'all 71 sorted valid N41 source codes; all 512 sorted sampled valid N131 source codes; exclude N131 constructed controls',
          'branch_rule': 'one independently selectable bit for each source code, shared across all output coordinates',
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
