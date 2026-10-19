"""Freeze and construct the W29 triple-plus-one-root-norm N131 XCNF experiment."""
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


protocol = json.loads((HERE / 'protocol.json').read_text())
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert protocol['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
assert protocol['rotations'] == [0, 0, 0, 36, 36]
design.ROTATIONS = protocol['rotations']
F = design.F
CINV = F.inverse(design.C)
BETA = F.frob(F.mul(design.H, CINV), 36)
control = json.loads(Path(protocol['constructed_control']).read_text())
public = json.loads(Path(protocol['public_point']).read_text())
collisions = json.loads(Path(protocol['collision_table']).read_text())
assert collisions['status'] == 'EXACT_VALID_N131_W29_FOLDED_COLLISION_PAIRS'
assert collisions['distinct_valid_collision_pairs'] == 2093
assert control['curve_id'] == public['curve_id'] == protocol['curve_id']
assert control['aligned_rotations'] == protocol['rotations']
bad_pairs = [tuple(row['codes']) for row in collisions['collision_pairs']]
assert len(bad_pairs) == len(set(bad_pairs)) == 2093
started = time.monotonic()


def constant(alg, value):
    return alg.expression(((-1, value),))


def scale(alg, value, coefficient):
    return alg.expression((wire, F.mul(basis, coefficient)) for wire, basis in value.terms)


def frob(alg, value, exponent):
    return alg.expression((wire, F.frob(basis, exponent)) for wire, basis in value.terms)


def one_root_norm(alg, alpha, gamma, z, t):
    one = alg.one
    beta = constant(alg, BETA)
    t2 = alg.square(t)
    ag = alg.mul(alpha, gamma)
    a = alg.add(alg.mul(t2, ag), t)
    common = alg.add(one, scale(alg, t2, BETA))
    b = alg.mul(alpha, common)
    d = alg.mul(gamma, common)
    e = scale(alg, t2, F.square(BETA) ^ 1)
    m = alg.add(alg.mul(a, z), d)
    n = alg.add(alg.mul(b, z), e)
    return alg.add(alg.square(n), alg.mul(gamma, alg.mul(n, m)),
                   scale(alg, alg.square(m), BETA))


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
    circ = design.previous.KaratsubaCircuit(design.N, design.TAPS)
    alg = design.previous.Algebra(circ, F, dense_and_threshold=3000)
    wires = {'mask': [], 'out': [], 'source_inverse': [], 'middle': []}
    nodes = []
    right_alpha = []
    for slot, rotation in enumerate(protocol['rotations']):
        masks = [circ.variable() for _ in design.BITS]
        wires['mask'].append(masks)
        product = alg.expression(zip(masks, design.PB))
        circ.require_zero([circ.xor(w for w, value in zip(masks, design.BASE)
                                    if design.previous.trace(value))])
        witness = [circ.variable() for _ in range(design.N)]
        wires['source_inverse'].append(witness)
        tensor = {(i, j): circ.and_(masks[i], witness[j])
                  for i in range(len(design.BITS)) for j in range(design.N)}
        product_inverse = alg.expression(
            (w, F.mul(design.PB[i], 1 << j)) for (i, j), w in tensor.items())
        source_inverse = alg.expression(
            (w, F.mul(design.BASE[i], 1 << j)) for (i, j), w in tensor.items())
        circ.require_zero(alg.add(product_inverse, alg.one).bits())
        circ.require_zero([circ.xor(w for w, tr in zip(source_inverse.bits(), design.TRACE) if tr)])
        circ.require_zero([circ.xor(w for j, w in enumerate(witness)
                                    if design.previous.trace(F.mul(design.SEED, 1 << j)))])
        if slot >= 3:
            right_alpha.append(frob(alg, scale(alg, product, CINV), rotation))
        if slot == 4:
            wires['out'].append(None)
            continue
        out = [circ.variable() for _ in range(design.N)]
        wires['out'].append(out)
        circ.clauses.append(' '.join(map(str, out)) + ' 0')
        z = alg.from_bits(out)
        cz2 = scale(alg, alg.square(z), design.C)
        circ.require_zero(alg.add(cz2, alg.mul(product, z), constant(alg, design.H)).bits())
        rotated = circ.linear_element(out, [F.frob(1 << i, rotation) for i in range(design.N)])
        nodes.append(alg.from_bits(rotated))
    assert len(right_alpha) == 2 and len(nodes) == 4
    for _ in range(3):
        middle = [circ.variable() for _ in range(design.N)]
        wires['middle'].append(middle)
        circ.clauses.append(' '.join(map(str, middle)) + ' 0')
        nodes.append(alg.from_bits(middle))
    target_expr = constant(alg, target)
    for a, b, z in ((nodes[0], nodes[1], nodes[4]),
                    (nodes[4], nodes[2], nodes[5]),
                    (nodes[5], nodes[6], target_expr)):
        ab = alg.mul(a, b)
        abz = alg.mul(ab, z)
        circ.require_zero(alg.add(alg.square(abz), abz,
                                  alg.square(alg.add(a, b)), alg.square(z)).bits())
    circ.require_zero(one_root_norm(alg, right_alpha[0], right_alpha[1],
                                   nodes[3], nodes[6]).bits())
    # The eliminated fourth output trace is recovered from a split root.
    same_code_clauses = 0
    collision_clauses = 0
    for left in range(5):
        for right in range(left + 1, 5):
            same_group = (left < 3 and right < 3) or (left >= 3 and right >= 3)
            if not same_group:
                differences = [circ.xor((a, b)) for a, b in
                               zip(wires['mask'][left], wires['mask'][right])]
                circ.clauses.append(' '.join(map(str, differences)) + ' 0')
                same_code_clauses += 1
            for a_code, b_code in bad_pairs:
                circ.clauses.append(' '.join(map(str,
                    mismatch(wires['mask'][left], a_code) +
                    mismatch(wires['mask'][right], b_code))) + ' 0')
                collision_clauses += 1
                if not same_group:
                    circ.clauses.append(' '.join(map(str,
                        mismatch(wires['mask'][left], b_code) +
                        mismatch(wires['mask'][right], a_code))) + ' 0')
                    collision_clauses += 1
    for left, right in ((0, 1), (1, 2), (3, 4)):
        circ.clauses.append(f'{strict_less(circ, wires["mask"][left], wires["mask"][right])} 0')
    counts = {'and_gates': circ.and_count, 'variables': circ.next_var - 1,
              'clauses': len(circ.clauses), 'xor_rows': len(circ.xors),
              'sparse_mul_calls': alg.sparse_mul_calls,
              'generic_mul_calls': alg.generic_mul_calls}
    policy = {'same_code_clauses': same_code_clauses,
              'collision_clauses': collision_clauses,
              'strict_order_clauses': 3}
    return circ, wires, counts, policy


def bind(values, wires, word):
    values.update({wire: word >> j & 1 for j, wire in enumerate(wires)})


def run_control():
    signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('build wall cap')))
    signal.alarm(protocol['build_wall_cap_seconds'])
    target = control['target_reciprocal']
    circ, wires, control_counts, control_policy = build(target)
    assignment = {}
    for slot, row in enumerate(control['pairs']):
        code = sum(((row['masks'][0] >> bit) & 1) << index
                   for index, bit in enumerate(design.BITS))
        bind(assignment, wires['mask'][slot], code)
        bind(assignment, wires['source_inverse'][slot], row['source_inverse_product'])
        if slot < 4:
            bind(assignment, wires['out'][slot], row['output_reciprocal'])
    for bits, value in zip(wires['middle'], control['middle_reciprocals']):
        bind(assignment, bits, value)
    full = selector.old.complete_assignment(circ, assignment)
    check = selector.old.check_assignment(circ, full)
    assert check['clauses'] == control_counts['clauses']
    assert check['native_xor_rows'] == control_counts['xor_rows']
    signal.alarm(0)
    result = {'status': 'PASS_N131_ONE_ROOT_NORM_CONSTRUCTED_CIRCUIT',
              'candidate_id': None, 'curve_id': protocol['curve_id'],
              'counts': control_counts, 'policy_counts': control_policy,
              'constructed_assignment_check': check,
              'control_target_reciprocal': target,
              'control_build_wall_seconds': time.monotonic() - started,
              'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(HERE / 'protocol.json')}
    (HERE / 'build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    run_control()
