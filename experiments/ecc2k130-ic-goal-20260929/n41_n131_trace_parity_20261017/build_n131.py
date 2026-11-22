"""Add global trace parity to the frozen W29 three-plus-two N131 circuit."""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_fivepair_w9_w29_20261017'
PUBLIC = ROOT / 'n131_w23_sixpair_public_sat_20261017/protocol.json'
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import selector

spec = importlib.util.spec_from_file_location('w29_trace_base', PRIOR / 'circuit_n131_3p2.py')
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> index & 1 for index, wire in enumerate(wires)})


def attach(target):
    circ, wires, counts = design.build(target)
    old_counts = (len(circ.clauses), len(circ.xors), circ.next_var - 1)
    trace_wires = [wire for row in wires['out']
                   for wire, tr in zip(row, design.TRACE) if tr]
    target_trace = design.previous.trace(target)
    assert len(trace_wires) == 5 * sum(design.TRACE)
    circ.require_zero([circ.xor(trace_wires + ([-1] if target_trace else []))])
    new_counts = (len(circ.clauses), len(circ.xors), circ.next_var - 1)
    assert new_counts[1] == old_counts[1] + 1
    return circ, wires, counts, old_counts, new_counts, target_trace, len(trace_wires)


control_path = PRIOR / 'n131_control_3p2.json'
control = json.loads(control_path.read_text())
public = json.loads(PUBLIC.read_text())
assert control['curve_id'] == public['curve_id']
start = time.monotonic_ns()
circ, wires, counts, old_counts, new_counts, trace_control, wire_count = attach(
    control['target_reciprocal'])
assignment = {}
for slot, row in enumerate(control['pairs']):
    code = sum(((row['masks'][0] >> bit) & 1) << index
               for index, bit in enumerate(design.BITS))
    bind(assignment, wires['mask'][slot], code)
    bind(assignment, wires['out'][slot], row['output_reciprocal'])
    bind(assignment, wires['source_inverse'][slot], row['source_inverse_product'])
for bits, value in zip(wires['middle'], control['middle_reciprocals']):
    bind(assignment, bits, value)
full = selector.old.complete_assignment(circ, assignment)
check = selector.old.check_assignment(circ, full)
assert check['clauses'] == new_counts[0]
assert check['native_xor_rows'] == new_counts[1]
control_done = time.monotonic_ns()

public_target = design.F.inverse(public['raw_point'][0])
assert public_target == 770794657550069419943936485965613853151
public_circ, public_wires, public_counts, public_old, public_new, trace_public, public_wire_count = attach(public_target)
assert public_counts == counts and public_old == old_counts and public_new == new_counts
assert public_wire_count == wire_count
baseline_path = HERE / 'n131_baseline.xcnf'
assert not baseline_path.exists()
baseline_circ, _, baseline_counts = design.build(public_target)
assert baseline_counts == counts
baseline_circ.write(baseline_path)
frozen_baseline = PRIOR / 'n131_3p2_ordinary.xcnf'
assert sha(baseline_path) == sha(frozen_baseline)
trace_path = HERE / 'n131_trace.xcnf'
assert not trace_path.exists()
public_circ.write(trace_path)
done = time.monotonic_ns()
result = {'status': 'PASS_N131_TRACE_GATE_CONSTRUCTED_ASSIGNMENT',
          'curve_id': control['curve_id'],
          'public_raw_point': public['raw_point'],
          'public_target_reciprocal': public_target,
          'control_target_trace': trace_control,
          'public_target_trace': trace_public,
          'trace_basis_weight': sum(design.TRACE),
          'global_parity_input_wires': wire_count,
          'baseline_counts': {'clauses': old_counts[0], 'xor_rows': old_counts[1],
                              'variables': old_counts[2]},
          'trace_counts': {'clauses': new_counts[0], 'xor_rows': new_counts[1],
                           'variables': new_counts[2]},
          'control_assignment_check': check,
          'control_build_and_check_ns': control_done - start,
          'public_build_and_write_ns': done - control_done,
          'baseline_sha256': sha(baseline_path), 'trace_sha256': sha(trace_path),
          'source_sha256': {name: sha(path) for name, path in
                            {'script': Path(__file__), 'circuit': PRIOR / 'circuit_n131_3p2.py',
                             'previous_circuit': Path(design.previous.__file__),
                             'control': control_path, 'public': PUBLIC,
                             'census': HERE / 'census_trace_result.json',
                             'runtime': HERE / 'sage_runtime_info.json',
                             'selector': Path(selector.__file__),
                             'checker': Path(selector.old.__file__)}.items()}}
with (HERE / 'build_n131_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'trace_basis_weight': result['trace_basis_weight'],
                  'global_parity_input_wires': wire_count,
                  'baseline_counts': result['baseline_counts'],
                  'trace_counts': result['trace_counts'],
                  'public_target_trace': trace_public}))
