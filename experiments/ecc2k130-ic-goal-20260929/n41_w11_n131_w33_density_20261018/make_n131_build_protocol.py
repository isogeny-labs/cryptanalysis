"""Freeze N131 W33 only after the independently replayed N41 public gate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
out = HERE / 'n131_build_protocol.json'
assert not out.exists()
n41_query = json.loads((HERE / 'n41_query_result.json').read_text())
n41_group = json.loads((HERE / 'n41_group_replay.json').read_text())
assert n41_query['status'] == 'SAT_MODEL_UNVERIFIED'
assert n41_group['status'] == 'PASS_N41_W11_INDEPENDENT_PUBLIC_RELATION'
assert n41_group['distinct_folded_columns'] == 10
control = ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n131_aligned_control.json'
public = ROOT / 'n131_w23_sixpair_public_sat_20261017' / 'protocol.json'
paths = [HERE / 'build_n131.py', HERE / 'sage_runtime_info.json',
         HERE / 'n41_query_result.json', HERE / 'n41_group_replay.json',
         HERE / 'n41_count_result.json', control, public,
         ROOT / 'n41_n131_fivepair_w9_w29_20261017' / 'circuit_n131_3p2.py',
         ROOT / 'n131_w23_sixpair_shared_circuit_20261017' / 'circuit.py',
         ROOT / 'n131_w18_allseed_fourpair_20261012' / 'fourpair_v2.py',
         ROOT / 'n131_w20_selector_elimination_v2_20261013' / 'selector.py']
record = {'status': 'FROZEN_AFTER_VERIFIED_N41_W11_BEFORE_N131_W33_BUILD',
          'candidate_id': None,
          'curve_id': 'EC1N131Ckb1heb5f1998f20b',
          'constructed_control': str(control),
          'public_point': str(public),
          'wall_cap_seconds': 240,
          'rss_cap_bytes': 4294967296,
          'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths}}
out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
