"""Independently verify one SAT assignment against source points and public Q."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'model_audit_protocol.json').read_text())
for name, path in {
    'script': Path(__file__), 'runtime': HERE / 'sage_runtime_info.json',
    'states': SOURCE, 'formula': HERE / 'formula.xcnf',
    'wires': HERE / 'input_wires.json',
    'solver_stdout': HERE / 'solver.stdout',
    'query': HERE / 'query_result.json',
}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'model_audit_result.json').exists()
query = json.loads((HERE / 'query_result.json').read_text())
assert query['status'] == 'SAT_MODEL_UNVERIFIED'
assert query['stdout_sha256'] == sha(HERE / 'solver.stdout')

start = time.monotonic()
source = json.loads(SOURCE.read_text())
wires = json.loads((HERE / 'input_wires.json').read_text())
values = {}
for line in (HERE / 'solver.stdout').read_text().splitlines():
    if not line.startswith('v '):
        continue
    for token in line[2:].split():
        literal = int(token)
        if literal:
            assert abs(literal) not in values
            values[abs(literal)] = literal > 0
assert values
assert len(values) >= json.loads((HERE / 'build_result.json').read_text())['variables']


def literal_value(literal):
    assert literal
    return values[abs(literal)] if literal > 0 else not values[abs(literal)]


clauses = 0
xors = 0
for line in (HERE / 'formula.xcnf').open():
    if line.startswith(('c ', 'p ')) or not line.strip():
        continue
    if line.startswith('x'):
        row = [int(x) for x in line[1:].split() if x != '0']
        assert sum(literal_value(x) for x in row) % 2 == 1
        xors += 1
    else:
        row = [int(x) for x in line.split() if x != '0']
        assert any(literal_value(x) for x in row)
        clauses += 1
build = json.loads((HERE / 'build_result.json').read_text())
assert clauses == build['clauses'] and xors == build['native_xor_rows']


def word(bit_wires):
    return sum(int(values[v]) << i for i, v in enumerate(bit_wires))


codes = [word(row) for row in wires['codes']]
zword = word(wires['left_reciprocal'])
wword = word(wires['intermediate_reciprocal'])
assert all(code in wires['allowed_code_words'] for code in codes)
mask_to_ordinal = {row['masks'][0]: i for i, row in
                   enumerate(source['states'][0][::4])}
ordinals = [mask_to_ordinal[wires['source_mask_for_code'][str(code)]]
            for code in codes]

K = PolynomialRing(GF(2), 'u')
u = K.gen()
F = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(number):
    return F(K([(int(number) >> i) & 1 for i in range(41)]))


def enc(x):
    return sum(int(c) << i for i, c in enumerate(x.polynomial().list()))


states = [[E(dec(row['point'][0]), dec(row['point'][1])) for row in slot]
          for slot in source['states']]
raw = E(dec(source['target_raw_point'][0]),
        dec(source['target_raw_point'][1]))
public = E(raw[0]**(1 << 6), raw[1]**(1 << 6))
t = dec(wires['public_reciprocal'])
assert t == 1/public[0]
z = dec(zword)
w = dec(wword)

first_options = [range(4*i, 4*i+4) for i in ordinals[:3]]
last_options = [range(4*i, 4*i+4) for i in ordinals[3:]]
left_candidates = []
for ids in itertools.product(*first_options):
    point = sum((states[slot][sid] for slot, sid in enumerate(ids)), E(0))
    if point != E(0) and point[0] and 1/point[0] == z:
        left_candidates.append((ids, point))
right_candidates = [(ids, states[3][ids[0]]+states[4][ids[1]])
                    for ids in itertools.product(*last_options)]

witnesses = []
for left_ids, left in left_candidates:
    for right_ids, right in right_candidates:
        middle=left+states[3][right_ids[0]]
        if middle==E(0) or not middle[0] or 1/middle[0]!=w:
            continue
        ids = list(left_ids+right_ids)
        columns = [col for slot, sid in enumerate(ids)
                   for col in source['states'][slot][sid]['columns']]
        if len(set(columns)) == 10 and left+right == public:
            witnesses.append(ids)

result = {
    'status': ('PASS_N41_UNPINNED_ORDINARY_RELATION'
               if witnesses else 'SAT_CHART_MODEL_WITHOUT_GROUP_WITNESS'),
    'curve_id': source['curve_id'],
    'candidate_id': None,
    'code_bit_words': codes,
    'code_ordinals': ordinals,
    'left_reciprocal': zword,
    'intermediate_reciprocal': wword,
    'left_signed_assignments_matching_coordinate': len(left_candidates),
    'right_signed_assignments_matching_coordinate': len(right_candidates),
    'exact_witnesses': witnesses,
    'clauses_checked': clauses,
    'native_xor_rows_checked': xors,
    'solver_model_variables_checked': len(values),
    'elapsed_seconds': time.monotonic()-start,
    'self_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE / 'model_audit_protocol.json'),
}
(HERE / 'model_audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status': result['status'], 'codes': codes,
                  'witnesses': witnesses}))
