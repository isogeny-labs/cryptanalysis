"""Build same-target exact-source N41 formulas for two slot rotations."""
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

spec = importlib.util.spec_from_file_location('w9_aligned_design', SOURCE)
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> index & 1 for index, wire in enumerate(wires)})


fixture = json.loads((HERE / 'n41_model_fixture.json').read_text())
assert fixture['status'] == 'PASS_ALIGNED_N41_EXACT_S3_MODEL'
target = fixture['target_reciprocal']
assert design.ROTATIONS == [0, 6, 12, 18, 24]
assert fixture['rotations'] == [0, 0, 12, 12, 24]
rows = {}
for variant, rotations in (('original', [0, 6, 12, 18, 24]),
                           ('aligned', [0, 0, 12, 12, 24])):
    design.ROTATIONS = rotations
    circ, wires, counts = design.build(target, 'exact5')
    parity_wires = [wire for row in wires['out']
                    for wire, tr in zip(row, design.TRACE) if tr]
    assert len(parity_wires) == 5
    target_trace = design.trace(target)
    circ.require_zero([circ.xor(parity_wires + ([-1] if target_trace else []))])
    final_counts = {'and_gates': circ.and_count,
                    'variables': circ.next_var - 1,
                    'clauses': len(circ.clauses),
                    'xor_rows': len(circ.xors)}
    assignment_check = None
    if variant == 'aligned':
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
        assignment_check = selector.old.check_assignment(circ, full)
        assert assignment_check['clauses'] == final_counts['clauses']
        assert assignment_check['native_xor_rows'] == final_counts['xor_rows']
    path = HERE / f'n41_{variant}.xcnf'
    circ.write(path)
    rows[variant] = {'rotations': rotations, 'base_counts': counts,
                     'trace_counts': final_counts,
                     'target_trace': target_trace,
                     'assignment_check': assignment_check,
                     'formula_bytes': path.stat().st_size,
                     'formula_sha256': sha(path)}

result = {'status': 'PASS_N41_ALIGNED_MODEL_AND_MATCHED_FORMULAS',
          'curve_id': fixture['curve_id'],
          'raw_oriented_point': fixture['raw_oriented_point'],
          'target_reciprocal': target, 'rows': rows,
          'source_sha256': {name: sha(path) for name, path in
                            {'script': Path(__file__), 'circuit': SOURCE,
                             'fixture': HERE / 'n41_model_fixture.json',
                             'selector': Path(selector.__file__),
                             'checker': Path(selector.old.__file__),
                             'runtime': HERE / 'sage_runtime_info.json'}.items()}}
with (HERE / 'build_n41_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'], 'rows': rows}, sort_keys=True))
