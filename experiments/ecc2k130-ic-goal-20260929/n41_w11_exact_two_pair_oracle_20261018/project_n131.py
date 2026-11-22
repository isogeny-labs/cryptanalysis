"""Exact embedded-W20 floor for one complete W33 inverse-oracle miss."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'n131_projection_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
out = HERE / 'n131_projection_result.json'
assert not out.exists()
source = json.loads((ROOT / 'n131_w20_sevenpair_gate_20261010' /
                     'count_result_v2.json').read_text())
count = json.loads((ROOT / 'n131_w20_code_trace_bitset_20261014' /
                    'native_result.json').read_text())
prior = json.loads((ROOT / 'n41_w11_fivepair_native_join_20261018' /
                    'projection_result.json').read_text())
assert source['status'] == 'PASS_EXACT_W20_SEVEN_PAIR_SOURCE_SUPPORT'
assert count['status'] == 'COMPLETE_CODE_TRACE_BITSET'
assert prior['status'] == 'PASS_N131_W33_NATIVE_PAIR_TABLE_STORAGE_EXCLUSION'
assert source['curve_id'] == prior['curve_id'] == protocol['curve_id']
assert source['selected_valid_unordered_pairs_per_slot'] == count['valid_codes'] == 132045
assert source['signed_pair_states_per_slot'] == 528180
assert prior['embedded_w20_valid_codes'] == count['valid_codes']
assert set(prior['w20_free_bits']).issubset(prior['w33_free_bits'])
result = {'status': 'PASS_N131_W33_IMPLICIT_COMPLETE_MISS_STATE_FLOOR',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'embedded_w20_valid_codes': count['valid_codes'],
          'embedded_w20_signed_pair_states': source['signed_pair_states_per_slot'],
          'minimum_first_pair_states_per_complete_w33_miss': source['signed_pair_states_per_slot'],
          'scope': 'complete miss in an exact serial inverse oracle that visits each signed first-pair state; no block rejection, caching or target-conditioned source compression',
          'protocol_sha256': sha(HERE / 'n131_projection_protocol.json')}
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
