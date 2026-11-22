"""Read-only verification of the frozen W33 construction and capped search."""
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


def check_formula(index):
    row = record(f'build_{index}_result.json')
    path = HERE / ('positive.xcnf' if index == 0 else 'public.xcnf')
    counts = row['counts']
    assert row['status'] == 'PASS_W33_FIVEPAIR_CIRCUIT'
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
    positive_counts = check_formula(0)
    assert positive_counts == check_formula(1)
    positive = record('build_0_result.json')
    assert positive['positive_assignment_check'] == {
        'clauses': positive_counts['clauses'],
        'native_xor_rows': positive_counts['xor_rows']}
    for index in (0, 1):
        assert record(f'build_{index}_result.json')['protocol_sha256'] == digest(
            HERE / 'build_protocol.json')
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
    assert not (HERE / 'solver_1_result.json').exists()
    assert not (HERE / 'public_gate.json').exists()
    print(json.dumps({'status': 'PASS_FROZEN_W33_CAP_RECEIPT',
                      'positive_assignment_check': 'PASS',
                      'positive_search': result['status'],
                      'public_search': 'GATED_UNRUN',
                      'counts': positive_counts}, sort_keys=True))


if __name__ == '__main__':
    main()
