"""Read-only audit of the N41 exact/deferred SAT control receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(name):
    return json.loads((HERE / name).read_text())


def sources(protocol):
    for name, expected in protocol['sources'].items():
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path
        assert sha(path) == expected, name


def check_formula(variant, build):
    path = HERE / f'{variant}.xcnf'
    counts = build['counts']
    assert sha(path) == build['formula_sha256']
    assert path.stat().st_size == build['formula_bytes']
    with path.open() as stream:
        assert stream.readline().split() == [
            'p', 'cnf', str(counts['variables']),
            str(counts['clauses'] + counts['xor_rows'])]
        clauses = xors = 0
        for line in stream:
            assert line.endswith(' 0\n')
            if line.startswith('x'):
                xors += 1
            else:
                clauses += 1
    assert (clauses, xors) == (counts['clauses'], counts['xor_rows'])


def main():
    build_protocol = record('build_protocol.json')
    solver_protocol = record('solver_protocol.json')
    sources(build_protocol)
    sources(solver_protocol)
    assert build_protocol['oriented_point'] == [2105655159232, 891719206310]
    out = {}
    for variant in ('exact', 'deferred'):
        build = record(f'build_{variant}_result.json')
        result = record(f'solver_{variant}_result.json')
        assert build['status'] == 'PASS_N41_PUBLIC_RELATION_ASSIGNMENT'
        assert build['variant'] == result['variant'] == variant
        assert build['assignment_check'] == {
            'clauses': build['counts']['clauses'],
            'native_xor_rows': build['counts']['xor_rows']}
        assert build['protocol_sha256'] == sha(HERE / 'build_protocol.json')
        check_formula(variant, build)
        assert result['status'] == 'BOUNDED_UNKNOWN'
        assert result['stop_reason'] == 'WALL_CAP'
        assert result['solver_exit_code'] == -15
        assert result['wall_seconds'] >= solver_protocol['parent_wall_cap_seconds']
        assert result['sampled_peak_combined_rss_bytes'] < solver_protocol['rss_cap_bytes']
        assert not any(result[f'solver_terminal_{kind}'] for kind in
                       ('sat', 'unsat', 'indeterminate'))
        assert result['protocol_sha256'] == sha(HERE / 'solver_protocol.json')
        assert result['solver_stdout_sha256'] == sha(HERE / f'solver_{variant}.stdout')
        assert result['solver_stderr_sha256'] == sha(HERE / f'solver_{variant}.stderr')
        out[variant] = {'positive_assignment': 'PASS', 'search': result['status'],
                        'wall_seconds': result['wall_seconds'],
                        'counts': build['counts']}
    print(json.dumps({'status': 'PASS_N41_PAIRED_SAT_CAP_RECEIPTS',
                      'variants': out}, sort_keys=True))


if __name__ == '__main__':
    main()
