"""Read-only terminal replay of frozen five-pair source and query receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


protocol = load('verify_protocol.json')
assert protocol['status'] == 'FROZEN_BEFORE_TERMINAL_AUDIT'
for name, digest in protocol['source_sha256'].items():
    assert sha(HERE / name) == digest, name
assert load('orbit_audit_result.json')['status'] == 'PASS_INDEPENDENT_N41_W9_FIVEPAIR_PUBLIC_RELATION'
assert load('sample_audit_result.json')['status'] == 'PASS_INDEPENDENT_SAGE_W29_SAMPLE_REPLAY'
assert load('n131_model_control_result.json')['status'] == 'PASS_INDEPENDENT_W29_FIVEPAIR_CONSTRUCTED_CONTROL'
assert load('n131_model_control_result_3p2.json')['status'] == 'PASS_INDEPENDENT_W29_FIVEPAIR_CONSTRUCTED_CONTROL'
assert load('topology_audit_result.json')['status'] == 'PASS_TOPOLOGY_TERMINAL_AUDIT'
assert not (HERE / 'lean_v2.stderr').read_bytes()
lean_lines = (HERE / 'lean_v2.stdout').read_text().splitlines()
assert len(lean_lines) == 4 and all('does not depend on any axioms' in line for line in lean_lines)

query_rows = []
for suffix, formula_name, log_prefix in (
        ('', 'n131_ordinary.xcnf', 'n131_solver'),
        ('_3p2', 'n131_3p2_ordinary.xcnf', 'n131_3p2_solver')):
    frozen = load('n131_query_protocol' + suffix + '.json')
    result = load('n131_query_result' + suffix + '.json')
    assert result['protocol_sha256'] == sha(HERE / ('n131_query_protocol' + suffix + '.json'))
    assert result['curve_id'] == frozen['curve_id']
    assert result['workload_id'] == frozen['workload_id']
    assert result['public_target'] == frozen['public_target']
    assert result['raw_point'] == frozen['raw_point']
    assert result['worker_count'] == frozen['worker_count'] == 1
    assert result['formula_sha256'] == sha(HERE / formula_name)
    assert result['formula_bytes'] == (HERE / formula_name).stat().st_size
    assert result['solver_stdout_sha256'] == sha(HERE / (log_prefix + '.stdout'))
    assert result['solver_stderr_sha256'] == sha(HERE / (log_prefix + '.stderr'))
    assert sum(result['phase_ns'].values()) == result['target_dependent_attempt_ns']
    assert result['target_dependent_attempt_ns'] <= frozen['target_dependent_cap_seconds'] * 10**9
    assert result['sampled_peak_combined_rss_bytes'] < frozen['combined_rss_cap_bytes']
    assert not result['monitor_degraded']
    with (HERE / formula_name).open() as inp:
        header = inp.readline().split()
        assert header[:2] == ['p', 'cnf']
        variables, declared_rows = map(int, header[2:])
        cnf_rows = xor_rows = 0
        for line in inp:
            if line.startswith('x '):
                xor_rows += 1
            else:
                cnf_rows += 1
    assert variables == result['formula_counts']['variables']
    assert cnf_rows == result['formula_counts']['clauses']
    assert xor_rows == result['formula_counts']['xor_rows']
    assert declared_rows == cnf_rows + xor_rows
    output_lines = (HERE / (log_prefix + '.stdout')).read_text(errors='replace').splitlines()
    statuses = [line for line in output_lines if line.startswith('s ')]
    assert statuses == result['status_lines']
    assert sum(line.startswith('c rst') for line in output_lines) == result['restart_rows']
    if result['status'] == 'BOUNDED_UNKNOWN':
        assert not result['model_decoded']
        if result['stop_reason'] == 'TARGET_DEPENDENT_TIMEOUT':
            assert not statuses
        else:
            assert result['stop_reason'] is None
            assert statuses == ['s INDETERMINATE'] and result['solver_exit_code'] == 0
    elif result['status'] == 'SAT_PENDING_GROUP_REPLAY':
        model_name = 'n131_model_audit_result' + suffix + '.json'
        assert load(model_name)['status'] == 'PASS_INDEPENDENT_W29_FIVEPAIR_ORDINARY_RELATION'
    else:
        raise AssertionError(('unhandled result status', result['status']))
    query_rows.append({'topology': 'three_plus_two' if suffix else 'four_plus_one',
                       'status': result['status'],
                       'formula_sha256': result['formula_sha256'],
                       'target_dependent_attempt_ns': result['target_dependent_attempt_ns'],
                       'phase_ns': result['phase_ns'],
                       'sampled_peak_combined_rss_bytes': result['sampled_peak_combined_rss_bytes'],
                       'restart_rows': result['restart_rows']})

audit = {'status': 'PASS_W29_FIVEPAIR_TERMINAL_REPLAY',
         'curve_id': query_rows and load('n131_query_result.json')['curve_id'],
         'rows': query_rows, 'verify_protocol_sha256': sha(HERE / 'verify_protocol.json'),
         'auditor_sha256': sha(Path(__file__))}
with (HERE / 'verification.json').open('x') as out:
    json.dump(audit, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps(audit, sort_keys=True))
