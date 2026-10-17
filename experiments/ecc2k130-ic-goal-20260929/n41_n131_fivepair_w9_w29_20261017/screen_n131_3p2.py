"""Check the balanced W29 five-pair assignment and public circuit size."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import selector
import circuit_n131_3p2 as design


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(values, wires, word):
    values.update({wire: word >> bit & 1 for bit, wire in enumerate(wires)})


control_path = HERE / 'n131_control_3p2.json'
public_path = ROOT / 'n131_w23_sixpair_public_sat_20261017/protocol.json'
control = json.loads(control_path.read_text())
public = json.loads(public_path.read_text())
assert control['status'] == 'COMPLETE_CONSTRUCTED_CONTROL'
assert public['curve_id'] == control['curve_id']
public_x = public['raw_point'][0]
public_reciprocal = design.F.inverse(public_x)
assert public_reciprocal == 770794657550069419943936485965613853151
rows = []
for name, target in (('control', control['target_reciprocal']),
                     ('public', public_reciprocal)):
    start = time.monotonic_ns()
    circ, wires, counts = design.build(target)
    built = time.monotonic_ns()
    check = None
    if name == 'control':
        assignment = {}
        for slot, row in enumerate(control['pairs']):
            code = sum(((row['masks'][0] >> bit) & 1) << j
                       for j, bit in enumerate(design.BITS))
            bind(assignment, wires['mask'][slot], code)
            bind(assignment, wires['out'][slot], row['output_reciprocal'])
            bind(assignment, wires['source_inverse'][slot], row['source_inverse_product'])
        for bits, value in zip(wires['middle'], control['middle_reciprocals']):
            bind(assignment, bits, value)
        full = selector.old.complete_assignment(circ, assignment)
        check = selector.old.check_assignment(circ, full)
        assert check['clauses'] == len(circ.clauses)
        assert check['native_xor_rows'] == len(circ.xors)
    checked = time.monotonic_ns()
    rows.append({'target': name, 'target_reciprocal': target, **counts,
                 'build_ns': built - start, 'check_ns': checked - built,
                 'constructed_check': check,
                 'peak_self_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    print(json.dumps({'target': name, 'counts': counts, 'constructed_check': check}), flush=True)
result = {'status': 'COMPLETE_CIRCUIT_SCREEN', 'candidate_id': None,
          'curve_id': control['curve_id'], 'workload_id': public['workload_id'],
          'public_point': public['public_target'],
          'raw_public_point': public['raw_point'], 'rows': rows,
          'source_sha256': {path.name: sha(path) for path in
                            (Path(__file__), HERE / 'circuit_n131_3p2.py', control_path,
                             public_path, HERE / 'sage_runtime_info.json',
                             Path(design.previous.__file__),
                             Path(selector.__file__), Path(selector.old.__file__))}}
with (HERE / 'n131_circuit_result_3p2.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
