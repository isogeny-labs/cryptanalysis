"""Independent 960-state ANF, curve-group, and frozen query receipt audit."""
import hashlib
import importlib.util
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
PREV = ROOT / 'n41_rr_function_selector_20261017'
SPEC = importlib.util.spec_from_file_location('rr_previous_independent_audit', PREV / 'audit.py')
old = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(old)
WITNESS = (12, 122, 116, 47, 128, 34)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((D / 'protocol.json').read_text())
    build = json.loads((D / 'build_result.json').read_text())
    query_protocol = json.loads((D / 'query_protocol.json').read_text())
    query = json.loads((D / 'query_result.json').read_text())
    formula = D / 'formula.xcnf'
    assert protocol['source_sha256'] == sha(SOURCE)
    assert protocol['builder_sha256'] == sha(D / 'build.py')
    assert protocol['predecessor_audit_sha256'] == sha(PREV / 'audit_result.json')
    assert build['protocol_sha256'] == sha(D / 'protocol.json')
    assert build['formula_sha256'] == sha(formula)
    assert query_protocol['base_protocol_sha256'] == sha(D / 'protocol.json')
    assert query_protocol['query_runner_sha256'] == sha(D / 'query.py')
    assert query_protocol['build_result_sha256'] == sha(D / 'build_result.json')
    assert query_protocol['formula_sha256'] == sha(formula)
    assert query['protocol_sha256'] == sha(D / 'query_protocol.json')
    assert query['stdout_sha256'] == sha(D / 'solver.stdout')
    assert query['stderr_sha256'] == sha(D / 'solver.stderr')
    assert query['status'] == 'BOUNDED_UNKNOWN' and query['parent_cap']
    assert query['peak_child_rss_bytes'] < protocol['rss_boundary_bytes']
    assert not [line for line in (D / 'solver.stdout').read_text().splitlines()
                if line.startswith(('s SATISFIABLE', 's UNSATISFIABLE'))]

    lines = SOURCE.read_text().splitlines()
    head = lines[0].split()
    assert head[:3] == ['ECC2K41', '6', '160']
    target = tuple(map(int, head[3:5]))
    assert list(target) == protocol['target']
    states = {}
    for line in lines[1:]:
        parts = line.split()
        assert parts[0] == 'S'
        slot, index = map(int, parts[1:3])
        key = slot, index
        assert key not in states
        states[key] = {'signs': tuple(map(int, parts[5:7])),
                       'code': tuple(map(int, parts[7:9])),
                       'point': tuple(map(int, parts[9:11]))}
    assert len(states) == 960
    cover_checks = 0
    for slot in range(6):
        for code in range(40):
            group = [states[slot, 4 * code + sign] for sign in range(4)]
            assert [entry['signs'] for entry in group] == [
                (0, 0), (0, 1), (1, 0), (1, 1)]
            assert len({entry['code'] for entry in group}) == 1
            rows = [old.row(entry['point']) for entry in group]
            for coordinate in range(7):
                v00, v01, v10, v11 = [row[coordinate] for row in rows]
                d_a = v00 ^ v10
                d_b = v00 ^ v01
                d_ab = v00 ^ v01 ^ v10 ^ v11
                for sign, expected in enumerate((v00, v01, v10, v11)):
                    a, b = divmod(sign, 2)
                    actual = v00 ^ (d_a if a else 0) ^ (d_b if b else 0) ^ (
                        d_ab if a and b else 0)
                    assert actual == expected
                    cover_checks += 1
    assert cover_checks == 960 * 7
    selected = [states[slot, state]['point'] for slot, state in enumerate(WITNESS)]
    total = None
    for point in selected:
        total = old.add(total, point)
    assert total == target
    columns = [column for slot, state in enumerate(WITNESS)
               for column in states[slot, state]['code']]
    assert len(set(columns)) == 12
    assert len({point[0] for point in selected + [(target[0], target[1] ^ target[0])]}) == 7

    with formula.open() as stream:
        header = stream.readline().split()
        assert header[:2] == ['p', 'cnf']
        assert int(header[2]) == build['variables']
        clauses = xors = 0
        for line in stream:
            if line.startswith('x '):
                xors += 1
            elif line and line[0] not in 'cp':
                clauses += 1
    assert clauses == build['cnf_clauses']
    assert xors == build['native_xor_rows']
    assert int(header[3]) == clauses + xors
    assert formula.stat().st_size == build['formula_bytes']
    result = {'status': 'AUDIT_PASS', 'source_sha256': sha(SOURCE),
              'independent_field_code_sha256': sha(PREV / 'audit.py'),
              'complete_source_states': len(states),
              'coordinate_anf_checks': cover_checks,
              'witness_group_sum': list(total), 'distinct_columns': 12,
              'formula_sha256': sha(formula), 'variables': build['variables'],
              'cnf_clauses': clauses, 'native_xor_rows': xors,
              'query_status': query['status'], 'query_wall_s': query['wall_s'],
              'peak_child_rss_bytes': query['peak_child_rss_bytes']}
    (D / 'audit_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
