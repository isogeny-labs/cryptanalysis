"""Frozen fine-grid continuation of the original Hecke/shift density sweep."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARENT = ROOT / 'hecke-shift-density-20261024'
sys.path.insert(0, str(PARENT))
from density_sweep import components, point_key, rank_sparse  # noqa: E402


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_FINEGRID_SWEEP'
    paths = {
        'frontier': ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json',
        'seed': ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
        'producer_dependency': PARENT / 'density_sweep.py',
    }
    frontier, seed_data = (json.loads(paths[label].read_text()) for label in ('frontier', 'seed'))
    representatives = [tuple(rep) for rep in frontier['column_representatives']]
    assert len(representatives) == 3949
    rows = [r['coefficients'] for r in seed_data['accepted_rows']] + frontier['rows']
    curve = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
    origin = curve(0)
    def point(pair):
        return origin if pair == (-1, -1) else curve([*pair, 1])
    generator = 5 * point((1, 8630))
    assert 4021 * generator == origin
    projected = [5 * point(rep) for rep in representatives]
    by_point = {point_key(point): i for i, point in enumerate(projected)}
    assert len(by_point) == 3949
    edges = []
    for i, point in enumerate(projected):
        hit = by_point.get(point_key(point + generator))
        if hit is not None:
            assert projected[hit] == point + generator
            edges.append((i, hit))
    anchor = representatives.index((1, 8630))
    outcomes = []
    for seed in protocol['seeds']:
        order = sorted((i for i in range(3949) if i != anchor),
                       key=lambda i: sha256(f'hecke-shift-density/v1:{seed}:{i}'.encode()).digest())
        for size in protocol['table_sizes']:
            selected = {anchor, *order[:size - 1]}
            component, _, edge_count = components(selected, edges)
            count = max(component.values()) + 1
            quotient_rows = []
            retained_count = 0
            for row in rows:
                if any(int(j) not in selected for j in row):
                    continue
                retained_count += 1
                mapped = defaultdict(int)
                for j, coefficient in row.items():
                    mapped[component[int(j)]] += int(coefficient)
                quotient_rows.append({j: v % 4021 for j, v in mapped.items() if v % 4021})
            quotient_rows.append({component[anchor]: 1})
            incident = set().union(*(row.keys() for row in quotient_rows))
            rank = rank_sparse(quotient_rows)
            outcome = {
                'seed': seed, 'table_size': size,
                'subset_sha256': sha256(','.join(map(str, sorted(selected))).encode()).hexdigest(),
                'retained_relation_rows': retained_count,
                'available_shift_edges': edge_count,
                'shift_components': count,
                'zero_incidence_components': count - len(incident),
                'quotient_rank': rank,
                'residual_nullity': count - rank,
                'full_rank': rank == count,
            }
            assert outcome['residual_nullity'] >= outcome['zero_incidence_components']
            outcomes.append(outcome)
            print(json.dumps(outcome, sort_keys=True), flush=True)
    result = {
        'status': 'FINEGRID_SWEEP_PRODUCED',
        'protocol_sha256': sha(protocol_path),
        'source_sha256': {label: sha(path) for label, path in paths.items()},
        'full_table_shift_edges': len(edges), 'anchor_column': anchor,
        'outcomes': outcomes, 'candidate_id': None, 'timing_claim': None,
    }
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
