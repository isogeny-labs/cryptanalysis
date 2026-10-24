"""Frozen subset sweep: Hecke rows after exact generator-shift contraction."""
from collections import defaultdict, deque
from hashlib import sha256
import json
from pathlib import Path
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MOD = 4021


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def point_key(point):
    return (-1, -1) if point.is_zero() else (int(point[0]), int(point[1]))


def rank_sparse(rows):
    """Deterministic field elimination; rows are dicts of column:int."""
    pivots = {}
    for original in rows:
        row = {int(k): int(v) % MOD for k, v in original.items() if int(v) % MOD}
        while row:
            col = min(row)
            if col not in pivots:
                factor = pow(row[col], -1, MOD)
                pivots[col] = {k: v * factor % MOD for k, v in row.items()}
                break
            factor = row[col]
            for k, v in pivots[col].items():
                value = (row.get(k, 0) - factor * v) % MOD
                if value:
                    row[k] = value
                else:
                    row.pop(k, None)
    return len(pivots)


def components(subset, full_edges):
    adjacency = defaultdict(list)
    for source, hit in full_edges:
        if source in subset and hit in subset:
            adjacency[source].append((hit, 1))
            adjacency[hit].append((source, -1))
    component = {}
    offset = {}
    next_label = 0
    for start in sorted(subset):
        if start in component:
            continue
        label = next_label
        next_label += 1
        component[start], offset[start] = label, 0
        queue = deque([start])
        while queue:
            source = queue.popleft()
            for hit, delta in adjacency[source]:
                expected = (offset[source] + delta) % MOD
                if hit in component:
                    assert component[hit] == label and offset[hit] == expected
                else:
                    component[hit], offset[hit] = label, expected
                    queue.append(hit)
    return component, offset, sum(source in subset and hit in subset for source, hit in full_edges)


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_DENSITY_SWEEP'
    sources = {
        'frontier': ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json',
        'seed': ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
    }
    data = {name: json.loads(path.read_text()) for name, path in sources.items()}
    representatives = [tuple(pair) for pair in data['frontier']['column_representatives']]
    assert len(representatives) == 3949
    rows = [row['coefficients'] for row in data['seed']['accepted_rows']] + data['frontier']['rows']
    curve = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
    origin = curve(0)
    def point(pair):
        return origin if pair == (-1, -1) else curve([*pair, 1])
    generator = 5 * point((1, 8630))
    assert 4021 * generator == origin
    projected = [5 * point(rep) for rep in representatives]
    lookup = {point_key(q): i for i, q in enumerate(projected)}
    assert len(lookup) == len(representatives)
    anchor = representatives.index((1, 8630))
    full_edges = []
    for i, q in enumerate(projected):
        hit = lookup.get(point_key(q + generator))
        if hit is not None:
            assert projected[hit] == q + generator
            full_edges.append((i, hit))
    outcomes = []
    for seed in protocol['seeds']:
        ordering = sorted((i for i in range(len(representatives)) if i != anchor),
                          key=lambda i: sha256(f'hecke-shift-density/v1:{seed}:{i}'.encode()).digest())
        for table_size in protocol['table_sizes']:
            selected = {anchor, *ordering[:table_size - 1]}
            component, offset, edge_count = components(selected, full_edges)
            count = max(component.values()) + 1
            retained = []
            reduced = []
            for row in rows:
                if any(int(j) not in selected for j in row):
                    continue
                retained.append(row)
                mapped = defaultdict(int)
                for j, coefficient in row.items():
                    index = int(j)
                    mapped[component[index]] += int(coefficient)
                reduced.append({c: v % MOD for c, v in mapped.items() if v % MOD})
            reduced.append({component[anchor]: 1})
            rank = rank_sparse(reduced)
            outcome = {
                'seed': seed, 'table_size': table_size,
                'subset_sha256': sha256(','.join(map(str, sorted(selected))).encode()).hexdigest(),
                'retained_relation_rows': len(retained),
                'available_shift_edges': edge_count,
                'shift_components': count,
                'reduced_rank': rank,
                'residual_nullity': count - rank,
                'full_rank': rank == count,
            }
            outcomes.append(outcome)
            print(json.dumps(outcome, sort_keys=True), flush=True)
    result = {
        'status': 'DENSITY_SWEEP_PRODUCED', 'protocol_sha256': digest(protocol_path),
        'source_sha256': {name: digest(path) for name, path in sources.items()},
        'representatives_sha256': sha256(json.dumps(representatives).encode()).hexdigest(),
        'full_table_shift_edges': len(full_edges), 'anchor_column': anchor,
        'outcomes': outcomes, 'candidate_id': None, 'timing_claim': None,
    }
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
