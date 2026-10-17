"""Freeze selected W20 source and deterministic affine-cover rules."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
SOURCE = D.parent / 'n131_w20_sevenpair_gate_20261010'
BASE = D.parent / 'n131_symbolic_rect_projection_20261015'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
count = json.loads((SOURCE / 'count_result_v2.json').read_text())
assert count['status'] == 'PASS_EXACT_W20_SEVEN_PAIR_SOURCE_SUPPORT'
record = {'schema': 1, 'candidate_id': None, 'curve_id': count['curve_id'],
          'selected_seed_mask': count['selected_seed_mask'],
          'expected_valid_codes': count['selected_valid_unordered_pairs_per_slot'],
          'direction_family': 'all coordinate-axis pairs among the 19 nonpivot selector bits',
          'greedy_order': 'ascending canonical code; ascending coordinate directions',
          'pair_fallback': 'first available coordinate neighbor, then singleton',
          'source_sha256': {'support': sha(SOURCE / 'support_w20.tsv'),
                            'count': sha(SOURCE / 'count_result_v2.json'),
                            'prefix_result': sha(BASE / 'prefix_result.json'),
                            'worker': sha(D / 'run.py'), 'auditor': sha(D / 'audit.py')},
          'worker_count': 1, 'wall_cap_s': 600,
          'rss_cap_bytes': 4 * 1024**3}
with (D / 'protocol.json').open('x') as out:
    json.dump(record, out, sort_keys=True, indent=2); out.write('\n')
print(sha(D / 'protocol.json'))
