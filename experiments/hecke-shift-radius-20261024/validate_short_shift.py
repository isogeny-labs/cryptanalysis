"""Independent Sage point, graph, and matrix replay of short-shift radius cells."""
from hashlib import sha256
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, Graph, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def key(point):
    return (-1, -1) if point.is_zero() else (int(point[0]), int(point[1]))


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    result_path = HERE / 'result.json'
    result = json.loads(result_path.read_text())
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    sources = {
        'frontier': ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json',
        'seed': ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
        'logs': ROOT / 'hecke-l29-final-kernel-search-20261024/control_result.json',
    }
    saved = {label: json.loads(path.read_text()) for label, path in sources.items()}
    assert all(result['source_sha256'][label] == sha(sources[label]) for label in ('frontier', 'seed'))
    reps = [tuple(pair) for pair in saved['frontier']['column_representatives']]
    assert reps == [tuple(pair) for pair in saved['logs']['column_representatives']]
    logs = saved['logs']['results']['seed_plus_degree2_3_hecke']['logs_by_column']
    rows = [r['coefficients'] for r in saved['seed']['accepted_rows']] + saved['frontier']['rows']
    curve = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
    origin = curve(0)
    def point(rep):
        return origin if rep == (-1, -1) else curve([*rep, 1])
    generator = 5 * point((1, 8630))
    projected = [5 * point(rep) for rep in reps]
    lookup = {key(q): i for i, q in enumerate(projected)}
    assert len(lookup) == len(reps) == len(logs) == 3949
    assert all(int(logs[i]) * generator == projected[i] for i in range(3949))
    assert all(sum(int(v) * int(logs[int(j)]) for j, v in row.items()) % 4021 == 0 for row in rows)
    max_radius = max(protocol['shift_radii'])
    edges = {step: [] for step in range(1, max_radius + 1)}
    for source, q in enumerate(projected):
        for step in range(1, max_radius + 1):
            moved = q + step * generator
            hit = lookup.get(key(moved))
            if hit is not None:
                assert projected[hit] == moved
                assert (int(logs[hit]) - int(logs[source])) % 4021 == step
                edges[step].append((source, hit))
    assert {str(step): len(value) for step, value in edges.items()} == result['full_table_edges_by_step']
    anchor = reps.index((1, 8630))
    assert anchor == result['anchor_column'] and logs[anchor] == 1
    assert len(result['outcomes']) == len(protocol['seeds']) * len(protocol['table_sizes']) * len(protocol['shift_radii'])
    checked = []
    for cell in result['outcomes']:
        seed, size, radius = cell['seed'], cell['table_size'], cell['radius']
        assert seed in protocol['seeds'] and size in protocol['table_sizes'] and radius in protocol['shift_radii']
        order = sorted((i for i in range(3949) if i != anchor),
                       key=lambda i: sha256(f'hecke-shift-density/v1:{seed}:{i}'.encode()).digest())
        selected = {anchor, *order[:size - 1]}
        assert sha256(','.join(map(str, sorted(selected))).encode()).hexdigest() == cell['subset_sha256']
        internal = [(i, j) for step in range(1, radius + 1) for i, j in edges[step]
                    if i in selected and j in selected]
        graph = Graph()
        graph.add_vertices(selected)
        graph.add_edges(internal)
        groups = sorted((sorted(group) for group in graph.connected_components()), key=lambda group: group[0])
        group_of = {index: label for label, group in enumerate(groups) for index in group}
        retained = [row for row in rows if all(int(j) in selected for j in row)]
        entries = {}
        for i, row in enumerate(retained):
            for j, value in row.items():
                column = group_of[int(j)]
                entries[i, column] = (entries.get((i, column), 0) + int(value)) % 4021
        entries[(len(retained), group_of[anchor])] = 1
        active = {column for (_, column), value in entries.items() if value % 4021}
        reduced = matrix(GF(4021), len(retained) + 1, len(groups), entries, sparse=True)
        rank = int(reduced.rank())
        assert size * radius == cell['point_lookup_probes']
        assert len(internal) == cell['successful_directed_edges']
        assert size - len(groups) == cell['spanning_forest_edges']
        assert len(retained) == cell['retained_relation_rows']
        assert len(groups) == cell['shift_components']
        assert len(groups) - len(active) == cell['zero_incidence_components']
        assert rank == cell['quotient_rank'] and len(groups) - rank == cell['residual_nullity']
        assert (rank == len(groups)) == cell['full_rank']
        checked.append({'seed': seed, 'table_size': size, 'radius': radius,
                        'nullity': len(groups) - rank, 'components': len(groups)})
        print(json.dumps(checked[-1], sort_keys=True), flush=True)
    output = {
        'status': 'PASS_INDEPENDENT_SHORT_SHIFT_REPLAY',
        'source_sha256': {label: sha(path) for label, path in sources.items()},
        'result_sha256': sha(result_path),
        'full_table_edges_by_step_checked': {str(step): len(value) for step, value in edges.items()},
        'relation_rows_checked': len(rows),
        'table_logs_replayed': len(logs),
        'cells': checked,
    }
    (HERE / 'validation.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
