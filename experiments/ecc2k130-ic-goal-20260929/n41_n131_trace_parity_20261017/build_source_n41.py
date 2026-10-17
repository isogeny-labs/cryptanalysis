"""Bind the N41 target trace to existing source-product tensor wires."""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_w9_lazy_source_20261017'
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import selector

spec = importlib.util.spec_from_file_location('w9_source_base', PRIOR / 'circuit.py')
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> index & 1 for index, wire in enumerate(wires)})


fixture = json.loads((PRIOR / 'fixture.json').read_text())
screen = json.loads((PRIOR / 'screen_result.json').read_text())
coeff = json.loads((HERE / 'source_trace_coeff_result.json').read_text())
assert coeff['status'] == 'PASS_SOURCE_TENSOR_TRACE_COEFFICIENTS'
target = fixture['oriented_target_reciprocal']
start = time.monotonic_ns()
circ, wires, counts = design.build(target, 'exact5')
assert counts == next(row['counts'] for row in screen['rows'] if row['variant'] == 'exact5')
base_path = HERE / 'exact5_baseline.xcnf'
circ.write(base_path)
assert sha(base_path) == next(row['formula_sha256'] for row in screen['rows']
                              if row['variant'] == 'exact5')
old_counts = (len(circ.clauses), len(circ.xors), circ.next_var - 1, circ.and_count)
source_terms = []
for masks, inverse in zip(wires['mask'], wires['source_inverse']):
    source_terms += [circ.and_(masks[i], inverse[j])
                     for i, j in coeff['n41']['coefficients']]
assert circ.and_count == old_counts[3]
target_trace = design.trace(target)
circ.require_zero([circ.xor(source_terms + ([-1] if target_trace else []))])
new_counts = (len(circ.clauses), len(circ.xors), circ.next_var - 1, circ.and_count)
assert new_counts[1] == old_counts[1] + 1
assert new_counts[3] == old_counts[3]
assignment = {}
for slot, row in enumerate(fixture['pairs']):
    code = sum(((row['masks'][0] >> bit) & 1) << index
               for index, bit in enumerate(design.BITS))
    bind(assignment, wires['mask'][slot], code)
    bind(assignment, wires['source_inverse'][slot], row['source_inverse_product'])
    bind(assignment, wires['out'][slot], row['output_reciprocal'])
for bits, value in zip(wires['middle'], fixture['middle_reciprocals']):
    bind(assignment, bits, value)
full = selector.old.complete_assignment(circ, assignment)
check = selector.old.check_assignment(circ, full)
assert check['clauses'] == new_counts[0]
assert check['native_xor_rows'] == new_counts[1]
path = HERE / 'exact5_source_trace.xcnf'
circ.write(path)
result = {'status': 'PASS_N41_SOURCE_TRACE_GATE_CONSTRUCTED_ASSIGNMENT',
          'curve_id': fixture['curve_id'],
          'oriented_raw_point': fixture['oriented_raw_point'],
          'target_reciprocal': target, 'target_trace': target_trace,
          'source_trace_input_wires': len(source_terms),
          'per_slot_coefficient_weight': coeff['n41']['coefficient_weight'],
          'baseline_counts': {'clauses': old_counts[0], 'xor_rows': old_counts[1],
                              'variables': old_counts[2], 'and_gates': old_counts[3]},
          'source_counts': {'clauses': new_counts[0], 'xor_rows': new_counts[1],
                            'variables': new_counts[2], 'and_gates': new_counts[3]},
          'assignment_check': check, 'elapsed_ns': time.monotonic_ns() - start,
          'baseline_sha256': sha(base_path), 'source_sha256_formula': sha(path),
          'source_sha256': {name: sha(source) for name, source in
                            {'script': Path(__file__), 'circuit': PRIOR / 'circuit.py',
                             'fixture': PRIOR / 'fixture.json',
                             'coefficients': HERE / 'source_trace_coeff_result.json',
                             'runtime': HERE / 'sage_runtime_info.json',
                             'selector': Path(selector.__file__),
                             'checker': Path(selector.old.__file__)}.items()}}
with (HERE / 'build_source_n41_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'source_trace_input_wires': len(source_terms),
                  'baseline_counts': result['baseline_counts'],
                  'source_counts': result['source_counts']}))
