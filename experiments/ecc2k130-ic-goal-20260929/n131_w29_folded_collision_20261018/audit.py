"""Exact Frobenius-folded collision spaces of the canonical N131 W29 source."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_n131_fivepair_w9_w29_20261017'))
import circuit_n131_3p2 as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'protocol.json').read_text())
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert not (HERE / 'audit_result.json').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('collision audit wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
start = time.monotonic()

F = design.F
N = design.N
assert N == 131 and len(design.BASE) == 28
assert design.SEED == 898618 << 1


def echelon(columns):
    basis = {}
    kernel = []
    for index, column in enumerate(columns):
        word = column
        code = 1 << index
        while word:
            pivot = word.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (word, code)
                break
            value, label = basis[pivot]
            word ^= value
            code ^= label
        else:
            kernel.append(code)
    return basis, kernel


def solve(basis, value):
    code = 0
    while value:
        pivot = value.bit_length() - 1
        if pivot not in basis:
            return None
        word, label = basis[pivot]
        value ^= word
        code ^= label
    return code


def from_code(code, words):
    value = 0
    for i, word in enumerate(words):
        if code >> i & 1:
            value ^= word
    return value


base = design.BASE
seed = design.SEED
rows = []
for k in range(N):
    rotated = [F.frob(word, k) for word in base]
    rotated_seed = F.frob(seed, k)
    columns = rotated + base
    basis, kernel = echelon(columns)
    assert len(basis) + len(kernel) == 56
    for e in (0, 1):
        for f in (0, 1):
            offset = (rotated_seed if e else 0) ^ (seed if f else 0)
            solution = solve(basis, offset)
            if solution is not None:
                assert from_code(solution, columns) == offset
                assert all(from_code(code, columns) == 0 for code in kernel)
            rows.append({
                'frobenius_power': k,
                'source_endpoint_e': e,
                'other_endpoint_f': f,
                'rank': len(basis),
                'kernel_dimension': len(kernel),
                'offset': offset,
                'feasible': solution is not None,
                'solution_code': solution,
                'kernel_codes': kernel if solution is not None else [],
                'collision_pair_count_before_source_filter':
                    (1 << len(kernel)) if solution is not None else 0,
                'has_nontrivial_pair': solution is not None and
                    (solution != 0 or len(kernel) > 0),
            })
    if k == 0:
        assert len(basis) == 28
        assert [row['feasible'] for row in rows[:4]] == [True, False, False, True]

finished = time.monotonic()
signal.alarm(0)
histogram = {}
for row in rows:
    key = str(row['rank'])
    histogram[key] = histogram.get(key, 0) + 1
result = {
    'status': 'EXACT_N131_W29_FROBENIUS_COLLISION_SPACES',
    'candidate_id': None,
    'curve_id': protocol['curve_id'],
    'field_degree': N,
    'source_code_bits': 28,
    'seed': seed,
    'source_basis': base,
    'frobenius_powers': N,
    'endpoint_choices_per_power': 4,
    'case_count': len(rows),
    'feasible_case_count': sum(row['feasible'] for row in rows),
    'nontrivial_case_count': sum(row['has_nontrivial_pair'] for row in rows),
    'rank_histogram': histogram,
    'cases': rows,
    'wall_seconds': finished - start,
    'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE / 'protocol.json'),
}
(HERE / 'audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'case_count', 'feasible_case_count',
                   'nontrivial_case_count', 'rank_histogram', 'wall_seconds')},
                 sort_keys=True))
