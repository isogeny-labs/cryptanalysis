"""Recheck frozen all-aligned N41/N131 receipts and terminal statuses."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'verification_protocol.json').read_text())
assert protocol['status'] == 'FROZEN_BEFORE_ALL_ALIGNED_TERMINAL_AUDIT'
assert protocol['script_sha256'] == sha(Path(__file__))
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
for name in ('build_protocol.json', 'query_protocol.json',
             'probe_protocol.json'):
    nested = json.loads((HERE / name).read_text())
    for path, digest in nested.get('sources', {}).items():
        assert sha(path) == digest, (name, path)
    for record in nested.get('inputs', {}).values():
        assert sha(record['path']) == record['sha256'], (name, record['path'])
    if 'solver_sha256' in nested:
        assert sha(nested['solver']) == nested['solver_sha256']

transform = json.loads((HERE / 'transform_result.json').read_text())
n41 = json.loads((HERE / 'n41_audit_result.json').read_text())
build = json.loads((HERE / 'build_result.json').read_text())
control = json.loads((HERE / 'control_replay.json').read_text())
probe = json.loads((HERE / 'probe_result.json').read_text())
query = json.loads((HERE / 'query_result.json').read_text())
assert transform['rotations'] == build['aligned_rotations'] == [0] * 5
assert n41['status'] == 'PASS_ALL_ALIGNED_N41_PUBLIC_RELATION'
assert n41['distinct_folded_columns'] == 10
assert n41['raw_group_sum_verified'] and n41['subgroup_projection_verified']
assert control['status'] == 'PASS_CONSTRUCTED_INDEPENDENT_GROUP_REPLAY'
assert len(set(control['folded_orbit_ids'])) == 10
assert build['status'] == 'PASS_N131_W29_ALL_ALIGNED_COLLISION_EXACT_PUBLIC_CIRCUIT'
assert build['constructed_assignment_check'] == {
    'clauses': build['counts']['clauses'],
    'native_xor_rows': build['counts']['xor_rows']}
assert build['formula_sha256'] == sha(HERE / 'formula.xcnf')
assert build['input_wires_sha256'] == sha(HERE / 'input_wires.json')
assert build['policy_counts'] == {
    'collision_clauses': 20930, 'same_code_clauses': 0,
    'strict_order_clauses': 4}
assert probe['status'] == 'COMPLETE_PAIRED_N131_STAGE_PROBE'
assert probe['candidate_id'] is None
assert [row['label'] for row in probe['results']] == ['paired_aligned', 'all_aligned']
for row in probe['results']:
    assert row['status'] == 'BOUNDED_UNKNOWN' and row['stop_reason'] == 'WALL_CAP'
    assert row['stdout_sha256'] == sha(HERE / f"probe_{row['label']}.stdout")
    assert row['stderr_sha256'] == sha(HERE / f"probe_{row['label']}.stderr")
assert query['candidate_id'] is None
assert query['status'] == 'BOUNDED_UNKNOWN' and query['stop_reason'] == 'WALL_CAP'
assert query['worker_count'] == 1 and query['monitor_error'] is None
assert query['solver_stdout_sha256'] == sha(HERE / 'solver.stdout')
assert query['solver_stderr_sha256'] == sha(HERE / 'solver.stderr')
stream = (HERE / 'solver.stdout').read_text(errors='replace')
assert not any(line.startswith(('s SATISFIABLE', 's UNSATISFIABLE',
                                's INDETERMINATE', 'v ')) for line in stream.splitlines())
restarts = [line for line in stream.splitlines() if line.startswith('c rst')]
assert restarts and restarts[-1] == query['last_restart_line']
proof = (HERE / 'lean.stdout').read_text()
assert "'AllAlignedOrder.sort_preserves_sum' depends on axioms: [propext, Quot.sound]" in proof
assert "'AllAlignedOrder.sort_preserves_validity' depends on axioms: [propext, Quot.sound]" in proof
assert not (HERE / 'lean.stderr').read_bytes()
result = {
    'status': 'PASS_ALL_ALIGNED_TERMINAL_AUDIT', 'candidate_id': None,
    'n41_native_probe': n41['native_probe'],
    'n41_public_relation_verified': True,
    'n131_control_group_replay_verified': True,
    'n131_public_query_status': query['status'],
    'n131_public_query_stop_reason': query['stop_reason'],
    'n131_public_query_wall_seconds': query['query_parent_wall_seconds'],
    'n131_public_query_peak_rss_bytes': query['sampled_peak_combined_rss_bytes'],
    'n131_public_query_last_restart': query['last_restart_line'],
    'terminal_sat_unsat_lines': 0,
    'protocol_sha256': sha(HERE / 'verification_protocol.json'),
}
(HERE / 'terminal_audit.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
