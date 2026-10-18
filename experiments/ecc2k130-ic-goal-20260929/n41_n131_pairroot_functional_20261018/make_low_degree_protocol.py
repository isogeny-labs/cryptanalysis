"""Freeze source files and split for the low-degree interpolation falsifier."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
out = here/'low_degree_protocol.json'
assert not out.exists()
paths = [here/'low_degree.py', here/'n41_result.json', here/'n131_result.json']
record = {'status': 'FROZEN_BEFORE_QUADRATIC_SECTION_TEST',
          'candidate_id': None,
          'section': 'first halftrace pair root, prior to branch-bit addition',
          'n41_source_codes': 71, 'n131_training_codes': 448,
          'n131_rule': 'sort the 512 sampled integer codes and take the first 448; exclude two constructed controls',
          'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
