"""Independent trace census and low-degree source-code interpolation."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
N41 = ROOT / 'n41_n131_fivepair_w9_w29_20261017'
N131 = N41 / 'n131_control_3p2.json'
STATES = N41 / 'n41_states.json'
PUBLIC = ROOT / 'n131_w23_sixpair_public_sat_20261017/protocol.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(n, taps):
    R = PolynomialRing(GF(2), 'u')
    u = R.gen()
    return GF(2**n, name='u', modulus=u**n + sum(u**k for k in taps))


def dec(F, word, n):
    return F([int(word) >> bit & 1 for bit in range(n)])


def solve_fit(rows, degree, width):
    monomials = [()] + [part for size in range(1, degree + 1)
                      for part in itertools.combinations(range(width), size)]
    augmented = []
    for code, output in rows:
        feature = sum((int(all(code >> bit & 1 for bit in part))) << i
                      for i, part in enumerate(monomials))
        augmented.append(feature | (int(output) << len(monomials)))
    pivots = []
    for column in range(len(monomials)):
        pivot = next((index for index in range(len(pivots), len(augmented))
                      if augmented[index] >> column & 1), None)
        if pivot is None:
            continue
        augmented[len(pivots)], augmented[pivot] = augmented[pivot], augmented[len(pivots)]
        for index in range(len(augmented)):
            if index != len(pivots) and augmented[index] >> column & 1:
                augmented[index] ^= augmented[len(pivots)]
        pivots.append(column)
    consistent = not any((row & ((1 << len(monomials)) - 1)) == 0
                         and row >> len(monomials) & 1 for row in augmented)
    solution = []
    if consistent:
        coefficients = 0
        for row, column in zip(augmented, pivots):
            if row >> len(monomials) & 1:
                coefficients |= 1 << column
        solution = [list(part) for index, part in enumerate(monomials)
                    if coefficients >> index & 1]
        assert all(sum(all(code >> bit & 1 for bit in part) for part in solution) % 2 == output
                   for code, output in rows)
    return {'degree': degree, 'feature_count': len(monomials),
            'rank': len(pivots), 'consistent': consistent,
            'one_solution_monomials': solution}


F41 = field(41, [0, 3])
states = json.loads(STATES.read_text())
assert states['eligible_mask_count'] == 259 and states['usable_edges'] == 71
bits41 = [bit for bit in range(9) if bit != 5]
rows = []
for slot in range(5):
    grouped = {}
    for row in states['states'][slot]:
        mask = row['masks'][0]
        trace = int((1 / dec(F41, row['point'][0], 41)).trace())
        grouped.setdefault(mask, set()).add(trace)
    assert len(grouped) == 71 and all(len(values) == 1 for values in grouped.values())
    rows.append({str(mask): next(iter(values)) for mask, values in sorted(grouped.items())})
assert all(row == rows[0] for row in rows)
code_outputs = []
for mask_text, trace in rows[0].items():
    mask = int(mask_text)
    code = sum(((mask >> bit) & 1) << index for index, bit in enumerate(bits41))
    code_outputs.append((code, trace))
fits = [solve_fit(code_outputs, degree, 8) for degree in (0, 1, 2)]

F131 = field(131, [0, 1, 2, 13])
control = json.loads(N131.read_text())
public = json.loads(PUBLIC.read_text())
assert control['curve_id'] == public['curve_id']
seed = dec(F131, 898618 << 1, 131)
assert seed.trace() == 0
h = sum((seed**(1 << (2 * i)) for i in range(66)), F131.zero())
assert h**2 + h == seed
C = 1 + h**2
assert C
bits131 = [bit for bit in range(29) if bit != (898618).bit_length() - 1]
basis_checks = []
for bit in bits131:
    a = dec(F131, 1 << (bit + 1), 131)
    p = a**2 + seed * a
    basis_checks.append({'bit': bit, 'trace_source': int(a.trace()),
                         'trace_root_difference': int((p / C).trace())})
assert all(row['trace_source'] == row['trace_root_difference'] for row in basis_checks)
pair_traces = [int(dec(F131, row['output_reciprocal'], 131).trace())
               for row in control['pairs']]
target_trace = int(dec(F131, control['target_reciprocal'], 131).trace())
assert sum(pair_traces) % 2 == target_trace
result = {'status': 'PASS_INDEPENDENT_TRACE_SOURCE_AND_TARGET_PARITY',
          'n41': {'edge_count': len(code_outputs),
                  'trace_zero_edges': sum(value == 0 for _, value in code_outputs),
                  'trace_one_edges': sum(value == 1 for _, value in code_outputs),
                  'slot_tables_identical': True, 'code_trace_rows': sorted(code_outputs),
                  'fits': fits},
          'n131': {'basis_checks': basis_checks, 'constructed_pair_traces': pair_traces,
                   'constructed_target_trace': target_trace,
                   'source_bit_count': len(bits131)},
          'source_sha256': {path.name: sha(path) for path in
                            (Path(__file__), STATES, N131, PUBLIC,
                             HERE / 'sage_runtime_info.json')}}
with (HERE / 'census_trace_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'n41_fits': fits,
                  'n131_target_trace': target_trace,
                  'n131_pair_traces': pair_traces}))
