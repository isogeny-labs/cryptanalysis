"""Build the aligned N131 public formula with exact folded-column exclusions."""
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


protocol = json.loads((HERE / 'build_protocol.json').read_text())
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert not (HERE / 'formula.xcnf').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('circuit build wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()

control = json.loads(Path(protocol['constructed_control']).read_text())
public = json.loads(Path(protocol['public_point']).read_text())
collisions = json.loads(Path(protocol['collision_table']).read_text())
assert collisions['status'] == 'EXACT_VALID_N131_W29_FOLDED_COLLISION_PAIRS'
assert collisions['distinct_valid_collision_pairs'] == 2093
assert control['aligned_rotations'] == [0, 0, 36, 36, 72]
assert design.ROTATIONS == control['original_rotations']
assert control['curve_id'] == public['curve_id'] == protocol['curve_id']
design.ROTATIONS = control['aligned_rotations']
bad_pairs = [tuple(row['codes']) for row in collisions['collision_pairs']]
assert len(bad_pairs) == len(set(bad_pairs)) == 2093


def bit_or(circ, a, b):
    return circ.xor((a, b, circ.and_(a, b)))


def strict_less(circ, left, right):
    assert len(left) == len(right) == 28
    less = 0
    for a, b in zip(left, right):
        equal = circ.xor((a, b, -1))
        smaller_here = circ.and_(circ.xor((a, -1)), b)
        less = bit_or(circ, smaller_here, circ.and_(equal, less))
    return less


def mismatch(wires, code):
    return [-wire if code >> j & 1 else wire for j, wire in enumerate(wires)]


def build(target):
    circ, wires, base_counts = design.build(target)
    parity_wires = [wire for row in wires['out']
                    for wire, tr in zip(row, design.TRACE) if tr]
    assert len(parity_wires) == 10
    target_trace = design.previous.trace(target)
    circ.require_zero([circ.xor(parity_wires + ([-1] if target_trace else []))])

    same_code_clauses = 0
    collision_clauses = 0
    for left in range(5):
        for right in range(left + 1, 5):
            differences = [circ.xor((a, b)) for a, b in
                           zip(wires['mask'][left], wires['mask'][right])]
            circ.clauses.append(' '.join(map(str, differences)) + ' 0')
            same_code_clauses += 1
            for a_code, b_code in bad_pairs:
                circ.clauses.append(' '.join(map(str,
                    mismatch(wires['mask'][left], a_code) +
                    mismatch(wires['mask'][right], b_code))) + ' 0')
                circ.clauses.append(' '.join(map(str,
                    mismatch(wires['mask'][left], b_code) +
                    mismatch(wires['mask'][right], a_code))) + ' 0')
                collision_clauses += 2
    for left, right in ((0, 1), (3, 4)):
        circ.clauses.append(f'{strict_less(circ, wires["mask"][left], wires["mask"][right])} 0')
    counts = {'and_gates': circ.and_count, 'variables': circ.next_var - 1,
              'clauses': len(circ.clauses), 'xor_rows': len(circ.xors)}
    return circ, wires, base_counts, counts, target_trace, {
        'same_code_clauses': same_code_clauses,
        'collision_clauses': collision_clauses,
        'strict_order_clauses': 2,
    }


def bind(values, wires, word):
    values.update({wire: word >> j & 1 for j, wire in enumerate(wires)})


constructed, wires, control_base, control_counts, control_trace, policy_counts = build(control['target_reciprocal'])
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
after_control = time.monotonic()

public_target = design.F.inverse(public['raw_point'][0])
circ, public_wires, base_counts, counts, target_trace, public_policy = build(public_target)
assert counts == control_counts and base_counts == control_base
assert public_policy == policy_counts
assert public_target == 770794657550069419943936485965613853151
path = HERE / 'formula.xcnf'
circ.write(path)
wire_record = {
    'mask': public_wires['mask'],
    'out': public_wires['out'],
    'source_inverse': public_wires['source_inverse'],
    'middle': public_wires['middle'],
    'public_raw_point': public['raw_point'],
    'public_reciprocal': public_target,
    'rotations': design.ROTATIONS,
}
(HERE / 'input_wires.json').write_text(json.dumps(wire_record, sort_keys=True, indent=2) + '\n')
finished = time.monotonic()
signal.alarm(0)
result = {
    'status': 'PASS_N131_W29_ALIGNED_COLLISION_EXACT_PUBLIC_CIRCUIT',
    'candidate_id': None,
    'curve_id': protocol['curve_id'],
    'public_raw_point': public['raw_point'],
    'public_subgroup_point': public['public_target'],
    'public_reciprocal': public_target,
    'public_trace': target_trace,
    'aligned_rotations': design.ROTATIONS,
    'constructed_control_target': control['raw_target'],
    'constructed_control_trace': control_trace,
    'constructed_assignment_check': check,
    'base_counts': base_counts,
    'counts': counts,
    'policy_counts': policy_counts,
    'formula_bytes': path.stat().st_size,
    'formula_sha256': sha(path),
    'input_wires_sha256': sha(HERE / 'input_wires.json'),
    'control_and_first_build_seconds': after_control - started,
    'second_build_and_write_seconds': finished - after_control,
    'wall_seconds': finished - started,
    'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE / 'build_protocol.json'),
}
(HERE / 'build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'counts', 'policy_counts', 'wall_seconds', 'formula_bytes')},
                 sort_keys=True))
