"""Exact quadratic certificates for successively split source-state families."""
import hashlib
import importlib.util
import itertools
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_sixpair_shared_target_20261017/join_input.tsv'
RUN = HERE / 'run.py'
spec = importlib.util.spec_from_file_location('box_run', RUN)
box = importlib.util.module_from_spec(spec)
spec.loader.exec_module(box)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
p = json.loads((HERE / 'partition_protocol.json').read_text())
assert p['sources'] == {'source': sha(SOURCE), 'box_runner': sha(RUN),
                         'partition_runner': sha(Path(__file__))}
points = {}
for line in SOURCE.read_text().splitlines()[1:]:
    a = line.split()
    points[int(a[1]), int(a[2])] = (int(a[9]), int(a[10]))
neg = (p['target'][0], p['target'][1] ^ p['target'][0])
ids = [[4*c+s for s in range(4)] for c in p['codes']]
left_keys = list(itertools.product(*ids[:3]))
right_keys = list(itertools.product(*ids[3:]))
left = [box.rr.left_vector(tuple(points[j, key[j]] for j in range(3)))
        for key in left_keys]
right = [box.rr.right_vector(tuple(points[j+3, key[j]] for j in range(3))+(neg,))
         for key in right_keys]
started = time.monotonic()
values = {(l, r): box.rr.dot(left[i], right[j])
          for i, l in enumerate(left_keys) for j, r in enumerate(right_keys)}
assert len(values) == 4096


def solve(family):
    basis = {}
    for key in family:
        state = box.insert(basis, values[key])
        if state == 'INCONSISTENT':
            return {'status': 'NO_QUADRATIC_CERTIFICATE', 'rank': len(basis)}
    solution = 0
    for pivot in sorted(basis):
        row, rhs = basis[pivot]
        bit = rhs ^ ((row & solution).bit_count() & 1)
        solution |= bit << pivot
    # Independent feature calculation and direct certificate audit.
    for key in family:
        x = values[key]
        active = [i for i in range(41) if x >> i & 1]
        feature = x
        for i, j in itertools.combinations(active, 2):
            offset = i * (2*41-i-1)//2 + (j-i-1)
            feature |= 1 << (41+offset)
        assert (solution & feature).bit_count() & 1 == 1
    return {'status': 'CERTIFIED_NO_ZERO', 'rank': len(basis),
            'coefficient_bits_hex': hex(solution)}


rows = []
for depth in (0, 1, 2):
    for prefix in itertools.product(*ids[:depth]):
        family = [key for key in values if key[0][:depth] == prefix]
        decision = solve(family)
        rows.append({'depth': depth, 'prefix': prefix, 'states': len(family), **decision})
    print(depth, [(r['status'], r['rank']) for r in rows if r['depth'] == depth], flush=True)
record = {'status': 'COMPLETE', 'candidate_id': None, 'rows': rows,
          'determinants_evaluated': len(values),
          'certificate_seconds': time.monotonic()-started,
          'field_mul_calls': box.rr.MUL_CALLS,
          'protocol_sha256': sha(HERE/'partition_protocol.json')}
with (HERE/'partition_result.json').open('x') as f:
    json.dump(record, f, indent=2, sort_keys=True)
    f.write('\n')
