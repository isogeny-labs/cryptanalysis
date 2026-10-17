"""Read-only terminal audit of the frozen W23 public SAT attempt."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
SOURCE = ROOT / 'n131_w23_sixpair_shared_circuit_20261017'
N41 = ROOT / 'n41_sixpair_shared_target_20261017'
PUBLIC = ROOT / 'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def check():
    protocol = read(BASE / 'protocol.json')
    result = read(BASE / 'result.json')
    assert protocol['status'] == 'FROZEN_W23_SIXPAIR_PUBLIC_BEFORE_QUERY'
    paths = {'script': BASE / 'run.py', 'circuit': SOURCE / 'circuit.py',
             'fixture': SOURCE / 'fixture.json',
             'source_protocol': SOURCE / 'protocol_v3.json',
             'source_build': SOURCE / 'result_v3.json',
             'source_verification': SOURCE / 'verification.json',
             'n41_relation': N41 / 'join_audit_result.json',
             'public': PUBLIC, 'runtime': BASE / 'sage_runtime_info.json',
             'solver': Path('/opt/homebrew/bin/cryptominisat5')}
    assert protocol['source_sha256'] == {key: sha(value) for key, value in paths.items()}
    assert result['protocol_sha256'] == sha(BASE / 'protocol.json')
    assert (protocol['curve_id'], protocol['workload_id'], protocol['worker_count'],
            protocol['target_dependent_cap_seconds'],
            protocol['combined_rss_cap_bytes']) == (
            'EC1N131Ckb1heb5f1998f20b', 'cc09e7eb202a', 1, 600, 4294967296)
    assert protocol['raw_point'] == read(PUBLIC)['preimages'][0]['point']
    assert read(SOURCE / 'result_v3.json')['target_public_point'] == protocol['raw_point']
    assert read(N41 / 'join_audit_result.json')['status'].startswith('PASS')
    assert (result['curve_id'], result['workload_id'], result['public_target'],
            result['raw_point'], result['raw_preimage_index']) == (
            protocol['curve_id'], protocol['workload_id'], protocol['public_target'],
            protocol['raw_point'], 0)
    assert result['candidate_id'] is None and result['worker_count'] == 1
    assert result['solver_command'] == [
        '/opt/homebrew/bin/cryptominisat5', *protocol['solver_flags'],
        str(BASE / 'ordinary.xcnf')]
    formula = BASE / 'ordinary.xcnf'
    assert result['formula_sha256'] == sha(formula)
    assert result['formula_bytes'] == formula.stat().st_size
    counts = result['formula_counts']
    assert (counts['variables'], counts['clauses'], counts['xor_rows']) == (
        127822, 263060, 38657)
    with formula.open('r') as stream:
        assert stream.readline().strip() == 'p cnf 127822 301717'
        cnf = xor = 0
        for line in stream:
            assert line.endswith(' 0\n') or line == '0\n'
            if line.startswith('x '):
                xor += 1
            else:
                cnf += 1
    assert (cnf, xor) == (counts['clauses'], counts['xor_rows'])
    phase = result['phase_ns']
    assert set(phase) == {'target_conversion_ns', 'formula_construction_ns',
                         'formula_serialization_ns', 'solver_search_ns',
                         'terminal_parse_and_model_check_ns'}
    assert all(isinstance(v, int) and v >= 0 for v in phase.values())
    assert sum(phase.values()) == result['target_dependent_attempt_ns']
    assert 0 < result['target_dependent_attempt_ns'] <= 600_000_000_000
    assert result['sampled_peak_combined_rss_bytes'] <= 4294967296
    assert result['solver_stdout_sha256'] == sha(BASE / 'solver.stdout')
    assert result['solver_stderr_sha256'] == sha(BASE / 'solver.stderr')
    raw = (BASE / 'solver.stdout').read_text(errors='replace')
    assert result['status_lines'] == [line for line in raw.splitlines()
                                      if line.startswith('s ')]
    assert result['restart_rows'] == sum(line.startswith('c rst')
                                         for line in raw.splitlines())
    assert result['monitor_degraded'] is False
    if result['status'] == 'BOUNDED_UNKNOWN':
        assert result['model_decoded'] is False
        assert not any(s in result['status_lines']
                       for s in ('s SATISFIABLE', 's UNSATISFIABLE'))
    elif result['status'] == 'SAT_PENDING_GROUP_REPLAY':
        assert result['model_decoded'] is True
        assert (BASE / 'decoded_model.json').exists()
        assert 's SATISFIABLE' in result['status_lines']
    elif result['status'] == 'UNSAT_UNVERIFIED':
        assert result['model_decoded'] is False
        assert 's UNSATISFIABLE' in result['status_lines']
    else:
        raise AssertionError(f'unexpected status: {result["status"]}')
    first = BASE / 'attempt1'
    failure = (first / 'query.stderr').read_text()
    assert 'assert t3 - t0 < 20_000_000_000' in failure
    assert sha(first / 'run.py') == read(first / 'protocol.json')['source_sha256']['script']
    assert (first / 'ordinary.xcnf').stat().st_size > 8_000_000
    control = read(BASE / 'model_control_result.json')
    assert control['status'] == 'PASS_INDEPENDENT_W23_CONSTRUCTED_MODEL_CONTROL'
    assert control['distinct_columns'] == 12
    assert control['enumerated_signed_combinations'] == 64
    assert len(control['group_hits']) == 1
    assert control['source_sha256'] == {
        'script': sha(BASE / 'audit_model_sage.py'),
        'protocol': sha(BASE / 'protocol.json'),
        'input': sha(SOURCE / 'fixture.json'),
        'runtime': sha(BASE / 'sage_runtime_info.json')}
    assert (BASE / 'model_control.stderr').stat().st_size == 0
    print('PASS_W23_PUBLIC_SAT_RECEIPT_AUDIT', result['status'],
          result['target_dependent_attempt_ns'] / 1e9)


if __name__ == '__main__':
    check()
