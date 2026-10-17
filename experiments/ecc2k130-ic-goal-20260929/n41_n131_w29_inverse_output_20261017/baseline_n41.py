"""Matched exact-source N41 circuit with the same target trace row."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_w9_lazy_source_20261017'
PREVIOUS = ROOT / 'n41_n131_trace_parity_20261017'
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import selector
import inverse_output as design


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> bit & 1 for bit, wire in enumerate(wires)})


fixture = json.loads((PRIOR / 'fixture.json').read_text())
target = fixture['oriented_target_reciprocal']
circ, wires, counts = design.n41.build(target, 'exact5')
baseline = HERE / 'n41_exact5_baseline.xcnf'
circ.write(baseline)
assert sha(baseline) == sha(PREVIOUS / 'exact5_baseline.xcnf')
parity = [wire for row in wires['out'] for wire, tr in zip(row, design.n41.TRACE) if tr]
circ.require_zero([circ.xor(parity + ([-1] if design.n41.trace(target) else []))])
assignment = {}
for slot, row in enumerate(fixture['pairs']):
    code = sum(((row['masks'][0] >> bit) & 1) << i
               for i, bit in enumerate(design.n41.BITS))
    bind(assignment, wires['mask'][slot], code)
    bind(assignment, wires['source_inverse'][slot], row['source_inverse_product'])
    bind(assignment, wires['out'][slot], row['output_reciprocal'])
for bits, value in zip(wires['middle'], fixture['middle_reciprocals']):
    bind(assignment, bits, value)
full = selector.old.complete_assignment(circ, assignment)
check = selector.old.check_assignment(circ, full)
assert check['clauses'] == len(circ.clauses)
assert check['native_xor_rows'] == len(circ.xors)
path = HERE / 'n41_exact5_output_trace.xcnf'
circ.write(path)
result = {'status': 'PASS_N41_MATCHED_BASELINE_CONSTRUCTED_ASSIGNMENT',
          'curve_id': fixture['curve_id'], 'public_raw_point': fixture['oriented_raw_point'],
          'target_reciprocal': target, 'baseline_counts': counts,
          'trace_counts': {'and_gates': circ.and_count, 'variables': circ.next_var-1,
                           'clauses': len(circ.clauses), 'xor_rows': len(circ.xors)},
          'assignment_check': check, 'baseline_sha256': sha(baseline),
          'trace_sha256': sha(path),
          'source_sha256': {name: sha(source) for name, source in
                            {'script': Path(__file__), 'circuit': PRIOR / 'circuit.py',
                             'fixture': PRIOR / 'fixture.json',
                             'runtime': HERE / 'sage_runtime_info.json',
                             'checker': Path(selector.old.__file__)}.items()}}
with (HERE / 'baseline_n41_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'], 'trace_counts': result['trace_counts']}))
