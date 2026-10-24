"""Independent finite-point and Sage-matrix replay of every frozen density cell."""
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
    paths = {
        'frontier': ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json',
        'seed': ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
        'logs': ROOT / 'hecke-l29-final-kernel-search-20261024/control_result.json',
    }
    saved = {label: json.loads(path.read_text()) for label, path in paths.items()}
    assert all(result['source_sha256'][label] == sha(paths[label]) for label in ('frontier', 'seed'))
    reps = [tuple(pair) for pair in saved['frontier']['column_representatives']]
    assert len(reps) == 3949 == len(saved['logs']['column_representatives'])
    assert reps == [tuple(pair) for pair in saved['logs']['column_representatives']]
    logs = saved['logs']['results']['seed_plus_degree2_3_hecke']['logs_by_column']
    rows = [row['coefficients'] for row in saved['seed']['accepted_rows']] + saved['frontier']['rows']
    curve = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
    origin = curve(0)
    def point(rep):
        return origin if rep == (-1, -1) else curve([*rep, 1])
    generator = 5 * point((1, 8630))
    projected = [5 * point(rep) for rep in reps]
    by_point = {key(q): i for i, q in enumerate(projected)}
    assert len(by_point) == 3949
    assert all(int(logs[i]) * generator == projected[i] for i in range(3949))
    assert all(sum(int(v) * int(logs[int(j)]) for j, v in row.items()) % 4021 == 0 for row in rows)
    edges = []
    for i, q in enumerate(projected):
        hit = by_point.get(key(q + generator))
        if hit is not None:
            assert projected[hit] == q + generator
            assert (int(logs[hit]) - int(logs[i])) % 4021 == 1
            edges.append((i, hit))
    assert len(edges) == result['full_table_shift_edges']
    anchor = reps.index((1, 8630))
    assert anchor == result['anchor_column'] and logs[anchor] == 1
    checked = []
    for cell in result['outcomes']:
        seed, size = cell['seed'], cell['table_size']
        assert seed in protocol['seeds'] and size in protocol['table_sizes']
        order = sorted((i for i in range(3949) if i != anchor),
                       key=lambda i: sha256(f'hecke-shift-density/v1:{seed}:{i}'.encode()).digest())
        selected = {anchor, *order[:size - 1]}
        assert sha256(','.join(map(str, sorted(selected))).encode()).hexdigest() == cell['subset_sha256']
        graph = Graph()
        graph.add_vertices(selected)
        retained_edges = [(i, j) for i, j in edges if i in selected and j in selected]
        graph.add_edges(retained_edges)
        groups = sorted((sorted(group) for group in graph.connected_components()), key=lambda group: group[0])
        group_of = {index: label for label, group in enumerate(groups) for index in group}
        retained = [row for row in rows if all(int(j) in selected for j in row)]
        entries = {}
        for i, row in enumerate(retained):
            for j, value in row.items():
                col = group_of[int(j)]
                entries[i, col] = (entries.get((i, col), 0) + int(value)) % 4021
        entries[(len(retained), group_of[anchor])] = 1
        reduced = matrix(GF(4021), len(retained) + 1, len(groups), entries, sparse=True)
        rank = int(reduced.rank())
        assert len(retained_edges) == cell['available_shift_edges']
        assert len(retained) == cell['retained_relation_rows']
        assert len(groups) == cell['shift_components']
        assert rank == cell['reduced_rank']
        assert len(groups) - rank == cell['residual_nullity']
        assert (rank == len(groups)) == cell['full_rank']
        checked.append({'seed': seed, 'table_size': size, 'rank': rank,
                        'components': len(groups), 'nullity': len(groups) - rank})
        print(json.dumps(checked[-1], sort_keys=True), flush=True)
    out = {'status': 'PASS_INDEPENDENT_SAGE_DENSITY_REPLAY',
           'source_sha256': {label: sha(path) for label, path in paths.items()},
           'result_sha256': sha(result_path),
           'full_table_edges_checked': len(edges),
           'relation_rows_checked': len(rows),
           'table_logs_replayed': len(logs),
           'cells': checked}
    (HERE / 'validation.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
