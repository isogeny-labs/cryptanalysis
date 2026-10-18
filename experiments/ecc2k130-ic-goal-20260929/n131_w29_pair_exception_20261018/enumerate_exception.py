"""Exhaust the rank-reduced W29 reciprocal-exception equation exactly."""
import hashlib
import json
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent
sys.path.insert(0, str(root / 'n41_n131_fivepair_w9_w29_20261017'))
import circuit_n131_3p2 as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def add_pivot(basis, value, representation=0):
    while value:
        pivot = value.bit_length() - 1
        if pivot not in basis:
            basis[pivot] = (value, representation)
            return False, 0
        word, code = basis[pivot]
        value ^= word
        representation ^= code
    return True, representation


def reduce_pivots(basis, value):
    for pivot in sorted(basis, reverse=True):
        if value >> pivot & 1:
            value ^= basis[pivot][0]
    return value


F = design.F
PB = design.PB
CH = F.mul(design.C, design.H)
low = [1] + [F.square(b) for b in PB]
low += [F.mul(PB[i], PB[j]) for i in range(28) for j in range(i, 28)]
low_basis = {}
for word in low:
    add_pivot(low_basis, word)
high_basis = {}
kernel_codes = []
for i, b in enumerate(PB):
    word = reduce_pivots(low_basis, F.mul(CH, F.square(b)))
    dependent, relation = add_pivot(high_basis, word, 1 << i)
    if dependent:
        kernel_codes.append(relation)
assert len(low_basis) == 104
assert len(high_basis) == 11
assert len(kernel_codes) == 17
assert len({code.bit_length() - 1 for code in kernel_codes}) == 17


def product(code):
    value = 0
    for i, b in enumerate(PB):
        if code >> i & 1:
            value ^= b
    return value


s_basis = [product(code) for code in kernel_codes]
for s in s_basis:
    assert reduce_pivots(low_basis, F.mul(CH, F.square(s))) == 0
updates = [[F.mul(b, s) for b in PB] for s in s_basis]
rhs_updates = [F.mul(CH, F.square(s)) for s in s_basis]

# Gray order changes just one kernel-basis vector between adjacent inputs.
current_s_code = 0
current_s_word = 0
current_rhs = 1
columns = [F.square(b) for b in PB]
solvable_nonzero_s = 0
first_solution = None
full_rank_histogram = {}
started = time.monotonic()
for index in range(1 << len(kernel_codes)):
    if index:
        flip = (index & -index).bit_length() - 1
        current_s_code ^= kernel_codes[flip]
        current_s_word ^= s_basis[flip]
        current_rhs ^= rhs_updates[flip]
        columns = [a ^ delta for a, delta in zip(columns, updates[flip])]
    assert current_s_word == product(current_s_code) if index < 32 else True
    if not current_s_code:
        continue
    basis = {}
    for i, word in enumerate(columns):
        add_pivot(basis, word, 1 << i)
    full_rank_histogram[str(len(basis))] = full_rank_histogram.get(str(len(basis)), 0) + 1
    value = current_rhs
    p_code = 0
    while value:
        pivot = value.bit_length() - 1
        if pivot not in basis:
            break
        word, code = basis[pivot]
        value ^= word
        p_code ^= code
    if value == 0:
        solvable_nonzero_s += 1
        if first_solution is None:
            first_solution = {'p_code': p_code, 's_code': current_s_code,
                              'p_nonzero': bool(p_code),
                              'q_nonzero': bool(p_code ^ current_s_code)}

result = {
    'status': 'EXACT_EXHAUSTIVE_FIELD_LINEAR_SYSTEM_ENUMERATION',
    'candidate_id': None,
    'curve_id': 'EC1N131Ckb1heb5f1998f20b',
    'field_degree': design.N,
    'field_taps': design.TAPS,
    'C': design.C,
    'H': design.H,
    'CH': CH,
    'product_basis': PB,
    'low_rank': len(low_basis),
    'high_quotient_rank': len(high_basis),
    'kernel_dimension': len(kernel_codes),
    'kernel_codes': kernel_codes,
    'nonzero_s_checked': (1 << len(kernel_codes)) - 1,
    'solvable_nonzero_s': solvable_nonzero_s,
    'first_solution': first_solution,
    'linear_system_rank_histogram': full_rank_histogram,
    'wall_seconds': time.monotonic() - started,
    'sources': {str(path): sha(path) for path in
                (here / 'enumerate_exception.py', here / 'rank_result.json',
                 root / 'n41_n131_fivepair_w9_w29_20261017' / 'circuit_n131_3p2.py',
                 root / 'n131_w23_sixpair_shared_circuit_20261017' / 'circuit.py')},
}
(here / 'enumeration_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ('nonzero_s_checked',
                                               'solvable_nonzero_s', 'first_solution',
                                               'wall_seconds')}, sort_keys=True))
