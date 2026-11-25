"""Exact finite scalar-closure audit; research execution requires checkpoint gate."""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = HERE.parent / 'ecdlp-hecke-d39-holdout-20261026/data/exp11_class_walk_D39_f6.json'
SOURCE_SHA = '4bcc8eb1905a9ed79a47cc31820e722dc7a6ff87f18bb37aeebafa35e6cc6df9'


class Curve:
    """Generalized Weierstrass affine law for [0,-1,1,-10,-20]."""
    def __init__(self, p=367):
        self.p = p
        self.additions = 0

    def contains(self, point):
        if point is None:
            return True
        x, y = point
        return (y*y + y - x*x*x + x*x + 10*x + 20) % self.p == 0

    def neg(self, point):
        return None if point is None else (point[0], (-point[1]-1) % self.p)

    def add(self, left, right):
        self.additions += 1
        if left is None:
            return right
        if right is None:
            return left
        if right == self.neg(left):
            return None
        x, y = left
        u, v = right
        if left == right:
            slope = (3*x*x - 2*x - 10) * pow((2*y+1) % self.p, -1, self.p) % self.p
        else:
            slope = (v-y) * pow((u-x) % self.p, -1, self.p) % self.p
        out_x = (slope*slope + 1 - x - u) % self.p
        out_y = (-slope*out_x - (y-slope*x) - 1) % self.p
        result = (out_x, out_y)
        assert self.contains(result)
        return result

    def mul(self, scalar, point):
        if scalar < 0:
            return self.mul(-scalar, self.neg(point))
        result = None
        while scalar:
            if scalar & 1:
                result = self.add(result, point)
            point = self.add(point, point)
            scalar >>= 1
        return result


def dense_reduce(rows, columns, modulus=11):
    """Dense Gauss-Jordan independent of the frozen sparse audit."""
    matrix = [[int(row.get(str(j), row.get(j, 0))) % modulus
               for j in range(columns)] for row in rows]
    pivots = []
    for col in range(columns):
        pivot = next((i for i in range(len(pivots), len(matrix)) if matrix[i][col]), None)
        if pivot is None:
            continue
        k = len(pivots)
        matrix[k], matrix[pivot] = matrix[pivot], matrix[k]
        inv = pow(matrix[k][col], -1, modulus)
        matrix[k] = [v*inv % modulus for v in matrix[k]]
        for i in range(len(matrix)):
            if i != k and matrix[i][col]:
                scale = matrix[i][col]
                matrix[i] = [(a-scale*b) % modulus for a, b in zip(matrix[i], matrix[k])]
        pivots.append(col)
    return pivots, matrix[:len(pivots)]


def scalar_rows(points, curve, multipliers):
    """Collect by point equality only; never enumerate discrete logs."""
    by_point = defaultdict(list)
    for i, point in enumerate(points):
        by_point[point].append(i)
    rows = []
    for m in multipliers:
        for i, point in enumerate(points):
            image = curve.mul(m, point)
            for j in by_point.get(image, []):
                row = {j: 1}
                row[i] = row.get(i, 0) - m
                row = {k: v for k, v in row.items() if v}
                if row:
                    rows.append(row)
    return rows


def equality_rows(points):
    first, rows = {}, []
    for i, point in enumerate(points):
        if point is None:
            rows.append({i: 1})
        elif point in first:
            rows.append({i: 1, first[point]: -1})
        else:
            first[point] = i
    return rows


def check_rows(rows, points, curve):
    for row in rows:
        total = None
        for column, coefficient in row.items():
            i = int(column)
            assert 0 <= i < len(points)
            total = curve.add(total, curve.mul(int(coefficient), points[i]))
        assert total is None, 'invalid group relation'


def solve_fixture(data, sparse_rank):
    assert (data['DK'], data['f'], data['p'], data['n'], data['nprime']) == (-39, 6, 367, 385, 11)
    curve = Curve()
    full_order = 1 + sum(curve.contains((x, y)) for x in range(367) for y in range(367))
    assert full_order == 385
    points = []
    for text in data['column_points']:
        match = re.fullmatch(r'\((\d+) : (\d+) : 1\)', text)
        assert match is not None
        point = tuple(map(int, match.groups()))
        assert all(0 <= v < 367 for v in point) and curve.contains(point)
        points.append(point)
    assert len(points) == len(set(points)) == 64
    check_rows(data['relation_rows'], points, curve)
    projected = [curve.mul(35, point) for point in points]
    assert any(p is not None for p in projected)
    assert all(curve.mul(11, p) is None for p in projected)
    baseline = data['relation_rows'] + data['atkin_lehner_rows']
    check_rows(baseline, projected, curve)
    setup_ops = curve.additions
    eq = equality_rows(projected)
    start = curve.additions
    two = scalar_rows(projected, curve, [2])
    three = scalar_rows(projected, curve, [3])
    collection_ops = curve.additions - start
    check_rows(eq + two + three, projected, curve)
    arms = [('hecke', data['relation_rows']), ('baseline', baseline),
            ('equalities', baseline+eq), ('double', baseline+two),
            ('double_triple', baseline+two+three), ('all', baseline+eq+two+three)]
    results = []
    for name, rows in arms:
        pivots, _ = dense_reduce(rows, 64)
        rank = len(pivots)
        assert rank == sparse_rank(rows, 11, 64)
        assert rank <= 63, 'nonzero group-log vector must remain in the kernel'
        item = dict(arm=name, rows=len(rows), rank=rank, nullity=64-rank,
                    extra_pivots_over_baseline=rank-52)
        if rank == 63:
            anchor = next(i for i, point in enumerate(projected) if point is not None)
            augmented = [dict(row) for row in rows] + [{anchor: 1}]
            # Solve A*x=b by reducing 65 columns; the last is the RHS.
            augmented[-1][64] = 1
            solve_pivots, reduced = dense_reduce(augmented, 65)
            assert solve_pivots == list(range(64))
            logs = [row[64] for row in reduced]
            assert all(curve.mul(k, projected[anchor]) == point
                       for k, point in zip(logs, projected))
            item.update(anchor_column=anchor, normalized_logs=logs,
                        scalar_replay='verified')
        results.append(item)
    assert (results[0]['rank'], results[1]['rank']) == (40, 52)
    return dict(status='verified_finite_diagnostic', field=367, curve_ainvs=[0,-1,1,-10,-20],
                group_order=full_order, subgroup_order=11, cofactor=35,
                distinct_projected_points=len(set(projected)),
                equalities=len(eq), double_rows=len(two), triple_rows=len(three),
                group_addition_calls=dict(setup_and_baseline_checks=setup_ops,
                                         scalar_collection=collection_ops,
                                         total_with_verification=curve.additions),
                arms=results, performance_speedup=None, arbitrary_target_descent='not implemented')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(['bash', 'scripts/checkpoint.sh', 'gate'], cwd=ROOT, check=True)
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    spec = importlib.util.spec_from_file_location('frozen_sparse', SOURCE.parents[1] / 'audit_matrix.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    result = solve_fixture(json.loads(raw), frozen.rank)
    result.update(source_sha256=SOURCE_SHA,
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  python=sys.version, baseline_revision='cf35a825b25c3f1ece5d7d36dd98d78ea66a4022')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
