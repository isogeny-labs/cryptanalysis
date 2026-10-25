"""Screen genuine saved Hecke BFS frontiers for short-shift closure."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'hecke-shift-radius-20261024'))
from short_shift import components_unweighted  # noqa: E402
sys.path.insert(0, str(ROOT / 'hecke-shift-density-20261024'))
from density_sweep import point_key, rank_sparse  # noqa: E402


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_NATURAL_PREFIX_REPLAY'
    paths = {
        'frontier': ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json',
        'seed': ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
        'rank_dependency': ROOT / 'hecke-shift-density-20261024/density_sweep.py',
        'graph_dependency': ROOT / 'hecke-shift-radius-20261024/short_shift.py',
    }
    frontier = json.loads(paths['frontier'].read_text())
    seed_data = json.loads(paths['seed'].read_text())
    reps = [tuple(rep) for rep in frontier['column_representatives']]
    index = {rep: i for i, rep in enumerate(reps)}
    assert len(index) == 3949
    curve = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
    origin = curve(0)
    def point(rep):
        return origin if rep == (-1, -1) else curve([*rep, 1])
    generator = 5 * point((1, 8630))
    assert 4021 * generator == origin
    projected = [5 * point(rep) for rep in reps]
    lookup = {point_key(q): i for i, q in enumerate(projected)}
    assert len(lookup) == 3949
    max_radius = max(protocol['shift_radii'])
    edges = {step: [] for step in range(1, max_radius + 1)}
    for source, q in enumerate(projected):
        moved = q
        for step in range(1, max_radius + 1):
            moved += generator
            hit = lookup.get(point_key(moved))
            if hit is not None:
                assert projected[hit] == moved
                edges[step].append((source, hit))
    selected = {index[tuple(rep)] for rep in frontier['boundary_representatives']['seed']}
    assert len(selected) == 564
    rows = [record['coefficients'] for record in seed_data['accepted_rows']]
    anchor = index[(1, 8630)]
    source_total = 0
    outcome = []
    for stage in frontier['stages']:
        layer = stage['layer']
        assert layer in protocol['stages']
        new_indices = {index[tuple(rep)] for rep in stage['new_representatives']}
        selected.update(new_indices)
        rows.extend(record['coefficients'] for record in stage['accepted_rows'])
        assert all(all(int(j) in selected for j in row) for row in rows)
        source_total += stage['source_count']
        for radius in protocol['shift_radii']:
            internal = [(i, j) for step in range(1, radius + 1) for i, j in edges[step]
                        if i in selected and j in selected]
            component, count = components_unweighted(selected, internal)
            reduced = []
            for row in rows:
                mapped = defaultdict(int)
                for j, coefficient in row.items():
                    mapped[component[int(j)]] += int(coefficient)
                reduced.append({j: value % 4021 for j, value in mapped.items() if value % 4021})
            reduced.append({component[anchor]: 1})
            incident = set().union(*(row.keys() for row in reduced))
            rank = rank_sparse(reduced)
            cell = {
                'layer': layer, 'radius': radius,
                'table_columns': len(selected),
                'cumulative_source_points': source_total,
                'cumulative_hecke_degree_queries': 2 * source_total,
                'verified_relation_rows': len(rows),
                'shift_lookup_probes': len(selected) * radius,
                'successful_shift_edges': len(internal),
                'shift_components': count,
                'zero_incidence_components': count - len(incident),
                'quotient_rank': rank,
                'residual_nullity': count - rank,
                'full_rank': rank == count,
                'column_sha256': sha256(','.join(map(str, sorted(selected))).encode()).hexdigest(),
            }
            outcome.append(cell)
            print(json.dumps(cell, sort_keys=True), flush=True)
    result = {
        'status': 'NATURAL_PREFIX_SCREEN_PRODUCED',
        'protocol_sha256': sha(protocol_path),
        'source_sha256': {label: sha(path) for label, path in paths.items()},
        'anchor_column': anchor,
        'outcomes': outcome,
        'candidate_id': None,
        'timing_claim': None,
    }
    (HERE / 'screen_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
