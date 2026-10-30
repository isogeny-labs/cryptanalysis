"""Hecke-free rank controls and separate short-model scalar replay."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

from audit import HERE, ROOT, SOURCE, SOURCE_SHA, Curve, scalar_rows, equality_rows, dense_reduce

P = 367
A = -31 * pow(3, -1, P) % P
B = -2501 * pow(108, -1, P) % P


def short(point):
    if point is None:
        return None
    x, y = point
    result = ((x-pow(3, -1, P)) % P, (y+pow(2, -1, P)) % P)
    X, Y = result
    assert (Y*Y-X*X*X-A*X-B) % P == 0
    return result


def plus(left, right):
    if left is None:
        return right
    if right is None:
        return left
    x, y = left
    u, v = right
    if x == u and (y+v) % P == 0:
        return None
    if left == right:
        slope = (3*x*x+A) * pow(2*y % P, -1, P) % P
    else:
        slope = (v-y) * pow((u-x) % P, -1, P) % P
    out_x = (slope*slope-x-u) % P
    out_y = (slope*(x-out_x)-y) % P
    assert (out_y*out_y-out_x**3-A*out_x-B) % P == 0
    return out_x, out_y


def times(k, point):
    if k < 0:
        return times(-k, None if point is None else (point[0], -point[1] % P))
    result = None
    for _ in range(k):
        result = plus(result, point)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(['bash', 'scripts/checkpoint.sh', 'gate'], cwd=ROOT, check=True)
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    data = json.loads(raw)
    points = [tuple(map(int, text.strip('()').split(' : ')[:2])) for text in data['column_points']]
    curve = Curve()
    projected = [curve.mul(35, p) for p in points]
    independent = [times(35, short(p)) for p in points]
    assert independent == [short(p) for p in projected]
    assert all(times(11, p) is None for p in independent)
    first_path = HERE/'runs/20261030T030848Z/receipt.json'
    first = json.loads(first_path.read_text())
    replays = []
    for arm in first['arms']:
        if 'normalized_logs' in arm:
            anchor = arm['anchor_column']
            assert independent[anchor] is not None
            assert all(times(log, independent[anchor]) == p
                       for log, p in zip(arm['normalized_logs'], independent))
            replays.append(arm['arm'])
    assert len(replays) == 4
    spec = importlib.util.spec_from_file_location('frozen_sparse', SOURCE.parents[1]/'audit_matrix.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    equal = equality_rows(projected)
    double = scalar_rows(projected, curve, [2])
    triple = scalar_rows(projected, curve, [3])
    results = []
    for name, rows in [('equalities_only', equal), ('double_only', double),
                       ('double_triple_only', double+triple)]:
        for row in rows:
            total = None
            for i, coefficient in row.items():
                total = plus(total, times(coefficient, independent[int(i)]))
            assert total is None
        rank = len(dense_reduce(rows, 64)[0])
        assert rank == frozen.rank(rows, 11, 64)
        results.append(dict(arm=name, rows=len(rows), rank=rank, nullity=64-rank))
    result = dict(status='verified_finite_control', hecke_rows_used=0,
                  arms=results, independent_model=dict(p=P, a=A, b=B),
                  independently_replayed_arms=replays, scalars_checked=64*len(replays),
                  source_sha256=SOURCE_SHA,
                  prior_receipt_sha256=hashlib.sha256(first_path.read_bytes()).hexdigest(),
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as output:
        output.write(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
