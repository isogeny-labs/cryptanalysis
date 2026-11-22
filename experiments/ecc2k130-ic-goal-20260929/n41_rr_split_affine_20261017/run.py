"""Split-minor bilinear affine certificate on frozen N41 target boxes."""
import hashlib
import itertools
import json
import resource
import sys
import time
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_rr_joint_box_rank_20261017'
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017/join_input.tsv'
MOD = (1 << 41) | (1 << 3) | 1
MASK = (1 << 41) - 1
SUBSETS = tuple(itertools.combinations(range(7), 3))
COMPLEMENTS = tuple(tuple(j for j in range(7) if j not in s) for s in SUBSETS)
PERMS3 = tuple(itertools.permutations(range(3)))
PERMS4 = tuple(itertools.permutations(range(4)))
MUL_CALLS = 0


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(a, b):
    global MUL_CALLS
    MUL_CALLS += 1
    answer = 0
    while b:
        if b & 1:
            answer ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
            a ^= MOD
    return answer


@lru_cache(maxsize=50000)
def row(point):
    x, y = point
    x2 = mul(x, x)
    return (1, x, y, x2, mul(x, y), mul(x2, x), mul(x2, y))


def minor(rows, cols, permutations):
    result = 0
    for order in permutations:
        value = 1
        for i, j in enumerate(order):
            value = mul(value, rows[i][cols[j]])
        result ^= value
    return result


@lru_cache(maxsize=10000)
def left_vector(points):
    rows = tuple(row(p) for p in points)
    return tuple(minor(rows, cols, PERMS3) for cols in SUBSETS)


@lru_cache(maxsize=10000)
def right_vector(points):
    rows = tuple(row(p) for p in points)
    return tuple(minor(rows, cols, PERMS4) for cols in COMPLEMENTS)


def dot(left, right):
    result = 0
    for a, b in zip(left, right):
        result ^= mul(a, b)
    return result


def vector_xor(a, b):
    return tuple(x ^ y for x, y in zip(a, b))


def vector_pack(values):
    return sum(value << (41*i) for i, value in enumerate(values))


def vector_basis(vectors):
    leading = {}
    chosen = []
    for vector in vectors:
        bits = vector_pack(vector)
        while bits:
            pivot = bits.bit_length()-1
            if pivot not in leading:
                leading[pivot] = bits
                chosen.append(vector)
                break
            bits ^= leading[pivot]
    return chosen


def rank_insert(basis, value):
    while value:
        pivot = value.bit_length()-1
        if pivot not in basis:
            basis[pivot] = value
            return True
        value ^= basis[pivot]
    return False


def read_source():
    lines = SOURCE.read_text().splitlines()
    rows = {}
    for line in lines[1:]:
        values = line.split()
        slot, state = map(int, values[1:3])
        rows[slot, state] = (int(values[9]), int(values[10]))
    assert len(rows) == 960
    return rows


def inspect_box(box, rows, negative_target, deadline):
    global MUL_CALLS
    started_calls = MUL_CALLS
    left_ids = tuple(itertools.product(*box['slots'][:3]))
    right_ids = tuple(itertools.product(*box['slots'][3:]))
    left_points = tuple(tuple(rows[j, ids[j]] for j in range(3)) for ids in left_ids)
    right_points = tuple(tuple(rows[j+3, ids[j]] for j in range(3)) +
                         (negative_target,) for ids in right_ids)
    left_x = {p[0] for block in left_points for p in block}
    right_x = {p[0] for block in right_points for p in block}
    if left_x & right_x or any(len({p[0] for p in block}) != 3 for block in left_points) or \
            any(len({p[0] for p in block}) != 4 for block in right_points):
        return {'status': 'CHART_EXCEPTION', 'left_states': len(left_ids),
                'right_states': len(right_ids), 'mul_calls': MUL_CALLS-started_calls}
    if time.monotonic() >= deadline:
        return {'status': 'BOUNDED_UNKNOWN'}
    left = [left_vector(points) for points in left_points]
    right = [right_vector(points) for points in right_points]
    l0, r0 = left[0], right[0]
    l_basis = vector_basis(vector_xor(vector, l0) for vector in left[1:])
    r_basis = vector_basis(vector_xor(vector, r0) for vector in right[1:])
    first = dot(l0, r0)
    field_basis = {}
    pairings = 1
    rank_full = False
    for u in l_basis:
        pairings += 1
        rank_insert(field_basis, dot(u, r0))
        if len(field_basis) == 41:
            rank_full = True
            break
    if not rank_full:
        for v in r_basis:
            pairings += 1
            rank_insert(field_basis, dot(l0, v))
            if len(field_basis) == 41:
                rank_full = True
                break
    if not rank_full:
        for u in l_basis:
            for v in r_basis:
                pairings += 1
                rank_insert(field_basis, dot(u, v))
                if len(field_basis) == 41:
                    rank_full = True
                    break
            if rank_full or time.monotonic() >= deadline:
                break
    if time.monotonic() >= deadline and not rank_full:
        status = 'BOUNDED_UNKNOWN'
    elif rank_full:
        status = 'NO_AFFINE_LINEAR_SEPARATOR'
    else:
        reduced = first
        for pivot in sorted(field_basis, reverse=True):
            if reduced >> pivot & 1:
                reduced ^= field_basis[pivot]
        status = 'CERTIFIED_NO_ZERO' if reduced else 'AFFINE_HULL_CONTAINS_ZERO'
    return {'status': status, 'left_states': len(left_ids),
            'right_states': len(right_ids), 'left_vector_rank': len(l_basis),
            'right_vector_rank': len(r_basis), 'field_difference_rank': len(field_basis),
            'first_determinant': first, 'field_pairings': pairings,
            'mul_calls': MUL_CALLS-started_calls,
            'left_first_state_ids': left_ids[0], 'right_first_state_ids': right_ids[0]}


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['source_sha256'] == {
        'runner': sha(Path(__file__)), 'panel': sha(PRIOR / 'panel.json'),
        'source': sha(SOURCE), 'prior_result': sha(PRIOR / 'result.json')}
    panel = json.loads((PRIOR / 'panel.json').read_text())
    prior = json.loads((PRIOR / 'result.json').read_text())
    rows = read_source()
    target = tuple(panel['target'])
    negative_target = (target[0], target[1] ^ target[0])
    started = time.monotonic()
    deadline = started + protocol['wall_cap_seconds']
    output = []
    for index in protocol['panel_indices']:
        box = panel['panels'][index]
        result = inspect_box(box, rows, negative_target, deadline)
        if result['status'] not in ('BOUNDED_UNKNOWN', 'CHART_EXCEPTION'):
            assert result['first_determinant'] == prior['rows'][index]['first_determinant'], index
        output.append({'panel_index': index, 'kind': box['kind'], 'trial': box['trial'], **result})
        print(index, result['status'], result.get('mul_calls'), flush=True)
        if result['status'] == 'BOUNDED_UNKNOWN':
            break
    record = {'status': 'COMPLETE' if len(output) == len(protocol['panel_indices']) else 'BOUNDED_UNKNOWN',
              'candidate_id': None, 'rows': output, 'elapsed_seconds': time.monotonic()-started,
              'field_mul_calls': MUL_CALLS,
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(HERE / 'protocol.json')}
    with (HERE / 'result.json').open('x') as file:
        json.dump(record, file, indent=2, sort_keys=True)
        file.write('\n')
    print(record['status'], len(output), record['elapsed_seconds'], flush=True)


if __name__ == '__main__':
    main()
