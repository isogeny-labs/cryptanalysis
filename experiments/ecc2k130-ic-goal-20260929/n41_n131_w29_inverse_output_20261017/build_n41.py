"""Build and independently bind the unpinned N41 inverse-output control."""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_w9_lazy_source_20261017'
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import selector
import inverse_output as design


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(assignment, wires, word):
    assignment.update({wire: word >> bit & 1 for bit, wire in enumerate(wires)})


fixture = json.loads((PRIOR / 'fixture.json').read_text())
target = fixture['oriented_target_reciprocal']
start = time.monotonic_ns()
circ, wires, counts, decoder = design.build(target, 'n41', add_target_trace=True)
constructed = time.monotonic_ns()
assignment = {}
for slot, row in enumerate(fixture['pairs']):
    z = row['output_reciprocal']
    bind(assignment, wires['out'][slot], z)
    bind(assignment, wires['output_inverse'][slot], design.n41.F.inverse(z))
    bind(assignment, wires['source_inverse'][slot], row['source_inverse_product'])
for bits, value in zip(wires['middle'], fixture['middle_reciprocals']):
    bind(assignment, bits, value)
full = selector.old.complete_assignment(circ, assignment)
check = selector.old.check_assignment(circ, full)
assert check['clauses'] == counts['clauses']
assert check['native_xor_rows'] == counts['xor_rows']
for slot, row in enumerate(fixture['pairs']):
    actual_code = sum(full[wire] << bit for bit, wire in enumerate(wires['mask'][slot]))
    expected_code = sum(((row['masks'][0] >> bit) & 1) << i
                        for i, bit in enumerate(design.n41.BITS))
    assert actual_code == expected_code
checked = time.monotonic_ns()
path = HERE / 'n41_inverse_output_trace.xcnf'
circ.write(path)
result = {'status': 'PASS_N41_INVERSE_OUTPUT_CONSTRUCTED_ASSIGNMENT',
          'curve_id': fixture['curve_id'],
          'public_raw_point': fixture['oriented_raw_point'],
          'target_reciprocal': target,
          'counts': counts, 'decoder': decoder,
          'assignment_check': check,
          'construction_ns': constructed - start,
          'assignment_check_ns': checked - constructed,
          'formula_sha256': sha(path),
          'source_sha256': {name: sha(source) for name, source in
                            {'script': Path(__file__), 'circuit': HERE / 'inverse_output.py',
                             'fixture': PRIOR / 'fixture.json',
                             'runtime': HERE / 'sage_runtime_info.json',
                             'checker': Path(selector.old.__file__)}.items()}}
with (HERE / 'build_n41_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'], 'counts': counts,
                  'construction_seconds': (constructed-start)/1e9}))
