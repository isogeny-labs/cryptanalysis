"""Add exact slot-permutation symmetry cuts to aligned N41 source masks."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_w9_lazy_source_20261017/circuit.py'
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import selector

spec = importlib.util.spec_from_file_location('w9_aligned_ordered', SOURCE)
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> index & 1 for index, wire in enumerate(wires)})


def bit_or(circ, a, b):
    return circ.xor((a, b, circ.and_(a, b)))


def strict_less(circ, left, right):
    assert len(left) == len(right)
    less = 0
    for a, b in zip(left, right):
        equal = circ.xor((a, b, -1))
        smaller_here = circ.and_(circ.xor((a, -1)), b)
        less = bit_or(circ, smaller_here, circ.and_(equal, less))
    return less


fixture = json.loads((HERE / 'n41_model_fixture.json').read_text())
prior = json.loads((HERE / 'build_n41_result.json').read_text())
assert fixture['status'] == 'PASS_ALIGNED_N41_EXACT_S3_MODEL'
assert prior['status'] == 'PASS_N41_ALIGNED_MODEL_AND_MATCHED_FORMULAS'
assert fixture['pairs'][0]['masks'][0] < fixture['pairs'][1]['masks'][0]
assert fixture['pairs'][3]['masks'][0] < fixture['pairs'][4]['masks'][0]
design.ROTATIONS = [0, 0, 12, 12, 24]
circ, wires, base_counts = design.build(fixture['target_reciprocal'], 'exact5')
trace_wires = [wire for row in wires['out']
               for wire, tr in zip(row, design.TRACE) if tr]
assert len(trace_wires) == 5 and design.trace(fixture['target_reciprocal']) == 0
circ.require_zero([circ.xor(trace_wires)])
for a, b in ((0, 1), (3, 4)):
    circ.clauses.append(f'{strict_less(circ, wires["mask"][a], wires["mask"][b])} 0')
counts = {'and_gates': circ.and_count, 'variables': circ.next_var - 1,
          'clauses': len(circ.clauses), 'xor_rows': len(circ.xors)}
assignment = {}
for slot, row in enumerate(fixture['pairs']):
    code = sum(((row['masks'][0] >> bit) & 1) << index
               for index, bit in enumerate(design.BITS))
    bind(assignment, wires['mask'][slot], code)
    bind(assignment, wires['out'][slot], row['output_reciprocal'])
    bind(assignment, wires['source_inverse'][slot], row['source_inverse_product'])
for bits, value in zip(wires['middle'], fixture['middle_reciprocals']):
    bind(assignment, bits, value)
full = selector.old.complete_assignment(circ, assignment)
check = selector.old.check_assignment(circ, full)
assert check['clauses'] == counts['clauses']
assert check['native_xor_rows'] == counts['xor_rows']
path = HERE / 'n41_aligned_ordered.xcnf'
circ.write(path)
result = {'status': 'PASS_N41_ALIGNED_ORDERED_MODEL',
          'curve_id': fixture['curve_id'],
          'raw_oriented_point': fixture['raw_oriented_point'],
          'target_reciprocal': fixture['target_reciprocal'],
          'rotations': design.ROTATIONS,
          'order_rule': [[0, 1], [3, 4]],
          'base_counts': base_counts, 'counts': counts,
          'assignment_check': check,
          'formula_bytes': path.stat().st_size, 'formula_sha256': sha(path),
          'source_sha256': {name: sha(p) for name, p in
                            {'script': Path(__file__), 'circuit': SOURCE,
                             'fixture': HERE / 'n41_model_fixture.json',
                             'prior_build': HERE / 'build_n41_result.json',
                             'selector': Path(selector.__file__),
                             'checker': Path(selector.old.__file__),
                             'runtime': HERE / 'sage_runtime_info.json'}.items()}}
with (HERE / 'build_n41_ordered_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'], 'counts': counts,
                  'assignment_check': check, 'formula_sha256': result['formula_sha256']}))
