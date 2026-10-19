"""Audit the frozen resultant and one-root norm experiment receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FULL = ROOT / 'n131_pair_resultant_circuit_20261019'
PREVIOUS = ROOT / 'n41_n131_triple_pair_20261019'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def audit_protocol(path):
    data = load(path)
    for source, digest in data['sources'].items():
        assert sha(source) == digest, (path, source)
    if 'script_sha256' in data:
        assert sha(path.parent / 'audit_sage.py') == data['script_sha256']
    return data


previous = load(PREVIOUS / 'query_result.json')
assert previous['status'] == 'BOUNDED_UNKNOWN'
assert previous['stop_reason'] == 'WALL_CAP'
assert previous['worker_count'] == 1
assert load(PREVIOUS / 'control_replay.json')['status'].startswith('PASS_')

variants = []
for directory, expected_status in (
    (FULL, 'PASS_N131_RESULTANT_PUBLIC_CIRCUIT'),
    (HERE, 'PASS_N131_ONE_ROOT_NORM_PUBLIC_CIRCUIT'),
):
    build_protocol = audit_protocol(directory / 'protocol.json')
    public_protocol = audit_protocol(directory / 'public_build_protocol.json')
    query_protocol = audit_protocol(directory / 'query_protocol.json')
    constructed = load(directory / 'build_result.json')
    public = load(directory / 'public_build_result.json')
    query = load(directory / 'query_result.json')
    assert constructed['candidate_id'] is public['candidate_id'] is query['candidate_id'] is None
    assert constructed['constructed_assignment_check']['clauses'] == constructed['counts']['clauses']
    assert constructed['constructed_assignment_check']['native_xor_rows'] == constructed['counts']['xor_rows']
    assert public['status'] == expected_status
    assert public['counts'] == constructed['counts']
    assert public['formula_sha256'] == sha(directory / 'formula.xcnf')
    assert public['input_wires_sha256'] == sha(directory / 'input_wires.json')
    assert query['status'] == 'BOUNDED_UNKNOWN'
    assert query['stop_reason'] == 'WALL_CAP'
    assert query['worker_count'] == query_protocol['worker_count'] == 1
    assert query['sampled_peak_combined_rss_bytes'] < query_protocol['rss_cap_bytes']
    assert query['query_parent_wall_seconds'] >= query_protocol['parent_wall_cap_seconds']
    assert query['query_parent_wall_seconds'] < query_protocol['parent_wall_cap_seconds'] + 1
    assert not query['solver_terminal_sat'] and not query['solver_terminal_unsat']
    assert query['solver_stdout_sha256'] == sha(directory / 'solver.stdout')
    assert query['solver_stderr_sha256'] == sha(directory / 'solver.stderr')
    assert query['protocol_sha256'] == sha(directory / 'query_protocol.json')
    assert build_protocol['curve_id'] == public_protocol['curve_id'] == query_protocol['curve_id']
    variants.append({'name': directory.name,
                     'counts': public['counts'],
                     'formula_sha256': public['formula_sha256'],
                     'query_status': query['status'],
                     'query_wall_seconds': query['query_parent_wall_seconds'],
                     'sampled_peak_rss_bytes': query['sampled_peak_combined_rss_bytes'],
                     'query_result_sha256': sha(directory / 'query_result.json')})

audit_protocol(HERE / 'audit_protocol.json')
independent = load(HERE / 'audit_result.json')
assert independent['status'] == 'PASS_INDEPENDENT_ONE_ROOT_NORM_AUDIT'
assert independent['n41_root_cases_checked'] == 78670
assert independent['n131_constructed_norm_zero']
assert independent['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
assert (HERE / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.34.1'
assert sha(HERE / 'PairResultant.lean') == sha(ROOT / 'n41_pair_resultant_filter_20261019/PairResultant.lean')
proof = (HERE / 'lean.stdout').read_text()
for theorem in ('norm_eq_two_f3', 'norm_zero_iff_one_f3'):
    assert theorem in proof
assert proof.count('[propext, Classical.choice, Quot.sound]') == 2
source = (HERE / 'OneRootNorm.lean').read_text()
for forbidden in ('sorry', 'admit', 'sorryAx', 'axiom '):
    assert forbidden not in source

result = {'status': 'PASS_N131_RESULTANT_NORM_TERMINAL_AUDIT',
          'candidate_id': None,
          'previous_status': previous['status'],
          'variants': variants,
          'independent_audit_sha256': sha(HERE / 'audit_result.json'),
          'lean_stdout_sha256': sha(HERE / 'lean.stdout'),
          'verifier_sha256': sha(__file__)}
(HERE / 'terminal_audit.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(result['status'])
