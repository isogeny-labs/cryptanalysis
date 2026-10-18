"""Audit the frozen N41 gate, N131 build, group control, and public query."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


for name in ('build_protocol.json', 'query_protocol.json'):
    protocol = read(HERE / name)
    for path, digest in protocol['sources'].items():
        assert sha(path) == digest, (name, path)
    assert protocol['candidate_id'] is None

n41 = read(ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n41_result.json')
n41_audit = read(ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n41_audit_result.json')
assert n41['status'] == 'HIT_PENDING_SAGE_REPLAY'
assert n41_audit['status'] == 'PASS_INDEPENDENT_N41_ALIGNED_PUBLIC_RELATION'

collision = read(ROOT / 'n131_w29_folded_collision_20261018' / 'filter_result.json')
collision_audit = read(ROOT / 'n131_w29_folded_collision_20261018' / 'verification_result.json')
assert collision['distinct_valid_collision_pairs'] == 2093
assert collision_audit['status'] == 'PASS_INDEPENDENT_SAGE_ORBIT_AND_CURVE_VALIDITY_REPLAY'
assert collision_audit['distinct_valid_collision_pairs'] == 2093

build = read(HERE / 'build_result.json')
query = read(HERE / 'query_result.json')
control = read(HERE / 'control_replay.json')
assert build['status'] == 'PASS_N131_W29_ALIGNED_COLLISION_EXACT_PUBLIC_CIRCUIT'
assert build['formula_sha256'] == sha(HERE / 'formula.xcnf')
assert build['input_wires_sha256'] == sha(HERE / 'input_wires.json')
assert build['protocol_sha256'] == sha(HERE / 'build_protocol.json')
assert build['constructed_assignment_check'] == {
    'clauses': build['counts']['clauses'],
    'native_xor_rows': build['counts']['xor_rows']}
assert build['policy_counts'] == {
    'same_code_clauses': 10,
    'collision_clauses': 2*2093*10,
    'strict_order_clauses': 2}
assert build['self_maxrss_raw'] <= 4294967296
assert control['status'] == 'PASS_CONSTRUCTED_INDEPENDENT_GROUP_REPLAY'
assert control['matching_group_sign_choices'] > 0
assert len(set(control['folded_orbit_ids'])) == 10

assert query['status'] == 'BOUNDED_UNKNOWN'
assert query['stop_reason'] == 'WALL_CAP'
assert query['candidate_id'] is None
assert query['worker_count'] == 1
assert query['sampled_peak_combined_rss_bytes'] <= 4294967296
assert query['query_parent_wall_seconds'] >= 600
assert not any(query[key] for key in
               ('solver_terminal_sat', 'solver_terminal_unsat',
                'solver_terminal_indeterminate'))
assert query['protocol_sha256'] == sha(HERE / 'query_protocol.json')
assert query['solver_stdout_sha256'] == sha(HERE / 'solver.stdout')
assert query['solver_stderr_sha256'] == sha(HERE / 'solver.stderr')
assert abs(query['charged_stage_wall_seconds'] -
           (build['wall_seconds'] + query['query_parent_wall_seconds'])) < 1e-6

receipt = {
    'status': 'PASS_FROZEN_COLLISION_EXACT_PUBLIC_QUERY_AUDIT',
    'candidate_id': None,
    'curve_id': query['curve_id'],
    'n41_independent_control': n41_audit['status'],
    'n131_collision_audit': collision_audit['status'],
    'n131_constructed_group_control': control['status'],
    'public_query_status': query['status'],
    'build_result_sha256': sha(HERE / 'build_result.json'),
    'query_result_sha256': sha(HERE / 'query_result.json'),
}
(HERE / 'verification_result.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps(receipt, sort_keys=True))
