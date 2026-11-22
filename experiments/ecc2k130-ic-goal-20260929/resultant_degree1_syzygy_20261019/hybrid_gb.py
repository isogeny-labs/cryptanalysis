"""Quartic resultant plus exact cubic consequences for frozen blocks."""
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

from sage.all import BooleanPolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
case_name = sys.argv[1]
cfg = json.loads((HERE / 'hybrid_protocol.json').read_text())
case = cfg['cases'][case_name]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name, digest in cfg['sources'].items():
    assert sha(name) == digest, name


class BinaryField:
    def __init__(self, degree, reduction):
        self.degree = degree
        self.mask = (1 << degree) - 1
        self.reduction = reduction

    def mul(self, a, b):
        assert 0 <= a <= self.mask and 0 <= b <= self.mask
        out = 0
        while b:
            if b & 1:
                out ^= a
            b >>= 1
            a <<= 1
            if a >> self.degree:
                a = (a & self.mask) ^ self.reduction
        return out

    def square(self, a):
        return self.mul(a, a)

    def frob(self, a, steps):
        for _ in range(steps):
            a = self.square(a)
        return a


def load_instance():
    if case['field_degree'] == 41:
        field = BinaryField(41, (1 << 3) | 1)
        source = ROOT / 'n41_w11_freecode_resultant_20261018' / 'resultant_input.tsv'
        lines = source.read_text().splitlines()
        assert lines[0] == 'FREECODE 25 281 13'
        index = case['target_index']
        pos = 1 + 281 + index * 14
        target = list(map(int, lines[pos].split()[1:]))
        assert target[0] == index
        terms = []
        for line in lines[pos+1:pos+14]:
            tag, row, i, j, value = line.split()
            assert tag == 'C' and int(row) == index
            terms.append((int(i), int(j), int(value)))
        return field, 112, [0, 1, 2, 3, 4, 6, 7, 8, 9, 10], (12, 24), target[1:], terms
    assert case['field_degree'] == 131
    field = BinaryField(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
    data = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' / 'coefficients.json').read_text())
    row = data['rows'][case['target_index']]
    seed_mask = 898618
    bits = [i for i in range(33) if i != seed_mask.bit_length() - 1]
    assert len(bits) == 32
    return field, seed_mask << 1, bits, (0, 18), row['point'], row['terms']


def xor_into(out, monomial, value):
    if value:
        result = out.get(monomial, 0) ^ value
        if result:
            out[monomial] = result
        else:
            out.pop(monomial, None)


def multiply_anf(field, left, right):
    out = {}
    for ml, cl in left.items():
        for mr, cr in right.items():
            xor_into(out, ml | mr, field.mul(cl, cr))
    return out


def square_anf(field, value):
    return {m: field.square(c) for m, c in value.items()}


def powers(field, value):
    first = value
    second = square_anf(field, first)
    third = multiply_anf(field, first, second)
    fourth = square_anf(field, second)
    return [{0: 1}, first, second, third, fourth]


def evaluate(terms, field, p, q):
    pp = [1, p]
    qq = [1, q]
    for _ in range(3):
        pp.append(field.mul(pp[-1], p))
        qq.append(field.mul(qq[-1], q))
    out = 0
    for i, j, c in terms:
        out ^= field.mul(c, field.mul(pp[i], qq[j]))
    return out


started = time.monotonic()
field, seed, positions, rotations, target, terms = load_instance()
assert len(terms) == 13
k = case['first_free_bits']
assert 1 <= k <= len(positions)
assert case['first_base_code'] & ((1 << k) - 1) == 0
assert case['first_base_code'] < (1 << len(positions))
base = [1 << (i + 1) for i in positions]
pb = [field.frob(field.square(a) ^ field.mul(seed, a), rotations[0]) for a in base]
qb = [field.frob(field.square(a) ^ field.mul(seed, a), rotations[1]) for a in base]
p0 = 0
for i, value in enumerate(pb):
    if (case['first_base_code'] >> i) & 1:
        p0 ^= value
p_anf = {0: p0} if p0 else {}
for i in range(k):
    xor_into(p_anf, 1 << i, pb[i])
q_anf = {1 << (k + i): value for i, value in enumerate(qb) if value}
P = powers(field, p_anf)
Q = powers(field, q_anf)
resultant = {}
for i, j, c in terms:
    for m, value in multiply_anf(field, P[i], Q[j]).items():
        xor_into(resultant, m, field.mul(c, value))
assert max((m & ((1 << k) - 1)).bit_count() for m in resultant) <= 2
assert max((m >> k).bit_count() for m in resultant) <= 2
scaled = multiply_anf(field, resultant, p_anf)
assert max(m.bit_count() for m in scaled) <= 3


def evaluate_anf(bits):
    out = 0
    for monomial, c in resultant.items():
        if bits & monomial == monomial:
            out ^= c
    return out


def evaluate_scaled(bits):
    out = 0
    for monomial, c in scaled.items():
        if bits & monomial == monomial:
            out ^= c
    return out


if case['field_degree'] == 41:
    for first_local in range(1 << k):
        p = p0
        for i in range(k):
            if first_local >> i & 1:
                p ^= pb[i]
        for second_code in range(1 << len(positions)):
            q = 0
            for j in range(len(positions)):
                if second_code >> j & 1:
                    q ^= qb[j]
            assignment = first_local | (second_code << k)
            assert evaluate_anf(assignment) == evaluate(terms, field, p, q)
            assert evaluate_scaled(assignment) == field.mul(p, evaluate_anf(assignment))
elif case['target_index'] == 0:
    first_code, second_code = 3, 16722
    if first_code & ~((1 << k) - 1) == case['first_base_code']:
        assignment = (first_code & ((1 << k) - 1)) | (second_code << k)
        assert evaluate_anf(assignment) == 0
        assert evaluate_scaled(assignment) == 0

variable_count = k + len(positions)
R = BooleanPolynomialRing(variable_count, 'x', order=cfg['term_order'])
x = R.gens()
monomials = {}
for mask in set(resultant) | set(scaled):
    term = R.one()
    for j in range(variable_count):
        if mask >> j & 1:
            term *= x[j]
    monomials[mask] = term
equations = [R.zero() for _ in range(2*field.degree)]
for mask, c in resultant.items():
    term = monomials[mask]
    while c:
        low = c & -c
        equations[low.bit_length() - 1] += term
        c ^= low
for mask, c in scaled.items():
    term = monomials[mask]
    while c:
        low = c & -c
        equations[field.degree + low.bit_length() - 1] += term
        c ^= low
build_seconds = time.monotonic() - started
print(json.dumps({'event': 'GB_START', 'case': case_name,
                  'term_order': cfg['term_order'],
                  'variables': variable_count, 'equations': len(equations),
                  'anf_monomials': len(resultant),
                  'cubic_monomials': len(scaled),
                  'degree_histogram': dict(Counter(m.bit_count() for m in resultant)),
                  'build_seconds': build_seconds}), flush=True)
gb_started = time.monotonic()
gb = list(R.ideal(equations).groebner_basis())
gb_seconds = time.monotonic() - gb_started
unit = len(gb) == 1 and gb[0] == R.one()
pins = {}
if not unit:
    for i in range(variable_count):
        if x[i] in gb:
            pins[i] = 0
        elif x[i] + 1 in gb:
            pins[i] = 1
recovered = None
if len(pins) == variable_count:
    assignment = sum(v << i for i, v in pins.items())
    assert evaluate_anf(assignment) == 0
    recovered = {'first_code': case['first_base_code'] | (assignment & ((1 << k) - 1)),
                 'second_code': assignment >> k}
status = 'GB_UNIT_IDEAL' if unit else 'GB_COMPLETE'
out = {'status': status, 'candidate_id': None, 'curve_id': cfg['curve_ids'][str(field.degree)],
       'term_order': cfg['term_order'],
       'case': case_name, 'target_index': case['target_index'], 'target_point': target,
       'first_base_code': case['first_base_code'], 'first_free_bits': k,
       'second_free_bits': len(positions), 'variables': variable_count,
       'equations': len(equations), 'anf_monomials': len(resultant),
       'degree_histogram': dict(Counter(m.bit_count() for m in resultant)),
       'cubic_monomials': len(scaled),
       'method': 'quartic field equations with exact p-scaled cubic consequences',
       'build_seconds': build_seconds, 'gb_seconds': gb_seconds,
       'gb_polynomials': len(gb), 'pinned_bits': len(pins),
       'recovered_codes': recovered,
       'protocol_sha256': sha(HERE / 'hybrid_protocol.json')}
(HERE / ('hybrid_' + case_name + '_result.json')).write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True), flush=True)
