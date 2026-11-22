"""Exact embedded-source storage floor for extending this join to W33."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'projection_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
out = HERE / 'projection_result.json'
assert not out.exists()
assert json.loads((HERE / 'audit_result.json').read_text())['status'] == \
    'PASS_INDEPENDENT_N41_W11_FIVEPAIR_PUBLIC_RELATION'
w20 = json.loads((ROOT / 'n131_w20_sevenpair_gate_20261010' /
                  'count_result_v2.json').read_text())
native = json.loads((ROOT / 'n131_w20_code_trace_bitset_20261014' /
                     'native_result.json').read_text())
native_audit = json.loads((ROOT / 'n131_w20_code_trace_bitset_20261014' /
                           'terminal_verification.json').read_text())
w29 = json.loads((ROOT / 'n131_w29_folded_collision_20261018' /
                  'filter_result.json').read_text())
w29_audit = json.loads((ROOT / 'n131_w29_folded_collision_20261018' /
                        'verification_result.json').read_text())
assert w20['status'] == 'PASS_EXACT_W20_SEVEN_PAIR_SOURCE_SUPPORT'
assert native['status'] == 'COMPLETE_CODE_TRACE_BITSET'
assert native_audit['status'] == 'PASS_W20_CODE_TRACE_BITSET_TERMINAL_VERIFICATION'
assert w29['status'] == 'EXACT_VALID_N131_W29_FOLDED_COLLISION_PAIRS'
assert w29_audit['status'].startswith('PASS_')
assert w20['curve_id'] == w29['curve_id'] == protocol['curve_id']
assert w20['selected_seed_mask'] == 898618
assert w20['selected_valid_unordered_pairs_per_slot'] == native['valid_codes'] == 132045
assert w20['selected_same_column_pair_exclusions'] == 0
assert w29['distinct_valid_collision_pairs'] == 2093
w33_source = (ROOT / 'n41_w11_n131_w33_density_20261018' / 'build_n131.py').read_text()
design_source = (ROOT / 'n131_w23_sixpair_shared_circuit_20261017' / 'circuit.py').read_text()
assert 'design.WIDTH = 33' in w33_source
assert 'design.BITS = [bit for bit in range(33)' in w33_source
assert 'SEED_MASK=898618' in design_source
seed_bit = (898618).bit_length() - 1
w20_bits = [i for i in range(20) if i != seed_bit]
w33_bits = [i for i in range(33) if i != seed_bit]
assert len(w20_bits) == 19 and len(w33_bits) == 32
assert set(w20_bits).issubset(w33_bits)
valid = native['valid_codes']
collisions = w29['distinct_valid_collision_pairs']
ordered_distinct = valid*(valid-1)
minimum_compatible = ordered_distinct - 2*collisions
minimum_key_bytes = 16*minimum_compatible
cap = 4*1024**3
assert minimum_key_bytes > cap
result = {'status': 'PASS_N131_W33_NATIVE_PAIR_TABLE_STORAGE_EXCLUSION',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'embedded_w20_valid_codes': valid,
          'w20_free_bits': w20_bits, 'w33_free_bits': w33_bits,
          'maximum_folded_collision_pairs_in_subset': collisions,
          'minimum_ordered_distinct_column_pairs_one_state_per_code': minimum_compatible,
          'minimum_bytes_at_16_bytes_per_point_key': minimum_key_bytes,
          'four_gib_cap_bytes': cap,
          'minimum_key_storage_to_cap_ratio': str(minimum_key_bytes / cap),
          'bound_scope': 'one signed state per embedded W20 valid code; two-pair explicit table; 16 bytes per key only, excluding witness IDs, hash overhead and all other storage',
          'protocol_sha256': sha(HERE / 'projection_protocol.json')}
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'minimum_ordered_distinct_column_pairs_one_state_per_code',
                   'minimum_bytes_at_16_bytes_per_point_key',
                   'minimum_key_storage_to_cap_ratio')}, sort_keys=True))
