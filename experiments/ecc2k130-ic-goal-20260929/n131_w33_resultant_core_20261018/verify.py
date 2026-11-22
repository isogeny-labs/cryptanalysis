"""Check frozen N131 resultant-core, solver, replay, and proof receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def check_protocol(name):
    data = read(name)
    for source, expected in data['sources'].items():
        path = Path(source)
        if not path.is_absolute():
            path = WORKSPACE / path
        assert sha(path) == expected, source
    return data


def check_run(protocol_name, result_name, stem, expected_status, cap=None):
    protocol = check_protocol(protocol_name)
    result = read(result_name)
    assert result['protocol_sha256'] == sha(HERE / protocol_name)
    assert result['status'] == expected_status
    assert 0 < result['sampled_peak_combined_rss_bytes'] < protocol['rss_cap_bytes']
    assert result['stdout_sha256' if 'stdout_sha256' in result else 'solver_stdout_sha256'] == sha(HERE / (stem + '.stdout'))
    assert result['stderr_sha256' if 'stderr_sha256' in result else 'solver_stderr_sha256'] == sha(HERE / (stem + '.stderr'))
    if cap is not None:
        assert result['stop_reason'] == 'WALL_CAP'
        assert cap <= result['wall_seconds'] < cap + 2
    else:
        assert result['stop_reason'] is None
    return result


def main():
    check_protocol('protocol.json')
    first = read('build_0_result.json')
    assert first['status'] == 'PASS_N131_W33_RESULTANT_CORE'
    assert first['candidate_id'] is None
    assert first['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert first['counts'] == {'and_gates': 6841, 'variables': 11868,
                               'clauses': 20655, 'xor_rows': 4963,
                               'generic_mul_calls': 1, 'sparse_mul_calls': 4,
                               'sparse_pair_products': 6240,
                               'linear_squares': 4}
    assert first['positive_assignment_check'] == {'clauses': 20655,
                                                   'native_xor_rows': 4963}
    assert first['formula_sha256'] == sha(HERE / 'positive_core.xcnf')
    assert first['formula_bytes'] == (HERE / 'positive_core.xcnf').stat().st_size
    check_run('solver_protocol.json', 'solver_0_result.json',
              'solver_0', 'BOUNDED_UNKNOWN', 300)
    check_protocol('pin_protocol.json')
    pin = read('pin_build_result.json')
    assert pin['status'] == 'PASS_CORE_PIN_FIRST_FORMULA'
    assert pin['formula_sha256'] == sha(HERE / 'positive_core_pin_first.xcnf')
    assert pin['protocol_sha256'] == sha(HERE / 'pin_protocol.json')
    check_run('pin_solver_protocol.json', 'pin_result.json',
              'pin_solver', 'BOUNDED_UNKNOWN', 120)

    check_run('quadratic_protocol.json', 'quadratic_run_result.json',
              'quadratic', 'GB_COMPLETE')
    positive = read('quadratic_result.json')
    assert positive['protocol_sha256'] == sha(HERE / 'quadratic_protocol.json')
    assert positive['gb_polynomials'] == positive['pinned_bits'] == 32
    assert positive['recovered_second_code'] == positive['known_second_code'] == 16722
    check_protocol('replay_protocol.json')
    replay = read('replay_result.json')
    assert replay['status'] == 'PASS_INDEPENDENT_N131_CURVE_REPLAY'
    assert replay['protocol_sha256'] == sha(HERE / 'replay_protocol.json')
    assert replay['source_codes'] == [3, 16722]
    assert replay['target_point'] == first['target_point']
    assert replay['matching_branch_pairs'] == [
        {'first_branches': [0, 0], 'second_branches': [1, 0]}]

    check_run('public_quadratic_protocol.json',
              'public_quadratic_run_result.json',
              'public_quadratic', 'GB_COMPLETE')
    public = read('public_quadratic_result.json')
    assert public['protocol_sha256'] == sha(HERE / 'public_quadratic_protocol.json')
    assert public['first_code'] == 3 and public['unit_ideal_reported'] is True
    assert public['gb_polynomials'] == 1 and public['recovered_second_code'] is None
    assert public['target_point'] != first['target_point']

    lean = (HERE / 'lean_check.log').read_text()
    assert "axioms: [propext, Classical.choice, Quot.sound]" in lean
    assert 'sorryAx' not in lean and 'error:' not in lean
    code = (HERE / 'QuadraticSourceExpansion.lean').read_text()
    assert all(word not in code for word in ('sorry', 'admit', 'axiom '))
    print(json.dumps({'status': 'PASS_CORE_GB_REPLAY',
                      'positive_second_code': 16722,
                      'public_first_code_3': 'GB_UNIT_IDEAL_REPORTED',
                      'lean': 'CHECKED'}, sort_keys=True))


if __name__ == '__main__':
    main()
