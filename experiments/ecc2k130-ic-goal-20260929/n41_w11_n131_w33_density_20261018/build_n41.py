"""Build an exact N41 W11 aligned source on the frozen public point."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_w9_lazy_source_20261017'))
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import circuit as design
import selector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'n41_build_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'n41_formula.xcnf').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('N41 W11 build cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
fixture = json.loads(Path(protocol['fixture']).read_text())
assert fixture['status'] == 'PASS_ALIGNED_N41_EXACT_S3_MODEL'
assert fixture['curve_id'] == protocol['curve_id']

design.WIDTH = 11
design.BITS = [bit for bit in range(11) if bit != design.SEED_MASK.bit_length() - 1]
design.BASE = [1 << (bit + 1) for bit in design.BITS]
design.PB = [design.F.square(word) ^ design.F.mul(design.SEED, word)
             for word in design.BASE]
design.ROTATIONS = [0, 0, 12, 12, 24]
assert len(design.BITS) == 10
assert fixture['rotations'] == design.ROTATIONS


def bit_or(circ, a, b):
    return circ.xor((a, b, circ.and_(a, b)))


def strict_less(circ, left, right):
    less = 0
    for a, b in zip(left, right):
        equal = circ.xor((a, b, -1))
        smaller_here = circ.and_(circ.xor((a, -1)), b)
        less = bit_or(circ, smaller_here, circ.and_(equal, less))
    return less


def bind(values, wires, word):
    values.update({wire: word >> bit & 1 for bit, wire in enumerate(wires)})


circ, wires, base_counts = design.build(fixture['target_reciprocal'], 'exact5')
for masks in wires['mask']:
    circ.require_zero([circ.xor(wire for wire, value in zip(masks, design.BASE)
                                if design.trace(value))])
parity_wires = [wire for row in wires['out']
                for wire, trace in zip(row, design.TRACE) if trace]
target_trace = design.trace(fixture['target_reciprocal'])
circ.require_zero([circ.xor(parity_wires + ([-1] if target_trace else []))])
for left in range(5):
    for right in range(left + 1, 5):
        diff = [circ.xor((a, b)) for a, b in
                zip(wires['mask'][left], wires['mask'][right])]
        circ.clauses.append(' '.join(map(str, diff)) + ' 0')
for left, right in ((0, 1), (3, 4)):
    circ.clauses.append(f'{strict_less(circ, wires["mask"][left], wires["mask"][right])} 0')

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

path = HERE / 'n41_formula.xcnf'
circ.write(path)
wire_record = {'mask': wires['mask'], 'out': wires['out'],
               'source_inverse': wires['source_inverse'],
               'middle': wires['middle'],
               'source_bits': design.BITS,
               'raw_oriented_point': fixture['raw_oriented_point'],
               'public_reciprocal': fixture['target_reciprocal'],
               'rotations': design.ROTATIONS}
(HERE / 'n41_input_wires.json').write_text(json.dumps(wire_record, sort_keys=True, indent=2) + '\n')
finished = time.monotonic()
signal.alarm(0)
result = {'status': 'PASS_N41_W11_ALIGNED_CONSTRUCTED_CONTROL',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'source_bits': design.BITS,
          'source_basis': design.BASE,
          'product_basis': design.PB,
          'source_trace_nonzero_basis_bits':
              [bit for bit, word in zip(design.BITS, design.BASE) if design.trace(word)],
          'rotations': design.ROTATIONS,
          'public_raw_point': fixture['raw_oriented_point'],
          'public_reciprocal': fixture['target_reciprocal'],
          'base_counts': base_counts, 'counts': counts,
          'constructed_assignment_check': check,
          'formula_bytes': path.stat().st_size,
          'formula_sha256': sha(path),
          'input_wires_sha256': sha(HERE / 'n41_input_wires.json'),
          'wall_seconds': finished - started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'n41_build_protocol.json')}
(HERE / 'n41_build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'counts', 'wall_seconds',
                   'source_trace_nonzero_basis_bits')}, sort_keys=True))
