"""Freeze root0 code-chart panel before determinant and certificate work."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009' / 'geometry.json'
WITNESS = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_audit_result.json'
RR = ROOT / 'n41_n131_sixpair_rr_root_span_20261016' / 'run.py'
LINEAR = ROOT / 'n41_n131_rr_code_family_span_20261017' / 'result_n41_root0.json'
AUDIT = ROOT / 'n41_rr_joint_box_rank_20261017' / 'audit.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


geometry = json.loads(GEOMETRY.read_text())
witness = json.loads(WITNESS.read_text())
linear = json.loads(LINEAR.read_text())
assert geometry['curve_id'] == 'EC1N41Ckb1h7d5e80d3c4d0'
assert witness['status'] == 'PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION'
assert linear['valid_charts'] == 35 and linear['exceptional_charts'] == 0
used = {column for row in witness['pair_rows'][1:] for column in row['columns']}
masks = [mask for mask in geometry['permitted_canonical_a']
         if not ({geometry['mask_columns'][str(mask)],
                  geometry['mask_columns'][str(mask ^ 56)]} & used)]
assert len(masks) == 35
positive_mask = witness['pair_rows'][0]['masks'][0]
assert positive_mask in masks
record = {'schema': 1, 'curve_id': geometry['curve_id'],
          'candidate_id': None,
          'target': witness['raw_target'],
          'root0_masks': masks, 'positive_mask': positive_mask,
          'fixed_slots': [row['state_id'] for row in witness['pair_rows'][1:]],
          'sign_policy': 'lower-y point at witness x root for five fixed slots; lower x root of every free code, both y signs of all six points',
          'feature_policy': 'all linear coordinate bits, then all distinct unordered quadratic bit products; no constant term',
          'sources': {str(path): sha(path) for path in
                      (GEOMETRY, WITNESS, RR, LINEAR, AUDIT)},
          'producer_sha256': sha(D / 'screen.py'),
          'one_worker': True, 'wall_cap_s': 180,
          'rss_cap_bytes': 4 * 1024**3}
(D / 'protocol.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(json.dumps({'protocol_sha256': sha(D / 'protocol.json'),
                  'root0_code_charts': len(masks), 'positive_mask': positive_mask}))
