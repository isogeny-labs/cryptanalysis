"""Quadratic determinant-value certificate capacity on exact N41 six-pair boxes."""
import hashlib
import importlib.util
import itertools
import json
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017/join_input.tsv'
SPLIT = ROOT / 'n41_rr_split_affine_20261017/run.py'
spec = importlib.util.spec_from_file_location('rr_split', SPLIT)
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)
N = 41
FEATURES = N + N * (N - 1) // 2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def feature(value):
    bits = value
    active = [i for i in range(N) if value >> i & 1]
    k = N
    for i in range(N):
        for j in range(i + 1, N):
            if value >> i & 1 and value >> j & 1:
                bits |= 1 << k
            k += 1
    assert k == FEATURES
    return bits


def insert(basis, value):
    row = feature(value)
    rhs = 1
    while row:
        pivot = row.bit_length() - 1
        if pivot not in basis:
            basis[pivot] = (row, rhs)
            return 'INDEPENDENT'
        old, old_rhs = basis[pivot]
        row ^= old
        rhs ^= old_rhs
    return 'DEPENDENT' if rhs == 0 else 'INCONSISTENT'


def states(codes):
    return tuple(tuple(4 * code + sign for code in group for sign in range(4))
                 for group in codes)


def inspect_box(name, codes, points, target, deadline):
    ids = states(codes)
    edges = {}
    for slot, group in enumerate(codes):
        for code in group:
            edges[slot, code] = points[slot, 4 * code][2]
    for selected in itertools.product(*codes):
        columns = [c for slot, code in enumerate(selected) for c in edges[slot, code]]
        assert len(columns) == len(set(columns)), (name, selected)
    neg = (target[0], target[1] ^ target[0])
    left_ids = tuple(itertools.product(*ids[:3]))
    right_ids = tuple(itertools.product(*ids[3:]))
    left_pts = [tuple(points[j, idx][:2] for j, idx in enumerate(key)) for key in left_ids]
    right_pts = [tuple(points[j + 3, idx][:2] for j, idx in enumerate(key)) + (neg,)
                 for key in right_ids]
    for block in left_pts + right_pts:
        assert len({p[0] for p in block}) == len(block), (name, 'within chart')
    assert not ({p[0] for block in left_pts for p in block} &
                {p[0] for block in right_pts for p in block}), (name, 'cross chart')
    t0 = time.monotonic()
    left = [rr.left_vector(block) for block in left_pts]
    right = [rr.right_vector(block) for block in right_pts]
    prep = time.monotonic() - t0
    basis = {}
    seen = 0
    zero = None
    status = 'CERTIFIED_NO_ZERO'
    t1 = time.monotonic()
    for li, lv in enumerate(left):
        for ri, rv in enumerate(right):
            if time.monotonic() >= deadline:
                status = 'BOUNDED_UNKNOWN'
                break
            value = rr.dot(lv, rv)
            seen += 1
            if value == 0:
                zero = {'left': left_ids[li], 'right': right_ids[ri]}
            if insert(basis, value) == 'INCONSISTENT':
                status = 'NO_QUADRATIC_CERTIFICATE'
                break
        if status != 'CERTIFIED_NO_ZERO':
            break
    return {'name': name, 'codes': codes, 'status': status,
            'left_states': len(left), 'right_states': len(right),
            'possible_pairs': len(left) * len(right), 'evaluated_pairs': seen,
            'feature_rank': len(basis), 'first_zero': zero,
            'vector_preparation_seconds': prep,
            'certificate_seconds': time.monotonic() - t1}


def main():
    p = json.loads((HERE / 'protocol.json').read_text())
    assert p['source_sha256'] == {'source': sha(SOURCE), 'split_runner': sha(SPLIT),
                                   'runner': sha(Path(__file__))}
    points = {}
    for line in SOURCE.read_text().splitlines()[1:]:
        a = line.split()
        points[int(a[1]), int(a[2])] = (int(a[9]), int(a[10]), (int(a[3]), int(a[4])))
    assert len(points) == 960
    w = p['witness_codes']
    e = p['extra_codes']
    b = p['replacement_first_code']
    boxes = [('witness_single', [[x] for x in w]),
             ('disjoint_single', [[x] for x in e]),
             ('witness_double', [[w[i], e[i]] for i in range(6)]),
             ('shifted_double', [[b, e[0]]] + [[w[i], e[i]] for i in range(1, 6)])]
    started = time.monotonic()
    deadline = started + p['wall_cap_seconds']
    output = []
    for name, codes in boxes:
        row = inspect_box(name, codes, points, tuple(p['target']), deadline)
        output.append(row)
        print(name, row['status'], row['evaluated_pairs'], row['feature_rank'], flush=True)
        if row['status'] == 'BOUNDED_UNKNOWN':
            break
    record = {'candidate_id': None, 'rows': output,
              'status': 'COMPLETE' if len(output) == len(boxes) else 'BOUNDED_UNKNOWN',
              'elapsed_seconds': time.monotonic() - started,
              'field_mul_calls': rr.MUL_CALLS,
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(HERE / 'protocol.json')}
    with (HERE / 'result.json').open('x') as f:
        json.dump(record, f, indent=2, sort_keys=True)
        f.write('\n')


if __name__ == '__main__':
    main()
