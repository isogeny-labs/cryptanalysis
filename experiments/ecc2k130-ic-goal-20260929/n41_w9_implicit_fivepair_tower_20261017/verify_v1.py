"""Verify frozen tower inputs, build controls, bounded statuses, and proof log."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


verification = read('verify_protocol.json')
assert verification['source_sha256']['script'] == sha(Path(__file__))
for name, expected in verification['artifact_sha256'].items():
    assert sha(HERE / name) == expected, name

fixture_sources = {
    'script': HERE / 'fixture_sage.py',
    'runtime': HERE / 'sage_runtime_info.json',
    'states': ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
}
build_sources = {
    'states': fixture_sources['states'], 'fixture': HERE / 'fixture.json',
    'tower': ROOT / 'n41_w8_three_code_resultant_20261015/tower_circuit.py',
    'prior': ROOT / 'n41_w8_quotient_first_pair_20261015/circuit.py',
    'norm': ROOT / 'n41_w8_quotient_first_pair_20261015/norm_gate_early.py',
    'runtime': HERE / 'builder_runtime_info.json',
    'selector': ROOT / 'n131_w20_selector_elimination_v2_20261013/selector.py',
    'linear': ROOT / 'n131_w20_output_inverse_linear_20261012/linear.py',
    'trace_runner': ROOT / 'n131_w20_inverse_trace_20261012/run.py',
    'ninepair_runner': ROOT / 'n131_fixed_seed_ninepair_cubic_20261011/run.py',
    'sevenpair': ROOT / 'n131_w20_sevenpair_gate_20261010/sevenpair_circuit.py',
    'fixed_pair': ROOT / 'n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py',
    'sparse': ROOT / 'n41_basis_aware_quartic_20261011/sparse.py',
    'karatsuba': ROOT.parent / 'koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py',
    'field': ROOT / 'n41_basis_aware_quartic_20261011/replay.py',
}
protocols = [
    ('fixture_protocol.json', 'fixture.json', fixture_sources),
    ('build_protocol_v2.json', 'build_result.json',
     {'script': HERE / 'build.py', **build_sources}),
    ('early_build_protocol.json', 'early_build_result.json',
     {'script': HERE / 'build_early_target.py', **build_sources}),
    ('pair_law_protocol.json', 'pair_law_result.json', {
        'script': HERE / 'audit_pair_law_sage.py',
        'runtime': HERE / 'pair_law_runtime_info.json',
        'states': fixture_sources['states'],
        'build': HERE / 'build_result.json',
        'early_build': HERE / 'early_build_result.json',
    }),
]
for protocol_name, result_name, paths in protocols:
    protocol = read(protocol_name)
    result = read(result_name)
    assert protocol['source_sha256'] == {k: sha(v) for k, v in paths.items()}
    assert result['protocol_sha256'] == sha(HERE / protocol_name)
    assert result['status'].startswith('PASS_')

initial = read('build_result.json')
early = read('early_build_result.json')
fixture = read('fixture.json')
pair = read('pair_law_result.json')
assert fixture['state_ids'] == [105, 244, 66, 47, 111]
assert fixture['code_bit_words'] == [93, 228, 60, 35, 95]
assert initial['witness_control']['all_clauses_and_xors_satisfied']
assert early['witness_control']['all_clauses_and_xors_satisfied']
assert pair['pair_code_rows_checked'] == 355
assert pair['signed_states_checked'] == 1420
for build, formula in ((initial, 'formula.xcnf'),
                       (early, 'formula_early.xcnf')):
    assert build['candidate_id'] is None
    assert build['formula_sha256'] == sha(HERE / formula)
    header = next(line for line in (HERE / formula).open()
                  if line.startswith('p cnf ')).split()
    assert int(header[2]) == build['variables']
    assert int(header[3]) == build['clauses'] + build['native_xor_rows']

query = read('query_protocol.json')
query_paths = {
    'script': HERE / 'run_solver.py',
    'runtime': HERE / 'query_runtime_info.json',
    'formula': HERE / 'formula.xcnf',
    'build': HERE / 'build_result.json',
    'wires': HERE / 'input_wires.json',
    'fixture': HERE / 'fixture.json',
    'solver': Path('/opt/homebrew/bin/cryptominisat5'),
}
assert query['source_sha256'] == {k: sha(v) for k, v in query_paths.items()}
assert query['worker_count'] == 1 and query['wall_cap_seconds'] == 600
assert query['rss_cap_bytes'] == 4*1024**3
failed = read('query_failure_v1.json')
assert failed['status'] == 'MONITOR_FAILURE_CHILD_CONFIRMED_LIVE'
assert failed['protocol_sha256'] == sha(HERE / 'query_protocol.json')
assert failed['stderr_sha256'] == sha(HERE / 'query.stderr')
first = read('query_result.json')
assert first['status'] == 'WALL_CAP_MONITOR_FAILURE'
assert first['resource_gate_status'] == 'UNVERIFIED_MONITOR_FAILURE'
assert first['solver_terminal_status'] is None and first['rss_peak_bytes'] is None
assert first['stdout_sha256'] == sha(HERE / 'solver.stdout')
assert first['query_protocol_sha256'] == sha(HERE / 'query_protocol.json')
assert 's SATISFIABLE' not in (HERE / 'solver.stdout').read_text()

early_query = read('early_query_protocol.json')
early_paths = {
    'script': HERE / 'run_early_solver.py',
    'runtime': HERE / 'early_query_runtime_info.json',
    'formula': HERE / 'formula_early.xcnf',
    'build': HERE / 'early_build_result.json',
    'wires': HERE / 'input_wires_early.json',
    'fixture': HERE / 'fixture.json',
    'solver': query_paths['solver'],
}
assert early_query['source_sha256'] == {k: sha(v) for k, v in early_paths.items()}
assert early_query['worker_count'] == 1 and early_query['wall_cap_seconds'] == 600
assert early_query['rss_cap_bytes'] == 4*1024**3
second = read('early_query_result.json')
assert second['status'] == 'WALL_CAP' and second['monitor_error'] is None
assert 600 <= second['parent_wall_seconds'] < 605
assert second['peak_sampled_process_tree_rss_bytes'] < 4*1024**3
assert second['returncode'] == -15
assert second['stdout_sha256'] == sha(HERE / 'solver_early.stdout')
assert second['protocol_sha256'] == sha(HERE / 'early_query_protocol.json')
assert 's SATISFIABLE' not in (HERE / 'solver_early.stdout').read_text()

proof = (HERE / 'TargetTowerSound.lean').read_text()
axioms = (HERE / 'lean_v2.stdout').read_text()
assert not (HERE / 'lean_v2.stderr').read_text()
assert 'sorry' not in proof and 'admit' not in proof
for declaration in ('f3_swap_middle', 'common_quadratic_root',
                    'right_target_f4_zero', 'right_root_product_zero'):
    assert f"'TargetTowerSound.{declaration}' depends on axioms: " in axioms
assert 'sorryAx' not in axioms
assert 'unsolved goals' in (HERE / 'lean_attempt_v1.stderr').read_text()

result = {
    'status': 'PASS_IMPLICIT_FIVEPAIR_TERMINAL_BINDINGS',
    'protocol_sha256': sha(HERE / 'verify_protocol.json'),
    'frozen_protocols_checked': len(protocols)+2,
    'pair_code_rows_checked': pair['pair_code_rows_checked'],
    'first_query_status': first['status'],
    'second_query_status': second['status'],
    'second_query_wall_seconds': second['parent_wall_seconds'],
}
(HERE / 'verification.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, sort_keys=True))
