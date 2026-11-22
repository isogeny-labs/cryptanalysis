"""Pure-integer affine replay of regenerated stage-0 rows, rank, logs, and target."""
from collections import Counter, defaultdict, deque
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
P, R = 20023, 4021


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def decode(pair):
    return None if tuple(pair) == (-1, -1) else tuple(pair)


def key(point):
    return (-1, -1) if point is None else point


def on(point):
    if point is None:
        return True
    x, y = point
    return (y*y + y - x*x*x + x*x + 10*x + 20) % P == 0


def add(left, right):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2 + 1) % P == 0:
        return None
    if left == right:
        slope = ((3*x1*x1 - 2*x1 - 10) * pow((2*y1 + 1) % P, -1, P)) % P
    else:
        slope = ((y2 - y1) * pow((x2 - x1) % P, -1, P)) % P
    intercept = (y1 - slope*x1) % P
    x = (slope*slope + 1 - x1 - x2) % P
    y = (-slope*x - intercept - 1) % P
    answer = (x, y)
    assert on(answer)
    return answer


def mul(scalar, point):
    assert scalar >= 0
    answer = None
    while scalar:
        if scalar & 1:
            answer = add(answer, point)
        point = add(point, point)
        scalar >>= 1
    return answer


def rank(rows):
    pivots = {}
    for original in rows:
        row = {int(j): int(value) % R for j, value in original.items() if int(value) % R}
        while row:
            lead = min(row)
            if lead not in pivots:
                inverse = pow(row[lead], -1, R)
                pivots[lead] = {j: value * inverse % R for j, value in row.items()}
                break
            factor = row[lead]
            for j, value in pivots[lead].items():
                updated = (row.get(j, 0) - factor*value) % R
                if updated:
                    row[j] = updated
                else:
                    row.pop(j, None)
    return len(pivots)


def main():
    fresh_path, solve_path = HERE / 'fresh_result.json', HERE / 'solve_result.json'
    fresh, solved = json.loads(fresh_path.read_text()), json.loads(solve_path.read_text())
    protocol = json.loads((HERE / 'solve_protocol.json').read_text())
    assert fresh['status'] == 'PASS_FRESH_STAGE0_SOURCE_REBUILD'
    assert solved['fresh_source_sha256'] == sha(fresh_path)
    assert solved['protocol_sha256'] == sha(HERE / 'solve_protocol.json')
    frontier = json.loads((ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json').read_text())
    seed = json.loads((ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json').read_text())
    reps = [tuple(pair) for pair in fresh['column_representatives']]
    assert len(reps) == len(set(reps)) == 1760
    assert [tuple(pair) for pair in frontier['boundary_representatives']['seed']] == [tuple(pair) for pair in reps if tuple(pair) in {tuple(x) for x in frontier['boundary_representatives']['seed']}]
    assert set(tuple(pair) for pair in fresh['new_orbits']) == {tuple(pair) for pair in frontier['stages'][0]['new_representatives']}
    all_reps = [tuple(pair) for pair in frontier['column_representatives']]
    index = {rep: i for i, rep in enumerate(reps)}
    def canonical(records, saved=False):
        output = []
        for record in records:
            coeff = record['coefficients']
            if saved:
                coeff = {str(index[all_reps[int(j)]]): value for j, value in coeff.items()}
            output.append((tuple(record['source']), int(record['degree']),
                           tuple(sorted(tuple(q) for q in record['neighbours'])),
                           tuple(sorted((int(j), int(value)) for j, value in coeff.items()))))
        return sorted(output)
    assert canonical(fresh['seed_rows']) == canonical(seed['accepted_rows'], saved=True)
    assert canonical(fresh['frontier_rows']) == canonical(frontier['stages'][0]['accepted_rows'], saved=True)
    assert fresh['seed_status_counts'] == seed['status_counts']
    assert fresh['frontier_status_counts'] == frontier['stages'][0]['status_counts']
    rows = [record['coefficients'] for record in fresh['seed_rows'] + fresh['frontier_rows']]
    torsion = (5, 5)
    assert mul(5, torsion) is None
    generator = mul(5, (1, 8630))
    assert mul(R, generator) is None
    points = [mul(5, decode(rep)) for rep in reps]
    assert all(on(decode(rep)) for rep in reps)
    by_point = {point: i for i, point in enumerate(points)}
    assert len(by_point) == len(points)
    logs = solved['logs_by_column']
    assert len(logs) == len(points)
    assert all(mul(int(logs[i]), generator) == point for i, point in enumerate(points))
    assert all(sum(int(value) * int(logs[int(j)]) for j, value in row.items()) % R == 0 for row in rows)
    adjacency = defaultdict(list)
    edge_count = Counter()
    for i, point in enumerate(points):
        shifted = point
        for step in range(1, protocol['shift_radius'] + 1):
            shifted = add(shifted, generator)
            hit = by_point.get(shifted)
            if hit is not None:
                assert (logs[hit] - logs[i]) % R == step
                adjacency[i].append((hit, step))
                adjacency[hit].append((i, -step))
                edge_count[step] += 1
    assert {str(step): edge_count[step] for step in range(1, 4)} == solved['shift_edges_by_step']
    component, offset, label = {}, {}, 0
    for start in range(len(points)):
        if start in component:
            continue
        component[start], offset[start] = label, 0
        queue = deque([start])
        while queue:
            source = queue.popleft()
            for hit, step in adjacency[source]:
                expected = (offset[source] + step) % R
                if hit in component:
                    assert component[hit] == label and offset[hit] == expected
                else:
                    component[hit], offset[hit] = label, expected
                    queue.append(hit)
        label += 1
    assert label == solved['shift_components'] == 312
    reduced = []
    for row in rows:
        mapped = defaultdict(int)
        for j, coefficient in row.items():
            mapped[component[int(j)]] += int(coefficient)
        reduced.append({j: value % R for j, value in mapped.items() if value % R})
    anchor = index[(1, 8630)]
    reduced.append({component[anchor]: 1})
    assert rank(reduced) == solved['quotient_rank'] == label
    scalar = int.from_bytes(sha256(protocol['target_seed'].encode()).digest(), 'big') % R
    target = mul(scalar, generator)
    assert scalar == solved['target_scalar_fixture'] == solved['target_recovered_scalar']
    assert list(key(target)) == solved['target_point']
    shifted = target
    for target_offset in range(R):
        hit = by_point.get(shifted)
        if hit is not None:
            recovered = (logs[hit] - target_offset) % R
            assert recovered == scalar and mul(recovered, generator) == target
            break
        shifted = add(shifted, generator)
    assert target_offset == solved['target_lookup_offset']
    histogram = Counter()
    point = None
    for k in range(R):
        shifted = point
        for shift in range(R):
            hit = by_point.get(shifted)
            if hit is not None:
                assert (logs[hit] - shift) % R == k
                histogram[shift] += 1
                break
            shifted = add(shifted, generator)
        point = add(point, generator)
    assert point is None
    assert {str(j): value for j, value in sorted(histogram.items())} == solved['subgroup_offset_histogram']
    output = {'status': 'PASS_INTEGER_FRESH_STAGE0_REPLAY',
              'fresh_sha256': sha(fresh_path), 'solve_sha256': sha(solve_path),
              'seed_rows_replayed': len(fresh['seed_rows']),
              'frontier_rows_replayed': len(fresh['frontier_rows']),
              'shift_edges_replayed': sum(edge_count.values()),
              'quotient_rank': label, 'table_logs_replayed': len(logs),
              'target_scalar_replayed': recovered,
              'subgroup_targets_replayed': sum(histogram.values()),
              'subgroup_maximum_offset': max(histogram)}
    (HERE / 'validation.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps(output, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
