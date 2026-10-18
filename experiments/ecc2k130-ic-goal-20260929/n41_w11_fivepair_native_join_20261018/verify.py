"""Bind the native hit, independent group replay and N131 storage gate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'verify_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
prepare = json.loads((HERE / 'prepare_result.json').read_text())
query = json.loads((HERE / 'query_result.json').read_text())
audit = json.loads((HERE / 'audit_result.json').read_text())
projection = json.loads((HERE / 'projection_result.json').read_text())
assert prepare['status'] == 'PASS_N41_W11_FIVEPAIR_NATIVE_INPUT'
assert prepare['input_sha256'] == sha(HERE / 'join_input.tsv')
assert prepare['signed_states_per_slot'] == 1124
assert query['status'] == 'N41_W11_NATIVE_RELATION_UNVERIFIED'
assert query['exit_code'] == 0 and query['stop_reason'] is None
assert query['monitor_error'] is None and query['worker_count'] == 1
assert query['parent_wall_seconds'] < 600
assert query['sampled_peak_combined_rss_bytes'] < 4*1024**3
assert query['stdout_sha256'] == sha(HERE / 'join.stdout')
assert query['stderr_sha256'] == sha(HERE / 'join.stderr')
assert len(query['stage_lines']) == 3 and len(query['hit']['state_ids']) == 5
assert 0 < query['hit']['online_query_seconds'] < query['parent_wall_seconds']
assert audit['status'] == 'PASS_INDEPENDENT_N41_W11_FIVEPAIR_PUBLIC_RELATION'
assert audit['target_point'] == prepare['target_point']
assert audit['distinct_folded_columns'] == audit['summand_count'] == 10
assert audit['raw_group_sum_matches_target']
assert audit['projected_subgroup_sum_matches_target']
assert audit['projected_target_nonidentity']
assert [row['state_id'] for row in audit['rows']] == query['hit']['state_ids']
assert projection['status'] == 'PASS_N131_W33_NATIVE_PAIR_TABLE_STORAGE_EXCLUSION'
assert projection['minimum_bytes_at_16_bytes_per_point_key'] > projection['four_gib_cap_bytes']
assert projection['minimum_ordered_distinct_column_pairs_one_state_per_code'] == \
    132045*132044-2*2093
lean_log = (HERE / 'lean_check.log').read_text()
assert 'sorryAx' not in lean_log
assert 'PairTableFloor.storage_floor_from_count' in lean_log
assert 'PairTableFloor.exact_key_floor' in lean_log
result = {'status': 'PASS_N41_NATIVE_PUBLIC_RELATION_AND_N131_STORAGE_GATE',
          'candidate_id': None, 'n41_curve_id': audit['curve_id'],
          'n131_curve_id': projection['curve_id'],
          'n41_relation_state_ids': query['hit']['state_ids'],
          'n41_distinct_folded_columns': audit['distinct_folded_columns'],
          'n41_query_online_seconds': query['hit']['online_query_seconds'],
          'n41_query_parent_wall_seconds': query['parent_wall_seconds'],
          'n131_minimum_key_bytes': projection['minimum_bytes_at_16_bytes_per_point_key'],
          'protocol_sha256': sha(HERE / 'verify_protocol.json')}
out = HERE / 'verification_result.json'
assert not out.exists()
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
