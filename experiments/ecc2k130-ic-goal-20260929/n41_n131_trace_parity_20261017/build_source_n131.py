"""Bind the N131 public trace to the existing five source tensors."""
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

spec = importlib.util.spec_from_file_location('w29_source_base', PRIOR / 'circuit_n131_3p2.py')
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> index & 1 for index, wire in enumerate(wires)})


coeff = json.loads((HERE / 'source_trace_coeff_result.json').read_text())
assert coeff['status'] == 'PASS_SOURCE_TENSOR_TRACE_COEFFICIENTS'
control = json.loads((PRIOR / 'n131_control_3p2.json').read_text())
public = json.loads(PUBLIC.read_text())
assert control['curve_id'] == public['curve_id']


def attach(target):
    circ, wires, counts = design.build(target)
    old_counts = (len(circ.clauses), len(circ.xors), circ.next_var - 1, circ.and_count)
    terms = [circ.and_(masks[i], inverse[j])
             for masks, inverse in zip(wires['mask'], wires['source_inverse'])
             for i, j in coeff['n131']['coefficients']]
    assert circ.and_count == old_counts[3]
    target_trace = design.previous.trace(target)
    circ.require_zero([circ.xor(terms + ([-1] if target_trace else []))])
    new_counts = (len(circ.clauses), len(circ.xors), circ.next_var - 1, circ.and_count)
    assert new_counts[1] == old_counts[1] + 1
    assert new_counts[3] == old_counts[3]
    return circ, wires, counts, old_counts, new_counts, target_trace, len(terms)


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
public_circ, _, public_counts, public_old, public_new, trace_public, public_wire_count = attach(public_target)
assert public_counts == counts and public_old == old_counts and public_new == new_counts
assert public_wire_count == wire_count
baseline_path = HERE / 'n131_baseline.xcnf'
assert sha(baseline_path) == sha(PRIOR / 'n131_3p2_ordinary.xcnf')
path = HERE / 'n131_source_trace.xcnf'
assert not path.exists()
public_circ.write(path)
done = time.monotonic_ns()
result = {'status': 'PASS_N131_SOURCE_TRACE_GATE_CONSTRUCTED_ASSIGNMENT',
          'curve_id': control['curve_id'], 'public_raw_point': public['raw_point'],
          'public_target_reciprocal': public_target,
          'control_target_trace': trace_control,
          'public_target_trace': trace_public,
          'source_trace_input_wires': wire_count,
          'per_slot_coefficient_weight': coeff['n131']['coefficient_weight'],
          'baseline_counts': {'clauses': old_counts[0], 'xor_rows': old_counts[1],
                              'variables': old_counts[2], 'and_gates': old_counts[3]},
          'source_counts': {'clauses': new_counts[0], 'xor_rows': new_counts[1],
                            'variables': new_counts[2], 'and_gates': new_counts[3]},
          'control_assignment_check': check,
          'control_build_and_check_ns': control_done - start,
          'public_build_and_write_ns': done - control_done,
          'baseline_sha256': sha(baseline_path), 'source_trace_sha256': sha(path),
          'source_sha256': {name: sha(source) for name, source in
                            {'script': Path(__file__), 'circuit': PRIOR / 'circuit_n131_3p2.py',
                             'control': PRIOR / 'n131_control_3p2.json', 'public': PUBLIC,
                             'coefficients': HERE / 'source_trace_coeff_result.json',
                             'runtime': HERE / 'sage_runtime_info.json',
                             'selector': Path(selector.__file__),
                             'checker': Path(selector.old.__file__)}.items()}}
with (HERE / 'build_source_n131_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'source_trace_input_wires': wire_count,
                  'baseline_counts': result['baseline_counts'],
                  'source_counts': result['source_counts']}))
