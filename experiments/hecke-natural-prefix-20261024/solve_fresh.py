"""Solve the freshly rebuilt first-frontier log table and one frozen target."""
from collections import Counter, defaultdict, deque
from hashlib import sha256
import json
from pathlib import Path
import time
from sage.all import EllipticCurve, GF, matrix, vector

HERE = Path(__file__).resolve().parent
MOD = 4021


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def key(point):
    return (-1, -1) if point.is_zero() else (int(point[0]), int(point[1]))


def main():
    protocol_path = HERE / 'solve_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_FRESH_STAGE0_SOLVE'
    input_path = HERE / 'fresh_result.json'
    data = json.loads(input_path.read_text())
    assert data['status'] == 'PASS_FRESH_STAGE0_SOURCE_REBUILD'
    reps = [tuple(pair) for pair in data['column_representatives']]
    rows = [row['coefficients'] for row in data['seed_rows'] + data['frontier_rows']]
    assert len(reps) == 1760 and len(rows) == 1506
    curve = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
    origin = curve(0)
    def point(rep):
        return origin if rep == (-1, -1) else curve([*rep, 1])
    generator = 5 * point((1, 8630))
    assert 4021 * generator == origin
    projected = [5 * point(rep) for rep in reps]
    by_point = {key(q): i for i, q in enumerate(projected)}
    assert len(by_point) == 1760
    anchor = reps.index((1, 8630))
    t0 = time.monotonic_ns()
    adjacency = defaultdict(list)
    edge_count = Counter()
    for source, q in enumerate(projected):
        moved = q
        for step in range(1, protocol['shift_radius'] + 1):
            moved += generator
            hit = by_point.get(key(moved))
            if hit is not None:
                assert projected[hit] == moved
                adjacency[source].append((hit, step))
                adjacency[hit].append((source, -step))
                edge_count[step] += 1
    component, offset = {}, {}
    next_label = 0
    for start in range(len(reps)):
        if start in component:
            continue
        component[start], offset[start] = next_label, 0
        queue = deque([start])
        while queue:
            source = queue.popleft()
            for hit, step in adjacency[source]:
                expected = (offset[source] + step) % MOD
                if hit in component:
                    assert component[hit] == next_label and offset[hit] == expected
                else:
                    component[hit], offset[hit] = next_label, expected
                    queue.append(hit)
        next_label += 1
    assert next_label == 312
    t1 = time.monotonic_ns()
    field = GF(MOD)
    entries = {}
    rhs = []
    for row_number, row in enumerate(rows):
        constant = 0
        for j, coefficient in row.items():
            index, value = int(j), int(coefficient)
            column = component[index]
            entries[(row_number, column)] = entries.get((row_number, column), 0) + value
            constant += value * offset[index]
        rhs.append(field(-constant))
    entries[(len(rows), component[anchor])] = 1
    rhs.append(field(1 - offset[anchor]))
    system = matrix(field, len(rows) + 1, next_label, entries, sparse=False)
    right = vector(field, rhs)
    assert int(system.rank()) == next_label
    component_logs = system.solve_right(right)
    assert system * component_logs == right
    logs = [(int(component_logs[component[i]]) + offset[i]) % MOD for i in range(len(reps))]
    assert logs[anchor] == 1
    assert all(logs[i] * generator == projected[i] for i in range(len(reps)))
    assert all(sum(int(coefficient) * logs[int(j)] for j, coefficient in row.items()) % MOD == 0 for row in rows)
    t2 = time.monotonic_ns()
    target_scalar = int.from_bytes(sha256(protocol['target_seed'].encode()).digest(), 'big') % MOD
    target = target_scalar * generator
    target_point = key(target)
    # The target point is the sole input to the following interval.
    query_start = time.monotonic_ns()
    shifted = target
    recovered = None
    for shift in range(MOD):
        hit = by_point.get(key(shifted))
        if hit is not None:
            recovered = (logs[hit] - shift) % MOD
            break
        shifted += generator
    assert recovered is not None
    query_end = time.monotonic_ns()
    assert recovered * generator == target
    verify_end = time.monotonic_ns()
    assert recovered == target_scalar
    offsets = Counter()
    Q = origin
    for scalar in range(MOD):
        shifted = Q
        for shift_audit in range(MOD):
            hit = by_point.get(key(shifted))
            if hit is not None:
                assert (logs[hit] - shift_audit) % MOD == scalar
                offsets[shift_audit] += 1
                break
            shifted += generator
        else:
            raise AssertionError('subgroup point without table offset')
        Q += generator
    assert Q == origin and sum(offsets.values()) == MOD
    output = {
        'status': 'PASS_FRESH_STAGE0_SHIFT_SOLVE_AND_TARGET_REPLAY',
        'protocol_sha256': sha(protocol_path),
        'fresh_source_sha256': sha(input_path),
        'column_count': len(reps), 'relation_row_count': len(rows),
        'shift_edges_by_step': {str(step): edge_count[step] for step in range(1, protocol['shift_radius'] + 1)},
        'shift_lookup_probes': len(reps) * protocol['shift_radius'],
        'shift_components': next_label, 'quotient_rank': int(system.rank()),
        'logs_by_column': logs,
        'target_seed': protocol['target_seed'],
        'target_scalar_fixture': target_scalar,
        'target_point': target_point,
        'target_recovered_scalar': recovered,
        'target_lookup_offset': shift,
        'target_lookup_probes': shift + 1,
        'target_curve_additions': shift,
        'subgroup_offset_histogram': {str(j): count for j, count in sorted(offsets.items())},
        'subgroup_maximum_offset': max(offsets),
        'phase_wall_ns_diagnostic': {
            'shift_graph_and_component_build': t1 - t0,
            'matrix_rank_solve_and_table_replay': t2 - t1,
            'target_query_and_scalar_recovery': query_end - query_start,
            'target_recovery_check': verify_end - query_end,
        },
        'candidate_id': None, 'timing_claim': None,
    }
    (HERE / 'solve_result.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: output[k] for k in ('status', 'column_count', 'shift_components',
                                            'target_lookup_offset', 'subgroup_maximum_offset')},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
