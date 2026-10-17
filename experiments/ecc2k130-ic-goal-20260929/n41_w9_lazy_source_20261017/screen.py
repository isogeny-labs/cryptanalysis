"""Constructed assignment checks and frozen public formulas for W9 gates."""
import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import selector
spec = importlib.util.spec_from_file_location('w9_lazy_circuit', HERE / 'circuit.py')
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> bit & 1 for bit, wire in enumerate(wires)})


fixture = json.loads((HERE / 'fixture.json').read_text())
target = fixture['oriented_target_reciprocal']
rows = []
for variant in ('exact5', 'exact3', 'table5'):
    start = time.monotonic_ns()
    circ, wires, counts = design.build(target, variant)
    built = time.monotonic_ns()
    assignment = {}
    for slot, row in enumerate(fixture['pairs']):
        code = sum(((row['masks'][0] >> bit) & 1) << j
                   for j, bit in enumerate(design.BITS))
        bind(assignment, wires['mask'][slot], code)
        bind(assignment, wires['out'][slot], row['output_reciprocal'])
        if wires['source_inverse'][slot] is not None:
            bind(assignment, wires['source_inverse'][slot],
                 row['source_inverse_product'])
    for bits, value in zip(wires['middle'], fixture['middle_reciprocals']):
        bind(assignment, bits, value)
    full = selector.old.complete_assignment(circ, assignment)
    check = selector.old.check_assignment(circ, full)
    assert check['clauses'] == counts['clauses']
    assert check['native_xor_rows'] == counts['xor_rows']
    checked = time.monotonic_ns()
    path = HERE / (variant + '.xcnf')
    assert not path.exists()
    circ.write(path)
    written = time.monotonic_ns()
    rows.append({'variant': variant, 'counts': counts,
                 'constructed_check': check, 'build_ns': built - start,
                 'check_ns': checked - built, 'write_ns': written - checked,
                 'formula_bytes': path.stat().st_size,
                 'formula_sha256': sha(path),
                 'peak_self_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    print(json.dumps(rows[-1]), flush=True)

result = {'status': 'COMPLETE_CONSTRUCTED_CIRCUIT_SCREEN',
          'curve_id': fixture['curve_id'],
          'oriented_raw_point': fixture['oriented_raw_point'],
          'target_reciprocal': target, 'rows': rows,
          'source_sha256': {path.name: sha(path) for path in
                            (Path(__file__), HERE / 'circuit.py',
                             HERE / 'fixture.json', design.SOURCE,
                             HERE / 'sage_runtime_info.json',
                             Path(selector.__file__), Path(selector.old.__file__))}}
with (HERE / 'screen_result.json').open('x') as output:
    json.dump(result, output, indent=2, sort_keys=True)
    output.write('\n')
