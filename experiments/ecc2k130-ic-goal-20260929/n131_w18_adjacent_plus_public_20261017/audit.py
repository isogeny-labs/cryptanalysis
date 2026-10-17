#!/usr/bin/env python3
"""Independent readback of the frozen plus-only adjacent N131 attempt."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARCHIVE = ROOT / 'n131_w18_tenpair_binary_frob_20261012'
TARGET = ROOT / 'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, sort_keys=True, indent=2)
        file.write('\n')


def paths():
    return {'script': HERE / 'audit.py', 'protocol': HERE / 'protocol.json',
            'plus_source': HERE / 'plus.py',
            'constructed_fixture': HERE / 'control_fixture.json',
            'control_sage_protocol': HERE / 'control_sage_protocol.json',
            'control_sage_audit': HERE / 'control_sage_audit.json',
            'control_result': HERE / 'control_result.json',
            'control_xcnf': HERE / 'control.xcnf',
            'query_result': HERE / 'query_result.json',
            'ordinary_xcnf': HERE / 'ordinary.xcnf',
            'solver_stdout': HERE / 'solver.stdout.txt',
            'solver_stderr': HERE / 'solver.stderr.txt',
            'public_workload': TARGET,
            'archived_unlinked_control': ARCHIVE / 'control_result.json',
            'archived_unlinked_query': ARCHIVE / 'query_result.json'}


def count_xcnf(path):
    counts = {'cnf': 0, 'xor': 0}
    with path.open() as file:
        header = file.readline().split()
        assert header[:2] == ['p', 'cnf']
        for line in file:
            if line.startswith('x '):
                counts['xor'] += 1
            else:
                assert line and not line.startswith('c')
                counts['cnf'] += 1
    assert counts['cnf'] + counts['xor'] == int(header[3])
    return int(header[2]), counts


def freeze():
    save('audit_protocol.json', {'status': 'FROZEN_ADJACENT_PLUS_N131_TERMINAL_AUDIT',
         'source_sha256': {name: sha(path) for name, path in paths().items()}})


def run():
    frozen = load('audit_protocol.json')
    assert frozen['status'] == 'FROZEN_ADJACENT_PLUS_N131_TERMINAL_AUDIT'
    assert frozen['source_sha256'] == {name: sha(path) for name, path in paths().items()}
    protocol, control, query = load('protocol.json'), load('control_result.json'), load('query_result.json')
    fixture, sage = load('control_fixture.json'), load('control_sage_audit.json')
    assert protocol['status'] == 'FROZEN_N131_ADJACENT_PLUS_TENPAIR_BEFORE_CONTROL_AND_QUERY'
    assert protocol['source_sha256']['runner'] == sha(HERE / 'plus.py')
    assert protocol['source_sha256']['constructed_fixture'] == sha(HERE / 'control_fixture.json')
    assert protocol['source_sha256']['constructed_sage_audit'] == sha(HERE / 'control_sage_audit.json')
    assert protocol['source_sha256']['solver'] == sha(Path('/opt/homebrew/bin/cryptominisat5'))
    assert protocol['target_choice_count'] == 524
    assert protocol['linked_slots'] == [0, 1]
    assert protocol['linked_rotation_gap'] == 1
    assert protocol['first_join'] == 'direct_adjacent_plus_reciprocal'
    assert protocol['source_sign_policy'] == 'same_signed_pair_point_in_linked_slots'
    assert protocol['distinct_folded_columns_required'] == 18
    assert sage['status'] == 'PASS_ADJACENT_PLUS_TENPAIR_SAGE_CONTROL'
    assert sage['distinct_folded_columns'] == 18
    assert sage['raw_target'] == fixture['target'] == control['target']
    assert control['status'] == 'PASS_ADJACENT_PLUS_TENPAIR_CONSTRUCTED_XCNF'
    assert control['assignment_check'] == {'clauses': control['formula']['clauses'],
                                           'native_xor_rows': control['formula']['native_xor_rows']}
    assert control['protocol_sha256'] == query['protocol_sha256'] == sha(HERE / 'protocol.json')
    for name, profile in (('control', control['formula']), ('ordinary', query['formula'])):
        path = HERE / (name + '.xcnf')
        assert sha(path) == profile['xcnf_sha256']
        assert path.stat().st_size == profile['xcnf_bytes']
        variables, counts = count_xcnf(path)
        assert variables == profile['variables']
        assert counts == {'cnf': profile['clauses'], 'xor': profile['native_xor_rows']}
    workload = json.loads(TARGET.read_text())
    assert workload['workload_id'] == protocol['workload_id'] == query['workload_id']
    assert workload['public_target'] == protocol['public_target'] == query['public_target']
    assert query['status'] in ('BOUNDED_UNKNOWN', 'SAT_PENDING_GROUP_REPLAY')
    assert query['worker_count'] == protocol['worker_count'] == 1
    assert query['solver_flags'] == protocol['solver_flags']
    assert sum(query['phase_ns'].values()) == query['target_dependent_attempt_ns']
    assert 0 < query['target_dependent_attempt_ns'] < 600_300_000_000
    assert query['peak_combined_rss_bytes_sampled'] < protocol['combined_rss_cap_bytes']
    stdout = (HERE / 'solver.stdout.txt').read_text(errors='replace')
    stderr = (HERE / 'solver.stderr.txt').read_text(errors='replace')
    assert query['stdout_sha256'] == sha(HERE / 'solver.stdout.txt')
    assert query['stderr_sha256'] == sha(HERE / 'solver.stderr.txt')
    assert not stderr and not (HERE / 'query.stderr').read_text()
    if query['status'] == 'BOUNDED_UNKNOWN':
        assert query['stop_reason'] == 'TOTAL_QUERY_TIMEOUT'
        assert 600_000_000_000 <= query['target_dependent_attempt_ns']
        assert query['solver_exit_code'] == -9 and not query['decoded_model_saved']
        assert not query['status_lines']
        assert not [line for line in stdout.splitlines() if line.startswith('s ')]
    else:
        assert query['stop_reason'] is None
        assert query['decoded_model_saved']
        assert 's SATISFIABLE' in stdout
    assert query['restart_rows'] == sum(line.startswith('c [') for line in stdout.splitlines())
    matrix_sizes = [line.strip() for line in stdout.splitlines()
                    if line.startswith('c [g ') and ' size:' in line]
    archived = json.loads((ARCHIVE / 'control_result.json').read_text())
    save('audit_result.json', {'status': 'PASS_ADJACENT_PLUS_N131_QUERY_AUDIT',
         'candidate_id': None, 'protocol_sha256': sha(HERE / 'audit_protocol.json'),
         'source_sha256': frozen['source_sha256'],
         'query_status': query['status'],
         'target_dependent_attempt_ns': query['target_dependent_attempt_ns'],
         'sampled_peak_rss_bytes': query['peak_combined_rss_bytes_sampled'],
         'solver_restart_rows': query['restart_rows'],
         'gaussian_matrix_size_log_lines': len(matrix_sizes),
         'control_and_gate_delta_vs_archive': control['formula']['and_gates'] - archived['formula']['and_gates'],
         'control_variable_delta_vs_archive': control['formula']['variables'] - archived['formula']['variables']})
    print('PASS_ADJACENT_PLUS_N131_QUERY_AUDIT')


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
