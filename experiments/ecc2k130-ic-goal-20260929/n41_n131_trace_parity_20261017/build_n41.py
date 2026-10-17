"""Add the exact target trace parity across all five W9 pair outputs."""
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

spec = importlib.util.spec_from_file_location('w9_trace_base', PRIOR / 'circuit.py')
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> index & 1 for index, wire in enumerate(wires)})


fixture = json.loads((PRIOR / 'fixture.json').read_text())
baseline = json.loads((PRIOR / 'screen_result.json').read_text())
trace_census = json.loads((HERE / 'census_trace_result.json').read_text())
assert trace_census['status'] == 'PASS_INDEPENDENT_TRACE_SOURCE_AND_TARGET_PARITY'
target = fixture['oriented_target_reciprocal']
start = time.monotonic_ns()
circ, wires, counts = design.build(target, 'table5')
assert counts == next(row['counts'] for row in baseline['rows'] if row['variant'] == 'table5')
baseline_path = HERE / 'table5_baseline.xcnf'
circ.write(baseline_path)
assert sha(baseline_path) == next(row['formula_sha256'] for row in baseline['rows']
                                  if row['variant'] == 'table5')
old_counts = (len(circ.clauses), len(circ.xors), circ.next_var - 1)
target_trace = design.trace(target)
parity_wires = [wire for row in wires['out'] for wire, tr in zip(row, design.TRACE) if tr]
assert len(parity_wires) == 5 * sum(design.TRACE)
circ.require_zero([circ.xor(parity_wires + ([-1] if target_trace else []))])
new_counts = (len(circ.clauses), len(circ.xors), circ.next_var - 1)
assert new_counts[1] == old_counts[1] + 1
assignment = {}
for slot, row in enumerate(fixture['pairs']):
    code = sum(((row['masks'][0] >> bit) & 1) << index
               for index, bit in enumerate(design.BITS))
    bind(assignment, wires['mask'][slot], code)
    bind(assignment, wires['out'][slot], row['output_reciprocal'])
for bits, value in zip(wires['middle'], fixture['middle_reciprocals']):
    bind(assignment, bits, value)
full = selector.old.complete_assignment(circ, assignment)
check = selector.old.check_assignment(circ, full)
assert check['clauses'] == len(circ.clauses)
assert check['native_xor_rows'] == len(circ.xors)
path = HERE / 'table5_trace.xcnf'
circ.write(path)
result = {'status': 'PASS_N41_TRACE_GATE_CONSTRUCTED_ASSIGNMENT',
          'curve_id': fixture['curve_id'],
          'oriented_raw_point': fixture['oriented_raw_point'],
          'target_reciprocal': target, 'target_trace': target_trace,
          'output_trace_basis_weight': sum(design.TRACE),
          'global_parity_input_wires': len(parity_wires),
          'baseline_counts': {'clauses': old_counts[0], 'xor_rows': old_counts[1],
                              'variables': old_counts[2]},
          'trace_counts': {'clauses': new_counts[0], 'xor_rows': new_counts[1],
                           'variables': new_counts[2]},
          'assignment_check': check, 'elapsed_ns': time.monotonic_ns() - start,
          'baseline_sha256': sha(baseline_path), 'trace_sha256': sha(path),
          'source_sha256': {name: sha(source) for name, source in
                            {'script': Path(__file__), 'circuit': PRIOR / 'circuit.py',
                             'fixture': PRIOR / 'fixture.json',
                             'census': HERE / 'census_trace_result.json',
                             'runtime': HERE / 'sage_runtime_info.json',
                             'selector': Path(selector.__file__),
                             'checker': Path(selector.old.__file__)}.items()}}
with (HERE / 'build_n41_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'], 'target_trace': target_trace,
                  'global_parity_input_wires': len(parity_wires),
                  'baseline_counts': result['baseline_counts'],
                  'trace_counts': result['trace_counts']}))
