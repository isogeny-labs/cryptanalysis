"""Build the constructed W33 deferred-source positive control."""
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
import circuit_deferred as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


index = int(sys.argv[1])
assert index == 0
cfg = json.loads((HERE / 'build_protocol.json').read_text())
for name, expected in cfg['sources'].items():
    assert sha(name) == expected, name
assert cfg['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
assert design.WIDTH == 33 and len(design.BITS) == 32
rank = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' / 'coefficients.json').read_text())
assert rank['source_product_rank'] == 32
control = json.loads((ROOT / 'n41_n131_fivepair_w9_w29_20261017' / 'n131_control_3p2.json').read_text())
public = json.loads((ROOT / 'n131_w23_sixpair_public_sat_20261017' / 'protocol.json').read_text())
assert control['status'] == 'COMPLETE_CONSTRUCTED_CONTROL'
assert control['curve_id'] == public['curve_id'] == cfg['curve_id']
assert control['rotations'] == design.ROTATIONS
assert public['raw_point'][0] != 0
target = (control['target_reciprocal'] if index == 0
          else design.F.inverse(public['raw_point'][0]))
assert target
started = time.monotonic()
circ, wires, counts = design.build(target)
build_seconds = time.monotonic()-started
check = None
codes = None
if index == 0:
    assignment = {}

    def bind(wire_bits, value):
        assignment.update({wire: (value >> j) & 1
                           for j, wire in enumerate(wire_bits)})

    codes = []
    for slot, row in enumerate(control['pairs']):
        code = sum(((row['masks'][0] >> bit) & 1) << j
                   for j, bit in enumerate(design.BITS))
        codes.append(code)
        bind(wires['mask'][slot], code)
        bind(wires['out'][slot], row['output_reciprocal'])
        if wires['source_inverse'][slot] is not None:
            bind(wires['source_inverse'][slot], row['source_inverse_product'])
    for bits, value in zip(wires['middle'], control['middle_reciprocals']):
        bind(bits, value)
    full = selector.old.complete_assignment(circ, assignment)
    check = selector.old.check_assignment(circ, full)
    assert check == {'clauses': counts['clauses'],
                     'native_xor_rows': counts['xor_rows']}
    assert codes == [3, 18, 19, 22, 29]
check_seconds = time.monotonic()-started-build_seconds
formula = HERE / 'positive.xcnf'
assert not formula.exists()
circ.write(formula)
serialize_seconds = time.monotonic()-started-build_seconds-check_seconds
result = {'status': 'PASS_W33_DEFERRED_POSITIVE_CIRCUIT',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'target_index': index, 'target_reciprocal': target,
          'target_point': (control['target_raw_point'] if index == 0
                           else public['raw_point']),
          'constructed_codes': codes, 'positive_assignment_check': check,
          'counts': counts, 'formula_bytes': formula.stat().st_size,
          'formula_sha256': sha(formula),
          'build_seconds': build_seconds, 'check_seconds': check_seconds,
          'serialize_seconds': serialize_seconds,
          'wall_seconds': time.monotonic()-started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'build_protocol.json')}
(HERE / f'build_{index}_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': result['status'], 'target_index': index,
                  'counts': counts, 'wall_seconds': result['wall_seconds'],
                  'formula_bytes': result['formula_bytes']}, sort_keys=True))
