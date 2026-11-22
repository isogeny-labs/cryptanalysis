"""Read-only verification of the deferred-source positive screen."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(name):
    return json.loads((HERE / name).read_text())


def check_sources(protocol):
    for name, expected in protocol['sources'].items():
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path
        assert digest(path) == expected, name


def check_formula():
    row = record('build_0_result.json')
    path = HERE / 'positive.xcnf'
    counts = row['counts']
    assert row['status'] == 'PASS_W33_DEFERRED_POSITIVE_CIRCUIT'
    assert digest(path) == row['formula_sha256']
    assert path.stat().st_size == row['formula_bytes']
    with path.open() as stream:
        header = stream.readline().split()
        assert header == ['p', 'cnf', str(counts['variables']),
                          str(counts['clauses'] + counts['xor_rows'])]
        clauses = xors = 0
        for line in stream:
            assert line.endswith(' 0\n')
            if line.startswith('x'):
                xors += 1
            else:
                clauses += 1
    assert (clauses, xors) == (counts['clauses'], counts['xor_rows'])
    return counts


def main():
    build_protocol = record('build_protocol.json')
    solver_protocol = record('solver_protocol.json')
    check_sources(build_protocol)
    check_sources(solver_protocol)
    positive_counts = check_formula()
    positive = record('build_0_result.json')
    assert positive['positive_assignment_check'] == {
        'clauses': positive_counts['clauses'],
        'native_xor_rows': positive_counts['xor_rows']}
    assert positive['protocol_sha256'] == digest(HERE / 'build_protocol.json')
    result = record('solver_0_result.json')
    assert result['status'] == 'BOUNDED_UNKNOWN'
    assert result['stop_reason'] == 'WALL_CAP'
    assert result['solver_exit_code'] == -15
    assert result['wall_seconds'] >= solver_protocol['parent_wall_cap_seconds']
    assert result['sampled_peak_combined_rss_bytes'] < solver_protocol['rss_cap_bytes']
    assert not any(result[f'solver_terminal_{kind}'] for kind in
                   ('sat', 'unsat', 'indeterminate'))
    assert result['protocol_sha256'] == digest(HERE / 'solver_protocol.json')
    assert result['solver_stdout_sha256'] == digest(HERE / 'solver_0.stdout')
    assert result['solver_stderr_sha256'] == digest(HERE / 'solver_0.stderr')
    assert not (HERE / 'public.xcnf').exists()
    print(json.dumps({'status': 'PASS_DEFERRED_W33_SCREEN_RECEIPT',
                      'positive_assignment_check': 'PASS',
                      'positive_search': result['status'],
                      'public_search': 'NOT_PROMOTED',
                      'counts': positive_counts}, sort_keys=True))


if __name__ == '__main__':
    main()
