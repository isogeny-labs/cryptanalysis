"""Replay signed degree-2 incidence components over the integers."""
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(rows, nonfloor):
    owners = defaultdict(list)
    parent = {i: i for i in rows}

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, row in rows.items():
        for column in row:
            if column in nonfloor:
                owners[column].append(i)
    for incident in owners.values():
        for i in incident[1:]:
            parent[root(i)] = root(incident[0])
    grouped = defaultdict(list)
    for i in rows:
        grouped[root(i)].append(i)
    return list(grouped.values()), owners


def signed_component(indices, rows, owners, floor):
    lower = {c for i in indices for c in rows[i] if c not in floor}
    if len(lower) != len(indices):
        return None, 'unequal row and lower-column counts'
    if any(sum(c in floor for c in rows[i]) != 1 for i in indices):
        return None, 'row floor incidence is not one'
    adjacency = defaultdict(list)
    for column in lower:
        incident = [(i, rows[i][column]) for i in owners[column]]
        if sorted(v for _, v in incident) != [1, 1, 2]:
            return None, 'lower incidence is not [1,1,2]'
        heavy = next(i for i, v in incident if v == 2)
        for light, v in incident:
            if v == 1:
                adjacency[heavy].append(light)
                adjacency[light].append(heavy)
    signs = {indices[0]: 1}
    queue = deque([indices[0]])
    while queue:
        i = queue.popleft()
        for other in adjacency[i]:
            required = -signs[i]
            if other in signs:
                if signs[other] != required:
                    return None, 'inconsistent signed cycle'
            else:
                signs[other] = required
                queue.append(other)
    if len(signs) != len(indices):
        return None, 'signed incidence disconnected'
    vector = Counter()
    for i, sign in signs.items():
        for column, value in rows[i].items():
            vector[column] += sign*value
    vector = {c: v for c, v in vector.items() if v}
    if not set(vector) <= floor or set(vector.values()) - {-1, 1} or len(vector) != len(indices):
        return None, 'integer cancellation failed'
    return {'signed_rows': {str(i): v for i, v in sorted(signs.items())},
            'signed_floor_columns': {str(c): v for c, v in sorted(vector.items())}}, None


def main():
    source = HERE / 'data' / 'exp11_class_walk_D39_f6.json'
    conductor = HERE / 'conductor_audit.json'
    data = json.loads(source.read_text())
    receipt = json.loads(conductor.read_text())
    assert receipt['status'] == 'verified' and receipt['source_sha256'] == digest(source)
    floor = {i for i, d in enumerate(receipt['column_conductors']) if d == 6}
    nonfloor = set(range(64)) - floor
    degree2 = {index: {int(k): int(v) for k, v in row.items()}
               for index, row in enumerate(data['relation_rows']) if len(row) == 4 and sum(row.values()) == 5}
    groups, owners = components(degree2, nonfloor)
    accepted, rejected = [], []
    for group in groups:
        certificate, reason = signed_component(group, degree2, owners, floor)
        if certificate:
            accepted.append(certificate)
        else:
            rejected.append({'rows': len(group), 'reason': reason})
    covered = Counter(int(k) for c in accepted for k in c['signed_floor_columns'])
    assert len(degree2) == 32
    assert all(n == 1 for n in covered.values())
    result = {'status': 'verified', 'source_sha256': digest(source),
              'conductor_audit_sha256': digest(conductor),
              'graph_audit_source_sha256': digest(Path(__file__)),
              'degree2_rows': len(degree2), 'incidence_components': len(groups),
              'signed_floor_components': len(accepted),
              'component_sizes': [len(c['signed_rows']) for c in accepted],
              'floor_columns': len(floor), 'covered_floor_columns': len(covered),
              'rejected': rejected, 'certificates': accepted}
    (HERE / 'graph_audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'certificates'}, sort_keys=True))


if __name__ == '__main__':
    main()
