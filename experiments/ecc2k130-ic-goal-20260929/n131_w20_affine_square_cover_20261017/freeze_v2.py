"""Freeze second affine-cover sweep over weight-one and weight-two directions."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
prior = json.loads((D / 'result.json').read_text())
audit = json.loads((D / 'audit_result.json').read_text())
assert prior['status'] == 'PASS_EXACT_W20_AFFINE_COVER'
assert audit['status'] == 'PASS_INDEPENDENT_AFFINE_COVER'
record = {'schema': 2, 'candidate_id': None,
          'source_protocol_sha256': sha(D / 'protocol.json'),
          'source_audit_sha256': sha(D / 'audit_result.json'),
          'source_groups_sha256': sha(D / 'groups.tsv'),
          'worker_sha256': sha(D / 'run_v2.py'),
          'auditor_sha256': sha(D / 'audit_v2.py'),
          'directions': 'all selector masks of Hamming weight one or two, weight then numeric order',
          'greedy_order': 'ascending code; first active affine square in direction order',
          'pair_fallback': 'first active neighbor in the same direction order',
          'worker_count': 1, 'wall_cap_s': 600, 'rss_cap_bytes': 4*1024**3}
with (D / 'protocol_v2.json').open('x') as out:
    json.dump(record, out, indent=2, sort_keys=True); out.write('\n')
print(sha(D / 'protocol_v2.json'))
