"""Independent Sage graph/matrix replay of all natural-frontier prefix cells."""
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
    result_path = HERE / 'screen_result.json'
    result = json.loads(result_path.read_text())
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    frontier_path = ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json'
    seed_path = ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json'
    frontier, seed = json.loads(frontier_path.read_text()), json.loads(seed_path.read_text())
    assert result['source_sha256']['frontier'] == sha(frontier_path)
    assert result['source_sha256']['seed'] == sha(seed_path)
    reps = [tuple(pair) for pair in frontier['column_representatives']]
    index = {rep: i for i, rep in enumerate(reps)}
    curve = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
    origin = curve(0)
    def point(rep):
        return origin if rep == (-1, -1) else curve([*rep, 1])
    generator = 5 * point((1, 8630))
    projected = [5 * point(rep) for rep in reps]
    by_point = {key(q): i for i, q in enumerate(projected)}
    assert len(by_point) == 3949
    edges = {}
    for step in range(1, 5):
        step_points = []
        for i, q in enumerate(projected):
            hit = by_point.get(key(q + step*generator))
            if hit is not None:
                assert projected[hit] == q + step*generator
                step_points.append((i, hit))
        edges[step] = step_points
    anchor = index[(1, 8630)]
    selected = {index[tuple(rep)] for rep in frontier['boundary_representatives']['seed']}
    rows = [record['coefficients'] for record in seed['accepted_rows']]
    sources = 0
    checked = []
    for stage in frontier['stages']:
        selected.update(index[tuple(rep)] for rep in stage['new_representatives'])
        rows.extend(record['coefficients'] for record in stage['accepted_rows'])
        sources += stage['source_count']
        assert all(all(int(j) in selected for j in row) for row in rows)
        for radius in protocol['shift_radii']:
            saved_cell = next(cell for cell in result['outcomes']
                              if cell['layer'] == stage['layer'] and cell['radius'] == radius)
            graph = Graph()
            graph.add_vertices(selected)
            internal = [(i, j) for step in range(1, radius+1) for i, j in edges[step]
                        if i in selected and j in selected]
            graph.add_edges(internal)
            groups = sorted((sorted(group) for group in graph.connected_components()), key=lambda group: group[0])
            group_of = {i: label for label, group in enumerate(groups) for i in group}
            entries = {}
            for row_number, row in enumerate(rows):
                for j, coefficient in row.items():
                    column = group_of[int(j)]
                    entries[(row_number, column)] = (entries.get((row_number, column), 0) + int(coefficient)) % 4021
            entries[(len(rows), group_of[anchor])] = 1
            active = {column for (_, column), value in entries.items() if value % 4021}
            rank = int(matrix(GF(4021), len(rows)+1, len(groups), entries, sparse=True).rank())
            assert len(selected) == saved_cell['table_columns']
            assert sources == saved_cell['cumulative_source_points']
            assert len(rows) == saved_cell['verified_relation_rows']
            assert len(selected)*radius == saved_cell['shift_lookup_probes']
            assert len(internal) == saved_cell['successful_shift_edges']
            assert len(groups) == saved_cell['shift_components']
            assert len(groups)-len(active) == saved_cell['zero_incidence_components']
            assert rank == saved_cell['quotient_rank']
            assert len(groups)-rank == saved_cell['residual_nullity']
            checked.append({'layer': stage['layer'], 'radius': radius,
                            'table_columns': len(selected), 'nullity': len(groups)-rank})
            print(json.dumps(checked[-1], sort_keys=True), flush=True)
    assert len(checked) == len(result['outcomes']) == 24
    output = {'status': 'PASS_INDEPENDENT_NATURAL_PREFIX_RANK_REPLAY',
              'source_sha256': {'frontier': sha(frontier_path), 'seed': sha(seed_path)},
              'screen_sha256': sha(result_path), 'cells': checked}
    (HERE / 'screen_validation.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
