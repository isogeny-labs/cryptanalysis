"""Frozen radius sweep for short generator-shift closure."""
from collections import defaultdict, deque
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARENT = ROOT / 'hecke-shift-density-20261024'
sys.path.insert(0, str(PARENT))
from density_sweep import point_key, rank_sparse  # noqa: E402


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def components_unweighted(subset, edges):
    adjacency = defaultdict(list)
    for source, hit in edges:
        adjacency[source].append(hit)
        adjacency[hit].append(source)
    label_of = {}
    label = 0
    for start in sorted(subset):
        if start in label_of:
            continue
        label_of[start] = label
        queue = deque([start])
        while queue:
            source = queue.popleft()
            for hit in adjacency[source]:
                if hit not in label_of:
                    label_of[hit] = label
                    queue.append(hit)
        label += 1
    return label_of, label


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_SHORT_SHIFT_SWEEP'
    paths = {
        'frontier': ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json',
        'seed': ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
        'producer_dependency': PARENT / 'density_sweep.py',
    }
    frontier = json.loads(paths['frontier'].read_text())
    seed_data = json.loads(paths['seed'].read_text())
    reps = [tuple(pair) for pair in frontier['column_representatives']]
    assert len(reps) == 3949
    rows = [record['coefficients'] for record in seed_data['accepted_rows']] + frontier['rows']
    curve = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
    origin = curve(0)
    def point(pair):
        return origin if pair == (-1, -1) else curve([*pair, 1])
    generator = 5 * point((1, 8630))
    assert 4021 * generator == origin
    projected = [5 * point(rep) for rep in reps]
    lookup = {point_key(q): i for i, q in enumerate(projected)}
    assert len(lookup) == 3949
    edge_by_step = {step: [] for step in protocol['shift_radii']}
    for source, q in enumerate(projected):
        moved = q
        for step in range(1, max(protocol['shift_radii']) + 1):
            moved += generator
            hit = lookup.get(point_key(moved))
            if hit is not None:
                assert projected[hit] == moved
                edge_by_step[step].append((source, hit))
    anchor = reps.index((1, 8630))
    outcomes = []
    for seed in protocol['seeds']:
        order = sorted((i for i in range(3949) if i != anchor),
                       key=lambda i: sha256(f'hecke-shift-density/v1:{seed}:{i}'.encode()).digest())
        for size in protocol['table_sizes']:
            selected = {anchor, *order[:size - 1]}
            subset_sha = sha256(','.join(map(str, sorted(selected))).encode()).hexdigest()
            retained = [row for row in rows if all(int(j) in selected for j in row)]
            for radius in protocol['shift_radii']:
                edges = [edge for step in range(1, radius + 1) for edge in edge_by_step[step]
                         if edge[0] in selected and edge[1] in selected]
                component, count = components_unweighted(selected, edges)
                edge_count = len(edges)
                quotient_rows = []
                for row in retained:
                    mapped = defaultdict(int)
                    for j, coefficient in row.items():
                        mapped[component[int(j)]] += int(coefficient)
                    quotient_rows.append({j: v % 4021 for j, v in mapped.items() if v % 4021})
                quotient_rows.append({component[anchor]: 1})
                incident = set().union(*(row.keys() for row in quotient_rows))
                rank = rank_sparse(quotient_rows)
                outcome = {
                    'seed': seed, 'table_size': size, 'radius': radius,
                    'subset_sha256': subset_sha,
                    'retained_relation_rows': len(retained),
                    'point_lookup_probes': size * radius,
                    'successful_directed_edges': edge_count,
                    'spanning_forest_edges': size - count,
                    'shift_components': count,
                    'zero_incidence_components': count - len(incident),
                    'quotient_rank': rank,
                    'residual_nullity': count - rank,
                    'full_rank': rank == count,
                }
                assert outcome['residual_nullity'] >= outcome['zero_incidence_components']
                outcomes.append(outcome)
                print(json.dumps(outcome, sort_keys=True), flush=True)
    out = {
        'status': 'SHORT_SHIFT_SWEEP_PRODUCED',
        'protocol_sha256': sha(protocol_path),
        'source_sha256': {label: sha(path) for label, path in paths.items()},
        'full_table_edges_by_step': {str(step): len(edges) for step, edges in edge_by_step.items()},
        'anchor_column': anchor,
        'outcomes': outcomes,
        'candidate_id': None,
        'timing_claim': None,
    }
    (HERE / 'result.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
