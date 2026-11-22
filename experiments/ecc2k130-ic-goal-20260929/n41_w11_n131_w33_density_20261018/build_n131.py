"""Construct the W33 N131 aligned public circuit after an N41 promotion gate."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_n131_fivepair_w9_w29_20261017'))
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import circuit_n131_3p2 as design
import selector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'n131_build_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'n131_formula.xcnf').exists()
assert json.loads((HERE / 'n41_query_result.json').read_text())['status'] == 'SAT_MODEL_UNVERIFIED'
assert json.loads((HERE / 'n41_group_replay.json').read_text())['status'] == 'PASS_N41_W11_INDEPENDENT_PUBLIC_RELATION'
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('N131 W33 build cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
control = json.loads(Path(protocol['constructed_control']).read_text())
public = json.loads(Path(protocol['public_point']).read_text())
assert control['aligned_rotations'] == [0, 0, 36, 36, 72]
assert public['curve_id'] == control['curve_id'] == protocol['curve_id']

design.WIDTH = 33
design.BITS = [bit for bit in range(33) if bit != design.SEED_MASK.bit_length() - 1]
design.BASE = [1 << (bit + 1) for bit in design.BITS]
design.PB = [design.F.square(value) ^ design.F.mul(design.SEED, value)
             for value in design.BASE]
design.ROTATIONS = [0, 0, 36, 36, 72]
assert len(design.BITS) == 32


def rank(words):
    pivots = {}
    for word in words:
        while word:
            bit = word.bit_length() - 1
            if bit not in pivots:
                pivots[bit] = word
                break
            word ^= pivots[bit]
    return len(pivots)


assert rank(design.PB) == 32


def bit_or(circ, a, b):
    return circ.xor((a, b, circ.and_(a, b)))


def strict_less(circ, left, right):
    less = 0
    for a, b in zip(left, right):
        equal = circ.xor((a, b, -1))
        smaller_here = circ.and_(circ.xor((a, -1)), b)
        less = bit_or(circ, smaller_here, circ.and_(equal, less))
    return less


def build(target):
    circ, wires, base_counts = design.build(target)
    parity_wires = [wire for row in wires['out']
                    for wire, tr in zip(row, design.TRACE) if tr]
    target_trace = design.previous.trace(target)
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
    return circ, wires, base_counts, counts


def bind(values, wires, word):
    values.update({wire: word >> index & 1 for index, wire in enumerate(wires)})


constructed, wires, control_base, control_counts = build(control['target_reciprocal'])
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
assert check == {'clauses': control_counts['clauses'],
                 'native_xor_rows': control_counts['xor_rows']}
after_control = time.monotonic()

public_target = design.F.inverse(public['raw_point'][0])
circ, public_wires, base_counts, counts = build(public_target)
assert counts == control_counts and base_counts == control_base
path = HERE / 'n131_formula.xcnf'
circ.write(path)
wire_record = {'mask': public_wires['mask'], 'out': public_wires['out'],
               'source_inverse': public_wires['source_inverse'],
               'middle': public_wires['middle'],
               'source_bits': design.BITS,
               'public_raw_point': public['raw_point'],
               'public_subgroup_point': public['public_target'],
               'public_reciprocal': public_target,
               'rotations': design.ROTATIONS}
(HERE / 'n131_input_wires.json').write_text(json.dumps(wire_record, sort_keys=True, indent=2) + '\n')
finished = time.monotonic()
signal.alarm(0)
result = {'status': 'PASS_N131_W33_ALIGNED_CONSTRUCTED_AND_PUBLIC_CIRCUIT',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'source_bits': design.BITS, 'source_product_basis_rank': 32,
          'rotations': design.ROTATIONS,
          'public_raw_point': public['raw_point'],
          'public_subgroup_point': public['public_target'],
          'public_reciprocal': public_target,
          'constructed_control_target': control['raw_target'],
          'constructed_assignment_check': check,
          'base_counts': base_counts, 'counts': counts,
          'formula_bytes': path.stat().st_size,
          'formula_sha256': sha(path),
          'input_wires_sha256': sha(HERE / 'n131_input_wires.json'),
          'control_and_first_build_seconds': after_control - started,
          'second_build_and_write_seconds': finished - after_control,
          'wall_seconds': finished - started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'n131_build_protocol.json')}
(HERE / 'n131_build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'counts', 'wall_seconds', 'formula_bytes')}, sort_keys=True))
