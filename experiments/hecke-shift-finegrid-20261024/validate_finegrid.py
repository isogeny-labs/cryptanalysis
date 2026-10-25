"""Separate Sage graph/matrix replay of all 36 fine-grid cells."""
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
    logs_data = saved['logs']
    assert reps == [tuple(pair) for pair in logs_data['column_representatives']]
    logs = logs_data['results']['seed_plus_degree2_3_hecke']['logs_by_column']
    rows = [row['coefficients'] for row in saved['seed']['accepted_rows']] + saved['frontier']['rows']
    curve = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
    origin = curve(0)
    def point(rep):
        return origin if rep == (-1, -1) else curve([*rep, 1])
    generator = 5 * point((1, 8630))
    projected = [5 * point(rep) for rep in reps]
    by_point = {key(point): i for i, point in enumerate(projected)}
    assert len(by_point) == len(reps) == len(logs) == 3949
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
    assert len(result['outcomes']) == len(protocol['seeds']) * len(protocol['table_sizes'])
    for saved_cell in result['outcomes']:
        seed, size = saved_cell['seed'], saved_cell['table_size']
        assert seed in protocol['seeds'] and size in protocol['table_sizes']
        order = sorted((i for i in range(3949) if i != anchor),
                       key=lambda i: sha256(f'hecke-shift-density/v1:{seed}:{i}'.encode()).digest())
        selected = {anchor, *order[:size - 1]}
        assert sha256(','.join(map(str, sorted(selected))).encode()).hexdigest() == saved_cell['subset_sha256']
        graph = Graph()
        graph.add_vertices(selected)
        internal_edges = [(i, j) for i, j in edges if i in selected and j in selected]
        graph.add_edges(internal_edges)
        groups = sorted((sorted(group) for group in graph.connected_components()), key=lambda group: group[0])
        group_of = {index: label for label, group in enumerate(groups) for index in group}
        kept_rows = [row for row in rows if all(int(j) in selected for j in row)]
        entries = {}
        for i, row in enumerate(kept_rows):
            for j, coefficient in row.items():
                column = group_of[int(j)]
                entries[i, column] = (entries.get((i, column), 0) + int(coefficient)) % 4021
        entries[(len(kept_rows), group_of[anchor])] = 1
        active = {col for (_, col), value in entries.items() if value % 4021}
        reduced = matrix(GF(4021), len(kept_rows) + 1, len(groups), entries, sparse=True)
        rank = int(reduced.rank())
        assert len(internal_edges) == saved_cell['available_shift_edges']
        assert len(kept_rows) == saved_cell['retained_relation_rows']
        assert len(groups) == saved_cell['shift_components']
        assert len(groups) - len(active) == saved_cell['zero_incidence_components']
        assert rank == saved_cell['quotient_rank']
        assert len(groups) - rank == saved_cell['residual_nullity']
        assert (rank == len(groups)) == saved_cell['full_rank']
        checked.append({'seed': seed, 'table_size': size, 'nullity': len(groups) - rank,
                        'zero_incidence': len(groups) - len(active)})
        print(json.dumps(checked[-1], sort_keys=True), flush=True)
    output = {'status': 'PASS_INDEPENDENT_FINEGRID_REPLAY',
              'source_sha256': {label: sha(path) for label, path in sources.items()},
              'result_sha256': sha(result_path),
              'full_table_edges_checked': len(edges),
              'relation_rows_checked': len(rows),
              'table_logs_replayed': len(logs),
              'cells': checked}
    (HERE / 'validation.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
