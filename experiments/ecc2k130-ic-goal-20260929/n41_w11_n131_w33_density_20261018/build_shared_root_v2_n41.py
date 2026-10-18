"""Constrain every pair root through its already-present source inverse."""
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


protocol = json.loads((HERE / 'shared_root_build_v2_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'shared_root_formula.xcnf').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('shared-root build cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
fixture = json.loads(Path(protocol['fixture']).read_text())
design.WIDTH = 11
design.BITS = [bit for bit in range(11) if bit != design.SEED_MASK.bit_length() - 1]
design.BASE = [1 << (bit+1) for bit in design.BITS]
design.PB = [design.F.square(word) ^ design.F.mul(design.SEED, word)
             for word in design.BASE]
design.ROTATIONS = [0, 0, 12, 12, 24]
assert len(design.BITS) == 10 and fixture['rotations'] == design.ROTATIONS
F = design.F
CH = F.mul(design.C, design.H)
invC = F.inverse(design.C)


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
alg = design.Algebra(circ, F, dense_and_threshold=3000)
branch_wires = []
for slot in range(5):
    masks = wires['mask'][slot]
    inverse = wires['source_inverse'][slot]
    output = wires['out'][slot]
    p_over_c = alg.expression((wire, F.mul(invC, basis))
                              for wire, basis in zip(masks, design.PB))
    v = alg.from_bits(inverse)
    rhs = alg.expression((wire, F.mul(CH, basis))
                         for wire, basis in alg.square(v).terms)
    canonical = alg.expression((wire, design.halftrace(basis ^ design.trace(basis)))
                               for wire, basis in rhs.terms)
    branch = circ.variable()
    branch_wires.append(branch)
    branch_expr = alg.expression(((branch, 1),))
    z = alg.add(alg.mul(p_over_c, canonical),
                alg.mul(p_over_c, branch_expr))
    circ.require_zero(alg.add(alg.from_bits(output), z).bits())
    circ.require_zero([circ.xor(wire for wire, value in rhs.terms
                                if design.trace(value))])

for masks in wires['mask']:
    circ.require_zero([circ.xor(wire for wire, value in zip(masks, design.BASE)
                                if design.trace(value))])
parity_wires = [wire for row in wires['out']
                for wire, tr in zip(row, design.TRACE) if tr]
target_trace = design.trace(fixture['target_reciprocal'])
circ.require_zero([circ.xor(parity_wires + ([-1] if target_trace else []))])
for left in range(5):
    for right in range(left+1, 5):
        diff = [circ.xor((a, b)) for a, b in
                zip(wires['mask'][left], wires['mask'][right])]
        circ.clauses.append(' '.join(map(str, diff)) + ' 0')
for left, right in ((0, 1), (3, 4)):
    circ.clauses.append(f'{strict_less(circ, wires["mask"][left], wires["mask"][right])} 0')

counts = {'and_gates': circ.and_count, 'variables': circ.next_var-1,
          'clauses': len(circ.clauses), 'xor_rows': len(circ.xors)}
assignment = {}
branch_choices = []
for slot, row in enumerate(fixture['pairs']):
    mask = row['masks'][0]
    code = sum(((mask >> bit) & 1) << index
               for index, bit in enumerate(design.BITS))
    p = F.mul(mask << 1, (mask ^ design.SEED_MASK) << 1)
    assert p
    inverse = F.inverse(p)
    assert inverse == row['source_inverse_product']
    v0 = design.halftrace(F.mul(CH, F.square(inverse)))
    unit = F.mul(p, invC)
    root0 = F.mul(unit, v0)
    roots = (root0, root0 ^ unit)
    assert row['output_reciprocal'] in roots
    branch = roots.index(row['output_reciprocal'])
    branch_choices.append(branch)
    bind(assignment, wires['mask'][slot], code)
    bind(assignment, wires['out'][slot], row['output_reciprocal'])
    bind(assignment, wires['source_inverse'][slot], inverse)
    assignment[branch_wires[slot]] = branch
for bits, value in zip(wires['middle'], fixture['middle_reciprocals']):
    bind(assignment, bits, value)
full = selector.old.complete_assignment(circ, assignment)
check = selector.old.check_assignment(circ, full)
assert check == {'clauses': counts['clauses'],
                 'native_xor_rows': counts['xor_rows']}

path = HERE / 'shared_root_formula.xcnf'
circ.write(path)
wire_record = {'mask': wires['mask'], 'out': wires['out'],
               'source_inverse': wires['source_inverse'],
               'middle': wires['middle'], 'branch': branch_wires,
               'source_bits': design.BITS,
               'raw_oriented_point': fixture['raw_oriented_point'],
               'public_reciprocal': fixture['target_reciprocal'],
               'rotations': design.ROTATIONS}
(HERE / 'shared_root_input_wires.json').write_text(json.dumps(wire_record, sort_keys=True, indent=2) + '\n')
finished = time.monotonic()
signal.alarm(0)
result = {'status': 'PASS_N41_W11_SHARED_INVERSE_ROOT_CONTROL',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'source_width': 11, 'branch_bits': 5,
          'constructed_branch_choices': branch_choices,
          'constructed_assignment_check': check,
          'base_counts': base_counts, 'counts': counts,
          'formula_bytes': path.stat().st_size,
          'formula_sha256': sha(path),
          'input_wires_sha256': sha(HERE / 'shared_root_input_wires.json'),
          'wall_seconds': finished-started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'shared_root_build_v2_protocol.json')}
(HERE / 'shared_root_build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'counts', 'wall_seconds', 'constructed_branch_choices')},
                 sort_keys=True))
