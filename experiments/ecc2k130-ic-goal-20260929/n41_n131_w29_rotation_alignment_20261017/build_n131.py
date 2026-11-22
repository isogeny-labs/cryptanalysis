"""Build the aligned W29 public formula and independently checked control."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'
PUBLIC = ROOT / 'n131_w23_sixpair_public_sat_20261017/protocol.json'
TRACE = ROOT / 'n41_n131_trace_parity_20261017'
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import selector

spec = importlib.util.spec_from_file_location('w29_aligned_design', SOURCE)
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> index & 1 for index, wire in enumerate(wires)})


def build(target):
    circ, wires, base_counts = design.build(target)
    parity_wires = [wire for row in wires['out']
                    for wire, tr in zip(row, design.TRACE) if tr]
    assert len(parity_wires) == 10
    target_trace = design.previous.trace(target)
    circ.require_zero([circ.xor(parity_wires + ([-1] if target_trace else []))])
    counts = {'and_gates': circ.and_count, 'variables': circ.next_var - 1,
              'clauses': len(circ.clauses), 'xor_rows': len(circ.xors)}
    return circ, wires, base_counts, counts, target_trace


control = json.loads((HERE / 'n131_aligned_control.json').read_text())
public = json.loads(PUBLIC.read_text())
old = json.loads((TRACE / 'build_n131_result.json').read_text())
assert control['status'] == 'PASS_N131_ALIGNED_CONSTRUCTED_GROUP_CONTROL'
assert design.ROTATIONS == control['original_rotations']
assert public['curve_id'] == control['curve_id'] == old['curve_id']
design.ROTATIONS = control['aligned_rotations']
constructed, wires, control_base, control_counts, control_trace = build(control['target_reciprocal'])
assignment = {}
for slot, row in enumerate(control['pairs']):
    code = sum(((row['masks'][0] >> bit) & 1) << index
               for index, bit in enumerate(design.BITS))
    bind(assignment, wires['mask'][slot], code)
    bind(assignment, wires['out'][slot], row['output_reciprocal'])
    bind(assignment, wires['source_inverse'][slot], row['source_inverse_product'])
for bits, value in zip(wires['middle'], control['middle_reciprocals']):
    bind(assignment, bits, value)
full = selector.old.complete_assignment(constructed, assignment)
check = selector.old.check_assignment(constructed, full)
assert check['clauses'] == control_counts['clauses']
assert check['native_xor_rows'] == control_counts['xor_rows']

public_target = design.F.inverse(public['raw_point'][0])
assert public_target == old['public_target_reciprocal']
circ, public_wires, base_counts, counts, target_trace = build(public_target)
assert counts == control_counts and base_counts == control_base
path = HERE / 'n131_aligned_trace.xcnf'
circ.write(path)
result = {'status': 'PASS_N131_ALIGNED_CONSTRUCTED_AND_PUBLIC_FORMULA',
          'curve_id': control['curve_id'],
          'public_raw_point': public['raw_point'],
          'public_subgroup_point': public['public_target'],
          'public_target_reciprocal': public_target,
          'public_target_trace': target_trace,
          'rotations': design.ROTATIONS,
          'constructed_control_target': control['raw_target'],
          'constructed_control_trace': control_trace,
          'constructed_assignment_check': check,
          'base_counts': base_counts, 'counts': counts,
          'formula_bytes': path.stat().st_size,
          'formula_sha256': sha(path),
          'original_formula_sha256': old['trace_sha256'],
          'source_sha256': {name: sha(p) for name, p in
                            {'script': Path(__file__), 'circuit': SOURCE,
                             'previous_circuit': Path(design.previous.__file__),
                             'control': HERE / 'n131_aligned_control.json',
                             'public': PUBLIC, 'original_build': TRACE / 'build_n131_result.json',
                             'selector': Path(selector.__file__),
                             'checker': Path(selector.old.__file__),
                             'runtime': HERE / 'sage_runtime_info.json'}.items()}}
with (HERE / 'build_n131_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'], 'counts': counts,
                  'constructed_assignment_check': check,
                  'formula_sha256': result['formula_sha256']}))
