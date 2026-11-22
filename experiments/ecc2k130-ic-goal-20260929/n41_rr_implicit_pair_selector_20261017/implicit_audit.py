"""Independent field/group replay of mask-generated source and query receipt."""
import hashlib
import importlib.util
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009' / 'geometry.json'
PREV = ROOT / 'n41_rr_function_selector_20261017'
SPEC = importlib.util.spec_from_file_location('rr_independent_field', PREV / 'audit.py')
field = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(field)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def halftrace(value):
    result = 0
    for _ in range(21):
        result ^= value
        square = field.mul(value, value)
        value = field.mul(square, square)
    return result


def endpoint(basis, mask):
    u = 0
    for bit, coefficient in enumerate(basis):
        if mask >> bit & 1:
            u ^= coefficient
    assert u not in (0, 1)
    x = field.inv(u) ^ 1
    assert x
    rhs = x ^ field.inv(field.mul(x, x))
    z = halftrace(rhs)
    assert field.mul(z, z) ^ z == rhs
    y = field.mul(x, z)
    assert field.mul(y, y) ^ field.mul(x, y) == field.mul(field.mul(x, x), x) ^ 1
    return (x, y), (x, y ^ x)


def rotate(point, count):
    x, y = point
    for _ in range(count):
        x, y = field.mul(x, x), field.mul(y, y)
    return x, y


def main():
    protocol = json.loads((D / 'implicit_build_protocol.json').read_text())
    build = json.loads((D / 'implicit_build_result.json').read_text())
    query_protocol = json.loads((D / 'implicit_query_protocol.json').read_text())
    query = json.loads((D / 'implicit_query_result.json').read_text())
    preflight = json.loads((D / 'implicit_result.json').read_text())
    assert protocol['source_sha256'] == sha(SOURCE)
    assert protocol['geometry_sha256'] == sha(GEOMETRY)
    assert protocol['implicit_result_sha256'] == sha(D / 'implicit_result.json')
    assert protocol['builder_sha256'] == sha(D / 'implicit_build.py')
    assert build['status'] == 'IMPLICIT_SOURCE_BUILD_AND_WITNESS_PASS'
    assert build['protocol_sha256'] == sha(D / 'implicit_build_protocol.json')
    assert query_protocol['base_protocol_sha256'] == sha(D / 'implicit_build_protocol.json')
    assert query_protocol['query_runner_sha256'] == sha(D / 'implicit_query.py')
    assert query_protocol['build_result_sha256'] == sha(D / 'implicit_build_result.json')
    assert query['protocol_sha256'] == sha(D / 'implicit_query_protocol.json')
    assert query['stdout_sha256'] == sha(D / 'implicit_solver.stdout')
    assert query['stderr_sha256'] == sha(D / 'implicit_solver.stderr')
    assert query['status'] == 'BOUNDED_UNKNOWN' and query['parent_cap']
    assert query['peak_child_rss_bytes'] < protocol['rss_boundary_bytes']
    assert not [line for line in (D / 'implicit_solver.stdout').read_text().splitlines()
                if line.startswith(('s SATISFIABLE', 's UNSATISFIABLE'))]

    geometry = json.loads(GEOMETRY.read_text())
    assert geometry['fixed_seed_sum_code'] == 56
    assert geometry['rotations'][:6] == [0, 6, 12, 18, 24, 30]
    permitted = geometry['permitted_canonical_a']
    assert len(permitted) == 40
    basis = geometry['blocks'][0]['basis']
    lines = SOURCE.read_text().splitlines()
    target = tuple(map(int, lines[0].split()[3:5]))
    assert list(target) == protocol['target']
    states = {}
    for line in lines[1:]:
        parts = line.split()
        slot, state = map(int, parts[1:3])
        assert (slot, state) not in states
        states[slot, state] = {'point': tuple(map(int, parts[9:11])),
                               'columns': tuple(map(int, parts[7:9]))}
    assert len(states) == 960
    mapping = {}
    for code, a in enumerate(permitted):
        assert not a & (1 << 5)
        pa = endpoint(basis, a)
        pb = endpoint(basis, a ^ 56)
        for slot, rotation in enumerate(geometry['rotations'][:6]):
            by_point = {states[slot, 4 * code + s]['point']: 4 * code + s
                        for s in range(4)}
            assert len(by_point) == 4
            hits = []
            for sign_a in range(2):
                for sign_b in range(2):
                    point = field.add(rotate(pa[sign_a], rotation),
                                      rotate(pb[sign_b], rotation))
                    assert point in by_point
                    hits.append(by_point[point])
            assert len(set(hits)) == 4
            mapping[f'{slot}:{code}'] = hits
    assert mapping == preflight['code_sign_to_archived_state']
    witness = (12, 122, 116, 47, 128, 34)
    total = None
    columns = []
    for slot, state in enumerate(witness):
        total = field.add(total, states[slot, state]['point'])
        columns.extend(states[slot, state]['columns'])
    assert total == target and len(set(columns)) == 12
    assert len({states[slot, state]['point'][0] for slot, state in enumerate(witness)}
               | {target[0]}) == 7

    formula = D / 'implicit_formula.xcnf'
    assert build['formula_sha256'] == sha(formula)
    assert query_protocol['formula_sha256'] == sha(formula)
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
    result = {'status': 'INDEPENDENT_AUDIT_PASS',
              'source_sha256': sha(SOURCE),
              'geometry_sha256': sha(GEOMETRY),
              'independent_field_code_sha256': sha(PREV / 'audit.py'),
              'endpoint_points_checked': 160,
              'pair_outputs_checked': 960,
              'witness_group_sum': list(total),
              'distinct_columns': len(set(columns)),
              'formula_sha256': sha(formula),
              'variables': build['variables'],
              'cnf_clauses': clauses, 'native_xor_rows': xors,
              'query_status': query['status'],
              'query_wall_s': query['wall_s'],
              'peak_child_rss_bytes': query['peak_child_rss_bytes']}
    (D / 'implicit_audit_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
