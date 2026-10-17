"""Build an exact five-pair tower with a rootless final pair resultant."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'
FIXTURE = ROOT / 'n41_w9_implicit_fivepair_tower_20261017/fixture.json'
PRIOR = ROOT / 'n41_w8_quotient_first_pair_20261015'
TOWER = ROOT / 'n41_w8_three_code_resultant_20261015'
sys.path.insert(0, str(PRIOR))
sys.path.insert(0, str(TOWER))
import circuit as previous
from tower_circuit import TowerCircuit, f4


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'build_protocol.json').read_text())
for name, path in {
    'script': Path(__file__), 'states': SOURCE, 'fixture': FIXTURE,
    'witness': HERE / 'witness.json',
    'tower': TOWER / 'tower_circuit.py', 'prior': PRIOR / 'circuit.py',
    'norm': PRIOR / 'norm_gate_early.py',
    'runtime': HERE / 'sage_runtime_info.json',
    'selector': ROOT / 'n131_w20_selector_elimination_v2_20261013/selector.py',
    'linear': ROOT / 'n131_w20_output_inverse_linear_20261012/linear.py',
    'trace_runner': ROOT / 'n131_w20_inverse_trace_20261012/run.py',
    'ninepair_runner': ROOT / 'n131_fixed_seed_ninepair_cubic_20261011/run.py',
    'sevenpair': ROOT / 'n131_w20_sevenpair_gate_20261010/sevenpair_circuit.py',
    'fixed_pair': ROOT / 'n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py',
    'sparse': ROOT / 'n41_basis_aware_quartic_20261011/sparse.py',
    'karatsuba': ROOT.parent / 'koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py',
    'field': ROOT / 'n41_basis_aware_quartic_20261011/replay.py',
}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'formula.xcnf').exists()
source = json.loads(SOURCE.read_text())
fixture = json.loads(FIXTURE.read_text())
witness = json.loads((HERE / 'witness.json').read_text())
F = previous.F
N = 41


def xor(items):
    out = 0
    for x in items:
        out ^= x
    return out


def frob(value, k):
    for _ in range(k):
        value = F.square(value)
    return value


def f3(a, b, c, one):
    ab = a*b
    return (one+ab.square())*c.square()+ab*c+a.square()+b.square()


def alarm(_signal, _frame):
    raise TimeoutError('circuit build exceeded frozen wall cap')


signal.signal(signal.SIGALRM, alarm)
signal.alarm(protocol['build_cap_seconds'])
start = time.monotonic()
bits = [i for i in range(9) if i != 5]
assert len(bits) == 8 and source['rotations'] == [0, 0, 12, 12, 24]
seed = source['seed'] << 1
h0 = F.square(F.halftrace(seed))
base_products = [F.mul((1 << bit) << 1, ((1 << bit) << 1) ^ seed)
                 for bit in bits]
code_masks = {}
code_columns = {}
for ordinal in range(71):
    row = source['states'][0][4*ordinal]
    mask = row['masks'][0]
    code = sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits))
    assert code not in code_masks
    assert xor(base_products[j] for j in range(8) if code >> j & 1) == \
        F.mul(mask << 1, (mask ^ source['seed']) << 1)
    code_masks[code] = mask
    code_columns[code] = frozenset(row['columns'])
assert len(code_masks) == 71
assert fixture['code_bit_words'] == [
    sum(((source['states'][slot][sid]['masks'][0] >> bit) & 1) << j
        for j, bit in enumerate(bits))
    for slot, sid in enumerate(fixture['state_ids'])]

circ = previous.old.KaratsubaCircuit(N, [0, 3])
alg = previous.old.Algebra(circ, previous.Field(), dense_and_threshold=3000)
codes = [[circ.variable() for _ in range(8)] for _ in range(5)]
zbits = [circ.variable() for _ in range(N)]
wbits = [circ.variable() for _ in range(N)]


def mismatch(wires, code):
    return [(-wire if code >> j & 1 else wire)
            for j, wire in enumerate(wires)]


for slot in range(5):
    for forbidden in range(256):
        if forbidden not in code_masks:
            circ.clauses.append(' '.join(map(str, mismatch(codes[slot], forbidden)))+' 0')
collision_clauses = 0
for left_slot in range(5):
    for right_slot in range(left_slot+1, 5):
        for left_code, left_cols in code_columns.items():
            for right_code, right_cols in code_columns.items():
                if not left_cols & right_cols:
                    continue
                row = (mismatch(codes[left_slot], left_code) +
                       mismatch(codes[right_slot], right_code))
                circ.clauses.append(' '.join(map(str, row))+' 0')
                collision_clauses += 1

relations = []
for slot, rotation in enumerate(source['rotations']):
    h = frob(h0, rotation)
    c = 1 ^ h
    assert h and c
    cinv = F.inv(c)
    alpha = alg.expression(zip(codes[slot],
                               [F.mul(frob(v, rotation), cinv)
                                for v in base_products]))
    beta = alg.expression(((-1, F.mul(h, cinv)),))
    relations.append((alpha, beta))

z = alg.from_bits(zbits)
w = alg.from_bits(wbits)
one = alg.one
left_relations = relations[:3]
a, b, c = [TowerCircuit.basis(alg, left_relations, i) for i in range(3)]
z_element = TowerCircuit.constant(alg, left_relations, z)
one_left = TowerCircuit.constant(alg, left_relations, one)
left = f4(a, b, c, z_element, one_left)
after_f4 = time.monotonic()
for bit in range(3):
    left = left.norm(bit)
assert all(not x.terms for x in left.coeffs[1:])
after_left_norm = time.monotonic()

dummy = (alg.zero, alg.zero)
right_relations = [relations[3], dummy, dummy]
d = TowerCircuit.basis(alg, right_relations, 0)
z_right = TowerCircuit.constant(alg, right_relations, z)
w_right = TowerCircuit.constant(alg, right_relations, w)
one_right = TowerCircuit.constant(alg, right_relations, one)
t = fixture['public_reciprocal']
t_expr = alg.expression(((-1, t),))
dz = d*z_right
right_link = (one_right+dz.square())*w_right.square()+dz*w_right+d.square()+z_right.square()
right_link = right_link.norm(0)
assert all(not x.terms for x in right_link.coeffs[1:])

# Res_e(C*e^2+p*e+H, A*e^2+B*e+D)=M^2+L*N.
# This is a binary-linearized quadratic in the final pair's code product p.
add,mul,square=alg.add,alg.mul,alg.square
tw=mul(t_expr,w)
A=add(one,square(tw));B=tw;D=add(square(t_expr),square(w))
he=frob(h0,source['rotations'][4]);ce=1^he
H=alg.expression(((-1,he),));C=alg.expression(((-1,ce),))
p_last=alg.expression(zip(codes[4],[frob(v,source['rotations'][4])
                                   for v in base_products]))
M=add(mul(A,H),mul(C,D))
L=add(mul(A,p_last),mul(C,B))
Nres=add(mul(B,H),mul(p_last,D))
resultant=add(square(M),mul(L,Nres))
after_right_norm = time.monotonic()

initial = {}
for slot, code in enumerate(fixture['code_bit_words']):
    initial.update({wire: (code >> j) & 1 for j, wire in enumerate(codes[slot])})
initial.update({wire: (fixture['left_reciprocal'] >> j) & 1
                for j, wire in enumerate(zbits)})
initial.update({wire: (witness['intermediate_reciprocal'] >> j) & 1
                for j, wire in enumerate(wbits)})


def output_zero(expr, assignment):
    return all((0 if wire == 0 else 1 if wire == -1 else assignment[wire]) == 0
               for wire in expr.bits())


control_values = previous.old.complete_assignment(circ, initial)
assert output_zero(left.coeffs[0], control_values)
assert output_zero(right_link.coeffs[0], control_values)
assert output_zero(resultant, control_values)
after_control = time.monotonic()

for expr in (left.coeffs[0], right_link.coeffs[0], resultant):
    circ.require_zero(expr.bits())
previous.old.check_assignment(circ, previous.old.complete_assignment(circ, initial))
after_constraints = time.monotonic()

circ.write(HERE / 'formula.xcnf')
wire_record = {
    'codes': codes, 'left_reciprocal': zbits,
    'intermediate_reciprocal': wbits,
    'allowed_code_words': sorted(code_masks),
    'source_mask_for_code': {str(k): v for k, v in code_masks.items()},
    'public_reciprocal': t,
}
(HERE / 'input_wires.json').write_text(json.dumps(wire_record, sort_keys=True, indent=2)+'\n')
result = {
    'status': 'PASS_N41_CODE_LINEAR_TOWER_BUILD',
    'candidate_id': None,
    'curve_id': source['curve_id'],
    'public_reciprocal': t,
    'and_gates': circ.and_count,
    'variables': circ.next_var-1,
    'clauses': len(circ.clauses),
    'native_xor_rows': len(circ.xors),
    'collision_clauses': collision_clauses,
    'formula_bytes': (HERE / 'formula.xcnf').stat().st_size,
    'formula_sha256': sha(HERE / 'formula.xcnf'),
    'wire_record_sha256': sha(HERE / 'input_wires.json'),
    'witness_control': {'codes': fixture['code_bit_words'],
                        'left_reciprocal': fixture['left_reciprocal'],
                        'intermediate_reciprocal': witness['intermediate_reciprocal'],
                        'all_three_equations_zero': True,
                        'all_clauses_and_xors_satisfied': True},
    'phase_seconds': {'f4': after_f4-start,
                      'left_norm': after_left_norm-after_f4,
                      'right_link_and_resultant': after_right_norm-after_left_norm,
                      'control': after_control-after_right_norm,
                      'constraints': after_constraints-after_control},
    'total_seconds': time.monotonic()-start,
    'self_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE / 'build_protocol.json'),
}
(HERE / 'build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
signal.alarm(0)
print(json.dumps({'status': result['status'], 'gates': circ.and_count,
                  'clauses': len(circ.clauses),
                  'seconds': result['total_seconds']}))
