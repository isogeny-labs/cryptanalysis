"""Verify the frozen N41 functional S3 experiment receipts."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


protocols = ('n41_build_protocol.json', 'n41_query_protocol.json',
             'fixed_build_protocol.json', 'fixed_query_protocol.json',
             'direct_replay_protocol.json')
source_count = 0
for name in protocols:
    item = read(name)
    assert item['candidate_id'] is None
    for path, expected in item['sources'].items():
        assert sha(path) == expected, (name, path)
        source_count += 1
build = read('n41_build_result.json')
query = read('n41_query_result.json')
fixed_build = read('fixed_build_result.json')
fixed_query = read('fixed_query_result.json')
direct = read('direct_replay_result.json')
assert build['status'] == 'PASS_N41_W11_FUNCTIONAL_S3_CONSTRUCTED_CONTROL'
assert build['formula_sha256'] == sha(HERE / 'n41_formula.xcnf')
assert build['input_wires_sha256'] == sha(HERE / 'n41_input_wires.json')
assert build['constructed_assignment_check'] == {'clauses': 129763, 'native_xor_rows': 5272}
assert fixed_build['status'] == 'PASS_N41_FUNCTIONAL_S3_FIXED_CODES_OUTPUTS_CONTROL_BUILD'
assert fixed_build['formula_sha256'] == sha(HERE / 'fixed_formula.xcnf')
assert fixed_build['base_formula_sha256'] == build['formula_sha256']
assert fixed_build['additional_unit_clauses'] == 255
assert direct['status'] == 'PASS_N41_FUNCTIONAL_S3_DIRECT_FIXED_REPLAY'
assert direct['fixed_formula_sha256'] == fixed_build['formula_sha256']
assert direct['candidate_middle_tuples'] == 8 and direct['target_compatible_tuples'] == 1
for result, prefix, protocol in ((query, 'n41', 'n41_query_protocol.json'),
                                 (fixed_query, 'fixed', 'fixed_query_protocol.json')):
    assert result['candidate_id'] is None
    assert result['status'] == 'BOUNDED_UNKNOWN' and result['stop_reason'] == 'WALL_CAP'
    assert not any(result[f'solver_terminal_{x}'] for x in ('sat', 'unsat', 'indeterminate'))
    assert result['monitor_error'] is None and result['worker_count'] == 1
    assert result['protocol_sha256'] == sha(HERE / protocol)
    assert result['solver_stdout_sha256'] == sha(HERE / f'{prefix}_solver.stdout')
    assert result['solver_stderr_sha256'] == sha(HERE / f'{prefix}_solver.stderr')
lean = (HERE / 'lean.stdout').read_text()
assert "'FunctionalS3.functional_branch_exists' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
assert not (HERE / 'lean.stderr').read_text()
theorem = (HERE / 'FunctionalS3.lean').read_text()
assert re.search(r'\b(?:sorry|admit|sorryAx)\b', theorem) is None
result = {'status': 'PASS_N41_FUNCTIONAL_S3_TERMINAL_AUDIT',
          'candidate_id': None, 'protocols_verified': len(protocols),
          'source_hashes_verified': source_count,
          'ordinary_query_status': query['status'],
          'fixed_query_status': fixed_query['status'],
          'direct_replay_status': direct['status'],
          'proof_axioms': ['propext', 'Classical.choice', 'Quot.sound'],
          'script_sha256': sha(__file__)}
(HERE / 'terminal_audit.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
